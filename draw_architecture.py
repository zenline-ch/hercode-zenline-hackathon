import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(22, 30))
ax.set_xlim(0, 22)
ax.set_ylim(0, 30)
ax.axis("off")
fig.patch.set_facecolor("#0D1117")

BG     = "#0D1117"
CARD   = "#161B27"
CARD2  = "#1C2235"
BLUE   = "#4A90D9"
GREEN  = "#27AE60"
ORANGE = "#E67E22"
RED    = "#E74C3C"
PURPLE = "#8E44AD"
TEAL   = "#16A085"
YELLOW = "#F1C40F"
WHITE  = "#FFFFFF"
MUTED  = "#6B7A99"
DASHED = "#3A4255"

def box(x, y, w, h, fc=CARD, ec="none", lw=1.2, ls="solid", alpha=1.0, r=0.28):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw,
        linestyle=ls, alpha=alpha, zorder=3))

def txt(x, y, s, sz=9, c=WHITE, w="normal", ha="center", va="center"):
    ax.text(x, y, s, fontsize=sz, color=c, ha=ha, va=va, fontweight=w, zorder=5)

def arr(x1, y1, x2, y2, c=BLUE, ls="solid", lw=1.8):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=c, lw=lw,
                        linestyle=ls, connectionstyle="arc3,rad=0.0"), zorder=4)

def section_header(x, y, w, h, color, number, title, subtitle=""):
    box(x, y, w, h, fc=CARD, ec=color, lw=1.0)
    txt(x + 0.55, y + h - 0.32, number, sz=7.5, c=color, w="bold", ha="left")
    txt(x + 1.1,  y + h - 0.32, title,  sz=9,   c=color, w="bold", ha="left")
    if subtitle:
        txt(x + w/2, y + h - 0.58, subtitle, sz=7, c=MUTED)

def chip(x, y, label, color, sz=7.0):
    tw = len(label) * 0.072 + 0.22
    box(x - tw/2, y - 0.13, tw, 0.28, fc=color + "33", ec=color, lw=0.8, r=0.12)
    txt(x, y, label, sz=sz, c=color, w="bold")

def subdim(x, y, w, label, detail, color):
    box(x, y, w, 0.78, fc=BG, ec=color, lw=0.6, r=0.15)
    txt(x + 0.18, y + 0.54, label,  sz=7.8, c=color, w="bold", ha="left")
    txt(x + 0.18, y + 0.22, detail, sz=6.6, c=MUTED,  ha="left")


# ═══════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════
txt(11, 29.55, "Zenline Retail Radar", sz=20, c=WHITE, w="bold")
txt(11, 29.1,  "Reusable opportunity detection pipeline   ·   Swiss outdoor retail demo", sz=9.5, c=MUTED)

# ═══════════════════════════════════════════════════════════════════════════
# 1  Q&A ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 27.1, 21.2, 1.75, BLUE, "①", "Q&A ENTRYPOINT",
               "Produces RetailerContext — single config object consumed by every downstream module")

qa = [
    ("Target Market",      "Switzerland"),
    ("Comparison Markets", "Sweden · Canada · Nordics"),
    ("Niche / Category",   "Outdoor Retailer"),
    ("Demographics",       "Gender · Age range"),
    ("Competitor URLs",    "transa.ch · ochsner-sport.ch"),
    ("Risk Factors",       "Supply chain · Regulatory\nSeasonal · Single-supplier"),
    ("Score Weights",      "Sliders (default: equal)"),
]
sw = 21.2 / len(qa)
for i, (k, v) in enumerate(qa):
    cx = 0.4 + sw * i + sw / 2
    box(cx - sw/2 + 0.1, 27.18, sw - 0.2, 1.05, fc=CARD2, r=0.15)
    txt(cx, 27.87, k, sz=6.8, c=MUTED)
    txt(cx, 27.48, v, sz=7.2, c=WHITE, w="bold")

arr(11, 27.1, 11, 26.7)
txt(12.9, 26.9, "RetailerContext", sz=8.5, c=BLUE, w="bold")

# ═══════════════════════════════════════════════════════════════════════════
# 2  DATA COLLECTION
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 24.45, 21.2, 2.0, TEAL, "②", "DATA COLLECTION",
               "Scrapes comparison markets defined in RetailerContext")

sources = [
    ("Google Trends",    "pytrends",       "Momentum · search slope",     TEAL),
    ("Reddit",           "praw",           "Community buzz · r/outdoor",  TEAL),
    ("Amazon",           "beautifulsoup4", "Marketplace rank & titles",   TEAL),
    ("BFS Open Data",    "requests + JSON","Swiss structural trends",     TEAL),
    ("Competitor Sites", "from Q&A URLs",  "Assortment & pricing gaps",   TEAL),
]
cw = 21.2 / len(sources)
for i, (name, lib, sig, col) in enumerate(sources):
    cx = 0.4 + cw * i + cw / 2
    box(cx - cw/2 + 0.1, 24.55, cw - 0.2, 1.6, fc=CARD2, r=0.18)
    txt(cx, 25.83, name, sz=9,   c=col,  w="bold")
    txt(cx, 25.47, lib,  sz=7,   c=MUTED)
    txt(cx, 25.12, sig,  sz=7.5, c=WHITE)

arr(11, 24.45, 11, 24.05)

# ═══════════════════════════════════════════════════════════════════════════
# 3  FILTER LAYER
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 22.35, 21.2, 1.45, ORANGE, "③", "FILTER LAYER")

box(0.6,  22.45, 10.3, 0.88, fc=CARD2, r=0.18)
txt(1.1,  22.98, "Relevance Filter", sz=8.5, c=ORANGE, w="bold", ha="left")
txt(1.1,  22.65, "Keep signals matching RetailerContext niche and originating from target or comparison markets", sz=7.2, c=WHITE, ha="left")

box(11.1, 22.45, 10.3, 0.88, fc=CARD2, r=0.18)
txt(11.6, 22.98, "Deduplication", sz=8.5, c=ORANGE, w="bold", ha="left")
txt(11.6, 22.65, "Collapse same opportunity across source types · preserve all source_types for breadth counting", sz=7.2, c=WHITE, ha="left")

arr(11, 22.35, 11, 21.95)

# ═══════════════════════════════════════════════════════════════════════════
# 4  SCORING LAYER  —  4 pillars
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 12.7, 21.2, 9.0, PURPLE, "④", "SCORING LAYER",
               "Four pillars · deterministic + LLM-hybrid · equal-weight composite · configurable via sliders")

PW       = 5.0    # pillar width
GAP      = 0.4    # gap between pillars
PY_TOP   = 21.35  # top of pillar content
PH       = 6.8    # pillar height
SD_W     = PW - 0.3  # subdim box width

pillar_xs = [0.4 + i * (PW + GAP) for i in range(4)]   # 0.4, 5.8, 11.2, 16.6
pillar_cx = [x + PW / 2 for x in pillar_xs]            # centres

# ── PILLAR A: TREND SCORE  (Deterministic) ──────────────────────────────────
Ax = pillar_xs[0]; Acx = pillar_cx[0]
box(Ax, PY_TOP - PH, PW, PH, fc="#160E22", ec=PURPLE, lw=0.9, r=0.22)
txt(Acx, PY_TOP - 0.28, "TREND SCORE", sz=9, c=PURPLE, w="bold")
txt(Acx, PY_TOP - 0.55, "Deterministic", sz=6.8, c=MUTED)

subdim(Ax + 0.15, PY_TOP - 1.55, SD_W, "Growth",
       "Google Trends 90d slope · normalized 0-10", PURPLE)

# Trend Stage box (larger, uses remaining space)
box(Ax + 0.15, PY_TOP - PH + 1.2, SD_W, 3.4, fc="#1E1030", ec=PURPLE, lw=0.7, r=0.18)
txt(Acx, PY_TOP - PH + 4.3, "TREND STAGE", sz=8, c=PURPLE, w="bold")
txt(Acx, PY_TOP - PH + 3.95, "derived from Growth score", sz=6.5, c=MUTED)
stage_data = [("Emerging", GREEN), ("Growing", BLUE), ("Mainstream", YELLOW), ("Declining", RED)]
for k, (stage, col2) in enumerate(stage_data):
    sy = PY_TOP - PH + 3.35 - k * 0.68
    chip(Acx, sy, stage, col2, sz=7.5)

# Derived box — Buy Recommendation
box(Ax + 0.15, PY_TOP - PH + 0.18, SD_W, 0.95, fc="#251840", ec=PURPLE, lw=0.7, r=0.15)
txt(Acx, PY_TOP - PH + 0.78, "BUY RECOMMENDATION", sz=7.5, c=PURPLE, w="bold")
txt(Acx, PY_TOP - PH + 0.42, "Auto-assigned from Trend Stage", sz=6.5, c=MUTED)

# ── PILLAR B: SWISS TRANSFERABILITY  (LLM) ──────────────────────────────────
Bx = pillar_xs[1]; Bcx = pillar_cx[1]
box(Bx, PY_TOP - PH, PW, PH, fc="#0D1A20", ec=TEAL, lw=0.9, r=0.22)
txt(Bcx, PY_TOP - 0.28, "SWISS TRANSFERABILITY", sz=9, c=TEAL, w="bold")
txt(Bcx, PY_TOP - 0.55, "LLM-assisted  ·  source market -> target market", sz=6.8, c=MUTED)

dims_b = [
    ("Outdoor Relevance",    "Fits the outdoor niche from Q&A?",        TEAL),
    ("DACH Availability Gap","Product absent/undersupplied in DACH?",   TEAL),
]
for j, (name, detail, col) in enumerate(dims_b):
    subdim(Bx + 0.15, PY_TOP - 1.55 - j * 0.97, SD_W, name, detail, col)

box(Bx + 0.15, PY_TOP - PH + 0.18, SD_W, 0.95, fc="#0A1C1A", ec=TEAL, lw=0.7, r=0.15)
txt(Bcx, PY_TOP - PH + 0.78, 'EXPLAIN "Why it fits Switzerland"', sz=7.5, c=TEAL, w="bold")
txt(Bcx, PY_TOP - PH + 0.42, '"Flyer & Stromer validate DACH demand"', sz=6.5, c=MUTED)

# ── PILLAR C: OPPORTUNITY SCORE  (LLM) ──────────────────────────────────────
Cx = pillar_xs[2]; Ccx = pillar_cx[2]
box(Cx, PY_TOP - PH, PW, PH, fc="#0D1A10", ec=GREEN, lw=0.9, r=0.22)
txt(Ccx, PY_TOP - 0.28, "OPPORTUNITY SCORE", sz=9, c=GREEN, w="bold")
txt(Ccx, PY_TOP - 0.55, "LLM-assisted  ·  grounded in Q&A context", sz=6.8, c=MUTED)

dims_c = [
    ("Availability Gap",  "Can the retailer stock this? Supplier access?", GREEN),
    ("Retail Saturation", "How crowded is Swiss outdoor in this category?", GREEN),
    ("Brand Availability","Brand in DACH via distributor or direct?",      GREEN),
]
for j, (name, detail, col) in enumerate(dims_c):
    subdim(Cx + 0.15, PY_TOP - 1.55 - j * 0.97, SD_W, name, detail, col)

box(Cx + 0.15, PY_TOP - PH + 0.18, SD_W, 0.95, fc="#091A0D", ec=GREEN, lw=0.7, r=0.15)
txt(Ccx, PY_TOP - PH + 0.78, 'EXPLAIN "Why an opportunity now"', sz=7.5, c=GREEN, w="bold")
txt(Ccx, PY_TOP - PH + 0.42, '"Low CH saturation · distributor ships direct"', sz=6.5, c=MUTED)

# ── PILLAR D: RED-FLAG SCORING  (LLM, inverted) ─────────────────────────────
Dx = pillar_xs[3]; Dcx = pillar_cx[3]
box(Dx, PY_TOP - PH, PW, PH, fc="#1A0D0D", ec=RED, lw=0.9, r=0.22)
txt(Dcx, PY_TOP - 0.28, "RED-FLAG SCORING", sz=9, c=RED, w="bold")
txt(Dcx, PY_TOP - 0.55, "LLM-assessed  ·  inverted in composite", sz=6.8, c=MUTED)

dims_d = [
    ("Supply Chain Risk",   "Single supplier · limited DACH distribution?",  RED),
    ("Regulatory Risk",     "CH import rules · certification barriers?",      RED),
    ("Brand Concentration", "Category dominated by 1-2 entrenched brands?",  RED),
]
for j, (name, detail, col) in enumerate(dims_d):
    subdim(Dx + 0.15, PY_TOP - 1.55 - j * 0.97, SD_W, name, detail, col)

box(Dx + 0.15, PY_TOP - PH + 0.18, SD_W, 0.95, fc="#200A0A", ec=RED, lw=0.7, r=0.15)
txt(Dcx, PY_TOP - PH + 0.78, 'EXPLAIN "Why to be cautious"', sz=7.5, c=RED, w="bold")
txt(Dcx, PY_TOP - PH + 0.42, '"Single EU distributor · seasonal demand spike"', sz=6.5, c=MUTED)

# ── COMPOSITE SCORE ──────────────────────────────────────────────────────────
COMP_Y = 13.3
box(0.55, COMP_Y, 21.1, 0.72, fc="#181828", ec=BLUE, lw=0.9, r=0.2)
txt(11, COMP_Y + 0.48, "COMPOSITE SCORE  =  weighted avg ( Trend  ·  Transferability  ·  Opportunity  ·  (1 - Red-Flag) )", sz=9, c=WHITE, w="bold")
txt(11, COMP_Y + 0.18, "Default: equal weights  ·  Red-Flag is inverted so high risk reduces composite  ·  weights configurable via UI sliders", sz=7.2, c=MUTED)

arr(11, 13.1, 11, 12.65)

# ═══════════════════════════════════════════════════════════════════════════
# 5  OUTPUT
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 6.3, 21.2, 6.1, GREEN, "⑤", "OUTPUT",
               "Streamlit MVP  ·  Lovable React (next iteration)")

def output_card(x, y, w, opp, stage, stage_col, rec, bars, explain, risk_lv):
    box(x, y, w, 5.55, fc="#0A1A0D" if stage_col == GREEN else "#1A1200", ec=stage_col, lw=1.0, r=0.22)
    txt(x + w/2, y + 5.2, "ACT NOW" if stage_col == GREEN else "WATCH", sz=13, c=stage_col, w="bold")
    txt(x + w/2, y + 4.85, "High composite score  +  LLM urgency = act_now" if stage_col == GREEN
        else "Rising signal  ·  low transferability or early stage", sz=7.2, c=MUTED)

    for r_i, (opp_n, stg, rec_n, sc, b_trend, b_trans, b_opp, b_risk) in enumerate(bars):
        ry = y + 4.35 - r_i * 2.1
        box(x + 0.12, ry - 1.72, w - 0.24, 1.88, fc=CARD2, r=0.16)
        txt(x + 0.28, ry - 0.17, opp_n, sz=9, c=WHITE, w="bold", ha="left")
        chip(x + w - 1.4, ry - 0.17, stg, sc, sz=7)
        txt(x + 0.28, ry - 0.46, f"Rec:  {rec_n}", sz=7.2, c=YELLOW, ha="left")
        for b_i, (bl, bv, bc) in enumerate([
            ("Trend",           b_trend, PURPLE),
            ("Transferability", b_trans, TEAL),
            ("Opportunity",     b_opp,   GREEN),
            ("Red-Flag",        b_risk,  RED),
        ]):
            txt(x + 0.28, ry - 0.80 - b_i * 0.3, f"{bl:<15} {bv}", sz=6.5, c=bc, ha="left", w="bold")
        txt(x + 0.28, ry - 1.62, explain[r_i], sz=6.3, c=MUTED, ha="left")

output_card(
    x=0.5, y=6.42, w=10.2,
    opp="act", stage="Growing", stage_col=GREEN, rec="",
    bars=[
        ("Gravel E-Bikes",     "Growing",  "Scale up · negotiate terms",
         BLUE,  "████████░░", "████████░░", "██████████", "██░░░░░░░░"),
        ("Trail Running Gear", "Emerging", "Test order · small stock",
         GREEN, "██████░░░░", "██████░░░░", "████████░░", "█░░░░░░░░░"),
    ],
    explain=[
        '"Strong Nordics signal · outdoor fit · low DACH saturation · one distributor risk"',
        '"Early US signal · great CH fit · brand not yet in DACH · low risk"',
    ],
    risk_lv=None,
)

output_card(
    x=11.3, y=6.42, w=10.2,
    opp="watch", stage="Emerging", stage_col=ORANGE, rec="",
    bars=[
        ("Mycelium Insoles",  "Emerging",  "Monitor · no action yet",
         GREEN, "████░░░░░░", "███░░░░░░░", "████░░░░░░", "████░░░░░░"),
        ("Packraft Kits",     "Declining", "Wind down · clearance",
         RED,   "██░░░░░░░░", "███░░░░░░░", "█████░░░░░", "███████░░░"),
    ],
    explain=[
        '"Social-only signal · no DACH supplier found · regulatory import questions"',
        '"Declining trend · high brand concentration · supply chain fragile"',
    ],
    risk_lv=None,
)

arr(11, 6.3, 11, 5.9, c=DASHED, ls="dashed", lw=1.2)

# ═══════════════════════════════════════════════════════════════════════════
# FUTURE: LOVABLE
# ═══════════════════════════════════════════════════════════════════════════
box(1.0, 4.15, 20.0, 1.55, fc=BG, ec=DASHED, lw=1.3, ls="dashed", r=0.28)
txt(11, 5.32, "NEXT  ->  LOVABLE", sz=9, c=DASHED, w="bold")
txt(11, 4.95, "FastAPI  ·  POST /context  ·  POST /analyze  ·  GET /results  ->  React UI", sz=8, c=DASHED)
txt(11, 4.62, "Pure Python modules decoupled from Streamlit — zero refactor for API wrapper", sz=7.5, c=DASHED)

arr(11, 4.15, 11, 3.82, c=DASHED, ls="dashed", lw=1.2)

# ═══════════════════════════════════════════════════════════════════════════
# REUSABILITY
# ═══════════════════════════════════════════════════════════════════════════
box(0.4, 0.25, 21.2, 3.38, fc="#080E18", ec=BLUE, lw=1.0, r=0.28)
txt(11, 3.3,  "REUSABILITY", sz=10, c=BLUE, w="bold")
txt(11, 2.98, "Change only RetailerContext — same pipeline for any retailer, market, or category", sz=8.5, c=MUTED)

reuse = [
    ("Target Market",      "Paris · Tokyo · NYC"),
    ("Comparison Markets", "Any geography"),
    ("Niche / Category",   "Fashion · Electronics · Food"),
    ("Competitor URLs",    "Any retailer"),
    ("Risk Factors",       "Domain-specific"),
    ("Score Weights",      "Per use case"),
]
rcw = 21.2 / len(reuse)
for i, (k, v) in enumerate(reuse):
    cx = 0.4 + rcw * i + rcw / 2
    box(cx - rcw/2 + 0.1, 0.38, rcw - 0.2, 2.3, fc=CARD2, r=0.15)
    txt(cx, 1.42, k, sz=7.8, c=MUTED, w="bold")
    txt(cx, 1.05, v, sz=8,   c=WHITE)

txt(11, 0.44, "Buy recommendations and Red-Flag assessment adapt automatically — no hardcoded rules per category", sz=7.5, c=MUTED)

plt.tight_layout(pad=0)
plt.savefig("assets/architecture.png", dpi=160, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
print("Saved: assets/architecture.png")
