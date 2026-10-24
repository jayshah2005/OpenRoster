"""Candidate -> Opportunity, using only rules. Candidates without a confident date become review items."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from ..adapters.base import Candidate
from ..config import Source, known_verdict_for
from ..extract.classify import (
    classify_type,
    detect_audience,
    detect_cost,
    detect_eligibility,
    detect_mode,
    detect_roles,
    mentions_travel_support,
)
from ..extract.dates import find_deadline
from ..extract.geo import find_place_in_text, find_school_in_text, lookup, near_schools
from ..model import Opportunity

TYPE_LABEL = {
    "hackathon": "Hackathon", "info_session": "Info session", "tech_talk": "Tech talk",
    "career_fair": "Career fair", "networking": "Networking event", "workshop": "Workshop",
    "conference": "Conference", "case_competition": "Case competition",
    "early_career_program": "Early-career program", "other": "Event",
}
ROLE_PHRASE = {
    "volunteer": "volunteers", "mentor": "mentors", "judge": "judges",
    "organizer_team": "organizers", "workshop_lead": "workshop leads",
}
# "Fireside chat with Jane Doe" -> "Fireside chat". Speaker names are personal data and are not kept.
_WITH_PERSON = re.compile(
    r"\s*(?:[-–—:|,]\s*)?\b(?:with|featuring|feat\.|ft\.|w/)\s+(?:dr\.?\s+|prof\.?\s+)?"
    r"[A-Z][a-z'’-]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z'’-]+){1,2}\s*$"
)
_ORG_WORDS = re.compile(r"\b(?:inc|ltd|bank|university|college|group|labs?|technologies|corp|club|society|team)\b", re.I)


@dataclass
class ReviewItem:
    key: str
    source_id: str
    title: str
    url: str
    reasons: list[str]
    evidence: str


def slugify(s: str, n: int = 50) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:n].rstrip("-") or "event"


def make_id(organizer: str, title: str, start: datetime, key: str) -> str:
    h = hashlib.sha1(key.encode()).hexdigest()[:4]
    base = slugify(title, 50)
    org = slugify(organizer, 20)
    if not base.startswith(org[:8]):
        base = f"{org}-{base}"
    return f"{start:%Y-%m}-{base[:70].rstrip('-')}-{h}"


def candidate_key(c: Candidate) -> str:
    """Identity of a candidate within its source: UID if given, else URL + start date."""
    if c.uid:
        return f"{c.source_id}|{c.uid}"
    day = c.start.date().isoformat() if c.start else "nodate"
    return f"{c.source_id}|{c.url}|{day}|{c.title.lower()}"


def strip_person_names(title: str) -> str:
    m = _WITH_PERSON.search(title)
    if m and not _ORG_WORDS.search(m.group(0)):
        return title[: m.start()].strip(" -–—:|,") or title
    return title


AUDIENCE_PHRASE = {
    "first_year": "first-year students", "second_year": "second-year students",
    "women_nonbinary": "women and non-binary students", "black_students": "Black students",
    "indigenous_students": "Indigenous students", "lgbtq": "2SLGBTQIA+ students",
}
ELIG_PHRASE = {"undergrad": "undergraduates", "grad": "graduate students", "high_school": "high-school students"}


def build_summary(type_: str, organizer: str, mode: str, city: str | None, roles: list[dict], tags: list[str],
                  eligibility: list[str], cost: str, tz: str) -> str:
    """A one-line summary in our own words, built only from facts we already store (never from source text)."""
    words = ["free" if cost == "free" else "", {"online": "online", "hybrid": "hybrid"}.get(mode, ""),
             TYPE_LABEL.get(type_, "Event").lower()]
    s = " ".join(w for w in words if w).capitalize() + f" by {organizer}"
    if city and mode != "online":
        s += f" in {city}"
    who = [AUDIENCE_PHRASE[t] for t in tags if t in AUDIENCE_PHRASE] or [ELIG_PHRASE[e] for e in eligibility if e in ELIG_PHRASE]
    if "mostly_high_school" in tags:
        who = ["mostly high-school students"]
    if who:
        s += " for " + " and ".join(who[:2])
    s += "."
    if "beginner_friendly" in tags:
        s += " Beginners welcome."
    participant = next((r for r in roles if r["role"] == "participant" and r.get("closes")), None)
    if participant:
        s += f" Apply by {participant['closes'].astimezone(ZoneInfo(tz)):%b %-d}."
    extra = [ROLE_PHRASE[r["role"]] for r in roles if r["role"] in ROLE_PHRASE]
    if extra:
        s += " Also looking for " + (", ".join(extra[:-1]) + " and " + extra[-1] if len(extra) > 1 else extra[0]) + "."
    return s[:200]


def registration_route(url: str | None, source: Source | None) -> str:
    if source and source.options.get("registration") == "school_portal_login":
        return "school_portal_login"
    if not url:
        return "unknown"
    if url.startswith("mailto:"):
        return "email"
    kv = known_verdict_for(url)
    if kv and kv.verdict == "link_only":
        return "form"
    return "public_link"


def role_status(opens: datetime | None, closes: datetime | None, now: datetime) -> str:
    if closes and closes < now:
        return "closed"
    if opens and opens > now:
        return "upcoming"
    if opens or closes:
        return "open"
    return "unknown"


def normalize(c: Candidate, source: Source | None, now: datetime) -> Opportunity | ReviewItem:
    key = candidate_key(c)
    reasons = list(c.review_reasons)
    if c.start is None:
        reasons = reasons or ["no start date"]
    if c.date_confidence == "none" and "no date could be parsed with confidence" not in reasons:
        reasons.append("no date could be parsed with confidence")
    if reasons:
        return ReviewItem(key, c.source_id, c.title, c.url, reasons, (c.date_evidence or c.text)[:300])
    assert c.start is not None
    tz = c.timezone or (source.timezone if source else "America/Toronto")
    text = f"{c.title} {c.text}"

    title = strip_person_names(c.title)[:200]
    organizer = (c.organizer or (source.options.get("organizer") if source else None)
                 or (source.name if source else "Unknown"))[:120]
    type_ = c.type or classify_type(text, source.default_type if source else None) or "other"

    # Roles: explicit roles from the candidate; otherwise the source defaults plus calls named in the title.
    role_names = [r.role for r in c.roles] or list(dict.fromkeys(
        (source.default_roles if source else ["participant"]) + detect_roles(c.title)
    ))
    roles = []
    for name in role_names:
        rc = next((r for r in c.roles if r.role == name), None)
        opens = rc.opens if rc else None
        closes = rc.closes if rc else None
        evidence = rc.evidence if rc else None
        if name == "participant" and closes is None and c.text:
            dl = find_deadline(c.text, tz, infer_year=bool(source and source.options.get("infer_year")))
            if dl and dl.start <= (c.end or c.start) + timedelta(days=1):
                closes, evidence = dl.start, dl.evidence
        status = rc.status if rc and rc.status != "unknown" else role_status(opens, closes, now)
        roles.append({"role": name, "opens": opens, "closes": closes, "status": status,
                      "url": rc.url if rc else None, "evidence": evidence})

    mode = c.mode or detect_mode(text)
    loc_defaults = (source.location if source else None) or {}
    city, region, country = c.city, c.region, c.country
    place = None
    if mode != "online":
        place = lookup(city, region, country) if city else find_place_in_text(f"{c.venue or ''} {c.text}")
        if place is None and loc_defaults.get("city"):
            place = lookup(loc_defaults["city"], loc_defaults.get("region"), loc_defaults.get("country"))
    campus = None
    if mode != "online" and place is None and city is None:
        campus = find_school_in_text(f"{c.title} {c.venue or ''}")
        if campus:
            place = lookup(campus.city, None, "CA") if campus.city else None
            city = city or campus.city
    if place:
        city, region, country = city or place.name, region or place.region, country or place.country
    region = region or loc_defaults.get("region")
    country = country or loc_defaults.get("country")
    if country is None and region:
        country = region.split("-")[0]
    if c.lat is not None and c.lon is not None:
        lat, lon = c.lat, c.lon
    elif campus:
        lat, lon = campus.lat, campus.lon
    elif place:
        lat, lon = place.lat, place.lon
    else:
        lat, lon = None, None

    tags = list(dict.fromkeys([*(source.tags if source else []), *c.tags, *detect_audience(f"{c.title} {c.text}")]))
    if c.date_confidence == "inferred_year":
        tags.append("year_inferred")
    eligibility = c.eligibility or (source.eligibility if source else None) or detect_eligibility(text)
    cost = c.cost if c.cost in ("free", "paid", "unknown") else (detect_cost(c.cost) if c.cost else detect_cost(text))
    travel = mentions_travel_support(text)
    start = c.start
    end = c.end if c.end and c.end >= start else None
    opp_id = make_id(organizer, title, start, key)

    status = "cancelled" if c.cancelled else "scheduled"
    record = {
        "id": opp_id,
        "type": type_,
        "title": title,
        "organizer": organizer,
        "roles": roles,
        "start": start,
        "end": end,
        "timezone": tz,
        "all_day": c.all_day,
        "series_id": c.series_id,
        "mode": mode,
        "location": {"venue_name": (c.venue or None) and c.venue[:120], "city": city, "region": region,
                     "country": country},
        "geo": {"lat": lat, "lon": lon, "source": "venue" if c.lat is not None else "gazetteer"}
        if lat is not None else None,
        "near_schools": [{"school_id": s, "km": d} for s, d in near_schools(lat, lon)]
        if lat is not None and lon is not None else [],
        "schools": c.schools or (source.schools if source and source.schools else ["open_to_all"]),
        "eligibility": eligibility,
        "registration": {"route": registration_route(c.registration_url or c.url, source),
                         "url": c.registration_url or c.url},
        "cost": {"kind": cost},
        "travel_support": {"stated": travel},
        "tags": tags,
        "summary": c.summary or build_summary(type_, organizer, mode, city, roles, tags, eligibility, cost, tz),
        "sources": [{"url": c.url, "adapter": c.adapter, "source_id": c.source_id, "fetched_at": now}],
        "obtained_via": [c.adapter],
        "first_seen": now,
        "last_seen": now,
        "last_verified": now,
        "status": status,
        "ai_suggested": c.ai_suggested,
    }
    return Opportunity.model_validate(record)


def host_of(url: str) -> str:
    return urlsplit(url).hostname or ""
