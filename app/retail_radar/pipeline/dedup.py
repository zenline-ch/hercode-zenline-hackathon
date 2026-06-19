"""Deduplicate stage (ARCHITECTURE.md §5).

key = (keyword, brand, market, source_type). Market is deliberately part of
the key so the same trend appearing in two markets stays as two rows --
that's the evidence leadlag.py needs to prove which market led. source_type
is included too: a "marketplace has no listing" check and a "competitor
shelf scan" check are different evidence categories even when they share a
keyword/brand/market, and coverage_gap_score() specifically depends on
source_type=="competitor" rows surviving -- collapsing across types would
silently delete that evidence.

Merging never discards a source name: contributing_sources accumulates
every source that confirmed this signal, so the Breadth pillar (scorer.py)
still sees full source diversity even after near-duplicate rows collapse
(CONTEXT.md: "preserving all contributing source types for Breadth
counting").
"""
from retail_radar.schema import Signal


def _key(s: Signal):
    return (s.keyword.lower().strip(), s.brand.lower().strip(), s.market, s.source_type)


def deduplicate(signals: list[Signal]) -> tuple[list[Signal], dict]:
    before = len(signals)
    seen: dict[tuple, Signal] = {}
    for s in sorted(signals, key=lambda x: x.signal_score, reverse=True):
        k = _key(s)
        if k not in seen:
            seen[k] = s.__class__(**{**s.__dict__, "contributing_sources": [s.source]})
        else:
            kept = seen[k]
            contributing = sorted(set(kept.contributing_sources) | {s.source})
            merged_notes = kept.notes if s.url and s.url in kept.notes else f"{kept.notes} | also: {s.url}" if s.url else kept.notes
            seen[k] = kept.__class__(**{**kept.__dict__, "notes": merged_notes, "contributing_sources": contributing})
    out = list(seen.values())
    log = {"before": before, "after": len(out), "merged": before - len(out)}
    return out, log
