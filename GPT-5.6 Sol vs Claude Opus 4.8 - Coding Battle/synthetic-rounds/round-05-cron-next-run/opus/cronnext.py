"""Cron "next run" calculator.

Exports next_run(expr, after) which returns the earliest datetime strictly
after `after` at which a standard 5-field cron expression fires.
"""

from datetime import datetime, timedelta


def _parse_field(field, lo, hi):
    """Parse one cron field into (set_of_values, is_unrestricted).

    is_unrestricted is True iff every item is `*` or `*/S` (POSIX star form).
    """
    if field == "":
        raise ValueError("empty field")
    values = set()
    unrestricted = True
    for item in field.split(","):
        if item == "":
            raise ValueError("empty item")
        base = item
        step = 1
        has_step = False
        if "/" in item:
            base, _, step_s = item.partition("/")
            if step_s == "" or "/" in step_s or not step_s.isdigit():
                raise ValueError("malformed step")
            step = int(step_s)
            if step < 1:
                raise ValueError("step < 1")
            has_step = True

        if base == "*":
            start, end = lo, hi
            item_unrestricted = True
        elif "-" in base:
            a_s, b_s = base.split("-", 1)
            if "-" in b_s or not a_s.isdigit() or not b_s.isdigit():
                raise ValueError("malformed range")
            start, end = int(a_s), int(b_s)
            if start > end:
                raise ValueError("range start > end")
            item_unrestricted = False
        else:
            if not base.isdigit():
                raise ValueError("non-numeric value")
            n = int(base)
            if has_step:
                start, end = n, hi
            else:
                start, end = n, n
            item_unrestricted = False

        if start < lo or end > hi:
            raise ValueError("value out of range")

        for v in range(start, end + 1, step):
            values.add(v)
        if not item_unrestricted:
            unrestricted = False

    return values, unrestricted


def _next_month(dt):
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1, day=1, hour=0, minute=0)
    return dt.replace(month=dt.month + 1, day=1, hour=0, minute=0)


def _day_matches(dt, dom_vals, dow_vals, dom_restricted, dow_restricted):
    dom = dt.day
    cron_dow = (dt.weekday() + 1) % 7  # Python Mon=0..Sun=6 -> cron Sun=0..Sat=6
    if dom_restricted and dow_restricted:
        return dom in dom_vals or cron_dow in dow_vals
    if dom_restricted:
        return dom in dom_vals
    if dow_restricted:
        return cron_dow in dow_vals
    return True


def next_run(expr: str, after: datetime) -> datetime:
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("expected 5 fields")

    minute_vals, _ = _parse_field(fields[0], 0, 59)
    hour_vals, _ = _parse_field(fields[1], 0, 23)
    dom_vals, dom_unres = _parse_field(fields[2], 1, 31)
    month_vals, _ = _parse_field(fields[3], 1, 12)
    dow_vals, dow_unres = _parse_field(fields[4], 0, 7)

    if 7 in dow_vals:  # both 0 and 7 mean Sunday
        dow_vals = set(dow_vals)
        dow_vals.discard(7)
        dow_vals.add(0)

    dom_restricted = not dom_unres
    dow_restricted = not dow_unres

    candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = candidate + timedelta(days=366 * 5 + 2)

    while candidate <= limit:
        if candidate.month not in month_vals:
            candidate = _next_month(candidate)
            continue
        if not _day_matches(candidate, dom_vals, dow_vals, dom_restricted, dow_restricted):
            candidate = candidate.replace(hour=0, minute=0) + timedelta(days=1)
            continue
        if candidate.hour not in hour_vals:
            candidate = candidate.replace(minute=0) + timedelta(hours=1)
            continue
        if candidate.minute not in minute_vals:
            candidate = candidate + timedelta(minutes=1)
            continue
        return candidate

    raise ValueError("no matching run within 5 years")
