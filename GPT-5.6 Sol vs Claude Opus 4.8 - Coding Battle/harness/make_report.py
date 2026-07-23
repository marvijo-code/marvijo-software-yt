import base64
import pathlib

sh = pathlib.Path("results/shots/small")


def b64(name):
    return "data:image/png;base64," + base64.b64encode((sh / name).read_bytes()).decode()


rounds = [
 ("Round 1", "Algorithms & spec correctness - mini spreadsheet engine",
  "15 hidden pytest tests: formulas, ranges, cycles, error propagation. Both models: 15/15. Sol 310.6s, Opus 324.3s.",
  "SOL", "time only, +4%", "r1_scorecard-01.png", None),
 ("Round 2", "Debugging - 6 planted bugs in eventlib.py",
  "Docstrings were the spec. Sol fixed all 6 bugs (14/14, 187.1s). Opus was 2.7x faster (69.7s) but left the touching-intervals merge bug (13/14).",
  "SOL", "correctness: 6/6 vs 5/6 bugs", "r2_scorecard-01.png", None),
 ("Round 3", "Performance - 200k points x 2k rects, stdlib only, under 30s",
  "Both independently wrote an offline x-sweep with a Fenwick tree over compressed y and finished ~50x under budget (0.48s / 0.58s). Opus shipped it in 62% of Sol's wall clock.",
  "OPUS", "1.6x faster, same algorithm", "r3_scorecard-01.png", None),
 ("Round 4", "Frontend build-to-spec - airport departures board",
  "Strict DOM contract graded by 11 Playwright checks: sorting + aria-sort, live filter, singular '1 flight', 4 distinct chip colors. Both 11/11 and genuinely polished; Opus 107.2s vs Sol 287.8s.",
  "OPUS", "2.7x faster, equal polish", "r4_scorecard-01.png", ("r4_board_sol-01.png", "r4_board_opus-01.png")),
 ("Round 5 - tiebreaker", "Edge-case correctness - cron next_run calculator",
  "The minefield: dom/dow OR rule, dow 7 = Sunday, Feb 29 2028, day-31 month skipping, 10 validation cases. Both 26/26; Sol 131.5s vs Opus 137.9s.",
  "SOL", "time only, +5%", "r5_scorecard-01.png", None),
 ("Round 6 - advanced set", "Async concurrency - job scheduler with deps, cancellation, retries",
  "asyncio semantics graded exactly: dependency DAG, peak-concurrency ceiling of 3, retry attempt counts, fail_fast cancelling in-flight jobs vs continue skip-propagation, cycle detection. Both 12/12; Opus 171.6s vs Sol 221.5s.",
  "OPUS", "23% faster", "r6_scorecard-01.png", None),
 ("Round 7 - advanced set", "Language implementation - MiniLang interpreter with proper tail calls",
  "Full lexer/parser/evaluator with closures, line-numbered errors, and mandatory TCO at 200,000-deep recursion. Sol 14/14 and faster; Opus 13/14 - its if-blocks don't open a new lexical scope, so an inner 'let x' clobbered the enclosing x.",
  "SOL", "correctness + speed", "r7_scorecard-01.png", None),
 ("Round 8 - advanced set", "Binary protocols - DNS wire-format codec",
  "Nested compression-pointer chains, CNAME decompression, byte-exact query building, and four malicious fixtures (pointer loop, forward pointer, truncation, oversized label) that must raise. Both 12/12; Opus 99.9s vs Sol 116.6s.",
  "OPUS", "14% faster", "r8_scorecard-01.png", None),
 ("Round 9 - advanced set", "Algorithms at scale - distinct substrings on 500k chars",
  "Exact count 124,989,998,315 + longest repeat 185 under a 60s budget (naive is hopeless). Both exact with ~1s linear-time constructions; Sol 112.9s dev vs Opus 123.4s (whose solution ran faster, 0.81s vs 0.98s). The closest round.",
  "SOL", "9% faster dev", "r9_scorecard-01.png", None),
 ("Round 10 - advanced set", "Type theory - Hindley-Milner inference (Algorithm W)",
  "Character-exact principal types: let-polymorphism vs lambda monomorphism, occurs check, letrec, canonical variable naming. Both 15/15; Opus 117.0s vs Sol 141.9s. Series ends 5-5.",
  "OPUS", "18% faster", "r10_scorecard-01.png", None),
 ("Round 11 - real repo", "psf/requests #4795 - no_proxy matching is too greedy",
  "Real closed bug: no_proxy=gle.com wrongly bypassed www.google.com. Both shipped maintainer-equivalent domain-boundary matching with all 228 module tests green. Opus in 57.9s vs Sol 216.8s - the largest speed gap of the series.",
  "OPUS", "3.7x faster", "rw1_scorecard-01.png", None),
 ("Round 12 - real repo", "pallets/click #2819 - a parameter named 'help' breaks parsing",
  "The maintainers' 11 hidden tests pin a reserved '_click_default_help' name neither model guessed. Sol's wider +23-line fix solved the reported collisions and lifted the 2/11 baseline to 5/11; Opus's rename-on-collision patch stayed at the buggy-base 2/11.",
  "SOL", "only model above baseline", "rw2_scorecard-01.png", None),
 ("Round 13 - real repo", "pydantic #12424 - exclude_if fields wrongly required in serialization schema",
  "The only double miss of the series: both fixed the reported case but neither inferred the json_schema_serialization_defaults_required interaction the hidden test also pins. Both kept 525 regressions green; Opus faster (92.2s vs 134.8s).",
  "OPUS", "double miss; clock decides", "rw3_scorecard-01.png", None),
 ("Round 14 - real repo", "Textualize/rich #4041 - FileProxy.isatty() always False",
  "MRO trap: TextIOBase.isatty shadows __getattr__ delegation. Both wrote the exact 3-line override the maintainers shipped; all 4 hidden tests green. Opus in 50.2s vs Sol 104.3s.",
  "OPUS", "2.1x faster, identical fix", "rw4_scorecard-01.png", None),
 ("Round 15 - real repo", "sympy #28219 - Pow.as_real_imag inconsistent for Pow(0, -1)",
  "Both navigated the 2M-line codebase to Pow.as_real_imag's real-base short-circuit and added the same zero-base guard. Hidden test + 44 module tests green for both; Opus 95.3s vs Sol 121.0s.",
  "OPUS", "21% faster", "rw5_scorecard-01.png", None),
]

cards = []
for tag, title, blurb, winner, margin, shot, boards in rounds:
    wincls = "sol" if winner == "SOL" else "opus"
    winname = "GPT-5.6 Sol" if winner == "SOL" else "Opus 4.8"
    b = ""
    if boards:
        b = (f'<div class="boards"><figure><img src="{b64(boards[0])}" alt="Sol board" loading="lazy">'
             f'<figcaption>Sol&#39;s board</figcaption></figure>'
             f'<figure><img src="{b64(boards[1])}" alt="Opus board" loading="lazy">'
             f'<figcaption>Opus&#39;s board</figcaption></figure></div>')
    cards.append(f'''<section class="round">
<div class="rhead"><span class="eyebrow">{tag}</span><span class="winchip {wincls}">{winname} &middot; {margin}</span></div>
<h2>{title}</h2><p>{blurb}</p>
<img class="shot" src="{b64(shot)}" alt="{tag} scorecard" loading="lazy">{b}</section>''')

css = """
:root { --bg:#0d1219; --panel:#131a24; --line:#25303f; --ink:#dde5ee; --dim:#8896a8;
  --sol:#6cb2ff; --opus:#c99aff; --gold:#e3b341; }
body { background:var(--bg); color:var(--ink); font-family:'Segoe UI',system-ui,sans-serif; line-height:1.6; }
.wrap { max-width:1080px; margin:0 auto; padding:48px 28px 80px; }
header h1 { font-size:clamp(26px,4vw,40px); line-height:1.15; margin:0 0 10px; text-wrap:balance; letter-spacing:-0.02em; }
header h1 .vs { color:var(--dim); font-weight:400; } header h1 .s { color:var(--sol); } header h1 .o { color:var(--opus); }
.sub { color:var(--dim); max-width:65ch; margin:0 0 26px; }
.verdict { border:1px solid var(--line); border-left:3px solid var(--gold); background:var(--panel); border-radius:10px; padding:18px 22px; margin-bottom:14px; }
.verdict b { color:var(--gold); }
table { border-collapse:collapse; width:100%; margin:26px 0 40px; font-size:14px; }
th,td { border-bottom:1px solid var(--line); padding:9px 12px; text-align:left; }
th { color:var(--dim); font-size:11px; text-transform:uppercase; letter-spacing:.08em; font-weight:600; }
td.num { font-family:Consolas,monospace; font-variant-numeric:tabular-nums; white-space:nowrap; }
td.w-sol { color:var(--sol); font-weight:600; } td.w-opus { color:var(--opus); font-weight:600; }
.tblwrap { overflow-x:auto; }
.round { margin:52px 0; }
.rhead { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.eyebrow { color:var(--dim); font-size:12px; text-transform:uppercase; letter-spacing:.12em; font-weight:600; }
.winchip { font-size:12px; padding:4px 12px; border-radius:99px; border:1px solid var(--line); background:var(--panel); }
.winchip.sol { color:var(--sol); border-color:#6cb2ff44; } .winchip.opus { color:var(--opus); border-color:#c99aff44; }
.round h2 { font-size:20px; margin:8px 0 6px; text-wrap:balance; }
.round p { color:var(--dim); max-width:72ch; margin:0 0 16px; }
.shot, .boards img { width:100%; border:1px solid var(--line); border-radius:10px; display:block; }
.boards { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:14px; }
.boards figure { margin:0; } .boards figcaption { color:var(--dim); font-size:12px; margin-top:6px; text-align:center; }
@media (max-width:760px) { .boards { grid-template-columns:1fr; } }
footer { color:var(--dim); font-size:13px; border-top:1px solid var(--line); margin-top:56px; padding-top:18px; }
"""

table = """<div class="tblwrap"><table>
<tr><th>Round</th><th>Category</th><th>GPT-5.6 Sol</th><th>Opus 4.8</th><th>Winner</th></tr>
<tr><td>1 &middot; Spreadsheet engine</td><td>Algorithms / spec</td><td class="num">15/15 &middot; 310.6s</td><td class="num">15/15 &middot; 324.3s</td><td class="w-sol">Sol (time)</td></tr>
<tr><td>2 &middot; eventlib bug hunt</td><td>Debugging</td><td class="num">14/14 &middot; 187.1s</td><td class="num">13/14 &middot; 69.7s</td><td class="w-sol">Sol (6/6 bugs)</td></tr>
<tr><td>3 &middot; Rect point-counting</td><td>Performance</td><td class="num">7/7 &middot; 115.1s</td><td class="num">7/7 &middot; 71.5s</td><td class="w-opus">Opus (1.6x faster)</td></tr>
<tr><td>4 &middot; Departures board</td><td>Frontend</td><td class="num">11/11 &middot; 287.8s</td><td class="num">11/11 &middot; 107.2s</td><td class="w-opus">Opus (2.7x faster)</td></tr>
<tr><td>5 &middot; Cron next_run</td><td>Edge cases</td><td class="num">26/26 &middot; 131.5s</td><td class="num">26/26 &middot; 137.9s</td><td class="w-sol">Sol (time)</td></tr>
<tr><td>6 &middot; Async job scheduler</td><td>Concurrency</td><td class="num">12/12 &middot; 221.5s</td><td class="num">12/12 &middot; 171.6s</td><td class="w-opus">Opus (23% faster)</td></tr>
<tr><td>7 &middot; MiniLang interpreter</td><td>Language impl + TCO</td><td class="num">14/14 &middot; 291.0s</td><td class="num">13/14 &middot; 340.9s</td><td class="w-sol">Sol (scope bug found)</td></tr>
<tr><td>8 &middot; DNS wire codec</td><td>Binary protocols</td><td class="num">12/12 &middot; 116.6s</td><td class="num">12/12 &middot; 99.9s</td><td class="w-opus">Opus (14% faster)</td></tr>
<tr><td>9 &middot; Distinct substrings 500k</td><td>Algorithms at scale</td><td class="num">8/8 &middot; 112.9s</td><td class="num">8/8 &middot; 123.4s</td><td class="w-sol">Sol (time)</td></tr>
<tr><td>10 &middot; Hindley-Milner</td><td>Type theory</td><td class="num">15/15 &middot; 141.9s</td><td class="num">15/15 &middot; 117.0s</td><td class="w-opus">Opus (18% faster)</td></tr>
<tr><td>11 &middot; requests #4795</td><td>Real repo: proxy logic</td><td class="num">1/1 &middot; 216.8s</td><td class="num">1/1 &middot; 57.9s</td><td class="w-opus">Opus (3.7x faster)</td></tr>
<tr><td>12 &middot; click #2819</td><td>Real repo: CLI parsing</td><td class="num">5/11 &middot; 291.8s</td><td class="num">2/11 &middot; 128.6s</td><td class="w-sol">Sol (above baseline)</td></tr>
<tr><td>13 &middot; pydantic #12424</td><td>Real repo: JSON schema</td><td class="num">0/1 &middot; 134.8s</td><td class="num">0/1 &middot; 92.2s</td><td class="w-opus">Opus (double miss, time)</td></tr>
<tr><td>14 &middot; rich #4041</td><td>Real repo: MRO bug</td><td class="num">4/4 &middot; 104.3s</td><td class="num">4/4 &middot; 50.2s</td><td class="w-opus">Opus (2.1x faster)</td></tr>
<tr><td>15 &middot; sympy #28219</td><td>Real repo: CAS math</td><td class="num">1/1 &middot; 121.0s</td><td class="num">1/1 &middot; 95.3s</td><td class="w-opus">Opus (21% faster)</td></tr>
<tr><td><b>Grand total (15 rounds)</b></td><td></td><td class="num"><b>145/152 &middot; 2785s</b></td><td class="num"><b>140/152 &middot; 1988s</b></td><td class="w-opus"><b>Opus 9-6</b></td></tr>
</table></div>"""

html = (
    '<title>GPT-5.6 Sol vs Opus 4.8 - 15-Round Coding Bench</title>\n'
    f'<style>{css}</style>\n<div class="wrap">\n<header>\n'
    '<h1><span class="s">GPT-5.6 Sol</span> <span class="vs">vs</span> '
    '<span class="o">Claude Opus 4.8</span><br>15-round coding benchmark</h1>\n'
    '<p class="sub">Both at high reasoning effort, identical prompts, isolated workdirs, '
    'wall-clock timed. Rounds 1-5: straightforward set. Rounds 6-10: advanced set (async '
    'concurrency, language implementation, binary protocols, algorithms at scale, type '
    'theory). Rounds 11-15: REAL closed bugs in requests, click, pydantic, rich and sympy - '
    'models saw only the issue text + repo, graded by the maintainers&#39; actual fix-PR '
    'tests, every task pre-validated solvable by an independent agent. Sol ran via Codex '
    'CLI, Opus via headless Claude Code. 2026-07-23.</p>\n'
    '<div class="verdict"><b>Final: Opus 4.8 wins 9-6</b> - the real-repo set flipped a 5-5 '
    'tie (Opus took it 4-1). Aggregate: Sol 145/152 tests in 2785s; Opus 140/152 in 1988s '
    '(29% less). <b>Sol = the correctness specialist</b>: perfect on all synthetic rounds, '
    'top test count, and the only model to beat the click baseline - its wide fixes cover '
    'scenarios minimal patches miss. <b>Opus = the real-world workhorse</b>: on real bugs in '
    'big codebases it shipped maintainer-identical fixes 2.1-3.7x faster, winning requests, '
    'rich, sympy and pydantic. Its known failure mode: preferring the narrow targeted patch '
    'when maintainers wanted a broader redesign (click). Both models missed the same '
    'unstated config-flag interaction on pydantic - the series&#39; only double miss.'
    '</div>\n</header>\n'
    + table + "\n" + "".join(cards) +
    '\n<section class="round"><div class="rhead"><span class="eyebrow">Final verdict</span></div>\n'
    f'<img class="shot" src="{b64("final_verdict15-01.png")}" alt="Final verdict card" loading="lazy"></section>\n'
    '<footer>Method: hidden tests authored before any model ran; both models saw only task.md + '
    'starter files. Wall clock includes each agent&#39;s own testing/verification.</footer>\n</div>'
)
pathlib.Path("results/bench_report.html").write_text(html, encoding="utf-8")
print("bytes:", len(html))
