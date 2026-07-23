# Task: Cron "next run" calculator (Python)

Create `cronnext.py` in this directory exporting:

```python
def next_run(expr: str, after: datetime) -> datetime
```

Returns the earliest datetime STRICTLY AFTER `after` at which the cron
expression fires. Result has second=0, microsecond=0 (cron fires on minute
boundaries; `after` may carry seconds - e.g. every-minute cron after
10:30:15 fires 10:31:00).

## Expression format
5 whitespace-separated fields: `minute hour day-of-month month day-of-week`.
- Allowed values: minute 0-59, hour 0-23, day-of-month 1-31, month 1-12,
  day-of-week 0-7 where BOTH 0 and 7 mean Sunday (1=Monday ... 6=Saturday).
- Each field is a comma-separated list of items. An item is:
  - `*` - all values
  - `N` - a single value
  - `A-B` - inclusive range (A <= B)
  - `*/S`, `A-B/S`, `A/S` - step values (for `A/S` the range runs from A to
    the field maximum). S >= 1.
- No names (jan/mon), no `L/W/#` extensions.

## Semantics
- Standard (POSIX) cron day rule: if BOTH day-of-month and day-of-week are
  restricted (i.e. neither is `*` or a `*/S` form starting from `*`), a day
  matches when EITHER field matches. If only one is restricted, that one
  must match. If neither is restricted, every day matches.
- Months without a day-31 simply don't fire for day-of-month 31, etc.
  (search continues into later months/years; every test has a firing within
  5 years).

## Validation
Raise `ValueError` for: wrong field count, out-of-range values, empty items,
malformed ranges/steps (e.g. `5-1`, step 0), non-numeric garbage.

Python 3.13, stdlib only. Work in this directory only. Hidden tests follow
this spec strictly. You may write and run your own tests.
