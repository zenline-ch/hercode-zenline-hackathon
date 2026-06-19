# Retail Radar — Architecture, Pipeline & Ideation Summary

> Team merge of Giulia's `feature/giulia` branch (hybrid scoring, `RetailerContext`, ADR 0001) and the team's earlier research (assortment-gap differentiator, persona layer, lead-lag, trend lifecycle). This is the single source of truth — built to survive a jury Q&A, not just a demo.

---

## 1. The pitch (memorize this, say it on stage)

> **"We don't just detect global trends — we score them against the Swiss shelf. A trend rising in Google Trends CH but absent from Bächli/Transa is a quantified assortment gap, not a guess."**

One-sentence version:

> *Retail Radar quantifies the gap between what's trending globally and what's actually on Swiss shelves — turning noisy signals into ranked, evidence-linked buy/test/monitor decisions, with calibrated confidence that tells the buyer when **not** to act.*

### Why a jury remembers this over the other teams

| # | Pillar | What most teams do instead |
| --- | --- | --- |
| 1 | **Assortment-gap is part of the score, not a footnote.** `coverage_status` (absent/partially_covered/covered) is one of five scoring pillars, worth 20% of `composite_score` by default. | Most teams say "X is trending" and stop. |
| 2 | **Calibrated honesty.** Low-evidence opportunities are explicitly flagged `watch`, not `act_now` — even if they're exciting. | Most teams rank everything as a buy. |
| 3 | **Hybrid scoring, not a black box.** Breadth and Momentum are pure arithmetic on scraped data (`numpy.polyfit`, source-type counts) — auditable with no API key. Only Transferability uses an LLM, and only because that judgment genuinely requires reasoning about culture/climate/commerce fit. ([ADR 0001](docs/adr/0001-hybrid-scoring.md)) | Most teams either hand everything to an LLM (unauditable) or hand-code thresholds with no reasoning layer (brittle). |
| 4 | **Reusability is demoed live, not claimed.** A `RetailerContext` Q&A wizard reconfigures the entire system for a new market/category/persona in front of the jury — no code edit. | Most teams say "this is reusable" in a slide with no proof. |

---

## 2. System overview

```
collect → normalise → clean → deduplicate → score (hybrid) → lead-lag → synthesise → present
                                                  ↑
                                          RetailerContext
                                  (target market, comparison markets,
                                   niche, demographics, competitor URLs,
                                   persona, scoring weights)
```

Full diagrams with Mermaid flowcharts live in [`diagram.md`](diagram.md).

---

## 3. `RetailerContext` — the reusability engine

Source: Giulia's `CONTEXT.md`. This is the single config object every module reads — nothing downstream is hardcoded to Switzerland or outdoor retail.

```python
@dataclass
class RetailerContext:
    target_market: str                 # e.g. "CH" — where the retailer sells
    comparison_markets: list[str]      # e.g. ["SE", "CA", "US"] — credible early-signal sources
    niche: str                         # e.g. "outdoor", swap to "cycling" to prove reuse
    demographic_filters: dict          # gender, age range
    competitor_urls: list[str]         # e.g. Bächli, Transa — for the assortment-gap check
    persona: str                       # "large_retailer" | "boutique" | "individual_dtc"  # we can write in Niche/Who we are sector 
    scoring_weights: dict              # {breadth, momentum, transferability, coverage_gap, risk} — sums to 1.0
```

**Why this matters for the demo:** instead of editing `config.py` and re-running a script, the jury watches you type answers into a Q&A flow on stage, hit submit, and watch the ranked list reorder for a different market or persona. That is the reusability proof the rubric asks for — *shown, not claimed.*

**Comparison market vs. target market — do not merge these:**

```python
# comparison_markets are NOT the same role as target_market.
# Example for the demo scenario:
target_market = "CH"                                  # DACH — where we sell
comparison_markets = ["US", "Nordics", "Japan", "Korea", "UK"]  # where trends appear first
```

A signal found in a comparison market earns an **early-signal** read (we're ahead of the curve). A signal found in the target market feeds the **transferability** assessment directly. Stage line: *"DACH is the target. Nordics, US, and Japan are our early-warning radar. We never mix the two."*

### Persona — same signal, different action

```python
PERSONA = {
    "large_retailer":  {"min_confidence": "high",   "buy_action": "commercial_proof_only"},
    "boutique":        {"min_confidence": "medium", "buy_action": "small_curated_test"},
    "individual_dtc":  {"min_confidence": "medium", "buy_action": "fast_small_bet"},
}
```

Persona is one field on `RetailerContext`. Switching it re-derives `buy_recommendation` for every opportunity without touching scoring code. Build `large_retailer` as the complete default; demo one more persona switch live to prove extensibility — don't build all three under time pressure.

---

## 4. Signal cleaning (between normalise and deduplicate)

Most teams skip this step. It's where "messy real-world sources → structured evidence" credit is won (directly named in `evaluation.md`).

1. **Validate** — drop rows with no name, no URL, or under 4 characters (fragments).
2. **Normalise text** — lowercase, collapse whitespace, **keep umlauts/accents** (äöüéè) — stripping them silently destroys German/French DACH evidence.
3. **Canonicalise entities** — hand-curated `BRAND_ALIASES` / `MARKET_ALIASES` allowlists, not fuzzy matching. Fuzzy matching with no test set at hour 5 of a hackathon will silently corrupt your output.
4. **Numeric cleanup** — parse `"$325"`, `"CHF 189.-"`, `"#3"` into clean values.
5. **Spam filter** — drop `"buy now"`, `"affiliate"`, `"[deleted]"`, `"sponsored"`.
6. **Date sanity** — drop or flag stale/malformed `observed_at` values.

**Log what you drop.** *"Ingested 140 raw signals → cleaned 95 → deduped 60"* is a concrete evidence-quality story for the jury — say it on stage.

---

## 5. Deduplication

```python
def signal_key(s):
    return (s.keyword.lower().strip(), s.brand.lower().strip(), s.market)
```

Two signals are the *same* signal only if keyword, brand, **and market** all match. Market is deliberately part of the key: `"gravel running" / US` and `"gravel running" / CH` must stay separate rows, because that's exactly the lead-lag evidence the system needs to prove a market led another. Collapsing across markets would destroy the one piece of evidence that makes the timing claim defensible.

When two rows do collapse (same keyword, brand, market, different source), keep the higher-scoring row and append the other's URL to `notes` — evidence is never discarded, only merged.

---

## 6. Scoring — the hybrid model (ADR 0001)

**Decision:** deterministic computation wherever data supports it; an LLM only where genuine judgment is required. See [`docs/adr/0001-hybrid-scoring.md`](docs/adr/0001-hybrid-scoring.md).

`composite_score` (0–1) is a transparent, traceable weighted average of five pillars. Every point on the final number can be justified on one slide — this is what "transparent scoring" in the evaluation rubric rewards, instead of a black-box LLM score.

| Pillar | Range | Computed by | What it captures |
| --- | --- | --- | --- |
| **Signal Breadth** | 0–5 → normalised /5 | Deterministic — count of distinct `signal_type` values independently surfacing the same opportunity | Independent confirmation across sources (Reddit ≠ Google Trends ≠ marketplace all agreeing is stronger than one loud source) |
| **Momentum** | 0–10 → normalised /10 | Deterministic — Google Trends 90-day slope per comparison market via `numpy.polyfit` | How fast it's actually rising, not just "is it mentioned" |
| **Transferability** | 1–5 → normalised (score−1)/4 | **LLM**, structured JSON output (`score`, `reason`, `urgency`), grounded in the specific market pair + `RetailerContext` | Whether *this* comparison-market → target-market pair makes cultural, climatic, and commercial sense — a judgment, not a lookup table |
| **Coverage Gap** | mapped to 0–1 | Deterministic — `coverage_status` from the competitor-assortment scan | `absent` = 1.0, `partially_covered` = 0.5, `covered` = 0.1, `unknown`/`not_relevant` = 0.2 |
| **Risk Factor** | mapped to 0–1, inverted | Deterministic — count of triggered `risk_flags` against a curated taxonomy | Lower score the more risk flags fire; rewards opportunities that are not just promising but *safe to act on* |

```python
RISK_TAXONOMY = [
    "supply_chain",        # single supplier, long lead time, geopolitical exposure
    "single_supplier",     # no fallback vendor if the deal falls through
    "price_volatility",    # FX exposure, tariff risk, raw-material cost swings
    "regulatory",          # import restrictions, safety certification, EU material rules
    "low_moq_barrier",     # minimum order quantity too high for a small test buy
]

def risk_score(flags: list[str]) -> float:
    triggered = len(set(flags) & set(RISK_TAXONOMY))
    return 1 - (triggered / len(RISK_TAXONOMY))   # 1.0 = no flags, fewer flags = safer

composite_score = (
    weights["breadth"]          * breadth_norm +
    weights["momentum"]         * momentum_norm +
    weights["transferability"]  * transferability_norm +
    weights["coverage_gap"]     * coverage_gap_score +
    weights["risk"]             * risk_score(risk_flags)
)
# default weights: equal, 0.20 each — overridable via RetailerContext.scoring_weights (UI sliders)
```

**Why Coverage Gap is a scoring pillar and not just a badge:** this is the single biggest differentiator vs. every other team's "trend list." Baking the assortment-gap check directly into the number — not just displaying it — means the score itself is already arguing "this is a buy because the shelf has a hole," not "this is popular."

**Why Risk Factor is a pillar too, not just `risk_flags` badges:** a high-momentum, absent-from-shelf opportunity that depends on a single overseas supplier with tariff exposure is *not* the same recommendation as one with a stable, diversified supply chain — even at identical Breadth/Momentum/Coverage scores. Scoring risk directly means two opportunities that look identical on hype and gap alone can still rank differently once supply realism is priced in. `risk_flags` stays in the output as a human-readable badge list; `risk_score()` is what actually moves the rank.

**Honest caveat to say on stage:** Transferability requires one LLM call per opportunity — added latency/cost, and it's the one non-deterministic input. Breadth, Momentum, Coverage Gap, and Risk Factor are fully auditable and rerunnable with zero API key. The risk taxonomy is a curated list, not exhaustive — say so if asked what's missing (e.g. currency exposure, brand-exclusivity lock-in). A future fully-offline mode could swap Transferability for a rule table if needed.

### Confidence label (derived, not separately scored)

```python
def confidence_label(composite_score: float) -> str:
    if composite_score >= 0.70: return "high"
    if composite_score >= 0.45: return "medium"
    return "low"
```

### Urgency guard (enforced by the synthesiser, not the LLM alone)

`urgency` (`act_now` / `watch`) comes from the Transferability LLM call, but the synthesiser **overrides it to `watch` whenever `confidence == "low"`** — no opportunity can be marked urgent on weak evidence, regardless of what the LLM says. This single guard *is* the "calibrated honesty" pitch line turned into actual code.

---

## 7. The core demo contrast: directional signal vs. commercial proof

This is the moment that makes the jury trust the rest of the list. Use these two as the stage example (swap with real findings from the day's run if better evidence turns up — these are illustrative anchors, not guaranteed live results):

**Commercial proof → `act_now`, buy/test**
*Gravel running.* Named SKUs already shipping (e.g. La Sportiva Prodigio 2, Keen Roam) with price, reviews, and a confirmed material spec. Rising in Google Trends CH **and** absent from Bächli/Transa.
→ `confidence: high`, `coverage_status: absent`, `urgency: act_now`, action = *test capsule, 2–3 SKUs, contact supplier.*

**Directional signal → `watch`, no buy**
*Mycelium / bio-synthetic membranes.* Cited as a 2026 fabric trend with real market CAGR — but **zero retail SKUs exist**, only press releases and R&D.
→ `confidence: low`, `coverage_status: not_relevant`, `urgency: watch` (guard-forced), action = *monitor, re-evaluate Q1 2027, no buy.*

**Stage line:**
> *"Most opportunity reports treat every trend as a buy. Ours doesn't. Gravel running is commercial proof — named SKUs, prices, a Swiss shelf gap — so we say buy. Mycelium is a directional signal — real buzz, but nothing you can order — so we say monitor, not buy. Telling a buyer when **not** to act is what makes the rest of the list trustworthy."*

### The full gradient (not binary)

| Confidence | Trend stage | Coverage | Action |
| --- | --- | --- | --- |
| High | emerging | absent | Full test capsule (2–3 SKUs, small qty, fast re-order) |
| High | growing | partially_covered | Buy flagship SKUs + material story; flag supply risk explicitly |
| Medium-high | growing | partially_covered | Staged buy — start with the lowest-MOQ SKU |
| Medium | emerging | absent | Small curated test, anchor to a niche community |
| Low | any | not_relevant/unknown | Watch only, zero stock |

---

## 8. Trend lifecycle & inventory discipline

Recommendations don't end at "buy" — they need a stop condition. Add these fields to every `Recommendation` / `Opportunity` record:

```python
trend_stage: str             # "emerging" | "growing" | "mainstream" | "declining"
expected_window: str         # e.g. "12-24 month first-mover advantage window"
monitor_triggers: list[str]  # if seen → stop or reduce stock
reversal_signals: list[str]  # signs the trend is breaking
```

### Buy recommendation by trend stage

| Trend Stage | Buy Recommendation |
| --- | --- |
| `emerging` | Test order · small stock · monitor closely |
| `growing` | Scale up · negotiate supplier terms |
| `mainstream` | Evaluate margin · assess competitive positioning |
| `declining` | Wind down · evaluate clearance strategy |

### Kill criteria example (gravel running)

```yaml
monitor_triggers:
  - "Google Trends CH momentum declines 3 months straight"
  - "Bächli/Transa stock the same category → no longer a gap"
  - "Key supplier raises price 30%+ or tariff shock hits"
reversal_signals:
  - "Review media reports the category label isn't sticking"
  - "Initial sell-through < 20% after 4 weeks"
```

**Two inventory principles to say on stage:**
1. **Start small, re-order fast** — a small test + short-lead-time supplier beats one big first order. Small loss if wrong, fast scale if right.
2. **Sell-through gate** — bake the exit condition into the recommendation itself: *"stop re-ordering if 4-week sell-through < 30%."*

**Honest caveat:** trend stage and sell-through gates are signal-based estimates, not validated sales data — say so explicitly. *"Signal-based estimate, re-validated by actual sell-through after stocking."*

---

## 9. Proving lead-lag (don't just claim "trends appear first elsewhere")

**Method A — Google Trends lead-lag comparison (strongest evidence):** pull the same keyword across multiple geos as a 12-month series; show which market crossed the momentum threshold first.

```python
def detect_lead_market(keyword, geos=["US", "Nordics", "DE", "CH"]):
    onset = {}
    for geo in geos:
        df = get_trends(keyword, geo)
        onset[geo] = first_month_above_threshold(df, threshold=50)
    return sorted(onset.items(), key=lambda x: x[1])  # earliest = lead market
```

Stage slide: *"gravel running search — US rose from 2025 Q2, CH only from 2026 Q1 → 9-month lag."*

**Method B — publication & launch timestamps:** compare media coverage date or brand-launch date in a comparison market vs. the target market, using the existing `observed_at` + `url` fields.

**Honest caveat:** this is correlation, not causation. Say *"in this signal, US led by 9 months, and we monitor whether the pattern repeats"* — not *"US is always first."*

**Hackathon scope note:** running full lead-lag across every opportunity risks `pytrends` rate-limiting. Pick 2–3 hero keywords, run it live or cache the result, and keep a screenshot as backup evidence.

---

## 10. Data contract (canonical — do not diverge from this)

The full reference lives in [`docs/data-contract.md`](docs/data-contract.md), extended by Giulia's branch with the per-opportunity JSON shape. Three layers:

**Signal row** — `source`, `market`, `keyword`, `signal_name`, `signal_type`, `product_name`, `brand`, `price`, `rank`, `url`, `signal_score`, `confidence`, `notes`, `observed_at`, `artifact_type`, `artifact_uri`, `created_by_tool`.

**Recommendation row** — `rank`, `opportunity`, `first_observed_market`, `evidence_summary`, `evidence_urls`, `transferability`, `coverage_status`, `recommended_action`, `confidence`, `risks`.

**Opportunity JSON (scoring layer output, consumed by the frontend)** — one object per opportunity:

```json
{
  "id": "gravel-running",
  "name": "Gravel Running Shoes",
  "trend_stage": "emerging",
  "urgency": "act_now",
  "buy_recommendation": "Test order · small stock · monitor closely",
  "composite_score": 0.82,
  "confidence": "high",
  "coverage_status": "absent",
  "scores": {
    "breadth": { "total": 0.8, "count": 4 },
    "momentum": { "total": 0.76, "slope": 8.2 },
    "transferability": { "total": 0.91, "explanation": "Matches Swiss trail-running culture; UTMB community is a ready-made audience" },
    "coverage_gap": { "total": 1.0, "explanation": "Absent from Bächli and Transa as of observed_at" },
    "risk": { "total": 0.8, "flags_triggered": ["supply_chain"], "explanation": "Single-supplier exposure on A-TPU foam component; otherwise low risk" }
  },
  "explainability": {
    "why_trending": "90-day search slope +8.2 in US and Nordics; 4 independent source types agree",
    "why_fits_switzerland": "Matches alpine/trail culture; named SKUs already reviewed in DACH gear media",
    "why_opportunity_now": "Zero CH retail coverage in the category; first-mover window open"
  },
  "monitor_triggers": ["CH momentum declines 3 months straight", "Bächli/Transa stock the category"],
  "reversal_signals": ["Sell-through < 20% after 4 weeks"],
  "expected_window": "12-24 month first-mover advantage window",
  "risk_flags": ["supply_chain"],
  "evidence_urls": ["https://trends.google.com/...", "https://reddit.com/..."]
}
```

This is the exact shape the Lovable frontend reads — see [`diagram.md`](diagram.md) for the integration plan.

---

## 11. Where the data actually comes from

**Layer A — global early-signal sources (trends appear first):** Claude/agent web search, Reddit RSS (no auth needed), gear media (GearJunkie, RoadTrailRun, Treeline), ISPO/OutDoor trade show coverage.

**Layer B — Swiss/DACH sources (transferability + assortment-gap check):**
- **Google Trends** (`geo=CH/DE/AT`, via `pytrends`, no API key) — search momentum, the cheapest credible transferability evidence available.
- **Galaxus.ch / Digitec** — CH's largest marketplace: CHF prices + bestseller ranks.
- **Bächli Bergsport, Transa** — premium assortment, the actual gap check.
- **Ochsner Sport / SportXX** — mass-market coverage check.
- **Amazon.de bestsellers** — DACH demand proxy.

**The killer move, restated:** rising in Google Trends CH + absent from Bächli/Transa = quantified assortment gap = the highest-scoring opportunity, by construction of the formula in §6.

**`pytrends` caveat:** it rate-limits and occasionally breaks. Cache every successful pull and keep a `seed_signals.json` fallback so a flaky connection never kills the live demo.

---

## 12. Tech stack

- **Backend:** Python 3.11+, Poetry-managed (`pyproject.toml` from `feature/giulia`). Pipeline stages as plain modules: `collectors/`, `cleaner.py`, `dedup.py`, `scorer.py` (hybrid), `leadlag.py`, `synthesiser.py`. Outputs `signals.csv` + `recommendations.json` matching §10 exactly.
- **LLM calls:** scoped to Transferability only, per ADR 0001 — keep the rest of the pipeline runnable with zero API key.
- **Frontend:** Lovable (Supabase-backed), consuming the JSON contract above. Full build plan in [`diagram.md`](diagram.md).

---

## 13. What to stress in the pitch (map directly to the rubric)

| Rubric area (`docs/evaluation.md`) | What to say |
| --- | --- |
| Signal detection | "We pulled from 5 source types and logged exactly what we dropped at each cleaning step." |
| Evidence quality | "Every opportunity carries its source URLs and `observed_at` — nothing is asserted without a link." |
| Transferability | "Transferability is LLM-reasoned over the specific market pair and `RetailerContext`, not a generic trend score — and it's grounded by a deterministic assortment-gap check." |
| Business actionability | "We don't say buy — we say how much, for how long, and what to watch to stop. Trends turn." |
| Risk awareness | "Risk isn't a footnote either — supply-chain, single-supplier, and regulatory exposure are a fifth scoring pillar, so two equally hyped opportunities can still rank differently once we price in how safe they are to act on." |
| Reusability | "Watch this: we change `RetailerContext` live — new market, new persona — and the ranking recomputes with zero code change." |
| Technical architecture | "Hybrid by design: deterministic dimensions need no API key and are fully rerunnable; only the one dimension that requires judgment uses an LLM." |
| Communication | "The dashboard splits `act_now` from `watch` at a glance, and every card opens into its full evidence trail." |

---

## 14. Known limitations (say these out loud — it's the strategy, not a weakness)

- Lead-lag is correlation, not causation; we monitor for repeat patterns rather than asserting a law.
- Trend stage and sell-through gates are signal-based estimates, re-validated against real sell-through after stocking.
- Entity canonicalisation uses a curated allowlist, not fuzzy matching — safer under time pressure, but only as complete as the list.
- Transferability scoring requires one LLM call per opportunity (cost/latency); everything else is free to rerun.
- The risk taxonomy (§6) is a curated, fixed list — it catches the risk types we anticipated, not every possible one.
- Demo scope: one persona (`large_retailer`) fully implemented, a second persona switched live to prove the pattern — not all three built out.
