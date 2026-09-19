from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def runtime_paths() -> set[tuple[str, str]]:
    from app.main import app

    return {
        (route.path, method.upper())
        for route in app.routes
        for method in getattr(route, "methods", set())
        if route.path.startswith("/api/v1/") or route.path == "/api/v1"
    }


def formal_paths() -> set[tuple[str, str]]:
    spec = yaml.safe_load((ROOT / "contracts" / "openapi.yaml").read_text(encoding="utf-8"))
    result: set[tuple[str, str]] = set()
    for path, item in spec.get("paths", {}).items():
        runtime_path = "/api/v1" + (path if path != "/" else "")
        for method in item:
            if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}:
                result.add((runtime_path, method.upper()))
    return result


def main() -> int:
    formal = formal_paths()
    runtime = runtime_paths()
    missing = sorted(runtime - formal)
    extra = sorted(formal - runtime)
    print(
        f"OpenAPI 3.1.0; formal {len(formal)}; runtime {len(runtime)}; "
        f"missing {len(missing)}; extra {len(extra)}"
    )
    if missing:
        print("MISSING:", missing)
    if extra:
        print("EXTRA:", extra)
    return 1 if missing or extra else 0


if __name__ == "__main__":
    raise SystemExit(main())

