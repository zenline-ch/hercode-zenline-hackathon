"""Collect stage (ARCHITECTURE.md / diagram.md §1).

Live scrapers (pytrends, marketplace/competitor scans) belong here later.
For now this loads the offline seed dataset so the app runs with zero API
keys and never breaks live in front of a jury (ARCHITECTURE.md §11 caveat).
"""
import json
from pathlib import Path

from retail_radar.schema import Signal

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED_SIGNALS_PATH = DATA_DIR / "seed_signals.json"


def load_seed_signals() -> list[Signal]:
    raw = json.loads(SEED_SIGNALS_PATH.read_text())
    return [Signal(**row) for row in raw["signals"]]


def collect(context) -> list[Signal]:
    """Entry point the pipeline calls. Swap this body for live collectors
    (pytrends per context.comparison_markets, competitor scrapers for
    context.competitor_urls, etc.) without touching anything downstream."""
    return load_seed_signals()
