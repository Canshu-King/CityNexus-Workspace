"""Capture normalized mobility evidence for deterministic replay.

The command never writes API keys or unredacted provider headers. With a live
Valhalla URL configured the snapshot is labeled LIVE_CAPTURE; otherwise the
existing deterministic provider is explicitly labeled SYNTHETIC_FIXTURE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import pairwise
from pathlib import Path

from app.core.config import settings
from app.db.models import Activity, Journey
from app.db.session import SessionLocal, ensure_schema
from app.integrations.mobility.replay import load_sealed_provider_capture
from app.integrations.mobility.runtime import capture_runtime_mobility_snapshot
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--journey")
    parser.add_argument("--output", default="data/replay/provider_capture_v10.json")
    parser.add_argument("--replay")
    parser.add_argument("--allow-synthetic-replay", action="store_true")
    args = parser.parse_args()
    if args.replay:
        snapshot = load_sealed_provider_capture(
            args.replay, allow_synthetic=args.allow_synthetic_replay
        )
        print(
            f"REPLAYED {args.replay} provider={snapshot.source_provider_key} "
            f"facts={len(snapshot.facts)}"
        )
        return 0
    if not args.journey:
        raise SystemExit("--journey is required unless --replay is provided")
    ensure_schema()
    with SessionLocal() as session:
        journey = session.get(Journey, args.journey)
        if journey is None or not journey.active_plan_version_id:
            raise SystemExit("journey must exist with an active plan")
        activities = session.scalars(
            select(Activity)
            .where(Activity.plan_version_id == journey.active_plan_version_id)
            .order_by(Activity.sequence_no)
        ).all()
        pairs = tuple(
            (left.place_id or left.city_service_id or "", right.place_id or right.city_service_id or "")
            for left, right in pairwise(activities)
        )
        result = capture_runtime_mobility_snapshot(
            session, journey, pairs, operation_key=f"v10-capture:{journey.id}"
        )
        payload = result.snapshot.to_evidence()
        payload["provenance"] = "LIVE_CAPTURE" if settings.live_valhalla_url else "SYNTHETIC_FIXTURE"
        payload["redaction"] = {"authorization_headers": "omitted", "raw_provider_body": "omitted"}
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload["checksum"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {output} provenance={payload['provenance']} facts={len(payload['facts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
