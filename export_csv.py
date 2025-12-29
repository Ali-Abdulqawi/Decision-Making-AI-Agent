import json
import csv
from pathlib import Path

INPUT_PATH = Path("memory/decisions.jsonl")
OUTPUT_PATH = Path("memory/decisions_export.csv")

def safe_get(d, path, default=""):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur

def main():
    if not INPUT_PATH.exists():
        print(f"❌ Not found: {INPUT_PATH}")
        return

    rows = []
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)

            opp = r.get("opportunity", {})
            res = r.get("result", {})  # ✅ your file uses "result"

            row = {
                "timestamp": r.get("timestamp", ""),
                "opportunity_title": opp.get("opportunity_title", ""),
                "client_type": opp.get("client_type", ""),
                "client_level": opp.get("client_level", ""),
                "expected_time_days": opp.get("expected_time_days", ""),
                "cost_to_fulfill": opp.get("cost_to_fulfill", ""),
                "expected_earnings": opp.get("expected_earnings", ""),

                # ✅ FIX: pull from result.*
                "decision": res.get("decision", ""),
                "confidence": res.get("confidence", ""),
                "total_score": safe_get(res, ["score", "total_score"], ""),
                "summary": res.get("summary", ""),
            }
            rows.append(row)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "opportunity_title",
        "client_type",
        "client_level",
        "expected_time_days",
        "cost_to_fulfill",
        "expected_earnings",
        "decision",
        "confidence",
        "total_score",
        "summary",
    ]

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Exported {len(rows)} rows to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

