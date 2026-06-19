"""Relevance filter and deduplication — pre-scoring steps.

Relevance filter:
  Remove signals not matching the RetailerContext niche and not originating
  from a target or comparison market.

Deduplication:
  Collapse signals referring to the same opportunity across multiple source
  types into a single opportunity record, preserving all contributing source
  types for Signal Breadth counting.
"""

from collections import defaultdict

from .context import RetailerContext


# ---------------------------------------------------------------------------
# Relevance filter
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return text.lower().strip()


def _keyword_matches(signal: dict, ctx: RetailerContext) -> bool:
    """True if any RetailerContext keyword appears in the signal's keyword or name."""
    haystack = _normalize(
        f"{signal.get('keyword', '')} {signal.get('signal_name', '')} {signal.get('product_name', '')} {signal.get('brand', '')}"
    )
    return any(_normalize(kw) in haystack for kw in ctx.category_keywords)


def _market_matches(signal: dict, ctx: RetailerContext) -> bool:
    """True if the signal's market is the target or a comparison market."""
    valid = {ctx.target_market} | set(ctx.comparison_markets)
    return signal.get("market", "").upper() in valid


def apply_relevance_filter(signals: list[dict], ctx: RetailerContext) -> list[dict]:
    """Remove signals that don't match niche keywords or known markets."""
    filtered = [
        s for s in signals
        if _keyword_matches(s, ctx) and _market_matches(s, ctx)
    ]
    return filtered


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _opportunity_key(signal: dict) -> str:
    """Canonical key for grouping signals into a single opportunity."""
    name = _normalize(signal.get("signal_name") or signal.get("keyword") or "")
    # Strip common suffixes/prefixes for better grouping
    for sub in ("shoes", "jacket", "mat", "tent", "poles", "backpack", "bike"):
        if sub in name:
            name = name.replace(sub, "").strip()
    return name


def deduplicate(signals: list[dict]) -> list[dict]:
    """Group signals by opportunity and produce one record per opportunity.

    The merged record carries:
    - All contributing source types (for Signal Breadth)
    - The highest signal_score observed
    - All evidence URLs
    - All markets seen
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    for s in signals:
        key = _opportunity_key(s)
        groups[key].append(s)

    opportunities: list[dict] = []
    for key, group in groups.items():
        source_types = list({s["signal_type"] for s in group})
        markets = list({s["market"] for s in group})
        best = max(group, key=lambda s: s.get("signal_score", 0))
        urls = list({s["url"] for s in group if s.get("url")})

        merged = {
            "id": key.replace(" ", "-"),
            "name": best.get("signal_name") or best.get("keyword", key).title(),
            "keyword": best.get("keyword", key),
            "brand": best.get("brand", ""),
            "product_name": best.get("product_name", ""),
            "markets": markets,
            "source_types": source_types,
            "signal_breadth": len(source_types),  # count of distinct source types
            "best_signal_score": best.get("signal_score", 0),
            "evidence_urls": urls,
            "confidence": _aggregate_confidence(group),
            "signals": group,
        }
        opportunities.append(merged)

    return opportunities


def _aggregate_confidence(signals: list[dict]) -> str:
    levels = {"high": 3, "medium": 2, "low": 1}
    scores = [levels.get(s.get("confidence", "low"), 1) for s in signals]
    avg = sum(scores) / len(scores)
    if avg >= 2.5:
        return "high"
    if avg >= 1.5:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_filter_pipeline(signals: list[dict], ctx: RetailerContext) -> list[dict]:
    """Apply relevance filter then deduplication. Returns opportunity records."""
    relevant = apply_relevance_filter(signals, ctx)
    opportunities = deduplicate(relevant)
    return opportunities
