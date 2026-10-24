from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from openroster.adapters.base import AdapterResult, Candidate
from openroster.config import Source
from openroster.model import Opportunity
from openroster.pipeline import run as run_mod
from openroster.pipeline import store
from openroster.pipeline.merge import MergeState, ingest, title_score
from openroster.pipeline.normalize import ReviewItem, candidate_key, normalize, strip_person_names
from openroster.validate import pii_problems

TOR = ZoneInfo("America/Toronto")
NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)


def S(sid="s1", **kw) -> Source:
    return Source(id=sid, name="Test Org", adapter="ics", url="https://example.edu/cal.ics", owner="t", **kw)


def C(title="Hack the Valley", start=datetime(2026, 11, 20, 18, tzinfo=TOR), **kw) -> Candidate:
    base = dict(source_id="s1", adapter="ics", url="https://hackthevalley.io", title=title, start=start,
                timezone="America/Toronto", date_confidence="structured")
    base.update(kw)
    return Candidate(**base)


def test_normalize_builds_valid_record():
    o = normalize(C(text="Join us at UTSC, Toronto, ON. Volunteers wanted!", uid="u1"), S(), NOW)
    assert isinstance(o, Opportunity)
    assert o.type == "hackathon" and o.location.city == "Toronto" and o.location.region == "CA-ON"
    assert o.geo is not None and o.summary and len(o.summary) <= 200
    assert o.roles[0].role == "participant"
    assert o.id.startswith("2026-11-")


def test_no_date_becomes_review_item():
    out = normalize(C(start=None, date_confidence="none", date_evidence="Coming soon!"), S(), NOW)
    assert isinstance(out, ReviewItem) and out.evidence == "Coming soon!"


def test_speaker_names_are_stripped_from_titles():
    assert strip_person_names("Fireside Chat with Jane Doe") == "Fireside Chat"
    assert strip_person_names("AMA with Shopify Engineering Team") == "AMA with Shopify Engineering Team"


def test_volunteer_role_from_title():
    o = normalize(C(title="DeltaHacks volunteer applications", uid="v"), S(), NOW)
    assert {r.role for r in o.roles} == {"participant", "volunteer"}


def test_title_similarity():
    assert title_score("Hack the Valley X", "Hack The Valley X 2026") >= 90
    assert title_score("Coffee Chat", "Career Fair") < 80


def _state(records=None):
    return MergeState(records=records or {}, keys={}, aliases={}, misses={})


def test_cross_source_duplicates_merge_and_keep_both_links():
    st = _state()
    a = normalize(C(uid="a"), S(), NOW)
    rid = ingest(st, "s1|a", a, NOW)
    b = normalize(C(source_id="s2", adapter="html", url="https://other.org/htv", uid="b",
                    title="Hack The Valley 2026"), S("s2"), NOW)
    rid2 = ingest(st, "s2|b", b, NOW)
    assert rid == rid2 and len(st.records) == 1
    rec = st.records[rid]
    assert {s.source_id for s in rec.sources} == {"s1", "s2"}
    assert set(rec.obtained_via) == {"ics", "html"}


def test_moved_date_is_tracked():
    st = _state()
    a = normalize(C(uid="m"), S(), NOW)
    rid = ingest(st, "s1|m", a, NOW)
    moved = normalize(C(uid="m", start=datetime(2026, 11, 27, 18, tzinfo=TOR)), S(), NOW)
    ingest(st, "s1|m", moved, NOW + timedelta(hours=6))
    rec = st.records[rid]
    assert rec.status == "moved" and rec.start.day == 27
    assert rec.history[0].field == "start"


def test_cancellation_is_tracked():
    st = _state()
    rid = ingest(st, "s1|c", normalize(C(uid="c"), S(), NOW), NOW)
    ingest(st, "s1|c", normalize(C(uid="c", cancelled=True), S(), NOW), NOW)
    assert st.records[rid].status == "cancelled"


def test_pii_check():
    assert pii_problems({"summary": "Contact jane@example.com or 905-555-1234"}, "x")
    assert not pii_problems({"sources": [{"url": "https://calendar.google.com/calendar/ical/a%40b.com/basic.ics"}]}, "x")


@pytest.fixture
def tmpdata(tmp_path, monkeypatch):
    for name in ("RECORDS", "ARCHIVE", "REVIEW"):
        monkeypatch.setattr(store, name, tmp_path / name.lower())
    for name in ("STATE", "KEYS", "ALIASES", "TAKEDOWNS"):
        monkeypatch.setattr(store, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(run_mod, "load_sources", lambda: [])
    monkeypatch.setattr(run_mod, "load_manual", lambda: AdapterResult())
    monkeypatch.setattr(run_mod, "load_submissions", lambda: AdapterResult())
    return tmp_path


def test_run_end_to_end_writes_archives_and_reviews(tmpdata):
    res = AdapterResult(candidates=[
        C(uid="future"),
        C(title="Old Hackathon", uid="old", start=datetime(2026, 10, 1, tzinfo=TOR)),
        C(title="Mystery event", uid="nodate", start=None, date_confidence="none", date_evidence="TBA"),
    ])
    rep = run_mod.run(extra=[(S(), res)], now=NOW, include_hackathons=False)
    files = list((tmpdata / "records").glob("*.json"))
    assert len(files) == 1 and len(rep.new) == 1
    assert rep.review and rep.review[0]["title"] == "Mystery event"
    # Second identical run: no changes
    rep2 = run_mod.run(extra=[(S(), res)], now=NOW, include_hackathons=False)
    assert rep2.new == [] and rep2.updated == 0
    # After the event: archived
    rep3 = run_mod.run(extra=[(S(), AdapterResult())], now=NOW + timedelta(days=60), include_hackathons=False)
    assert rep3.archived and not list((tmpdata / "records").glob("*.json"))


def test_takedown_suppresses(tmpdata):
    (tmpdata / "takedowns.json").write_text('{"urls": ["https://hackthevalley.io"]}')
    rep = run_mod.run(extra=[(S(), AdapterResult(candidates=[C(uid="x")]))], now=NOW, include_hackathons=False)
    assert rep.new == []


def test_candidate_key_stable():
    assert candidate_key(C(uid="u")) == "s1|u"


def test_audience_tags():
    o = normalize(C(title="HerHacks: beginner-friendly hackathon for first-year students", uid="aud"), S(), NOW)
    assert {"women_nonbinary", "first_year", "beginner_friendly"} <= set(o.tags)
    plain = normalize(C(title="Distributed systems talk", uid="plain", text="Room 101"), S(), NOW)
    assert not {"women_nonbinary", "first_year"} & set(plain.tags)
