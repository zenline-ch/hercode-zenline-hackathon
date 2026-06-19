# Suggested Data Contract

Use any format that fits your solution. Structured CSV or JSON is recommended so the jury can inspect and rerun your work.

## Signal Row

| Field | Description |
| --- | --- |
| `source` | Source name, such as retailer site, publication, TikTok, marketplace, Google Trends, API, or manual research. |
| `market` | Market where the signal appears, such as CH, DACH, US, Japan, Korea, Nordics, or UK. |
| `keyword` | Keyword, query, hashtag, product phrase, or category label. |
| `signal_name` | Human-readable name of the trend or opportunity. |
| `signal_type` | `search`, `social`, `web`, `marketplace`, `competitor`, `manual`, `api`, or another explicit type. |
| `product_name` | Product or example item, if relevant. |
| `brand` | Brand, supplier, creator, retailer, or source entity, if relevant. |
| `price` | Observed price, if relevant and source-backed. |
| `rank` | Bestseller rank, listing position, popularity rank, or internal rank, if relevant. |
| `url` | Evidence URL. |
| `signal_score` | Your score for signal strength. Define the scale in your submission. |
| `confidence` | `high`, `medium`, `low`, or a documented numeric confidence scale. |
| `notes` | Short evidence notes and limitations. |
| `observed_at` | Date or timestamp when the signal was observed. |
| `artifact_type` | `csv`, `json`, `markdown`, `pdf`, `dashboard`, `screenshot`, `api`, or another explicit type. |
| `artifact_uri` | Path or URL to the generated artifact. |
| `created_by_tool` | Script, model, notebook, scraper, API, or manual workflow that created the row. |

## Recommendation Row

| Field | Description |
| --- | --- |
| `rank` | Recommendation rank. |
| `opportunity` | The recommended opportunity. |
| `first_observed_market` | Where the signal appears first or strongest. |
| `evidence_summary` | Concise summary of supporting evidence. |
| `evidence_urls` | List of source URLs. |
| `transferability` | Assessment for Switzerland or DACH. |
| `coverage_status` | `covered`, `partially_covered`, `absent`, `unknown`, or `not_relevant`. |
| `recommended_action` | What the retailer should test, buy, launch, or monitor. |
| `confidence` | Confidence score or label. |
| `risks` | Main risks and missing evidence. |

## Example Files

See [`../examples/signals.csv`](../examples/signals.csv) for a small example shape. Replace it with your own data or add your own files.

---

## Scoring Layer Output (per Opportunity)

The scoring pipeline produces one JSON object per opportunity. This is the shape consumed by the frontend.

```json
{
  "id": "gravel-ebikes",
  "name": "Gravel E-Bikes",

  "trend_stage": "growing",
  "urgency": "act_now",
  "buy_recommendation": "Scale up · negotiate supplier terms",
  "composite_score": 0.82,

  "scores": {

    "trend": {
      "total": 0.76,
      "growth": 8.2,
      "geographic_spread": 4,
      "noise_score": 4.1,
      "recency_days": 12
    },

    "transferability": {
      "total": 0.91,
      "outdoor_relevance": 5,
      "climate_fit": 4,
      "dach_availability_gap": 4,
      "explanation": "Matches alpine commuter culture; Flyer and Stromer validate DACH demand"
    },

    "opportunity": {
      "total": 0.75,
      "availability_gap": 4,
      "retail_saturation": 3,
      "brand_availability": 4,
      "explanation": "Low CH saturation in gravel segment; German distributor ships direct"
    }

  },

  "explainability": {
    "why_trending":         "90-day search slope +8.2 in Nordics and US; 4 independent source types agree",
    "why_fits_switzerland": "Matches alpine commuter culture; Flyer and Stromer validate DACH demand",
    "why_opportunity_now":  "Low CH saturation in gravel segment; German distributor ships direct"
  },

  "risk_flags": ["supply_chain"],

  "signals": [
    {
      "source": "Google Trends",
      "source_type": "search",
      "market": "SE",
      "keyword": "gravel e-bike",
      "signal_score": 8.2,
      "url": "https://trends.google.com/trends/explore?q=gravel+e-bike&geo=SE",
      "observed_at": "2026-06-19"
    },
    {
      "source": "Reddit",
      "source_type": "social",
      "market": "US",
      "keyword": "gravel ebike",
      "signal_score": 6.1,
      "url": "https://reddit.com/r/gravelcycling/comments/example",
      "observed_at": "2026-06-17"
    },
    {
      "source": "Amazon Bestsellers",
      "source_type": "marketplace",
      "market": "US",
      "keyword": "gravel electric bike",
      "signal_score": 7.4,
      "url": "https://amazon.com/best-sellers-sports-outdoors",
      "observed_at": "2026-06-19"
    }
  ],

  "evidence_urls": [
    "https://trends.google.com/trends/explore?q=gravel+e-bike&geo=SE",
    "https://reddit.com/r/gravelcycling/comments/example",
    "https://amazon.com/best-sellers-sports-outdoors"
  ]
}
```

### Field reference

| Field | Scale | Source | Notes |
| --- | --- | --- | --- |
| `trend_stage` | `emerging` · `growing` · `mainstream` · `declining` | Derived from Trend sub-scores | Drives `buy_recommendation` |
| `urgency` | `act_now` · `watch` | LLM (transferability step) | Used to split output into two sections |
| `composite_score` | 0–1 | Weighted avg of three pillar totals | Default equal weight, configurable via UI |
| `trend.growth` | 0–10 | Google Trends 90-day slope | Higher = faster rising |
| `trend.geographic_spread` | 0–5 | Count of distinct markets with signal | Higher = more markets confirm the trend |
| `trend.noise_score` | 0–5 | Ratio of multi-source vs social-only signals | Higher = less noisy |
| `trend.recency_days` | integer | Avg days since signals were observed | Lower = fresher evidence |
| `transferability.*` | 1–5 | LLM-scored | 5 = strong fit for Switzerland / DACH |
| `opportunity.*` | 1–5 | LLM-scored | 5 = large gap / low saturation / high access |
| `*.total` | 0–1 | Normalized avg of sub-dimensions | Ready for weighted composite |
| `*.explanation` | string | LLM | Same text as matching `explainability` field |
| `risk_flags` | string[] | LLM, grounded in Q&A risk factors | Displayed as warning badges in UI |

### Buy recommendation by trend stage

| Trend Stage | Buy Recommendation |
| --- | --- |
| `emerging` | Test order · small stock · monitor closely |
| `growing` | Scale up · negotiate supplier terms |
| `mainstream` | Evaluate margin · assess competitive positioning |
| `declining` | Wind down · evaluate clearance strategy |
