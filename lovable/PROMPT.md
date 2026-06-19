# Zenline Retail Radar — Lovable Prompt

Paste the text below into Lovable to generate the frontend.
The backend API runs at `http://localhost:8000` (FastAPI — `poetry run uvicorn api:app --reload`).

---

## Prompt

Build a web app called **Zenline Retail Radar** — a tool for outdoor retail buyers to discover emerging product, brand, and material opportunities before competitors do.

**Tech stack:** React, TypeScript, Tailwind CSS, shadcn/ui. Dark theme throughout (`background: #0f0f1a`, accent purple `#7c3aed`, green `#10b981`, amber `#f59e0b`).

---

### App structure — 3 pages

**Page 1: Setup**
**Page 2: Analysis (running)**
**Page 3: Results**

Use React state to move between pages. No routing needed.

---

### Page 1 — Setup

Header: `🔭 Zenline Retail Radar` + subtitle "Detect emerging outdoor opportunities before competitors do."

A single card with these sections:

**Retailer Profile** (2 columns)
- Target market: text input, default "CH"
- Niche: text input, default "outdoor retail"
- Comparison markets: text input, default "SE, CA, US, NO" (comma-separated)

**Category Keywords** — textarea, pre-filled with these 14 keywords (one per line):
```
trail running shoes
merino wool base layer
recycled down jacket
gravel bike
inflatable kayak
lightweight tent
solar panel backpack
cork yoga mat
bamboo hiking poles
arc'teryx
salewa
mammut
ortovox
picture organic
```

**Competitor URLs** — textarea (one per line), pre-filled:
```
https://www.bächli-bergsport.ch
https://www.transa.ch
https://www.ochsner-sport.ch
```

**Risk Factors** — three checkboxes (all checked by default):
- Supply chain risk
- Regulatory risk
- Brand concentration

**Score Weights** — 4 horizontal sliders (0.0–2.0, step 0.1, default 1.0):
- Trend, Transferability, Opportunity, Red-Flag (inverse)

**Data & AI section** (2 columns):
- Left: checkboxes "Google Trends (live, ~30s)" and "Amazon Bestsellers (live, ~10s)" — both unchecked
- Right: toggle "Use cached demo results (no API calls)" — ON by default. Text input for Anthropic API key (password type, hidden if toggle is on).

Big primary button at bottom: "Run Analysis →"

On submit, move to Page 2.

---

### Page 2 — Analysis

Show a step-by-step progress view. Each step appears sequentially with a small animation.

**Header:** "🔭 Analysing [niche] opportunities for [target_market]"

**Step 1 — Detection rules** (shown immediately as 3 cards in a row):
- 📋 Curated research — "Expert-vetted signals · Always detected"
- 📈 Google Trends — "90-day slope × 10 · Detected if score ≥ 2.0"
- 🛒 Amazon Bestsellers — "Keyword in top-50 titles · Detected if matches ≥ 1"

**Step 2 — Signal detection** (animated table that builds row by row):
Columns: Keyword | Source | Market | Score | Confidence

Rows appear one by one with a fade-in. Show a pulsing "scanning..." row at the bottom while loading.

Fetch from `GET /api/mock-results` if demo mode, or `POST /api/analyze` if live.

**Step 3 — Filter & deduplicate** (shown after signals load):
A second table: Opportunity | Markets | Signal breadth | Best score | Confidence
Rows fade in.

**Step 4 — AI Scoring** (progress bar 0→100% animating over 1.5 seconds in demo mode):
"Loading cached demo scores..." then "✓ 8 opportunities scored"

Auto-navigate to Page 3 when done.

---

### Page 3 — Results

**Header row:**
- Left: `🔭 Zenline Retail Radar` + subtitle "[target_market] · [niche] · [N] opportunities · Comparison: [markets]"
- Right: "← New analysis" button

**Two sections:**

#### ⚡ Act Now
Section header with green left border.

#### 👁 Watch
Section header with amber left border.

Split results by `urgency === "act_now"` vs others.

---

### Opportunity Card

Each opportunity is an expandable card (top 3 auto-expanded). Card has a subtle left border — green for act_now, amber for watch.

**Card header (always visible):**
`#[rank]  [name]  ·  [brand]  —  [composite_score as %]`
Two chips inline: stage chip (purple=emerging, green=growing, amber=mainstream, red=declining) + urgency chip.
Below: bold buy recommendation text.

**Card body (expanded):**

Left column (1/3 width) — Score bars:
Each bar is a label + percentage + colored fill bar (height 8px, rounded):
- Composite score — white fill
- Trend (growth X.X/10) — indigo `#6366f1`
- Transferability — purple `#8b5cf6`
- Opportunity — cyan `#06b6d4`
- Red-Flag risk (lower is better) — red `#ef4444`

Right column (2/3 width) — Explainability:
Four rows, each: **bold label** — sentence text, then source citation badges below.

Source citation badges are small pill buttons with a border. Format:
`[Source Label]` — clicking opens the URL in a new tab.

Rows:
1. **Why it's trending** — `explainability.why_trending` — sources from `explainability_sources.why_trending`
2. **Why it fits Switzerland** — `explainability.why_fits_switzerland` — sources from `explainability_sources.why_fits_switzerland`
3. **Why act now** — `explainability.why_opportunity_now` — sources from `explainability_sources.why_opportunity_now`
4. **⚠ Caution** (amber text) — `explainability.why_to_be_cautious` — sources from `explainability_sources.why_to_be_cautious`

---

### API calls

```typescript
// Demo mode — get pre-scored results
const results = await fetch('http://localhost:8000/api/mock-results').then(r => r.json())

// Live mode — run full pipeline
const { results } = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    target_market: 'CH',
    comparison_markets: ['SE', 'CA', 'US', 'NO'],
    niche: 'outdoor retail',
    category_keywords: [...],
    competitor_urls: [...],
    risk_factors: ['supply_chain', 'regulatory', 'brand_concentration'],
    score_weights: { trend: 1.0, transferability: 1.0, opportunity: 1.0, red_flag: 1.0 },
    enable_search: false,
    enable_marketplace: false,
    use_mock: true,
    api_key: null
  })
}).then(r => r.json())
```

---

### Result data shape (TypeScript types)

```typescript
interface Source {
  label: string
  url: string
}

interface ScorePillar {
  total: number
  growth?: number
  outdoor_relevance?: number
  dach_availability_gap?: number
  availability_gap?: number
  retail_saturation?: number
  brand_availability?: number
  supply_chain_risk?: number
  regulatory_risk?: number
  brand_concentration?: number
  explanation?: string
}

interface Opportunity {
  id: string
  name: string
  brand: string
  product_name: string
  markets: string[]
  signal_breadth: number
  rank: number
  composite_score: number
  trend_stage: 'emerging' | 'growing' | 'mainstream' | 'declining'
  urgency: 'act_now' | 'watch'
  buy_recommendation: string
  scores: {
    trend: ScorePillar
    transferability: ScorePillar
    opportunity: ScorePillar
    red_flag: ScorePillar
  }
  explainability: {
    why_trending: string
    why_fits_switzerland: string
    why_opportunity_now: string
    why_to_be_cautious: string
  }
  explainability_sources: {
    why_trending: Source[]
    why_fits_switzerland: Source[]
    why_opportunity_now: Source[]
    why_to_be_cautious: Source[]
  }
  evidence_urls: string[]
}
```

---

### Design details
- Font: Inter or system-ui
- Cards: `background: #1e1e2e`, border-radius 12px, subtle shadow
- Stage chips: pill shape, 0.7rem, all-caps, letter-spacing 0.06em
- Score bars: 8px height, border-radius 4px, background `#374151`
- Source badges: border `#374151`, hover border `#6366f1`, font-size 0.72rem
- Section dividers: `border-bottom: 2px solid #374151`
- Animations: fade-in on card mount (opacity 0→1, translateY 8px→0, 200ms)
- No emojis in code — use Lucide icons instead
