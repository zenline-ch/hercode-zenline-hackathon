# Context

## Glossary

**RetailerContext**
The structured configuration object produced by the Q&A entrypoint. Captures: target market, comparison markets, niche/category, demographic filters (gender, age range), and competitor URLs. All downstream modules receive a `RetailerContext` — nothing is hardcoded to Switzerland or outdoor retail.

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
Count of distinct source types that independently surface the same opportunity. Scale 0–5. Higher = more independent confirmation. Preserved during Deduplication so all contributing source types are counted.

**Trend Score**
Pillar score with a single deterministic sub-dimension: Growth. Normalized 0–1.

**Growth**
Rate of increase of an opportunity's keyword over the last 90 days, measured via Google Trends for the comparison market(s). Normalized 0–10. Slope computed with `numpy.polyfit`. The only sub-dimension of Trend Score.

**Trend Stage**
Classification derived from the Trend Score sub-dimensions: `emerging`, `growing`, `mainstream`, or `declining`. Drives the Buy Recommendation shown in the output.

**Swiss Transferability Score**
Pillar score derived from two LLM-assessed sub-dimensions: Outdoor Relevance and DACH Availability Gap. The LLM receives the signal, the source market → target market pair, and the RetailerContext. Returns a score (1–5) and a one-sentence explanation per sub-dimension.

**Opportunity Score**
Pillar score derived from three LLM-assessed sub-dimensions: Availability Gap, Retail Saturation, and Brand Availability. Grounded in RetailerContext competitor URLs and niche.

**Red-Flag Scoring**
Fourth scoring pillar. LLM-assessed sub-dimensions: Supply Chain Risk, Regulatory Risk, Brand Concentration. Each scored 1–5 where 5 = highest risk. The pillar total is inverted in the Composite Score — high risk lowers the composite. Returns a one-sentence explanation ("Why to be cautious").

**Composite Score**
Weighted average of four normalized pillar totals: `avg(Trend · Transferability · Opportunity · (1 - Red-Flag))`. Red-Flag is inverted so high risk lowers the composite. Default weight is equal across all four pillars. Weights are configurable via UI sliders.

**Urgency**
Binary classification of each opportunity: `act_now` or `watch`. Set by the LLM during transferability scoring. Used to split the output into two sections.

**Relevance Filter**
Pre-scoring step that removes signals not matching the RetailerContext niche and not originating from a target or comparison market.

**Deduplication**
Pre-scoring step that collapses signals referring to the same opportunity across multiple source types into a single opportunity record, preserving all contributing source types for Breadth counting.
