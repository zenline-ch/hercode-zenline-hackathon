import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEFAULT_CONTEXT, useApp } from "@/lib/store";
import type { RetailerContext } from "@/lib/domain";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Scout · Build your retail context" },
      { name: "description", content: "Answer five questions to produce a structured RetailerContext used by every downstream step." },
    ],
  }),
  component: Page,
});

type Step = {
  key: keyof RetailerContext;
  q: string;
  hint: string;
  placeholder: string;
  parse: (v: string) => unknown;
  format: (v: unknown) => string;
};

const STEPS: Step[] = [
  {
    key: "retailerName",
    q: "What's the retailer's name?",
    hint: "Used only as a label in your report.",
    placeholder: "e.g. Bergsteiger AG",
    parse: (v) => v.trim(),
    format: (v) => String(v),
  },
  {
    key: "targetMarket",
    q: "Which market do you sell into?",
    hint: "Every transferability judgement is made relative to this market.",
    placeholder: "e.g. Switzerland",
    parse: (v) => v.trim(),
    format: (v) => String(v),
  },
  {
    key: "comparisonMarkets",
    q: "Which markets do you watch for early signals?",
    hint: "Comma-separated. Signals are scraped from these markets and transferred to your target market.",
    placeholder: "Sweden, Canada",
    parse: (v) => v.split(",").map((s) => s.trim()).filter(Boolean),
    format: (v) => (v as string[]).join(", "),
  },
  {
    key: "niche",
    q: "What category do you operate in?",
    hint: "Used by the relevance filter to discard signals outside your niche keywords.",
    placeholder: "Outdoor & alpine apparel",
    parse: (v) => v.trim(),
    format: (v) => String(v),
  },
  {
    key: "competitorUrls",
    q: "Who are your two main local competitors?",
    hint: "Comma-separated domains. Grounds the Availability Gap sub-score in real assortments.",
    placeholder: "transa.ch, bachercher.ch",
    parse: (v) => v.split(",").map((s) => s.trim().replace(/^https?:\/\//, "")).filter(Boolean),
    format: (v) => (v as string[]).join(", "),
  },
];

type Msg =
  | { role: "agent"; text: string }
  | { role: "user"; text: string }
  | { role: "summary"; ctx: RetailerContext };

function Page() {
  const navigate = useNavigate();
  const setContext = useApp((s) => s.setContext);
  const existing = useApp((s) => s.context);

  const [draft, setDraft] = useState<RetailerContext>(existing ?? DEFAULT_CONTEXT);
  const [stepIdx, setStepIdx] = useState(0);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([
    { role: "agent", text: "Hi — I'll ask five quick questions to build a RetailerContext. Every later step will use exactly what you tell me here, nothing hardcoded." },
    { role: "agent", text: STEPS[0].q },
  ]);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, [stepIdx]);
  useEffect(() => { scrollRef.current?.scrollTo({ top: 1e9, behavior: "smooth" }); }, [messages]);

  const done = stepIdx >= STEPS.length;

  function submit() {
    if (done) return;
    const val = input.trim();
    if (!val) return;
    const step = STEPS[stepIdx];
    const parsed = step.parse(val) as never;
    const next = { ...draft, [step.key]: parsed } as RetailerContext;
    setDraft(next);
    const nextIdx = stepIdx + 1;
    const newMessages: Msg[] = [
      ...messages,
      { role: "user", text: val },
    ];
    if (nextIdx < STEPS.length) {
      newMessages.push({ role: "agent", text: STEPS[nextIdx].q });
    } else {
      newMessages.push({ role: "agent", text: "Locked in. Here's your RetailerContext — it'll be passed verbatim to detection." });
      newMessages.push({ role: "summary", ctx: next });
    }
    setMessages(newMessages);
    setInput("");
    setStepIdx(nextIdx);
  }

  function confirm() {
    setContext(draft);
    navigate({ to: "/scraping" });
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto px-6 py-10">
        <header className="mb-8">
          <p className="chip mb-3">Step 01 · Context</p>
          <h1 className="font-serif text-4xl font-semibold leading-tight">
            Tell me about the shop.
          </h1>
          <p className="mt-2 text-muted-foreground max-w-lg">
            A short, leading Q&A. Your answers become the <code className="font-mono text-[0.85em]">RetailerContext</code> that grounds every later score.
          </p>
        </header>

        <div className="border border-border rounded-lg bg-card overflow-hidden">
          <div ref={scrollRef} className="max-h-[55vh] overflow-y-auto p-6 space-y-4">
            {messages.map((m, i) => {
              if (m.role === "summary") return <ContextCard key={i} ctx={m.ctx} />;
              if (m.role === "agent") {
                const stepHint =
                  i === messages.length - 1 && !done ? STEPS[stepIdx].hint : null;
                return (
                  <div key={i} className="max-w-[85%]">
                    <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                      Scout
                    </p>
                    <p className="text-foreground leading-relaxed">{m.text}</p>
                    {stepHint && (
                      <p className="mt-1.5 text-xs text-muted-foreground italic border-l-2 border-rule pl-2">
                        {stepHint}
                      </p>
                    )}
                  </div>
                );
              }
              return (
                <div key={i} className="max-w-[85%] ml-auto text-right">
                  <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-1">
                    You
                  </p>
                  <p className="inline-block bg-primary text-primary-foreground px-3 py-2 rounded-md text-left">
                    {m.text}
                  </p>
                </div>
              );
            })}
          </div>

          <div className="border-t border-border p-4 bg-card/60">
            {!done ? (
              <form
                onSubmit={(e) => { e.preventDefault(); submit(); }}
                className="flex gap-2"
              >
                <Input
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={STEPS[stepIdx].placeholder}
                  className="font-mono text-sm"
                />
                <Button type="submit" disabled={!input.trim()}>
                  Answer
                </Button>
              </form>
            ) : (
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-muted-foreground">
                  Context ready. Pass it to the detection step?
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => {
                    setStepIdx(0); setMessages([
                      { role: "agent", text: "Start over — first question:" },
                      { role: "agent", text: STEPS[0].q },
                    ]);
                  }}>Restart</Button>
                  <Button onClick={confirm}>Run detection →</Button>
                </div>
              </div>
            )}
          </div>
        </div>

        <p className="text-xs font-mono text-muted-foreground mt-4">
          Why a wizard, not a free-form chat? Each downstream score must trace to a field. Locked questions = traceable inputs.
        </p>
      </div>
    </AppShell>
  );
}

function ContextCard({ ctx }: { ctx: RetailerContext }) {
  const rows: [string, string][] = [
    ["retailerName", ctx.retailerName],
    ["targetMarket", ctx.targetMarket],
    ["comparisonMarkets", ctx.comparisonMarkets.join(", ")],
    ["niche", ctx.niche],
    ["competitorUrls", ctx.competitorUrls.join(", ")],
  ];
  return (
    <div className="border border-border rounded-md bg-background p-4 my-2">
      <p className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-2">
        RetailerContext
      </p>
      <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1 font-mono text-xs">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-muted-foreground">{k}</dt>
            <dd className="text-foreground">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
