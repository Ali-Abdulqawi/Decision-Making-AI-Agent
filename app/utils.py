import json
from typing import Any, Dict

def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Robustly extract JSON from model output.
    Strategy:
    1) Try full text as JSON
    2) Find first '{' and last '}' and try that slice
    """
    text = (text or "").strip()

    # 1) direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) slice between first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")

    candidate = text[start:end+1]
    return json.loads(candidate)
