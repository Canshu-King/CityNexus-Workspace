"""Probe what a booking + captured transaction actually creates.

pass-16 B asks the frontend fixtures to hold a *real* protected commitment instead
of trusting `locked_commitments_preserved` on a journey that has none.  Before
writing that helper, measure what the public endpoints produce: the commitment
level, whether the activity becomes locked, and whether /experience reports it.
"""

import json
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:8051/api/v1"


def call(path, method="GET", body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:400]


status, demo = call("/demo/reset", "POST")
journey = demo["journey_id"]
status, plans = call(f"/journeys/{journey}/plans/generate", "POST", {"candidate_count": 1})
plan = plans[0]
call(f"/journeys/{journey}/plans/{plan['id']}/select", "POST")

cruise = next(a for a in plan["activities"] if a["place_id"] == "place-river-cruise")
print("cruise activity", cruise["id"], cruise["title"], "locked=", cruise.get("locked"))

status, booking = call(f"/journeys/{journey}/bookings", "POST", {"activity_id": cruise["id"]})
print("booking", status, json.dumps(booking, ensure_ascii=False)[:300])

status, txn = call(f"/journeys/{journey}/transactions", "POST", {
    "booking_id": booking["id"], "transaction_type": "CAPTURE", "amount": booking.get("amount"),
}, headers={"Idempotency-Key": "probe-" + str(uuid.uuid4())})
print("capture", status, json.dumps(txn, ensure_ascii=False)[:300])

status, commitments = call(f"/journeys/{journey}/commitments")
print("commitments", status, json.dumps(commitments, ensure_ascii=False)[:600])

status, started = call(f"/journeys/{journey}/start", "POST")
print("start", status, str(started)[:120])

status, exp = call(f"/journeys/{journey}/experience")
active = exp.get("active_plan") or {}
cruise_after = next((a for a in active.get("activities", []) if a.get("place_id") == "place-river-cruise"), None)
print("experience cruise:", json.dumps(cruise_after, ensure_ascii=False)[:400])
print("experience keys:", sorted(exp.keys()))
for key in ("commitments", "protected_commitments"):
    if key in exp:
        print(key, json.dumps(exp[key], ensure_ascii=False)[:400])
