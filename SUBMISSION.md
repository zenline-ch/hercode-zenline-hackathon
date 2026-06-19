# Submission

> **IMPORTANT FOR REVIEWERS: all of this team's work is on the `feature/giulia` branch, not
> `main`. Please review https://github.com/angelaschereraiza/hercode-zenline-hackathon/tree/feature/giulia
> -- the default branch (`main`) does not contain the submission.**

Complete this file in your fork before submitting.

## Team

- Team name: The Fine Tuners
- Team members: Seung ju Paek, Katerina Vitsaxaki, Angela Scherer, Giulia Zobrist
- GitHub fork URL: https://github.com/angelaschereraiza/hercode-zenline-hackathon
- Demo URL, if any: _not deployed yet -- run locally per "How To Run" below, or deploy via app/README.md_
- Video walkthrough URL, if any: _none -- optional_

## Summary

**Retail Radar**: a reusable, config-driven pipeline that detects emerging outdoor-retail
opportunities, scores them with a transparent 5-pillar formula, checks whether they're actually
covered on the Swiss shelf, and turns the result into buy/test/monitor recommendations -- served
through an AI chat + dashboard.

We built the full opportunity-detection system end to end: collection (offline seed dataset +
a working live Reddit fetcher), cleaning, deduplication, hybrid scoring, lead-lag analysis,
synthesis into ranked recommendations, and a Streamlit frontend (chat + dashboard) that will be
swapped for a Lovable frontend later without any backend changes. Full design rationale is in
[`ARCHITECTURE.md`](ARCHITECTURE.md) and [`diagram.md`](diagram.md).

## How To Run

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. Runs with **zero API keys** (deterministic fallbacks for
scoring and chat). Optionally set `ANTHROPIC_API_KEY` for LLM-reasoned transferability scoring
and a real conversational chat -- see [`app/README.md`](app/README.md) for details, plus free
deployment instructions (Streamlit Community Cloud, shareable link).

To run just the pipeline and print scores without the UI:

```bash
python3 -m retail_radar.pipeline.run_pipeline
```

## Inputs

- Market: target market `CH`; comparison/early-signal markets `US, Nordics, Japan, Korea, UK`
  (configurable per run via the in-app `RetailerContext` wizard)
- Category: `outdoor` (any niche/category string works -- swap it live to prove reuse)
- Persona: `large_retailer` / `boutique` / `individual_dtc` (`app/retail_radar/config/personas.json`)
- Seed keywords: gravel running, bio-Dyneema/A-TPU foam, run-culture brands (Satisfy/Norda/Ciele),
  ultralight/bikepacking crossover, mycelium/bio-synthetic membranes
- Sources: 15 registered sources spanning search, social, marketplace, competitor, government,
  and web/media, each with a credibility weight -- `app/retail_radar/config/sources.json`
- Languages: English seed data; pipeline and cleaner explicitly preserve German/French umlauts
  and accents for DACH terms
- External files, APIs, or datasets: `app/retail_radar/data/seed_signals.json` (offline dataset,
  24 signals across the 5 opportunities above); `app/retail_radar/resources/scrape_targets.json`
  (real scrape-target registry for going live); optional Anthropic API for LLM scoring/chat

## Outputs

- Dashboard or UI: two frontends. (1) `app/streamlit_app.py` -- a working Streamlit app
  (RetailerContext wizard, AI chat, Act Now / Watch dashboard) wired to the **real backend**,
  runnable today. (2) `frontend/` -- a Lovable-built React/TanStack/shadcn chat-wizard + dashboard
  with the intended production UX, currently on mock data with no backend call. Both converged on
  the same RetailerContext -> Act Now/Watch -> explainability shape independently; field-by-field
  integration mapping is in `frontend/INTEGRATION.md`.
- Report: `app/retail_radar/data/recommendations.json` (one record per opportunity, matching the
  schema in `ARCHITECTURE.md` §10)
- Structured data: `app/retail_radar/data/signals.csv` (data-contract Signal rows), downloadable
  directly from the app sidebar
- API endpoint: none yet -- the pipeline is called in-process; see `diagram.md` §6 for the planned
  static-JSON / FastAPI path when the Lovable frontend is wired in
- Screenshots or visuals: Mermaid diagrams in `diagram.md`; live dashboard screenshots _TODO_

## Ranked Opportunities

Confidence = `high` (>=0.70), `medium` (>=0.45), `low` (below), derived from `composite_score`
(weighted average of Breadth, Momentum, Transferability, Coverage Gap, and Risk -- see
`ARCHITECTURE.md` §6). This run used the default persona (`large_retailer`) and equal pillar
weights; full per-opportunity evidence is in `recommendations.json`.

| Rank | Opportunity | Evidence | Confidence |
| --- | --- | --- | --- |
| 1 | Gravel Running Shoes | Composite 0.735. Named SKUs (La Sportiva Prodigio 2, Keen Roam) priced and reviewed in US gear media; rising in Google Trends US/CH; **absent from Bachli Bergsport and Transa** as of the latest assortment scan -> quantified Swiss shelf gap. |
| 2 | Ultralight / Bikepacking Crossover | Composite 0.722. Reddit + Google Trends momentum in the US; corroborated by official BFS (Swiss Federal Statistical Office) tourism stats showing growth in self-supported multi-day cycling; absent from Ochsner Sport. |
| 3 | Run-Culture Brands (Satisfy / Norda / Ciele) | Composite 0.59. Pinterest/Reddit lifestyle buzz plus a real CH listing (Ciele caps on Galaxus, very limited stock); absent from Ochsner Sport; below this persona's confidence threshold -> monitor, not buy. |
| 4 | Bio-Dyneema / A-TPU Foams | Composite 0.584. Material story confirmed in gear media (Norda 005), partially covered in CH (DTC-only channel via Galaxus/Transa) -> staged/flagged-risk recommendation, not a clean buy. |
| 5 | Mycelium / Bio-Synthetic Membranes | Composite 0.363, **low confidence**. Press-release/R&D coverage only, near-zero search volume, zero retail SKUs (Galaxus and Transa both confirm no commercial product exists) -> `not_relevant` coverage, watch only, no buy. |

This is also the system's core honesty proof: opportunity #1 gets a clean buy signal because the
evidence is commercial proof; opportunity #5 is explicitly flagged as a directional signal only,
even though it has real media buzz, because there is nothing to actually stock.

## Evidence Trail

- `app/retail_radar/data/seed_signals.json` -- 24 raw signals, each with a source, market,
  evidence URL, and observed date (offline dataset standing in for live scraping during the
  hackathon build)
- `app/retail_radar/data/signals.csv` / `recommendations.json` -- generated, inspectable
  artifacts matching the data contract in `docs/data-contract.md`
- `app/retail_radar/resources/scrape_targets.json` -- real base domains and request templates for
  every source (Google Trends, Reddit, Galaxus, Zalando, Amazon, Ochsner Sport, SportXX,
  Decathlon Switzerland, Bachli Bergsport, Transa, Brack.ch, Microspot, Manor, Globus, Pinterest,
  BFS, gear media), flagged by what's confirmed reachable vs. what needs a manual check
- `app/retail_radar/resources/fetch_reddit.py` -- a tested, working live fetcher (confirmed
  pulling real current posts from r/trailrunning during development, including an organic mention
  of "La Sportiva Prodigio Max")

## Reusability

Every module downstream of `collectors.py` only depends on the `Signal` dataclass shape -- not on
outdoor retail or Switzerland specifically. To reuse the system:

- **Category swap**: change `niche` in the `RetailerContext` wizard (e.g. `outdoor` -> `cycling`);
  scoring, cleaning, and dedup logic are unchanged.
- **Market swap**: change `target_market` / `comparison_markets`; the lead-lag and transferability
  logic are market-agnostic by construction.
- **Persona swap**: switch `large_retailer` / `boutique` / `individual_dtc` live and watch buy
  recommendations re-derive with no code change (`app/retail_radar/config/personas.json`).
- **New sources**: add a row to `app/retail_radar/config/sources.json` (credibility) and
  `app/retail_radar/resources/scrape_targets.json` (where to scrape it) -- no code change required
  for the scoring pipeline to start using it.

## Known Limitations

- The pipeline currently runs on an **offline seed dataset**, not live scrapers. Only Reddit has a
  tested, working live fetcher (`resources/fetch_reddit.py`); Google Trends, marketplace, and
  competitor-site collection are documented in `scrape_targets.json` but not yet wired into
  `collectors.py`.
- Transferability scoring and the AI chat use a deterministic fallback unless `ANTHROPIC_API_KEY`
  is set -- the fallback is evidence-grounded but not LLM-reasoned.
- Marketplace/competitor search-path URLs in `scrape_targets.json` are best-effort templates for
  sites we didn't live-test (Galaxus, Zalando, Ochsner Sport, etc.) -- verify before automating.
- Clustering signals into opportunities is a manual `opportunity_id` tag in the seed data, not
  automated NLP clustering.
- Lead-lag and trend-stage estimates are signal-based, not validated against real sell-through.
- No persisted multi-user state yet (each session recomputes from the same seed data); no
  authentication (not needed for the <20-person demo audience).

## Architecture Notes

Pipeline: `collect -> clean -> deduplicate -> score (hybrid) -> lead-lag -> synthesise -> present`,
orchestrated by `app/retail_radar/pipeline/run_pipeline.py`. Scoring is a 5-pillar weighted
composite (Breadth, Momentum, Transferability, Coverage Gap, Risk) -- deterministic everywhere
except Transferability, which optionally uses an LLM grounded in the specific market pair (see
ADR-style rationale in `ARCHITECTURE.md` §6). The Streamlit app (`app/streamlit_app.py`) is a thin
presentation layer: a `RetailerContext` setup wizard, an AI chat that answers only from computed
opportunity data and deep-links into the dashboard, and a dashboard rendering the same JSON
contract a future Lovable frontend will consume. Full diagrams in [`diagram.md`](diagram.md).
