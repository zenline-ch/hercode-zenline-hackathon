# ADR 0001: Hybrid scoring — deterministic dimensions + LLM transferability

## Status
Accepted

## Context
The scoring system has three dimensions: Signal Breadth, Momentum, and Transferability. Breadth and Momentum can be computed deterministically from scraped data (source type count, Google Trends slope). Transferability requires reasoning about whether a specific market pair (e.g. Sweden → Switzerland) makes cultural, climatic, and commercial sense — a judgment that is hard to express as a rule.

## Decision
Use deterministic computation for Breadth and Momentum. Use an LLM for Transferability only, with structured JSON output (`score`, `reason`, `urgency`). The LLM receives the signal, source market, target market, and RetailerContext as structured input so the judgment is grounded, not generic.

## Consequences
- The `reason` field from the LLM is displayed directly in the UI — no extra explainability layer needed.
- Transferability scoring requires an LLM API call per opportunity, adding latency and cost.
- Deterministic dimensions are fully auditable and rerunnable without an API key.
- A future fully-offline mode could replace LLM transferability with a rule table, if needed.
