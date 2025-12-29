import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

MEMORY_PATH = os.getenv("MEMORY_PATH", "memory/decisions.jsonl")


def append_memory(record: Dict[str, Any]) -> None:
    """
    Appends one JSON record per line to MEMORY_PATH.
    Safe for MVP; simple log-based memory.
    """
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)

    with open(MEMORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_record(opportunity: Any, decision_output: Any) -> Dict[str, Any]:
    return {
        "timestamp": now_iso(),
        "opportunity": opportunity.model_dump(),
        "result": decision_output.model_dump(),
    }

