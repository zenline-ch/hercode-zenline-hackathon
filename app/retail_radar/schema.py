"""Dataclasses matching the canonical contract in ARCHITECTURE.md / docs/data-contract.md."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_ALIASES = json.loads((Path(__file__).resolve().parent / "config" / "market_aliases.json").read_text())
_MARKET_ALIASES = _ALIASES["aliases"]
_REGION_EXPANSIONS = _ALIASES["region_expansions"]


def _normalise_market_value(market: str) -> str:
    return _MARKET_ALIASES.get(market.strip().lower(), market.strip())


def _normalise_market_list(markets: list[str]) -> list[str]:
    out = []
    for m in markets:
        key = m.strip().upper()
        if key in _REGION_EXPANSIONS:  # e.g. "DACH" -> ["CH", "DE", "AT"]
            out.extend(_REGION_EXPANSIONS[key])
        else:
            out.append(_normalise_market_value(m))
    seen = set()
    return [m for m in out if not (m in seen or seen.add(m))]


@dataclass
class Signal:
    opportunity_id: str
    opportunity_name: str
    source: str
    source_type: str
    market: str
    keyword: str
    signal_name: str
    product_name: str = ""
    brand: str = ""
    price: str = ""
    rank: str = ""
    url: str = ""
    signal_score: float = 0.0
    confidence: str = "medium"
    notes: str = ""
    observed_at: str = ""
    artifact_type: str = "json"
    artifact_uri: str = "app/retail_radar/data/seed_signals.json"
    created_by_tool: str = "seed_signals"
    contributing_sources: list = field(default_factory=list)


@dataclass
class RetailerContext:
    target_market: str = "CH"
    comparison_markets: list = field(default_factory=lambda: ["US", "Nordics", "Japan", "Korea", "UK"])
    niche: str = "outdoor"
    persona: str = "large_retailer"
    competitor_urls: list = field(default_factory=lambda: ["baechli-bergsport.ch", "transa.ch"])
    scoring_weights: dict = field(default_factory=lambda: {
        "breadth": 0.20,
        "momentum": 0.20,
        "transferability": 0.20,
        "coverage_gap": 0.20,
        "risk": 0.20,
    })

    def __post_init__(self):
        # Accept free-text market names (Switzerland, Swiss, Germany, Austria, DACH, ...)
        # and normalise to the short codes used throughout the pipeline (CH, DE, AT, ...).
        self.target_market = _normalise_market_value(self.target_market)
        self.comparison_markets = _normalise_market_list(self.comparison_markets)

    def normalised_weights(self) -> dict:
        total = sum(self.scoring_weights.values()) or 1.0
        return {k: v / total for k, v in self.scoring_weights.items()}
