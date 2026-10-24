"""iCalendar feeds: official Luma iCal links, campus and club exports. (Google Calendar feeds are blocked by its robots.txt.)"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import recurring_ical_events
from icalendar import Calendar
from x_wr_timezone import to_standard

from ..config import Source
from ..fetch import Fetcher
from .base import Adapter, AdapterResult, Candidate
from .common import clean, first_url, keep

HORIZON_DAYS = 120


def _as_dt(value: date | datetime, tz: str) -> tuple[datetime, bool]:
    if isinstance(value, datetime):
        if value.tzinfo is None:  # floating time: interpret in the source's zone
            value = value.replace(tzinfo=ZoneInfo(tz))
        return value, False
    return datetime.combine(value, time(0, 0), ZoneInfo(tz)), True


def parse_ics(text: str, source: Source, now: datetime | None = None) -> AdapterResult:
    res = AdapterResult()
    cal = to_standard(Calendar.from_ical(text))
    now = now or datetime.now(UTC)
    cal_tz = str(cal.get("X-WR-TIMEZONE") or source.timezone)
    try:
        ZoneInfo(cal_tz)
    except Exception:
        cal_tz = source.timezone
    events = recurring_ical_events.of(cal).between(now - timedelta(days=1), now + timedelta(days=HORIZON_DAYS))
    for ev in events:
        res.raw_count += 1
        title = clean(str(ev.get("SUMMARY", "")))
        desc = clean(str(ev.get("DESCRIPTION", "")))
        loc = clean(str(ev.get("LOCATION", "")))
        text = f"{title} {desc} {loc}"
        if not title or not keep(source, text):
            continue
        start, all_day = _as_dt(ev.decoded("DTSTART"), cal_tz)
        end = None
        if ev.get("DTEND"):
            end, _ = _as_dt(ev.decoded("DTEND"), cal_tz)
            if all_day:  # DTEND is exclusive for all-day events
                end = end - timedelta(minutes=1)
        uid = str(ev.get("UID", "")) or None
        recurring = ev.get("RRULE") is not None or ev.get("RECURRENCE-ID") is not None
        url = str(ev.get("URL", "")) or first_url(desc) or source.options.get("landing_url") or source.url
        res.candidates.append(
            Candidate(
                source_id=source.id,
                adapter="ics",
                url=url,
                title=title,
                start=start,
                end=end,
                all_day=all_day,
                timezone=cal_tz,
                uid=f"{uid}@{start.isoformat()}" if (uid and recurring) else uid,
                series_id=uid if recurring else None,
                venue=loc or None,
                cancelled=str(ev.get("STATUS", "")).upper() == "CANCELLED",
                text=text,
                date_confidence="structured",
            )
        )
    return res


class IcsAdapter(Adapter):
    name = "ics"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        r = fetcher.get(source.url, source_id=source.id, accept="text/calendar, */*;q=0.5")
        if "BEGIN:VCALENDAR" not in r.text[:2000]:
            out = AdapterResult(pages=1)
            out.errors.append("response is not an iCalendar file")
            return out
        out = parse_ics(r.text, source)
        out.pages = 1
        return out
