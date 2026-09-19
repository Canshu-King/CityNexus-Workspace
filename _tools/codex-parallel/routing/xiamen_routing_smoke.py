#!/usr/bin/env python3
"""Opt-in Valhalla preflight for Xiamen route pairs.

This tool talks directly to a caller-supplied Valhalla URL. It does not modify
CityNexus configuration, deploy services, or attach credentials. Unverified
coordinates are rejected unless the operator explicitly opts in.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

PROVIDER = "valhalla-http"
EXPECTED_FACT_QUALITY = "LIVE_PROVIDER_CAPTURE"
VERIFIED_STATUSES = {"PROJECT_KNOWN", "OPERATOR_VERIFIED"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None,
                 timeout: float = 10.0) -> tuple[int, dict[str, Any], float]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, method=method, headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except HTTPError as exc:
        raw = exc.read()
        status = exc.code
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"non-JSON response from {url}: HTTP {status}") from exc
    if not isinstance(decoded, dict):
        raise RuntimeError(f"response from {url} is not a JSON object")
    if status < 200 or status >= 300:
        raise RuntimeError(f"HTTP {status} from {url}: {decoded}")
    return status, decoded, duration_ms


def validate_point(point: dict[str, Any]) -> None:
    for key in ("lat", "lon"):
        value = point.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"point {point.get('id')} has invalid {key}")
    if not (-90 <= point["lat"] <= 90 and -180 <= point["lon"] <= 180):
        raise ValueError(f"point {point.get('id')} is outside coordinate bounds")


def load_pairs(path: Path, allow_unverified: bool) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    points = {item["id"]: item for item in data["points"]}
    for point in points.values():
        validate_point(point)
        status = point.get("verification_status", "UNVERIFIED")
        if status not in VERIFIED_STATUSES and not allow_unverified:
            raise ValueError(
                f"point {point['id']} is {status}; verify coordinates or pass "
                "--allow-unverified-coordinates explicitly"
            )
    pairs = [item for item in data["pairs"] if item.get("enabled", True)]
    for pair in pairs:
        if pair["origin"] not in points or pair["destination"] not in points:
            raise ValueError(f"pair {pair.get('id')} references an unknown point")
    return points, pairs


def compact_route_response(response: dict[str, Any]) -> dict[str, Any]:
    trip = response.get("trip") if isinstance(response.get("trip"), dict) else {}
    summary = trip.get("summary") if isinstance(trip.get("summary"), dict) else {}
    legs = trip.get("legs") if isinstance(trip.get("legs"), list) else []
    return {
        "trip_status": trip.get("status"),
        "summary": summary,
        "leg_count": len(legs),
        "shape_present": any(isinstance(x, dict) and bool(x.get("shape")) for x in legs),
        "raw": response,
    }


def run(base_url: str, config: Path, output_dir: Path, timeout: float,
        costing: str, allow_unverified: bool) -> dict[str, Any]:
    points, pairs = load_pairs(config, allow_unverified)
    base = base_url.rstrip("/") + "/"
    result: dict[str, Any] = {
        "schema_version": 1,
        "captured_at": now_utc(),
        "provider": PROVIDER,
        "base_url": base_url,
        "credential_headers_sent": False,
        "citynexus_expected_fact_quality": EXPECTED_FACT_QUALITY,
        "important_boundary": (
            "Direct provider observations are not CityNexus frozen facts. "
            "The application capture path must persist provenance separately."
        ),
        "status": None,
        "routes": [],
        "errors": [],
    }
    try:
        code, payload, duration = request_json(urljoin(base, "status"), timeout=timeout)
        result["status"] = {"http_status": code, "duration_ms": duration, "response": payload}
    except (RuntimeError, URLError, TimeoutError) as exc:
        result["errors"].append({"stage": "status", "error": str(exc)})

    for pair in pairs:
        origin = points[pair["origin"]]
        destination = points[pair["destination"]]
        payload = {
            "locations": [
                {"lat": origin["lat"], "lon": origin["lon"]},
                {"lat": destination["lat"], "lon": destination["lon"]},
            ],
            "costing": pair.get("costing", costing),
            "units": "kilometers",
        }
        observation: dict[str, Any] = {
            "pair_id": pair["id"],
            "origin": pair["origin"],
            "destination": pair["destination"],
            "request": payload,
            "provider": PROVIDER,
            "observed_at": now_utc(),
        }
        try:
            code, response, duration = request_json(
                urljoin(base, "route"), method="POST", payload=payload, timeout=timeout
            )
            compact = compact_route_response(response)
            summary = compact["summary"]
            seconds = summary.get("time")
            if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
                raise RuntimeError("route summary.time is missing or invalid")
            observation.update({
                "ok": True,
                "http_status": code,
                "duration_ms": duration,
                "duration_min_ceil": math.ceil(seconds / 60),
                "distance_km": summary.get("length"),
                "response": compact,
            })
        except (RuntimeError, URLError, TimeoutError) as exc:
            observation.update({"ok": False, "error": str(exc)})
            result["errors"].append({"stage": "route", "pair_id": pair["id"], "error": str(exc)})
        result["routes"].append(observation)

    result["ok"] = not result["errors"] and bool(result["routes"])
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "xiamen-routing-smoke.json"
    md_path = output_dir / "xiamen-routing-smoke.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Xiamen routing smoke result", "",
        f"- Captured: `{result['captured_at']}`",
        f"- Provider: `{PROVIDER}`",
        f"- Overall: `{'PASS' if result['ok'] else 'FAIL'}`",
        f"- Credential headers sent: `{result['credential_headers_sent']}`", "",
        "| Pair | Result | Duration | Route minutes | Distance km |", "| --- | --- | ---: | ---: | ---: |",
    ]
    for item in result["routes"]:
        lines.append(
            f"| {item['pair_id']} | {'PASS' if item['ok'] else 'FAIL'} | "
            f"{item.get('duration_ms', '-')} ms | {item.get('duration_min_ceil', '-')} | "
            f"{item.get('distance_km', '-')} |"
        )
    lines.extend(["", "Direct observations are not frozen CityNexus mobility facts."])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


class StubHandler(BaseHTTPRequestHandler):
    def log_message(self, *_: Any) -> None:
        return

    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._send({"version": "stub-1", "has_live_traffic": False})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        json.loads(self.rfile.read(length) or b"{}")
        self._send({"trip": {"status": 0, "summary": {"time": 725, "length": 4.2}, "legs": [{"shape": "stub"}]}})


def self_test(output_dir: Path) -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = output_dir / "self-test-pairs.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({
        "points": [
            {"id": "a", "lat": 24.4581979, "lon": 118.0689473, "verification_status": "PROJECT_KNOWN"},
            {"id": "b", "lat": 24.4590, "lon": 118.0700, "verification_status": "PROJECT_KNOWN"},
        ],
        "pairs": [{"id": "stub-a-b", "origin": "a", "destination": "b"}],
    }, indent=2), encoding="utf-8")
    try:
        result = run(f"http://127.0.0.1:{server.server_port}", config, output_dir, 2.0, "pedestrian", False)
        return 0 if result["ok"] and result["routes"][0]["duration_min_ceil"] == 13 else 1
    finally:
        server.shutdown()
        server.server_close()


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("CITYNEXUS_LIVE_VALHALLA_URL"))
    parser.add_argument("--pairs", type=Path, default=here / "xiamen_route_pairs.json")
    parser.add_argument("--output-dir", type=Path, default=here / "out")
    parser.add_argument("--timeout", type=float, default=float(os.getenv("CITYNEXUS_ROUTING_TIMEOUT_SECONDS", "10")))
    parser.add_argument("--costing", default=os.getenv("CITYNEXUS_ROUTING_COSTING", "pedestrian"))
    parser.add_argument("--allow-unverified-coordinates", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test(args.output_dir)
    if not args.base_url:
        print("Missing --base-url or CITYNEXUS_LIVE_VALHALLA_URL", file=sys.stderr)
        return 2
    try:
        result = run(args.base_url, args.pairs, args.output_dir, args.timeout, args.costing,
                     args.allow_unverified_coordinates)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

