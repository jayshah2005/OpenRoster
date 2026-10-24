"""openroster discover: proposes feeds found by audits and hackathons found in data, never blocked hosts."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from openroster import discover as disc
from openroster.adapters.base import Candidate
from openroster.pipeline.normalize import normalize


def test_discover_feeds_and_hackathons(monkeypatch):
    audits = {
        "brock-experiencebu-rss": {
            "verdict": "allowed", "url": "https://experiencebu.brocku.ca/events",
            "feeds": [
                "https://csclub.example.ca/events.ics",
                "https://calendar.google.com/calendar/ical/club%40gmail.com/public/basic.ics",  # robots.txt: blocked
                "https://lu.ma/some-page",                      # blocked host: never proposed
                "https://experiencebu.brocku.ca/events.rss",    # already configured
            ],
        },
        "some-blocked": {"verdict": "blocked", "feeds": ["https://x.example/feed.ics"]},
    }
    monkeypatch.setattr(disc, "load_results", lambda: audits)
    now = datetime(2026, 10, 23, tzinfo=UTC)
    rec = normalize(Candidate(source_id="s", adapter="api", url="https://newhacks2026.example.ca", title="NewHacks 2026",
                              start=datetime(2026, 11, 20, tzinfo=ZoneInfo("America/Toronto")), type="hackathon",
                              country="CA", region="CA-ON", city="Toronto", date_confidence="structured"), None, now)
    devpost = normalize(Candidate(source_id="s", adapter="api", url="https://x.devpost.com", title="Devpost Thing",
                                  start=datetime(2026, 11, 21, tzinfo=ZoneInfo("America/Toronto")), type="hackathon",
                                  country="CA", date_confidence="structured"), None, now)
    monkeypatch.setattr(disc.store, "load_records", lambda: {rec.id: rec, devpost.id: devpost})
    found = disc.discover()
    assert [s["url"] for s in found.sources] == ["https://csclub.example.ca/events.ics"]
    assert found.sources[0]["reviewed"] is False
    assert [h["name"] for h in found.hackathons] == ["NewHacks 2026"]


def test_engage_feed_is_detected_and_proposed_as_rss(monkeypatch):
    from openroster.audit.core import AuditResult, detect_platform

    class NoNet:
        def get(self, *a, **k):
            raise AssertionError("no network in tests")

    res = AuditResult(url="https://newschool.campuslabs.ca/engage/events", checked="x")
    detect_platform(res.url, "<html><body><script src='https://static.campuslabs.com/x.js'></script></body></html>", NoNet(), res)
    assert "https://newschool.campuslabs.ca/engage/events.rss" in res.feeds

    monkeypatch.setattr(disc, "load_results", lambda: {"x": {"verdict": "allowed", "url": res.url, "feeds": res.feeds}})
    monkeypatch.setattr(disc.store, "load_records", lambda: {})
    found = disc.discover()
    assert any(s["adapter"] == "rss" and s["url"].endswith("/engage/events.rss") for s in found.sources)


def test_autoselect_finds_working_selectors_without_network():
    from pathlib import Path

    from openroster.config import Source
    from openroster.ops.autoselect import candidates_for

    html = (Path(__file__).parent / "fixtures/sources/scotiabank-campus-events.html").read_text()
    src = Source(id="x", name="x", adapter="html", url="https://www.scotiabank.com/careers/", owner="x",
                 options={"filter": "all"})
    chosen, dated = candidates_for(html, src)
    assert chosen and chosen["item"] and dated >= 10


def test_dated_exports_are_skipped(monkeypatch):
    audits = {"hackathon:uworcs": {"verdict": "allowed", "url": "https://www.uwo.ca/x", "feeds": [
        "https://www.uwo.ca/events/2026/04/one-event.ics",
        "https://www.uwindsor.ca/science/computerscience/ical/2026-10/events.ics",
        "https://www.uwindsor.ca/science/computerscience/ical/%2A/events.ics",
    ]}}
    monkeypatch.setattr(disc, "load_results", lambda: audits)
    monkeypatch.setattr(disc.store, "load_records", lambda: {})
    found = disc.discover()
    assert [s["url"] for s in found.sources] == ["https://www.uwindsor.ca/science/computerscience/ical/%2A/events.ics"]
    assert found.sources[0]["id"] == "hackathon-uworcs-feed-1"
