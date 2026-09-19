# v3 evidence gate

Package:

`CityNexus-Qoder-Xiaomi-Truth-Hardening-v3-20260918.zip`

must contain:

- QODER_V3_IMPLEMENTATION_REPORT.md
- CHANGED_FILES.txt
- TEST_RESULTS.md
- raw_focused_v3.log
- raw_full_backend_v3.log
- raw_full_backend_baseline.log
- fail_baseline.txt
- fail_v3.txt
- clean patch against the same synthetic baseline
- frontend typecheck raw output
- frontend build raw output
- rendered-test raw output

Claims must match tests.

Do not say:
"candidate A survives"
unless the endpoint test asserts 201 + candidate A identity.

Do not label:
- pure-function browser tests as E2E;
- Live-only test as Today+Live proof;
- activity-only rendered data as cross-source stay/booking proof.

Final verdict exactly:

`QODER_V3_PATCH_READY_FOR_INTEGRATION`

or

`QODER_V3_BLOCKED`
