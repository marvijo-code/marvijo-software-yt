"""Run inside a model's r9 workdir: python ../../grade_r9.py"""
import json
import random
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "../..")  # not used; expected file read directly

try:
    from distinct import count_distinct_substrings, longest_repeated_substring
except Exception as e:
    print(f"IMPORT FAIL: {e}")
    print("SCORE 0/8 time=NA")
    sys.exit()


def brute(s):
    subs = set()
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n + 1):
            subs.add(s[i:j])
    lrs = 0
    for L in range(n - 1, 0, -1):
        seen = set()
        hit = False
        for i in range(n - L + 1):
            t = s[i:i + L]
            if t in seen:
                hit = True
                break
            seen.add(t)
        if hit:
            lrs = L
            break
    return len(subs), lrs


rng = random.Random(555)
score = 0
for i in range(6):
    if i < 3:
        n = rng.randint(1, 80)
        s = "".join(rng.choice("ab") for _ in range(n))
    else:
        n = rng.randint(100, 400)
        s = "".join(rng.choice("abcde ") for _ in range(n))
    exp = brute(s)
    try:
        got = (count_distinct_substrings(s), longest_repeated_substring(s))
        ok = got == exp
    except Exception as e:
        ok = False
        print(f"  case {i}: EXC {e}")
    score += ok
    print(f"small case {i} (n={len(s)}): {'PASS' if ok else 'FAIL'}"
          + ("" if ok else f" exp={exp} got={got}"))

s = open("data_big.txt", encoding="utf-8").read()
exp = json.load(open("../expected_big.json"))
t0 = time.perf_counter()
d = count_distinct_substrings(s)
r = longest_repeated_substring(s)
elapsed = time.perf_counter() - t0
big_ok = (d == exp["distinct"] and r == exp["lrs"])
budget_ok = elapsed < 60.0
score += big_ok + budget_ok
print(f"big case: {elapsed:.2f}s  distinct={d} lrs={r}  "
      f"{'PASS' if big_ok else 'FAIL (exp %s %s)' % (exp['distinct'], exp['lrs'])}")
print(f"budget <60s: {'PASS' if budget_ok else 'FAIL'}")
print(f"SCORE {score}/8 time={elapsed:.2f}")
