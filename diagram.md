# Retail Radar — System Diagrams & Frontend (Lovable) Plan

> Companion to [`ARCHITECTURE.md`](ARCHITECTURE.md). Diagrams reflect the merged pipeline (Giulia's hybrid scoring + `RetailerContext` + the team's assortment-gap/persona/lead-lag work). Mermaid renders directly in GitHub and VS Code.

---

## 1. Full pipeline

```mermaid
flowchart TB
    CTX["RetailerContext\n(Q&A wizard: target market, comparison markets,\nniche, demographics, competitor URLs, persona, weights)"]

    subgraph SOURCES["1. Collect"]
        direction LR
        WS["Web Search"]
        GT["Google Trends\n(pytrends, per geo)"]
        RD["Reddit RSS"]
        MP["Marketplace\n(Galaxus.ch)"]
        CP["Competitor\n(Bächli / Transa)"]
    end

    CTX -.configures.-> SOURCES
    SOURCES --> NORM["2. Normalise\n→ Signal row (data-contract)"]
    NORM --> CLEAN["3. Clean\nvalidate · spam filter ·\nbrand/market canonicalise (keep umlauts)"]
    CLEAN --> DEDUP["4. Deduplicate\nhash(keyword, brand, market)"]
    DEDUP --> SCORE["5. Score — hybrid\nBreadth + Momentum (deterministic)\n+ Transferability (LLM)\n+ Coverage Gap (deterministic)"]

    SCORE --> CLUSTER["Cluster\nsignals → opportunities"]
    CLUSTER --> LEADLAG["Lead-Lag analysis\ngeo timeseries → first-mover market"]
    CLUSTER --> COVER["Coverage check\nBächli/Transa scan → coverage_status"]

    LEADLAG --> SYNTH
    COVER --> SYNTH["6. Synthesise\ncomposite_score · confidence ·\nurgency (act_now/watch, guarded) ·\ntrend_stage · monitor_triggers"]

    CTX -.persona + weights.-> SCORE
    CTX -.persona.-> SYNTH

    SYNTH --> OUT["7. Present"]
    OUT --> CSV["signals.csv"]
    OUT --> JSON["recommendations.json\n(per-opportunity contract)"]
    OUT --> API["API / static JSON endpoint"]
    API --> FE["Lovable frontend"]

    style CTX fill:#fff3e0
    style SOURCES fill:#e8f0e8
    style SCORE fill:#e3f2fd
    style COVER fill:#c8e6c9
    style FE fill:#f3e5f5
```

---

## 2. Hybrid scoring detail (ADR 0001)

```mermaid
flowchart LR
    subgraph DET["Deterministic — no API key, fully rerunnable"]
        B["Breadth\nsource-type count, 0-5"]
        M["Momentum\nGoogle Trends slope\n(numpy.polyfit), 0-10"]
        CG["Coverage Gap\nabsent=1.0 / partial=0.5 / covered=0.1"]
    end
    subgraph LLM["LLM — judgment required"]
        T["Transferability\nscore 1-5 + reason + urgency\ngrounded in RetailerContext"]
    end
    DET --> COMP["composite_score\nweighted avg, default 0.25 each"]
    LLM --> COMP
    COMP --> CONF["confidence label\nhigh ≥0.70 / medium ≥0.45 / low below"]
    CONF -->|"low forces"| GUARD["urgency guard\nlow confidence → urgency=watch\n(LLM cannot override)"]

    style DET fill:#e8f5e9
    style LLM fill:#fce4ec
    style GUARD fill:#fff3e0
```

---

## 3. Core differentiator — the assortment gap

```mermaid
flowchart LR
    A["Global momentum\n(comparison markets: US/Nordics/Japan...)"] --> C{"Cross-reference"}
    B["Swiss shelf scan\n(Bächli/Transa)"] --> C
    C -->|"rising + absent"| D["coverage_status: absent\n= highest-scoring opportunity"]
    C -->|"rising + already stocked"| E["coverage_status: covered\n= already too late"]
    C -->|"buzz, zero SKUs"| F["coverage_status: not_relevant\nconfidence: low → watch only"]

    style D fill:#c8e6c9
    style E fill:#ffe0b2
    style F fill:#ffcdd2
```

---

## 4. Deduplication logic

```mermaid
flowchart TB
    S1["Signal: Reddit / 'gravel running' / Norda / US"]
    S2["Signal: Web search / 'gravel running' / Norda / US"]
    S3["Signal: Google Trends / 'gravel running' / Norda / CH"]

    S1 --> K1["key: (gravel running, norda, US)"]
    S2 --> K1
    K1 --> MERGED["1 row kept, URLs merged into notes"]

    S3 --> K2["key: (gravel running, norda, CH)\n— different market, kept SEPARATE"]
    K2 --> SEPARATE["Preserved as distinct evidence\n→ feeds Lead-Lag analysis"]

    style MERGED fill:#c8e6c9
    style SEPARATE fill:#e3f2fd
```

---

## 5. Confidence → inventory action

```mermaid
flowchart TB
    S["composite_score + trend_stage"] --> H["High + emerging\ncommercial proof + absent"]
    S --> M["Medium\nearly signal"]
    S --> L["Low\ndirectional only"]

    H --> H2["Test capsule\n2-3 SKUs, small qty, fast re-order"]
    M --> M2["Small curated test\nlowest-MOQ SKU first"]
    L --> L2["Zero stock\nwatch, re-evaluate later"]

    H2 --> GATE["Sell-through gate\n<30% in 4 weeks → stop re-order\nmonitor_triggers checked weekly"]
    M2 --> GATE

    style H fill:#c8e6c9
    style M fill:#fff9c4
    style L fill:#ffcdd2
    style GATE fill:#e1f5fe
```

---

## 6. Frontend plan — building it with Lovable

**Goal:** Lovable owns the UI; it talks to the Python pipeline's output, not a reimplementation of the scoring logic. Keep the contract dumb and stable: the frontend renders the Opportunity JSON from `ARCHITECTURE.md` §10, nothing more.

### 6.1 Data flow (what Lovable actually fetches)

```mermaid
flowchart LR
    PY["Python pipeline\n(Poetry project)"] -->|"writes"| ART["recommendations.json\nsignals.csv"]
    ART --> SERVE{"How it's served\nduring the hackathon"}
    SERVE -->|"fastest, lowest risk"| STATIC["Static JSON file\ncommitted to repo / hosted on Vercel"]
    SERVE -->|"if time allows"| API["Tiny FastAPI endpoint\nGET /api/opportunities\nPOST /api/context → reruns pipeline"]
    STATIC --> FE["Lovable frontend\nfetch() on load"]
    API --> FE
    SERVE -->|"stretch goal"| SUPA["Supabase tables\nretailer_context, opportunities\n(Lovable's native backend)"]
    SUPA --> FE
```

**Recommendation for hackathon time pressure:** ship the **static JSON** path first. Re-run the pipeline whenever the data changes, commit the new `recommendations.json`, and have Lovable fetch it from a fixed URL (e.g. raw file hosted alongside the deployed frontend, or a one-route Vercel function that just returns the file). This has zero backend-uptime risk during the live demo. Only reach for the FastAPI endpoint or Supabase tables if there's slack time left — they make the `RetailerContext` Q&A wizard *actually* trigger a rerun instead of switching between two pre-computed JSON files.

**Cheap trick that still proves reusability live:** pre-compute two `recommendations.json` files (e.g. `outdoor_large_retailer.json` and `cycling_boutique.json`). The Q&A wizard's "submit" button just swaps which file the dashboard fetches. The audience sees the full ranking change live; you don't need a real-time rerun to make the point.

### 6.2 Screens to build in Lovable

1. **Landing / pitch screen** — USP one-liner, "Act Now" vs "Watch" opportunity count as a hook, a "Run the demo" CTA.
2. **`RetailerContext` Q&A wizard** — short form: target market, comparison markets (multi-select), niche/category, persona (radio: large retailer / boutique / individual DTC), competitor URLs, scoring weight sliders (4 sliders summing to 1.0, default 0.25 each). On submit: swap data source per §6.1.
3. **Opportunity dashboard** — two columns/sections, `act_now` and `watch`, cards sorted by `composite_score` descending. Each card: name, `composite_score`, `confidence` badge, `coverage_status` badge, `buy_recommendation`.
4. **Opportunity detail view** (click a card) — `explainability` block (`why_trending`, `why_fits_switzerland`, `why_opportunity_now`), the 4 score sub-totals as a small bar chart, `signals[]` list with clickable `url`s, `risk_flags` as warning chips, `monitor_triggers` / `reversal_signals` / `expected_window` as a "when to stop" panel.
5. **Evidence export** — buttons to download `signals.csv` and `recommendations.json` directly (judges explicitly want inspectable artifacts).
6. **Reusability toggle** — a visible switch/button that swaps category or persona and re-renders the dashboard live, labelled something like "See it work for cycling" — this *is* the reusability proof, make it impossible to miss.

### 6.3 Build order (if time is tight, in this order)

1. Opportunity dashboard reading static JSON (the demo cannot exist without this).
2. Opportunity detail view (this is where "evidence quality" and "business actionability" get judged up close).
3. Reusability toggle (cheap to build if using the pre-computed-file trick in §6.1; high pitch value).
4. `RetailerContext` Q&A wizard UI (can be a thin form even if it just swaps the pre-computed file rather than triggering a real rerun).
5. CSV/JSON export buttons (trivial, but a named rubric item — don't skip it).
6. Stretch: real FastAPI rerun or Supabase persistence of `RetailerContext` answers.

### 6.4 What NOT to build in Lovable

- Don't reimplement scoring, cleaning, or dedup logic in the frontend — it must stay backend-owned so the "auditable, rerunnable" claim in `ARCHITECTURE.md` §6 stays true.
- Don't wire real-time `pytrends` calls into the frontend — it rate-limits and will break live in front of the jury. The frontend only ever reads already-computed JSON.
