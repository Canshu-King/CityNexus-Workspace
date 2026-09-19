"""V4.1 visual reservation extraction; output remains a confirmation draft."""

from __future__ import annotations

import json
from typing import Any

from app.integrations.ai.responses import DeepSeekResponsesClient, DeepSeekResponsesError


def extract_reservation_image(
    client: DeepSeekResponsesClient, image_url: str, *, hint: str = "booking confirmation"
) -> dict[str, Any]:
    result = client.complete(
        [
            {
                "role": "system",
                "content": (
                    "Read this travel document image and return only JSON with reservation_type, "
                    "confirmation_ref, origin, destination, scheduled_departure_at, "
                    "scheduled_arrival_at, price_amount_minor, currency, and field_provenance. "
                    "Use null or UNKNOWN when unreadable. Never guess a confirmation number or price. "
                    "Every critical field needs source=image and status=EXTRACTED or UNKNOWN."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": hint},
                    {"type": "input_image", "image_url": image_url},
                ],
            },
        ],
        reasoning_effort="low",
        json_mode=True,
    )
    try:
        parsed = json.loads(result.text)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DeepSeekResponsesError("visual reservation extraction was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise DeepSeekResponsesError("visual reservation extraction was not an object")
    return parsed


def extract_reservation_text(client: DeepSeekResponsesClient, text: str) -> dict[str, Any]:
    result = client.complete(
        [
            {
                "role": "system",
                "content": (
                    "Extract a travel reservation from pasted text. Return only JSON with "
                    "reservation_type, confirmation_ref, origin, destination, "
                    "scheduled_departure_at, scheduled_arrival_at, price_amount_minor, currency, "
                    "and field_provenance. Use null or UNKNOWN when absent. Never invent facts."
                ),
            },
            {"role": "user", "content": text},
        ],
        reasoning_effort="low",
        json_mode=True,
    )
    try:
        parsed = json.loads(result.text)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DeepSeekResponsesError("text reservation extraction was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise DeepSeekResponsesError("text reservation extraction was not an object")
    return parsed
