from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ReplacementChoice:
    place_id: str
    title: str
    duration_min: int
    cost_minor: int
    reason_codes: tuple[str, ...]


def _json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def choose_closure_replacement(
    *,
    affected_place: Any,
    candidate_places: Iterable[Any],
    occupied_place_ids: set[str],
    max_duration_min: int,
) -> ReplacementChoice | None:
    """Choose one deterministic same-slot replacement for a closed flexible place.

    This is a mock candidate-family generator, not the feasibility authority.
    The returned candidate must still pass the shared deterministic gate.
    """

    affected_tags = set(_json(getattr(affected_place, "tags_json", "[]"), []))
    ranked: list[tuple[tuple[int, int, int, str], ReplacementChoice]] = []
    for place in candidate_places:
        place_id = str(getattr(place, "id"))
        if place_id in occupied_place_ids or place_id == str(getattr(affected_place, "id")):
            continue
        meta = _json(getattr(place, "metadata_json", "{}"), {})
        tags = set(_json(getattr(place, "tags_json", "[]"), []))
        duration = int(meta.get("duration_min", 60))
        cost = int(meta.get("cost_minor", 0))
        if duration <= 0 or duration > max_duration_min:
            continue
        overlap = len(affected_tags & tags)
        indoor = 1 if "indoor" in tags else 0
        choice = ReplacementChoice(
            place_id=place_id,
            title=str(getattr(place, "name")),
            duration_min=duration,
            cost_minor=cost,
            reason_codes=(
                "DISRUPTED_ACTIVITY_REPLACED",
                "MINIMAL_SCHEDULE_CHANGE",
                *(('INDOOR_ALTERNATIVE',) if indoor else ()),
            ),
        )
        # Highest tag overlap, then indoor, then lower cost, then stable ID.
        rank = (-overlap, -indoor, cost, place_id)
        ranked.append((rank, choice))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0])
    return ranked[0][1]
