"""Signal collection from multiple source types.

Each scraper returns a list of raw Signal dicts matching the data-contract.md
schema. No scoring happens here — that's the scorer's job.
"""

import time
import datetime
import logging
from typing import Optional

import numpy as np
import requests
from bs4 import BeautifulSoup

from .context import RetailerContext

logger = logging.getLogger(__name__)

_TODAY = datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# Signal helpers
# ---------------------------------------------------------------------------

def _signal(
    source: str,
    signal_type: str,
    market: str,
    keyword: str,
    signal_name: str,
    signal_score: float,
    url: str,
    confidence: str = "medium",
    notes: str = "",
    product_name: str = "",
    brand: str = "",
) -> dict:
    return {
        "source": source,
        "signal_type": signal_type,
        "market": market,
        "keyword": keyword,
        "signal_name": signal_name,
        "product_name": product_name,
        "brand": brand,
        "signal_score": round(signal_score, 2),
        "confidence": confidence,
        "url": url,
        "notes": notes,
        "observed_at": _TODAY,
    }


# ---------------------------------------------------------------------------
# Google Trends (pytrends)
# ---------------------------------------------------------------------------

def scrape_google_trends(ctx: RetailerContext, keywords: list[str]) -> list[dict]:
    """Return search-trend signals for each keyword × comparison market."""
    try:
        from pytrends.request import TrendReq
    except ImportError:
        logger.warning("pytrends not installed — skipping Google Trends")
        return []

    signals: list[dict] = []
    pytrends = TrendReq(hl="en-US", tz=60)

    for market in ctx.comparison_markets:
        for kw in keywords:
            try:
                pytrends.build_payload([kw], timeframe="today 3-m", geo=market)
                df = pytrends.interest_over_time()
                if df.empty or kw not in df.columns:
                    continue
                series = df[kw].values
                if len(series) < 2:
                    continue
                # 90-day slope via numpy.polyfit (normalised 0–10)
                x = np.arange(len(series))
                slope = float(np.polyfit(x, series, 1)[0])
                score = max(0.0, min(10.0, slope * 10.0))
                url = (
                    f"https://trends.google.com/trends/explore"
                    f"?q={kw.replace(' ', '+')}&geo={market}"
                )
                signals.append(_signal(
                    source="Google Trends",
                    signal_type="search",
                    market=market,
                    keyword=kw,
                    signal_name=kw.title(),
                    signal_score=score,
                    url=url,
                    confidence="high",
                    notes=f"90-day slope={slope:.4f}",
                ))
                time.sleep(0.5)  # stay within rate limits
            except Exception as exc:
                logger.warning("Google Trends error [%s / %s]: %s", market, kw, exc)

    return signals


# ---------------------------------------------------------------------------
# Reddit (PRAW)
# ---------------------------------------------------------------------------

def scrape_reddit(
    ctx: RetailerContext,
    keywords: list[str],
    reddit_client_id: Optional[str] = None,
    reddit_client_secret: Optional[str] = None,
    reddit_user_agent: str = "zenline-radar/0.1",
) -> list[dict]:
    """Return social signals from outdoor-relevant subreddits."""
    if not (reddit_client_id and reddit_client_secret):
        logger.info("Reddit credentials not set — skipping Reddit scraper")
        return []

    try:
        import praw
    except ImportError:
        logger.warning("praw not installed — skipping Reddit")
        return []

    subreddits = [
        "ultralight", "hiking", "trailrunning", "cycling", "gravel",
        "skiandsnowboard", "climbing", "kayaking", "alpinism", "outdoors",
    ]

    reddit = praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
    )

    signals: list[dict] = []
    for sub_name in subreddits:
        for kw in keywords:
            try:
                sub = reddit.subreddit(sub_name)
                results = list(sub.search(kw, limit=5, time_filter="month"))
                if not results:
                    continue
                score = min(10.0, len(results) * 2.0)
                top_url = f"https://reddit.com/r/{sub_name}/search/?q={kw.replace(' ', '+')}"
                signals.append(_signal(
                    source=f"Reddit r/{sub_name}",
                    signal_type="social",
                    market="US",  # Reddit is predominantly US/EN
                    keyword=kw,
                    signal_name=kw.title(),
                    signal_score=score,
                    url=top_url,
                    confidence="medium",
                    notes=f"{len(results)} posts in last 30 days",
                ))
            except Exception as exc:
                logger.warning("Reddit error [%s / %s]: %s", sub_name, kw, exc)

    return signals


# ---------------------------------------------------------------------------
# Amazon Bestsellers (lightweight scrape)
# ---------------------------------------------------------------------------

_AMAZON_OUTDOOR_URL = "https://www.amazon.com/Best-Sellers-Sports-Outdoors/zgbs/sporting-goods"

def scrape_amazon_bestsellers(ctx: RetailerContext, keywords: list[str]) -> list[dict]:
    """Scrape Amazon US outdoor bestseller page and match against keywords."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    signals: list[dict] = []
    try:
        resp = requests.get(_AMAZON_OUTDOOR_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("div.zg-item-immersion")[:50]

        titles = [
            el.get_text(" ", strip=True)
            for el in soup.select("._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y, span.a-text-normal")
        ]

        for kw in keywords:
            kw_lower = kw.lower()
            matches = [t for t in titles if kw_lower in t.lower()]
            if not matches:
                continue
            rank_score = min(10.0, len(matches) * 3.0)
            signals.append(_signal(
                source="Amazon Bestsellers",
                signal_type="marketplace",
                market="US",
                keyword=kw,
                signal_name=kw.title(),
                signal_score=rank_score,
                url=_AMAZON_OUTDOOR_URL,
                confidence="medium",
                notes=f"{len(matches)} bestseller titles matched",
            ))
    except Exception as exc:
        logger.warning("Amazon scrape error: %s", exc)

    return signals


# ---------------------------------------------------------------------------
# Manual / curated signals (always available)
# ---------------------------------------------------------------------------

_MANUAL_SIGNALS: list[dict] = [
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "SE",
        "keyword": "merino wool base layer",
        "signal_name": "Merino Wool Base Layer",
        "product_name": "",
        "brand": "Icebreaker",
        "signal_score": 7.5,
        "confidence": "high",
        "url": "https://www.icebreaker.com",
        "notes": "Top-selling category in Scandinavian outdoor retail Q1 2026",
        "observed_at": _TODAY,
    },
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "CA",
        "keyword": "recycled down jacket",
        "signal_name": "Recycled Down Jacket",
        "product_name": "",
        "brand": "Picture Organic",
        "signal_score": 8.0,
        "confidence": "high",
        "url": "https://www.picture-organic-clothing.com",
        "notes": "Sustainability angle gaining mainstream traction in Canadian market",
        "observed_at": _TODAY,
    },
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "NO",
        "keyword": "solar panel backpack",
        "signal_name": "Solar Panel Backpack",
        "product_name": "",
        "brand": "Goal Zero",
        "signal_score": 6.5,
        "confidence": "medium",
        "url": "https://www.goalzero.com",
        "notes": "Growing interest in tech-integrated outdoor gear",
        "observed_at": _TODAY,
    },
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "US",
        "keyword": "trail running shoes",
        "signal_name": "Trail Running Shoes",
        "product_name": "Speedgoat 5",
        "brand": "Hoka",
        "signal_score": 9.0,
        "confidence": "high",
        "url": "https://www.hoka.com",
        "notes": "Hoka gaining significant market share from Salomon in trail running",
        "observed_at": _TODAY,
    },
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "SE",
        "keyword": "gravel bike",
        "signal_name": "Gravel E-Bike",
        "product_name": "",
        "brand": "Specialized",
        "signal_score": 8.5,
        "confidence": "high",
        "url": "https://www.specialized.com",
        "notes": "Gravel cycling category overtaking MTB in Scandinavian markets",
        "observed_at": _TODAY,
    },
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "CA",
        "keyword": "cork yoga mat",
        "signal_name": "Cork Yoga Mat",
        "product_name": "",
        "brand": "Manduka",
        "signal_score": 6.0,
        "confidence": "medium",
        "url": "https://www.manduka.com",
        "notes": "Eco-material yoga gear growing in wellness-outdoor crossover segment",
        "observed_at": _TODAY,
    },
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "NO",
        "keyword": "lightweight tent",
        "signal_name": "Ultralight Tent",
        "product_name": "Aura 2",
        "brand": "Nemo",
        "signal_score": 7.0,
        "confidence": "medium",
        "url": "https://www.nemoequipment.com",
        "notes": "Ultralight camping trend driving premium tent demand",
        "observed_at": _TODAY,
    },
    {
        "source": "Manual Research",
        "signal_type": "manual",
        "market": "US",
        "keyword": "bamboo hiking poles",
        "signal_name": "Bamboo Hiking Poles",
        "product_name": "",
        "brand": "Gossamer Gear",
        "signal_score": 5.5,
        "confidence": "low",
        "url": "https://www.gossamergear.com",
        "notes": "Niche sustainable materials entering trekking poles market",
        "observed_at": _TODAY,
    },
]


def get_manual_signals(ctx: RetailerContext) -> list[dict]:
    """Return curated manual signals relevant to the retailer's keywords."""
    kw_lower = {kw.lower() for kw in ctx.category_keywords}
    return [
        s for s in _MANUAL_SIGNALS
        if any(k in s["keyword"].lower() or k in s["signal_name"].lower() for k in kw_lower)
    ]


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def collect_signals(
    ctx: RetailerContext,
    enable_google_trends: bool = True,
    enable_reddit: bool = False,
    enable_amazon: bool = True,
    reddit_client_id: Optional[str] = None,
    reddit_client_secret: Optional[str] = None,
) -> list[dict]:
    """Collect signals from all active sources and return a flat list."""
    signals: list[dict] = []

    signals.extend(get_manual_signals(ctx))

    if enable_google_trends:
        logger.info("Scraping Google Trends (%d keywords × %d markets)...",
                    len(ctx.category_keywords), len(ctx.comparison_markets))
        signals.extend(scrape_google_trends(ctx, ctx.category_keywords))

    if enable_amazon:
        logger.info("Scraping Amazon Bestsellers...")
        signals.extend(scrape_amazon_bestsellers(ctx, ctx.category_keywords))

    if enable_reddit:
        signals.extend(scrape_reddit(
            ctx, ctx.category_keywords,
            reddit_client_id=reddit_client_id,
            reddit_client_secret=reddit_client_secret,
        ))

    logger.info("Collected %d raw signals", len(signals))
    return signals
