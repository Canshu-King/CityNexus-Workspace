from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.contracts import (
    AgentAction,
    AuthoritativeActionFacts,
    AuthorizationDecision,
)
from app.agent.delegation_policy import (
    evaluate_action,
    get_or_create_policy,
    policy_from_model,
)
from app.agent.tool_catalog import RUNTIME_MCP_ALLOWLIST_V1, tool_catalog
from app.commerce.idempotency import canonical_request_signature
from app.core.audit import record_audit
from app.db.models import (
    CityService,
    Event,
    IdempotencyKey,
    Journey,
    ReplanProposal,
)
from app.schemas import AgentToolCall, ReplanGenerateRequest
from app.services import journey_schema, service_schema


def _agent_key(kind: str, *parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"agent.{kind}:{digest}"


def _read_idempotent(session: Session, key: str, signature: str) -> dict[str, Any] | None:
    row = session.get(IdempotencyKey, key)
    if row is None:
        return None
    if row.request_hash != signature:
        raise HTTPException(409, "same agent request id used for a different request")
    stored = json.loads(row.response_json or "{}")
    if not stored:
        raise HTTPException(409, "agent idempotency record is incomplete")
    return stored


def _write_idempotent(
    session: Session,
    *,
    key: str,
    operation: str,
    signature: str,
    response: dict[str, Any],
) -> None:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    session.add(
        IdempotencyKey(
            key=key,
            operation=operation,
            request_hash=signature,
            response_status=200,
            response_json=json.dumps(response, sort_keys=True, default=str),
            created_at=now.isoformat(),
            expires_at=(now + timedelta(days=7)).isoformat(),
        )
    )


def _json(value: object) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _require_journey(session: Session, journey_id: UUID | None) -> Journey:
    if journey_id is None:
        raise HTTPException(422, "journey_id is required for this Agent tool")
    journey = session.get(Journey, str(journey_id))
    if journey is None:
        raise HTTPException(404, f"Journey {journey_id} was not found")
    return journey


def _facts_for_accept(
    session: Session,
    proposal: ReplanProposal,
    journey: Journey,
) -> tuple[AuthoritativeActionFacts, dict[str, Any]]:
    try:
        diff = json.loads(proposal.diff_json or "{}")
    except json.JSONDecodeError:
        diff = {}
    verified = diff.get("verified_evidence", {})
    envelope = diff.get("after_feasibility_envelope", {})
    mobility = verified.get("mobility", {})
    trigger = session.get(Event, proposal.trigger_event_id) if proposal.trigger_event_id else None
    preserved = bool(proposal.locked_commitments_preserved)
    preserved = preserved and diff.get("preserved_protected", True) is not False
    preserved = preserved and verified.get("commitment_preservation", {}).get("preserved", True)
    degraded_providers = envelope.get("degraded_providers") or []
    provider_degraded = bool(
        degraded_providers
        or mobility.get("degraded") is True
        or mobility.get("snapshot", {}).get("degraded") is True
    )
    base_current = journey.active_plan_version_id == proposal.base_plan_version_id
    trigger_actionable = trigger is not None and trigger.status in {"DETECTED", "ACKNOWLEDGED"}
    facts = AuthoritativeActionFacts(
        hard_constraints_passed=bool(proposal.hard_constraints_passed),
        locked_commitments_preserved=preserved,
        c4_affected=not preserved,
        cost_delta_minor=int(diff.get("cost_delta_minor") or 0),
        provider_degraded=provider_degraded,
        event_severity=trigger.severity if trigger is not None else None,
        proposal_presented=proposal.status == "PRESENTED",
        base_plan_current=base_current,
        trigger_actionable=trigger_actionable,
    )
    evidence = {
        "hard_constraints_passed": facts.hard_constraints_passed,
        "locked_commitments_preserved": facts.locked_commitments_preserved,
        "c4_affected": facts.c4_affected,
        "cost_delta_minor": facts.cost_delta_minor,
        "provider_degraded": facts.provider_degraded,
        "event_severity": facts.event_severity,
        "proposal_presented": facts.proposal_presented,
        "base_plan_current": facts.base_plan_current,
        "trigger_actionable": facts.trigger_actionable,
    }
    return facts, evidence


class AgentToolGateway:
    """The only server entry point for the V1 Agent tool surface.

    The gateway accepts typed intent and resolves every policy and feasibility
    fact from CityNexus persistence. It never accepts a client supplied gate
    result, provider state, cost delta, or C4 assertion.
    """

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def catalog() -> list[dict[str, object]]:
        return tool_catalog()

    def dispatch(self, tool_name: str, request: AgentToolCall) -> dict[str, Any]:
        if tool_name not in RUNTIME_MCP_ALLOWLIST_V1:
            raise HTTPException(404, "Agent tool is not in the CityNexus V1 allowlist")
        handlers = {
            "inspect_journey": self.inspect_journey,
            "inspect_twin": self.inspect_twin,
            "list_replans": self.list_replans,
            "search_city_services": self.search_city_services,
            "request_replan": self.request_replan,
            "accept_replan": self.accept_replan,
        }
        return handlers[tool_name](request)

    def inspect_journey(self, request: AgentToolCall) -> dict[str, Any]:
        journey = _require_journey(self.session, request.journey_id)
        return {
            "tool": "inspect_journey",
            "decision": AuthorizationDecision.ALLOW_AUTO.value,
            "journey": _json(journey_schema(journey)),
        }

    def inspect_twin(self, request: AgentToolCall) -> dict[str, Any]:
        journey = _require_journey(self.session, request.journey_id)
        from app.main import _twin_snapshot

        savepoint = self.session.begin_nested()
        try:
            twin = _twin_snapshot(self.session, journey)
        finally:
            savepoint.rollback()
        return {
            "tool": "inspect_twin",
            "decision": AuthorizationDecision.ALLOW_AUTO.value,
            "twin": twin,
        }

    def list_replans(self, request: AgentToolCall) -> dict[str, Any]:
        journey = _require_journey(self.session, request.journey_id)
        from app.main import _replan_payload

        proposals = self.session.scalars(
            select(ReplanProposal)
            .where(ReplanProposal.journey_id == journey.id)
            .order_by(ReplanProposal.created_at, ReplanProposal.id)
        ).all()
        return {
            "tool": "list_replans",
            "decision": AuthorizationDecision.ALLOW_AUTO.value,
            "proposals": [_replan_payload(item) for item in proposals],
        }

    def search_city_services(self, request: AgentToolCall) -> dict[str, Any]:
        city_code = request.city_code
        if city_code is None and request.journey_id is not None:
            city_code = _require_journey(self.session, request.journey_id).city_code
        if not city_code:
            raise HTTPException(422, "city_code or journey_id is required for this Agent tool")
        items = self.session.scalars(
            select(CityService).where(CityService.city_code == city_code).order_by(CityService.id)
        ).all()
        if request.service_type:
            items = [
                item for item in items if item.service_type.lower() == request.service_type.lower()
            ]
        if request.q:
            needle = request.q.lower()
            items = [item for item in items if needle in item.name.lower()]
        return {
            "tool": "search_city_services",
            "decision": AuthorizationDecision.ALLOW_AUTO.value,
            "city_code": city_code,
            "services": [_json(service_schema(item)) for item in items],
        }

    def request_replan(self, request: AgentToolCall) -> dict[str, Any]:
        journey = _require_journey(self.session, request.journey_id)
        if request.trigger_event_id is None:
            raise HTTPException(422, "trigger_event_id is required for request_replan")
        policy_row = get_or_create_policy(self.session, journey.traveler_id)
        policy = policy_from_model(policy_row)
        auth = evaluate_action(policy, AgentAction.REQUEST_REPLAN, AuthoritativeActionFacts())
        signature = canonical_request_signature(
            {
                "tool": "request_replan",
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "journey_id": journey.id,
                "trigger_event_id": str(request.trigger_event_id),
                "candidate_count": request.candidate_count,
            }
        )
        key = _agent_key("request_replan", request.agent_id, request.request_id, journey.id)
        stored = _read_idempotent(self.session, key, signature)
        if stored is not None:
            return stored

        from app.main import generate_replan

        inner_key = _agent_key(
            "replan_generation", request.agent_id, request.request_id, journey.id
        )
        generated = generate_replan(
            UUID(journey.id),
            ReplanGenerateRequest(
                trigger_event_id=request.trigger_event_id,
                candidate_count=request.candidate_count,
            ),
            idempotency_key=inner_key,
            session=self.session,
        )
        proposals = self.session.scalars(
            select(ReplanProposal)
            .where(
                ReplanProposal.journey_id == journey.id,
                ReplanProposal.trigger_event_id == str(request.trigger_event_id),
            )
            .order_by(ReplanProposal.created_at, ReplanProposal.id)
        ).all()
        response = {
            "tool": "request_replan",
            "decision": auth.decision.value,
            "reason_codes": list(auth.reason_codes),
            "policy_version": auth.policy_version,
            "request_id": request.request_id,
            "proposal": generated,
            "proposals": [
                {
                    "id": item.id,
                    "status": item.status,
                    "hard_constraints_passed": bool(item.hard_constraints_passed),
                    "locked_commitments_preserved": bool(item.locked_commitments_preserved),
                }
                for item in proposals
            ],
        }
        record_audit(
            self.session,
            action="agent.request_replan",
            entity_type="ReplanProposal",
            entity_id=str(generated["id"]),
            journey_id=journey.id,
            actor_type="AI_AGENT",
            actor_id=request.agent_id,
            after={
                "policy_version": auth.policy_version,
                "authorization_decision": auth.decision.value,
                "reason_codes": list(auth.reason_codes),
                "before_status": None,
                "after_status": "PRESENTED",
                "request_id": request.request_id,
            },
        )
        _write_idempotent(
            self.session,
            key=key,
            operation="agent.request_replan",
            signature=signature,
            response=response,
        )
        self.session.commit()
        return response

    def accept_replan(self, request: AgentToolCall) -> dict[str, Any]:
        if request.proposal_id is None:
            raise HTTPException(422, "proposal_id is required for accept_replan")
        proposal = self.session.get(ReplanProposal, str(request.proposal_id))
        if proposal is None:
            raise HTTPException(404, "Replan proposal was not found")
        journey = _require_journey(self.session, request.journey_id or UUID(proposal.journey_id))
        if proposal.journey_id != journey.id:
            raise HTTPException(403, "proposal does not belong to this Journey")
        policy_row = get_or_create_policy(self.session, journey.traveler_id)
        policy = policy_from_model(policy_row)
        facts, evidence = _facts_for_accept(self.session, proposal, journey)
        auth = evaluate_action(policy, AgentAction.ACCEPT_REPLAN, facts)
        signature = canonical_request_signature(
            {
                "tool": "accept_replan",
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "journey_id": journey.id,
                "proposal_id": proposal.id,
            }
        )
        key = _agent_key("accept_replan", request.agent_id, request.request_id, proposal.id)
        stored = _read_idempotent(self.session, key, signature)
        if stored is not None:
            return stored

        if not facts.base_plan_current or not facts.trigger_actionable:
            # Staleness is a domain conflict. The policy result is still
            # recorded in the response for a caller that is comparing receipts.
            raise HTTPException(409, "replan proposal is stale or its trigger is resolved")

        response: dict[str, Any]
        if auth.decision == AuthorizationDecision.ALLOW_AUTO:
            from app.main import _accept_replan_impl

            inner_key = _agent_key(
                "replan_accept", request.agent_id, request.request_id, proposal.id
            )
            result = _accept_replan_impl(
                UUID(proposal.id),
                inner_key,
                self.session,
                actor_type="AI_AGENT",
                actor_id=request.agent_id,
                policy_version=auth.policy_version,
                authorization_decision=auth.decision.value,
                reason_codes=auth.reason_codes,
            )
            response = {
                "tool": "accept_replan",
                "decision": auth.decision.value,
                "reason_codes": list(auth.reason_codes),
                "policy_version": auth.policy_version,
                "request_id": request.request_id,
                "executed": True,
                "facts": evidence,
                "result": result,
            }
            after_status = "ACCEPTED"
        else:
            response = {
                "tool": "accept_replan",
                "decision": auth.decision.value,
                "reason_codes": list(auth.reason_codes),
                "policy_version": auth.policy_version,
                "request_id": request.request_id,
                "executed": False,
                "facts": evidence,
                "proposal_id": proposal.id,
                "status": proposal.status,
            }
            after_status = proposal.status

        record_audit(
            self.session,
            action="agent.accept_replan",
            entity_type="ReplanProposal",
            entity_id=proposal.id,
            journey_id=journey.id,
            actor_type="AI_AGENT",
            actor_id=request.agent_id,
            before={
                "status": "PRESENTED",
                "policy_version": auth.policy_version,
            },
            after={
                "status": after_status,
                "policy_version": auth.policy_version,
                "authorization_decision": auth.decision.value,
                "reason_codes": list(auth.reason_codes),
                "request_id": request.request_id,
            },
        )
        _write_idempotent(
            self.session,
            key=key,
            operation="agent.accept_replan",
            signature=signature,
            response=response,
        )
        self.session.commit()
        return response
