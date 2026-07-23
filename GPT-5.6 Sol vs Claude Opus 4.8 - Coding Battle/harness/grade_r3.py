"""Run inside a model's r3 workdir: python ../../grade_r3.py"""
import json
import random
import sys
import time

sys.path.insert(0, ".")
import naive  # noqa: E402

results = []
try:
    import fastcount
except Exception as e:
    print(f"IMPORT FAIL: {e}")
    print("SCORE 0/7 time=NA")
    sys.exit()

# 5 independent small correctness cases
rng = random.Random(1234)
small_pass = 0
for i in range(5):
    pts = [(rng.randint(0, 1000), rng.randint(0, 1000)) for _ in range(500)]
    rcs = []
    for _ in range(50):
        x1, x2 = sorted(rng.randint(0, 1000) for _ in range(2))
        y1, y2 = sorted(rng.randint(0, 1000) for _ in range(2))
        rcs.append((x1, y1, x2, y2))
    exp = naive.count_points_in_rects(pts, rcs)
    try:
        got = fastcount.count_points_in_rects(pts, rcs)
        ok = list(got) == exp
    except Exception as e:
        ok = False
        print(f"  case {i}: EXC {e}")
    small_pass += ok
    print(f"small case {i}: {'PASS' if ok else 'FAIL'}")

# big case timed
d = json.load(open("data_big.json"))
pts = [tuple(p) for p in d["points"]]
rcs = [tuple(r) for r in d["rects"]]
t0 = time.perf_counter()
res = fastcount.count_points_in_rects(pts, rcs)
elapsed = time.perf_counter() - t0
print(f"big case: {elapsed:.2f}s for {len(rcs)} rects / {len(pts)} points")

# spot-verify 25 random rects against naive
rng2 = random.Random(99)
idxs = rng2.sample(range(len(rcs)), 25)
exp_spot = naive.count_points_in_rects(pts, [rcs[i] for i in idxs])
spot_ok = all(res[i] == e for i, e in zip(idxs, exp_spot)) and len(res) == len(rcs)
print(f"spot-check 25 rects: {'PASS' if spot_ok else 'FAIL'}")
budget_ok = elapsed < 30.0
print(f"budget <30s: {'PASS' if budget_ok else 'FAIL'}")
score = small_pass + (1 if spot_ok else 0) + (1 if budget_ok else 0)
print(f"SCORE {score}/7 time={elapsed:.2f}")
