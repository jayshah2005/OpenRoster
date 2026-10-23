"""Every adapter is tested against saved fixtures; no test touches the network."""

import json
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openroster.adapters.api import parse_hackclub
from openroster.adapters.campus import parse_localist, parse_tribe
from openroster.adapters.html import parse_html_list
from openroster.adapters.ics import parse_ics
from openroster.adapters.jsonld import event_to_candidate, extract_events, parse_sitemap
from openroster.config import Source, load_sources

FX = Path(__file__).parent / "fixtures"
TOR = ZoneInfo("America/Toronto")
NOW = datetime(2026, 10, 20, tzinfo=UTC)


def src(adapter: str, **kw) -> Source:
    return Source(id=f"test-{adapter}", name="Test", adapter=adapter, url="https://example.edu/events", owner="t", **kw)


def configured(sid: str) -> Source:
    return next(s for s in load_sources() if s.id == sid)


# ---- ICS ------------------------------------------------------------------------------------------------
def test_ics_recurring_exdate_dst_cancelled_floating():
    res = parse_ics((FX / "ics/club-recurring.ics").read_text(), src("ics", options={"filter": "cs"}), now=NOW)
    titles = [c.title for c in res.candidates]
    nights = [c for c in res.candidates if c.title == "Weekly Coding Night"]
    # COUNT=4 minus one EXDATE
    assert [c.start.date().isoformat() for c in nights] == ["2026-10-22", "2026-11-05", "2026-11-12"]
    # DST ends Nov 1: 18:00 local both before and after, different UTC offsets
    assert nights[0].start.utcoffset() != nights[1].start.utcoffset()
    assert all(c.start.hour == 18 for c in nights)
    assert len({c.uid for c in nights}) == 3 and nights[0].series_id == "weekly-coding-night@club.example"
    assert nights[0].url == "https://club.example/coding-night"
    talk = next(c for c in res.candidates if c.title.startswith("Tech Talk"))
    assert talk.cancelled
    floating = next(c for c in res.candidates if c.title == "Resume Workshop")
    assert floating.start == datetime(2026, 11, 12, 15, 0, tzinfo=TOR)
    hackday = next(c for c in res.candidates if c.title == "Club Hack Day")
    assert hackday.all_day and hackday.end.date().isoformat() == "2026-11-22"
    assert "Lunchtime yoga" not in titles  # filtered out by the CS relevance rule


def test_ics_real_luma_fixture_parses():
    text = (FX / "ics/luma-cutc.ics").read_text()
    res = parse_ics(text, src("ics"), now=datetime(2026, 1, 1, tzinfo=UTC))
    assert res.raw_count >= 0  # shape check: parsing a real export does not raise


# ---- Tribe / Localist -----------------------------------------------------------------------------------
def test_tribe_real_fixture():
    payload = json.loads((FX / "tribe/vector.json").read_text())
    cands, n, _next = parse_tribe(payload, src("tribe"))
    assert n == len(payload["events"]) and n > 0
    for c in cands:
        assert c.start is not None and c.start.tzinfo is not None
        assert c.uid.startswith("tribe:") and c.url.startswith("https://")


def test_localist():
    payload = json.loads((FX / "localist/events.json").read_text())
    cands, n, total = parse_localist(payload, src("localist", options={"filter": "cs"}))
    assert n == 3 and total == 1
    titles = [c.title for c in cands]
    assert "Choir rehearsal" not in titles
    ds = [c for c in cands if c.title.startswith("Data Science")]
    assert len(ds) == 2 and ds[0].series_id == "localist:102" and ds[0].mode == "online"
    g = next(c for c in cands if c.title.startswith("Google"))
    assert g.city == "Waterloo" and g.lat and g.cost == "free"


# ---- JSON-LD / sitemap ----------------------------------------------------------------------------------
def test_jsonld():
    html = (FX / "jsonld/page.html").read_text()
    events = extract_events(html)
    assert len(events) == 3  # includes the one repaired from a trailing comma
    cands = [event_to_candidate(e, "https://example.org/events", src("jsonld")) for e in events]
    wit = next(c for c in cands if c and c.title.startswith("Women"))
    assert wit.city == "Toronto" and wit.region == "CA-ON" and wit.country == "CA"
    assert wit.mode == "in_person" and wit.cost == "free" and wit.organizer == "Example Tech Org"
    ml = next(c for c in cands if c and c.title.startswith("Intro"))
    assert ml.all_day and ml.cancelled and ml.mode == "online"


def test_sitemap_parse():
    xml = """<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://ex.org/events/a</loc><lastmod>2026-10-01</lastmod></url>
    <url><loc>https://ex.org/about</loc></url></urlset>"""
    urls, children = parse_sitemap(xml)
    assert urls[0] == ("https://ex.org/events/a", "2026-10-01") and not children


# ---- HTML (configured sources) --------------------------------------------------------------------------
def test_bmo_on_campus_cards():
    s = configured("bmo-student-events")
    res = parse_html_list((FX / "sources/bmo-student-events.html").read_text(), s.url, s)
    titles = {c.title: c for c in res.candidates}
    assert len(res.candidates) >= 5
    hh = titles["HerHacks Hackathon"]
    assert hh.start.date().isoformat() == "2026-11-28" and hh.date_confidence == "explicit"
    assert all(c.start is not None for c in res.candidates)


def test_bmo_virtual_workshops_one_candidate_per_session():
    s = configured("bmo-virtual-workshops")
    res = parse_html_list((FX / "sources/bmo-virtual-workshops.html").read_text(), s.url, s)
    interviews = [c for c in res.candidates if c.title == "Interviewing 101"]
    assert len(interviews) >= 2
    assert interviews[0].end > interviews[0].start
    assert all(c.date_confidence == "inferred_year" for c in interviews)
    assert interviews[0].url.startswith("https://jobs.bmo.com/ca/en/event/")


def test_scotiabank_cards_and_atlantic_time():
    s = configured("scotiabank-campus-events")
    res = parse_html_list((FX / "sources/scotiabank-campus-events.html").read_text(), s.url, s)
    assert len(res.candidates) >= 20
    smu = next(c for c in res.candidates if "St. Mary" in c.title)
    assert smu.timezone == "America/Halifax"
    assert all(c.title.startswith("Scotiabank on campus: ") or "Discover" in c.title for c in res.candidates)


def test_html_undated_item_goes_to_review():
    s = src("html", options={"item": "li", "filter": "all"})
    res = parse_html_list("<ul><li><h3>Hack Night</h3> sometime soon</li></ul>", s.url, s)
    assert res.candidates[0].review_reasons and res.candidates[0].start is None


# ---- Hack Club API --------------------------------------------------------------------------------------
def test_hackclub_tags_high_school():
    items = json.loads((FX / "api/hackclub.json").read_text())
    res = parse_hackclub(items, src("hackclub", options={"countries": ["CA", "US"]}))
    assert res.raw_count == len(items)
    for c in res.candidates:
        assert "mostly_high_school" in c.tags and c.eligibility == ["high_school"] and c.type == "hackathon"


# ---- RSS / JSON feeds -----------------------------------------------------------------------------------
from openroster.adapters.feeds import _norm_dt, get_path, parse_json_items, parse_rss  # noqa: E402


def test_engage_rss_brock():
    s = configured("brock-experiencebu-rss")
    res = parse_rss((FX / "rss/brock-engage.xml").read_text(), s)
    assert res.raw_count >= 40
    assert res.candidates, "CS/career filter should keep some events"
    for c in res.candidates:
        assert c.start is not None and c.start.tzinfo is not None and c.date_confidence == "structured"
        assert c.url.startswith("https://experiencebu.brocku.ca/event/")
    assert all("chess" not in c.title.lower() for c in res.candidates)


def test_rss_without_structured_dates_uses_rules_or_review():
    xml = """<rss version="2.0"><channel><item><title>Coding workshop</title><link>https://x.ca/e/1</link>
    <description>Join us on November 12, 2026 from 6-8pm in room 101.</description></item>
    <item><title>Hack night</title><link>https://x.ca/e/2</link><description>Date TBA</description></item>
    </channel></rss>"""
    res = parse_rss(xml, src("rss", options={"filter": "all"}))
    a, b = res.candidates
    assert a.start.isoformat() == "2026-11-12T18:00:00-05:00" and a.date_confidence == "explicit"
    assert b.start is None and b.review_reasons


def test_json_western_mapping_never_reads_contacts():
    s = configured("western-events-json")
    payload = json.loads((FX / "json/western.json").read_text())
    res = parse_json_items(payload, s)
    assert res.raw_count == len(payload["events"])
    for c in res.candidates:
        assert c.start is not None and c.uid.startswith("western-events-json:")
        assert "@" not in c.text


def test_wordpress_cu_event_mapping():
    s = configured("carleton-scs-events-api")
    res = parse_json_items(json.loads((FX / "wp/carleton-scs.json").read_text()), s)
    assert res.candidates and all(c.start is not None for c in res.candidates)
    assert all(c.url.startswith("https://carleton.ca/scs/") for c in res.candidates)


def test_path_and_datetime_helpers():
    assert get_path({"a": [{"b": 1}]}, "a.0.b") == 1
    assert get_path({"a": []}, "a.0.b") is None
    assert _norm_dt("2026-10-27 11:00:00") == "2026-10-27T11:00:00"
    assert _norm_dt("2026-11-24T12:30-0500") == "2026-11-24T12:30-05:00"
