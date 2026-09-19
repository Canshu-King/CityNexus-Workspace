"""Sensitivity check for C0: would the old panel behaviour fail the new case?

Sabotages `V14PreventivePanel` back to the shape the arbitration rejected - stop
polling as soon as any preventive run exists, and trust `runs[0]` - runs the
lifecycle spec, and restores the file.
"""

import io
import os
import subprocess

PATH = "frontend/src/features/recovery/V14PreventivePanel.tsx"
original = io.open(PATH, encoding="utf-8", newline="").read()

sabotage = original.replace(
    """      if (preventive.status === "COMPLETED" && timer !== undefined) {""",
    """      if (timer !== undefined) {""",
    1,
)
assert sabotage != original, "stop-condition anchor did not match"

env = dict(os.environ)
env.update(
    {
        "CITYNEXUS_E2E_AUTHORITATIVE": "1",
        "CITYNEXUS_E2E_RUN_ID": "c0sab1",
        "DEEPSEEK_API_KEY": "",
        "CITYNEXUS_AI_API_KEY": "",
        "CITYNEXUS_AI_ENABLED": "false",
        "CITYNEXUS_PYTHON": r"D:\moodle\CityNexus\.venv\Scripts\python.exe",
        "CITYNEXUS_BACKEND_PORT": "8071",
        "CITYNEXUS_E2E_PORT": "4241",
        "CITYNEXUS_DATABASE_URL": "sqlite:///./_c0sab1.db",
    }
)

try:
    io.open(PATH, "w", encoding="utf-8", newline="").write(sabotage)
    print("=== panel reverted to stop-on-first-sighting; the case should fail ===")
    result = subprocess.run(
        ["npx.cmd", "playwright", "test", "e2e/qoder-preventive-lifecycle.spec.ts", "--reporter=line"],
        cwd="frontend",
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [line for line in result.stdout.splitlines() if "passed" in line or "failed" in line]
    print("verdict:", "KILLED" if result.returncode else "SURVIVED", "|", lines[-1:] or result.stdout[-300:])
finally:
    io.open(PATH, "w", encoding="utf-8", newline="").write(original)
    print("=== panel restored ===")
