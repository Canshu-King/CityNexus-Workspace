"""Create the deterministic CityNexus mock catalog and canonical journey."""

from __future__ import annotations

import json

from app.db.session import SessionLocal, ensure_schema
from app.services import seed_demo


def main() -> None:
    ensure_schema()
    with SessionLocal() as session:
        print(json.dumps(seed_demo(session), sort_keys=True))


if __name__ == "__main__":
    main()
