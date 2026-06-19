"""Pipeline orchestrator (diagram.md §1): collect -> clean -> deduplicate ->
score+synthesise -> present. This is the one function the Streamlit app
(and later, the Lovable frontend's backend calls) needs to know about."""
import csv
import json
from dataclasses import asdict
from pathlib import Path

from retail_radar.pipeline import collectors, cleaner, dedup, synthesiser
from retail_radar.schema import RetailerContext

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SIGNALS_CSV_PATH = DATA_DIR / "signals.csv"
RECOMMENDATIONS_JSON_PATH = DATA_DIR / "recommendations.json"

CSV_FIELDS = [
    "source", "market", "keyword", "signal_name", "signal_type", "product_name", "brand",
    "price", "rank", "url", "signal_score", "confidence", "notes", "observed_at",
    "artifact_type", "artifact_uri", "created_by_tool",
]


def build_recommendations(context: RetailerContext, write_artifacts: bool = True) -> dict:
    raw_signals = collectors.collect(context)
    cleaned, clean_log = cleaner.clean(raw_signals)
    deduped, dedup_log = dedup.deduplicate(cleaned)
    opportunities = synthesiser.synthesise(deduped, context)

    pipeline_log = {
        "ingested": clean_log["ingested"],
        "cleaned": clean_log["cleaned"],
        "deduped": dedup_log["after"],
        "opportunities": len(opportunities),
        "narration": (
            f"Ingested {clean_log['ingested']} raw signals -> cleaned to {clean_log['cleaned']} "
            f"-> deduped to {dedup_log['after']} -> clustered into {len(opportunities)} opportunities."
        ),
    }

    if write_artifacts:
        _write_signals_csv(deduped)
        _write_recommendations_json(opportunities, context, pipeline_log)

    return {"opportunities": opportunities, "log": pipeline_log, "context": asdict(context)}


def _write_signals_csv(signals) -> None:
    with open(SIGNALS_CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for s in signals:
            row = asdict(s)
            row["signal_type"] = row.pop("source_type")
            del row["opportunity_id"]
            del row["opportunity_name"]
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})


def _write_recommendations_json(opportunities, context: RetailerContext, log: dict) -> None:
    payload = {"context": asdict(context), "log": log, "opportunities": opportunities}
    RECOMMENDATIONS_JSON_PATH.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    result = build_recommendations(RetailerContext())
    print(result["log"]["narration"])
    for opp in result["opportunities"]:
        print(f"- {opp['name']}: composite={opp['composite_score']} confidence={opp['confidence']} "
              f"coverage={opp['coverage_status']} urgency={opp['urgency']} -> {opp['buy_recommendation']}")
