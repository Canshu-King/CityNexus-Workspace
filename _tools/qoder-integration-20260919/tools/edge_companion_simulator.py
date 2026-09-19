"""ESP8266/PIC16F877A compact-protocol simulator for the Edge Companion API."""

from __future__ import annotations

import argparse
import os
from typing import Any

import httpx


def snapshot_to_uart(snapshot: dict[str, Any]) -> str:
    fields = (
        ("SEQ", snapshot.get("sequence", 0)),
        ("NOW", snapshot.get("now_title", "")),
        ("NEXT", snapshot.get("next_title", "")),
        ("AT", snapshot.get("next_at") or ""),
        ("MODE", snapshot.get("mode", "NONE")),
        ("ETA", snapshot.get("eta_min", 0)),
        ("C4", snapshot.get("c4_countdown_min") if snapshot.get("c4_countdown_min") is not None else -1),
        ("RISK", snapshot.get("risk", "UNKNOWN")),
        ("STATE", snapshot.get("journey_state", "UNKNOWN")),
    )
    return "\n".join(f"{key}|{str(value)[:80]}" for key, value in fields)


def parse_pic_message(message: str) -> tuple[str, dict[str, Any]]:
    kind, separator, value = message.strip().partition("|")
    if not separator or not kind:
        raise ValueError("PIC message must use KIND|VALUE")
    normalized = kind.upper()
    if normalized in {"ACK", "REJECT", "BTN"}:
        action = {
            "ACK": "ACKNOWLEDGE",
            "REJECT": "REJECT_PROPOSAL",
            "BTN": "NEXT",
        }[normalized]
        return "action", {"action": action, "payload": {"value": value}}
    if normalized in {"SOS", "RAIN", "TEMP"}:
        return "observation", {"observation_type": normalized, "payload": {"value": value}}
    raise ValueError("PIC message is outside the Edge Companion protocol")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("device_id")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument(
        "--pic-message",
        help="Optional PIC-to-ESP message such as ACK|REPLAN or RAIN|1",
    )
    args = parser.parse_args()
    token = os.getenv("CITYNEXUS_EDGE_DEVICE_TOKEN")
    if not token:
        raise SystemExit("CITYNEXUS_EDGE_DEVICE_TOKEN is required")
    response = httpx.get(
        f"{args.base_url}/edge/devices/{args.device_id}/journey-snapshot",
        headers={"X-Edge-Token": token},
        timeout=10.0,
    )
    response.raise_for_status()
    print(snapshot_to_uart(response.json()))
    if args.pic_message:
        kind, payload = parse_pic_message(args.pic_message)
        endpoint = "actions" if kind == "action" else "observations"
        posted = httpx.post(
            f"{args.base_url}/edge/devices/{args.device_id}/{endpoint}",
            headers={"X-Edge-Token": token},
            json=payload,
            timeout=10.0,
        )
        posted.raise_for_status()
        print(f"POSTED|{kind.upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
