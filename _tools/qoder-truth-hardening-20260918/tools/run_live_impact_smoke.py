"""Run one live semantic-impact demonstration without printing provider data."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app


def _fail(label: str, response) -> None:
    if response.status_code >= 400:
        raise RuntimeError(f"{label}:{response.status_code}")


def main() -> int:
    client = TestClient(app)
    try:
        ids_response = client.post("/api/v1/demo/reset")
        _fail("reset", ids_response)
        ids = ids_response.json()
        journey_id = ids["journey_id"]

        plans_response = client.post(
            f"/api/v1/journeys/{journey_id}/plans/generate",
            json={"candidate_count": 1},
        )
        _fail("generate", plans_response)
        plan = plans_response.json()[0]
        selected = client.post(
            f"/api/v1/journeys/{journey_id}/plans/{plan['id']}/select"
        )
        _fail("select", selected)

        cruise = next(item for item in plan["activities"] if item["place_id"] == "place-river-cruise")
        booking = client.post(
            f"/api/v1/journeys/{journey_id}/bookings", json={"activity_id": cruise["id"]}
        )
        _fail("booking", booking)
        booking_body = booking.json()
        captured = client.post(
            f"/api/v1/journeys/{journey_id}/transactions",
            headers={"Idempotency-Key": "live-impact-smoke-capture-01"},
            json={
                "booking_id": booking_body["id"],
                "transaction_type": "CAPTURE",
                "amount": booking_body["amount"],
            },
        )
        _fail("capture", captured)
        started = client.post(f"/api/v1/journeys/{journey_id}/start")
        _fail("start", started)

        tech = next(item for item in plan["activities"] if item["place_id"] == "place-tech-art")
        for activity in plan["activities"]:
            if activity["id"] == tech["id"]:
                break
            completed = client.post(
                f"/api/v1/journeys/{journey_id}/activities/{activity['id']}/complete"
            )
            _fail("complete", completed)

        event_response = client.post(
            f"/api/v1/journeys/{journey_id}/events",
            json={
                "event_type": "CLOSURE",
                "severity": "MAJOR",
                "occurred_at": "2026-10-10T13:25:00+08:00",
                "payload": {
                    "text": "Temporary security control and traffic restriction around the Tech Art Center; access is unavailable for the next hour.",
                    "valid_from": "2026-10-10T13:25:00+08:00",
                    "valid_until": "2026-10-10T14:45:00+08:00",
                },
            },
        )
        _fail("event", event_response)
        event = event_response.json()

        proposal_response = client.post(
            f"/api/v1/journeys/{journey_id}/replans",
            headers={"Idempotency-Key": "live-impact-smoke-replan-01"},
            json={"trigger_event_id": event["id"], "candidate_count": 3},
        )
        _fail("replan", proposal_response)
        proposal = proposal_response.json()
        impact_response = client.get(
            f"/api/v1/journeys/{journey_id}/events/{event['id']}/impact"
        )
        _fail("impact", impact_response)
        impact = impact_response.json()
        evidence = proposal.get("diff", {}).get("verified_evidence", {}).get(
            "impact_resolution", {}
        )

        if (
            impact.get("status") == "VALIDATED_AI"
            and impact.get("selected_activity_id") == tech["id"]
            and evidence.get("selected_activity_id") == tech["id"]
            and proposal.get("hard_constraints_passed") is True
        ):
            status = "PASS"
        elif impact.get("status") in {"FALLBACK", "AI_REJECTED_FALLBACK", "REJECTED"}:
            status = "PARTIAL"
        else:
            status = "FAILED_BLOCKED"
        print(f"DEEPSEEK_LIVE_SMOKE={status}")
        print(f"IMPACT_STATUS={impact.get('status')}")
        print(f"IMPACT_PROVIDER={impact.get('provider_key')}")
        print(f"IMPACT_SELECTED_ACTIVITY={'yes' if impact.get('selected_activity_id') == tech['id'] else 'no'}")
        print(f"ORT_DETERMINISTIC_GATE={'PASS' if proposal.get('hard_constraints_passed') else 'FAIL'}")
        return 0 if status in {"PASS", "PARTIAL"} else 1
    except Exception as exc:  # keep diagnostics free of response bodies/secrets
        print(f"DEEPSEEK_LIVE_SMOKE=FAILED_BLOCKED")
        print(f"FAILURE_TYPE={type(exc).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
