"""Retune the guardian projection test against how a preventive run is produced.

Measured: `POST /guardian/scan` runs the reactive controller only - with no open
event it answers `NO_ACTION`, and a second scan of the same state is deduplicated.
The preventive cycle belongs to the autopilot, so the fixture has to enrol the
journey and wait for the run rather than ask for it twice.
"""

import io

PATH = "backend/tests/test_sol_guardian_projection.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

old = '''    assert client.post(f"/api/v1/journeys/{journey_id}/guardian/scan").status_code == 200
    assert (
        client.post(
            f"/api/v1/journeys/{journey_id}/guardian/provider-fixture",
            json={"state": "RISK_FORECAST", "payload": {"risk_score": 88}},
        ).status_code
        == 200
    )
    assert client.post(f"/api/v1/journeys/{journey_id}/guardian/scan").status_code == 200
    runs = client.get(f"/api/v1/journeys/{journey_id}/guardian/status").json()["runs"]
    return journey_id, runs'''

new = '''    # A scan is the reactive controller: with no open event it answers NO_ACTION,
    # and re-scanning the same state is deduplicated.  Prevention is the autopilot's
    # cycle, so enrol the journey and let it run.
    assert client.post(f"/api/v1/journeys/{journey_id}/guardian/scan").status_code == 200
    assert (
        client.post(
            f"/api/v1/journeys/{journey_id}/guardian/provider-fixture",
            json={"state": "RISK_FORECAST", "payload": {"risk_score": 88}},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/journeys/{journey_id}/guardian/autopilot/start", json={"interval_seconds": 0.5}
        ).status_code
        == 200
    )
    runs = []
    for _ in range(120):
        runs = client.get(f"/api/v1/journeys/{journey_id}/guardian/status").json()["runs"]
        if any(
            item["decision"] == "PREEMPTIVE_RECOVERY" and item["trigger_kind"] == "PREDICTIVE"
            for item in runs
        ):
            break
        time.sleep(0.5)
    client.post(f"/api/v1/journeys/{journey_id}/guardian/autopilot/stop", json={})
    return journey_id, runs'''

assert old in text
text = text.replace(old, new, 1)
text = text.replace(
    "from datetime import datetime\nfrom typing import Any",
    "import time\nfrom datetime import datetime\nfrom typing import Any",
    1,
)
io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("projection test retuned")
