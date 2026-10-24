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
                "https://calendar.google.com/calendar/ical/club%40gmail.com/public/basic.ics",
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
    assert [s["url"] for s in found.sources] == ["https://calendar.google.com/calendar/ical/club%40gmail.com/public/basic.ics"]
    assert found.sources[0]["reviewed"] is False
    assert [h["name"] for h in found.hackathons] == ["NewHacks 2026"]
