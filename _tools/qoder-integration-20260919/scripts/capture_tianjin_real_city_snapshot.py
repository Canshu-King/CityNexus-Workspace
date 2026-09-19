"""Capture a bounded, sanitized real-city provider bundle for sealed replay.

The output contains only provider facts needed by CityNexus planning. It never
copies credentials or raw HTTP headers into the fixture.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def _hours(raw: Any) -> dict[str, Any]:
    value = str(raw or "").strip()
    if not value:
        return {"status": "UNKNOWN", "raw": None, "intervals": []}
    if value.casefold() == "24/7":
        return {
            "status": "NORMALIZED_VALID",
            "raw": value,
            "open": "00:00",
            "close": "24:00",
            "intervals": [{"open": "00:00", "close": "24:00"}],
        }
    import re

    matches = re.findall(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", value)
    intervals = [{"open": start, "close": end} for start, end in matches]
    if not intervals:
        return {"status": "RAW_UNPARSED", "raw": value, "intervals": []}
    return {
        "status": "NORMALIZED_VALID",
        "raw": value,
        "open": intervals[0]["open"],
        "close": intervals[0]["close"],
        "intervals": intervals,
    }


def capture(output: Path, *, anchor_override: dict[str, Any] | None = None) -> dict[str, Any]:
    captured_at = datetime.now(timezone.utc).isoformat()
    timeout = float(os.getenv("CITYNEXUS_REAL_CITY_TIMEOUT_SECONDS", "12"))
    nominatim = os.getenv("CITYNEXUS_NOMINATIM_URL", "https://nominatim.openstreetmap.org")
    overpass = os.getenv("CITYNEXUS_OVERPASS_URL", "https://overpass-api.de/api")
    open_meteo = os.getenv("CITYNEXUS_OPEN_METEO_URL", "https://api.open-meteo.com")
    valhalla = os.getenv("CITYNEXUS_VALHALLA_URL", "https://valhalla1.openstreetmap.de")
    result: dict[str, Any] = {
        "schema_version": "citynexus.real-city.snapshot.v1",
        "city_code": "TSN",
        "city_name": "Tianjin",
        "captured_at": captured_at,
        "providers": {},
        "anchor": None,
        "candidates": [],
        "evidence_completion": [],
        "weather": None,
        "mobility": {"status": "NOT_CAPTURED", "facts": []},
        "map": {"provider": "OpenFreeMap", "style_url": "https://tiles.openfreemap.org/styles/liberty"},
    }
    headers = {"User-Agent": "CityNexus/7.0 real-city snapshot"}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        if anchor_override:
            result["anchor"] = {
                "latitude": float(anchor_override["latitude"]),
                "longitude": float(anchor_override["longitude"]),
                "display_name": str(anchor_override.get("display_name") or "Journey anchor"),
                "provider": "journey-memory",
                "source": str(anchor_override.get("source") or "journey_memory"),
            }
            result["providers"]["nominatim"] = "SKIPPED_JOURNEY_ANCHOR"
        else:
            try:
                rows = client.get(
                    f"{nominatim.rstrip('/')}/search",
                    params={"q": "Tianjin, China", "format": "jsonv2", "limit": 1},
                ).json()
                anchor = rows[0] if rows else None
                if anchor:
                    result["anchor"] = {
                        "latitude": float(anchor["lat"]),
                        "longitude": float(anchor["lon"]),
                        "display_name": str(anchor.get("display_name") or "Tianjin"),
                        "provider": "nominatim",
                    }
                    result["providers"]["nominatim"] = "CAPTURED"
                else:
                    result["providers"]["nominatim"] = "NO_RESULTS"
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                result["providers"]["nominatim"] = f"FAILED:{type(exc).__name__}"

        anchor = result["anchor"]
        if anchor:
            query = (
                "[out:json][timeout:10];"
                "nwr[amenity~\"cafe|restaurant|library|arts_centre|theatre|museum\"]"
                f"(around:5000,{anchor['latitude']},{anchor['longitude']});out center tags;"
            )
            try:
                elements = client.post(f"{overpass.rstrip('/')}/interpreter", content=query).json().get(
                    "elements", []
                )
                for element in elements[:40]:
                    tags = element.get("tags") or {}
                    center = element.get("center") or element
                    try:
                        latitude = float(center["lat"])
                        longitude = float(center["lon"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    category = str(
                        tags.get("amenity") or tags.get("leisure") or tags.get("tourism") or "service"
                    )
                    result["candidates"].append(
                        {
                            "provider": "overpass",
                            "external_id": f"{element.get('type', 'n')}/{element.get('id')}",
                            "name": str(tags.get("name") or f"OSM {category}"),
                            "category": category,
                            "latitude": latitude,
                            "longitude": longitude,
                            "tags": tags,
                            "opening_hours": _hours(tags.get("opening_hours")),
                            "cost_evidence": {"status": "UNKNOWN", "currency": "CNY", "source": "overpass"},
                        }
                    )
                    result["providers"]["overpass"] = "CAPTURED"
                if not result["candidates"]:
                    result["providers"]["overpass"] = "NO_RESULTS"
                    nominatim_rows = client.get(
                        f"{nominatim.rstrip('/')}/search",
                        params={
                            "q": "museum Tianjin China",
                            "format": "jsonv2",
                            "limit": 12,
                            "addressdetails": 1,
                        },
                    ).json()
                    for row in nominatim_rows:
                        try:
                            latitude = float(row["lat"])
                            longitude = float(row["lon"])
                        except (KeyError, TypeError, ValueError):
                            continue
                        result["candidates"].append(
                            {
                                "provider": "nominatim",
                                "external_id": f"{row.get('osm_type', 'place')}/{row.get('osm_id', row.get('place_id'))}",
                                "name": str(row.get("display_name") or "Tianjin museum").split(",")[0],
                                "category": str(row.get("type") or "museum"),
                                "latitude": latitude,
                                "longitude": longitude,
                                "tags": {"tourism": "museum", "name": row.get("display_name")},
                                "opening_hours": {"status": "UNKNOWN", "raw": None, "intervals": []},
                                "cost_evidence": {"status": "UNKNOWN", "currency": "CNY", "source": "nominatim"},
                            }
                        )
                    result["providers"]["nominatim_candidates"] = "CAPTURED"
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                result["providers"]["overpass"] = f"FAILED:{type(exc).__name__}"

        if anchor:
            try:
                route_nodes = [
                    {
                        "key": "journey-anchor",
                        "latitude": float(anchor["latitude"]),
                        "longitude": float(anchor["longitude"]),
                    }
                ]
                for candidate in result["candidates"]:
                    if len(route_nodes) >= 8:
                        break
                    route_nodes.append(
                        {
                            "key": str(candidate["external_id"]),
                            "latitude": float(candidate["latitude"]),
                            "longitude": float(candidate["longitude"]),
                        }
                    )
                matrix_payload = {
                    "sources": [
                        {"lat": item["latitude"], "lon": item["longitude"]}
                        for item in route_nodes
                    ],
                    "targets": [
                        {"lat": item["latitude"], "lon": item["longitude"]}
                        for item in route_nodes
                    ],
                    "costing": "auto",
                    "units": "kilometers",
                }
                matrix = client.post(
                    f"{valhalla.rstrip('/')}/sources_to_targets",
                    json=matrix_payload,
                ).json()
                rows = matrix.get("sources_to_targets") or []
                facts = []
                for source_index, row in enumerate(rows):
                    for cell in row or []:
                        if not isinstance(cell, dict):
                            continue
                        facts.append(
                            {
                                "from_key": route_nodes[source_index]["key"],
                                "to_key": route_nodes[int(cell.get("to_index", 0))]["key"],
                                "duration_min": round(float(cell.get("time", 0)) / 60),
                                "distance_km": float(cell.get("distance", 0)),
                                "from_index": source_index,
                                "to_index": int(cell.get("to_index", 0)),
                            }
                        )
                result["mobility"] = {
                    "status": "CAPTURED" if facts else "NO_RESULTS",
                    "provider": "valhalla",
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "nodes": route_nodes,
                    "facts": facts,
                }
                result["providers"]["valhalla"] = "CAPTURED" if facts else "NO_RESULTS"
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                result["mobility"] = {
                    "status": "FAILED",
                    "provider": "valhalla",
                    "facts": [],
                    "error_type": type(exc).__name__,
                }
                result["providers"]["valhalla"] = f"FAILED:{type(exc).__name__}"

        if anchor:
            try:
                weather = client.get(
                    f"{open_meteo.rstrip('/')}/v1/forecast",
                    params={
                        "latitude": anchor["latitude"],
                        "longitude": anchor["longitude"],
                        "hourly": "precipitation_probability,weather_code",
                        "forecast_days": 1,
                        "timezone": "Asia/Shanghai",
                    },
                ).json()
                result["weather"] = {
                    "provider": "open-meteo",
                    "hourly": weather.get("hourly", {}),
                }
                result["providers"]["open-meteo"] = "CAPTURED"
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                result["providers"]["open-meteo"] = f"FAILED:{type(exc).__name__}"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "replay" / "tianjin_real_snapshot.json",
    )
    parser.add_argument("--anchor-lat", type=float)
    parser.add_argument("--anchor-lon", type=float)
    parser.add_argument("--anchor-label", default="Journey-derived Tianjin anchor")
    args = parser.parse_args()
    anchor_override = None
    if args.anchor_lat is not None and args.anchor_lon is not None:
        anchor_override = {
            "latitude": args.anchor_lat,
            "longitude": args.anchor_lon,
            "display_name": args.anchor_label,
            "source": "journey_memory",
        }
    result = capture(args.output, anchor_override=anchor_override)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "captured_at": result["captured_at"],
                "providers": result["providers"],
                "candidate_count": len(result["candidates"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
