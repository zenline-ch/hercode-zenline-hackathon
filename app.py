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
                "enable_search": enable_google,
                "enable_marketplace": enable_amazon,
            },
            "page": "running",
        })
        st.rerun()


# ---------------------------------------------------------------------------
# Page 2 — Running
# ---------------------------------------------------------------------------

def page_running():
    from zenline_radar.scraper import (
        SEARCH_MIN_SCORE, MARKETPLACE_MIN_MATCHES,
        manual_signals, search_signals, marketplace_signals,
    )
    import pandas as pd

    st.title("🔭 Zenline Retail Radar")
    ctx: RetailerContext = st.session_state["ctx"]
    api_key: str = st.session_state["api_key"]
    src_cfg = st.session_state.get("source_config", {})
    use_mock_llm: bool = st.session_state.get("use_mock_llm", True)

    st.markdown(f"Analysing **{ctx.niche}** opportunities for **{ctx.target_market}**")

    # --- Detection rules legend ---
    st.markdown("#### Detection rules")
    r1, r2, r3 = st.columns(3)
    r1.info(f"**📋 Curated**\nExpert-vetted signals\nAlways included")
    r2.info(f"**📈 Search (Google Trends)**\n90-day slope × 10\nDetected if score ≥ {SEARCH_MIN_SCORE}")
    r3.info(f"**🛒 Marketplace (Amazon)**\nKeyword in top-50 titles\nDetected if matches ≥ {MARKETPLACE_MIN_MATCHES}")

    st.divider()

    # --- Live signal table ---
    st.markdown("#### Step 1 · Signal detection")
    table_placeholder = st.empty()
    all_signals: list[dict] = []

    def _refresh_table(signals: list[dict], source_running: str | None = None):
        rows = []
        for s in signals:
            rows.append({
                "Keyword": s["signal_name"],
                "Source": s["source"],
                "Market": s["market"],
                "Score": f"{s['signal_score']:.1f} / 10",
                "Confidence": s["confidence"],
            })
        if source_running:
            rows.append({
                "Keyword": "...",
                "Source": source_running,
                "Market": "—",
                "Score": "scanning",
                "Confidence": "—",
            })
        if rows:
            table_placeholder.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

    # Curated
    curated = manual_signals(ctx)
    all_signals.extend(curated)
    _refresh_table(all_signals)

    # Search
    if src_cfg.get("enable_search"):
        _refresh_table(all_signals, source_running="Google Trends")
        found = search_signals(ctx)
        all_signals.extend(found)
        _refresh_table(all_signals)

    # Marketplace
    if src_cfg.get("enable_marketplace"):
        _refresh_table(all_signals, source_running="Amazon Bestsellers")
        found = marketplace_signals(ctx)
        all_signals.extend(found)
        _refresh_table(all_signals)

    st.success(f"**{len(all_signals)} signals detected** across {len({s['source'] for s in all_signals})} source(s)")

    # --- Filter + dedup ---
    st.divider()
    st.markdown("#### Step 2 · Filter & deduplicate")
    with st.spinner("Matching signals to your niche and markets..."):
        opportunities = run_filter_pipeline(all_signals, ctx)

    opp_rows = [{"Opportunity": o["name"], "Markets": ", ".join(o["markets"]),
                 "Signal breadth": o["signal_breadth"],
                 "Best score": f"{o['best_signal_score']:.1f} / 10",
                 "Confidence": o["confidence"]} for o in opportunities]
    if opp_rows:
        st.dataframe(pd.DataFrame(opp_rows), use_container_width=True, hide_index=True)
    st.success(f"**{len(opportunities)} unique opportunities** identified")

    if not opportunities:
        st.warning("No opportunities found. Try broadening your keywords.")
        if st.button("← Back to setup"):
            st.session_state["page"] = "setup"
            st.rerun()
        return

    # --- Scoring ---
    st.divider()
    st.markdown("#### Step 3 · AI scoring")

    if use_mock_llm:
        with st.spinner("Loading cached demo scores..."):
            time.sleep(0.6)
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

        # Right: why sentences + inline sources
        with col_why:
            src = opp.get("explainability_sources", {})

            def _why_row(label: str, text: str, key: str, color: str = "#e5e7eb"):
                if not text:
                    return
                sources = src.get(key, [])
                source_links = "  ".join(
                    f'<a href="{s["url"]}" target="_blank" style="font-size:0.72rem;color:#60a5fa;text-decoration:none;border:1px solid #374151;padding:1px 6px;border-radius:4px;">{s["label"]}</a>'
                    for s in sources
                )
                st.markdown(
                    f'<div style="margin-bottom:0.7rem;">'
                    f'<span style="font-weight:700;color:{color};">{label}</span>'
                    f'<span style="color:#d1d5db;"> — {text}</span>'
                    f'{"<br><span style=margin-top:4px;display:inline-block>" + source_links + "</span>" if source_links else ""}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            _why_row("Why it's trending", expl.get("why_trending", ""), "why_trending")
            _why_row("Why it fits Switzerland", expl.get("why_fits_switzerland", ""), "why_fits_switzerland")
            _why_row("Why act now", expl.get("why_opportunity_now", ""), "why_opportunity_now")
            _why_row("⚠ Caution", expl.get("why_to_be_cautious", ""), "why_to_be_cautious", color="#fbbf24")


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
