# Task: Fast rectangle point-counting

`naive.py` in this directory is the CORRECT reference implementation of
`count_points_in_rects(points, rects)` (borders inclusive). It is far too slow.

Write `fastcount.py` in this directory exporting the same function
`count_points_in_rects(points, rects)` returning identical results.

## Performance requirement
`data_big.json` in this directory holds the exact grading workload:
`{"points": [[x,y],...], "rects": [[x1,y1,x2,y2],...]}` with 200,000 points
and 2,000 large rectangles (coordinates 0..1,000,000).

Grading (on this machine, CPython 3.13):
```python
import json, time, fastcount
d = json.load(open("data_big.json"))
pts = [tuple(p) for p in d["points"]]; rcs = [tuple(r) for r in d["rects"]]
t0 = time.perf_counter(); res = fastcount.count_points_in_rects(pts, rcs)
elapsed = time.perf_counter() - t0
```
- Results must exactly match the naive reference (checked on random subsets
  and independent small cases).
- HARD BUDGET: `elapsed` must be under 30 seconds. Faster is better - the
  measured time is part of your score.

## Rules
- CPython 3.13 **stdlib only** (no numpy). Single process (no multiprocessing).
- Pure algorithmic speedup. Do not precompute anything outside the timed
  function call. Do not read data_big.json from inside fastcount.py.
- Work in this directory only. You may test/time your solution yourself.
