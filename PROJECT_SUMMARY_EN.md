# Retail Radar — Project Summary (English)
> HerCode × Zenline Hackathon · Consolidated decisions & rationale

---

## Unique Selling Point (USP)

> **"We don't just detect global trends — we score them against the Swiss shelf. A trend rising in Google Trends CH but absent from Bächli/Transa is a quantified assortment gap, not a guess."**

One-sentence pitch version:
> *Retail Radar quantifies the gap between what's trending globally and what's actually on Swiss shelves — turning noisy signals into ranked, evidence-linked buy/test/monitor decisions, with calibrated confidence that tells the buyer when NOT to act.*

### Why it's unique (4 pillars)
1. **Assortment-gap scoring** — cross-reference global momentum against actual Swiss retailer assortment → `coverage_status: absent/partially_covered/covered`. Turns a trend into a buy decision.
2. **Calibrated honesty as a feature** — explicitly separate directional signals from commercial proof; flag low-confidence items as *monitor, don't buy*.
3. **Transparent scoring** — 4-component formula where every point is traceable, not a black box.
4. **Demonstrated reusability** — config swap → live re-run for another category/persona. Shown, not claimed.

---

## Directional Signal vs Commercial Proof (the core demo contrast)

**Commercial proof → "BUY / TEST"**
- *Gravel running.* Named SKUs already shipping (La Sportiva Prodigio 2, Keen Roam, Mount to Coast H1), priced, reviewed, A-TPU foam confirmed spec. Rising in Google Trends CH AND absent from Bächli/Transa.
- → `confidence: high`, `coverage_status: absent`, action = **test capsule, contact La Sportiva IT**.

**Directional signal → "MONITOR, don't buy"**
- *Mycelium / bio-synthetic membranes.* Cited as a 2026 fabric trend, real market CAGR — but **zero retail SKUs exist**. Press releases and R&D only.
- → `confidence: low`, `coverage_status: not_relevant`, action = **monitor, re-evaluate Q1 2027, no buy**.

**Stage line for the jury:**
> "Most opportunity reports treat every trend as a buy. Ours doesn't. Gravel running is commercial proof — named SKUs, prices, a Swiss shelf gap — so we say buy. Mycelium is a directional signal — real buzz, but nothing you can order — so we say monitor, not buy. Telling a buyer when NOT to act is what makes the rest of the list trustworthy."

### The confidence gradient (not binary)
| Confidence | Trend stage | Action |
|---|---|---|
| High + Emerging | big gap | Full buy / test capsule |
| High + Growth (partially covered) | Bio-Dyneema | Buy flagship SKUs + material story; flag supply risk |
| Medium-high | Run-culture brands | Staged buy — start with Ciele headwear (low MOQ) |
| Medium | Ultralight crossover | Small curated test, anchor to UTMB community |
| Low | Mycelium | No stock, monitor only |

---

## Market Roles: Target vs Early-Signal (corrected)

**DACH ≠ Nordics.** Two separate roles:

```python
TARGET_MARKETS = {"CH", "DE", "AT"}        # DACH — where we SELL
EARLY_MARKETS  = {"US", "Nordics", "Japan", "Korea", "UK"}  # where trends appear FIRST
```

- Signal in `EARLY_MARKETS` → **early-signal bonus** in scoring (we're ahead).
- Signal in `TARGET_MARKETS` → input to **transferability** assessment.
- Never merge the two. Nordics is an early-warning radar, not a target market.

**Stage line:**
> "DACH is the target. Nordics, US, and Japan are our early-warning radar. We never mix them."

---

## Proving "trends appear first in X market" (lead-lag)

Don't claim it — show it with data.

**(a) Google Trends lead-lag comparison (strongest)**
Pull the same keyword across multiple geos as a 12-month time series; show which market rose first.
- Example slide: "gravel running search — US rose from 2025 Q2, CH only from 2026 Q1 → **9-month lag**."

**(b) Publication & launch timestamps**
- US media coverage date vs DACH media date; brand launch date vs DACH availability date.
- Uses existing `observed_at` + `url` fields per market.

**Honest caveat (state it):** Google Trends lead-lag is correlation, not causation. Say "in this signal US led by 9 months, and we monitor whether the pattern repeats" — not "US is always first."

```python
def detect_lead_market(keyword, geos=["US","Nordics","DE","CH"]):
    onset = {}
    for geo in geos:
        df = get_trends(keyword, geo)
        onset[geo] = first_month_above_threshold(df, threshold=50)
    return sorted(onset.items(), key=lambda x: x[1])  # earliest = lead market
```

---

## Persona Approach (buyer decision profiles)

Split by **decision scale & risk tolerance**, not just seller size:

| Persona | Who | Risk tolerance | Same opportunity → different action |
|---|---|---|---|
| **Large retailer** (Bächli, Transa) | buying team, big budget | low — proven only | High-confidence only. Buy when commercial proof |
| **Boutique / small-batch** (specialist shop) | curation, differentiation | medium | Bets on medium too — small test for differentiation (low-MOQ entry like Ciele caps) |
| **Individual / DTC seller** (online edit shop) | fast, agile | high | Front-runs at emerging stage. Small buy, fast turn |

```python
PERSONA = {
    "large_retailer":  {"min_confidence": "high",   "buy_action": "commercial_proof_only"},
    "boutique":        {"min_confidence": "medium", "buy_action": "small_curated_test"},
    "individual_dtc":  {"min_confidence": "medium", "buy_action": "fast_small_bet"},
}
```

Persona is a `config.py` parameter that **auto-adjusts scoring thresholds and recommended actions** — proves reusability beyond category swaps.

**Build note:** finish `large_retailer` as default; show 1 more persona as a demo of extensibility (don't implement all 3 under time pressure).

---

## Trend Lifecycle & Inventory Strategy

Recommendations shouldn't end at "buy" — they need a monitoring loop.

### Add these fields to Recommendation
```python
trend_stage: str        # "emerging" | "growth" | "mainstream" | "peak" | "declining"
expected_window: str    # e.g. "12-24 month first-mover advantage window"
monitor_triggers: list[str]   # if seen → stop / reduce stock
reversal_signals: list[str]   # trend is breaking
```

### Kill criteria example (gravel running)
```
monitor_triggers:
  - "Google Trends CH momentum declines 3 months straight"
  - "Bächli/Transa stock the same category → no longer a gap (first-mover edge gone)"
  - "Key supplier raises price 30%+ or tariff shock"
reversal_signals:
  - "Review media reports the category label isn't sticking"
  - "Initial sell-through < 20% after 4 weeks"
```

### Inventory strategy by confidence × stage
| Confidence | Stage | Inventory strategy |
|---|---|---|
| High + Emerging | big gap | **Test capsule**: 2–3 SKUs, small qty, fast re-order option |
| High + Growth | partially covered | **Staged expansion**: re-order every 4–6 weeks based on sell-through |
| Medium | early | **Small curated**: start with low-MOQ SKUs (e.g. Ciele caps) |
| Low | directional | **Zero stock, monitor only** |

**Two principles (reduce risk, maximise utility):**
1. **Start small, re-order fast** — small test + short-lead-time supplier beats a big first order. Small loss if wrong, fast scale if right.
2. **Sell-through gate** — bake an exit condition into the recommendation: "stop re-ordering if 4-week sell-through < 30%."

**Stage line:**
> "We don't just say buy. We say how much, for how long, and what to watch for to stop. Trends turn."

**Honest caveat:** trend stage and sell-through gates are estimates, not validated sales data. Say "signal-based estimate, re-validated by actual sell-through after stocking."

---

## Where to collect Swiss/DACH data

**Layer A — Global early-signal sources (trends appear first):**
- Claude web search, Reddit RSS (no auth), gear media (GearJunkie, RoadTrailRun, Treeline), ISPO/OutDoor trade shows.

**Layer B — Swiss/DACH sources (transferability + assortment gap):**
- **Google Trends (geo=CH/DE/AT)** via pytrends — search momentum
- **Galaxus.ch / Digitec** — CH's biggest marketplace, CHF prices + ranks
- **Bächli Bergsport, Transa** — premium assortment gap check
- **Ochsner Sport / SportXX** — mass-market coverage
- **Amazon.de bestsellers** — DACH demand proxy

**Killer move:** rising in Google Trends CH + absent from Bächli/Transa = quantified assortment gap = highest opportunity.

---

## Scoring (transparent 4-component formula, 0–1)

1. **Source credibility (0–0.25)** — Google Trends / marketplace highest (hard data); Reddit lowest (weak signal)
2. **Evidence strength (0–0.25)** — URL + brand + product_name + price/rank
3. **Momentum / novelty (0–0.30)** — emerging keywords + Google Trends momentum value
4. **Early-market bonus (0–0.20)** — foreign origin = ahead of CH

**Opportunity rank** rewards multi-source diversity + transferability + `absent` coverage (the real gap).

Every score is traceable: "0.78 = credible source 0.22 + URL/brand 0.17 + emerging keyword 0.20 + US origin 0.20."

---

## Signal Cleaning (between Normalise and Deduplicate)

1. **Validation** — drop no-name, no-URL, fragment rows
2. **Text normalisation** — lowercase, collapse whitespace; **keep umlauts/accents** (äöüéè) for DACH terms
3. **Entity canonicalisation** — hand-curated `BRAND_ALIASES` + `MARKET_ALIASES` (not fuzzy matching)
4. **Numeric cleanup** — parse "$325" / "CHF 189.-" / "#3" to clean values
5. **Spam filter** — drop "buy now", "affiliate", "[deleted]", etc.
6. **Date sanity** — drop/flag stale or malformed dates

**Log what you drop:** "ingested 140 → cleaned 95 → deduped 60." Concrete evidence-quality story for the jury.

**Caveat:** don't over-clean. Keep aliases a curated allowlist — fuzzy matching at 16:00 with no test set silently corrupts output.

---

## Reusability (config swap)

Change `config.py` inputs only; collectors/scorer/clusterer code unchanged:
```python
SCENARIO = {
    "category": "cycling",                       # outdoor → cycling
    "web_queries": ["gravel bike emerging brands 2026", ...],
    "trend_keywords": ["gravel bike", "rennrad", ...],   # incl. German
    "competitor_urls": ["https://www.bike-components.de/", ...],
}
```
Caveat: far-off categories need new `CLUSTER_TAGS` / `BRAND_ALIASES`. Demo with an *adjacent* category (outdoor→cycling) for safety.
