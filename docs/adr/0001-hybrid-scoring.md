# ADR 0001: Hybrid scoring — deterministic Trend + LLM for Transferability, Opportunity, and Red-Flag

## Status
Accepted

## Context
The scoring system has four pillars. The Trend pillar can be computed deterministically from scraped search data (Google Trends 90-day slope). The other three pillars — Transferability, Opportunity, and Red-Flag — require contextual judgment that is difficult to express as a rule: whether a specific market pair makes cultural and commercial sense, whether a brand is accessible to a small Swiss retailer, whether regulatory hurdles exist. These judgments change per opportunity and per market pair.

## Decision
Use deterministic computation for the Trend pillar only. Use a single LLM call per opportunity for all three contextual pillars (Transferability, Opportunity, Red-Flag), returning structured JSON with scores and one-sentence justifications per sub-dimension.

The LLM receives: opportunity name, keyword, brand, signal breadth, markets seen, evidence URLs, the specific comparison market → target market pair, competitor URLs, niche, and active risk factors.

## Why one call for three pillars
Bundling all three LLM pillars into one call keeps latency and cost manageable (one API call per opportunity instead of three) and ensures the justifications are internally consistent — the same model reasons over the same context in one pass.

## Scoring transparency
Every sub-dimension score (1–5) is accompanied by a one-sentence explanation from the LLM. These sentences are shown verbatim in the UI. No post-processing or paraphrasing layer is applied. The Composite Score formula is fully deterministic given the pillar totals: `avg(Trend · Transferability · Opportunity · (1 − Red-Flag))` with equal weights by default. Weights are configurable via UI sliders and stored in `RetailerContext.score_weights`.

## Detection transparency
Signal detection uses explicit numeric thresholds, exported as constants from `scraper.py`:
- `SEARCH_MIN_SCORE = 2.0` — Google Trends 90-day slope × 10 must exceed this
- `MARKETPLACE_MIN_MATCHES = 1` — keyword must appear in at least this many top-50 Amazon bestseller titles
- Curated signals are always emitted (pre-vetted)

These constants are displayed in the UI during the analysis run so the audience can see exactly what rule triggered each signal.

## Consequences
- Each LLM sub-dimension score is directly traceable to a justification sentence shown in the UI.
- Trend scoring is fully deterministic and rerunnable without an API key.
- Transferability, Opportunity, and Red-Flag require one LLM API call per opportunity (~1–3 s each).
- A demo mode with cached pre-scored results bypasses all LLM calls, making the system runnable offline.
- Detection thresholds are single constants in `scraper.py` — easy to tune and explain to a non-technical audience.
