# CityNexus Next Gate Contract

## Gate A: Post-Goal semantic repair

PASS requires all five defect-specific tests green:

```text
F3 effective Event time
C4 new-Plan activity remap
MobilitySnapshot injectable into authoritative persisted-plan gate
Open-Meteo Unix/UTC semantics
TRAFFIC_DELAY explicit extra_minutes
```

No aggregate test count may substitute for these semantics.

## Gate B: Backend Golden Scenario

PASS requires real API + database proof of:

```text
Plan → Booking → CAPTURE → C4 → Start
→ Event → Replan → Feasibility/C4 preservation
→ Accept → active/superseded PlanVersion transition
→ C4 activity remap → JourneyTwin reload
```

The provided `test_backend_connected_golden_contract.py` is the minimum executable proof.

## Gate C: Frontend backend-connected vertical slice

PASS requires:

```text
React UI data originates from backend responses
Event injection calls backend
Replan candidates originate from backend
Accept/reject calls backend
Reload GETs backend JourneyTwin
Accepted PlanVersion / C4 truth is not localStorage truth
Playwright launches or reaches a real local backend
frontend build passes
```

Do not treat the existing offline UI smoke as this gate.

## Gate D: Optional real-provider/solver/AI expansion

Only after Gate C:

```text
Valhalla frozen snapshot runtime path
Open-Meteo bounded runtime path + degradation/recovery
OR-Tools candidate generation → authoritative Gate
LiteLLM/DeepSeek verified-facts explanation + deterministic fallback
```

Live network remains optional. Course demo must remain runnable offline.
