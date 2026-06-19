import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(22, 30))
ax.set_xlim(0, 22)
ax.set_ylim(0, 30)
ax.axis("off")
fig.patch.set_facecolor("#0D1117")

# ── PALETTE ─────────────────────────────────────────────────────────────────
BG        = "#0D1117"
CARD      = "#161B27"
CARD2     = "#1C2235"
BLUE      = "#4A90D9"
GREEN     = "#27AE60"
ORANGE    = "#E67E22"
RED       = "#E74C3C"
PURPLE    = "#8E44AD"
TEAL      = "#16A085"
YELLOW    = "#F1C40F"
PINK      = "#E91E8C"
WHITE     = "#FFFFFF"
MUTED     = "#6B7A99"
DASHED    = "#3A4255"

# ── HELPERS ──────────────────────────────────────────────────────────────────
def box(x, y, w, h, fc=CARD, ec="none", lw=1.2, ls="solid", alpha=1.0, r=0.28):
    p = FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw,
        linestyle=ls, alpha=alpha, zorder=3)
    ax.add_patch(p)

def txt(x, y, s, sz=9, c=WHITE, w="normal", ha="center", va="center"):
    ax.text(x, y, s, fontsize=sz, color=c, ha=ha, va=va, fontweight=w, zorder=5)

def arr(x1, y1, x2, y2, c=BLUE, ls="solid", lw=1.8):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=c, lw=lw,
                        linestyle=ls, connectionstyle="arc3,rad=0.0"), zorder=4)

def section_header(x, y, w, h, color, number, title, subtitle=""):
    box(x, y, w, h, fc=CARD, ec=color, lw=1.0, alpha=1.0)
    txt(x + 0.55, y + h - 0.32, number, sz=7.5, c=color, w="bold", ha="left")
    txt(x + 1.1, y + h - 0.32, title, sz=9, c=color, w="bold", ha="left")
    if subtitle:
        txt(x + w/2, y + h - 0.58, subtitle, sz=7, c=MUTED)

def chip(x, y, label, color, sz=7.0):
    tw = len(label) * 0.072 + 0.22
    box(x - tw/2, y - 0.13, tw, 0.28, fc=color + "33", ec=color, lw=0.8, r=0.12)
    txt(x, y, label, sz=sz, c=color, w="bold")

def subdim(x, y, label, detail, color, det_color=None):
    box(x, y, 4.5, 0.78, fc=BG, ec=color, lw=0.6, r=0.15)
    txt(x + 0.2, y + 0.54, label, sz=8, c=color, w="bold", ha="left")
    txt(x + 0.2, y + 0.22, detail, sz=6.8, c=det_color or MUTED, ha="left")


# ═══════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════
txt(11, 29.55, "Zenline Retail Radar", sz=20, c=WHITE, w="bold")
txt(11, 29.1,  "Reusable opportunity detection pipeline   ·   Swiss outdoor retail demo", sz=9.5, c=MUTED)

# ═══════════════════════════════════════════════════════════════════════════
# 1  Q&A ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 27.1, 21.2, 1.75, BLUE, "①", "Q&A ENTRYPOINT",
               "Produces RetailerContext — the single config object consumed by every downstream module")

qa = [
    ("Target Market",       "Switzerland"),
    ("Comparison Markets",  "Sweden · Canada · Nordics"),
    ("Niche / Category",    "Outdoor Retailer"),
    ("Demographics",        "Gender · Age range"),
    ("Competitor URLs",     "transa.ch · ochsner-sport.ch"),
    ("Risk Factors",        "Supply chain · Regulatory\nSeasonal · Single-supplier"),
]
slot_w = 21.2 / len(qa)
for i, (k, v) in enumerate(qa):
    cx = 0.4 + slot_w * i + slot_w / 2
    box(cx - slot_w/2 + 0.12, 27.18, slot_w - 0.24, 1.05, fc=CARD2, r=0.15)
    txt(cx, 27.87, k, sz=7, c=MUTED)
    txt(cx, 27.48, v, sz=7.5, c=WHITE, w="bold")

arr(11, 27.1, 11, 26.7)
txt(12.9, 26.9, "RetailerContext", sz=8.5, c=BLUE, w="bold")

# ═══════════════════════════════════════════════════════════════════════════
# 2  DATA COLLECTION
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 24.45, 21.2, 2.0, TEAL, "②", "DATA COLLECTION",
               "Scrapes comparison markets defined in RetailerContext")

sources = [
    ("Google Trends",    "pytrends",         "Momentum · search slope",      TEAL),
    ("Reddit",           "praw",             "Community buzz · r/outdoor",   TEAL),
    ("Amazon",           "beautifulsoup4",   "Marketplace rank & titles",    TEAL),
    ("BFS Open Data",    "requests + JSON",  "Swiss structural trends",      TEAL),
    ("Competitor Sites", "from Q&A URLs",    "Assortment & pricing gaps",    TEAL),
]
sw = 21.2 / len(sources)
for i, (name, lib, sig, col) in enumerate(sources):
    cx = 0.4 + sw * i + sw / 2
    box(cx - sw/2 + 0.12, 24.55, sw - 0.24, 1.6, fc=CARD2, r=0.18)
    txt(cx, 25.83, name, sz=9, c=col, w="bold")
    txt(cx, 25.47, lib,  sz=7, c=MUTED)
    txt(cx, 25.12, sig,  sz=7.5, c=WHITE)

arr(11, 24.45, 11, 24.05)

# ═══════════════════════════════════════════════════════════════════════════
# 3  FILTER LAYER
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 22.35, 21.2, 1.45, ORANGE, "③", "FILTER LAYER")

box(0.6,  22.45, 10.3, 0.88, fc=CARD2, r=0.18)
txt(1.1,  22.98, "Relevance Filter", sz=8.5, c=ORANGE, w="bold", ha="left")
txt(1.1,  22.65, "Keep only signals matching RetailerContext niche and originating from target or comparison markets", sz=7.2, c=WHITE, ha="left")

box(11.1, 22.45, 10.3, 0.88, fc=CARD2, r=0.18)
txt(11.6, 22.98, "Deduplication", sz=8.5, c=ORANGE, w="bold", ha="left")
txt(11.6, 22.65, "Collapse same opportunity across source types · preserve all source_types for breadth counting", sz=7.2, c=WHITE, ha="left")

arr(11, 22.35, 11, 21.95)

# ═══════════════════════════════════════════════════════════════════════════
# 4  SCORING LAYER
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 13.1, 21.2, 8.6, PURPLE, "④", "SCORING LAYER",
               "Three pillars · deterministic + LLM-hybrid · equal-weight composite")

PILLAR_Y_TOP = 20.85
PILLAR_H     = 5.2
PW = 6.7

# ── PILLAR A: TREND SCORE ───────────────────────────────────────────────────
box(0.55, PILLAR_Y_TOP - PILLAR_H, PW, PILLAR_H, fc="#160E22", ec=PURPLE, lw=0.8, r=0.22)
txt(3.9, PILLAR_Y_TOP - 0.28, "TREND SCORE", sz=9.5, c=PURPLE, w="bold")
txt(3.9, PILLAR_Y_TOP - 0.58, "Deterministic", sz=7, c=MUTED)

dims_a = [
    ("Growth",      "Google Trends 90d slope · normalized 0-10",          PURPLE),
    ("Noise Score", "Penalty: % signals that are social-media-only · 0-5", RED),
    ("Low Recency", "Penalty: avg signal age in days · staleness score",   RED),
]
for j, (name, detail, col) in enumerate(dims_a):
    subdim(0.65, PILLAR_Y_TOP - 1.1 - j * 0.95, name, detail, col)

# Trend Stage derived box
box(0.65, PILLAR_Y_TOP - PILLAR_H + 0.15, PW - 0.2, 0.95, fc="#1E1030", ec=PURPLE, lw=0.8, r=0.15)
txt(3.9, PILLAR_Y_TOP - PILLAR_H + 0.75, "TREND STAGE  (derived)", sz=8, c=PURPLE, w="bold")
for k, (stage, col2) in enumerate([("Emerging", GREEN), ("Growing", BLUE), ("Mainstream", YELLOW), ("Declining", RED)]):
    chip(0.65 + PW * (k + 0.5) / 4, PILLAR_Y_TOP - PILLAR_H + 0.33, stage, col2, sz=7)

# ── PILLAR B: SWISS TRANSFERABILITY ─────────────────────────────────────────
box(7.65, PILLAR_Y_TOP - PILLAR_H, PW, PILLAR_H, fc="#0D1A20", ec=TEAL, lw=0.8, r=0.22)
txt(11.0, PILLAR_Y_TOP - 0.28, "SWISS TRANSFERABILITY SCORE", sz=9.5, c=TEAL, w="bold")
txt(11.0, PILLAR_Y_TOP - 0.58, "LLM-assisted  ·  source market -> target market", sz=7, c=MUTED)

dims_b = [
    ("Outdoor Relevance",    "Does opportunity fit the outdoor niche from Q&A?",  TEAL),
    ("Climate Fit",          "Matches Swiss alpine / urban climate conditions?",   TEAL),
    ("DACH Availability Gap","Is product absent or undersupplied in DACH market?", TEAL),
]
for j, (name, detail, col) in enumerate(dims_b):
    subdim(7.75, PILLAR_Y_TOP - 1.1 - j * 0.95, name, detail, col)

# Explainability A for this pillar
box(7.75, PILLAR_Y_TOP - PILLAR_H + 0.15, PW - 0.2, 0.95, fc="#0A1C1A", ec=TEAL, lw=0.8, r=0.15)
txt(11.0, PILLAR_Y_TOP - PILLAR_H + 0.75, 'Explain "Why it fits Switzerland"', sz=8, c=TEAL, w="bold")
txt(11.0, PILLAR_Y_TOP - PILLAR_H + 0.35, '"Matches alpine commuter culture; Flyer & Stromer validate DACH demand"', sz=7, c=MUTED)

# ── PILLAR C: OPPORTUNITY SCORE ──────────────────────────────────────────────
box(14.75, PILLAR_Y_TOP - PILLAR_H, PW, PILLAR_H, fc="#0D1A10", ec=GREEN, lw=0.8, r=0.22)
txt(18.1, PILLAR_Y_TOP - 0.28, "OPPORTUNITY SCORE", sz=9.5, c=GREEN, w="bold")
txt(18.1, PILLAR_Y_TOP - 0.58, "LLM-assisted  ·  grounded in Q&A context", sz=7, c=MUTED)

dims_c = [
    ("Availability Gap",  "Can the retailer actually stock this? Supplier access?", GREEN),
    ("Retail Saturation", "How crowded is Swiss outdoor retail in this category?",  GREEN),
    ("Brand Availability","Is brand present in DACH via distributor or direct?",    GREEN),
]
for j, (name, detail, col) in enumerate(dims_c):
    subdim(14.85, PILLAR_Y_TOP - 1.1 - j * 0.95, name, detail, col)

box(14.85, PILLAR_Y_TOP - PILLAR_H + 0.15, PW - 0.2, 0.95, fc="#091A0D", ec=GREEN, lw=0.8, r=0.15)
txt(18.1, PILLAR_Y_TOP - PILLAR_H + 0.75, 'Explain "Why an opportunity now"', sz=8, c=GREEN, w="bold")
txt(18.1, PILLAR_Y_TOP - PILLAR_H + 0.35, '"Low CH saturation; German distributor ships direct; no major local brand"', sz=7, c=MUTED)

# ── EXPLAINABILITY ROW ───────────────────────────────────────────────────────
EXP_Y = 14.55
box(0.55, EXP_Y, 21.1, 0.88, fc="#161028", ec="#6C3FB5", lw=0.9, r=0.2)
txt(1.05, EXP_Y + 0.65, "EXPLAINABILITY DIMENSIONS  (one LLM sentence per pillar, shown on scorecard row)", sz=8, c="#B39DDB", w="bold", ha="left")
txt(1.05, EXP_Y + 0.28, '"Why trending"  ·  "Why it fits Switzerland"  ·  "Why an opportunity now"', sz=8, c=MUTED, ha="left")

# ── RISK BADGES ROW ──────────────────────────────────────────────────────────
RISK_Y = 13.5
box(0.55, RISK_Y, 21.1, 0.75, fc="#1A0D0D", ec=RED, lw=0.8, r=0.2)
txt(1.05, RISK_Y + 0.53, "RISK BADGES  (from Q&A risk factors, LLM-assessed per opportunity)", sz=8, c=RED, w="bold", ha="left")
for k, badge in enumerate(["Supply Chain", "Regulatory", "Seasonal", "Single Supplier"]):
    chip(2.0 + k * 3.5, RISK_Y + 0.22, badge, RED, sz=7.5)

# ── COMPOSITE SCORE ──────────────────────────────────────────────────────────
COMP_Y = 13.18
box(0.55, COMP_Y, 21.1, 0.62, fc="#181828", ec=BLUE, lw=0.9, r=0.2)
txt(11,   COMP_Y + 0.35, "COMPOSITE SCORE  =  equal-weight avg ( Trend Score  ·  Swiss Transferability  ·  Opportunity Score )    +   BUY RECOMMENDATION  from Trend Stage", sz=8.5, c=WHITE, w="bold")

arr(11, 13.1, 11, 12.7)

# ═══════════════════════════════════════════════════════════════════════════
# 5  OUTPUT
# ═══════════════════════════════════════════════════════════════════════════
section_header(0.4, 6.7, 21.2, 6.15, GREEN, "⑤", "OUTPUT",
               "Streamlit MVP  ·  Lovable React (next iteration)")

# ACT NOW column
box(0.6, 6.85, 10.1, 5.7, fc="#0A1A0D", ec=GREEN, lw=1.0, r=0.22)
txt(5.65, 12.2, "ACT NOW", sz=13, c=GREEN, w="bold")
txt(5.65, 11.82, "High composite score  +  urgency flag from LLM", sz=7.5, c=MUTED)

rows_act = [
    ("Gravel E-Bikes",    "Growing",     "Scale up · negotiate terms",    BLUE,   "████████░░", "████████░░", "██████████"),
    ("Trail Running Gear","Emerging",    "Test order · small stock",       GREEN,  "██████░░░░", "████░░░░░░", "████████░░"),
]
for r_i, (opp, stage, rec, sc, tb, tsb, trsb) in enumerate(rows_act):
    ry = 11.35 - r_i * 2.35
    box(0.7, ry - 1.95, 9.9, 2.1, fc=CARD2, r=0.18)
    txt(1.1, ry - 0.2, opp, sz=9.5, c=WHITE, w="bold", ha="left")
    chip(3.5, ry - 0.2, stage, sc if stage != "Emerging" else GREEN, sz=7)
    txt(1.1, ry - 0.52, f"Buy rec:  {rec}", sz=7.5, c=YELLOW, ha="left")
    for b_i, (blabel, bval, bc) in enumerate([
        ("Trend", tb, PURPLE), ("Transferability", tsb, TEAL), ("Opportunity", trsb, GREEN)
    ]):
        txt(1.1, ry - 0.88 - b_i * 0.38, f"{blabel:<16} {bval}", sz=7, c=bc, ha="left", w="bold")
    txt(1.1, ry - 1.78, '"Rising fast in Nordics · strong CH outdoor culture · DACH distributor available"', sz=6.5, c=MUTED, ha="left")

# WATCH column
box(10.9, 6.85, 10.1, 5.7, fc="#1A1200", ec=ORANGE, lw=1.0, r=0.22)
txt(15.95, 12.2, "WATCH", sz=13, c=ORANGE, w="bold")
txt(15.95, 11.82, "Rising signal  ·  low transferability or early stage", sz=7.5, c=MUTED)

rows_watch = [
    ("Mycelium Insoles", "Emerging",  "Monitor · no action yet",       GREEN,  "████░░░░░░", "███░░░░░░░", "████░░░░░░"),
    ("Packraft Kits",    "Declining", "Wind down · evaluate clearance", RED,    "██░░░░░░░░", "███░░░░░░░", "█████░░░░░"),
]
for r_i, (opp, stage, rec, sc, tb, tsb, trsb) in enumerate(rows_watch):
    ry = 11.35 - r_i * 2.35
    box(11.0, ry - 1.95, 9.9, 2.1, fc=CARD2, r=0.18)
    txt(11.4, ry - 0.2, opp, sz=9.5, c=WHITE, w="bold", ha="left")
    chip(14.0, ry - 0.2, stage, sc, sz=7)
    txt(11.4, ry - 0.52, f"Buy rec:  {rec}", sz=7.5, c=YELLOW, ha="left")
    for b_i, (blabel, bval, bc) in enumerate([
        ("Trend", tb, PURPLE), ("Transferability", tsb, TEAL), ("Opportunity", trsb, GREEN)
    ]):
        txt(11.4, ry - 0.88 - b_i * 0.38, f"{blabel:<16} {bval}", sz=7, c=bc, ha="left", w="bold")
    txt(11.4, ry - 1.78, '"Signal only on Reddit · no DACH distributor found · climate mismatch for CH"', sz=6.5, c=MUTED, ha="left")

arr(11, 6.7, 11, 6.3)

# ═══════════════════════════════════════════════════════════════════════════
# FUTURE: LOVABLE
# ═══════════════════════════════════════════════════════════════════════════
box(1.0, 4.5, 20.0, 1.55, fc=BG, ec=DASHED, lw=1.3, ls="dashed", r=0.28)
txt(11, 5.67, "NEXT  ->  LOVABLE", sz=9, c=DASHED, w="bold")
txt(11, 5.3,  "FastAPI backend  ·  POST /context  ·  POST /analyze  ·  GET /results  ->  React UI", sz=8, c=DASHED)
txt(11, 4.95, "Pure Python modules already decoupled from Streamlit — zero refactor needed for API wrapper", sz=7.5, c=DASHED)
txt(11, 4.65, "Same RetailerContext dataclass  ·  same scoring modules  ·  swap Streamlit for React frontend", sz=7.2, c=DASHED)

arr(11, 4.5, 11, 4.15, c=DASHED, ls="dashed", lw=1.2)

# ═══════════════════════════════════════════════════════════════════════════
# REUSABILITY
# ═══════════════════════════════════════════════════════════════════════════
box(0.4, 0.3, 21.2, 3.65, fc="#080E18", ec=BLUE, lw=1.0, r=0.28)
txt(11, 3.65, "REUSABILITY", sz=10, c=BLUE, w="bold")
txt(11, 3.3,  "Change only RetailerContext  -  same pipeline runs for any retailer, market, or category", sz=8.5, c=MUTED)

reuse = [
    ("Target Market",       "Paris · Tokyo · NYC"),
    ("Comparison Markets",  "Any geography"),
    ("Niche / Category",    "Fashion · Electronics · Food"),
    ("Competitor URLs",     "Any retailer"),
    ("Risk Factors",        "Domain-specific"),
]
cw = 21.2 / len(reuse)
for i, (k, v) in enumerate(reuse):
    cx = 0.4 + cw * i + cw / 2
    box(cx - cw/2 + 0.12, 0.45, cw - 0.24, 2.45, fc=CARD2, r=0.15)
    txt(cx, 1.6, k, sz=8, c=MUTED, w="bold")
    txt(cx, 1.15, v, sz=8.5, c=WHITE)

txt(11, 0.52, "Trend Stage buy recommendations adapt automatically to detected stage — no hardcoded rules per category", sz=7.5, c=MUTED)

plt.tight_layout(pad=0)
plt.savefig("assets/architecture.png", dpi=160, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
print("Saved: assets/architecture.png")
