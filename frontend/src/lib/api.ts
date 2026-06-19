// Backend wiring: fetch real LLM-scored opportunities from the FastAPI backend
// (../../api.py -> zenline_radar/) and adapt them into the frontend `Opportunity`
// shape that domain.ts / results.tsx already consume.
//
// The backend was purpose-built for this frontend (see api.py docstring). Its
// per-opportunity JSON is *almost* the same shape but nested differently, so the
// only real work here is `adaptOpportunity` — a field-by-field map.
//
// Source of truth for the mapping: ../INTEGRATION.md.
import type { Opportunity, PillarScore, SubScore } from "./domain";

const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

// Mirrors zenline_radar DEMO_CONTEXT — the /api/analyze endpoint requires these.
const DEMO_REQUEST = {
  target_market: "CH",
  comparison_markets: ["SE", "CA", "US", "NO"],
  niche: "outdoor retail",
  category_keywords: [
    "trail running shoes",
    "merino wool base layer",
    "recycled down jacket",
    "gravel bike",
    "inflatable kayak",
    "lightweight tent",
    "solar panel backpack",
    "cork yoga mat",
    "bamboo hiking poles",
    "arc'teryx",
    "salewa",
    "mammut",
    "ortovox",
    "picture organic",
  ],
  competitor_urls: [] as string[],
  risk_factors: ["supply_chain", "regulatory", "brand_concentration"],
  score_weights: { trend: 1.0, transferability: 1.0, opportunity: 1.0, red_flag: 1.0 },
};

export type DataSource = "live" | "mock-api" | "offline";

export interface FetchResult {
  opportunities: Opportunity[];
  source: DataSource;
  mode?: string;
}

// ---- backend JSON shapes (loosely typed — backend is the contract) ----------
interface BackendScores {
  trend?: { total?: number; growth?: number };
  transferability?: {
    total?: number;
    outdoor_relevance?: number;
    dach_availability_gap?: number;
    explanation?: string;
  };
  opportunity?: {
    total?: number;
    availability_gap?: number;
    retail_saturation?: number;
    brand_availability?: number;
    explanation?: string;
  };
  red_flag?: {
    total?: number;
    supply_chain_risk?: number;
    regulatory_risk?: number;
    brand_concentration?: number;
    explanation?: string;
  };
}
interface BackendOpportunity {
  id: string;
  name: string;
  brand?: string;
  keyword?: string;
  confidence?: "high" | "medium" | "low";
  trend_stage?: string;
  scores?: BackendScores;
  explainability?: Record<string, string>;
}

function sub(score: number | undefined, max: number, why: string): SubScore {
  return { score: typeof score === "number" ? score : 0, max, why };
}

function pillarFromSubs(total: number | undefined, subs: Record<string, SubScore>): PillarScore {
  // Prefer the backend's own pillar total; fall back to averaging the subs.
  if (typeof total === "number") return { total: +total.toFixed(3), subs };
  const vals = Object.values(subs);
  const t = vals.reduce((a, s) => a + s.score / s.max, 0) / Math.max(1, vals.length);
  return { total: +t.toFixed(3), subs };
}

const STAGES = ["growing", "emerging", "mainstream", "declining"] as const;
function stage(s: string | undefined): Opportunity["trendStage"] {
  return (STAGES as readonly string[]).includes(s ?? "") ? (s as Opportunity["trendStage"]) : "emerging";
}

/** Map one backend opportunity into the frontend `Opportunity` interface. */
export function adaptOpportunity(raw: BackendOpportunity, niche: string): Opportunity {
  const s = raw.scores ?? {};
  const tr = s.transferability ?? {};
  const op = s.opportunity ?? {};
  const rf = s.red_flag ?? {};
  const ex = raw.explainability ?? {};

  return {
    id: raw.id,
    name: raw.name,
    brand: raw.brand ?? "—",
    keyword: raw.keyword ?? raw.name,
    niche,
    trend: pillarFromSubs(s.trend?.total, {
      Growth: sub(s.trend?.growth, 10, ex.why_trending ?? "Google Trends 90-day slope, normalized 0–10."),
    }),
    transfer: pillarFromSubs(tr.total, {
      "Outdoor relevance": sub(tr.outdoor_relevance, 5, tr.explanation ?? ""),
      "DACH availability gap": sub(tr.dach_availability_gap, 5, tr.explanation ?? ""),
    }),
    transferCaveat: {
      confidence: raw.confidence ?? "medium",
      reason:
        tr.explanation ??
        "A signal in a comparison market is not a guarantee for the target market.",
    },
    opportunity: pillarFromSubs(op.total, {
      "Availability gap": sub(op.availability_gap, 5, op.explanation ?? ""),
      "Retail saturation": sub(op.retail_saturation, 5, op.explanation ?? ""),
      "Brand availability": sub(op.brand_availability, 5, op.explanation ?? ""),
    }),
    // Backend red_flag.total is raw risk (high = risky), which is exactly what the
    // frontend's `compositeScore` expects (it inverts via 1 - redflag.total).
    redflag: pillarFromSubs(rf.total, {
      "Supply chain risk": sub(rf.supply_chain_risk, 5, rf.explanation ?? ""),
      "Regulatory risk": sub(rf.regulatory_risk, 5, rf.explanation ?? ""),
      "Brand concentration": sub(rf.brand_concentration, 5, rf.explanation ?? ""),
    }),
    trendStage: stage(raw.trend_stage),
    explain: {
      why_trending: ex.why_trending ?? "",
      // backend names this field for Switzerland; frontend is market-agnostic.
      why_fits_target: ex.why_fits_switzerland ?? ex.why_fits_target ?? "",
      why_opportunity_now: ex.why_opportunity_now ?? "",
      why_to_be_cautious: ex.why_to_be_cautious ?? "",
    },
  };
}

/**
 * Fetch opportunities from the backend.
 * @param live  true  -> POST /api/analyze use_mock=false  (runs the real LLM, exercises ANTHROPIC_API_KEY)
 *              false -> POST /api/analyze use_mock=true   (pre-scored demo JSON, no key needed)
 * Throws on network/HTTP error so the caller can fall back to bundled mock data.
 */
export async function fetchOpportunities(live: boolean): Promise<FetchResult> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...DEMO_REQUEST, use_mock: !live }),
  });
  if (!res.ok) throw new Error(`Backend ${res.status}: ${await res.text().catch(() => "")}`);
  const payload = await res.json();
  const rawList: BackendOpportunity[] = Array.isArray(payload)
    ? payload
    : (payload.results ?? []);
  return {
    opportunities: rawList.map((r) => adaptOpportunity(r, DEMO_REQUEST.niche)),
    source: live ? "live" : "mock-api",
    mode: payload.mode,
  };
}
