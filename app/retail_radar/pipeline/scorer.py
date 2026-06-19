"""Hybrid scoring (ARCHITECTURE.md §6, ADR 0001).

Deterministic: breadth, momentum, coverage_gap, risk -- no API key needed,
fully auditable and rerunnable.
LLM (optional): transferability -- the one dimension that genuinely needs
judgment about a specific comparison-market -> target-market pair. Falls
back to a transparent heuristic if no ANTHROPIC_API_KEY is set, so the app
never breaks live.
"""
import json
import os
from pathlib import Path

from retail_radar.schema import Signal, RetailerContext

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_json(name: str) -> dict:
    return json.loads((CONFIG_DIR / name).read_text())


SOURCES = _load_json("sources.json")["sources"]
SOURCE_CREDIBILITY = {row["name"]: row["credibility"] for row in SOURCES}
TOTAL_CREDIBILITY = sum(SOURCE_CREDIBILITY.values())

RISK_CFG = _load_json("risk_taxonomy.json")
RISK_TAXONOMY = RISK_CFG["taxonomy"]
RISK_KEYWORD_TRIGGERS = RISK_CFG["keyword_triggers"]

COVERAGE_CFG = _load_json("coverage_keywords.json")
COVERAGE_KEYWORD_TO_STATUS = COVERAGE_CFG["keyword_to_status"]
COVERAGE_STATUS_SCORE = COVERAGE_CFG["status_score"]


def breadth_score(signals: list[Signal]) -> tuple[float, dict]:
    present_sources = {s.source for s in signals if s.source in SOURCE_CREDIBILITY}
    raw = sum(SOURCE_CREDIBILITY[name] for name in present_sources)
    norm = min(1.0, raw / TOTAL_CREDIBILITY) if TOTAL_CREDIBILITY else 0.0
    return norm, {"sources_used": sorted(present_sources), "count": len(present_sources)}


def momentum_score(signals: list[Signal]) -> tuple[float, dict]:
    search_signals = [s for s in signals if s.source_type == "search"]
    if not search_signals:
        return 0.0, {"slope_proxy": 0.0, "note": "no search-type signal for this opportunity"}
    avg = sum(s.signal_score for s in search_signals) / len(search_signals)
    slope_proxy = round(avg * 10, 1)  # 0-10 scale, matches data-contract trend.growth
    return min(1.0, avg), {"slope_proxy": slope_proxy}


def coverage_gap_score(signals: list[Signal]) -> tuple[float, str, dict]:
    competitor_signals = [s for s in signals if s.source_type == "competitor"]
    if not competitor_signals:
        return COVERAGE_STATUS_SCORE["unknown"], "unknown", {"note": "no competitor scan for this opportunity"}

    status = "unknown"
    matched_note = ""
    for s in competitor_signals:
        note_lc = s.notes.lower()
        for keyword, mapped_status in COVERAGE_KEYWORD_TO_STATUS.items():
            if keyword in note_lc:
                status = mapped_status
                matched_note = s.notes
                break
        if status != "unknown":
            break
    score = COVERAGE_STATUS_SCORE.get(status, COVERAGE_STATUS_SCORE["unknown"])
    return score, status, {"matched_note": matched_note, "competitors_checked": [s.source for s in competitor_signals]}


def risk_score(signals: list[Signal]) -> tuple[float, list[str]]:
    all_notes = " ".join(s.notes.lower() for s in signals)
    triggered = set()
    for keyword, flag in RISK_KEYWORD_TRIGGERS.items():
        if keyword in all_notes:
            triggered.add(flag)
    score = 1 - (len(triggered) / len(RISK_TAXONOMY))
    return max(0.0, score), sorted(triggered)


def transferability_score(signals: list[Signal], context: RetailerContext, opportunity_name: str) -> tuple[float, dict]:
    """Returns (normalised 0-1 score, detail dict with raw score/reason/urgency)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _transferability_llm(signals, context, opportunity_name, api_key)
        except Exception as exc:  # noqa: BLE001 -- never let an LLM hiccup break the score
            return _transferability_fallback(signals, context, opportunity_name, error=str(exc))
    return _transferability_fallback(signals, context, opportunity_name)


def _transferability_llm(signals, context: RetailerContext, opportunity_name: str, api_key: str) -> tuple[float, dict]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    evidence = "\n".join(
        f"- [{s.source}, {s.market}] {s.signal_name}: {s.notes}" for s in signals[:8]
    )
    prompt = (
        f"Retailer context: target_market={context.target_market}, "
        f"comparison_markets={context.comparison_markets}, niche={context.niche}.\n"
        f"Opportunity: {opportunity_name}\nEvidence:\n{evidence}\n\n"
        "Score how likely this opportunity is to transfer successfully from the "
        "comparison markets into the target market. Respond with ONLY a JSON object: "
        '{"score": <1-5 integer>, "reason": "<one sentence>", "urgency": "act_now"|"watch"}'
    )
    resp = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    start, end = text.find("{"), text.rfind("}") + 1
    parsed = json.loads(text[start:end])
    raw_score = int(parsed["score"])
    norm = (raw_score - 1) / 4
    return norm, {"raw_score": raw_score, "reason": parsed["reason"], "urgency": parsed["urgency"], "via": "llm"}


def _transferability_fallback(signals, context: RetailerContext, opportunity_name: str, error: str | None = None) -> tuple[float, dict]:
    """Deterministic heuristic used when no ANTHROPIC_API_KEY is set, or the LLM call fails.
    Grounded in the same evidence: source diversity + evidence quality + whether a competitor
    assortment check exists. Competitor-type signal_score is excluded from the evidence-quality
    average -- for those rows, 0.0 means "confirmed absent from the shelf" (good news for the
    opportunity), not "weak evidence", so it must not drag the quality average down."""
    distinct_sources = {s.source for s in signals}
    has_competitor_signal = any(s.source_type == "competitor" for s in signals)
    quality_signals = [s.signal_score for s in signals if s.source_type != "competitor"]
    avg_quality = sum(quality_signals) / len(quality_signals) if quality_signals else 0.0

    if len(distinct_sources) >= 3 and has_competitor_signal and avg_quality >= 0.5:
        raw_score, reason, urgency = 4, "Heuristic fallback: multiple independent, strong sources plus a direct Swiss assortment check.", "act_now"
    elif len(distinct_sources) >= 2 and avg_quality >= 0.35:
        raw_score, reason, urgency = 3, "Heuristic fallback: moderate source diversity and evidence strength.", "watch"
    else:
        raw_score, reason, urgency = 2, "Heuristic fallback: thin or weak evidence base, treat as directional only.", "watch"
    norm = (raw_score - 1) / 4
    detail = {"raw_score": raw_score, "reason": reason, "urgency": urgency, "via": "heuristic_fallback", "avg_quality": round(avg_quality, 2)}
    if error:
        detail["llm_error"] = error
    return norm, detail


def confidence_label(composite_score: float) -> str:
    if composite_score >= 0.70:
        return "high"
    if composite_score >= 0.45:
        return "medium"
    return "low"


def score_opportunity(signals: list[Signal], context: RetailerContext, opportunity_name: str) -> dict:
    weights = context.normalised_weights()

    b_norm, b_detail = breadth_score(signals)
    m_norm, m_detail = momentum_score(signals)
    t_norm, t_detail = transferability_score(signals, context, opportunity_name)
    c_norm, coverage_status, c_detail = coverage_gap_score(signals)
    r_norm, risk_flags = risk_score(signals)

    composite = (
        weights["breadth"] * b_norm
        + weights["momentum"] * m_norm
        + weights["transferability"] * t_norm
        + weights["coverage_gap"] * c_norm
        + weights["risk"] * r_norm
    )
    confidence = confidence_label(composite)
    urgency = t_detail.get("urgency", "watch")
    if confidence == "low":
        urgency = "watch"  # urgency guard, ARCHITECTURE.md §6

    return {
        "composite_score": round(composite, 3),
        "confidence": confidence,
        "coverage_status": coverage_status,
        "urgency": urgency,
        "risk_flags": risk_flags,
        "scores": {
            "breadth": {"total": round(b_norm, 3), **b_detail},
            "momentum": {"total": round(m_norm, 3), **m_detail},
            "transferability": {"total": round(t_norm, 3), **t_detail},
            "coverage_gap": {"total": round(c_norm, 3), **c_detail},
            "risk": {"total": round(r_norm, 3), "flags_triggered": risk_flags},
        },
    }
