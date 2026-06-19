"""CLI entrypoint — run the pipeline without Streamlit.

Usage:
  poetry run python -m zenline_radar.cli --api-key sk-ant-...
  ANTHROPIC_API_KEY=... poetry run python -m zenline_radar.cli
"""

import argparse
import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from .context import DEMO_CONTEXT
from .scraper import collect_signals
from .filter import run_filter_pipeline
from .scorer import score_opportunities


def main():
    parser = argparse.ArgumentParser(description="Zenline Retail Radar CLI")
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"), help="Anthropic API key")
    parser.add_argument("--google-trends", action="store_true", help="Enable live Google Trends scraping")
    parser.add_argument("--amazon", action="store_true", help="Enable live Amazon scraping")
    parser.add_argument("--output", default="results.json", help="Output file path")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of opportunities to score (0 = all)")
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: Anthropic API key required. Set ANTHROPIC_API_KEY or pass --api-key.", file=sys.stderr)
        sys.exit(1)

    ctx = DEMO_CONTEXT
    print(f"Target market: {ctx.target_market} | Niche: {ctx.niche}")
    print(f"Comparison markets: {ctx.comparison_markets}")
    print(f"Keywords: {len(ctx.category_keywords)}")

    print("\n[1/4] Collecting signals...")
    signals = collect_signals(
        ctx,
        enable_google_trends=args.google_trends,
        enable_amazon=args.amazon,
    )
    print(f"  → {len(signals)} raw signals")

    print("\n[2/4] Filtering and deduplicating...")
    opportunities = run_filter_pipeline(signals, ctx)
    print(f"  → {len(opportunities)} unique opportunities")

    if args.limit and args.limit < len(opportunities):
        opportunities = opportunities[:args.limit]
        print(f"  → limited to {len(opportunities)}")

    print("\n[3/4] Scoring with Claude...")

    def progress(i, total, name):
        print(f"  [{i+1}/{total}] {name}")

    results = score_opportunities(opportunities, ctx, api_key=args.api_key, progress_callback=progress)

    print(f"\n[4/4] Writing {args.output}...")
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n=== Top 5 Opportunities ===")
    for opp in results[:5]:
        print(
            f"#{opp['rank']:2d}  {opp['name']:<30s}  "
            f"composite={opp['composite_score']:.3f}  "
            f"urgency={opp.get('urgency','watch'):<8s}  "
            f"stage={opp.get('trend_stage','')}"
        )


if __name__ == "__main__":
    main()
