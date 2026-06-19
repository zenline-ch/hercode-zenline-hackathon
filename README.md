# HerCode Zenline Hackathon

Build the retail radar that spots the next outdoor opportunity before it becomes obvious.

## Challenge

Retail teams are flooded with weak signals: TikTok clips, search spikes, niche communities, new materials, marketplace bestsellers, competitor drops, weather shifts, and regional lifestyle changes. The hard part is not finding more data. It is turning noisy signals into one clear answer: what should a retailer do next?

Your mission is to build a reusable system that detects emerging product, material, and brand opportunities from global and local market signals.

Use the shared scenario of a Swiss outdoor retailer to prove that the system works, but design it so the same method could be reused for another industry, market, product category, retailer, or brand.

The best submissions are not one-off research reports. They show a repeatable flow where inputs can change and the method still works.

This is the **B2B challenge**: help the retailer decide what emerging products, materials, brands, or product features are worth stocking, testing, or monitoring. There is also a companion **B2C challenge** by Scandit, focused on the in-store shopper experience: [`raffaelefarinaro/hercode-scandit-challenge`](https://github.com/raffaelefarinaro/hercode-scandit-challenge).

## Challenge Scenario

Detect promising emerging outdoor product, material, and brand opportunities for Switzerland or DACH. Think beyond "new product list": your system could uncover a rising product format, material, technology, feature, brand, supplier, or product gap.

Your system should answer:

- What are the emerging product, material, or brand opportunities?
- Where is the trend appearing first: US, Japan, Korea, Nordics, UK, DACH, Switzerland, or another market?
- What evidence supports the opportunity?
- Could the trend transfer into Switzerland or DACH?
- What should the retailer test, buy, launch, or monitor next?
- How reusable is the system beyond outdoor retail?

Start by asking what a Swiss outdoor retailer would actually want to know. For example:

- Which rising brands should the buying team watch, contact, or onboard?
- Which product types are growing in other markets before they become obvious in Switzerland?
- Which materials, technologies, or product features are becoming commercially meaningful?
- Which price bands, formats, sizes, or use cases are undercovered by local retailers?
- Which product, material, or brand gaps could create differentiation, margin, or customer loyalty?
- Which trends are just noise, and which deserve a test, supplier conversation, or deeper analysis?

Based on those questions, define your own methodology: choose sources, collect evidence, score signals, assess Swiss/DACH transferability, and turn the best findings into clear retail actions.

## Event Timeline

- Event date: June 19, 2026
- Meeting point: Zenline AI Office
- 10:00 CEST: Yoga session at the lake
- 10:45 CEST: Challenge reveal, Q&A, and kick-off
- 11:15-16:30 CEST: Build session
- 15:00 CEST: Pre-submission deadline
- 16:30 CEST: Final submission deadline
- 16:30 CEST: Miss Liquid Bar at the lake while the jury evaluates results
- 17:45 CEST: Back in the office for finalist presentations and awards

Teams should have 2-4 people. Discord is the main communication channel before and during the hackathon.

Intro session deck: [`slides/hercode-zenline-hackathon-intro.pptx`](slides/hercode-zenline-hackathon-intro.pptx).

## Zenline Retail Radar — Our Submission

### Setup

```bash
# Install dependencies
poetry install

# Copy and fill in your API key
cp .env.example .env
# edit .env → ANTHROPIC_API_KEY=sk-ant-...
```

### Run the Streamlit dashboard

```bash
poetry run streamlit run app.py
```

### Run the CLI pipeline

```bash
ANTHROPIC_API_KEY=sk-ant-... poetry run python -m zenline_radar.cli

# With live data sources:
ANTHROPIC_API_KEY=sk-ant-... poetry run python -m zenline_radar.cli --google-trends --amazon

# Limit to first N opportunities (faster for testing):
ANTHROPIC_API_KEY=sk-ant-... poetry run python -m zenline_radar.cli --limit 3
```

### Architecture

```
Q&A Setup (RetailerContext)
    ↓
Signal Collection (Google Trends · Amazon · Reddit · Manual)
    ↓
Relevance Filter + Deduplication
    ↓
Scoring Pipeline
  ├─ Trend Score       (deterministic: 90-day Google Trends slope)
  ├─ Transferability   (LLM: outdoor relevance + DACH gap)
  ├─ Opportunity       (LLM: availability gap + saturation + brand access)
  └─ Red-Flag          (LLM: supply chain + regulatory + brand concentration)
    ↓
Composite Score → Act Now / Watch ranked list
    ↓
Streamlit Dashboard (→ Lovable port)
```

See [`assets/architecture.png`](assets/architecture.png) for the pitch diagram
and [`docs/data-contract.md`](docs/data-contract.md) for the full scoring JSON schema.

---

## What's In This Repo

- [`SUBMISSION.md`](SUBMISSION.md): fill this in before submitting your fork.
- [`docs/challenge.md`](docs/challenge.md): deeper challenge brief and quality bar.
- [`docs/data-contract.md`](docs/data-contract.md): suggested structured fields for signals and recommendations.
- [`docs/evaluation.md`](docs/evaluation.md): judging rubric.
- [`examples/signals.csv`](examples/signals.csv): minimal example signal-row shape.
- [`slides/hercode-zenline-hackathon-intro.pptx`](slides/hercode-zenline-hackathon-intro.pptx): intro-session slide deck.

## Required Deliverables

Submit a fork of this repository that contains:

- Your code, scripts, notebooks, app, dashboard, API, or workflow.
- A completed [`SUBMISSION.md`](SUBMISSION.md).
- Clear setup and run instructions.
- Evidence sources used by your system, including URLs where possible.
- A ranked list of detected opportunities with confidence, risks, and next actions.
- An explanation or visualization of your dashboard or tool.
- Optional but encouraged: a short video walkthrough of your tool or dashboard.

Do not commit API keys, passwords, tokens, private datasets, or other secrets.

## Submission Process

1. Fork this repository into your own GitHub account or team organization.
2. Build your solution in the fork.
3. Update [`SUBMISSION.md`](SUBMISSION.md) with your team name, approach, run instructions, outputs, and demo links.
4. Push all final work to your fork before 16:30 CEST on June 19, 2026.
5. Submit the fork URL through the channel or form announced by the organizers.

The jury will review the code and submission artifacts from your fork.

## What You Can Build

You can build any useful part of the opportunity-detection system. Pick the part where your team can create the most leverage:

- Custom research agents or scripts.
- Scrapers for retailer, marketplace, social, or publication sources.
- Dashboards or review UIs for ranking signals.
- Notebooks for scoring, clustering, or enrichment.
- APIs that expose normalized results.
- Evidence deduplication, source credibility, or opportunity-scoring tools.
- Report generators that convert structured evidence into a business-ready recommendation.

Pick one direction and make it work well. One useful capability that runs live is better than four half-finished ideas.

A strong demo does not need to replace the whole flow. Improving one source, analysis step, scoring module, API, UI, or handoff artifact can be enough if the result is reusable and well demonstrated.

## Demo Target

By the end, the jury should be able to open your fork and understand:

- What product, material, or brand opportunity your system found.
- Why the opportunity matters now.
- Which sources support it.
- Whether it can realistically work in Switzerland or DACH.
- What the retailer should test next.
- How your approach could run again for another category or market.

For the final session, be ready to present a short live demo and answer questions. Keep the demo focused on what works: the jury can inspect technical depth from your fork, code, data, and artifacts.

## Suggested Evidence Sources

Combine multiple signal types where possible:

- Web research: publications, brand pages, retailer listings, forums, outdoor events, market articles.
- Search trends: search momentum, rising queries, local vocabulary, and market comparisons.
- Social signals: creator visibility, hashtags, product usage, and weak lifestyle signals.
- Marketplace or competitor scans: product formats, brands, prices, bestseller or ranking hints, and assortment examples.
- Participant/custom data: scraper output, API pulls, notebooks, manual store checks, CSV files, or Google Sheets.

See [`docs/data-contract.md`](docs/data-contract.md) for a recommended output schema.

## Evaluation

The jury will evaluate:

- Signal detection: can the system find a real emerging product, material, or brand opportunity from messy sources?
- Evidence quality: are trends backed by sources, not guesses?
- Transferability: does the system reason whether a global trend can work in Switzerland or DACH?
- Business actionability: does the output lead to a clear retail decision?
- Reusability: could the same flow be reused for another industry, market, or category with input changes?
- Technical architecture: is the system robust, understandable, and practical to run during the hackathon?

More detail is available in [`docs/evaluation.md`](docs/evaluation.md).

## Organizers And Partners

- Organizers: Zenline AI, HerCode
- Partners: Scandit, Miss Liquid
