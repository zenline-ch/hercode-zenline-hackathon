// Domain types + mock data + deterministic scoring. Everything here is meant
// to be read by a human — every number returned has a stated rule behind it.

export type SourceType = "search" | "marketplace" | "manual";

export interface RetailerContext {
  retailerName: string;
  targetMarket: string;
  comparisonMarkets: string[];
  niche: string;
  demographic: string;
  competitorUrls: string[];
  riskFactors: string[];
  weights: { trend: number; transfer: number; opportunity: number; redflag: number };
}

export const DEFAULT_CONTEXT: RetailerContext = {
  retailerName: "Bergsteiger AG",
  targetMarket: "Switzerland",
  comparisonMarkets: ["Sweden", "Canada"],
  niche: "Outdoor & alpine apparel",
  demographic: "All adults, 25–55",
  competitorUrls: ["transa.ch", "bachercher.ch"],
  riskFactors: ["EU textile regulation", "CHF/USD volatility"],
  weights: { trend: 1, transfer: 1, opportunity: 1, redflag: 1 },
};

// ── Detection thresholds (ADR 0002) ────────────────────────────────────────
export const THRESHOLDS = {
  SEARCH_MIN_SCORE: 2.0,
  MARKETPLACE_MIN_MATCHES: 1,
} as const;

export interface RelatedSource {
  label: string;
  url: string;
  note: string;
}

export interface RawDataPoint {
  source: SourceType;
  market: string;
  keyword: string;
  opportunityId: string;
  // search: 90-day slope; marketplace: title matches; manual: pre-assigned score
  raw: number;
  url: string;
  // For Google Trends search points: a corroborating, human-readable source
  // so the slope number is nachvollziehbar (editorial coverage, retailer page,
  // forum thread, etc.). Required on `search`, optional elsewhere.
  related?: RelatedSource;
}

export interface Signal extends RawDataPoint {
  score: number; // 0–10
  emitted: boolean;
  rule: string;
  ruleDetail: string;
}

export function detect(d: RawDataPoint): Signal {
  if (d.source === "search") {
    const score = +(d.raw * 10).toFixed(2);
    const emitted = score >= THRESHOLDS.SEARCH_MIN_SCORE;
    return {
      ...d,
      score,
      emitted,
      rule: `Google Trends slope × 10 ≥ ${THRESHOLDS.SEARCH_MIN_SCORE}`,
      ruleDetail: `Google Trends 90-day slope = ${d.raw.toFixed(3)} (${d.market}) → score ${score} ${emitted ? "≥" : "<"} ${THRESHOLDS.SEARCH_MIN_SCORE}. Slope is computed only after de-seasonalising the series; a corroborating source is attached so the number is nachvollziehbar.`,
    };
  }
  if (d.source === "marketplace") {
    const score = +(d.raw * 2.5).toFixed(2);
    const emitted = d.raw >= THRESHOLDS.MARKETPLACE_MIN_MATCHES;
    return {
      ...d,
      score,
      emitted,
      rule: `top-50 matches ≥ ${THRESHOLDS.MARKETPLACE_MIN_MATCHES}`,
      ruleDetail: `${d.raw} match${d.raw === 1 ? "" : "es"} in Amazon top-50 titles × 2.5 → score ${score}`,
    };
  }
  return {
    ...d,
    score: +d.raw.toFixed(2),
    emitted: true,
    rule: "curated (pre-vetted)",
    ruleDetail: `Expert-assigned score ${d.raw.toFixed(2)} — always emitted`,
  };
}

// ── Mock raw data (what the "scraper" returns) ─────────────────────────────
export const RAW_DATA: RawDataPoint[] = [
  // merino base layer — strong search + marketplace
  { source: "search", market: "Sweden", keyword: "merino base layer", opportunityId: "merino-base", raw: 0.84,
    url: "https://trends.google.com/trends/explore?geo=SE&q=merino%20base%20layer",
    related: { label: "Sportamore SE — merino category", url: "https://www.sportamore.se/herr/underkl-der/merinoull/", note: "Top SE outdoor retailer expanded its merino base-layer shelf 2× in 12 months — corroborates the slope." } },
  { source: "search", market: "Canada", keyword: "merino base layer", opportunityId: "merino-base", raw: 0.71,
    url: "https://trends.google.com/trends/explore?geo=CA&q=merino%20base%20layer",
    related: { label: "MEC editorial — base-layer guide 2025", url: "https://www.mec.ca/en/explore/base-layer-buying-guide", note: "Mountain Equipment Co-op (CA) refreshed its base-layer guide and led with merino in March 2025." } },
  { source: "marketplace", market: "Sweden", keyword: "merino", opportunityId: "merino-base", raw: 7,
    url: "https://www.amazon.se/gp/bestsellers/sports",
    related: { label: "Snapshot scraped 2025-06-12", url: "https://www.amazon.se/gp/bestsellers/sports", note: "7 of top-50 SKU titles contained 'merino' on snapshot day." } },

  // grid fleece — search emerging, marketplace match
  { source: "search", market: "Sweden", keyword: "grid fleece", opportunityId: "grid-fleece", raw: 0.62,
    url: "https://trends.google.com/trends/explore?geo=SE&q=grid%20fleece",
    related: { label: "Addnature SE — Patagonia R1 listing", url: "https://www.addnature.com/sv/patagonia-r1", note: "Specialist retailer flags R1 as 'restocking weekly' — anecdotal but matches the slope." } },
  { source: "marketplace", market: "Canada", keyword: "grid fleece", opportunityId: "grid-fleece", raw: 4,
    url: "https://www.amazon.ca/gp/bestsellers/sports",
    related: { label: "Snapshot scraped 2025-06-12", url: "https://www.amazon.ca/gp/bestsellers/sports", note: "4 grid-construction titles in top-50 (Rab, Patagonia, Arc'teryx, BD)." } },

  // bivy quilt — niche curated
  { source: "manual", market: "Canada", keyword: "ultralight bivy quilt", opportunityId: "bivy-quilt", raw: 7.5,
    url: "https://www.outdoorgearlab.com/topics/camping-and-hiking/best-ultralight-sleeping-bag",
    related: { label: "OutdoorGearLab editorial round-up", url: "https://www.outdoorgearlab.com/topics/camping-and-hiking/best-ultralight-sleeping-bag", note: "Editor-assigned 7.5; cottage US brands dominate the round-up." } },

  // alpine running vest — borderline below search threshold
  { source: "search", market: "Sweden", keyword: "alpine running vest", opportunityId: "running-vest", raw: 0.18,
    url: "https://trends.google.com/trends/explore?geo=SE&q=alpine%20running%20vest",
    related: { label: "Slope dominated by branded 'Salomon vest' queries", url: "https://trends.google.com/trends/explore?geo=SE&q=salomon%20vest", note: "Branded — not a category signal. Discarded on purpose." } },
  { source: "marketplace", market: "Sweden", keyword: "running vest", opportunityId: "running-vest", raw: 2,
    url: "https://www.amazon.se/gp/bestsellers/sports",
    related: { label: "Snapshot scraped 2025-06-12", url: "https://www.amazon.se/gp/bestsellers/sports", note: "2 vest SKUs in top-50, both Salomon." } },

  // approach shoe — strong all three
  { source: "search", market: "Canada", keyword: "approach shoe", opportunityId: "approach-shoe", raw: 0.55,
    url: "https://trends.google.com/trends/explore?geo=CA&q=approach%20shoe",
    related: { label: "Gripped Magazine — 2025 approach shoe review", url: "https://gripped.com/gear/best-approach-shoes-2025/", note: "Canadian climbing title published a 2025 round-up — likely driver of the slope." } },
  { source: "marketplace", market: "Canada", keyword: "approach shoe", opportunityId: "approach-shoe", raw: 3,
    url: "https://www.amazon.ca/gp/bestsellers/shoes",
    related: { label: "Snapshot scraped 2025-06-12", url: "https://www.amazon.ca/gp/bestsellers/shoes", note: "3 approach-shoe SKUs in top-50 (La Sportiva ×2, Scarpa ×1)." } },
  { source: "manual", market: "Sweden", keyword: "approach shoe", opportunityId: "approach-shoe", raw: 6.8,
    url: "https://gripped.com/approach-shoes-2025",
    related: { label: "Analyst note 2025-Q2", url: "https://gripped.com/approach-shoes-2025", note: "Expert flagged via ferrata adjacency to Swiss audience." } },

  // discarded — below search threshold, no other source
  { source: "search", market: "Sweden", keyword: "puffer skirt", opportunityId: "puffer-skirt", raw: 0.09,
    url: "https://trends.google.com/trends/explore?geo=SE&q=puffer%20skirt",
    related: { label: "No editorial coverage found", url: "https://trends.google.com/trends/explore?geo=SE&q=puffer%20skirt", note: "Flat slope and no corroborating source — discarded as noise." } },

  // gravel cycling jacket
  { source: "search", market: "Sweden", keyword: "gravel cycling jacket", opportunityId: "gravel-jacket", raw: 0.49,
    url: "https://trends.google.com/trends/explore?geo=SE&q=gravel%20cycling%20jacket",
    related: { label: "CyclingTips feature on gravel apparel", url: "https://cyclingtips.com/gravel-apparel-2025/", note: "Feature naming Pas Normal and MAAP coincides with the slope start." } },
  { source: "marketplace", market: "Sweden", keyword: "gravel jacket", opportunityId: "gravel-jacket", raw: 2,
    url: "https://www.amazon.se/gp/bestsellers/sports",
    related: { label: "Snapshot scraped 2025-06-12", url: "https://www.amazon.se/gp/bestsellers/sports", note: "2 gravel-tagged jackets in top-50 cycling sub-category." } },
];

// ── Opportunities (post-dedupe, pre-scored) ────────────────────────────────
export interface SubScore { score: number; max: number; why: string }
export interface PillarScore { total: number; subs: Record<string, SubScore> }
export interface Opportunity {
  id: string;
  name: string;
  brand: string;
  keyword: string;
  niche: string;
  trend: PillarScore;        // 0–10 (Growth only)
  transfer: PillarScore;     // 1–5 subs
  // Explicit caveat: a trend in a comparison market does NOT auto-transfer.
  // We capture the dominant reason it might fail to translate to the target.
  transferCaveat: { confidence: "high" | "medium" | "low"; reason: string };
  opportunity: PillarScore;  // 1–5 subs
  redflag: PillarScore;      // 1–5 subs (high = risky)
  trendStage: "growing" | "emerging" | "mainstream" | "declining";
  explain: {
    why_trending: string;
    why_fits_target: string;
    why_opportunity_now: string;
    why_to_be_cautious: string;
  };
}

function pillar(subs: Record<string, SubScore>): PillarScore {
  const vals = Object.values(subs);
  const total = vals.reduce((a, s) => a + s.score / s.max, 0) / vals.length;
  return { total: +total.toFixed(3), subs };
}

function trendPillar(growth: number): PillarScore {
  return {
    total: +(growth / 10).toFixed(3),
    subs: {
      Growth: {
        score: +growth.toFixed(2),
        max: 10,
        why: `Google Trends 90-day slope normalized to 0–10. ${growth >= 7.5 ? "Steep, sustained upslope." : growth >= 5 ? "Clear positive slope across comparison markets." : "Modest slope — early signal."}`,
      },
    },
  };
}

function stageOf(growth: number): Opportunity["trendStage"] {
  if (growth >= 7.5) return "growing";
  if (growth >= 5.0) return "emerging";
  if (growth >= 2.5) return "mainstream";
  return "declining";
}

export const OPPORTUNITIES: Opportunity[] = [
  {
    id: "merino-base",
    name: "Merino base layers (mid-weight)",
    brand: "Woolpower, Smartwool, Icebreaker",
    keyword: "merino base layer",
    niche: "Outdoor apparel",
    trend: trendPillar(7.8),
    transfer: pillar({
      "Outdoor relevance": { score: 5, max: 5, why: "Core alpine layering category — universal in Swiss outdoor assortments." },
      "DACH availability gap": { score: 4, max: 5, why: "Swedish brands (Woolpower) under-distributed in CH outside of specialist retail." },
    }),
    opportunity: pillar({
      "Availability gap": { score: 4, max: 5, why: "Top competitors carry only 2 of the 5 trending merino SKUs in Sweden." },
      "Retail saturation": { score: 3, max: 5, why: "Category is established but mid-weight grid construction is under-represented." },
      "Brand availability": { score: 4, max: 5, why: "Direct B2B contact available via Nordic distributors." },
    }),
    redflag: pillar({
      "Supply chain risk": { score: 2, max: 5, why: "Stable Nordic wool sourcing; no acute disruption." },
      "Regulatory risk": { score: 1, max: 5, why: "No restricted-substance concerns for mulesing-free certified wool." },
      "Brand concentration": { score: 3, max: 5, why: "Three brands hold ~70% — workable but watch margin pressure." },
    }),
    trendStage: stageOf(7.8),
    transferCaveat: { confidence: "high", reason: "Sweden and Canada both share a cold-shoulder-season profile with Switzerland; merino is a category-level need, not a style fad. Transfer risk: low." },
    explain: {
      why_trending: "Search slope is steep across both Sweden and Canada and Amazon top-50 carries seven merino titles.",
      why_fits_target: "Mid-weight merino is a core Swiss alpine layering need with cold shoulder-seasons.",
      why_opportunity_now: "Sweden-led brands have measurable distribution gaps in CH that two of your competitors haven't closed.",
      why_to_be_cautious: "Brand concentration is moderate — pricing power sits with three suppliers.",
    },
  },
  {
    id: "approach-shoe",
    name: "Approach shoes (climber crossover)",
    brand: "La Sportiva, Scarpa, Black Diamond",
    keyword: "approach shoe",
    niche: "Outdoor footwear",
    trend: trendPillar(6.4),
    transfer: pillar({
      "Outdoor relevance": { score: 5, max: 5, why: "Highly relevant to Swiss alpine and via ferrata audiences." },
      "DACH availability gap": { score: 3, max: 5, why: "Available at major DACH retailers but specific 2025 models lag Canada by one season." },
    }),
    opportunity: pillar({
      "Availability gap": { score: 3, max: 5, why: "Mid-tier price band (CHF 150–200) is thin across your two listed competitors." },
      "Retail saturation": { score: 3, max: 5, why: "Established category; differentiation via brand exclusivity, not breadth." },
      "Brand availability": { score: 4, max: 5, why: "Italian and US brands have CH distributors actively seeking new accounts." },
    }),
    redflag: pillar({
      "Supply chain risk": { score: 2, max: 5, why: "EU-sourced footwear; no acute exposure." },
      "Regulatory risk": { score: 1, max: 5, why: "Standard footwear regulation; no new requirements." },
      "Brand concentration": { score: 2, max: 5, why: "Four credible brands; balanced negotiating position." },
    }),
    trendStage: stageOf(6.4),
    transferCaveat: { confidence: "medium", reason: "Canadian climbing-media coverage drives the slope; CH via-ferrata audience is sympathetic but smaller. Validate against Swiss alpine-club search before committing volume." },
    explain: {
      why_trending: "Curated expert score plus a Canadian search upslope and three Amazon top-50 titles.",
      why_fits_target: "Direct match to Swiss summer alpine demand profile and via ferrata growth.",
      why_opportunity_now: "Brand-side distributors are open and the CHF 150–200 band is under-stocked.",
      why_to_be_cautious: "Footwear ties up working capital — sizing breadth amplifies SKU count fast.",
    },
  },
  {
    id: "grid-fleece",
    name: "Grid fleece mid-layer",
    brand: "Patagonia R1, Rab Power Grid",
    keyword: "grid fleece",
    niche: "Outdoor apparel",
    trend: trendPillar(5.6),
    transfer: pillar({
      "Outdoor relevance": { score: 5, max: 5, why: "Standard mid-layer for active alpine pursuits." },
      "DACH availability gap": { score: 3, max: 5, why: "Patagonia is broadly available; smaller grid-knit brands are not." },
    }),
    opportunity: pillar({
      "Availability gap": { score: 4, max: 5, why: "Smaller specialist brands (Rab Power Grid variants) absent at both competitors." },
      "Retail saturation": { score: 3, max: 5, why: "Category present but grid-knit construction under-marketed locally." },
      "Brand availability": { score: 3, max: 5, why: "UK and US brands accessible via existing EU distributors." },
    }),
    redflag: pillar({
      "Supply chain risk": { score: 2, max: 5, why: "Synthetic supply is diversified." },
      "Regulatory risk": { score: 2, max: 5, why: "PFC-free claims need verification per EU textile rules — manageable." },
      "Brand concentration": { score: 2, max: 5, why: "Multiple credible brands keep leverage with you." },
    }),
    trendStage: stageOf(5.6),
    transferCaveat: { confidence: "medium", reason: "Construction (grid-knit) is climate-agnostic, but Canadian Amazon mix is North-American brand-heavy; expect 20–30% slope decay in CH where Patagonia is already saturated." },
    explain: {
      why_trending: "Swedish search slope is positive and four matches appear in Canadian Amazon top-50.",
      why_fits_target: "Strong year-round Swiss mid-layer category with low cannibalisation risk.",
      why_opportunity_now: "Two specialist brand families are entirely absent from your listed competitors.",
      why_to_be_cautious: "EU textile regulation review for PFC-free claims requires documentation.",
    },
  },
  {
    id: "bivy-quilt",
    name: "Ultralight bivy quilts",
    brand: "Katabatic, Hammock Gear",
    keyword: "ultralight bivy quilt",
    niche: "Camping & shelter",
    trend: trendPillar(5.25), // 0.7 * 7.5 (manual rule from CONTEXT)
    transfer: pillar({
      "Outdoor relevance": { score: 4, max: 5, why: "Niche but growing — fits Swiss multi-day alpine traverses." },
      "DACH availability gap": { score: 5, max: 5, why: "Cottage US brands not stocked anywhere in DACH retail." },
    }),
    opportunity: pillar({
      "Availability gap": { score: 5, max: 5, why: "Zero distribution in CH; pure greenfield." },
      "Retail saturation": { score: 4, max: 5, why: "Ultralight segment is thin — no incumbent." },
      "Brand availability": { score: 2, max: 5, why: "Cottage brands have limited wholesale capacity; allocation risk." },
    }),
    redflag: pillar({
      "Supply chain risk": { score: 4, max: 5, why: "Small US manufacturers — long lead times and FX exposure." },
      "Regulatory risk": { score: 2, max: 5, why: "Down sourcing needs RDS certification — verifiable." },
      "Brand concentration": { score: 4, max: 5, why: "Two cottage brands cover the segment; concentration is real." },
    }),
    trendStage: stageOf(5.25),
    transferCaveat: { confidence: "low", reason: "Signal is a single curated expert score from a US/CA context — ultralight thru-hike culture is much larger there than in CH. Treat composite as exploratory, not directional." },
    explain: {
      why_trending: "Curated expert signal (7.5) — non-search opportunities are normalized at 0.7× best signal score.",
      why_fits_target: "Aligns with growing Swiss interest in long-distance alpine traverses.",
      why_opportunity_now: "Greenfield distribution with no incumbent — first mover advantage available.",
      why_to_be_cautious: "Cottage supply, USD pricing, and brand concentration all push working-capital risk up.",
    },
  },
  {
    id: "gravel-jacket",
    name: "Gravel cycling shell",
    brand: "Pas Normal, MAAP, 7mesh",
    keyword: "gravel cycling jacket",
    niche: "Cycling apparel",
    trend: trendPillar(4.9),
    transfer: pillar({
      "Outdoor relevance": { score: 3, max: 5, why: "Adjacent to outdoor — gravel overlaps with bikepacking audience." },
      "DACH availability gap": { score: 4, max: 5, why: "Pas Normal and MAAP under-distributed in CH outside cycling specialists." },
    }),
    opportunity: pillar({
      "Availability gap": { score: 4, max: 5, why: "Your competitors do not list any of the three brand families." },
      "Retail saturation": { score: 4, max: 5, why: "Outdoor channel has not absorbed gravel cycling yet." },
      "Brand availability": { score: 3, max: 5, why: "Scandinavian brands open to new EU accounts; Canadian (7mesh) more selective." },
    }),
    redflag: pillar({
      "Supply chain risk": { score: 3, max: 5, why: "Mostly EU/Asia mixed — manageable but not strong." },
      "Regulatory risk": { score: 2, max: 5, why: "Standard apparel; no acute regulation." },
      "Brand concentration": { score: 3, max: 5, why: "Three credible brands; reasonable position." },
    }),
    trendStage: stageOf(4.9),
    transferCaveat: { confidence: "low", reason: "Adjacency stretch — gravel cycling sits outside the alpine-apparel core. Slope may not transfer because the buyer persona is different from the target outdoor audience." },
    explain: {
      why_trending: "Search slope is moderate and two Amazon matches confirm marketplace presence.",
      why_fits_target: "Adjacent category — fits bikepacking-curious portion of your outdoor base.",
      why_opportunity_now: "Outdoor channel has not absorbed gravel cycling — first mover space exists.",
      why_to_be_cautious: "Outside your core niche; SKU productivity will need close monitoring.",
    },
  },
  {
    id: "running-vest",
    name: "Alpine running vest",
    brand: "Salomon, Black Diamond",
    keyword: "alpine running vest",
    niche: "Trail running",
    trend: trendPillar(3.5),
    transfer: pillar({
      "Outdoor relevance": { score: 4, max: 5, why: "Strong fit to Swiss trail running audience." },
      "DACH availability gap": { score: 2, max: 5, why: "Salomon broadly distributed; little gap to exploit." },
    }),
    opportunity: pillar({
      "Availability gap": { score: 2, max: 5, why: "Both competitors stock the leading brand." },
      "Retail saturation": { score: 2, max: 5, why: "Mature category in CH." },
      "Brand availability": { score: 3, max: 5, why: "Brands open but margin tight." },
    }),
    redflag: pillar({
      "Supply chain risk": { score: 2, max: 5, why: "Mature category, well-served supply." },
      "Regulatory risk": { score: 1, max: 5, why: "Standard sports apparel." },
      "Brand concentration": { score: 4, max: 5, why: "Salomon dominates — pricing power sits there." },
    }),
    trendStage: stageOf(3.5),
    transferCaveat: { confidence: "medium", reason: "Audience overlaps cleanly with CH trail-running, but category is already mature in DACH — even a clean transfer doesn't open assortment space." },
    explain: {
      why_trending: "Marketplace signal present (2 Amazon matches) but search slope was below threshold (0.18 × 10 = 1.8 < 2.0).",
      why_fits_target: "Audience fits but category is already saturated with the incumbent.",
      why_opportunity_now: "Limited — gap to existing assortments is small.",
      why_to_be_cautious: "Margin pressure from incumbent brand concentration.",
    },
  },
];

export function compositeScore(o: Opportunity, w: RetailerContext["weights"]): number {
  const num =
    w.trend * o.trend.total +
    w.transfer * o.transfer.total +
    w.opportunity * o.opportunity.total +
    w.redflag * (1 - o.redflag.total);
  const den = w.trend + w.transfer + w.opportunity + w.redflag;
  return +(num / den).toFixed(3);
}

export function urgency(o: Opportunity, w: RetailerContext["weights"]): "act_now" | "watch" {
  // Deterministic for the demo: act when composite ≥ 0.65 AND trend stage is growing/emerging
  const c = compositeScore(o, w);
  return c >= 0.65 && (o.trendStage === "growing" || o.trendStage === "emerging") ? "act_now" : "watch";
}
