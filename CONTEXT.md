# Context

## Glossary

**RetailerContext**
The structured configuration object produced by the Q&A entrypoint. Captures: target market, comparison markets, niche/category, demographic filters (gender, age range), competitor URLs, and scoring weights. All downstream modules receive a `RetailerContext` — nothing is hardcoded to Switzerland or outdoor retail.

**Comparison Market**
A market the user identifies as a credible signal source for the target market. Example: Sweden and Canada for a Swiss outdoor retailer. Signals are scraped *from* comparison markets. Transferability scoring reasons over the specific pair: comparison market → target market.

**Target Market**
The market the retailer operates in. Switzerland for the demo scenario. All transferability judgments are made relative to the target market.

**Signal**
A single piece of evidence from one source about one emerging opportunity. Has a source type, a market, a keyword or phrase, and a URL. Defined by the fields in `docs/data-contract.md`.

**Source Type**
The category of a signal's origin: `search`, `social`, `marketplace`, `web`, `manual`. Used as the unit of Signal Breadth counting.

**Opportunity**
A candidate product, material, brand, or feature that the scoring pipeline has surfaced and ranked. An opportunity is backed by one or more signals across one or more source types.

**Signal Breadth**
Count of distinct source types that independently surface the same opportunity. Scale 0–5. Higher = more independent confirmation.

**Momentum**
Rate of growth of an opportunity's keyword over the last 90 days, measured via Google Trends for the comparison market(s). Normalized 0–10. Slope computed with `numpy.polyfit`.

**Transferability**
LLM-assessed likelihood that an opportunity observed in a comparison market will succeed in the target market. Scored 1–5 with a one-sentence rationale and an urgency flag (`act_now` or `watch`). The LLM receives the signal, the source market, the target market, and relevant RetailerContext fields as structured input.

**Composite Score**
Weighted average of normalized Breadth (÷5), Momentum (÷10), and Transferability ((score−1)÷4). Default weight is equal across all three. Weights are configurable via UI sliders.

**Urgency**
Binary classification of each opportunity: `act_now` or `watch`. Set by the LLM during transferability scoring. Used to split the output into two sections.

**Relevance Filter**
Pre-scoring step that removes signals not matching the RetailerContext niche and not originating from a target or comparison market.

**Deduplication**
Pre-scoring step that collapses signals referring to the same opportunity across multiple source types into a single opportunity record, preserving all contributing source types for Breadth counting.
