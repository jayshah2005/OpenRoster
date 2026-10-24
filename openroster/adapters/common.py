"""Helpers shared by adapters."""

from __future__ import annotations

import html
import re
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from dateutil import parser as dtparser
from selectolax.lexbor import LexborHTMLParser as HTMLParser

from ..config import Source
from ..extract.classify import is_cs_relevant

_WS = re.compile(r"\s+")
_URL = re.compile(r"https?://[^\s<>\"')\]]+")


def clean(text: str | None) -> str:
    if not text:
        return ""
    if "<" in text and ">" in text:
        tree = HTMLParser(text)
        text = tree.body.text(separator=" ") if tree.body else tree.text(separator=" ")
    return _WS.sub(" ", html.unescape(text)).strip()


def first_url(text: str | None) -> str | None:
    if not text:
        return None
    m = _URL.search(text)
    return m.group(0).rstrip(".,;") if m else None


def keep(source: Source, text: str, title: str | None = None) -> bool:
    """Relevance filter configured per source.

    options.filter: "all" keeps everything (dedicated CS/tech sources); "cs" (default for campus-wide
    calendars) keeps items that match CS/tech/career keywords (see extract/classify.py: broad words count only in
    `title`, which adapters pass as title + host + categories). options.include / options.exclude are extra
    regexes applied on top.
    """
    opts = source.options
    for rx in opts.get("exclude", []):
        if re.search(rx, text, re.I):
            return False
    for rx in opts.get("include", []):
        if re.search(rx, text, re.I):
            return True
    mode = opts.get("filter", "all")
    if mode == "all":
        return not opts.get("include")
    return is_cs_relevant(text, title)


def parse_structured(value: str | None, tz: str) -> tuple[datetime | None, bool]:
    """Parse an ISO-like structured datetime (from APIs / JSON-LD). Naive values take the source time zone.

    Returns (datetime, all_day). Structured fields are trusted: they are machine-written, not prose.
    """
    if not value:
        return None, False
    value = value.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            d = date.fromisoformat(value)
            return datetime.combine(d, time(0, 0), ZoneInfo(tz)), True
        dt = dtparser.isoparse(value)
    except (ValueError, OverflowError):
        return None, False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
    return dt, False


def to_zone(dt: datetime | None, tz: str) -> datetime | None:
    return dt.astimezone(ZoneInfo(tz)) if dt else None
