"""Official free public APIs, and the manual / submission YAML entries."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

from ..config import CONFIG, Source
from ..fetch import Fetcher
from .base import Adapter, AdapterResult, Candidate, RoleCandidate
from .common import clean, parse_structured


def parse_hackclub(items: list[dict], source: Source) -> AdapterResult:
    """Hack Club's hackathon list (https://hackathons.hackclub.com). Mostly high-school events.
    Their terms ask for a credit link to hackathons.hackclub.com, shown on the About page."""
    res = AdapterResult()
    countries = set(source.options.get("countries", ["CA"]))
    include_virtual = source.options.get("include_virtual", True)
    for e in items:
        res.raw_count += 1
        virtual = bool(e.get("virtual"))
        if (e.get("countryCode") or "") not in countries and not (include_virtual and virtual):
            continue
        start, _ = parse_structured(e.get("start"), "UTC")
        end, _ = parse_structured(e.get("end"), "UTC")
        mode = "hybrid" if e.get("hybrid") else "online" if virtual else "in_person"
        cc = e.get("countryCode") or None
        st = e.get("state") or None
        res.candidates.append(
            Candidate(
                source_id=source.id,
                adapter="api",
                url=e.get("website") or "https://hackathons.hackclub.com",
                title=clean(e.get("name")),
                start=start,
                end=end,
                timezone=source.timezone,
                uid=f"hackclub:{e.get('id')}",
                organizer=clean(e.get("name")),  # student-run events organize themselves; Hack Club only lists them
                type="hackathon",
                mode=mode,
                city=e.get("city") or None,
                region=f"{cc}-{st}" if cc and st and len(st) <= 3 else None,
                country=cc,
                lat=e.get("latitude"),
                lon=e.get("longitude"),
                tags=["mostly_high_school"],
                eligibility=["high_school"],
                text=clean(e.get("name")),
                date_confidence="structured",
            )
        )
    return res


class HackClubAdapter(Adapter):
    name = "hackclub"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        r = fetcher.get(source.url, source_id=source.id, accept="application/json")
        res = parse_hackclub(json.loads(r.text), source)
        res.pages = 1
        return res


def entry_to_candidate(e: dict, source_id: str, adapter: str) -> Candidate:
    """Manual and submission YAML use the record field names directly; dates must be explicit ISO 8601."""
    tz = e.get("timezone", "America/Toronto")

    def dt(v: object) -> datetime | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        return parse_structured(str(v), tz)[0]

    start, all_day = parse_structured(str(e["start"]), tz)
    roles = [
        RoleCandidate(
            role=r["role"],
            opens=dt(r.get("opens")),
            closes=dt(r.get("closes")),
            status=r.get("status", "unknown"),
            url=r.get("url"),
        )
        for r in e.get("roles", [{"role": "participant"}])
    ]
    loc = e.get("location") or {}
    return Candidate(
        source_id=source_id,
        adapter=adapter,
        url=e["url"],
        title=e["title"],
        start=start,
        end=dt(e.get("end")),
        all_day=e.get("all_day", all_day),
        timezone=tz,
        uid=f"{adapter}:{e['key']}" if e.get("key") else None,
        organizer=e.get("organizer"),
        type=e.get("type"),
        roles=roles,
        mode=e.get("mode"),
        venue=loc.get("venue_name"),
        city=loc.get("city"),
        region=loc.get("region"),
        country=loc.get("country"),
        registration_url=(e.get("registration") or {}).get("url"),
        cost=(e.get("cost") or {}).get("kind"),
        tags=e.get("tags", []),
        eligibility=e.get("eligibility"),
        schools=e.get("schools"),
        cancelled=e.get("status") == "cancelled",
        text=f"{e['title']} {e.get('summary', '')}",
        date_confidence="structured",
        ai_suggested=list(e.get("ai_suggested") or []),
    )


def load_entries(folder: Path, adapter: str) -> AdapterResult:
    res = AdapterResult()
    for f in sorted(folder.glob("*.yaml")):
        doc = yaml.safe_load(f.read_text()) or {}
        entries = doc.get("entries", [doc] if "title" in doc else [])
        for e in entries:
            if e.get("ignore") or not e.get("start"):
                continue  # unfilled review stubs
            res.raw_count += 1
            c = entry_to_candidate(e, f"{adapter}:{f.stem}", adapter)
            c.summary = (e.get("summary") or "")[:200] or None
            res.candidates.append(c)
    return res


def load_manual() -> AdapterResult:
    return load_entries(CONFIG / "manual", "manual")


def load_submissions() -> AdapterResult:
    return load_entries(CONFIG / "submissions", "submission")
