"""Capture the V13.5 Journey-shaped Tianjin provider snapshot."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def _matrix(client: httpx.Client, base_url: str, nodes: list[dict[str, Any]], costing: str) -> list[dict[str, Any]]:
    locations = [{"lat": item["latitude"], "lon": item["longitude"]} for item in nodes]
    response = client.post(
        f"{base_url.rstrip('/')}/sources_to_targets",
        json={"sources": locations, "targets": locations, "costing": costing, "units": "kilometers", "verbose": False},
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("sources_to_targets")
    if isinstance(rows, dict):
        nested_rows = rows.get("sources_to_targets") or rows.get("cells")
        if isinstance(nested_rows, list):
            rows = nested_rows
        else:
            durations = rows.get("durations")
            distances = rows.get("distances")
            if isinstance(durations, list):
                facts: list[dict[str, Any]] = []
                for source_index, row in enumerate(durations):
                    for target_index, seconds in enumerate(row):
                        if seconds is None:
                            continue
                        facts.append(
                            {
                                "from_key": nodes[source_index]["key"],
                                "to_key": nodes[target_index]["key"],
                                "mode": "WALK" if costing == "pedestrian" else "AUTO",
                                "duration_min": round(float(seconds) / 60),
                                "distance_km": float(distances[source_index][target_index])
                                if isinstance(distances, list)
                                else 0.0,
                            }
                        )
                return facts
    facts: list[dict[str, Any]] = []
    if isinstance(rows, list):
        for source_index, row in enumerate(rows):
            for positional_index, cell in enumerate(row or []):
                if not isinstance(cell, dict):
                    continue
                target_index = int(cell.get("to_index", positional_index))
                facts.append(
                    {
                        "from_key": nodes[source_index]["key"],
                        "to_key": nodes[target_index]["key"],
                        "mode": "WALK" if costing == "pedestrian" else "AUTO",
                        "duration_min": round(float(cell.get("time", 0)) / 60),
                        "distance_km": float(cell.get("distance", 0)),
                    }
                )
        return facts
    durations = payload.get("durations")
    if not isinstance(durations, list):
        raise ValueError("Valhalla matrix has no route cells")
    for source_index, row in enumerate(durations):
        for target_index, seconds in enumerate(row):
            if seconds is None:
                continue
            facts.append(
                {
                    "from_key": nodes[source_index]["key"],
                    "to_key": nodes[target_index]["key"],
                    "mode": "WALK" if costing == "pedestrian" else "AUTO",
                    "duration_min": round(float(seconds) / 60),
                    "distance_km": 0.0,
                }
            )
    return facts


def capture(output: Path, base_snapshot: Path) -> dict[str, Any]:
    base = json.loads(base_snapshot.read_text(encoding="utf-8"))
    captured_at = datetime.now(timezone.utc).isoformat()
    nodes: list[dict[str, Any]] = [
        {
            "key": "anchor:arrival",
            "role": "ARRIVAL",
            "anchor_key": "ARRIVAL",
            "latitude": 39.112,
            "longitude": 117.198,
        },
        {
            "key": "commitment:place-river-cruise",
            "role": "COMMITMENT",
            "place_id": "place-river-cruise",
            "latitude": 39.1200,
            "longitude": 117.2100,
        },
        {
            "key": "anchor:departure",
            "role": "DEPARTURE",
            "anchor_key": "DEPARTURE",
            "latitude": 39.112,
            "longitude": 117.198,
        },
    ]
    for candidate in base.get("candidates", []):
        nodes.append(
            {
                "key": f"place:{candidate['external_id']}",
                "role": "ACTIVITY",
                "external_id": candidate["external_id"],
                "latitude": float(candidate["latitude"]),
                "longitude": float(candidate["longitude"]),
            }
        )
    valhalla = os.getenv("CITYNEXUS_VALHALLA_URL", "https://valhalla1.openstreetmap.de")
    facts: list[dict[str, Any]] = []
    providers: dict[str, str] = dict(base.get("providers") or {})
    with httpx.Client(timeout=float(os.getenv("CITYNEXUS_REAL_CITY_TIMEOUT_SECONDS", "20")), headers={"User-Agent": "CityNexus/13.5 journey capture"}) as client:
        for costing in ("pedestrian", "auto"):
            mode_facts = _matrix(client, valhalla, nodes, costing)
            for fact in mode_facts:
                fact.update(
                    {
                        "captured_at": captured_at,
                        "route_provider": "valhalla",
                        "route_provenance": "CAPTURED_REPLAY",
                        "cost_provenance": "CITYNEXUS_COST_ESTIMATE",
                        "time_basis": "VALHALLA_SOURCES_TO_TARGETS_CAPTURED_AT",
                    }
                )
            facts.extend(mode_facts)
            providers[f"valhalla_{costing}"] = "CAPTURED"
    mobility = {
        "status": "CAPTURED",
        "provider": "valhalla",
        "captured_at": captured_at,
        "journey_shape": "ARRIVAL -> candidate/commitment -> DEPARTURE",
        "nodes": nodes,
        "facts": facts,
        "supported_modes": ["WALK", "AUTO"],
        "route_provenance": "CAPTURED_REPLAY",
        "cost_provenance": "CITYNEXUS_COST_ESTIMATE",
        "time_basis": "VALHALLA_SOURCES_TO_TARGETS_CAPTURED_AT",
    }
    weather = dict(base.get("weather") or {})
    weather["time_basis"] = "OPEN_METEO_HOURLY_LOCAL_TIME_SEALED"
    weather["timezone"] = "Asia/Shanghai"
    result = {
        **base,
        "schema_version": "citynexus.real-city.snapshot.v135",
        "captured_at": captured_at,
        "providers": providers,
        "mobility": mobility,
        "weather": weather,
        "capture_contract": {
            "journey_specific_structural_nodes": True,
            "route_provider": "valhalla",
            "route_provenance": "CAPTURED_REPLAY",
            "cost_provenance": "CITYNEXUS_COST_ESTIMATE",
            "supported_modes": ["WALK", "AUTO"],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--base",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "replay" / "tianjin_real_snapshot.json",
    )
    args = parser.parse_args()
    result = capture(args.output, args.base)
    print(json.dumps({"output": str(args.output), "captured_at": result["captured_at"], "fact_count": len(result["mobility"]["facts"]), "providers": result["providers"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
