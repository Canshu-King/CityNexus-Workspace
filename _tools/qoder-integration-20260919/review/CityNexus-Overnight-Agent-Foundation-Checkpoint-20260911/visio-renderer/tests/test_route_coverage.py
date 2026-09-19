from pathlib import Path
import yaml


def test_all_p1_uc_connectors_have_exactly_one_route():
    root = Path(__file__).resolve().parents[2]
    page = yaml.safe_load((root / 'visio-spec' / 'pages' / 'p1_uc_overview.yaml').read_text(encoding='utf8'))
    routes = yaml.safe_load((root / 'visio-renderer' / 'phase1-routing.yaml').read_text(encoding='utf8'))
    expected = [item['id'] for item in page['connectors']]
    actual = [item['id'] for item in routes['routes']['P1_UC_Overview']]
    assert len(expected) == 21
    assert sorted(actual) == sorted(expected)
    assert len(actual) == len(set(actual))
