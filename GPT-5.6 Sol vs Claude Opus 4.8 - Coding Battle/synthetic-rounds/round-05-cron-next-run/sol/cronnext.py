"""A small, dependency-free calculator for five-field cron expressions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import re


@dataclass(frozen=True)
class _Field:
    values: frozenset[int]
    unrestricted: bool = False


_NUMBER = re.compile(r"\d+\Z")
_RANGE = re.compile(r"(\d+)-(\d+)\Z")
_STAR_STEP = re.compile(r"\*/\d+\Z")


def _number(text: str) -> int:
    if not _NUMBER.fullmatch(text):
        raise ValueError(f"invalid numeric value: {text!r}")
    return int(text)


def _parse_field(text: str, minimum: int, maximum: int, *, day_of_week: bool = False) -> _Field:
    if not text:
        raise ValueError("empty cron field")

    values: set[int] = set()
    for item in text.split(","):
        if not item:
            raise ValueError("empty item in cron field")

        parts = item.split("/")
        if len(parts) > 2 or not parts[0] or (len(parts) == 2 and not parts[1]):
            raise ValueError(f"malformed step: {item!r}")

        base = parts[0]
        step = 1
        if len(parts) == 2:
            step = _number(parts[1])
            if step < 1:
                raise ValueError("step must be at least 1")

        if base == "*":
            start, end = minimum, maximum
        else:
            match = _RANGE.fullmatch(base)
            if match:
                start, end = int(match.group(1)), int(match.group(2))
                if start > end:
                    raise ValueError(f"descending range: {base!r}")
            else:
                start = _number(base)
                end = maximum if len(parts) == 2 else start

            if start < minimum or start > maximum or end < minimum or end > maximum:
                raise ValueError(f"value outside {minimum}-{maximum}: {base!r}")

        for value in range(start, end + 1, step):
            values.add(0 if day_of_week and value == 7 else value)

    # Per the specified POSIX day rule, only a whole-field wildcard (possibly
    # stepped) is unrestricted.  A list such as "*,1" is not that form.
    unrestricted = text == "*" or _STAR_STEP.fullmatch(text) is not None
    return _Field(frozenset(values), unrestricted)


def _day_matches(day: date, dom: _Field, dow: _Field) -> bool:
    dom_matches = day.day in dom.values
    # datetime.weekday(): Monday=0; cron: Sunday=0, Monday=1, ...
    dow_matches = (day.weekday() + 1) % 7 in dow.values

    if not dom.unrestricted and not dow.unrestricted:
        return dom_matches or dow_matches
    if not dom.unrestricted:
        return dom_matches
    if not dow.unrestricted:
        return dow_matches
    return True


def next_run(expr: str, after: datetime) -> datetime:
    """Return the first minute boundary strictly after *after* matching *expr*."""

    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("cron expression must contain exactly five fields")

    minute = _parse_field(fields[0], 0, 59)
    hour = _parse_field(fields[1], 0, 23)
    dom = _parse_field(fields[2], 1, 31)
    month = _parse_field(fields[3], 1, 12)
    dow = _parse_field(fields[4], 0, 7, day_of_week=True)

    first = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    hours = sorted(hour.values)
    minutes = sorted(minute.values)
    current_day = first.date()

    while True:
        if current_day.month in month.values and _day_matches(current_day, dom, dow):
            for candidate_hour in hours:
                for candidate_minute in minutes:
                    candidate = datetime.combine(
                        current_day,
                        time(candidate_hour, candidate_minute),
                        tzinfo=after.tzinfo,
                    )
                    if candidate >= first:
                        return candidate
        current_day += timedelta(days=1)
