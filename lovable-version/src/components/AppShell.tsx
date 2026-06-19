import { Link, Outlet, useLocation } from "@tanstack/react-router";

const steps = [
  { to: "/", label: "01 · Context", short: "Context" },
  { to: "/scraping", label: "02 · Detection", short: "Detection" },
  { to: "/results", label: "03 · Watch / Act", short: "Watch · Act" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const activeIdx = steps.findIndex((s) => s.to === loc.pathname);
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border bg-card/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-6">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="font-serif text-xl font-semibold tracking-tight">Scout</span>
            <span className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
              retail signal log
            </span>
          </Link>
          <nav className="flex items-center gap-1 text-sm">
            {steps.map((s, i) => {
              const active = s.to === loc.pathname;
              const done = activeIdx > i;
              return (
                <Link
                  key={s.to}
                  to={s.to}
                  className={[
                    "px-3 py-1.5 rounded-md font-mono text-xs tracking-wider uppercase transition-colors",
                    active
                      ? "bg-primary text-primary-foreground"
                      : done
                      ? "text-foreground hover:bg-muted"
                      : "text-muted-foreground hover:bg-muted",
                  ].join(" ")}
                >
                  {s.short}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="flex-1">{children ?? <Outlet />}</main>
      <footer className="border-t border-border py-6 mt-12">
        <div className="max-w-6xl mx-auto px-6 text-xs font-mono text-muted-foreground flex justify-between">
          <span>Every score on this page is traceable to a rule or a one-sentence judgement.</span>
          <span>Demo data · ADR 0001 / ADR 0002</span>
        </div>
      </footer>
    </div>
  );
}
