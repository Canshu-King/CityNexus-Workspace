"""Write the bounded v0.3.1 C1 review manifest."""
import hashlib
import json
import os


HERE = os.path.dirname(__file__)
RENDERER = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(RENDERER, '..'))
OUT = os.path.join(HERE, 'out')
FILES = [
    'build_calibrations.py',
    'render_core.py',
    'style_adapter.py',
    'class_adapter.py',
    'presentation.py',
    'routing.py',
    'render_phase1.py',
    'native-master-map.json',
    'phase1-routing.yaml',
    'calibration/validate_c1.py',
    'tests/test_no_legacy_imports.py',
    'tests/test_style_resolution.py',
    'tests/test_coordinate_conversion.py',
    'tests/test_route_coverage.py',
    'calibration/out/C1_Font_Style.vsdx',
    'calibration/out/C1_Font_Style.svg',
    'calibration/out/C1_Font_Style.png',
    'calibration/out/C1_Font_Style-report.json',
    'calibration/out/calibration-summary.json',
    'calibration/out/static-test-report.json',
]


def entry(relative):
    path = os.path.join(RENDERER, relative.replace('/', os.sep))
    with open(path, 'rb') as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    return {'path': relative, 'bytes': os.path.getsize(path), 'sha256': digest}


manifest = {
    'release': 'Visio Renderer v0.3.1',
    'scope': 'C1 true font/style calibration only',
    'formalPagesRendered': False,
    'calibration': {'C1': 'PASS', 'C2': 'BLOCKED', 'C3': 'BLOCKED', 'C4': 'BLOCKED'},
    'files': [entry(relative) for relative in FILES],
}
with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf8') as handle:
    json.dump(manifest, handle, indent=2)
