"""Diagnose where activity identity is lost across a replan.

Question the pass-16 ruling asks before any code change:

    /plans/generate  -> activity.place_id populated
    accepted replan  -> /experience reports place_id null for every activity

Is identity lost while the child PlanVersion is created/copied, or only while
/experience projects it?  The fix belongs at the layer that actually loses it, so
this script reads the same plan from both places and prints them side by side.

Run against a backend started from this tree with a throwaway database:

    cd backend && CITYNEXUS_E2E_RUN_ID=diag1 \
      CITYNEXUS_DATABASE_URL='sqlite:///./_p16diag.db' \
      DEEPSEEK_API_KEY= CITYNEXUS_AI_API_KEY= CITYNEXUS_AI_ENABLED=false \
      <venv python> -m uvicorn app.main:app --port 8050
"""

import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get("DIAG_BASE", "http://127.0.0.1:8050") + "/api/v1"


def call(path, method="GET", body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:300]


def rows(activities):
    return [
        {
            "id": (a.get("id") or "")[:8],
            "title": a.get("title"),
            "place_id": a.get("place_id"),
            "kind": a.get("activity_type") or a.get("kind"),
        }
        for a in (activities or [])
    ]


status, demo = call("/demo/reset", "POST", {})
journey = demo["journey_id"]
print("journey", journey)

status, plans = call(f"/journeys/{journey}/plans/generate", "POST", {"candidate_count": 1})
plan = plans[0]
print("\n== generated plan %s ==" % plan["id"][:8])
for row in rows(plan.get("activities")):
    print("   ", row)

call(f"/journeys/{journey}/plans/{plan['id']}/select", "POST")
call(f"/journeys/{journey}/start", "POST")

tech = next((a for a in plan["activities"] if a.get("place_id") == "place-tech-art"), None)
assert tech, "no tech-art activity to close"
status, event = call(f"/journeys/{journey}/events", "POST", {
    "event_type": "CLOSURE", "severity": "MAJOR",
    "affected_activity_id": tech["id"],
    "occurred_at": "2026-10-10T13:25:00+08:00",
    "payload": {"reason": "pass-16 identity diagnosis"},
})
print("\nevent", status, event.get("id"))

status, receipt = call("/agent/tools/request_replan", "POST", {
    "request_id": "diag-" + event["id"], "agent_id": "citynexus-local-agent",
    "journey_id": journey, "trigger_event_id": event["id"], "candidate_count": 3,
})
print("request_replan", status, receipt.get("decision") if isinstance(receipt, dict) else receipt)

status, proposals = call(f"/journeys/{journey}/replans")
presented = [p for p in proposals if p.get("trigger_event_id") == event["id"] and p.get("status") == "PRESENTED"]
print("presented proposals:", [(p["id"][:8], p.get("proposed_plan_version_id", "")[:8]) for p in presented])
assert presented, "no proposal to accept"
proposal = presented[0]

status, accepted = call(f"/replans/{proposal['id']}/accept", "POST", headers={"Idempotency-Key": "diag-accept"})
print("accept", status, str(accepted)[:200])

child_id = proposal.get("proposed_plan_version_id")
status, canonical = call(f"/plans/{child_id}")
print("\n== canonical child PlanVersion /plans/%s == status %s" % (child_id[:8], status))
if isinstance(canonical, dict):
    for row in rows(canonical.get("activities")):
        print("   ", row)

status, listed = call(f"/journeys/{journey}/plans")
if isinstance(listed, list):
    for item in listed:
        print("   listed plan %s chosen=%s activities=%d with-place=%d" % (
            item.get("id", "")[:8], item.get("chosen"), len(item.get("activities") or []),
            sum(1 for a in item.get("activities") or [] if a.get("place_id"))))

status, experience = call(f"/journeys/{journey}/experience")
print("\n== /experience active_plan %s ==" % (experience.get("active_plan", {}) or {}).get("id", "")[:8])
for row in rows((experience.get("active_plan") or {}).get("activities")):
    print("   ", row)

print("\n== verdict ==")
canon_with = sum(1 for a in (canonical.get("activities") if isinstance(canonical, dict) else []) or [] if a.get("place_id"))
exp_with = sum(1 for a in (experience.get("active_plan") or {}).get("activities", []) if a.get("place_id"))
print("canonical child activities with place_id: %d/%d" % (
    canon_with, len((canonical.get("activities") if isinstance(canonical, dict) else []) or [])))
print("experience  active activities with place_id: %d/%d" % (
    exp_with, len((experience.get("active_plan") or {}).get("activities", []))))
if canon_with and not exp_with:
    print("=> identity survives in the canonical plan and is lost in the /experience projection")
elif not canon_with:
    print("=> identity is already gone in the canonical child PlanVersion (copy/creation bug)")
else:
    print("=> identity present in both; the pass-15 observation needs re-reading")
