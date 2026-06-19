import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { useApp } from "@/lib/store";
import { RAW_DATA, THRESHOLDS, detect, type Signal } from "@/lib/domain";

export const Route = createFileRoute("/scraping")({
  head: () => ({
    meta: [
      { title: "Scout · Detection run" },
      { name: "description", content: "Threshold-based signal detection — every emitted signal is annotated with the rule that triggered it." },
    ],
  }),
  component: Page,
});

function Page() {
  const ctx = useApp((s) => s.context);
  const navigate = useNavigate();
  const [tick, setTick] = useState(0);
  const [running, setRunning] = useState(true);

  // Animate signals appearing one by one
  useEffect(() => {
    if (!running) return;
    if (tick >= RAW_DATA.length) { setRunning(false); return; }
    const t = setTimeout(() => setTick((x) => x + 1), 280);
    return () => clearTimeout(t);
  }, [tick, running]);

  if (!ctx) {
    return (
      <AppShell>
        <div className="max-w-2xl mx-auto px-6 py-16 text-center">
          <p className="text-muted-foreground">No context yet.</p>
          <Link to="/" className="text-primary underline">Build your context first →</Link>
        </div>
      </AppShell>
    );
  }

  const signals: Signal[] = RAW_DATA.slice(0, tick).map(detect);
  const emitted = signals.filter((s) => s.emitted).length;
  const discarded = signals.length - emitted;

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-6 py-10">
        <header className="mb-8">
          <p className="chip mb-3">Step 02 · Detection</p>
          <h1 className="font-serif text-4xl font-semibold leading-tight">
            Scraping, with the rulebook open.
          </h1>
          <p className="mt-2 text-muted-foreground max-w-2xl">
            Each source applies one threshold. A data point only becomes a signal if it passes. Below-threshold points are shown anyway so you can audit what was discarded.
          </p>
        </header>

        <div className="grid lg:grid-cols-[1fr_320px] gap-8">
          {/* Signal log */}
          <section>
            <div className="flex items-baseline justify-between mb-3">
              <h2 className="font-serif text-xl">Signal log</h2>
              <div className="font-mono text-xs text-muted-foreground">
                {signals.length}/{RAW_DATA.length} processed · {emitted} emitted · {discarded} discarded
              </div>
            </div>

            <ol className="space-y-2">
              {signals.map((s, i) => (
                <li
                  key={i}
                  className={[
                    "border rounded-md p-3 grid grid-cols-[max-content_1fr_max-content] gap-x-4 items-start animate-in fade-in slide-in-from-bottom-1 duration-300",
                    s.emitted
                      ? "border-border bg-card"
                      : "border-dashed border-rule bg-transparent opacity-60",
                  ].join(" ")}
                >
                  <span className="chip" style={{
                    color: s.emitted ? "var(--color-act)" : "var(--color-ink-muted)",
                    borderColor: s.emitted ? "var(--color-act)" : undefined,
                  }}>
                    {s.source === "search" ? "google trends" : s.source}
                  </span>
                  <div>
                    <p className="font-medium">
                      <span className="font-mono text-xs text-muted-foreground mr-2">{s.market}</span>
                      {s.keyword}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5 font-mono">
                      {s.ruleDetail}
                    </p>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[11px] font-mono text-muted-foreground underline underline-offset-2 hover:text-foreground block mt-1"
                    >
                      primary · {s.url.replace(/^https?:\/\//, "").slice(0, 70)}
                    </a>
                    {s.related && (
                      <div className="mt-2 pl-3 border-l-2 border-rule">
                        <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
                          related source {s.source === "search" ? "(corroborates the slope)" : ""}
                        </p>
                        <a
                          href={s.related.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs font-medium underline underline-offset-2 hover:text-foreground"
                        >
                          {s.related.label}
                        </a>
                        <p className="text-[11px] text-muted-foreground leading-snug mt-0.5">
                          {s.related.note}
                        </p>
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="font-serif text-2xl tabular-nums">
                      {s.score.toFixed(1)}
                    </p>
                    <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                      {s.emitted ? "emitted" : "discarded"}
                    </p>
                  </div>
                </li>
              ))}
            </ol>

            {!running && (
              <div className="mt-6 flex items-center justify-between gap-3 border-t border-border pt-6">
                <p className="text-sm text-muted-foreground">
                  Detection complete. {emitted} signals will be deduplicated into opportunities and scored.
                </p>
                <Button onClick={() => navigate({ to: "/results" })}>
                  Score opportunities →
                </Button>
              </div>
            )}
          </section>

          {/* Rules panel */}
          <aside className="space-y-4 lg:sticky lg:top-24 self-start">
            <div className="border border-border rounded-lg bg-card p-4">
              <h3 className="font-serif text-base mb-3">Active thresholds</h3>
              <RuleRow
                source="google trends"
                rule="90-day slope × 10"
                threshold={`≥ ${THRESHOLDS.SEARCH_MIN_SCORE}`}
                note="De-seasonalised with numpy.polyfit. Every emitted slope ships with a corroborating editorial or retailer source so the number is auditable, not just a line on a chart."
              />
              <RuleRow
                source="marketplace"
                rule="Amazon top-50 matches"
                threshold={`≥ ${THRESHOLDS.MARKETPLACE_MIN_MATCHES}`}
                note="Score = matches × 2.5."
              />
              <RuleRow
                source="manual"
                rule="Curated by analyst"
                threshold="always"
                note="Pre-vetted; expert-assigned 0–10."
              />
              <p className="text-[11px] font-mono text-muted-foreground mt-3 pt-3 border-t border-rule">
                Thresholds are exported constants in <code>scraper.py</code>. Change one number, change every detection.
              </p>
            </div>

            <div className="border border-border rounded-lg bg-card p-4">
              <h3 className="font-serif text-base mb-2">Context filter</h3>
              <p className="text-xs text-muted-foreground mb-2">
                Signals are kept only if they originate from a known market and match niche keywords.
              </p>
              <dl className="font-mono text-xs space-y-0.5">
                <div className="flex justify-between"><dt className="text-muted-foreground">target</dt><dd>{ctx.targetMarket}</dd></div>
                <div className="flex justify-between"><dt className="text-muted-foreground">comparison</dt><dd>{ctx.comparisonMarkets.join(", ")}</dd></div>
                <div className="flex justify-between"><dt className="text-muted-foreground">niche</dt><dd className="text-right">{ctx.niche}</dd></div>
              </dl>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

function RuleRow({ source, rule, threshold, note }: { source: string; rule: string; threshold: string; note: string }) {
  return (
    <div className="py-2 border-b border-rule last:border-0">
      <div className="flex items-baseline justify-between gap-2">
        <span className="chip">{source}</span>
        <span className="font-mono text-xs">{threshold}</span>
      </div>
      <p className="text-sm mt-1 font-medium">{rule}</p>
      <p className="text-xs text-muted-foreground">{note}</p>
    </div>
  );
}
