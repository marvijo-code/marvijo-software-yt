import html
import json
import sys

TPL = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title><style>
body {{ margin:0; background:#0b0f14; color:#e6edf3; font-family:'Segoe UI',system-ui,sans-serif; padding:28px; }}
h1 {{ font-size:22px; margin:0 0 4px; }} .sub {{ color:#8b949e; margin-bottom:20px; font-size:14px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.card {{ background:#11161d; border:1px solid #232b36; border-radius:12px; padding:18px; }}
.card.winner {{ border-color:#2ea04366; box-shadow:0 0 0 1px #2ea04366; }}
.model {{ font-size:17px; font-weight:600; }} .badge {{ float:right; font-size:12px; padding:3px 10px; border-radius:99px; background:#1f6feb33; color:#79c0ff; }}
.badge.win {{ background:#2ea04333; color:#56d364; }}
.stats {{ display:flex; gap:22px; margin:14px 0; }} .stat b {{ display:block; font-size:22px; }} .stat span {{ color:#8b949e; font-size:12px; }}
.bar {{ height:8px; background:#21262d; border-radius:4px; overflow:hidden; margin:6px 0 14px; }}
.bar i {{ display:block; height:100%; background:linear-gradient(90deg,#238636,#2ea043); }}
.bar i.partial {{ background:linear-gradient(90deg,#9e6a03,#d29922); }}
pre {{ background:#0d1117; border:1px solid #232b36; border-radius:8px; padding:12px; font-size:11px; line-height:1.5; overflow:hidden; white-space:pre-wrap; max-height:340px; color:#9da7b3; }}
.verdict {{ margin-top:22px; background:#11161d; border:1px solid #232b36; border-radius:12px; padding:16px 18px; font-size:15px; }}
.verdict b {{ color:#56d364; }} .notes {{ font-size:13px; color:#8b949e; margin-top:8px; }}
</style></head><body>
<h1>{header}</h1><div class="sub">{sub}</div>
<div class="grid">{cards}</div>
<div class="verdict">🏆 Round winner: <b>{winner}</b><div class="notes">{verdict_notes}</div></div>
</body></html>"""

CARD = """<div class="card {wincls}"><span class="badge {bwin}">{badge}</span><div class="model">{name}</div>
<div class="stats"><div class="stat"><b>{passed}/{total}</b><span>hidden tests</span></div>
<div class="stat"><b>{time}</b><span>wall clock</span></div>{extra}</div>
<div class="bar"><i class="{barcls}" style="width:{pct}%"></i></div>
<pre>{output}</pre></div>"""


def card(m, win):
    pct = 100 * m["passed"] / max(m["total"], 1)
    extra = "".join(
        f'<div class="stat"><b>{html.escape(str(v))}</b><span>{html.escape(k)}</span></div>'
        for k, v in m.get("extra", {}).items())
    return CARD.format(
        wincls="winner" if win else "", bwin="win" if win else "",
        badge="WINNER" if win else "", name=html.escape(m["name"]),
        passed=m["passed"], total=m["total"], time=html.escape(m["time"]),
        extra=extra, pct=pct, barcls="" if pct == 100 else "partial",
        output=html.escape(m["output"][-2200:]))


d = json.load(open(sys.argv[1], encoding="utf-8"))
cards = "".join(card(m, m["name"] == d["winner"]) for m in d["models"])
open(sys.argv[2], "w", encoding="utf-8").write(TPL.format(
    title=d["header"], header=d["header"], sub=html.escape(d["sub"]),
    cards=cards, winner=html.escape(d["winner"]),
    verdict_notes=html.escape(d["verdict_notes"])))
print("wrote", sys.argv[2])
