# GPT-5.6 Sol vs Claude Opus 4.8 - 15-Round Coding Battle

A head-to-head benchmark of **GPT-5.6 Sol** (via the Codex CLI) against **Claude Opus 4.8**
(via headless Claude Code), both at **high reasoning effort**, on 15 coding tasks across three
difficulty tiers - including 5 **real, closed bugs** from large open-source GitHub repos graded
by the maintainers' own fix-PR tests.

Every task was graded by a hidden test suite written *before* either model ran. Each model got
an identical prompt, an isolated working directory, and was wall-clock timed. Ties break on
tests first, then wall clock.

## Final result: Claude Opus 4.8 wins 9-6

| | GPT-5.6 Sol | Opus 4.8 |
|---|---|---|
| **Rounds won** | 6 | **9** |
| **Hidden tests passed** | **145 / 152** | 140 / 152 |
| **Total wall clock** | 2785s | **1988s (29% less)** |

Two clear profiles emerged, confirmed across all 15 rounds:

- **GPT-5.6 Sol - the correctness specialist.** The only model to pass every synthetic test
  (134/134 on rounds 1-10), highest overall test count, and the only model to beat the click
  baseline - its wider fixes cover user-facing scenarios that minimal patches miss. Slower,
  roughly 2x, on real-repo work.
- **Claude Opus 4.8 - the real-world workhorse.** On real bugs in big codebases it located the
  right line and shipped maintainer-identical fixes 2.1-3.7x faster than Sol at equal quality.
  Its known failure mode: preferring the narrow targeted patch when the maintainers chose a
  broader redesign (round 12, click).

## The three tiers

### Tier 1 - Straightforward (rounds 1-5): 3-2 Sol
Build-from-spec and debugging tasks graded by hidden `pytest`/Playwright suites.

| # | Task | Sol | Opus | Winner |
|---|---|---|---|---|
| 1 | Mini spreadsheet engine (formulas, ranges, cycles) | 15/15 · 310.6s | 15/15 · 324.3s | Sol (time) |
| 2 | eventlib bug hunt (6 planted bugs) | **14/14** · 187.1s | 13/14 · 69.7s | Sol (6/6 bugs) |
| 3 | Rectangle point-counting (200k pts, <30s) | 7/7 · 115.1s | 7/7 · 71.5s | Opus (1.6x) |
| 4 | Airport departures board (DOM contract) | 11/11 · 287.8s | 11/11 · 107.2s | Opus (2.7x) |
| 5 | Cron `next_run` calculator (POSIX edge cases) | 26/26 · 131.5s | 26/26 · 137.9s | Sol (time) |

### Tier 2 - Advanced (rounds 6-10): 3-2 Opus (5-5 cumulative)
Concurrency, language implementation, protocols, algorithms at scale, type theory.

| # | Task | Sol | Opus | Winner |
|---|---|---|---|---|
| 6 | Async job scheduler (deps, cancellation, retries) | 12/12 · 221.5s | 12/12 · 171.6s | Opus (23%) |
| 7 | MiniLang interpreter (closures + proper tail calls) | **14/14** · 291.0s | 13/14 · 340.9s | Sol (scope bug) |
| 8 | DNS wire-format codec (compression pointers) | 12/12 · 116.6s | 12/12 · 99.9s | Opus (14%) |
| 9 | Distinct substrings on 500k chars (<60s) | 8/8 · 112.9s | 8/8 · 123.4s | Sol (time) |
| 10 | Hindley-Milner type inference (Algorithm W) | 15/15 · 141.9s | 15/15 · 117.0s | Opus (18%) |

### Tier 3 - Real GitHub bugs (rounds 11-15): 4-1 Opus
Real closed bugs; models saw only the issue text + a pristine checkout, graded by the
maintainers' actual fix-PR tests. Each task was pre-validated solvable by an independent agent
(fail-at-base, pass-at-merge, and solved from scratch).

| # | Repo (stars) | Bug | Sol | Opus | Winner |
|---|---|---|---|---|---|
| 11 | psf/requests (52k) | [#4795](https://github.com/psf/requests/issues/4795) greedy `no_proxy` | 1/1 · 216.8s | 1/1 · 57.9s | Opus (3.7x) |
| 12 | pallets/click (16k) | [#2819](https://github.com/pallets/click/issues/2819) param named `help` | **5/11** · 291.8s | 2/11 · 128.6s | Sol (only one above baseline) |
| 13 | pydantic/pydantic (24k) | [#12424](https://github.com/pydantic/pydantic/issues/12424) `exclude_if` schema | 0/1 · 134.8s | 0/1 · 92.2s | Opus (double miss, time) |
| 14 | Textualize/rich (52k) | [#4041](https://github.com/Textualize/rich/issues/4041) `FileProxy.isatty` | 4/4 · 104.3s | 4/4 · 50.2s | Opus (2.1x) |
| 15 | sympy/sympy (13k) | [#28219](https://github.com/sympy/sympy/issues/28219) `Pow.as_real_imag` | 1/1 · 121.0s | 1/1 · 95.3s | Opus (21%) |

Notable: round 12 (click) is the one round where thorough functional coverage beat a fast
minimal patch - the maintainers reserved an internal name neither model guessed, but Sol's wider
fix still lifted the 2/11 baseline to 5/11 while Opus's narrow patch stayed at baseline. Round 13
(pydantic) is the series' only double miss: both fixed the reported case but missed an unstated
config-flag interaction the hidden test also pins.

## Layout

```
report/
  bench_report.html        Full standalone report (open in a browser) - every scorecard + verdict
  scorecards/              Per-round side-by-side scorecard PNGs + the departures-board UIs
  summaries/               Machine-readable per-round results (JSON)
synthetic-rounds/
  round-01..10/            task.md (the spec), test_hidden.py (the grader), starter/ files,
                           and each model's solution under sol/ and opus/
real-repo-rounds/
  round-11..15/            task.md (verbatim issue), meta.json (SHAs, grade tests, validation),
                           tests.patch (the maintainers' test-only diff = the hidden grader),
                           sol_fix.patch + opus_fix.patch (each model's source fix)
harness/
  make_scorecard.py        Renders a round's summary JSON to an HTML scorecard
  make_report.py           Assembles the full report from all summaries + screenshots
  grade_r3.py / grade_r9.py  Standalone graders for the perf/algorithms rounds
  grade_r4.mjs             Playwright browser grader for the departures board
  prompt.txt               The identical instruction both models received
```

## Methodology

1. Hidden tests authored before either model ran; models saw only the task spec (or, for real
   rounds, the verbatim GitHub issue) plus starter files.
2. Both models run in isolated working directories, identical prompt (`harness/prompt.txt`),
   wall-clock timed.
3. Synthetic rounds graded with `pytest` (or Playwright for the UI round). Real rounds graded by
   applying `tests.patch` (the maintainers' own tests) and running the specified node IDs plus a
   regression module.

### Reproducing a round

Synthetic (example, round 1):
```bash
cd synthetic-rounds/round-01-spreadsheet-engine
cp sol/sheet.py .          # or opus/sheet.py
python -m pytest test_hidden.py -q
```

Real-repo (example, round 14 - rich):
```bash
# clone rich at the base commit listed in meta.json, create a venv, pip install -e . pytest
git apply tests.patch      # injects the maintainers' hidden test
git apply opus_fix.patch   # or sol_fix.patch (each model's source fix)
python -m pytest tests/test_file_proxy.py -q
```
See each round's `meta.json` for the exact base/merge SHAs, grade-test node IDs, extra
dependencies, and the exact grading command.

> Rounds 3 and 9 ship without their large generated data files (`data_big.json`, `data_big.txt`);
> regenerate them with the generators referenced in each `task.md`. Real-repo rounds ship the
> fix diffs and specs, not the full multi-hundred-MB checkouts + virtualenvs.

## How the models were driven

- **GPT-5.6 Sol:** `codex exec --skip-git-repo-check -m gpt-5.6-sol -c model_reasoning_effort="high" "<prompt>"`
- **Claude Opus 4.8:** `claude -p "<prompt>" --model claude-opus-4-8 --effort high --dangerously-skip-permissions`

---

Part of the [Marvijo AI Software](https://www.youtube.com/@MarvijoSoftware) YouTube channel resources.
