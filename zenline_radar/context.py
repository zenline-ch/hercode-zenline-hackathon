from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetailerContext:
    """Single configuration object produced by the Q&A entrypoint.

    All downstream pipeline modules receive this object — nothing is
    hardcoded to Switzerland or outdoor retail.
    """

    # Core geography
    target_market: str                     # e.g. "CH"
    comparison_markets: list[str]          # e.g. ["SE", "CA"]

    # Retailer identity
    niche: str                             # e.g. "outdoor retail"
    category_keywords: list[str]           # seed keywords for scraping

    # Demographics (optional filters)
    include_gender: Optional[str] = None   # "female", "male", "all"
    age_range: Optional[tuple[int, int]] = None  # e.g. (25, 45)

    # Competitor intelligence
    competitor_urls: list[str] = field(default_factory=list)

    # Risk profile — checkboxes, not a slider
    risk_factors: list[str] = field(default_factory=list)
    # e.g. ["supply_chain", "regulatory", "brand_concentration"]

    # Score weights (defaults to equal — configurable via UI sliders)
    score_weights: dict[str, float] = field(default_factory=lambda: {
        "trend": 1.0,
        "transferability": 1.0,
        "opportunity": 1.0,
        "red_flag": 1.0,
    })


# ---------------------------------------------------------------------------
# Demo scenario — Swiss outdoor retailer
# ---------------------------------------------------------------------------

DEMO_CONTEXT = RetailerContext(
    target_market="CH",
    comparison_markets=["SE", "CA", "US", "NO"],
    niche="outdoor retail",
    category_keywords=[
        "trail running shoes",
        "merino wool base layer",
        "recycled down jacket",
        "gravel bike",
        "inflatable kayak",
        "lightweight tent",
        "solar panel backpack",
        "cork yoga mat",
        "bamboo hiking poles",
        "arc'teryx",
        "salewa",
        "mammut",
        "ortovox",
        "picture organic",
    ],
    competitor_urls=[
        "https://www.bächli-bergsport.ch",
        "https://www.transa.ch",
        "https://www.ochsner-sport.ch",
    ],
    risk_factors=["supply_chain", "regulatory", "brand_concentration"],
)
