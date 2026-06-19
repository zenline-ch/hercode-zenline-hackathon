"""Synthesise stage (ARCHITECTURE.md §8, §10): turn a scored cluster of
signals into the final Opportunity record the chat + dashboard consume."""
import json
from pathlib import Path

from retail_radar.pipeline.leadlag import lead_lag_for_opportunity
from retail_radar.pipeline.scorer import score_opportunity
from retail_radar.schema import RetailerContext, Signal

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
PERSONAS = json.loads((CONFIG_DIR / "personas.json").read_text())
PERSONAS = {k: v for k, v in PERSONAS.items() if not k.startswith("_")}

_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}

_BUY_RECOMMENDATION = {
    "emerging": "Test order · small stock · monitor closely",
    "growing": "Scale up · negotiate supplier terms",
    "mainstream": "Evaluate margin · assess competitive positioning",
    "declining": "Wind down · evaluate clearance strategy",
}

_EXPECTED_WINDOW = {
    "emerging": "12-24 month first-mover advantage window",
    "growing": "6-12 month window to build out assortment",
    "mainstream": "Margin/positioning window only -- first-mover edge is gone",
    "declining": "No window -- plan exit",
}


def _trend_stage(momentum_norm: float, coverage_status: str) -> str:
    if coverage_status == "covered":
        return "mainstream"
    if coverage_status == "partially_covered":
        return "growing"
    return "emerging"  # absent / unknown / not_relevant


def _group_by_opportunity(signals: list[Signal]) -> dict[str, list[Signal]]:
    groups: dict[str, list[Signal]] = {}
    for s in signals:
        groups.setdefault(s.opportunity_id, []).append(s)
    return groups


def synthesise(signals: list[Signal], context: RetailerContext) -> list[dict]:
    groups = _group_by_opportunity(signals)
    persona_cfg = PERSONAS.get(context.persona, PERSONAS["large_retailer"])
    opportunities = []

    for opp_id, opp_signals in groups.items():
        opp_name = opp_signals[0].opportunity_name
        scored = score_opportunity(opp_signals, context, opp_name)
        stage = _trend_stage(scored["scores"]["momentum"]["total"], scored["coverage_status"])

        buy_recommendation = _BUY_RECOMMENDATION[stage]
        if _CONFIDENCE_RANK[scored["confidence"]] < _CONFIDENCE_RANK[persona_cfg["min_confidence"]]:
            buy_recommendation = f"Below {persona_cfg['label']}'s confidence threshold -- monitor only, no buy"

        leadlag = lead_lag_for_opportunity(opp_signals, context.target_market)

        opportunities.append({
            "id": opp_id,
            "name": opp_name,
            "trend_stage": stage,
            "urgency": scored["urgency"],
            "buy_recommendation": buy_recommendation,
            "persona_buy_action": persona_cfg["buy_action"],
            "composite_score": scored["composite_score"],
            "confidence": scored["confidence"],
            "coverage_status": scored["coverage_status"],
            "scores": scored["scores"],
            "explainability": {
                "why_trending": f"Momentum proxy {scored['scores']['momentum'].get('slope_proxy', 0)}/10 across "
                                 f"{scored['scores']['breadth']['count']} independent source type(s): "
                                 f"{', '.join(scored['scores']['breadth']['sources_used'])}.",
                "why_fits_switzerland": scored["scores"]["transferability"].get("reason", ""),
                "why_opportunity_now": (
                    f"coverage_status={scored['coverage_status']} -- "
                    f"{scored['scores']['coverage_gap'].get('matched_note') or 'no competitor evidence yet'}"
                ),
            },
            "lead_lag": leadlag,
            "monitor_triggers": [
                f"{context.target_market} momentum declines 3 months straight",
                "Competitor assortment now covers this category -- gap closed",
            ],
            "reversal_signals": ["Initial sell-through < 20% after 4 weeks"],
            "expected_window": _EXPECTED_WINDOW[stage],
            "risk_flags": scored["risk_flags"],
            "evidence_urls": sorted({s.url for s in opp_signals if s.url}),
            "signals": [
                {
                    "source": s.source, "source_type": s.source_type, "market": s.market,
                    "keyword": s.keyword, "signal_score": s.signal_score, "url": s.url,
                    "observed_at": s.observed_at, "notes": s.notes,
                }
                for s in opp_signals
            ],
        })

    opportunities.sort(key=lambda o: o["composite_score"], reverse=True)
    return opportunities
