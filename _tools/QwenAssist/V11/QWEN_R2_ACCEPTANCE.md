# ROUND-2 ACCEPTANCE GATES

Mandatory gates:

G1
All candidate `.py` files parse with Python AST.

G2
No candidate test contains:
- TODO
- placeholder `pass`
- Ellipsis `...` used as pseudo-code.

G3
At least 25 non-placeholder test functions exist across:
- DeepSeek Agent
- Compose/provider
- Money
- Execution
- Journey Inbox.

G4
REAL_TRAVEL_EDGE_CASES.csv:
- >=150 rows;
- exactly 8 columns each;
- unique ID;
- non-empty Priority;
- machine-readable by Python csv module.

G5
Tracks G/H/I/K from round 1 are now completed.

G6
GitHub adoption research explicitly verifies current license metadata.

G7
21st-dev licensing is corrected based on current evidence, not "unclear" if current metadata is explicit.

G8
P0 code map contains no "TBD" for files that exist locally.

G9
OpenAPI duplicate-type CSV contains actual scanned source rows.

G10
Storybook matrix contains actual scanned component/story paths.

G11
PIC/Edge cases reflect the actual architecture:
PIC = display/input/sensor/RTC edge device;
ESP8266 = network gateway;
server = AI/planner truth.

G12
QR/barcode decode is never described as authenticity verification unless there is a separate cryptographic/provider validation step.

G13
Final handoff is written only after the validator passes or documented blockers remain.

Optional high-value gate:
Run a subset of candidate tests against a temporary copy or test environment without modifying the authoritative repository.
