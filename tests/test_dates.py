from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from openroster.extract.dates import find_deadline, has_ambiguous_date, parse_when

TOR = ZoneInfo("America/Toronto")
TODAY = date(2026, 10, 23)


def p(text, **kw):
    return parse_when(text, "America/Toronto", today=TODAY, **kw)


def test_full_date_with_time_range_and_tz():
    r = p("University of Waterloo (Sep 21, 2026, 11:30am-1:30pm ET)")
    assert r.start == datetime(2026, 9, 21, 11, 30, tzinfo=TOR)
    assert r.end == datetime(2026, 9, 21, 13, 30, tzinfo=TOR)
    assert r.confidence == "explicit" and not r.all_day


def test_weekday_and_long_month():
    r = p("Friday, November 28, 2026 at 6:00 PM")
    assert r.start == datetime(2026, 11, 28, 18, 0, tzinfo=TOR)


def test_range_across_months():
    r = p("Hack the North runs Nov 28 – Dec 1, 2026 in Waterloo")
    assert r.start.date() == date(2026, 11, 28) and r.end.date() == date(2026, 12, 1)
    assert r.all_day


def test_dmy():
    r = p("Applications: 28 November 2026")
    assert r.start.date() == date(2026, 11, 28)


def test_missing_year_is_not_guessed_by_default():
    assert p("Join us Nov 28 at 5pm") is None


def test_missing_year_inferred_only_when_source_opts_in():
    r = p("Join us Nov 28 at 5pm", infer_year=True)
    assert r.start == datetime(2026, 11, 28, 17, 0, tzinfo=TOR)
    assert r.confidence == "inferred_year"
    r2 = p("Workshop: Feb 3, 6-8pm", infer_year=True)
    assert r2.start == datetime(2027, 2, 3, 18, 0, tzinfo=TOR)
    assert r2.end == datetime(2027, 2, 3, 20, 0, tzinfo=TOR)


def test_pacific_time_zone():
    r = p("Dec 2, 2026 10am PT")
    assert r.timezone == "America/Vancouver"
    # Offsets come from tzdata (BC's switch to permanent Pacific time is in recent tzdata), never hard-coded.
    assert r.start == datetime(2026, 12, 2, 10, 0, tzinfo=ZoneInfo("America/Vancouver"))


def test_lowercase_at_is_not_a_time_zone():
    assert p("Meet at 5pm on Nov 28, 2026").timezone == "America/Toronto"
    assert p("Nov 28, 2026 5pm Atlantic Time").timezone == "America/Halifax"


def test_dst_is_respected():
    summer = p("Jul 10, 2026 9:00 AM")
    winter = p("Jan 10, 2027 9:00 AM")
    assert summer.start.utcoffset() != winter.start.utcoffset()


def test_iso():
    r = p("2026-11-04T17:30")
    assert r.start == datetime(2026, 11, 4, 17, 30, tzinfo=TOR)


@pytest.mark.parametrize("text", ["11/12/2026", "on 3/4/26"])
def test_numeric_dates_are_ambiguous(text):
    assert has_ambiguous_date(text)
    assert p(text) is None


def test_invalid_date_rejected():
    assert p("February 30, 2027") is None


def test_deadline():
    r = find_deadline("Mentor applications close November 30, 2026. Event is Jan 10, 2027.", "America/Toronto",
                      today=TODAY)
    assert r.start.date() == date(2026, 11, 30) and r.start.hour == 23
