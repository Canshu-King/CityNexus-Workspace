from pathlib import Path
import sys
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from style_adapter import resolve_style


def test_all_calibration_styles_resolve_to_hex_colours():
    root = Path(__file__).resolve().parents[2]
    tokens = yaml.safe_load((root / 'visio-spec' / 'style-tokens.yaml').read_text(encoding='utf8'))
    for ref in ('actorHuman', 'actorExternal', 'useCaseDefault', 'useCasePlanning', 'useCaseCommerce', 'classDefault', 'classJourney', 'classProjection', 'classPlanning', 'classCommerce', 'classEvent'):
        style = resolve_style(ref, tokens)
        assert all(style[key].startswith('#') and len(style[key]) == 7 for key in ('fill', 'stroke', 'text'))
