from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent.contracts import (
    AgentAction,
    AgentMode,
    AuthoritativeActionFacts,
    AuthorizationDecision,
    AuthorizationResult,
    DelegationPolicy,
)
from app.db.models import TravelerAgentPolicy

READ_ACTIONS = frozenset(
    {
        AgentAction.INSPECT_JOURNEY,
        AgentAction.INSPECT_TWIN,
        AgentAction.LIST_REPLANS,
        AgentAction.SEARCH_CITY_SERVICES,
    }
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def policy_from_model(row: TravelerAgentPolicy) -> DelegationPolicy:
    return DelegationPolicy(
        mode=AgentMode(str(row.mode)),
        auto_accept_replan=bool(row.auto_accept_replan),
        max_auto_replan_cost_delta_minor=int(row.max_auto_replan_cost_delta_minor),
        allow_auto_when_provider_degraded=bool(row.allow_auto_when_provider_degraded),
        allow_auto_on_critical_event=bool(row.allow_auto_on_critical_event),
        version=int(row.version),
    )


def policy_payload(row: TravelerAgentPolicy) -> dict[str, Any]:
    policy = policy_from_model(row)
    return {
        "traveler_id": row.traveler_id,
        "mode": policy.mode.value,
        "auto_accept_replan": policy.auto_accept_replan,
        "max_auto_replan_cost_delta_minor": policy.max_auto_replan_cost_delta_minor,
        "allow_auto_when_provider_degraded": policy.allow_auto_when_provider_degraded,
        "allow_auto_on_critical_event": policy.allow_auto_on_critical_event,
        "version": policy.version,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def get_or_create_policy(session: Session, traveler_id: str) -> TravelerAgentPolicy:
    row = session.get(TravelerAgentPolicy, str(traveler_id))
    if row is not None:
        return row
    now = _now()
    row = TravelerAgentPolicy(
        traveler_id=str(traveler_id),
        mode=AgentMode.ADVISORY.value,
        auto_accept_replan=False,
        max_auto_replan_cost_delta_minor=0,
        allow_auto_when_provider_degraded=False,
        allow_auto_on_critical_event=False,
        version=1,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    return row


def update_policy(
    session: Session,
    traveler_id: str,
    *,
    mode: AgentMode,
    auto_accept_replan: bool,
    max_auto_replan_cost_delta_minor: int,
    allow_auto_when_provider_degraded: bool,
    allow_auto_on_critical_event: bool,
) -> TravelerAgentPolicy:
    row = get_or_create_policy(session, traveler_id)
    row.mode = mode.value
    row.auto_accept_replan = bool(auto_accept_replan)
    row.max_auto_replan_cost_delta_minor = int(max_auto_replan_cost_delta_minor)
    row.allow_auto_when_provider_degraded = bool(allow_auto_when_provider_degraded)
    row.allow_auto_on_critical_event = bool(allow_auto_on_critical_event)
    row.version = int(row.version) + 1
    row.updated_at = _now()
    session.flush()
    return row


def evaluate_action(
    policy: DelegationPolicy,
    action: AgentAction,
    facts: AuthoritativeActionFacts,
) -> AuthorizationResult:
    if action in READ_ACTIONS:
        return AuthorizationResult(
            AuthorizationDecision.ALLOW_AUTO,
            ("READ_ONLY_TOOL",),
            policy.version,
        )

    if action == AgentAction.REQUEST_REPLAN:
        return AuthorizationResult(
            AuthorizationDecision.ALLOW_AUTO,
            ("PROPOSAL_ONLY", "DOMAIN_TRUTH_NOT_ACTIVATED"),
            policy.version,
        )

    if action == AgentAction.ACCEPT_REPLAN:
        if facts.hard_constraints_passed is not True:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                ("HARD_CONSTRAINTS_NOT_VERIFIED",),
                policy.version,
            )
        if facts.locked_commitments_preserved is not True or facts.c4_affected:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                ("C4_OR_LOCKED_COMMITMENT_NOT_PRESERVED",),
                policy.version,
            )
        if not facts.proposal_presented:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                ("PROPOSAL_NOT_PRESENTED",),
                policy.version,
            )
        if not facts.base_plan_current:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                ("BASE_PLAN_NOT_CURRENT",),
                policy.version,
            )
        if not facts.trigger_actionable:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                ("TRIGGER_EVENT_NOT_ACTIONABLE",),
                policy.version,
            )
        if policy.mode == AgentMode.ADVISORY or not policy.auto_accept_replan:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("USER_CONFIRMATION_REQUIRED",),
                policy.version,
            )
        if facts.cost_delta_minor > policy.max_auto_replan_cost_delta_minor:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("AUTO_COST_LIMIT_EXCEEDED",),
                policy.version,
            )
        if facts.provider_degraded and not policy.allow_auto_when_provider_degraded:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("PROVIDER_EVIDENCE_DEGRADED",),
                policy.version,
            )
        if (
            str(facts.event_severity or "").upper() == "CRITICAL"
            and not policy.allow_auto_on_critical_event
        ):
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_CONFIRMATION,
                ("CRITICAL_EVENT_REQUIRES_CONFIRMATION",),
                policy.version,
            )
        return AuthorizationResult(
            AuthorizationDecision.ALLOW_AUTO,
            ("DELEGATION_POLICY_MATCHED", "DETERMINISTIC_GATE_VERIFIED"),
            policy.version,
        )

    if action in {AgentAction.PAYMENT, AgentAction.REFUND, AgentAction.MODIFY_C4}:
        return AuthorizationResult(
            AuthorizationDecision.REQUIRE_STEP_UP,
            ("PROTECTED_ACTION_REQUIRES_STEP_UP",),
            policy.version,
        )

    return AuthorizationResult(
        AuthorizationDecision.DENY,
        ("ACTION_NOT_ALLOWLISTED",),
        policy.version,
    )


def default_policy_payload(traveler_id: UUID | str) -> dict[str, Any]:
    """Return the conservative policy without allowing an agent to mutate it."""
    return {
        "traveler_id": str(traveler_id),
        "mode": AgentMode.ADVISORY.value,
        "auto_accept_replan": False,
        "max_auto_replan_cost_delta_minor": 0,
        "allow_auto_when_provider_degraded": False,
        "allow_auto_on_critical_event": False,
        "version": 1,
    }
