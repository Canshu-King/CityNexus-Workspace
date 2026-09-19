from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


@dataclass(frozen=True)
class ReplacementChoice:
    place_id: str
    title: str
    duration_min: int
    cost_minor: int
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionPartition:
    terminal_prefix_ids: tuple[str, ...]
    current_activity_id: str | None
    c4_anchor_ids: tuple[str, ...]
    mutable_suffix_ids: tuple[str, ...]


def partition_execution(
    activities: Iterable[Any],
    *,
    current_activity_id: str | None,
    c4_anchors: Iterable[tuple[str, str]],
) -> ExecutionPartition:
    """Partition an active plan into immutable/current/C4/mutable sets."""

    rows = sorted(activities, key=lambda item: (int(item.sequence_no), str(item.id)))
    anchors = {
        (str(key), datetime.fromisoformat(str(start)).isoformat()) for key, start in c4_anchors
    }
    terminal: list[str] = []
    protected: list[str] = []
    mutable: list[str] = []
    current: str | None = None
    for item in rows:
        activity_id = str(item.id)
        status = str(getattr(item, "status", ""))
        semantic = str(
            getattr(item, "place_id", None) or getattr(item, "city_service_id", None) or activity_id
        )
        start_at = datetime.fromisoformat(str(item.start_at)).isoformat()
        if status in {"COMPLETED", "SKIPPED", "CANCELLED"}:
            terminal.append(activity_id)
        elif activity_id == current_activity_id:
            current = activity_id
        elif (semantic, start_at) in anchors:
            protected.append(activity_id)
        else:
            mutable.append(activity_id)
    return ExecutionPartition(tuple(terminal), current, tuple(protected), tuple(mutable))


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
        place_id = str(place.id)
        if place_id in occupied_place_ids or place_id == str(affected_place.id):
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
            title=str(place.name),
            duration_min=duration,
            cost_minor=cost,
            reason_codes=(
                "DISRUPTED_ACTIVITY_REPLACED",
                "MINIMAL_SCHEDULE_CHANGE",
                *(("INDOOR_ALTERNATIVE",) if indoor else ()),
            ),
        )
        # Highest tag overlap, then indoor, then lower cost, then stable ID.
        rank = (-overlap, -indoor, cost, place_id)
        ranked.append((rank, choice))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0])
    return ranked[0][1]
