# Frontend integration notes (Lovable -> Python backend)

This directory is the Lovable-designed production frontend (React + TanStack Router + Zustand +
shadcn/ui). It currently runs entirely on **mock data** (`src/lib/domain.ts`: `RAW_DATA`,
`OPPORTUNITIES`) -- there is no backend call anywhere yet. The Python backend in
[`../app/retail_radar/`](../app/retail_radar/) is the real, working pipeline (see
[`../ARCHITECTURE.md`](../ARCHITECTURE.md), [`../diagram.md`](../diagram.md)).

Both were built independently and converged on the same shape: a `RetailerContext` Q&A wizard,
weighted composite scoring with sliders, an Act Now / Watch split, and per-opportunity
explainability. That convergence is itself worth saying on stage -- two people independently
arrived at the same architecture. This file is the field-by-field map to actually wire them
together, post-hackathon (not attempted live, intentionally, to avoid breaking either side close
to the deadline -- see `app/README.md` "Replacing seed data" for the equivalent backend-side note).

## RetailerContext: `src/lib/domain.ts` <-> `app/retail_radar/schema.py`

| Frontend field | Backend field | Note |
| --- | --- | --- |
| `retailerName` | -- (none) | Display-only; add to backend `RetailerContext` if needed |
| `targetMarket` | `target_market` | Same concept |
| `comparisonMarkets` | `comparison_markets` | Same concept |
| `niche` | `niche` | Same concept |
| `demographic` | -- (none) | Backend doesn't model this yet |
| `competitorUrls` | `competitor_urls` | Same concept |
| `riskFactors` | -- (none, closest: `risk_taxonomy.json`) | Frontend's are free-text; backend's are a fixed taxonomy. Reconcile before wiring. |
| `weights.trend/transfer/opportunity/redflag` | `scoring_weights.momentum/transferability/coverage_gap/risk` | **4 vs 5 pillars** -- frontend has no separate `breadth` weight; backend's `breadth` would need a fixed/folded-in weight if frontend sliders drive it |

## Opportunity: `domain.ts` `Opportunity` <-> backend `recommendations.json` entry

| Frontend field | Backend field | Note |
| --- | --- | --- |
| `trend.total` / `trend.subs.Growth` | `scores.momentum.total` / `scores.momentum.growth` | Backend also has `geographic_spread` as a second sub-dim the frontend doesn't model |
| `transfer.total` / `transfer.subs["Outdoor relevance"]`, `["DACH availability gap"]` | `scores.transferability.total` / `.outdoor_relevance`, `.dach_availability_gap` | Field names match almost exactly (added in `app/retail_radar/pipeline/scorer.py::_transferability_subdims`) -- backend also has `climate_fit`, frontend doesn't (yet) |
| `opportunity.total` / `.subs["Availability gap"]`, `["Retail saturation"]`, `["Brand availability"]` | `scores.coverage_gap.total` / `.availability_gap`, `.retail_saturation`, `.brand_availability` | **Exact same 3 named sub-dimensions**, backend added them to match this design intent |
| `redflag.total` (high = risky) | `scores.risk.total` (high = **safe**, inverted!) | **Inversion mismatch** -- backend's `risk.total` is `1 - risk`, frontend's `redflag.total` is raw risk. Must flip one side when mapping. |
| `transferCaveat.confidence` / `.reason` | `confidence` (top-level) / `scores.transferability.reason` | Roughly equivalent |
| `trendStage` | `trend_stage` | Backend has `mainstream`+`declining` reachable; frontend's `stageOf()` threshold logic differs -- don't assume same opportunity gets the same stage from both |
| `explain.why_trending/why_fits_target/why_opportunity_now` | `explainability.why_trending/why_fits_switzerland/why_opportunity_now` | Same 3, frontend adds a 4th: `why_to_be_cautious` (backend has no equivalent field -- closest is `risk_flags`) |
| `compositeScore()` | `composite_score` | **Different formula** -- frontend: `(trend + transfer + opportunity + redflag_inverted) / 4` unweighted-average style; backend: weighted sum of 5 pillars. Will NOT produce the same number for the same inputs. |
| `urgency()` | `urgency` | Frontend: deterministic threshold (`composite >= 0.65` and stage is growing/emerging). Backend: LLM/heuristic-derived + a hard guard forcing `watch` when `confidence == "low"`. Different mechanism, same intent. |

## Recommended next step (not done here, by design)

Don't try to make the two formulas produce identical numbers -- that's a rabbit hole. Instead:
write one adapter function (Python, in `app/retail_radar/pipeline/`) that takes a
`recommendations.json` opportunity and emits an object literally shaped like `domain.ts`'s
`Opportunity` interface, including the `redflag` inversion. Export that as a static
`opportunities.json` the frontend fetches instead of importing `OPPORTUNITIES` from `domain.ts`.
This matches the "frontend stays a dumb consumer of backend JSON" rule already established in
`diagram.md` §6.4.
