"""Dataclasses matching the canonical contract in ARCHITECTURE.md / docs/data-contract.md."""
from dataclasses import dataclass, field
from typing import Optional


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

    def normalised_weights(self) -> dict:
        total = sum(self.scoring_weights.values()) or 1.0
        return {k: v / total for k, v in self.scoring_weights.items()}
