import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useApp } from "@/lib/store";
import {
  OPPORTUNITIES,
  compositeScore,
  urgency,
  type Opportunity,
  type PillarScore,
} from "@/lib/domain";

export const Route = createFileRoute("/results")({
  head: () => ({
    meta: [
      { title: "Scout · Watch & Act" },
      { name: "description", content: "Opportunities ranked by composite score. Every pillar score is traceable to a rule or one-sentence judgement." },
    ],
  }),
  component: Page,
});

function Page() {
  const ctx = useApp((s) => s.context);
  const setContext = useApp((s) => s.setContext);
  const [openId, setOpenId] = useState<string | null>(null);

  const weights = ctx?.weights ?? { trend: 1, transfer: 1, opportunity: 1, redflag: 1 };

  const scored = useMemo(() => {
    return OPPORTUNITIES
      .map((o) => ({ o, composite: compositeScore(o, weights), urgency: urgency(o, weights) }))
      .sort((a, b) => b.composite - a.composite);
  }, [weights]);

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

  const act = scored.filter((x) => x.urgency === "act_now");
  const watch = scored.filter((x) => x.urgency === "watch");

  function setWeight(k: keyof typeof weights, v: number) {
    setContext({ ...ctx!, weights: { ...weights, [k]: v } });
  }

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-6 py-10">
        <header className="mb-8">
          <p className="chip mb-3">Step 03 · Watch / Act</p>
          <h1 className="font-serif text-4xl font-semibold leading-tight">
            Six opportunities, fully shown work.
          </h1>
          <p className="mt-2 text-muted-foreground max-w-2xl">
            Composite score is a weighted average of four pillars. Click any card to open the breakdown — every sub-score has a one-sentence justification.
          </p>
        </header>

        <div className="grid lg:grid-cols-[1fr_280px] gap-8 items-start">
          <div className="space-y-10">
            <Section
              title="Act now"
              subtitle={`Composite ≥ 0.65 and trend is growing or emerging — window is open.`}
              tone="act"
              items={act}
              openId={openId}
              setOpenId={setOpenId}
            />
            <Section
              title="Watch"
              subtitle="Signal present but composite or trend stage doesn't justify action this cycle."
              tone="watch"
              items={watch}
              openId={openId}
              setOpenId={setOpenId}
            />
          </div>

          <aside className="lg:sticky lg:top-24 space-y-4 self-start">
            <div className="border border-border rounded-lg bg-card p-4">
              <h3 className="font-serif text-base mb-1">Pillar weights</h3>
              <p className="text-xs text-muted-foreground mb-3">
                Composite ={" "}
                <code className="font-mono text-[0.85em]">
                  Σ(wᵢ·pᵢ) / Σwᵢ
                </code>
                . Red-flag is inverted: <code className="font-mono text-[0.85em]">(1 − rf)</code>.
              </p>
              <WeightSlider label="Trend" value={weights.trend} onChange={(v) => setWeight("trend", v)} />
              <WeightSlider label="Transfer" value={weights.transfer} onChange={(v) => setWeight("transfer", v)} />
              <WeightSlider label="Opportunity" value={weights.opportunity} onChange={(v) => setWeight("opportunity", v)} />
              <WeightSlider label="Red-flag" value={weights.redflag} onChange={(v) => setWeight("redflag", v)} />
            </div>
            <div className="border border-border rounded-lg bg-card p-4">
              <h3 className="font-serif text-base mb-2">Reading the score</h3>
              <ul className="text-xs space-y-1.5 text-muted-foreground">
                <li><span className="font-mono">7.5+</span> growing — buy window open</li>
                <li><span className="font-mono">5.0+</span> emerging — early but real</li>
                <li><span className="font-mono">2.5+</span> mainstream — late mover</li>
                <li><span className="font-mono">&lt;2.5</span> declining — pass</li>
              </ul>
            </div>
            <Link to="/" className="block text-xs font-mono text-muted-foreground hover:text-foreground underline">
              ← edit context
            </Link>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

function WeightSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="mb-3 last:mb-0">
      <div className="flex justify-between items-baseline text-xs font-mono mb-1">
        <span>{label}</span>
        <span className="text-muted-foreground tabular-nums">{value.toFixed(1)}</span>
      </div>
      <Slider value={[value]} min={0} max={2} step={0.1} onValueChange={([v]) => onChange(v)} />
    </div>
  );
}

type Scored = { o: Opportunity; composite: number; urgency: "act_now" | "watch" };

function Section({
  title, subtitle, tone, items, openId, setOpenId,
}: {
  title: string;
  subtitle: string;
  tone: "act" | "watch";
  items: Scored[];
  openId: string | null;
  setOpenId: (id: string | null) => void;
}) {
  return (
    <section>
      <div className="flex items-baseline gap-3 mb-1">
        <h2 className="font-serif text-2xl">{title}</h2>
        <span
          className="font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded"
          style={{
            background: tone === "act" ? "var(--color-act)" : "var(--color-watch)",
            color: tone === "act" ? "var(--color-act-foreground)" : "var(--color-watch-foreground)",
          }}
        >
          {items.length}
        </span>
      </div>
      <p className="text-sm text-muted-foreground mb-4">{subtitle}</p>
      <ul className="space-y-3">
        {items.map(({ o, composite }) => (
          <OpportunityCard
            key={o.id}
            o={o}
            composite={composite}
            tone={tone}
            open={openId === o.id}
            onToggle={() => setOpenId(openId === o.id ? null : o.id)}
          />
        ))}
        {items.length === 0 && (
          <li className="text-sm text-muted-foreground italic">None at current weights.</li>
        )}
      </ul>
    </section>
  );
}

function OpportunityCard({
  o, composite, tone, open, onToggle,
}: { o: Opportunity; composite: number; tone: "act" | "watch"; open: boolean; onToggle: () => void }) {
  return (
    <li className="border border-border rounded-lg bg-card overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full text-left p-5 flex items-start gap-5 hover:bg-muted/40 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 mb-1">
            <h3 className="font-serif text-xl">{o.name}</h3>
            <span className="chip">{o.trendStage}</span>
          </div>
          <p className="text-sm text-muted-foreground truncate">{o.brand} · {o.niche}</p>
          <div className="mt-3 grid grid-cols-4 gap-3 max-w-md">
            <PillarMini label="Trend" v={o.trend.total} />
            <PillarMini label="Transfer" v={o.transfer.total} />
            <PillarMini label="Oppty" v={o.opportunity.total} />
            <PillarMini label="Red-flag" v={o.redflag.total} invert />
          </div>
        </div>
        <div className="text-right">
          <p
            className="font-serif text-5xl tabular-nums leading-none"
            style={{ color: tone === "act" ? "var(--color-act)" : "var(--color-watch-foreground)" }}
          >
            {composite.toFixed(2)}
          </p>
          <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mt-1">
            composite
          </p>
          <p className="text-xs font-mono mt-3 text-muted-foreground">
            {open ? "− hide" : "+ explain"}
          </p>
        </div>
      </button>

      {open && (
        <div className="border-t border-border p-5 bg-background/60 space-y-6">
          <div className="grid md:grid-cols-2 gap-x-8 gap-y-3">
            <Judgement label="Why trending" text={o.explain.why_trending} />
            <Judgement label="Why it fits the target market" text={o.explain.why_fits_target} />
            <Judgement label="Why act now" text={o.explain.why_opportunity_now} />
            <Judgement label="Why to be cautious" text={o.explain.why_to_be_cautious} />
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <PillarBreakdown label="Trend" pillar={o.trend} note="Deterministic — Google Trends slope, normalized 0–1." />
            <PillarBreakdown
              label="Transferability"
              pillar={o.transfer}
              note="LLM, scored 1–5 per sub-dimension."
              caveat={o.transferCaveat}
            />
            <PillarBreakdown label="Opportunity" pillar={o.opportunity} note="LLM, grounded in your competitor URLs." />
            <PillarBreakdown label="Red-flag" pillar={o.redflag} note="LLM, 5 = highest risk. Inverted in composite." invert />
          </div>
        </div>
      )}
    </li>
  );
}

function PillarMini({ label, v, invert }: { label: string; v: number; invert?: boolean }) {
  const display = invert ? 1 - v : v;
  return (
    <div>
      <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">{label}</p>
      <div className="mt-1 h-1.5 bg-muted rounded overflow-hidden">
        <div
          className="h-full"
          style={{
            width: `${Math.max(0, Math.min(1, display)) * 100}%`,
            background: invert
              ? `color-mix(in oklch, var(--color-risk) ${v * 100}%, var(--color-act))`
              : "var(--color-act)",
          }}
        />
      </div>
      <p className="text-xs font-mono tabular-nums mt-1">{display.toFixed(2)}</p>
    </div>
  );
}

function PillarBreakdown({
  label, pillar, note, invert, caveat,
}: { label: string; pillar: PillarScore; note: string; invert?: boolean; caveat?: { confidence: "high" | "medium" | "low"; reason: string } }) {
  const confColor =
    caveat?.confidence === "high" ? "var(--color-act)"
    : caveat?.confidence === "medium" ? "var(--color-watch-foreground)"
    : "var(--color-risk)";
  return (
    <div className="border border-border rounded-md p-3 bg-card">
      <div className="flex items-baseline justify-between mb-1">
        <h4 className="font-serif text-base">{label}</h4>
        <span className="font-mono text-xs tabular-nums">
          {(invert ? 1 - pillar.total : pillar.total).toFixed(2)}
        </span>
      </div>
      <p className="text-[11px] text-muted-foreground italic mb-3">{note}</p>
      {caveat && (
        <div className="mb-3 -mx-1 px-2 py-2 rounded border border-dashed" style={{ borderColor: confColor }}>
          <p className="text-[10px] font-mono uppercase tracking-widest mb-0.5" style={{ color: confColor }}>
            transfer confidence · {caveat.confidence}
          </p>
          <p className="text-[11px] leading-snug">{caveat.reason}</p>
          <p className="text-[10px] text-muted-foreground mt-1 italic">
            A signal in a comparison market is not a guarantee for the target market. Treat this pillar as a hypothesis, not a verdict.
          </p>
        </div>
      )}
      <ul className="space-y-2">
        {Object.entries(pillar.subs).map(([k, s]) => (
          <li key={k}>
            <div className="flex justify-between text-xs">
              <span className="font-medium">{k}</span>
              <span className="font-mono tabular-nums">{s.score}/{s.max}</span>
            </div>
            <p className="text-xs text-muted-foreground leading-snug mt-0.5">{s.why}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Judgement({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mb-0.5">
        {label}
      </p>
      <p className="text-sm leading-relaxed border-l-2 border-rule pl-3">{text}</p>
    </div>
  );
}

// Re-export Button to silence unused import if needed in future
void Button;
