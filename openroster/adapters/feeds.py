"""RSS event feeds (Anthology/Campus Labs Engage and others) and configurable JSON feeds (custom JSON files and
WordPress REST custom post types)."""

from __future__ import annotations

import json
import re
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from ..config import Source
from ..extract.dates import parse_when
from ..fetch import BudgetExceeded, Fetcher
from .base import Adapter, AdapterResult, Candidate
from .common import clean, keep, parse_structured, to_zone

EVENTS_NS = "{events}"  # Engage puts <start>, <end>, <host>, <location>, <status> in the "events" namespace


def _rfc822(s: str | None):
    if not s:
        return None
    try:
        return parsedate_to_datetime(s.strip())
    except (TypeError, ValueError):
        return None


def parse_rss(xml_text: str, source: Source) -> AdapterResult:
    """RSS 2.0. Dates come from Engage's <events:start>/<end>, an h-event dt-start in the description, or,
    failing those, the rule-based parser on the description text (never pubDate, which is not the event date)."""
    res = AdapterResult()
    root = ET.fromstring(xml_text.encode())
    for item in root.iter("item"):
        res.raw_count += 1
        title = clean(item.findtext("title"))
        title = re.sub(r"\s*\((?:cancelled|canceled)\)\s*$", "", title, flags=re.I)
        link = (item.findtext("link") or "").strip()
        desc_html = item.findtext("description") or ""
        host = clean(item.findtext(f"{EVENTS_NS}host"))
        location = clean(item.findtext(f"{EVENTS_NS}location"))
        status = (item.findtext(f"{EVENTS_NS}status") or "").lower()
        cats = " ".join(clean(c.text) for c in item.findall("category"))
        tree = HTMLParser(desc_html) if desc_html else None
        desc_text = clean(desc_html)
        text = f"{title} {host} {cats} {desc_text[:1500]}"
        # Title and host only: Engage categories ("Science and/or Technology", "Employment and/or Careers") are
        # so broad that a quizbowl practice would count as tech.
        if not title or not keep(source, text, f"{title} {host}"):
            continue
        start = to_zone(_rfc822(item.findtext(f"{EVENTS_NS}start")), source.timezone)
        end = to_zone(_rfc822(item.findtext(f"{EVENTS_NS}end")), source.timezone)
        confidence, evidence = "structured", None
        if start is None and tree is not None:
            t = tree.css_first("time.dt-start, time.dtstart")
            if t is not None and t.attributes.get("datetime"):
                start, _ = parse_structured(t.attributes["datetime"], source.timezone)
                e = tree.css_first("time.dt-end, time.dtend")
                end = parse_structured(e.attributes.get("datetime"), source.timezone)[0] if e is not None else None
        all_day = False
        if start is None:
            parsed = parse_when(desc_text, source.timezone, infer_year=bool(source.options.get("infer_year")))
            if parsed:
                start, end, all_day = parsed.start, parsed.end, parsed.all_day
                confidence, evidence = parsed.confidence, parsed.evidence
            else:
                confidence, evidence = "none", desc_text[:300]
        cand = Candidate(
            source_id=source.id,
            adapter="rss",
            url=link or source.options.get("landing_url") or source.url,
            title=title,
            start=start,
            end=end,
            all_day=all_day,
            timezone=source.timezone,
            uid=(item.findtext("guid") or link or None),
            organizer=host or None,
            venue=location or None,
            cancelled=status == "cancelled" or "(cancelled)" in (item.findtext("title") or "").lower(),
            text=text,
            date_confidence=confidence,
            date_evidence=evidence,
        )
        if confidence == "none":
            cand.review_reasons.append("no date could be parsed with confidence")
        res.candidates.append(cand)
    return res


class RssAdapter(Adapter):
    name = "rss"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        r = fetcher.get(source.url, source_id=source.id, accept="application/rss+xml, application/xml")
        res = parse_rss(r.text, source)
        res.pages = 1
        return res


def get_path(obj: Any, path: str | None) -> Any:
    """Dotted path lookup with list indexes: "acf.cu_event_start_date", "additionDetails.0.text"."""
    if not path:
        return None
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            if not part.isdigit() or int(part) >= len(cur):
                return None
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur


def _text(v: Any) -> str:
    if isinstance(v, list):
        return " ".join(_text(x) for x in v)
    if isinstance(v, dict):
        return clean(str(v.get("rendered") or v.get("text") or v.get("name") or ""))
    return clean(str(v)) if v is not None else ""


def parse_json_items(payload: Any, source: Source) -> AdapterResult:
    """Field mapping from source.options:
    items (path to the list, default: the payload itself), id, title, url, start, end, all_day, location,
    text (list of paths used for keyword rules only)."""
    o = source.options
    res = AdapterResult()
    items = get_path(payload, o["items"]) if o.get("items") else payload
    for it in items or []:
        res.raw_count += 1
        title = _text(get_path(it, o.get("title", "title")))
        texts = " ".join(_text(get_path(it, p)) for p in o.get("text", []))
        venue = _text(get_path(it, o["location"])) if o.get("location") else ""
        text = f"{title} {texts} {venue}"
        if not title or not keep(source, text, title):
            continue
        start, all_day = parse_structured(_norm_dt(get_path(it, o.get("start", "start"))), source.timezone)
        end, _ = parse_structured(_norm_dt(get_path(it, o.get("end", "end"))), source.timezone)
        if o.get("all_day"):
            all_day = str(get_path(it, o["all_day"])).lower() in ("true", "1", "yes")
        cand = Candidate(
            source_id=source.id,
            adapter="api",
            url=str(get_path(it, o.get("url", "url")) or o.get("landing_url") or source.url),
            title=title,
            start=start,
            end=end if end and start and end >= start else None,
            all_day=all_day,
            timezone=source.timezone,
            uid=f"{source.id}:{get_path(it, o.get('id', 'id'))}",
            venue=venue or None,
            text=text,
            date_confidence="structured" if start else "none",
        )
        if start is None:
            cand.review_reasons.append("no start date in the feed item")
            cand.date_evidence = json.dumps({k: get_path(it, o.get(k, k)) for k in ("start", "end")}, default=str)
        res.candidates.append(cand)
    return res


def _norm_dt(v: Any) -> str | None:
    """Normalise common machine formats: '2026-10-27 11:00:00' and '2026-11-24T12:30-0500'."""
    if v in (None, "", False):
        return None
    s = str(v).strip()
    s = re.sub(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})", r"\1T\2", s)
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
    return s


def _with_page(url: str, page: int) -> str:
    p = urlsplit(url)
    q = dict(parse_qsl(p.query))
    q["page"] = str(page)
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), ""))


class JsonAdapter(Adapter):
    """options.paginate: "wp" follows WordPress REST pages (X-WP-TotalPages); otherwise a single request."""

    name = "json"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        res = AdapterResult()
        page, total = 1, 1
        while page <= total:
            url = _with_page(source.url, page) if source.options.get("paginate") == "wp" else source.url
            try:
                r = fetcher.get(url, source_id=source.id, accept="application/json")
            except BudgetExceeded:
                res.errors.append("page budget reached; results are partial")
                break
            res.pages += 1
            part = parse_json_items(json.loads(r.text), source)
            res.candidates += part.candidates
            res.raw_count += part.raw_count
            if source.options.get("paginate") != "wp":
                break
            total = int(r.headers.get("x-wp-totalpages", "1") or 1)
            page += 1
        return res
