# ADR 0002: Explicit threshold-based signal detection

## Status
Accepted

## Context
Signal detection must be transparent enough to explain to a retail buyer in 30 seconds. Early designs scraped multiple sources with complex selectors and implicit scoring. This made it hard to answer "why was this flagged?" and "what would it take to get a higher score?".

## Decision
Each data source applies one explicit detection rule with a named, tunable threshold constant. A data point becomes a Signal only if it passes the threshold. Below-threshold data is discarded at collection time, not filtered later.

| Source | Detection rule | Threshold constant |
|---|---|---|
| Google Trends | 90-day slope × 10 ≥ threshold | `SEARCH_MIN_SCORE = 2.0` |
| Amazon bestsellers | keyword matches in top-50 titles ≥ threshold | `MARKETPLACE_MIN_MATCHES = 1` |
| Curated research | always detected | n/a (pre-vetted) |

The signal score is the rule's raw output: slope × 10 for search, matches × 2.5 for marketplace, expert-assigned for curated. All scores are on a 0–10 scale.

## Why threshold-at-source (not filter-later)
Filtering late means the UI must explain why data was discarded after the fact. Filtering at source means every emitted signal already satisfies a stated condition — the threshold constant is the answer to "why was this flagged?".

## Consequences
- The detection logic for each source fits in one function with one threshold check.
- Thresholds are exported constants — they are shown in the UI during analysis so the audience sees the exact rule that triggered each detection.
- Adding a new source = writing one function with one threshold check.
- Below-threshold signals are logged at DEBUG level (not emitted to the UI) so the analysis can be audited.
- Reddit was dropped: it requires OAuth credentials, has rate limits, and its detection logic (mention count) is harder to explain than a search slope. A future version could add it with a `SOCIAL_MIN_MENTIONS` constant.
