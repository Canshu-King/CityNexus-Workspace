from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

def main():
    result = subprocess.run([sys.executable, str(HERE / "validate_c4_freeze.py")], check=False)
    if result.returncode:
        print("C4 verifier failed; not changing summary.")
        return result.returncode
    p = OUT / "calibration-summary.json"
    summary = json.loads(p.read_text(encoding="utf-8"))
    summary.update({
        "C1":"FROZEN_PASS","C2":"FROZEN_PASS","C3":"FROZEN_PASS","C4":"FROZEN_PASS",
        "C4Architecture":"native UML semantic connector + deterministic presentation route",
        "C4AssociationCalibration":"C4F","C4ExtendCalibration":"C4E1",
        "nextMilestone":"P1_UC_OVERVIEW_ROUTE_PLAN",
    })
    p.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
