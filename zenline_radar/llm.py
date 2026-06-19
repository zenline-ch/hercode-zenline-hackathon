"""LLM scoring module — one call per opportunity, returns all three LLM pillars.

Uses claude-opus-4-8 with adaptive thinking and structured JSON output.
One call returns:
  - transferability score (outdoor_relevance + dach_availability_gap)
  - opportunity score (availability_gap + retail_saturation + brand_availability)
  - red_flag score (supply_chain_risk + regulatory_risk + brand_concentration)
  - urgency classification (act_now / watch)
  - four explainability sentences
"""

import json
import logging
import os

import anthropic

from .context import RetailerContext

logger = logging.getLogger(__name__)

_MODEL = "claude-opus-4-8"

_SYSTEM_PROMPT = """You are a retail market analyst assistant specializing in outdoor retail.
You assess emerging product opportunities for independent specialty retailers.
Always return valid JSON matching the exact schema provided. Be concise and evidence-based."""

_USER_PROMPT_TEMPLATE = """Assess this opportunity for a {niche} in {target_market}.

## Opportunity
Name: {name}
Keywords: {keyword}
Brand: {brand}
Signal breadth: {signal_breadth} independent source types
Markets where seen: {markets}
Evidence URLs: {evidence_urls}

## Comparison markets → Target market
{comparison_markets} → {target_market}

## Retailer context
Niche: {niche}
Competitor URLs: {competitor_urls}
Risk factors to watch: {risk_factors}

## Scoring task
Return ONLY a JSON object with this exact structure (no markdown, no prose):

{{
  "transferability": {{
    "outdoor_relevance": <int 1-5>,
    "dach_availability_gap": <int 1-5>,
    "explanation": "<one sentence why this fits or does not fit {target_market}>"
  }},
  "opportunity": {{
    "availability_gap": <int 1-5>,
    "retail_saturation": <int 1-5>,
    "brand_availability": <int 1-5>,
    "explanation": "<one sentence on sourcing/margin/gap opportunity>"
  }},
  "red_flag": {{
    "supply_chain_risk": <int 1-5>,
    "regulatory_risk": <int 1-5>,
    "brand_concentration": <int 1-5>,
    "explanation": "<one sentence on the main risk to be cautious about>"
  }},
  "urgency": "<act_now or watch>",
  "why_trending": "<one sentence on why this is gaining momentum now>",
  "why_fits_switzerland": "<one sentence on cultural/climate/commercial fit for {target_market}>",
  "why_opportunity_now": "<one sentence on the specific window of opportunity>"
}}

Scoring guide:
- outdoor_relevance: 5 = core niche fit, 1 = peripheral
- dach_availability_gap: 5 = product nearly absent in {target_market}/DACH, 1 = already saturated
- availability_gap: 5 = easy to source for a small retailer, 1 = very hard
- retail_saturation: 5 = low competition (good), 1 = dominated by incumbents
- brand_availability: 5 = brand accessible via EU/DACH distributor, 1 = no distributor exists
- supply_chain_risk: 5 = very high risk (single source, long lead time), 1 = no concern
- regulatory_risk: 5 = serious regulatory hurdles in CH, 1 = no issues
- brand_concentration: 5 = category already dominated by 1-2 incumbents, 1 = fragmented
- urgency act_now: window is open now (emerging/growing + low saturation + accessible)
- urgency watch: interesting but not yet ripe or too early to act"""


def score_opportunity_llm(
    opportunity: dict,
    ctx: RetailerContext,
    api_key: str | None = None,
) -> dict:
    """Call Claude to score one opportunity across all LLM pillars.

    Returns a dict with transferability, opportunity, red_flag, urgency,
    and explainability fields merged into the opportunity.
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    prompt = _USER_PROMPT_TEMPLATE.format(
        name=opportunity.get("name", ""),
        keyword=opportunity.get("keyword", ""),
        brand=opportunity.get("brand", ""),
        signal_breadth=opportunity.get("signal_breadth", 1),
        markets=", ".join(opportunity.get("markets", [])),
        evidence_urls="\n".join(opportunity.get("evidence_urls", [])[:5]),
        target_market=ctx.target_market,
        comparison_markets=", ".join(ctx.comparison_markets),
        niche=ctx.niche,
        competitor_urls=", ".join(ctx.competitor_urls) or "none provided",
        risk_factors=", ".join(ctx.risk_factors) or "none specified",
    )

    try:
        message = client.messages.create(
            model=_MODEL,
            max_tokens=1024,
            thinking={"type": "adaptive"},
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract the text content block
        text = next(
            (block.text for block in message.content if hasattr(block, "text")),
            "",
        )

        # Strip any accidental markdown fences
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        parsed = json.loads(text)
        return _merge_llm_result(opportunity, parsed)

    except json.JSONDecodeError as exc:
        logger.warning("JSON parse error for %s: %s", opportunity.get("name"), exc)
        return _merge_llm_result(opportunity, _fallback_scores())
    except Exception as exc:
        logger.error("LLM error for %s: %s", opportunity.get("name"), exc)
        return _merge_llm_result(opportunity, _fallback_scores())


def _merge_llm_result(opportunity: dict, parsed: dict) -> dict:
    """Merge LLM output into the opportunity record."""
    result = dict(opportunity)

    tf = parsed.get("transferability", {})
    opp = parsed.get("opportunity", {})
    rf = parsed.get("red_flag", {})

    # Pillar totals — normalised 0–1
    tf_total = _normalise_1_5(tf.get("outdoor_relevance", 3), tf.get("dach_availability_gap", 3))
    opp_total = _normalise_1_5(
        opp.get("availability_gap", 3),
        opp.get("retail_saturation", 3),
        opp.get("brand_availability", 3),
    )
    rf_total = _normalise_1_5(
        rf.get("supply_chain_risk", 3),
        rf.get("regulatory_risk", 2),
        rf.get("brand_concentration", 3),
    )

    result["scores"] = result.get("scores", {})
    result["scores"]["transferability"] = {
        "total": tf_total,
        "outdoor_relevance": tf.get("outdoor_relevance", 3),
        "dach_availability_gap": tf.get("dach_availability_gap", 3),
        "explanation": tf.get("explanation", ""),
    }
    result["scores"]["opportunity"] = {
        "total": opp_total,
        "availability_gap": opp.get("availability_gap", 3),
        "retail_saturation": opp.get("retail_saturation", 3),
        "brand_availability": opp.get("brand_availability", 3),
        "explanation": opp.get("explanation", ""),
    }
    result["scores"]["red_flag"] = {
        "total": rf_total,
        "supply_chain_risk": rf.get("supply_chain_risk", 3),
        "regulatory_risk": rf.get("regulatory_risk", 2),
        "brand_concentration": rf.get("brand_concentration", 3),
        "explanation": rf.get("explanation", ""),
    }

    result["urgency"] = parsed.get("urgency", "watch")
    result["explainability"] = {
        "why_trending": parsed.get("why_trending", ""),
        "why_fits_switzerland": parsed.get("why_fits_switzerland", ""),
        "why_opportunity_now": parsed.get("why_opportunity_now", ""),
        "why_to_be_cautious": rf.get("explanation", ""),
    }

    return result


def _normalise_1_5(*values: int | float) -> float:
    """Average a set of 1-5 scores and normalise to 0–1."""
    if not values:
        return 0.5
    avg = sum(values) / len(values)
    return round((avg - 1) / 4, 3)


def _fallback_scores() -> dict:
    return {
        "transferability": {"outdoor_relevance": 3, "dach_availability_gap": 3, "explanation": "Unable to assess"},
        "opportunity": {"availability_gap": 3, "retail_saturation": 3, "brand_availability": 3, "explanation": "Unable to assess"},
        "red_flag": {"supply_chain_risk": 3, "regulatory_risk": 2, "brand_concentration": 3, "explanation": "Unable to assess"},
        "urgency": "watch",
        "why_trending": "",
        "why_fits_switzerland": "",
        "why_opportunity_now": "",
    }
