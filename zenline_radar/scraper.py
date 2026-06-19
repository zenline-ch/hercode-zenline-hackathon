"""Signal detection — three explicit rules, each with a clear threshold.

Rule 1 — Search (Google Trends):
  Fetch 90-day interest. Compute slope via linear regression.
  score = slope × 10, clipped 0–10.
  DETECTED if score ≥ SEARCH_MIN_SCORE.

Rule 2 — Marketplace (Amazon bestsellers):
  Scrape top-50 outdoor titles. Count keyword matches.
  score = matches × 2.5, clipped 0–10.
  DETECTED if matches ≥ MARKETPLACE_MIN_MATCHES.

Rule 3 — Curated / manual:
  Expert-vetted signals with pre-assigned scores.
  Always detected.
"""

import datetime
import logging
import time

import numpy as np
import requests
from bs4 import BeautifulSoup

from .context import RetailerContext

logger = logging.getLogger(__name__)
_TODAY = datetime.date.today().isoformat()

# ---------------------------------------------------------------------------
# Detection thresholds — tweak these to change sensitivity
# ---------------------------------------------------------------------------

SEARCH_MIN_SCORE = 2.0          # Google Trends slope × 10 must exceed this
MARKETPLACE_MIN_MATCHES = 1     # keyword must appear in top-50 bestseller titles

# ---------------------------------------------------------------------------
# Signal factory
# ---------------------------------------------------------------------------

def _make_signal(
    source: str,
    signal_type: str,
    market: str,
    keyword: str,
    signal_name: str,
    score: float,
    url: str,
    notes: str = "",
    brand: str = "",
    product_name: str = "",
    confidence: str = "medium",
) -> dict:
    return {
        "source": source,
        "signal_type": signal_type,
        "market": market,
        "keyword": keyword,
        "signal_name": signal_name,
        "brand": brand,
        "product_name": product_name,
        "signal_score": round(score, 2),
        "confidence": confidence,
        "url": url,
        "notes": notes,
        "observed_at": _TODAY,
    }


# ---------------------------------------------------------------------------
# Rule 1 — Search: Google Trends 90-day slope
# ---------------------------------------------------------------------------

def search_signals(ctx: RetailerContext) -> list[dict]:
    """Detect keywords with a rising search trend in comparison markets.

    For each keyword × market: compute 90-day slope via polyfit.
    Emit a signal only when score ≥ SEARCH_MIN_SCORE.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        logger.warning("pytrends not installed — skipping search signals")
        return []

    pytrends = TrendReq(hl="en-US", tz=60)
    detected: list[dict] = []

    for market in ctx.comparison_markets:
        for kw in ctx.category_keywords:
            try:
                pytrends.build_payload([kw], timeframe="today 3-m", geo=market)
                df = pytrends.interest_over_time()
                if df.empty or kw not in df.columns or len(df) < 2:
                    continue

                x = np.arange(len(df))
                slope = float(np.polyfit(x, df[kw].values, 1)[0])
                score = max(0.0, min(10.0, slope * 10.0))

                if score >= SEARCH_MIN_SCORE:
                    detected.append(_make_signal(
                        source="Google Trends",
                        signal_type="search",
                        market=market,
                        keyword=kw,
                        signal_name=kw.title(),
                        score=score,
                        url=f"https://trends.google.com/trends/explore?q={kw.replace(' ', '+')}&geo={market}",
                        notes=f"90-day slope {slope:+.3f} → score {score:.1f}",
                        confidence="high",
                    ))
                    logger.info("DETECTED search: %s in %s (score %.1f)", kw, market, score)
                else:
                    logger.debug("below threshold: %s in %s (score %.1f)", kw, market, score)

                time.sleep(0.5)

            except Exception as exc:
                logger.warning("Google Trends error [%s / %s]: %s", market, kw, exc)

    return detected


# ---------------------------------------------------------------------------
# Rule 2 — Marketplace: Amazon outdoor bestsellers
# ---------------------------------------------------------------------------

_AMAZON_URL = "https://www.amazon.com/Best-Sellers-Sports-Outdoors/zgbs/sporting-goods"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

def marketplace_signals(ctx: RetailerContext) -> list[dict]:
    """Detect keywords appearing in Amazon top-50 outdoor bestseller titles.

    Emit a signal only when matches ≥ MARKETPLACE_MIN_MATCHES.
    """
    try:
        resp = requests.get(_AMAZON_URL, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Amazon fetch failed: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    titles = [
        el.get_text(" ", strip=True)
        for el in soup.select("span._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y, span.a-text-normal")
    ]

    detected: list[dict] = []
    for kw in ctx.category_keywords:
        matches = [t for t in titles if kw.lower() in t.lower()]
        if len(matches) >= MARKETPLACE_MIN_MATCHES:
            score = min(10.0, len(matches) * 2.5)
            detected.append(_make_signal(
                source="Amazon Bestsellers",
                signal_type="marketplace",
                market="US",
                keyword=kw,
                signal_name=kw.title(),
                score=score,
                url=_AMAZON_URL,
                notes=f"{len(matches)} title matches in top-50 outdoor bestsellers",
            ))
            logger.info("DETECTED marketplace: %s (%d matches, score %.1f)", kw, len(matches), score)

    return detected


# ---------------------------------------------------------------------------
# Rule 3 — Curated: expert-vetted signals
# ---------------------------------------------------------------------------

_CURATED: list[dict] = [
    {
        "keyword": "trail running shoes", "signal_name": "Trail Running Shoes",
        "brand": "Hoka", "product_name": "Speedgoat 5", "market": "US",
        "signal_score": 9.0, "confidence": "high",
        "url": "https://www.hoka.com",
        "notes": "Hoka overtook Salomon as #1 trail shoe brand in North America Q1 2026",
    },
    {
        "keyword": "merino wool base layer", "signal_name": "Merino Wool Base Layer",
        "brand": "Icebreaker", "product_name": "", "market": "SE",
        "signal_score": 7.5, "confidence": "high",
        "url": "https://www.icebreaker.com",
        "notes": "Top-selling category in Scandinavian outdoor retail Q1 2026",
    },
    {
        "keyword": "gravel bike", "signal_name": "Gravel E-Bike",
        "brand": "Specialized", "product_name": "", "market": "SE",
        "signal_score": 8.5, "confidence": "high",
        "url": "https://www.specialized.com",
        "notes": "Gravel cycling overtaking MTB in Scandinavian market",
    },
    {
        "keyword": "recycled down jacket", "signal_name": "Recycled Down Jacket",
        "brand": "Picture Organic", "product_name": "", "market": "CA",
        "signal_score": 8.0, "confidence": "high",
        "url": "https://www.picture-organic-clothing.com",
        "notes": "Sustainability angle gaining mainstream traction in Canada",
    },
    {
        "keyword": "lightweight tent", "signal_name": "Ultralight Tent",
        "brand": "Nemo", "product_name": "Aura 2", "market": "NO",
        "signal_score": 7.0, "confidence": "medium",
        "url": "https://www.nemoequipment.com",
        "notes": "Ultralight camping trend driving premium tent demand in Nordics",
    },
    {
        "keyword": "solar panel backpack", "signal_name": "Solar Panel Backpack",
        "brand": "Goal Zero", "product_name": "", "market": "NO",
        "signal_score": 6.5, "confidence": "medium",
        "url": "https://www.goalzero.com",
        "notes": "Tech-integrated outdoor gear growing in Norwegian market",
    },
    {
        "keyword": "cork yoga mat", "signal_name": "Cork Yoga Mat",
        "brand": "Manduka", "product_name": "", "market": "CA",
        "signal_score": 6.0, "confidence": "medium",
        "url": "https://www.manduka.com",
        "notes": "Eco-material yoga gear growing in wellness-outdoor crossover segment",
    },
    {
        "keyword": "bamboo hiking poles", "signal_name": "Bamboo Hiking Poles",
        "brand": "Gossamer Gear", "product_name": "", "market": "US",
        "signal_score": 5.5, "confidence": "low",
        "url": "https://www.gossamergear.com",
        "notes": "Niche sustainable materials entering trekking poles market",
    },
]


def manual_signals(ctx: RetailerContext) -> list[dict]:
    """Return curated signals whose keywords match the retailer's category list."""
    kw_lower = {kw.lower() for kw in ctx.category_keywords}
    results = []
    for row in _CURATED:
        if any(k in row["keyword"].lower() or k in row["signal_name"].lower() for k in kw_lower):
            results.append({
                "source": "Curated Research",
                "signal_type": "manual",
                "market": row["market"],
                "keyword": row["keyword"],
                "signal_name": row["signal_name"],
                "brand": row.get("brand", ""),
                "product_name": row.get("product_name", ""),
                "signal_score": row["signal_score"],
                "confidence": row["confidence"],
                "url": row["url"],
                "notes": row["notes"],
                "observed_at": _TODAY,
            })
    return results


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def collect_signals(
    ctx: RetailerContext,
    enable_search: bool = False,
    enable_marketplace: bool = False,
) -> list[dict]:
    """Run active detection rules and return a flat list of signals."""
    signals: list[dict] = []

    signals.extend(manual_signals(ctx))

    if enable_search:
        signals.extend(search_signals(ctx))

    if enable_marketplace:
        signals.extend(marketplace_signals(ctx))

    logger.info("Total signals detected: %d", len(signals))
    return signals
