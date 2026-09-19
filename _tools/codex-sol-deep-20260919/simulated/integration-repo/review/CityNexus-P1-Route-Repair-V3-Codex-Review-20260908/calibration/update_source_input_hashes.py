"""Generate current build-input hashes for frozen C3/C4 association fallback and C4 Extend calibration."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

RENDERER = Path(__file__).resolve().parents[1]
ROOT = RENDERER.parent
OUT = Path(__file__).resolve().parent / 'out' / 'source-input-hashes.json'
INPUTS = [
    'visio-spec/style-tokens.yaml',
    'visio-spec/pages/p1_uc_overview.yaml',
    'visio-renderer/render-config.yaml',
    'visio-renderer/native-master-map.json',
    'visio-renderer/phase1-routing.yaml',
    'visio-renderer/presentation.py',
    'visio-renderer/routing_geometry.py',
    'visio-renderer/TOOLCHAIN-BASELINE.md',
    'visio-renderer/calibration/c3-presentation-spec.yaml',
    'visio-renderer/calibration/build_c3.py',
    'visio-renderer/calibration/validate_c3.py',
    'visio-renderer/calibration/c4-routing-calibration-spec.yaml',
    'visio-renderer/calibration/validate_c4_plan.py',
    'visio-renderer/calibration/build_c4_fallback.py',
    'visio-renderer/calibration/validate_c4_fallback.py',
    'visio-renderer/calibration/audit_c4_fallback_openxml.py',
    'visio-renderer/tests/test_c4_fallback_contract.py',
    'visio-renderer/tests/test_c4_fallback_direction_validator_contract.py',
    'visio-renderer/calibration/c4-extend-calibration-spec.yaml',
    'visio-renderer/calibration/build_c4_extend.py',
    'visio-renderer/calibration/validate_c4_extend.py',
    'visio-renderer/tests/test_c4_extend_contract.py',
    'visio-renderer/calibration/c4-extend-calibration-spec-v0.1.1.yaml',
    'visio-renderer/calibration/build_c4_extend_1.py',
    'visio-renderer/calibration/validate_c4_extend_1.py',
    'visio-renderer/tests/test_c4_extend_1_contract.py',
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main() -> int:
    records=[]
    missing=[]
    for rel in INPUTS:
        p=ROOT/rel
        if not p.exists(): missing.append(rel); continue
        records.append({'path': rel, 'sha256': sha(p), 'source': 'package'})
    payload={'rendererVersion':'v0.3.2','milestone':'C4_ASSOCIATION_FROZEN_EXTEND_REPAIR_0_1_1','inputs':records,'missing':missing}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=True,indent=2))
    return 1 if missing else 0

if __name__=='__main__':
    raise SystemExit(main())
