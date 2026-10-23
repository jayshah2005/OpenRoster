"""Issue form -> YAML entry -> record (acceptance check 6, minus GitHub itself)."""

from datetime import UTC, datetime

import yaml

from openroster.adapters.api import load_entries
from openroster.ops import submission as sub
from openroster.ops.submission import parse_issue, parse_sections
from openroster.pipeline.normalize import normalize

BODY = """### Title

DeltaHacks 13

### Type

hackathon

### Organizer

DeltaHacks

### Official link

https://deltahacks.com

### Start

2027-01-09 09:00

### End

2027-01-10 17:00

### Time zone

America/Toronto

### Format

in_person

### City

Hamilton

### Province or state

ON

### Country

CA

### Ways to take part

- [X] participant
- [X] volunteer
- [ ] mentor
- [ ] judge
- [ ] organizer_team
- [ ] workshop_lead

### Deadlines

participant: 2026-12-15
volunteer: 2026-12-01 23:59

### Role links

volunteer: https://forms.gle/abc123

### Who can join

- [ ] open_to_all
- [ ] school_only
- [ ] high_school
- [X] undergrad
- [ ] grad

### Schools

_No response_

### Cost

free

### Travel support offered?

yes

### Short summary

McMaster's annual student hackathon. Volunteers wanted.

### Confirmations

- [X] The details are public and correct, and I included no personal data.
"""


def test_sections():
    s = parse_sections(BODY)
    assert s["Title"] == "DeltaHacks 13" and s["Schools"] == ""


def test_submission_becomes_a_record(tmp_path, monkeypatch):
    monkeypatch.setattr(sub, "CONFIG", tmp_path)
    monkeypatch.setattr(sub, "duplicates", lambda e: [])
    result = parse_issue(BODY, kind="submit", issue_number=42, write=True)
    assert result["ok"], result["errors"]
    files = list((tmp_path / "submissions").glob("*.yaml"))
    assert len(files) == 1
    entry = yaml.safe_load(files[0].read_text())
    assert entry["roles"][1] == {"role": "volunteer", "closes": "2026-12-01T23:59", "url": "https://forms.gle/abc123"}
    assert entry["location"] == {"city": "Hamilton", "region": "CA-ON", "country": "CA"}

    res = load_entries(tmp_path / "submissions", "submission")
    rec = normalize(res.candidates[0], None, datetime(2026, 10, 23, tzinfo=UTC))
    assert rec.title == "DeltaHacks 13" and rec.type == "hackathon"
    assert rec.obtained_via == ["submission"]
    assert {r.role for r in rec.roles} == {"participant", "volunteer"}
    assert rec.registration.url == "https://deltahacks.com"
    assert rec.summary.startswith("McMaster's annual")
    assert rec.location.city == "Hamilton" and rec.geo is not None


def test_bad_submission_explains_problems(monkeypatch):
    monkeypatch.setattr(sub, "duplicates", lambda e: [])
    bad = BODY.replace("2027-01-09 09:00", "next Saturday").replace(
        "McMaster's annual student hackathon. Volunteers wanted.", "Contact jane.doe@gmail.com " + "x" * 200
    ).replace("participant: 2026-12-15", "judge: 2026-12-15")
    result = parse_issue(bad, kind="submit", issue_number=7)
    text = " ".join(result["errors"])
    assert not result["ok"]
    assert "Start must look like" in text
    assert "200" in text
    assert "personal contact details" in text
    assert "`judge`" in text


def test_takedown_by_listing_and_by_site(tmp_path, monkeypatch):
    from openroster.pipeline import store

    monkeypatch.setattr(store, "TAKEDOWNS", tmp_path / "takedowns.json")
    r1 = parse_issue("### Listing link or site address\n\nhttps://openroster.vercel.app/o/2026-11-x-ab12/\n\n"
                     "### Your relationship to it\n\nI organize this event", kind="takedown", write=True)
    r2 = parse_issue("### Listing link or site address\n\nwww.example.com\n\n### Your relationship to it\n\nI run this site",
                     kind="takedown", write=True)
    assert r1["ok"] and r2["ok"]
    td = store.takedowns()
    assert td["ids"] == ["2026-11-x-ab12"] and "example.com" in td["hosts"]
