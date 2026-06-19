"""Lead-lag analysis (ARCHITECTURE.md §9): which market shows this
opportunity's search-type signal earliest, and how far behind is the
target market. Correlation evidence, not causation -- say so on stage."""
from datetime import date

from retail_radar.schema import Signal


def _parse_date(s: str) -> date | None:
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def lead_lag_for_opportunity(signals: list[Signal], target_market: str) -> dict:
    search_signals = [s for s in signals if s.source_type == "search" and _parse_date(s.observed_at)]
    if not search_signals:
        return {"lead_market": None, "lag_days": None, "note": "No search-type signals with a usable date."}

    earliest_by_market: dict[str, date] = {}
    for s in search_signals:
        d = _parse_date(s.observed_at)
        if s.market not in earliest_by_market or d < earliest_by_market[s.market]:
            earliest_by_market[s.market] = d

    ranked = sorted(earliest_by_market.items(), key=lambda kv: kv[1])
    lead_market, lead_date = ranked[0]

    if target_market in earliest_by_market and target_market != lead_market:
        lag_days = (earliest_by_market[target_market] - lead_date).days
    else:
        lag_days = None

    return {
        "lead_market": lead_market,
        "lead_date": lead_date.isoformat(),
        "target_market": target_market,
        "lag_days": lag_days,
        "note": (
            f"{lead_market} showed momentum {lag_days} days before {target_market}."
            if lag_days else
            f"{lead_market} is the earliest-observed market; {target_market} not yet confirmed in this dataset."
        ),
    }
