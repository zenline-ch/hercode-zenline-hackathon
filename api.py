"""Zenline Retail Radar — FastAPI backend.

Exposes the zenline_radar pipeline as a REST API.
The Lovable React frontend calls these endpoints.

Run:
  poetry run uvicorn api:app --reload --port 8000
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from zenline_radar.context import RetailerContext, DEMO_CONTEXT
from zenline_radar.scraper import (
    SEARCH_MIN_SCORE,
    MARKETPLACE_MIN_MATCHES,
    collect_signals,
)
from zenline_radar.filter import run_filter_pipeline
from zenline_radar.scorer import score_opportunities

_MOCK_PATH = Path(__file__).parent / "zenline_radar" / "mock_results.json"

app = FastAPI(title="Zenline Retail Radar API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    target_market: str = "CH"
    comparison_markets: list[str] = ["SE", "CA", "US", "NO"]
    niche: str = "outdoor retail"
    category_keywords: list[str]
    competitor_urls: list[str] = []
    risk_factors: list[str] = ["supply_chain", "regulatory", "brand_concentration"]
    score_weights: dict[str, float] = {"trend": 1.0, "transferability": 1.0, "opportunity": 1.0, "red_flag": 1.0}
    enable_search: bool = False
    enable_marketplace: bool = False
    use_mock: bool = True
    api_key: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"service": "Zenline Retail Radar API", "version": "0.1.0"}


@app.get("/api/detection-rules")
def detection_rules():
    """Return the active detection thresholds — shown in the frontend UI."""
    return {
        "rules": [
            {
                "id": "curated",
                "label": "Curated research",
                "icon": "clipboard",
                "description": "Expert-vetted signals",
                "threshold": "Always detected",
            },
            {
                "id": "search",
                "label": "Google Trends",
                "icon": "trending-up",
                "description": "90-day search slope × 10",
                "threshold": f"Detected if score ≥ {SEARCH_MIN_SCORE}",
                "constant": f"SEARCH_MIN_SCORE = {SEARCH_MIN_SCORE}",
            },
            {
                "id": "marketplace",
                "label": "Amazon Bestsellers",
                "icon": "shopping-cart",
                "description": "Keyword in top-50 outdoor titles",
                "threshold": f"Detected if matches ≥ {MARKETPLACE_MIN_MATCHES}",
                "constant": f"MARKETPLACE_MIN_MATCHES = {MARKETPLACE_MIN_MATCHES}",
            },
        ]
    }


@app.get("/api/demo-context")
def demo_context():
    """Return the default Swiss outdoor retailer demo configuration."""
    return {
        "target_market": DEMO_CONTEXT.target_market,
        "comparison_markets": DEMO_CONTEXT.comparison_markets,
        "niche": DEMO_CONTEXT.niche,
        "category_keywords": DEMO_CONTEXT.category_keywords,
        "competitor_urls": DEMO_CONTEXT.competitor_urls,
        "risk_factors": DEMO_CONTEXT.risk_factors,
        "score_weights": DEMO_CONTEXT.score_weights,
    }


@app.get("/api/mock-results")
def mock_results():
    """Return pre-scored demo results — no API key needed."""
    with open(_MOCK_PATH) as f:
        return json.load(f)


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """Run the full pipeline and return scored opportunities.

    Set use_mock=true to skip Anthropic API calls (demo mode).
    """
    if req.use_mock:
        with open(_MOCK_PATH) as f:
            return {"results": json.load(f), "mode": "mock"}

    api_key = req.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required when use_mock=false")

    ctx = RetailerContext(
        target_market=req.target_market,
        comparison_markets=req.comparison_markets,
        niche=req.niche,
        category_keywords=req.category_keywords,
        competitor_urls=req.competitor_urls,
        risk_factors=req.risk_factors,
        score_weights=req.score_weights,
    )

    signals = collect_signals(
        ctx,
        enable_search=req.enable_search,
        enable_marketplace=req.enable_marketplace,
    )
    opportunities = run_filter_pipeline(signals, ctx)
    results = score_opportunities(opportunities, ctx, api_key=api_key)

    return {"results": results, "mode": "live"}
