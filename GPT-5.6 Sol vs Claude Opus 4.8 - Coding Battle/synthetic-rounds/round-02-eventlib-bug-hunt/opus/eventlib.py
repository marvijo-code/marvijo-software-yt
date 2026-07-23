"""eventlib - tiny calendar utilities.

Times are minutes since midnight (int). Days are ISO date strings 'YYYY-MM-DD'.
The docstrings in this module are the authoritative spec.
"""
from datetime import date, timedelta


def _parse_day(s):
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def parse_event(s):
    """Parse 'YYYY-MM-DD HH:MM-HH:MM Title with spaces' into a dict
    {'day': 'YYYY-MM-DD', 'start': int, 'end': int, 'title': str}.

    start/end are minutes since midnight. Raise ValueError if the string
    is malformed or if the event would be empty or negative (end <= start).
    """
    try:
        day, times, title = s.split(" ", 2)
        t1, t2 = times.split("-")
        h1, m1 = t1.split(":")
        h2, m2 = t2.split(":")
        start = int(h1) * 60 + int(m1)
        end = int(h2) * 60 + int(m2)
        _parse_day(day)
    except ValueError as e:
        raise ValueError(f"bad event string: {s!r}") from e
    if end <= start:
        raise ValueError("event must have positive duration")
    return {"day": day, "start": start, "end": end, "title": title}


def expand(event, recur=None):
    """Expand an event into its occurrences.

    recur is None (single occurrence) or {'freq': 'daily'|'weekly',
    'until': 'YYYY-MM-DD'} where 'until' is INCLUSIVE (an occurrence
    landing exactly on 'until' is included).

    Returns a list of event dicts. Each occurrence must be an independent
    copy of the input event (mutating one occurrence, or the input, must
    not affect the others), with 'day' set to the occurrence's date.
    The input event dict itself must not be mutated.
    """
    if recur is None:
        return [dict(event)]
    until = _parse_day(recur["until"])
    step = timedelta(days=1) if recur["freq"] == "daily" else timedelta(days=7)
    out = []
    d = _parse_day(event["day"])
    while d <= until:
        occ = dict(event)
        occ["day"] = d.isoformat()
        out.append(occ)
        d = d + step
    return out


def merge_busy(intervals):
    """Merge a list of (start, end) minute intervals.

    Input may be unsorted and overlapping. Returns a sorted list of
    disjoint intervals. Touching intervals merge: (60,120) and (120,180)
    become (60,180).
    """
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda t: t[0])
    merged = [list(ordered[0])]
    for s, e in ordered[1:]:
        cur = merged[-1]
        if s >= cur[1]:
            merged.append([s, e])
        else:
            cur[1] = max(cur[1], e)
    return [tuple(x) for x in merged]


def free_slots(intervals, day_start, day_end):
    """Return the free gaps within [day_start, day_end] as a sorted list of
    (start, end) tuples, given busy intervals (unsorted/overlapping allowed,
    all within the day window). Zero-length gaps are excluded.
    """
    busy = merge_busy(intervals)
    out = []
    cursor = day_start
    for s, e in busy:
        if s > cursor:
            out.append((cursor, s))
        cursor = max(cursor, e)
    if day_end > cursor:
        out.append((cursor, day_end))
    return out
