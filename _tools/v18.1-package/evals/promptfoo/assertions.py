from __future__ import annotations

import json
from typing import Any


def check(output: str, context: dict[str, Any]) -> dict[str, Any]:
    expected = context.get("vars", {})
    try:
        payload = json.loads(output)
    except (TypeError, json.JSONDecodeError):
        return {"pass": False, "score": 0, "reason": "provider output was not JSON"}
    decision_ok = payload.get("decision") == expected.get("expected_decision")
    reason_ok = expected.get("expected_reason") in payload.get("reason_codes", [])
    return {
        "pass": bool(decision_ok and reason_ok),
        "score": 1 if decision_ok and reason_ok else 0,
        "reason": f"decision={payload.get('decision')} reason_codes={payload.get('reason_codes')}",
    }
