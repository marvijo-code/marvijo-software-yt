from datetime import datetime, timedelta

import pytest
from cronnext import next_run


def _next_day(after, pred, hour=0, minute=0):
    """Independent reference: first day d (searching forward from after's
    date) with pred(d) true whose hour:minute is strictly after `after`."""
    d = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if d <= after:
        d += timedelta(days=1)
    while not pred(d):
        d += timedelta(days=1)
    return d


def test_every_minute_truncates_seconds():
    assert next_run("* * * * *", datetime(2026, 3, 10, 10, 30, 15)) == \
        datetime(2026, 3, 10, 10, 31)


def test_strictly_after():
    assert next_run("* * * * *", datetime(2026, 3, 10, 10, 30)) == \
        datetime(2026, 3, 10, 10, 31)


def test_daily_time_wraps_to_next_day():
    assert next_run("30 9 * * *", datetime(2026, 3, 10, 9, 30)) == \
        datetime(2026, 3, 11, 9, 30)


def test_step_minutes():
    assert next_run("*/15 * * * *", datetime(2026, 3, 10, 10, 50)) == \
        datetime(2026, 3, 10, 11, 0)


def test_range_with_step():
    assert next_run("10-40/10 * * * *", datetime(2026, 3, 10, 10, 40)) == \
        datetime(2026, 3, 10, 11, 10)


def test_open_step_from_value():
    # 45/5 in minutes = 45,50,55
    assert next_run("45/5 * * * *", datetime(2026, 3, 10, 10, 56)) == \
        datetime(2026, 3, 10, 11, 45)


def test_list_minutes():
    assert next_run("5,20,35 14 * * *", datetime(2026, 3, 10, 14, 21)) == \
        datetime(2026, 3, 10, 14, 35)


def test_year_wrap():
    assert next_run("0 0 1 1 *", datetime(2026, 12, 31, 23, 59)) == \
        datetime(2027, 1, 1, 0, 0)


def test_leap_feb_29():
    assert next_run("0 0 29 2 *", datetime(2026, 3, 1)) == \
        datetime(2028, 2, 29, 0, 0)


def test_dom_only():
    assert next_run("0 12 15 * *", datetime(2026, 7, 16)) == \
        datetime(2026, 8, 15, 12, 0)


def test_dow_only_next_monday():
    after = datetime(2026, 7, 23, 9, 30)
    exp = _next_day(after, lambda d: d.weekday() == 0, hour=9, minute=0)
    assert next_run("0 9 * * 1", after) == exp


def test_dow_seven_is_sunday():
    after = datetime(2026, 7, 23, 9, 30)
    exp = _next_day(after, lambda d: d.weekday() == 6)
    assert next_run("0 0 * * 7", after) == exp


def test_dom_dow_both_restricted_is_or():
    # fires on the 13th OR on Fridays
    after = datetime(2026, 7, 1, 0, 0)
    exp = _next_day(after, lambda d: d.day == 13 or d.weekday() == 4)
    assert next_run("0 0 13 * 5", after) == exp
    # and from just before the 13th, the 13th itself if sooner than a Friday
    after2 = datetime(2026, 10, 12, 5, 0)
    exp2 = _next_day(after2, lambda d: d.day == 13 or d.weekday() == 4)
    assert next_run("0 0 13 * 5", after2) == exp2


def test_day_31_skips_short_months():
    assert next_run("0 0 31 * *", datetime(2026, 4, 5)) == \
        datetime(2026, 5, 31, 0, 0)


def test_weekday_range():
    after = datetime(2026, 7, 24, 9, 0)  # a Friday, exactly 09:00
    exp = _next_day(after, lambda d: d.weekday() <= 4, hour=9, minute=0)
    assert next_run("0 9 * * 1-5", after) == exp


def test_hour_list_with_minute_step():
    assert next_run("*/20 8,18 * * *", datetime(2026, 3, 10, 18, 40)) == \
        datetime(2026, 3, 11, 8, 0)


@pytest.mark.parametrize("expr", [
    "* * * *",            # wrong field count
    "60 * * * *",         # minute out of range
    "* 24 * * *",         # hour out of range
    "* * 0 * *",          # dom out of range
    "* * * 13 *",         # month out of range
    "* * * * 8",          # dow out of range
    "5-1 * * * *",        # reversed range
    "*/0 * * * *",        # zero step
    "a * * * *",          # garbage
    ",5 * * * *",         # empty item
])
def test_validation(expr):
    with pytest.raises(ValueError):
        next_run(expr, datetime(2026, 1, 1))
