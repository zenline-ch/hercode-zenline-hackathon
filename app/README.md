# Retail Radar -- draft app (chat + dashboard)

Backend pipeline (`retail_radar/`) + a Streamlit chat/dashboard frontend, built directly from
[`../ARCHITECTURE.md`](../ARCHITECTURE.md) and [`../diagram.md`](../diagram.md). This is the
**draft frontend** referenced in `diagram.md` §6 -- it exists so the team has a working,
deployable demo today. When the Lovable frontend is ready, it can read the exact same
`recommendations.json` contract and replace `streamlit_app.py` with zero backend changes.

## What's in here

```
app/
  retail_radar/
    schema.py              # Signal / RetailerContext dataclasses (the data contract)
    config/                # sources.json, personas.json, risk_taxonomy.json, coverage_keywords.json
    data/                  # seed_signals.json (offline fallback) + generated signals.csv / recommendations.json
    pipeline/               # collectors -> cleaner -> dedup -> scorer -> leadlag -> synthesiser -> run_pipeline
    chat/assistant.py      # AI chat, grounded in computed opportunities
  streamlit_app.py         # RetailerContext wizard -> chat -> dashboard
  requirements.txt
```

## Run locally

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. Works with **zero API keys** -- the chat and the
Transferability score fall back to deterministic logic if `ANTHROPIC_API_KEY` isn't set
(see `retail_radar/pipeline/scorer.py` and `retail_radar/chat/assistant.py`).

### Optional: enable the real LLM chat + transferability scoring

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# optional, defaults to claude-3-5-sonnet-latest
export ANTHROPIC_MODEL=claude-3-5-sonnet-latest
streamlit run streamlit_app.py
```

### Run just the pipeline (no UI), to sanity-check scoring

```bash
python3 -m retail_radar.pipeline.run_pipeline
```

Prints the ingest/clean/dedup log and every opportunity's score, confidence, coverage, and
buy recommendation. Writes `retail_radar/data/signals.csv` and
`retail_radar/data/recommendations.json`.

## Deploy for free, shareable by link (good for the <20 people on the team/jury)

1. Push this repo to GitHub (already done).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. "New app" -> pick this repo/branch -> **main file path: `app/streamlit_app.py`**.
4. (Optional) Under "Advanced settings -> Secrets", add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Deploy. You get a public `*.streamlit.app` URL -- send that link to the team/jury. Free tier
   easily covers <20 concurrent users.

No Docker, no server to manage, no cost. If the free tier's cold-start is a concern right before
a live demo, open the link a few minutes early to warm it up.

## Editing the source-credibility list (no code changes needed)

Edit `retail_radar/config/sources.json` -- add a row with `name`, `source_type`, `credibility`
(0-1), and it's picked up automatically by the Breadth pillar in `scorer.py`. Same pattern for
personas (`personas.json`), risk flags (`risk_taxonomy.json`), and coverage-status keyword
matching (`coverage_keywords.json`).

## Replacing seed data with live collectors

`retail_radar/pipeline/collectors.py` currently returns `seed_signals.json` (offline, zero API
keys, never breaks live). To go live, replace the body of `collect()` with real `pytrends`,
marketplace, and competitor-scraper calls -- keep the same `Signal` shape and nothing downstream
(cleaner, dedup, scorer, synthesiser, chat, dashboard) needs to change.
