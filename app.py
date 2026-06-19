"""Zenline Retail Radar — Streamlit MVP (demo version)."""

import json
import logging
import os
import time
from pathlib import Path

import streamlit as st

from zenline_radar.context import RetailerContext, DEMO_CONTEXT
from zenline_radar.scraper import collect_signals
from zenline_radar.filter import run_filter_pipeline
from zenline_radar.scorer import score_opportunities

logging.basicConfig(level=logging.INFO)

_MOCK_PATH = Path(__file__).parent / "zenline_radar" / "mock_results.json"

st.set_page_config(
    page_title="Zenline Retail Radar",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _init_state():
    defaults = {
        "page": "setup",
        "ctx": None,
        "results": None,
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

st.markdown("""
<style>
  .block-container { padding-top: 2rem; padding-bottom: 2rem; }
  .stage-chip {
    display: inline-block; font-size: 0.7rem; font-weight: 700;
    padding: 2px 10px; border-radius: 99px; text-transform: uppercase;
    letter-spacing: 0.06em; margin-right: 6px;
  }
  .stage-emerging   { background: #6366f1; color: #fff; }
  .stage-growing    { background: #10b981; color: #fff; }
  .stage-mainstream { background: #f59e0b; color: #111; }
  .stage-declining  { background: #ef4444; color: #fff; }
  .urgency-chip {
    display: inline-block; font-size: 0.7rem; font-weight: 700;
    padding: 2px 10px; border-radius: 99px; text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .urgency-act-now { background: #10b981; color: #fff; }
  .urgency-watch   { background: #f59e0b; color: #111; }
  .section-header {
    font-size: 1rem; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.1em; margin: 2rem 0 1rem;
    padding-bottom: 6px; border-bottom: 2px solid #374151;
    color: #e5e7eb;
  }
  .score-label { font-size: 0.75rem; color: #9ca3af; margin-bottom: 1px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page 1 — Setup
# ---------------------------------------------------------------------------

def page_setup():
    st.title("🔭 Zenline Retail Radar")
    st.markdown(
        "Detect emerging outdoor opportunities before competitors do — "
        "by scanning global signals and scoring Swiss/DACH transferability with AI."
    )

    with st.form("setup_form"):
        col1, col2 = st.columns(2)
        with col1:
            target_market = st.text_input("Target market", value="CH")
            niche = st.text_input("Retailer niche", value="outdoor retail")
        with col2:
            comparison_markets_raw = st.text_input(
                "Comparison markets (comma-separated)", value="SE, CA, US, NO"
            )

        keywords_raw = st.text_area(
            "Category keywords — one per line",
            value="\n".join(DEMO_CONTEXT.category_keywords),
            height=150,
        )

        col3, col4 = st.columns(2)
        with col3:
            competitor_urls_raw = st.text_area(
                "Competitor URLs (one per line)",
                value="\n".join(DEMO_CONTEXT.competitor_urls),
                height=80,
            )
        with col4:
            st.markdown("**Risk factors to watch**")
            rf_supply = st.checkbox("Supply chain risk", value=True)
            rf_regulatory = st.checkbox("Regulatory risk", value=True)
            rf_brand = st.checkbox("Brand concentration", value=True)

        st.markdown("**Score weights** (drag to emphasise a pillar)")
        wc1, wc2, wc3, wc4 = st.columns(4)
        w_trend    = wc1.slider("Trend",            0.0, 2.0, 1.0, 0.1)
        w_transfer = wc2.slider("Transferability",  0.0, 2.0, 1.0, 0.1)
        w_opp      = wc3.slider("Opportunity",      0.0, 2.0, 1.0, 0.1)
        w_rf       = wc4.slider("Red-Flag (inverse)", 0.0, 2.0, 1.0, 0.1)

        st.divider()

        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown("**Data sources**")
            use_demo    = st.checkbox("Demo / manual signals (always fast)", value=True)
            enable_google = st.checkbox("Google Trends (live, ~30 s)", value=False)
            enable_amazon = st.checkbox("Amazon Bestsellers (live, ~10 s)", value=False)
        with dc2:
            st.markdown("**AI scoring**")
            use_mock_llm = st.checkbox(
                "Use cached demo results (skip Anthropic API calls)",
                value=True,
                help="Loads pre-computed scores — great for demos and testing.",
            )
            api_key = st.text_input(
                "Anthropic API key",
                value=st.session_state["api_key"],
                type="password",
                help="Required when cached results are off.",
            )

        submitted = st.form_submit_button("Run Analysis →", type="primary", use_container_width=True)

    if submitted:
        if not use_mock_llm and not api_key:
            st.error("Paste your Anthropic API key, or enable cached demo results.")
            return

        comparison_markets = [m.strip().upper() for m in comparison_markets_raw.split(",") if m.strip()]
        keywords = [k.strip() for k in keywords_raw.splitlines() if k.strip()]
        competitor_urls = [u.strip() for u in competitor_urls_raw.splitlines() if u.strip()]
        risk_factors = [f for flag, f in [
            (rf_supply, "supply_chain"), (rf_regulatory, "regulatory"), (rf_brand, "brand_concentration")
        ] if flag]

        ctx = RetailerContext(
            target_market=target_market.strip().upper(),
            comparison_markets=comparison_markets,
            niche=niche.strip(),
            category_keywords=keywords,
            competitor_urls=competitor_urls,
            risk_factors=risk_factors,
            score_weights={
                "trend": w_trend, "transferability": w_transfer,
                "opportunity": w_opp, "red_flag": w_rf,
            },
        )

        st.session_state.update({
            "ctx": ctx,
            "api_key": api_key,
            "use_mock_llm": use_mock_llm,
            "source_config": {
                "enable_google": enable_google,
                "enable_amazon": enable_amazon,
                "use_demo": use_demo,
            },
            "page": "running",
        })
        st.rerun()


# ---------------------------------------------------------------------------
# Page 2 — Running
# ---------------------------------------------------------------------------

_SOURCE_LABELS = {
    "manual":      ("📋", "Curated manual signals"),
    "google":      ("📈", "Google Trends (90-day slope)"),
    "amazon":      ("🛒", "Amazon Bestsellers"),
}

def _show_source_step(icon: str, label: str, status: str, count: int | None = None):
    msg = f"{icon} **{label}**"
    if count is not None:
        msg += f" — {count} signal{'s' if count != 1 else ''} found"
    if status == "running":
        st.info(msg + " ...")
    elif status == "done":
        st.success(msg)
    else:
        st.markdown(f"<span style='color:#6b7280'>{msg}</span>", unsafe_allow_html=True)


def page_running():
    st.title("🔭 Zenline Retail Radar")
    ctx: RetailerContext = st.session_state["ctx"]
    api_key: str = st.session_state["api_key"]
    src_cfg = st.session_state.get("source_config", {})
    use_mock_llm: bool = st.session_state.get("use_mock_llm", True)

    st.markdown(f"Analysing **{ctx.niche}** opportunities for **{ctx.target_market}**")
    st.markdown("---")

    # --- Signal collection phase ---
    st.markdown("#### Step 1 · Collecting signals")
    step_manual  = st.empty()
    step_google  = st.empty()
    step_amazon  = st.empty()

    all_signals: list[dict] = []

    # Manual signals
    with step_manual.container():
        _show_source_step("📋", "Curated manual signals", "running")
    from zenline_radar.scraper import get_manual_signals
    manual = get_manual_signals(ctx)
    all_signals.extend(manual)
    with step_manual.container():
        _show_source_step("📋", "Curated manual signals", "done", len(manual))

    # Google Trends
    if src_cfg.get("enable_google"):
        with step_google.container():
            _show_source_step("📈", "Google Trends (90-day slope)", "running")
        from zenline_radar.scraper import scrape_google_trends
        g_signals = scrape_google_trends(ctx, ctx.category_keywords)
        all_signals.extend(g_signals)
        with step_google.container():
            _show_source_step("📈", "Google Trends (90-day slope)", "done", len(g_signals))

    # Amazon
    if src_cfg.get("enable_amazon"):
        with step_amazon.container():
            _show_source_step("🛒", "Amazon Bestsellers", "running")
        from zenline_radar.scraper import scrape_amazon_bestsellers
        a_signals = scrape_amazon_bestsellers(ctx, ctx.category_keywords)
        all_signals.extend(a_signals)
        with step_amazon.container():
            _show_source_step("🛒", "Amazon Bestsellers", "done", len(a_signals))

    total_signals = len(all_signals)
    st.markdown(f"**{total_signals} raw signals collected**")

    # --- Filter phase ---
    st.markdown("---")
    st.markdown("#### Step 2 · Filtering & deduplicating")
    with st.spinner("Matching signals to your niche and markets..."):
        opportunities = run_filter_pipeline(all_signals, ctx)
    st.success(f"{len(opportunities)} unique opportunities identified")

    if not opportunities:
        st.warning("No opportunities found. Try broadening your keywords.")
        if st.button("← Back to setup"):
            st.session_state["page"] = "setup"
            st.rerun()
        return

    # --- Scoring phase ---
    st.markdown("---")
    st.markdown("#### Step 3 · Scoring with AI")

    if use_mock_llm:
        with st.spinner("Loading cached demo scores..."):
            time.sleep(0.8)  # feels more real
            with open(_MOCK_PATH) as f:
                results = json.load(f)
        st.success(f"Loaded {len(results)} pre-scored opportunities (demo mode)")
    else:
        progress_bar = st.progress(0)
        score_status = st.empty()

        def update_progress(i: int, total: int, name: str):
            progress_bar.progress((i + 1) / total)
            score_status.info(f"Scoring {i + 1}/{total}: **{name}**")

        results = score_opportunities(
            opportunities, ctx, api_key=api_key, progress_callback=update_progress
        )
        progress_bar.progress(1.0)
        score_status.success(f"Scored {len(results)} opportunities")

    time.sleep(0.4)
    st.session_state["results"] = results
    st.session_state["page"] = "results"
    st.rerun()


# ---------------------------------------------------------------------------
# Page 3 — Results
# ---------------------------------------------------------------------------

def _mini_bar(label: str, value: float, max_val: float = 1.0, color: str = "#7c3aed"):
    pct = int(min(100, value / max_val * 100))
    st.markdown(
        f"<div class='score-label'>{label}</div>"
        f"<div style='background:#374151;border-radius:4px;height:7px;margin-bottom:6px;'>"
        f"<div style='background:{color};width:{pct}%;height:7px;border-radius:4px;'></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_opportunity(opp: dict):
    stage    = opp.get("trend_stage", "emerging")
    urgency  = opp.get("urgency", "watch")
    name     = opp.get("name", "")
    composite = opp.get("composite_score", 0)
    scores   = opp.get("scores", {})
    expl     = opp.get("explainability", {})
    rank     = opp.get("rank", "")
    buy_rec  = opp.get("buy_recommendation", "")
    brand    = opp.get("brand", "")

    label = f"#{rank}  {name}"
    if brand:
        label += f"  ·  {brand}"
    label += f"  —  {composite:.0%}"

    with st.expander(label, expanded=(rank <= 3)):
        # Top row: chips + buy recommendation
        chips = (
            f'<span class="stage-chip stage-{stage}">{stage}</span>'
            f'<span class="urgency-chip urgency-{"act-now" if urgency == "act_now" else "watch"}">'
            f'{"Act now" if urgency == "act_now" else "Watch"}</span>'
        )
        st.markdown(chips, unsafe_allow_html=True)
        st.markdown(f"**{buy_rec}**")
        st.markdown("")

        col_scores, col_why = st.columns([1, 2])

        # Left: score bars
        with col_scores:
            _mini_bar(f"Composite score  {composite:.0%}", composite, color="#ffffff")
            tr = scores.get("trend", {})
            _mini_bar(f"Trend  (growth {tr.get('growth', 0):.1f}/10)", tr.get("total", 0), color="#6366f1")
            tf = scores.get("transferability", {})
            _mini_bar(f"Transferability  {tf.get('total', 0):.0%}", tf.get("total", 0), color="#8b5cf6")
            op = scores.get("opportunity", {})
            _mini_bar(f"Opportunity  {op.get('total', 0):.0%}", op.get("total", 0), color="#06b6d4")
            rf = scores.get("red_flag", {})
            _mini_bar(f"Red-Flag risk  {rf.get('total', 0):.0%}  (lower is better)", rf.get("total", 0), color="#ef4444")

        # Right: why sentences
        with col_why:
            why_trending = expl.get("why_trending", "")
            why_fits     = expl.get("why_fits_switzerland", "")
            why_now      = expl.get("why_opportunity_now", "")
            why_caution  = expl.get("why_to_be_cautious", "")

            if why_trending:
                st.markdown(f"**Why it's trending** — {why_trending}")
            if why_fits:
                st.markdown(f"**Why it fits Switzerland** — {why_fits}")
            if why_now:
                st.markdown(f"**Why act now** — {why_now}")
            if why_caution:
                st.markdown(
                    f"<span style='color:#fbbf24'>⚠ <b>Caution</b></span> — {why_caution}",
                    unsafe_allow_html=True,
                )

        # Evidence URLs (compact)
        urls = opp.get("evidence_urls", [])
        if urls:
            with st.expander("Evidence sources", expanded=False):
                for url in urls[:5]:
                    display = url[:70] + "..." if len(url) > 70 else url
                    st.markdown(f"- [{display}]({url})")


def page_results():
    results: list[dict] = st.session_state["results"]
    ctx: RetailerContext = st.session_state["ctx"]

    col_h, col_btn = st.columns([5, 1])
    with col_h:
        st.title("🔭 Zenline Retail Radar")
        st.markdown(
            f"**{ctx.target_market}** · **{ctx.niche}** · "
            f"Comparison markets: {', '.join(ctx.comparison_markets)} · "
            f"**{len(results)} opportunities scored**"
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← New analysis"):
            st.session_state.update({"page": "setup", "results": None})
            st.rerun()

    act_now = [o for o in results if o.get("urgency") == "act_now"]
    watch   = [o for o in results if o.get("urgency") != "act_now"]

    st.markdown('<div class="section-header">⚡ Act Now</div>', unsafe_allow_html=True)
    if act_now:
        for opp in act_now:
            _render_opportunity(opp)
    else:
        st.markdown("*No act-now opportunities identified.*")

    st.markdown('<div class="section-header">👁 Watch</div>', unsafe_allow_html=True)
    if watch:
        for opp in watch:
            _render_opportunity(opp)
    else:
        st.markdown("*No watch-list opportunities identified.*")

    st.divider()
    st.download_button(
        "⬇ Download full results (JSON)",
        data=json.dumps(results, indent=2, default=str),
        file_name="zenline_radar_results.json",
        mime="application/json",
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

page = st.session_state["page"]
if page == "setup":
    page_setup()
elif page == "running":
    page_running()
elif page == "results":
    page_results()
