"""AI chat grounded in the computed opportunities (ARCHITECTURE.md, diagram.md §6).

Uses Anthropic Claude if ANTHROPIC_API_KEY is set. The model is told to tag
any opportunity it references with [[opp:<id>]] so the UI can render a
"View in dashboard" button under that message. Falls back to a deterministic
keyword-matching responder if no key is set or the call fails -- the chat
must never go blank in front of the jury.
"""
import os
import re

OPP_TAG_RE = re.compile(r"\[\[opp:([a-z0-9\-]+)\]\]")


def _condense_opportunities(opportunities: list[dict]) -> str:
    lines = []
    for o in opportunities:
        lines.append(
            f"- id={o['id']} | {o['name']} | composite_score={o['composite_score']} | "
            f"confidence={o['confidence']} | coverage_status={o['coverage_status']} | "
            f"urgency={o['urgency']} | trend_stage={o['trend_stage']} | "
            f"buy_recommendation=\"{o['buy_recommendation']}\" | "
            f"why_trending=\"{o['explainability']['why_trending']}\" | "
            f"why_opportunity_now=\"{o['explainability']['why_opportunity_now']}\""
        )
    return "\n".join(lines)


def answer(question: str, context, opportunities: list[dict], history: list[dict]) -> tuple[str, str | None]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _answer_llm(question, context, opportunities, history, api_key)
        except Exception as exc:  # noqa: BLE001
            return _answer_fallback(question, opportunities, error=str(exc))
    return _answer_fallback(question, opportunities)


def _answer_llm(question, context, opportunities, history, api_key) -> tuple[str, str | None]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    system = (
        "You are Retail Radar's analyst chat for a Swiss outdoor retailer. "
        "Answer using ONLY the opportunity data provided below -- do not invent SKUs, prices, "
        "or sources that aren't listed. Be concise (3-5 sentences). When you reference a specific "
        "opportunity, tag it inline like [[opp:gravel-running]] using its id from the list. "
        "If asked what to buy now, prioritise urgency=act_now and high confidence. If an "
        "opportunity is confidence=low, make clear it's a monitor-only signal, not a buy.\n\n"
        f"Retailer context: target_market={context.target_market}, persona={context.persona}, "
        f"niche={context.niche}, comparison_markets={context.comparison_markets}\n\n"
        f"Opportunities:\n{_condense_opportunities(opportunities)}"
    )
    messages = [{"role": h["role"], "content": h["content"]} for h in history[-6:]]
    messages.append({"role": "user", "content": question})

    resp = client.messages.create(model=model, max_tokens=400, system=system, messages=messages)
    text = resp.content[0].text.strip()
    match = OPP_TAG_RE.search(text)
    opp_id = match.group(1) if match else None
    clean_text = OPP_TAG_RE.sub("", text).strip()
    return clean_text, opp_id


def _answer_fallback(question: str, opportunities: list[dict], error: str | None = None) -> tuple[str, str | None]:
    q = question.lower()
    best = None
    for o in opportunities:
        if o["id"].replace("-", " ") in q or o["name"].lower() in q:
            best = o
            break

    prefix = "(offline mode -- no ANTHROPIC_API_KEY set, answering from computed scores only)\n\n" if not error else \
        "(LLM call failed, falling back to computed scores)\n\n"

    if best:
        text = (
            f"{prefix}**{best['name']}** -- composite score {best['composite_score']} ({best['confidence']} confidence), "
            f"coverage is {best['coverage_status']}, urgency is {best['urgency']}. "
            f"{best['buy_recommendation']}. {best['explainability']['why_opportunity_now']}"
        )
        return text, best["id"]

    if "buy" in q or "act now" in q or "what should we" in q:
        candidates = [o for o in opportunities if o["urgency"] == "act_now"]
        candidates.sort(key=lambda o: o["composite_score"], reverse=True)
        if candidates:
            top = candidates[0]
            text = (
                f"{prefix}Top act-now opportunity right now is **{top['name']}** "
                f"(score {top['composite_score']}, {top['confidence']} confidence, coverage {top['coverage_status']}). "
                f"{top['buy_recommendation']}"
            )
            return text, top["id"]
        text = f"{prefix}No opportunity currently clears the act-now bar at this persona's confidence threshold -- everything is monitor-only right now."
        return text, None

    if "watch" in q or "monitor" in q or "low confidence" in q:
        candidates = [o for o in opportunities if o["confidence"] == "low"]
        if candidates:
            top = candidates[0]
            text = f"{prefix}**{top['name']}** is the clearest monitor-only signal: confidence is low, coverage is {top['coverage_status']}. {top['buy_recommendation']}"
            return text, top["id"]

    ranked = sorted(opportunities, key=lambda o: o["composite_score"], reverse=True)[:3]
    summary = "; ".join(f"{o['name']} ({o['confidence']}, {o['urgency']})" for o in ranked)
    text = f"{prefix}Ask me about a specific opportunity by name, or what to buy now / what to watch. Top-ranked right now: {summary}."
    return text, None
