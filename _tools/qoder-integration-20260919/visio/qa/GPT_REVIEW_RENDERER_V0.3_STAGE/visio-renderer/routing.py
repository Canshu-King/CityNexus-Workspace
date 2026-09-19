"""Deterministic route metadata; semantics remain in page YAML."""
import yaml, os
def load_routes(path):
    if not os.path.exists(path): return {}
    return yaml.safe_load(open(path,encoding='utf8')) or {}
