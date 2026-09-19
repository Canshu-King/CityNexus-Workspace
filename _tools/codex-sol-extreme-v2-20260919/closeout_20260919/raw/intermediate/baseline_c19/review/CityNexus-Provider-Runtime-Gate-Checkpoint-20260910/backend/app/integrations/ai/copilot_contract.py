from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class VerifiedCopilotContext:
    journey_id: str
    journey_status: str
    reason_codes: tuple[str, ...]
    evidence: Mapping[str, Any]
    allowed_read_tools: tuple[str, ...] = (
        "get_journey",
        "get_journey_twin",
        "list_replans",
        "search_places",
    )

    def prompt_payload(self) -> dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "journey_status": self.journey_status,
            "reason_codes": list(self.reason_codes),
            "evidence": dict(self.evidence),
            "allowed_read_tools": list(self.allowed_read_tools),
            "mutation_policy": "NO_DIRECT_STATE_MUTATION",
        }


@dataclass(frozen=True)
class CopilotSuggestion:
    text: str
    provider_key: str
    degraded: bool
    proposed_action: str | None = None


def validate_proposed_action(action: str | None) -> str | None:
    """Allow only explicit request-style actions; never direct domain mutation."""

    if action is None:
        return None
    allowed = {
        "REQUEST_REPLAN",
        "REQUEST_PREFERENCE_UPDATE",
        "REQUEST_PLAN_EXPLANATION",
        "REQUEST_PLACE_SEARCH",
    }
    if action not in allowed:
        raise ValueError(f"unsupported copilot action: {action}")
    return action
