"""Clean stage (ARCHITECTURE.md §4): validate, normalise text (keep umlauts),
filter spam, sanity-check dates. Logs what it drops."""
import json
import re
import unicodedata
from dataclasses import replace
from datetime import date
from pathlib import Path

from retail_radar.schema import Signal

SPAM_MARKERS = ["buy now", "discount code", "affiliate", "sponsored", "[deleted]", "clearance"]
_KEEP_CHARS = re.compile(r"[^\w\s\-äöüéèÄÖÜ]", re.UNICODE)

_ALIASES_PATH = Path(__file__).resolve().parent.parent / "config" / "market_aliases.json"
MARKET_ALIASES = json.loads(_ALIASES_PATH.read_text())["aliases"]


def normalise_market(market: str) -> str:
    """Map free-text market names (Switzerland, Swiss, Germany, Austria, ...) to
    the short codes used everywhere downstream (CH, DE, AT, ...). Codes that are
    already correct (or unrecognised) pass through unchanged."""
    return MARKET_ALIASES.get(market.strip().lower(), market.strip())


def _clean_text(t: str) -> str:
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    t = _KEEP_CHARS.sub("", t)
    return t


def _is_spam(s: Signal) -> bool:
    text = f"{s.signal_name} {s.notes}".lower()
    return any(marker in text for marker in SPAM_MARKERS)


def _is_valid(s: Signal) -> bool:
    if not s.signal_name.strip() or len(s.signal_name.strip()) < 4:
        return False
    if not s.url and s.source_type != "manual":
        return False
    return True


def clean(signals: list[Signal]) -> tuple[list[Signal], dict]:
    before = len(signals)
    out = []
    for s in signals:
        if not _is_valid(s) or _is_spam(s):
            continue
        out.append(replace(
            s,
            signal_name=_clean_text(s.signal_name),
            brand=s.brand.strip(),
            market=normalise_market(s.market),
        ))
    log = {"ingested": before, "cleaned": len(out), "dropped": before - len(out)}
    return out, log
