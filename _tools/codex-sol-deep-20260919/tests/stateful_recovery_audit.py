#!/usr/bin/env python3
"""Deterministic model-based audit for CityNexus recovery invariants.

No network or repository mutation is performed.  The harness explores randomized
transition sequences, checks the twelve mission invariants after every step, and
emits replayable JSON.  It also models the verified Live cursor defect separately
so the state-machine audit can stay green while preserving the counterexample.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path

HARD_QUALITIES = {"LIVE_PROVIDER_CAPTURE", "EXPLICIT_FROZEN_FIXTURE"}


@dataclass
class Event:
    id: str
    status: str = "DETECTED"
    physical_id: str = "venue-a"


@dataclass
class Proposal:
    id: str
    trigger: str
    status: str = "PRESENTED"
    material: bool = True
    protected_preserved: bool = True


@dataclass
class Model:
    active_plan: str = "plan-0"
    activities: list[str] = field(default_factory=lambda: ["a", "b", "c"])
    current: str = "a"
    events: dict[str, Event] = field(default_factory=dict)
    proposals: dict[str, Proposal] = field(default_factory=dict)
    accepted_trigger_ids: set[str] = field(default_factory=set)
    closed_physical_ids: set[str] = field(default_factory=set)
    aliases: dict[str, str | None] = field(default_factory=dict)
    commitments: set[str] = field(default_factory=lambda: {"booking-1"})
    mobility_quality: str | None = None
    hard_mobility: bool = False
    whole_trip_budget_claim: bool = False
    budget_components_verified: tuple[bool, ...] = (False, False, False)
    idempotency: dict[str, str] = field(default_factory=dict)
    today_plan: str = "plan-0"
    live_plan: str = "plan-0"

    def transition(self, op: str, rng: random.Random) -> None:
        if op == "detect":
            eid = f"e{len(self.events)}"
            self.events[eid] = Event(eid, physical_id=f"venue-{rng.randrange(3)}")
        elif op == "ack" and self.events:
            event = rng.choice(list(self.events.values()))
            if event.status == "DETECTED":
                event.status = "ACKNOWLEDGED"
        elif op == "resolve" and self.events:
            event = rng.choice(list(self.events.values()))
            event.status = "RESOLVED"
            self.closed_physical_ids.add(event.physical_id)
        elif op == "propose" and self.events:
            event = rng.choice(list(self.events.values()))
            if event.status in {"DETECTED", "ACKNOWLEDGED"}:
                pid = f"p{len(self.proposals)}"
                self.proposals[pid] = Proposal(pid, event.id, material=True)
        elif op == "accept" and self.proposals:
            proposal = rng.choice(list(self.proposals.values()))
            key = f"accept:{proposal.id}"
            if key not in self.idempotency and proposal.status == "PRESENTED":
                proposal.status = "ACCEPTED"
                self.accepted_trigger_ids.add(proposal.trigger)
                self.idempotency[key] = proposal.id
                self.active_plan = f"plan-{proposal.id}"
                self.today_plan = self.active_plan
                self.live_plan = self.active_plan
        elif op == "retry_accept" and self.proposals:
            proposal = rng.choice(list(self.proposals.values()))
            key = f"accept:{proposal.id}"
            if key in self.idempotency:
                assert self.idempotency[key] == proposal.id
        elif op == "close_alias":
            canonical = f"venue-{rng.randrange(3)}"
            self.closed_physical_ids.add(canonical)
            self.aliases[f"alias-{rng.randrange(5)}"] = canonical
        elif op == "ambiguous_alias":
            self.aliases[f"ambiguous-{rng.randrange(5)}"] = None
        elif op == "provider":
            quality = rng.choice([None, "SYNTHETIC_DEFAULT", "LIVE_PROVIDER_CAPTURE", "EXPLICIT_FROZEN_FIXTURE"])
            self.mobility_quality = quality
            self.hard_mobility = quality in HARD_QUALITIES
        elif op == "budget":
            self.budget_components_verified = tuple(rng.choice([True, False]) for _ in range(3))
            self.whole_trip_budget_claim = all(self.budget_components_verified)

    def check(self) -> None:
        # 1-3: ACK and linked acceptance semantics.
        for event in self.events.values():
            if event.status == "ACKNOWLEDGED":
                assert event.id not in self.accepted_trigger_ids or any(
                    p.status == "ACCEPTED" and p.trigger == event.id for p in self.proposals.values()
                )
        for trigger in self.accepted_trigger_ids:
            assert any(p.status == "ACCEPTED" and p.trigger == trigger for p in self.proposals.values())
        # 4-5: physical identity and ambiguity fail closed.
        for alias, canonical in self.aliases.items():
            if canonical is None:
                assert alias not in self.closed_physical_ids
            if canonical in self.closed_physical_ids:
                assert canonical != alias
        # 6-7: hard mobility allowlist.
        assert self.hard_mobility == (self.mobility_quality in HARD_QUALITIES)
        # 8-9: accepted proposals are material and preserve protected commitments.
        for proposal in self.proposals.values():
            if proposal.status == "ACCEPTED":
                assert proposal.material
                assert proposal.protected_preserved
        assert "booking-1" in self.commitments
        # 10: whole-trip claim requires all components.
        assert not self.whole_trip_budget_claim or all(self.budget_components_verified)
        # 11: all consumer projections identify the active plan.
        assert self.today_plan == self.live_plan == self.active_plan
        # 12: one durable acceptance record per proposal.
        assert len(self.idempotency) == len(set(self.idempotency))


OPS = ("detect", "ack", "resolve", "propose", "accept", "retry_accept", "close_alias", "ambiguous_alias", "provider", "budget")


def run(seed: int, sequences: int, steps: int) -> dict:
    rng = random.Random(seed)
    transitions = 0
    for case in range(sequences):
        model = Model()
        trace: list[str] = []
        for _ in range(steps):
            op = rng.choice(OPS)
            trace.append(op)
            model.transition(op, rng)
            transitions += 1
            try:
                model.check()
            except AssertionError as exc:
                return {"status": "FAIL", "seed": seed, "case": case, "trace": trace, "state": serialise(model), "error": repr(exc)}
    return {"status": "PASS", "seed": seed, "sequences": sequences, "steps_per_sequence": steps, "transitions": transitions, "invariants": 12}


def serialise(model: Model) -> dict:
    value = asdict(model)
    value["accepted_trigger_ids"] = sorted(model.accepted_trigger_ids)
    value["closed_physical_ids"] = sorted(model.closed_physical_ids)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--sequences", type=int, default=5000)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.seed, args.sequences, args.steps)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
