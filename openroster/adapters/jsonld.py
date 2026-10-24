"""schema.org Event JSON-LD, on configured pages or pages found through a sitemap."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree as ET

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from ..config import Source
from ..fetch import BudgetExceeded, Fetcher, FetchError, FetchRefused
from .base import Adapter, AdapterResult, Candidate
from .common import clean, keep, parse_structured

EVENT_TYPES = {
    "Event", "EducationEvent", "BusinessEvent", "SocialEvent", "Hackathon", "ExhibitionEvent",
    "CourseInstance", "Festival", "LiteraryEvent", "ScreeningEvent", "PublicationEvent",
}
COUNTRY_NAMES = {"canada": "CA", "united states": "US", "usa": "US", "us": "US", "ca": "CA"}
PROVINCES = {
    "ontario": "ON", "on": "ON", "quebec": "QC", "québec": "QC", "qc": "QC", "british columbia": "BC", "bc": "BC",
    "alberta": "AB", "ab": "AB", "manitoba": "MB", "mb": "MB", "saskatchewan": "SK", "sk": "SK",
    "nova scotia": "NS", "ns": "NS", "new brunswick": "NB", "nb": "NB", "newfoundland and labrador": "NL",
    "nl": "NL", "prince edward island": "PE", "pe": "PE",
}


def _walk(node: object) -> Iterator[dict]:
    if isinstance(node, list):
        for n in node:
            yield from _walk(n)
    elif isinstance(node, dict):
        types = node.get("@type")
        tlist = types if isinstance(types, list) else [types]
        if any(isinstance(t, str) and t in EVENT_TYPES for t in tlist):
            yield node
        for key in ("@graph", "itemListElement", "item", "subEvent", "event", "events"):
            if key in node:
                yield from _walk(node[key])


def extract_events(html_text: str) -> list[dict]:
    tree = HTMLParser(html_text)
    out: list[dict] = []
    for s in tree.css('script[type="application/ld+json"]'):
        raw = s.text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Some CMSs emit trailing commas; one conservative repair attempt.
            try:
                data = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))
            except json.JSONDecodeError:
                continue
        out.extend(_walk(data))
    return out


def _name(v: object) -> str | None:
    if isinstance(v, dict):
        return clean(str(v.get("name") or "")) or None
    if isinstance(v, list) and v:
        return _name(v[0])
    if isinstance(v, str):
        return clean(v) or None
    return None


def event_to_candidate(e: dict, page_url: str, source: Source, adapter: str = "jsonld") -> Candidate | None:
    title = clean(str(e.get("name") or ""))
    if not title:
        return None
    desc = clean(str(e.get("description") or ""))
    start, all_day = parse_structured(e.get("startDate"), source.timezone)
    end, _ = parse_structured(e.get("endDate"), source.timezone)
    loc = e.get("location")
    loc = loc[0] if isinstance(loc, list) and loc else loc
    venue = city = region = country = None
    online = False
    if isinstance(loc, dict):
        if loc.get("@type") == "VirtualLocation":
            online = True
        venue = _name(loc)
        addr = loc.get("address")
        if isinstance(addr, dict):
            city = clean(str(addr.get("addressLocality") or "")) or None
            reg = clean(str(addr.get("addressRegion") or "")).lower()
            ctry = addr.get("addressCountry")
            ctry = _name(ctry) if isinstance(ctry, dict) else ctry
            country = COUNTRY_NAMES.get(str(ctry or "").lower(), str(ctry).upper() if ctry and len(str(ctry)) == 2 else None)
            if reg in PROVINCES and country in (None, "CA"):
                country = "CA"
                region = f"CA-{PROVINCES[reg]}"
            elif country == "US" and len(reg) == 2:
                region = f"US-{reg.upper()}"
        elif isinstance(addr, str):
            venue = venue or clean(addr)
    elif isinstance(loc, str):
        venue = clean(loc)
    mode_attr = str(e.get("eventAttendanceMode") or "")
    mode = (
        "online" if "Online" in mode_attr or online
        else "hybrid" if "Mixed" in mode_attr
        else "in_person" if "Offline" in mode_attr
        else None
    )
    status = str(e.get("eventStatus") or "")
    offers = e.get("offers")
    offers = offers[0] if isinstance(offers, list) and offers else offers
    cost = None
    if isinstance(offers, dict) and offers.get("price") is not None:
        cost = "free" if str(offers.get("price")) in ("0", "0.0", "0.00") else f"{offers.get('price')} {offers.get('priceCurrency', '')}".strip()
    text = f"{title} {desc} {venue or ''}"
    if not keep(source, text, title):
        return None
    return Candidate(
        source_id=source.id,
        adapter=adapter,
        url=str(e.get("url") or page_url),
        title=title,
        start=start,
        end=end,
        all_day=all_day,
        timezone=source.timezone,
        uid=str(e.get("@id")) if e.get("@id") else None,
        organizer=_name(e.get("organizer")),
        mode=mode,
        venue=venue,
        city=city,
        region=region,
        country=country,
        registration_url=offers.get("url") if isinstance(offers, dict) else None,
        cost=cost,
        cancelled="Cancelled" in status,
        text=text,
        date_confidence="structured",
    )


class JsonLdAdapter(Adapter):
    name = "jsonld"

    def pages(self, source: Source, fetcher: Fetcher) -> list[str]:
        return [source.url, *source.options.get("urls", [])]

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        res = AdapterResult()
        for url in self.pages(source, fetcher):
            try:
                r = fetcher.get(url, source_id=source.id)
            except BudgetExceeded:
                res.errors.append("page budget reached; results are partial")
                break
            except (FetchError, FetchRefused) as e:
                res.errors.append(str(e))
                continue
            res.pages += 1
            for ev in extract_events(r.text):
                res.raw_count += 1
                c = event_to_candidate(ev, url, source, self.name)
                if c:
                    res.candidates.append(c)
        return res


SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def parse_sitemap(xml_text: str) -> tuple[list[tuple[str, str | None]], list[str]]:
    """Returns ([(url, lastmod)], [child sitemap urls])."""
    root = ET.fromstring(xml_text.encode())
    urls = [
        (u.findtext(f"{SM_NS}loc", "").strip(), u.findtext(f"{SM_NS}lastmod"))
        for u in root.findall(f"{SM_NS}url")
    ]
    children = [s.findtext(f"{SM_NS}loc", "").strip() for s in root.findall(f"{SM_NS}sitemap")]
    return urls, children


class SitemapAdapter(JsonLdAdapter):
    """options: url_pattern (regex), max_age_days (lastmod filter, default 120), child_pattern (regex)."""

    name = "sitemap"

    def pages(self, source: Source, fetcher: Fetcher) -> list[str]:
        pattern = re.compile(source.options.get("url_pattern", r"/events?/"))
        child_rx = re.compile(source.options.get("child_pattern", r"event|post|page|sitemap"))
        max_age = timedelta(days=int(source.options.get("max_age_days", 120)))
        limit = int(source.options.get("max_pages", source.page_budget - 3))
        now = datetime.now(UTC)
        found: list[tuple[str, str | None]] = []
        queue = [source.url]
        seen: set[str] = set()
        while queue and len(seen) < 5:
            sm = queue.pop(0)
            if sm in seen:
                continue
            seen.add(sm)
            r = fetcher.get(sm, source_id=source.id, accept="application/xml, text/xml")
            urls, children = parse_sitemap(r.text)
            found.extend(u for u in urls if pattern.search(u[0]))
            queue.extend(c for c in children if child_rx.search(c))
        fresh: list[tuple[str, str]] = []
        for url, lastmod in found:
            dt, _ = parse_structured(lastmod, "UTC") if lastmod else (None, False)
            if dt is None or now - dt <= max_age:
                fresh.append((url, lastmod or ""))
        fresh.sort(key=lambda u: u[1], reverse=True)  # most recently modified first
        return [u for u, _ in fresh[:limit]]
