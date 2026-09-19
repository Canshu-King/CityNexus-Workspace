from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def main() -> int:
    repo = Path.cwd()
    if not (repo / "backend" / "app").exists():
        raise SystemExit("run this from the CityNexus repository root")
    sys.path.insert(0, str(repo / "backend"))

    from app.main import app  # noqa: PLC0415

    contract_path = repo / "contracts" / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    server_url = str((contract.get("servers") or [{"url": ""}])[0].get("url", ""))
    prefix = urlparse(server_url).path.rstrip("/")

    formal: set[tuple[str, str]] = set()
    for raw_path, path_item in (contract.get("paths") or {}).items():
        for raw_method in path_item:
            method = str(raw_method).lower()
            if method in HTTP_METHODS:
                formal.add((method.upper(), prefix + str(raw_path)))

    runtime: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not methods or not str(path).startswith(prefix + "/"):
            continue
        for method in methods:
            upper = str(method).upper()
            if upper.lower() in HTTP_METHODS:
                runtime.add((upper, str(path)))

    missing = sorted(formal - runtime)
    extra = sorted(runtime - formal)
    print(f"OpenAPI {contract.get('openapi')}; formal {len(formal)}; runtime {len(runtime)}")
    print(f"missing {len(missing)}; extra {len(extra)}")
    for item in missing:
        print("MISSING", *item)
    for item in extra:
        print("EXTRA", *item)
    return 1 if missing or extra else 0


if __name__ == "__main__":
    raise SystemExit(main())
