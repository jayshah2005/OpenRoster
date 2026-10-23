"""Rule-based date extraction. Nothing here guesses: if a rule cannot fire with confidence, it returns None
and the caller marks the record needs_review with the evidence text.

Confidence levels:
- "explicit": day, month and year are all present in the text (or the value came from a structured field).
- "inferred_year": day and month are present, and the source config allows inferring the year as the
  next occurrence (`options.infer_year: upcoming`). Allowed only when the source opts in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
_DAY = r"(\d{1,2})(?:st|nd|rd|th)?"
_YEAR = r"(20\d{2})"
_DASH = r"\s*(?:-|–|—|to|until|through)\s*"
_WEEKDAY = r"(?:(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)[a-z]*\.?,?\s+)?"

# "Nov 28, 2026" / "November 28 - 30, 2026" / "Nov 28 – Dec 1, 2026" / "Friday, November 28"
MDY = re.compile(
    rf"\b{_WEEKDAY}{_MON}\s+{_DAY}(?:{_DASH}(?:{_WEEKDAY}{_MON}\s+)?{_DAY})?(?:,?\s+{_YEAR})?\b",
    re.I,
)
# "28 November 2026" / "28-30 Nov 2026"
DMY = re.compile(rf"\b{_WEEKDAY}{_DAY}(?:{_DASH}{_DAY})?\s+{_MON}(?:,?\s+{_YEAR})?\b", re.I)
ISO_DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::\d{2})?)?\b")
# 11/12/2026 style dates are ambiguous between US and Canadian/UK order: never parsed, always reviewed.
AMBIGUOUS_NUMERIC = re.compile(r"\b\d{1,2}/\d{1,2}/(?:20)?\d{2}\b")

_T = r"(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?"
TIME_RANGE = re.compile(rf"\b{_T}\s*(?:-|–|—|to)\s*{_T}", re.I)
TIME_ONE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)", re.I)
TIME_24 = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")

# Short abbreviations must be uppercase ("at 5pm" is not Atlantic Time); AT and NT are too ambiguous
# to accept at all, so Atlantic and Newfoundland need the spelled-out form.
TZ_ABBR = {
    "ET": "America/Toronto", "EST": "America/Toronto", "EDT": "America/Toronto",
    "PT": "America/Vancouver", "PST": "America/Vancouver", "PDT": "America/Vancouver",
    "CT": "America/Chicago", "CST": "America/Chicago", "CDT": "America/Chicago",
    "MT": "America/Edmonton", "MST": "America/Edmonton", "MDT": "America/Edmonton",
    "AST": "America/Halifax", "ADT": "America/Halifax", "NST": "America/St_Johns", "NDT": "America/St_Johns",
}
TZ_NAMES = {
    "eastern": "America/Toronto", "pacific": "America/Vancouver", "central": "America/Chicago",
    "mountain": "America/Edmonton", "atlantic": "America/Halifax", "newfoundland": "America/St_Johns",
}
TZ_RE = re.compile(r"\b(" + "|".join(TZ_ABBR) + r")\b")
# Uppercase AT / NT are accepted only right after a time ("4:00pm AT", "10 AM (NT)").
TZ_AFTER_TIME = re.compile(r"(?:[apAP]\.?[mM]\.?|\d)\s*\(?(AT|NT)\)?(?![A-Za-z])")
_AFTER_TIME_ZONES = {"AT": "America/Halifax", "NT": "America/St_Johns"}
TZ_NAME_RE = re.compile(r"\b(" + "|".join(TZ_NAMES) + r")(?:\s+(?:standard|daylight))?\s+time\b", re.I)


@dataclass
class DateParse:
    start: datetime
    end: datetime | None
    all_day: bool
    confidence: str
    evidence: str
    timezone: str


def _month(s: str) -> int:
    return MONTHS[s[:3].lower()]


def _to_24(h: str, m: str | None, ampm: str | None) -> time | None:
    hour, minute = int(h), int(m or 0)
    if ampm:
        a = ampm.lower().replace(".", "")
        if not 1 <= hour <= 12:
            return None
        if a == "pm" and hour != 12:
            hour += 12
        if a == "am" and hour == 12:
            hour = 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return time(hour, minute)


def _times(text: str) -> tuple[time | None, time | None]:
    m = TIME_RANGE.search(text)
    if m and (m.group(3) or m.group(6)):
        h1, m1, a1, h2, m2, a2 = m.groups()
        # "6-8pm": the meridiem of the end applies to the start
        a1 = a1 or a2
        t1, t2 = _to_24(h1, m1, a1), _to_24(h2, m2, a2)
        if t1 and t2 and t2 < t1 and not m.group(3):
            # "11-1pm" -> 11am-1pm
            t1 = _to_24(h1, m1, "am")
        return t1, t2
    m1 = TIME_ONE.search(text)
    if m1:
        return _to_24(*m1.groups()), None
    m2 = TIME_24.search(text)
    if m2:
        return time(int(m2.group(1)), int(m2.group(2))), None
    return None, None


def _resolve_year(month: int, day: int, today: date) -> int:
    """Next occurrence: a date up to 30 days in the past still counts as this year (events already listed)."""
    for year in (today.year, today.year + 1):
        try:
            d = date(year, month, day)
        except ValueError:
            continue
        if d >= today - timedelta(days=30):
            return year
    return today.year + 1


def _snippet(text: str, start: int, end: int, pad: int = 60) -> str:
    s = text[max(0, start - pad) : min(len(text), end + pad)]
    return re.sub(r"\s+", " ", s).strip()[:300]


def parse_when(
    text: str,
    default_tz: str,
    *,
    infer_year: bool = False,
    today: date | None = None,
) -> DateParse | None:
    """Parse the first date (or date range) in free text. Returns None unless a rule fires confidently."""
    if not text:
        return None
    today = today or date.today()
    tzname = default_tz
    if tzm := TZ_RE.search(text):
        tzname = TZ_ABBR[tzm.group(1)]
    elif tza := TZ_AFTER_TIME.search(text):
        tzname = _AFTER_TIME_ZONES[tza.group(1)]
    elif tzn := TZ_NAME_RE.search(text):
        tzname = TZ_NAMES[tzn.group(1).lower()]
    tz = ZoneInfo(tzname)

    candidates: list[tuple[int, int, date, date | None, bool]] = []  # (pos, end, d1, d2, year_explicit)
    iso_times: dict[int, time] = {}

    for m in ISO_DATE.finditer(text):
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if m.group(4):
                iso_times[m.start()] = time(int(m.group(4)), int(m.group(5)))
        except ValueError:
            continue
        candidates.append((m.start(), m.end(), d, None, True))

    for m in MDY.finditer(text):
        mon1, d1, mon2, d2, yr = m.groups()
        cand = _build(mon1, d1, mon2 or (mon1 if d2 else None), d2, yr, infer_year, today)
        if cand:
            candidates.append((m.start(), m.end(), *cand))

    for m in DMY.finditer(text):
        d1, d2, mon, yr = m.groups()
        cand = _build(mon, d1, mon if d2 else None, d2, yr, infer_year, today)
        if cand:
            candidates.append((m.start(), m.end(), *cand))

    if not candidates:
        return None
    pos, endpos, d1, d2, year_explicit = min(candidates, key=lambda c: c[0])
    # Times are looked for close to the date only, so a time elsewhere on the page is not attached to it.
    window = text[endpos : endpos + 60] + " " + text[max(0, pos - 40) : pos]
    t1, t2 = (iso_times[pos], None) if pos in iso_times else _times(window)
    evidence = _snippet(text, pos, endpos)
    conf = "explicit" if year_explicit else "inferred_year"

    if t1 is None:
        start = datetime.combine(d1, time(0, 0), tz)
        end = datetime.combine(d2, time(23, 59), tz) if d2 else None
        return DateParse(start, end, True, conf, evidence, tzname)
    start = datetime.combine(d1, t1, tz)
    if d2:
        end = datetime.combine(d2, t2 or time(23, 59), tz)
    elif t2:
        end = datetime.combine(d1, t2, tz)
        if end < start:
            end += timedelta(days=1)
    else:
        end = None
    return DateParse(start, end, False, conf, evidence, tzname)


def _build(
    mon1: str, d1: str, mon2: str | None, d2: str | None, yr: str | None, infer_year: bool, today: date
) -> tuple[date, date | None, bool] | None:
    try:
        m1 = _month(mon1)
        if yr:
            y1 = int(yr)
        elif infer_year:
            y1 = _resolve_year(m1, int(d1), today)
        else:
            return None
        start = date(y1, m1, int(d1))
        end = None
        if d2:
            m2 = _month(mon2) if mon2 else m1
            y2 = y1 + 1 if m2 < m1 else y1
            end = date(y2, m2, int(d2))
            if end < start:
                return None
    except (ValueError, KeyError):
        return None
    return start, end, bool(yr)


def has_ambiguous_date(text: str) -> bool:
    return bool(AMBIGUOUS_NUMERIC.search(text or ""))


DEADLINE_HINT = re.compile(
    r"(deadline|apply by|applications? (?:close|due|open)|due|closes?|register by|registration (?:closes|ends)|until)",
    re.I,
)


def find_deadline(text: str, default_tz: str, *, infer_year: bool = False, today: date | None = None) -> DateParse | None:
    """A date that appears within 80 characters after a deadline phrase."""
    for m in DEADLINE_HINT.finditer(text or ""):
        window = text[m.start() : m.end() + 80]
        p = parse_when(window, default_tz, infer_year=infer_year, today=today)
        if p:
            if p.all_day:
                # "apply by Nov 30" means the end of that day
                p.start = p.start.replace(hour=23, minute=59)
            return p
    return None
