"""Campus calendar platforms with public read endpoints: WordPress The Events Calendar and Localist."""

from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlencode, urlsplit

from ..config import Source
from ..fetch import BudgetExceeded, Fetcher
from .base import Adapter, AdapterResult, Candidate
from .common import clean, keep, parse_structured


def tribe_endpoint(url: str) -> str:
    p = urlsplit(url)
    if "/wp-json/tribe/events/v1/events" in p.path:
        return url.split("?")[0]
    return f"{p.scheme}://{p.netloc}/wp-json/tribe/events/v1/events"


def parse_tribe(payload: dict, source: Source) -> tuple[list[Candidate], int, str | None]:
    out: list[Candidate] = []
    events = payload.get("events") or []
    for e in events:
        title = clean(e.get("title"))
        desc = clean(e.get("description") or e.get("excerpt"))
        cats = " ".join(c.get("name", "") for c in e.get("categories") or [])
        venue = e.get("venue") if isinstance(e.get("venue"), dict) else {}
        text = f"{title} {desc} {cats} {venue.get('venue', '')}"
        if not title or not keep(source, text):
            continue
        tz = e.get("timezone") or source.timezone
        start, _ = parse_structured(e.get("start_date"), tz)
        end, _ = parse_structured(e.get("end_date"), tz)
        all_day = bool(e.get("all_day"))
        organizers = e.get("organizer") or []
        org = organizers[0].get("organizer") if organizers and isinstance(organizers[0], dict) else None
        out.append(
            Candidate(
                source_id=source.id,
                adapter="tribe",
                url=e.get("url") or source.url,
                title=title,
                start=start,
                end=end,
                all_day=all_day,
                timezone=tz,
                uid=f"tribe:{e.get('id')}",
                organizer=clean(org) or None,
                venue=clean(venue.get("venue")) or None,
                city=venue.get("city") or None,
                registration_url=e.get("website") or None,
                cost=clean(e.get("cost")) or None,
                text=text,
                date_confidence="structured",
            )
        )
    return out, len(events), payload.get("next_rest_url")


class TribeAdapter(Adapter):
    name = "tribe"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        res = AdapterResult()
        q = {"start_date": date.today().isoformat(), "per_page": 50}
        url: str | None = f"{tribe_endpoint(source.url)}?{urlencode(q)}"
        while url:
            try:
                r = fetcher.get(url, source_id=source.id, accept="application/json")
            except BudgetExceeded:
                res.errors.append("page budget reached; results are partial")
                break
            res.pages += 1
            cands, n, url = parse_tribe(json.loads(r.text), source)
            res.raw_count += n
            res.candidates.extend(cands)
        return res


def localist_endpoint(url: str) -> str:
    p = urlsplit(url)
    if p.path.startswith("/api/2/events"):
        return url.split("?")[0]
    return f"{p.scheme}://{p.netloc}/api/2/events"


def parse_localist(payload: dict, source: Source) -> tuple[list[Candidate], int, int]:
    out: list[Candidate] = []
    events = payload.get("events") or []
    for wrapper in events:
        e = wrapper.get("event", wrapper)
        title = clean(e.get("title"))
        desc = clean(e.get("description_text") or e.get("description"))
        types = " ".join(t.get("name", "") for t in ((e.get("filters") or {}).get("event_types") or []))
        text = f"{title} {desc} {types} {e.get('location_name') or ''}"
        if not title or not keep(source, text):
            continue
        geo = e.get("geo") or {}
        experience = (e.get("experience") or "").lower()
        mode = {"inperson": "in_person", "virtual": "online", "hybrid": "hybrid"}.get(experience)
        for inst_wrap in e.get("event_instances") or []:
            inst = inst_wrap.get("event_instance", inst_wrap)
            start, _ = parse_structured(inst.get("start"), source.timezone)
            end, _ = parse_structured(inst.get("end"), source.timezone)
            many = len(e.get("event_instances") or []) > 1
            out.append(
                Candidate(
                    source_id=source.id,
                    adapter="localist",
                    url=e.get("localist_url") or e.get("url") or source.url,
                    title=title,
                    start=start,
                    end=end,
                    all_day=bool(inst.get("all_day")),
                    timezone=source.timezone,
                    uid=f"localist:{e.get('id')}:{inst.get('id')}",
                    series_id=f"localist:{e.get('id')}" if many else None,
                    mode=mode,
                    venue=clean(e.get("location_name")) or None,
                    city=geo.get("city") or None,
                    lat=float(geo["latitude"]) if geo.get("latitude") else None,
                    lon=float(geo["longitude"]) if geo.get("longitude") else None,
                    registration_url=e.get("ticket_url") or e.get("url") or None,
                    cost="free" if e.get("free") else (clean(e.get("ticket_cost")) or None),
                    text=text,
                    date_confidence="structured",
                )
            )
    page = payload.get("page") or {}
    return out, len(events), int(page.get("total") or 1)


class LocalistAdapter(Adapter):
    name = "localist"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        res = AdapterResult()
        base = localist_endpoint(source.url)
        page, total = 1, 1
        while page <= total:
            q = {"days": 120, "pp": 100, "page": page, "start": date.today().isoformat()}
            q.update(source.options.get("query", {}))
            try:
                r = fetcher.get(f"{base}?{urlencode(q)}", source_id=source.id, accept="application/json")
            except BudgetExceeded:
                res.errors.append("page budget reached; results are partial")
                break
            res.pages += 1
            cands, n, total = parse_localist(json.loads(r.text), source)
            res.raw_count += n
            res.candidates.extend(cands)
            page += 1
            if n == 0:
                break
        return res
