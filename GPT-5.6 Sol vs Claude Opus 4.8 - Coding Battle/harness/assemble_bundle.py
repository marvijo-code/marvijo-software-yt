import shutil
import pathlib

B = pathlib.Path(r"C:\Users\marvi\AppData\Local\Temp\claude\C--dev-marvijo-betting-solution\fdfd562f-c41b-4c34-9ac3-616cfe7415ab\scratchpad\bench")
DEST = pathlib.Path(r"C:\dev\marvijo-software-yt\GPT-5.6 Sol vs Claude Opus 4.8 - Coding Battle")

if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir(parents=True)


def cp(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dst)
        return True
    return False


# --- Synthetic rounds 1-10 ---
SYN = {
 "r1": ("round-01-spreadsheet-engine", ["sheet.py"]),
 "r2": ("round-02-eventlib-bug-hunt", ["eventlib.py"]),
 "r3": ("round-03-rect-point-counting", ["fastcount.py"]),
 "r4": ("round-04-departures-board", ["index.html"]),
 "r5": ("round-05-cron-next-run", ["cronnext.py"]),
 "r6": ("round-06-async-job-scheduler", ["scheduler.py"]),
 "r7": ("round-07-minilang-interpreter", ["minilang.py"]),
 "r8": ("round-08-dns-wire-codec", ["dnscodec.py"]),
 "r9": ("round-09-distinct-substrings", ["distinct.py"]),
 "r10": ("round-10-hindley-milner", ["hm.py"]),
}
for rd, (name, outfiles) in SYN.items():
    d = DEST / "synthetic-rounds" / name
    cp(B / rd / "task.md", d / "task.md")
    cp(B / rd / "test_hidden.py", d / "test_hidden.py")
    # starter/reference files present at round root (not task/test/solutions)
    for extra in ["eventlib.py", "naive.py", "data.js", "ref_sam.py"]:
        if rd in ("r2",) and extra == "eventlib.py":
            cp(B / rd / extra, d / "starter" / extra)
        if rd == "r3" and extra == "naive.py":
            cp(B / rd / extra, d / "starter" / extra)
        if rd == "r4" and extra == "data.js":
            cp(B / rd / extra, d / "starter" / extra)
        if rd == "r9" and extra == "ref_sam.py":
            cp(B / rd / extra, d / "reference" / extra)
    for m in ("sol", "opus"):
        for of in outfiles:
            cp(B / rd / f"work_{m}" / of, d / m / of)

# --- Real-repo rounds 11-15 ---
REAL = {
 "rw1": "round-11-requests-4795-no_proxy",
 "rw2": "round-12-click-2819-param-named-help",
 "rw3": "round-13-pydantic-12424-exclude_if-schema",
 "rw4": "round-14-rich-4041-fileproxy-isatty",
 "rw5": "round-15-sympy-28219-pow-as_real_imag",
}
for rd, name in REAL.items():
    d = DEST / "real-repo-rounds" / name
    cp(B / rd / "task.md", d / "task.md")
    cp(B / rd / "meta.json", d / "meta.json")
    cp(B / rd / "tests.patch", d / "tests.patch")
    for m in ("sol", "opus"):
        cp(B / rd / f"{m}_fix.patch", d / f"{m}_fix.patch")

# --- Harness / graders ---
H = DEST / "harness"
for f in ["make_scorecard.py", "make_report.py", "grade_r3.py", "grade_r4.mjs",
          "grade_r9.py", "prompt.txt", "assemble_bundle.py"]:
    cp(B / f, H / f)

# --- Report + scorecards ---
R = DEST / "report"
cp(B / "results" / "bench_report.html", R / "bench_report.html")
shots = B / "results" / "shots" / "small"
sc = R / "scorecards"
sc.mkdir(parents=True, exist_ok=True)
for png in sorted(shots.glob("*.png")):
    shutil.copy2(png, sc / png.name)

# summaries json
for js in sorted((B / "results").glob("*_summary.json")):
    cp(js, R / "summaries" / js.name)

print("bundle assembled at", DEST)
