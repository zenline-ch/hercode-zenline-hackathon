"""Scoring pipeline — deterministic + LLM pillars combined into composite score.

Deterministic:
  Trend Score: derived from the best Google Trends 90-day slope (signal_score)
  normalised to 0–1.

LLM (via llm.py):
  Transferability Score, Opportunity Score, Red-Flag Score

Composite:
  weighted_avg(Trend · Transferability · Opportunity · (1 - Red_Flag))
  Default: equal weights. Weights configurable via RetailerContext.score_weights.
"""

import logging

import numpy as np

from .context import RetailerContext
from .llm import score_opportunity_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Trend Score (deterministic)
# ---------------------------------------------------------------------------

_TREND_STAGE_THRESHOLDS = {
    # (lower_bound_exclusive, stage)
    # Sorted descending — first match wins
}

def _compute_trend_score(opportunity: dict) -> tuple[float, float, str]:
    """Return (trend_total 0-1, growth 0-10, trend_stage)."""
    # Use best_signal_score as proxy for Growth
    # signal_score for search signals was already computed as slope * 10, clipped 0-10
    search_signals = [
        s for s in opportunity.get("signals", [])
        if s.get("signal_type") == "search"
    ]

    if search_signals:
        growth = max(s.get("signal_score", 0) for s in search_signals)
    else:
        # Fallback: use best_signal_score across all signals, scaled down for non-search
        growth = min(10.0, opportunity.get("best_signal_score", 5.0) * 0.7)

    trend_total = round(growth / 10.0, 3)
    trend_stage = _classify_trend_stage(growth)
    return trend_total, growth, trend_stage


def _classify_trend_stage(growth: float) -> str:
    if growth >= 7.5:
        return "growing"
    if growth >= 5.0:
        return "emerging"
    if growth >= 2.5:
        return "mainstream"
    return "declining"


_BUY_RECOMMENDATION = {
    "emerging": "Test order · small stock · monitor closely",
    "growing": "Scale up · negotiate supplier terms",
    "mainstream": "Evaluate margin · assess competitive positioning",
    "declining": "Wind down · evaluate clearance strategy",
}


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------

def _composite(scores: dict, weights: dict) -> float:
    w_trend = weights.get("trend", 1.0)
    w_trans = weights.get("transferability", 1.0)
    w_opp = weights.get("opportunity", 1.0)
    w_rf = weights.get("red_flag", 1.0)

    trend = scores["trend"]["total"]
    trans = scores["transferability"]["total"]
    opp = scores["opportunity"]["total"]
    rf_inv = 1.0 - scores["red_flag"]["total"]

    total_weight = w_trend + w_trans + w_opp + w_rf
    composite = (
        w_trend * trend
        + w_trans * trans
        + w_opp * opp
        + w_rf * rf_inv
    ) / total_weight
    return round(composite, 3)


# ---------------------------------------------------------------------------
# Full scoring pipeline
# ---------------------------------------------------------------------------

def score_opportunities(
    opportunities: list[dict],
    ctx: RetailerContext,
    api_key: str | None = None,
    progress_callback=None,
) -> list[dict]:
    """Score all opportunities and return sorted by composite_score (desc)."""
    scored: list[dict] = []

    for i, opp in enumerate(opportunities):
        if progress_callback:
            progress_callback(i, len(opportunities), opp.get("name", ""))

        # 1. Trend (deterministic)
        trend_total, growth, trend_stage = _compute_trend_score(opp)
        opp.setdefault("scores", {})
        opp["scores"]["trend"] = {
            "total": trend_total,
            "growth": round(growth, 2),
        }

        # 2. Transferability + Opportunity + Red-Flag (LLM)
        opp = score_opportunity_llm(opp, ctx, api_key=api_key)

        # 3. Composite
        composite = _composite(opp["scores"], ctx.score_weights)
        opp["composite_score"] = composite
        opp["trend_stage"] = trend_stage
        opp["buy_recommendation"] = _BUY_RECOMMENDATION[trend_stage]

        scored.append(opp)
        logger.info(
            "Scored %s → composite=%.3f stage=%s urgency=%s",
            opp["name"], composite, trend_stage, opp.get("urgency", "watch"),
        )

    # Sort descending by composite score
    scored.sort(key=lambda o: o["composite_score"], reverse=True)

    # Add rank
    for rank, opp in enumerate(scored, start=1):
        opp["rank"] = rank

    return scored
