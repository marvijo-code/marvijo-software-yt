# Task: Distinct substrings at scale

Create `distinct.py` in this directory exporting:

```python
def count_distinct_substrings(s: str) -> int
def longest_repeated_substring(s: str) -> int   # length of the longest
                                                # substring occurring >= 2 times
                                                # (0 if none)
```

Both must be EXACT (no hashing-with-collisions tricks that can be wrong).

## Performance requirement
`data_big.txt` in this directory (UTF-8, single line, 500,000 chars, natural
repetitive English-like text) is the graded workload. Grading on this
machine, CPython 3.13:
```python
s = open("data_big.txt", encoding="utf-8").read()
t0 = time.perf_counter()
d = count_distinct_substrings(s)
r = longest_repeated_substring(s)
elapsed = time.perf_counter() - t0
```
- HARD BUDGET: `elapsed` under 60 seconds (the naive approaches are
  O(n^2) memory/time and are hopeless at n = 500k). Measured time is part
  of your score.
- Correctness is cross-checked against brute force on many small strings
  and against an independent reference on the big file.

## Rules
- CPython 3.13 **stdlib only**, single process, no multiprocessing.
- sys.setrecursionlimit is allowed but beware of the C stack; prefer
  iterative algorithms.
- Work only in this directory. Hard cap: finish within 10 minutes of wall
  clock. You may test/time your solution yourself.
