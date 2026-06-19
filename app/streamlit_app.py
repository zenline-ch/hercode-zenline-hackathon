"""Retail Radar -- draft frontend (chat + dashboard).

Implements diagram.md §6: a RetailerContext wizard, an AI chat that answers
from the computed opportunities, and a dashboard that the chat can deep-link
into. This is intentionally a thin presentation layer over
retail_radar.pipeline.run_pipeline.build_recommendations() -- when the
Lovable frontend is ready, it consumes the exact same recommendations.json
contract (ARCHITECTURE.md §10) and this file can be retired without
touching any backend code.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from retail_radar.chat import assistant
from retail_radar.pipeline.run_pipeline import build_recommendations
from retail_radar.schema import RetailerContext

import json
PERSONAS = json.loads((Path(__file__).resolve().parent / "retail_radar/config/personas.json").read_text())
PERSONAS = {k: v for k, v in PERSONAS.items() if not k.startswith("_")}
SOURCES = json.loads((Path(__file__).resolve().parent / "retail_radar/config/sources.json").read_text())["sources"]

st.set_page_config(page_title="Retail Radar", page_icon="🧭", layout="wide")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "setup"
if "context" not in st.session_state:
    st.session_state.context = None
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_opportunity_id" not in st.session_state:
    st.session_state.selected_opportunity_id = None


def goto(view: str):
    st.session_state.view = view


def run_pipeline_for_context(context: RetailerContext):
    st.session_state.context = context
    st.session_state.result = build_recommendations(context)
    st.session_state.chat_history = []
    st.session_state.selected_opportunity_id = None


# ---------------------------------------------------------------------------
# Sidebar -- always visible once context is set
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 Retail Radar")
    if st.session_state.context is not None:
        ctx = st.session_state.context
        st.caption(f"**{ctx.niche}** · target **{ctx.target_market}** · persona **{PERSONAS[ctx.persona]['label']}**")
        if st.button("💬 Chat", use_container_width=True):
            goto("chat")
        if st.button("📊 Dashboard", use_container_width=True):
            goto("dashboard")
        if st.button("⚙️ Edit context", use_container_width=True):
            goto("setup")
        st.divider()
        log = st.session_state.result["log"]
        st.caption(log["narration"])
        st.divider()
        st.markdown("**Download evidence**")
        signals_csv = (Path(__file__).resolve().parent / "retail_radar/data/signals.csv")
        rec_json = (Path(__file__).resolve().parent / "retail_radar/data/recommendations.json")
        if signals_csv.exists():
            st.download_button("signals.csv", signals_csv.read_bytes(), file_name="signals.csv", use_container_width=True)
        if rec_json.exists():
            st.download_button("recommendations.json", rec_json.read_bytes(), file_name="recommendations.json", use_container_width=True)
        st.divider()
        with st.expander("Source credibility (config-driven)"):
            for s in SOURCES:
                st.caption(f"**{s['name']}** ({s['source_type']}) -- {s['credibility']}")


# ---------------------------------------------------------------------------
# Setup view -- RetailerContext wizard
# ---------------------------------------------------------------------------
def render_setup():
    st.title("Retail Radar")
    st.caption(
        "We don't just detect global trends -- we score them against the Swiss shelf. "
        "A trend rising in Google Trends CH but absent from Bachli/Transa is a quantified "
        "assortment gap, not a guess."
    )
    st.subheader("1. Set up your RetailerContext")

    with st.form("context_form"):
        col1, col2 = st.columns(2)
        with col1:
            target_market = st.text_input("Target market", value="CH")
            niche = st.text_input("Niche / category", value="outdoor")
            persona = st.radio(
                "Persona",
                options=list(PERSONAS.keys()),
                format_func=lambda k: PERSONAS[k]["label"],
                index=0,
            )
        with col2:
            comparison_markets = st.multiselect(
                "Comparison markets (early-signal sources)",
                options=["US", "Nordics", "Japan", "Korea", "UK", "DE", "AT", "SE", "CA"],
                default=["US", "Nordics", "Japan", "Korea", "UK"],
            )
            competitor_urls = st.text_input(
                "Competitor URLs (comma-separated)",
                value="baechli-bergsport.ch, transa.ch",
            )

        st.markdown("**Scoring weights** (auto-normalised to sum to 1.0)")
        w1, w2, w3, w4, w5 = st.columns(5)
        breadth_w = w1.slider("Breadth", 0.0, 1.0, 0.20, 0.05)
        momentum_w = w2.slider("Momentum", 0.0, 1.0, 0.20, 0.05)
        transfer_w = w3.slider("Transferability", 0.0, 1.0, 0.20, 0.05)
        coverage_w = w4.slider("Coverage Gap", 0.0, 1.0, 0.20, 0.05)
        risk_w = w5.slider("Risk Factor", 0.0, 1.0, 0.20, 0.05)

        submitted = st.form_submit_button("🚀 Run Retail Radar", use_container_width=True)

    if submitted:
        context = RetailerContext(
            target_market=target_market.strip() or "CH",
            comparison_markets=comparison_markets or ["US", "Nordics", "Japan", "Korea", "UK"],
            niche=niche.strip() or "outdoor",
            persona=persona,
            competitor_urls=[u.strip() for u in competitor_urls.split(",") if u.strip()],
            scoring_weights={
                "breadth": breadth_w, "momentum": momentum_w, "transferability": transfer_w,
                "coverage_gap": coverage_w, "risk": risk_w,
            },
        )
        run_pipeline_for_context(context)
        goto("chat")
        st.rerun()


# ---------------------------------------------------------------------------
# Chat view
# ---------------------------------------------------------------------------
def render_chat():
    st.title("💬 Ask Retail Radar")
    opportunities = st.session_state.result["opportunities"]
    ctx = st.session_state.context

    act_now = sum(1 for o in opportunities if o["urgency"] == "act_now")
    watch = len(opportunities) - act_now
    c1, c2, c3 = st.columns(3)
    c1.metric("Opportunities found", len(opportunities))
    c2.metric("Act now", act_now)
    c3.metric("Watch only", watch)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("opp_id"):
                if st.button("📊 Open in dashboard →", key=f"open_{id(msg)}"):
                    st.session_state.selected_opportunity_id = msg["opp_id"]
                    goto("dashboard")
                    st.rerun()

    question = st.chat_input("e.g. \"What should we buy now?\" or \"Tell me about gravel running\"")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        text, opp_id = assistant.answer(question, ctx, opportunities, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": text, "opp_id": opp_id})
        st.rerun()

    if not st.session_state.chat_history:
        st.info(
            "Try: \"What should we buy now?\", \"What's the riskiest opportunity?\", "
            "or \"Tell me about mycelium\"."
        )


# ---------------------------------------------------------------------------
# Dashboard view
# ---------------------------------------------------------------------------
_CONF_COLOR = {"high": "🟢", "medium": "🟡", "low": "🔴"}


def render_opportunity_card(o: dict, expand: bool):
    header = f"{_CONF_COLOR[o['confidence']]} **{o['name']}** -- score {o['composite_score']} · {o['trend_stage']} · {o['coverage_status']}"
    with st.expander(header, expanded=expand):
        st.markdown(f"**Buy recommendation:** {o['buy_recommendation']}")
        st.markdown(f"**Confidence:** {o['confidence']} &nbsp;&nbsp; **Urgency:** {o['urgency']} &nbsp;&nbsp; **Expected window:** {o['expected_window']}")

        st.markdown("**Why**")
        st.markdown(f"- *Trending:* {o['explainability']['why_trending']}")
        st.markdown(f"- *Fits target market:* {o['explainability']['why_fits_switzerland']}")
        st.markdown(f"- *Opportunity now:* {o['explainability']['why_opportunity_now']}")

        ll = o.get("lead_lag", {})
        if ll.get("lead_market"):
            st.caption(f"📍 Lead-lag: {ll['note']}")

        st.markdown("**Score breakdown**")
        scores = o["scores"]
        st.bar_chart({k: v["total"] for k, v in scores.items() if k != "noise"})  # noise is on a 0-5 scale, others are 0-1
        noise = scores.get("noise", {})
        if noise:
            st.caption(f"Noise score (0-5, higher = cleaner): {noise['total']} "
                       f"(social-only ratio {noise['social_only_ratio']}, oldest evidence {noise['recency_days_avg']}d ago)")

        if o["risk_flags"]:
            st.warning("Risk flags: " + ", ".join(o["risk_flags"]))

        with st.container():
            st.markdown("**When to stop**")
            for trig in o["monitor_triggers"]:
                st.caption(f"⛔ {trig}")
            for rev in o["reversal_signals"]:
                st.caption(f"📉 {rev}")

        st.markdown("**Signals**")
        st.dataframe(
            [{"source": s["source"], "market": s["market"], "score": s["signal_score"], "url": s["url"], "observed_at": s["observed_at"]} for s in o["signals"]],
            use_container_width=True,
            hide_index=True,
        )


def render_dashboard():
    st.title("📊 Opportunity dashboard")
    opportunities = st.session_state.result["opportunities"]
    selected = st.session_state.selected_opportunity_id

    act_now = [o for o in opportunities if o["urgency"] == "act_now"]
    watch = [o for o in opportunities if o["urgency"] == "watch"]

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(f"🟢 Act now ({len(act_now)})")
        for o in act_now:
            render_opportunity_card(o, expand=(o["id"] == selected))
    with col_b:
        st.subheader(f"⏸️ Watch ({len(watch)})")
        for o in watch:
            render_opportunity_card(o, expand=(o["id"] == selected))


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if st.session_state.view == "setup" or st.session_state.context is None:
    render_setup()
elif st.session_state.view == "chat":
    render_chat()
elif st.session_state.view == "dashboard":
    render_dashboard()
