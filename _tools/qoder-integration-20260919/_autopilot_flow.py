"""Drive the CityNexus V5 Guardian Autopilot end-to-end against a live server.

Targets a server whose CITYNEXUS_AI_* env is configured with a real model, so the
tool loop is chosen by the model rather than by the deterministic fallback.

Flow: reset demo -> generate/select plan -> book + capture the protected cruise ->
start journey -> set AUTONOMOUS policy -> set a standing mission -> start the
autopilot -> flip the provider fixture to DISRUPTED -> wait for the server to
recover on its own, with no manual scan and no new chat prompt.
"""

from __future__ import annotations

import json
import sys
import time
from uuid import uuid4

import httpx

BASE = "http://127.0.0.1:8001/api/v1"
client = httpx.Client(base_url=BASE, timeout=180.0)


def show(label: str, payload: object) -> None:
    print(f"\n--- {label} ---")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)[:900])


ids = client.post("/demo/reset").json()
journey_id = ids["journey_id"]
traveler_id = ids["traveler_id"]
show("0. demo reset", ids)

generated = client.post(f"/journeys/{journey_id}/plans/generate", json={"candidate_count": 1})
generated.raise_for_status()
plan = generated.json()[0]
base_plan_id = plan["id"]
client.post(f"/journeys/{journey_id}/plans/{base_plan_id}/select").raise_for_status()
show("1. base plan", {"plan_id": base_plan_id, "titles": [a["title"] for a in plan["activities"]]})

cruise = next(item for item in plan["activities"] if item["place_id"] == "place-river-cruise")
booking = client.post(f"/journeys/{journey_id}/bookings", json={"activity_id": cruise["id"]}).json()
captured = client.post(
    f"/journeys/{journey_id}/transactions",
    json={"booking_id": booking["id"], "transaction_type": "CAPTURE", "amount": booking["amount"]},
    headers={"Idempotency-Key": f"autopilot-capture-{uuid4()}"},
)
show("2. protected cruise booked + captured", {"status": captured.status_code, "booking": booking["id"]})
client.post(f"/journeys/{journey_id}/start").raise_for_status()

policy = client.put(
    f"/travelers/{traveler_id}/agent-policy",
    json={
        "mode": "AUTONOMOUS",
        "auto_accept_replan": True,
        "max_auto_replan_cost_delta_minor": 5000,
        "max_auto_loss_minor": 0,
        "max_auto_schedule_drift_min": 120,
        "allowed_activity_types": ["visit", "meal", "transport"],
        "protected_commitment_levels": ["C4_Anchored"],
        "allow_auto_commitment_management": False,
        "allow_auto_when_provider_degraded": False,
        "allow_auto_on_critical_event": False,
    },
)
show("3. autonomy envelope", {"status": policy.status_code, "body": policy.json()})

mission = client.put(
    f"/journeys/{journey_id}/guardian/mission",
    json={
        "command": "游船和晚餐别动，优先室内、少走路，最多多花五十元，允许自动调整。",
        "requested_autonomy": "EXECUTE_WITHIN_BOUNDS",
    },
)
show("4. standing mission", {"status": mission.status_code, "body": mission.json()})

started = client.post(f"/journeys/{journey_id}/guardian/autopilot/start", json={"interval_seconds": 0.05})
show("5. autopilot started", started.json())

print("\n--- 6. provider flips to DISRUPTED (no manual scan, no new prompt) ---")
fixture = client.post(
    f"/journeys/{journey_id}/guardian/provider-fixture",
    json={"state": "DISRUPTED", "payload": {"scenario": "heavy-rain-and-delay"}},
)
print("fixture ->", fixture.status_code)

latest = None
deadline = time.time() + 240
while time.time() < deadline:
    status = client.get(f"/journeys/{journey_id}/guardian/status").json()
    candidate = status.get("latest")
    if candidate and candidate.get("action_status") == "EXECUTED":
        latest = candidate
        break
    time.sleep(1.0)

if latest is None:
    status = client.get(f"/journeys/{journey_id}/guardian/status").json()
    show("6b. NOT EXECUTED within deadline", status)
    sys.exit(1)

print("\n=== RECOVERY EXECUTED AUTOMATICALLY ===")
print("action_status          :", latest.get("action_status"))
print("trigger_kind           :", latest.get("trigger_kind"))
print("plan changed           :", latest.get("active_plan_after_id") != base_plan_id)
print("before / after plan    :", latest.get("active_plan_before_id"), "->", latest.get("active_plan_after_id"))

evidence = latest.get("evidence", {})
solver = evidence.get("solver", {})
observation = evidence.get("observation", {})
print("solver kind            :", solver.get("kind"))
print("incident fingerprints  :", observation.get("incident_fingerprints"))
print("agent runtime provider :", (latest.get("agent_runtime") or {}).get("provider_key"))
print("agent runtime model    :", (latest.get("agent_runtime") or {}).get("model_key"))
print("tool steps (model-chosen):", [s.get("tool_name") for s in latest.get("tool_steps", [])])

print("\n--- 7. model reasoning / tool trace ---")
for step in latest.get("tool_steps", []):
    print(f"  - {step.get('tool_name')}: {json.dumps(step.get('arguments') or {}, ensure_ascii=False)[:220]}")

print("\n--- 8. active plan after recovery ---")
plans = client.get(f"/journeys/{journey_id}/plans").json()
active = next((p for p in plans if p.get("status") == "ACTIVE"), None)
for activity in (active or {}).get("activities", []):
    print(f"   {activity['sequence_no']}. {activity['title']}  {activity['start_at']}")

print("\n--- 9. dedup: one more pulse must not mutate again ---")
before = client.get(f"/journeys/{journey_id}/guardian/status").json()
time.sleep(3)
after = client.get(f"/journeys/{journey_id}/guardian/status").json()
print("plan stable across extra pulses:", before.get("current_active_plan_version_id") == after.get("current_active_plan_version_id"))
print("latest action_status now       :", after.get("latest", {}).get("action_status"))
print("guardian run count             :", after.get("run_count") or after.get("total_runs"))
