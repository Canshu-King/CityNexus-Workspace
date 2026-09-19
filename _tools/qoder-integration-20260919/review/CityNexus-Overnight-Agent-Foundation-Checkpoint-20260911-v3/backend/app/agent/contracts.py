from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class AgentMode(str, Enum):
    ADVISORY = "ADVISORY"
    ASSISTED = "ASSISTED"
    AUTONOMOUS = "AUTONOMOUS"


class AgentAction(str, Enum):
    INSPECT_JOURNEY = "INSPECT_JOURNEY"
    INSPECT_TWIN = "INSPECT_TWIN"
    LIST_REPLANS = "LIST_REPLANS"
    SEARCH_CITY_SERVICES = "SEARCH_CITY_SERVICES"
    REQUEST_REPLAN = "REQUEST_REPLAN"
    ACCEPT_REPLAN = "ACCEPT_REPLAN"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    MODIFY_C4 = "MODIFY_C4"


class AuthorizationDecision(str, Enum):
    ALLOW_AUTO = "ALLOW_AUTO"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    REQUIRE_STEP_UP = "REQUIRE_STEP_UP"
    DENY = "DENY"


@dataclass(frozen=True)
class DelegationPolicy:
    mode: AgentMode = AgentMode.ADVISORY
    auto_accept_replan: bool = False
    max_auto_replan_cost_delta_minor: int = 0
    allow_auto_when_provider_degraded: bool = False
    allow_auto_on_critical_event: bool = False
    version: int = 1

    def __post_init__(self) -> None:
        if self.max_auto_replan_cost_delta_minor < 0:
            raise ValueError("max_auto_replan_cost_delta_minor cannot be negative")
        if self.version < 1:
            raise ValueError("policy version must be positive")


@dataclass(frozen=True)
class AgentActionRequest:
    request_id: str
    agent_id: str
    action: AgentAction
    journey_id: str | None = None
    arguments: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.request_id or not self.agent_id:
            raise ValueError("agent action requires request_id and agent_id")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))


@dataclass(frozen=True)
class AuthoritativeActionFacts:
    hard_constraints_passed: bool | None = None
    locked_commitments_preserved: bool | None = None
    c4_affected: bool = False
    cost_delta_minor: int = 0
    provider_degraded: bool = False
    event_severity: str | None = None
    proposal_presented: bool = True
    base_plan_current: bool = True
    trigger_actionable: bool = True


@dataclass(frozen=True)
class AuthorizationResult:
    decision: AuthorizationDecision
    reason_codes: tuple[str, ...]
    policy_version: int
