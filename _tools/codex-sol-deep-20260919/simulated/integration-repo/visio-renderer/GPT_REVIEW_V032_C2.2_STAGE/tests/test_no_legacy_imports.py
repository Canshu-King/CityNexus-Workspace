import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_source_has_no_legacy_imports():
    for path in ROOT.glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf8'), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(part.name != 'legacy' and not part.name.startswith('legacy.') for part in node.names), path
            if isinstance(node, ast.ImportFrom):
                assert not node.module or (node.module != 'legacy' and not node.module.startswith('legacy.')), path
