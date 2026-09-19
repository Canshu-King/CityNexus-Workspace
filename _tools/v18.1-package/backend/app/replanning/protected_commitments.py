from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


def active_c4_hard_constraints(commitments: Iterable[Any]) -> list[dict[str, Any]]:
    """Translate durable C4 Commitment facts into feasibility hard constraints.

    Commitment.activity_id belongs to a particular PlanVersion and therefore is
    not a stable cross-version identity.  The WP04 policy stores the stable
    semantic key and scheduled start; those facts are the authoritative anchor
    used for replanning.
    """

    constraints: list[dict[str, Any]] = []
    for item in commitments:
        if str(getattr(item, "status", "")) != "ACTIVE":
            continue
        if str(getattr(item, "level", "")) != "C4_Anchored":
            continue
        raw = getattr(item, "policy_json", "{}") or "{}"
        try:
            policy = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("C4 commitment policy is invalid JSON") from exc
        semantic_key = policy.get("semantic_key")
        scheduled_start = policy.get("scheduled_start_at")
        if not semantic_key or not scheduled_start:
            raise ValueError("C4 commitment lacks stable semantic/time anchor")
        constraints.append(
            {
                "kind": "HARD",
                "category": "commitment",
                "rule_code": "LOCKED_COMMITMENT",
                "params": {
                    "semantic_ref": str(semantic_key),
                    "start_at": str(scheduled_start),
                    "time_boundary": (
                        "END"
                        if str(policy.get("anchor_role") or "").upper() == "DEPARTURE"
                        else "START"
                    ),
                },
                "active": True,
            }
        )
    return constraints
