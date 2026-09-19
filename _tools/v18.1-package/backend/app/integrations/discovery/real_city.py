from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    AccommodationOfferSnapshot,
    Activity,
    CityService,
    Commitment,
    Journey,
    JourneyTripContext,
    Place,
    ProviderCall,
    RealPlaceCandidate,
    StayJourneyOption,
    WebObservation,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _external_id(provider: str, value: str) -> str:
    return f"{provider}:{value}"[:180]


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


_TIME_PATTERN = re.compile(r"(?P<open>\d{1,2}(?::\d{2})?)\s*[-–]\s*(?P<close>\d{1,2}(?::\d{2})?)")
_DAY_PATTERN = re.compile(
    r"^(?P<days>(?:Mo|Mon|Tu|Tue|We|Wed|Th|Thu|Fr|Fri|Sa|Sat|Su|Sun)"
    r"(?:\s*[-–]\s*(?:Mo|Mon|Tu|Tue|We|Wed|Th|Thu|Fr|Fri|Sa|Sat|Su|Sun))?)\s+(?P<times>.+)$",
    re.IGNORECASE,
)
_DAY_NAMES = {
    "mo": "Mo",
    "mon": "Mo",
    "tu": "Tu",
    "tue": "Tu",
    "we": "We",
    "wed": "We",
    "th": "Th",
    "thu": "Th",
    "fr": "Fr",
    "fri": "Fr",
    "sa": "Sa",
    "sat": "Sa",
    "su": "Su",
    "sun": "Su",
}


def _expand_days(raw: str) -> list[str]:
    parts = [item.strip().lower() for item in re.split(r"\s*[-–]\s*", raw)]
    normalized = [_DAY_NAMES[item] for item in parts]
    if len(normalized) == 1:
        return normalized
    order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    start, end = order.index(normalized[0]), order.index(normalized[1])
    if start <= end:
        return order[start : end + 1]
    return order[start:] + order[: end + 1]


def normalize_opening_hours(raw: Any) -> dict[str, Any]:
    """Normalize common OSM hours without treating unknown text as all-day."""

    if isinstance(raw, dict):
        if raw.get("status") in {
            "NORMALIZED_VALID",
            "CLOSED",
            "UNKNOWN",
            "RAW_UNPARSED",
            "OFFICIAL_WEB_VERIFIED",
            "VERIFIED_PROVIDER",
            "CONFLICTING",
        }:
            return dict(raw)
        raw_text = raw.get("raw") or (
            f"{raw.get('open')}-{raw.get('close')}" if raw.get("open") and raw.get("close") else ""
        )
    else:
        raw_text = str(raw or "").strip()
    raw_text = str(raw_text).strip()
    if not raw_text:
        return {"status": "UNKNOWN", "raw": None, "intervals": []}
    if raw_text.casefold() in {"off", "closed", "休息", "关闭"}:
        return {"status": "CLOSED", "raw": raw_text, "intervals": []}
    if raw_text.casefold() in {"24/7", "always", "全天"}:
        return {
            "status": "NORMALIZED_VALID",
            "raw": raw_text,
            "open": "00:00",
            "close": "24:00",
            "intervals": [{"open": "00:00", "close": "24:00"}],
        }
    intervals: list[dict[str, Any]] = []
    weekday_intervals: list[dict[str, Any]] = []
    segments = [segment.strip() for segment in re.split(r"\s*;\s*", raw_text) if segment.strip()]
    for segment in segments:
        day_match = _DAY_PATTERN.match(segment)
        days = _expand_days(day_match.group("days")) if day_match else ["*"]
        times_text = day_match.group("times") if day_match else segment
        segment_intervals: list[dict[str, str]] = []
        for match in _TIME_PATTERN.finditer(times_text):
            open_value = match.group("open")
            close_value = match.group("close")
            if ":" not in open_value:
                open_value = f"{open_value}:00"
            if ":" not in close_value:
                close_value = f"{close_value}:00"
            try:
                if not (0 <= int(open_value[:2]) <= 23 and 0 <= int(close_value[:2]) <= 24):
                    continue
            except ValueError:
                continue
            interval = {"open": open_value, "close": close_value}
            segment_intervals.append(interval)
            intervals.append({**interval, "days": days})
        if segment_intervals:
            weekday_intervals.append({"days": days, "intervals": segment_intervals})
    if not intervals:
        return {"status": "RAW_UNPARSED", "raw": raw_text, "intervals": []}
    first = intervals[0]
    return {
        "status": "NORMALIZED_VALID",
        "raw": raw_text,
        "open": first["open"],
        "close": first["close"],
        "intervals": intervals,
        "weekday_intervals": weekday_intervals,
    }


def cost_evidence_from_tags(tags: dict[str, Any] | None, *, source: str) -> dict[str, Any]:
    values = tags or {}
    currency = str(values.get("currency") or values.get("currency:code") or "CNY").upper()
    fee = values.get("fee")
    charge = values.get("charge") or values.get("price")
    if isinstance(fee, str) and fee.casefold() in {"no", "false", "free", "免费"}:
        return {"status": "KNOWN", "amount_minor": 0, "currency": currency, "source": source}
    candidate = charge if charge is not None else fee
    if candidate is not None:
        candidate_text = str(candidate)
        suffix = re.search(r"\b([A-Za-z]{3})\b", candidate_text)
        symbol_currency = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "CNY"}
        for symbol, code in symbol_currency.items():
            if symbol in candidate_text:
                currency = code
                break
        if suffix:
            currency = suffix.group(1).upper()
        match = re.search(r"(\d+(?:\.\d+)?)", candidate_text)
        if match:
            return {
                "status": "KNOWN",
                "amount_minor": round(float(match.group(1)) * 100),
                "currency": currency,
                "source": source,
            }
    return {"status": "UNKNOWN", "amount_minor": None, "currency": currency, "source": source}


def _load_json(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _replay_snapshot_path() -> Path:
    root = Path(__file__).resolve().parents[4]
    configured = Path(settings.real_city_replay_snapshot_path)
    return configured if configured.is_absolute() else root / configured


def _load_replay_snapshot() -> dict[str, Any]:
    try:
        value = json.loads(_replay_snapshot_path().read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


_OFFICIAL_EVIDENCE_CLASSES = {
    "OFFICIAL_WEB",
    "OFFICIAL_OPERATOR",
    "OFFICIAL_TICKETING",
    "MUNICIPAL_AUTHORITY",
}


def _promote_captured_evidence(
    candidate_external_id: str,
    completion: Any,
    *,
    opening_hours: dict[str, Any],
    cost_evidence: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    """Promote only facts tied to captured, official source observations."""

    if not isinstance(completion, dict):
        return opening_hours, cost_evidence, None
    if str(completion.get("candidate_external_id") or "") != candidate_external_id:
        return opening_hours, cost_evidence, None
    observations = completion.get("observations")
    if not isinstance(observations, list):
        return opening_hours, cost_evidence, None
    captured = {
        str(item.get("id")): item
        for item in observations
        if isinstance(item, dict)
        and item.get("id")
        and item.get("url")
        and str(item.get("source_class") or "") in _OFFICIAL_EVIDENCE_CLASSES
    }
    if not captured:
        return opening_hours, cost_evidence, None

    promoted: dict[str, Any] = {
        "candidate_external_id": candidate_external_id,
        "observations": [captured[key] for key in sorted(captured)],
        "promoted_facts": {},
        "authority": "CAPTURED_OFFICIAL_SOURCE_REQUIRED",
    }
    facts = completion.get("facts") if isinstance(completion.get("facts"), dict) else {}
    for fact_type, current in (
        ("opening_hours", opening_hours),
        ("cost_evidence", cost_evidence),
    ):
        proposed = facts.get(fact_type)
        if not isinstance(proposed, dict):
            continue
        source_ids = proposed.get("source_observation_ids")
        if not isinstance(source_ids, list) or not source_ids:
            continue
        if any(str(item) not in captured for item in source_ids):
            continue
        if proposed.get("status") == "CONFLICTING":
            promoted["promoted_facts"][fact_type] = {
                **proposed,
                "status": "CONFLICTING",
                "source_observation_ids": [str(item) for item in source_ids],
            }
            continue
        if fact_type == "opening_hours":
            normalized = normalize_opening_hours(proposed)
            if normalized.get("status") in {"UNKNOWN", "RAW_UNPARSED", "CLOSED"}:
                continue
            value = {
                **normalized,
                "status": "OFFICIAL_WEB_VERIFIED",
                "source_observation_ids": [str(item) for item in source_ids],
                "source_urls": [captured[str(item)]["url"] for item in source_ids],
            }
        else:
            if proposed.get("amount_minor") is None and proposed.get("status") != "CONFLICTING":
                continue
            value = {
                **proposed,
                "status": "VERIFIED_OFFICIAL_WEB",
                "source_observation_ids": [str(item) for item in source_ids],
                "source_urls": [captured[str(item)]["url"] for item in source_ids],
            }
        promoted["promoted_facts"][fact_type] = value
        if fact_type == "opening_hours":
            opening_hours = value
        else:
            cost_evidence = value
    return opening_hours, cost_evidence, promoted


def discovery_anchor_options(session: Session, journey: Journey) -> list[dict[str, Any]]:
    """Return server-known discovery centers in product precedence order."""

    activities: list[Activity] = []
    if journey.active_plan_version_id:
        activities = list(
            session.scalars(
                select(Activity)
                .where(Activity.plan_version_id == journey.active_plan_version_id)
                .order_by(Activity.sequence_no)
            ).all()
        )
    options: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(
        key: str,
        *,
        source: str,
        latitude: Any,
        longitude: Any,
        location: str | None = None,
        activity_id: str | None = None,
        place_id: str | None = None,
        at: str | None = None,
    ) -> None:
        if latitude is None or longitude is None:
            return
        try:
            point = {"latitude": float(latitude), "longitude": float(longitude)}
        except (TypeError, ValueError):
            return
        if key in seen:
            return
        seen.add(key)
        options.append(
            {
                "anchor_key": key,
                "source": source,
                **point,
                "location": location,
                "activity_id": activity_id,
                "place_id": place_id,
                "at": at,
            }
        )

    ordered = sorted(
        activities,
        key=lambda item: (0 if item.id == journey.current_activity_id else 1, item.sequence_no),
    )
    for activity in ordered:
        if not activity.place_id:
            continue
        place = session.get(Place, activity.place_id)
        if place is not None:
            add(
                "CURRENT_ACTIVITY" if activity.id == journey.current_activity_id else "ACTIVITY",
                source=(
                    "journey_current_activity"
                    if activity.id == journey.current_activity_id
                    else "journey_route_activity"
                ),
                latitude=place.latitude,
                longitude=place.longitude,
                location=place.name,
                    activity_id=activity.id if activity else None,
                place_id=place.id,
                at=activity.start_at,
            )
            if activity.id == journey.current_activity_id:
                break

    selected_option = session.scalar(
        select(StayJourneyOption).where(
            StayJourneyOption.journey_id == journey.id,
            StayJourneyOption.status == "SELECTED",
        ).order_by(StayJourneyOption.rank)
    )
    if selected_option is not None:
        hotel = session.get(AccommodationOfferSnapshot, selected_option.accommodation_offer_id)
        if hotel is not None:
            add(
                "HOTEL",
                source="selected_accommodation",
                latitude=hotel.latitude,
                longitude=hotel.longitude,
                location=hotel.property_name,
                at=hotel.check_in_at,
            )

    context = session.get(JourneyTripContext, journey.id)
    arrival = _load_json(context.arrival_anchor_json if context else None, {})
    departure = _load_json(context.departure_anchor_json if context else None, {})
    add(
        "ARRIVAL",
        source="journey_memory_arrival",
        latitude=arrival.get("latitude"),
        longitude=arrival.get("longitude"),
        location=arrival.get("location"),
        at=arrival.get("at") or journey.start_at,
    )

    commitment_rows = session.scalars(
        select(Commitment).where(
            Commitment.journey_id == journey.id,
            Commitment.status == "ACTIVE",
            Commitment.level == "C4_Anchored",
        )
    ).all()
    commitment_rows.sort(
        key=lambda item: str(_load_json(item.policy_json, {}).get("scheduled_start_at") or "")
    )
    for commitment in commitment_rows:
        activity = session.get(Activity, commitment.activity_id) if commitment.activity_id else None
        policy = _load_json(commitment.policy_json, {})
        semantic_place_id = str(policy.get("semantic_key") or "")
        place = (
            session.get(Place, activity.place_id)
            if activity and activity.place_id
            else session.get(Place, semantic_place_id)
        )
        if place is not None:
            add(
                "UPCOMING_COMMITMENT",
                source="protected_commitment",
                latitude=place.latitude,
                longitude=place.longitude,
                location=place.name,
                activity_id=activity.id if activity else None,
                place_id=place.id,
                at=policy.get("scheduled_start_at") or (activity.start_at if activity else None),
            )
            break

    add(
        "DEPARTURE",
        source="journey_memory_departure",
        latitude=departure.get("latitude"),
        longitude=departure.get("longitude"),
        location=departure.get("location"),
        at=departure.get("at") or journey.end_at,
    )
    return options


def derive_search_anchor(session: Session, journey: Journey) -> dict[str, Any] | None:
    """Resolve the first usable server-known Journey discovery anchor."""

    options = discovery_anchor_options(session, journey)
    return options[0] if options else None


def _city_label(city_code: str) -> str:
    raw = str(city_code or "").strip()
    if "-" in raw:
        raw = raw.split("-", 1)[1]
    return raw.replace("_", " ").replace("-", " ").strip() or str(city_code)


def _is_tianjin_replay_city(city_code: str) -> bool:
    normalized = str(city_code or "").strip().upper().replace("_", "-")
    return normalized in {"CN-TIANJIN", "TIANJIN", "TSN", "CNX-DEMO"}


@dataclass(frozen=True)
class DiscoveryCandidate:
    provider_key: str
    external_id: str
    name: str
    category: str
    latitude: float
    longitude: float
    tags: tuple[str, ...]
    opening_hours: dict[str, Any]
    metadata: dict[str, Any]
    distance_m: float | None = None
    cost_evidence: dict[str, Any] = field(default_factory=dict)

    def payload(self) -> dict[str, Any]:
        return {
            "provider_key": self.provider_key,
            "external_id": self.external_id,
            "name": self.name,
            "category": self.category,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "tags": list(self.tags),
            "opening_hours": self.opening_hours,
            "metadata": self.metadata,
            "distance_m": round(self.distance_m, 1) if self.distance_m is not None else None,
            "cost_evidence": self.cost_evidence,
        }


class NominatimGeocoder:
    """Small, identified Nominatim client for bounded discovery calls."""

    provider_key = "nominatim"

    def __init__(self, *, client: httpx.Client | None = None, base_url: str | None = None):
        self.client = client or httpx.Client(timeout=settings.real_city_timeout_seconds)
        self.base_url = (base_url or settings.nominatim_url).rstrip("/")
        self._owned_client = client is None

    def search(self, query: str, *, city: str, limit: int) -> list[DiscoveryCandidate]:
        response = self.client.get(
            f"{self.base_url}/search",
            params={
                "q": f"{query}, {city}",
                "format": "jsonv2",
                "limit": min(limit, 10),
                "addressdetails": 1,
                "extratags": 1,
            },
            headers={"User-Agent": "CityNexus/7.0 (+https://citynexus.local/real-city)"},
        )
        response.raise_for_status()
        rows = response.json()
        candidates: list[DiscoveryCandidate] = []
        for row in rows:
            try:
                lat = float(row["lat"])
                lon = float(row["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            osm_type = str(row.get("osm_type") or "place")
            osm_id = str(
                row.get("osm_id")
                or row.get("place_id")
                or hashlib.sha1(str(row).encode()).hexdigest()
            )
            category = str(row.get("type") or row.get("class") or "service")
            candidates.append(
                DiscoveryCandidate(
                    provider_key=self.provider_key,
                    external_id=_external_id(self.provider_key, f"{osm_type}/{osm_id}"),
                    name=str(row.get("display_name") or query).split(",")[0],
                    category=category,
                    latitude=lat,
                    longitude=lon,
                    tags=(category, "real_city"),
                    opening_hours={},
                    metadata={"display_name": row.get("display_name"), "osm_type": osm_type},
                    cost_evidence=cost_evidence_from_tags(row.get("extratags"), source="nominatim"),
                )
            )
        return candidates

    def close(self) -> None:
        if self._owned_client:
            self.client.close()


class OverpassPOIProvider:
    """Bounded OSM POI query with a provider-owned, auditable request."""

    provider_key = "overpass"

    def __init__(self, *, client: httpx.Client | None = None, base_url: str | None = None):
        self.client = client or httpx.Client(timeout=settings.real_city_timeout_seconds)
        self.base_url = (base_url or settings.overpass_url).rstrip("/")
        self._owned_client = client is None

    def search(
        self,
        query: str,
        *,
        latitude: float,
        longitude: float,
        radius_m: int,
        limit: int,
    ) -> list[DiscoveryCandidate]:
        requested = query.casefold()
        tags = '"amenity"~"cafe|restaurant|library|arts_centre|theatre|museum"'
        if any(token in requested for token in ("park", "outdoor", "garden")):
            tags = '"leisure"~"park|garden"'
        query_text = (
            f"[out:json][timeout:10];nwr[{tags}](around:{min(radius_m, 5000)},{latitude},{longitude});"
            "out center tags;"
        )
        response = self.client.post(
            f"{self.base_url}/interpreter",
            content=query_text,
            headers={"User-Agent": "CityNexus/7.0 (+https://citynexus.local/real-city)"},
        )
        response.raise_for_status()
        elements = response.json().get("elements", [])
        candidates: list[DiscoveryCandidate] = []
        for row in elements[:limit]:
            tags_data = row.get("tags") or {}
            center = row.get("center") or row
            try:
                lat = float(center["lat"])
                lon = float(center["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            category = str(
                tags_data.get("amenity")
                or tags_data.get("leisure")
                or tags_data.get("tourism")
                or "service"
            )
            name = str(tags_data.get("name") or f"OSM {category}")
            osm_id = f"{row.get('type', 'n')}/{row.get('id')}"
            candidates.append(
                DiscoveryCandidate(
                    provider_key=self.provider_key,
                    external_id=_external_id(self.provider_key, osm_id),
                    name=name,
                    category=category,
                    latitude=lat,
                    longitude=lon,
                    tags=tuple(
                        sorted(
                            {
                                category,
                                "real_city",
                                "indoor" if category not in {"park", "garden"} else "outdoor",
                            }
                        )
                    ),
                    opening_hours=normalize_opening_hours(tags_data.get("opening_hours")),
                    metadata={"osm_id": osm_id, "tags": tags_data},
                    distance_m=_distance_m(latitude, longitude, lat, lon),
                    cost_evidence=cost_evidence_from_tags(tags_data, source="overpass"),
                )
            )
        return candidates

    def close(self) -> None:
        if self._owned_client:
            self.client.close()


_TIANJIN_REPLAY = (
    DiscoveryCandidate(
        provider_key="openstreetmap-replay",
        external_id="node/281001",
        name="Tianjin Italian Style Town Indoor Gallery",
        category="arts_centre",
        latitude=39.1315,
        longitude=117.2050,
        tags=("culture", "indoor", "real_city", "tianjin"),
        opening_hours={"open": "10:00", "close": "21:00"},
        metadata={"source": "captured_replay", "city": "Tianjin"},
        cost_evidence={
            "status": "ESTIMATED",
            "amount_minor": 800,
            "currency": "CNY",
            "source": "captured_replay",
        },
    ),
    DiscoveryCandidate(
        provider_key="openstreetmap-replay",
        external_id="node/281002",
        name="Haihe Riverside Design Library",
        category="library",
        latitude=39.1226,
        longitude=117.1964,
        tags=("culture", "quiet", "indoor", "real_city", "tianjin"),
        opening_hours={"open": "09:30", "close": "20:00"},
        metadata={"source": "captured_replay", "city": "Tianjin"},
        cost_evidence={
            "status": "ESTIMATED",
            "amount_minor": 0,
            "currency": "CNY",
            "source": "captured_replay",
        },
    ),
    DiscoveryCandidate(
        provider_key="openstreetmap-replay",
        external_id="node/281003",
        name="Tianjin Ancient Culture Street Tea House",
        category="cafe",
        latitude=39.1530,
        longitude=117.1908,
        tags=("local_food", "indoor", "real_city", "tianjin"),
        opening_hours={"open": "09:00", "close": "22:00"},
        metadata={"source": "captured_replay", "city": "Tianjin"},
        cost_evidence={
            "status": "ESTIMATED",
            "amount_minor": 300,
            "currency": "CNY",
            "source": "captured_replay",
        },
    ),
)


def _replay_candidates(query: str, *, limit: int) -> list[DiscoveryCandidate]:
    needle = query.casefold()
    ranked = sorted(
        _TIANJIN_REPLAY,
        key=lambda item: (
            0
            if any(
                token in f"{item.name} {item.category} {' '.join(item.tags)}".casefold()
                for token in needle.split()
            )
            else 1,
            item.name,
        ),
    )
    return list(ranked[:limit])


def _captured_replay_candidates(
    query: str,
    *,
    limit: int,
    anchor: dict[str, Any] | None = None,
    snapshot: dict[str, Any] | None = None,
) -> list[DiscoveryCandidate]:
    path = _replay_snapshot_path()
    payload = snapshot if snapshot is not None else _load_replay_snapshot()
    if not payload:
        return []
    completions = {
        str(item.get("candidate_external_id")): item
        for item in payload.get("evidence_completion", [])
        if isinstance(item, dict) and item.get("candidate_external_id")
    }
    ranked: list[tuple[int, DiscoveryCandidate]] = []
    needle = query.casefold()
    for row in payload.get("candidates", []):
        try:
            tags_data = row.get("tags") or {}
            if isinstance(tags_data, dict):
                tags = tuple(
                    sorted({str(value).casefold() for value in tags_data.values() if value})
                )
            else:
                tags = tuple(str(value) for value in tags_data)
            semantic_tags = set(tags)
            category = str(row.get("category") or "service").casefold()
            if category in {"museum", "library", "arts_centre", "theatre", "gallery"}:
                semantic_tags.update({"indoor", "culture"})
            elif category in {"cafe", "restaurant", "food"}:
                semantic_tags.update({"indoor", "local_food"})
            elif category in {"park", "garden", "viewpoint"}:
                semantic_tags.update({"outdoor", "scenic"})
            opening_hours = normalize_opening_hours(row.get("opening_hours"))
            cost_evidence = row.get("cost_evidence") or {
                "status": "UNKNOWN",
                "currency": "CNY",
            }
            opening_hours, cost_evidence, promoted = _promote_captured_evidence(
                str(row["external_id"]),
                completions.get(str(row["external_id"])),
                opening_hours=opening_hours,
                cost_evidence=cost_evidence,
            )
            metadata = {
                "source": "sealed_live_capture",
                "capture_path": str(path),
                "provider": row.get("provider"),
                "city": payload.get("city_name"),
                "snapshot_captured_at": payload.get("captured_at"),
            }
            if promoted is not None:
                metadata["evidence_completion"] = promoted
            distance = None
            if anchor and anchor.get("latitude") is not None and anchor.get("longitude") is not None:
                distance = _distance_m(
                    float(anchor["latitude"]),
                    float(anchor["longitude"]),
                    float(row["latitude"]),
                    float(row["longitude"]),
                )
            candidate = DiscoveryCandidate(
                provider_key="openstreetmap-replay",
                external_id=str(row["external_id"]),
                name=str(row["name"]),
                category=category,
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                tags=(*sorted(semantic_tags), "real_city", "captured_live_replay"),
                opening_hours=opening_hours,
                metadata=metadata,
                distance_m=distance,
                cost_evidence=cost_evidence,
            )
        except (KeyError, TypeError, ValueError):
            continue
        score = (
            0
            if any(
                token
                in f"{candidate.name} {candidate.category} {' '.join(candidate.tags)}".casefold()
                for token in needle.split()
            )
            else 1
        )
        ranked.append((score, candidate))
    ranked.sort(key=lambda item: (item[0], item[1].name))
    return [item for _, item in ranked[:limit]]


def materialize_candidates(
    session: Session,
    journey: Journey,
    candidates: list[DiscoveryCandidate],
    *,
    captured_at: str,
    mode: str,
) -> list[dict[str, Any]]:
    expires_at = (
        datetime.fromisoformat(captured_at)
        + timedelta(seconds=settings.real_city_cache_ttl_seconds)
    ).isoformat()
    result: list[dict[str, Any]] = []
    for candidate in candidates:
        distance = candidate.distance_m
        external_id = candidate.external_id
        opening_hours = normalize_opening_hours(candidate.opening_hours)
        cost_evidence = candidate.cost_evidence or cost_evidence_from_tags(
            candidate.metadata.get("tags") if isinstance(candidate.metadata, dict) else None,
            source=candidate.provider_key,
        )
        row = session.scalar(
            select(RealPlaceCandidate).where(
                RealPlaceCandidate.journey_id == journey.id,
                RealPlaceCandidate.provider_key == candidate.provider_key,
                RealPlaceCandidate.external_id == external_id,
            )
        )
        if row is None:
            row = RealPlaceCandidate(
                id=f"rpc-{hashlib.sha1(f'{journey.id}|{candidate.provider_key}|{external_id}'.encode()).hexdigest()[:24]}",
                journey_id=journey.id,
                provider_key=candidate.provider_key,
                external_id=external_id,
            )
            session.add(row)
        row.journey_id = journey.id
        row.city_code = journey.city_code
        row.name = candidate.name
        row.category = candidate.category
        row.latitude = candidate.latitude
        row.longitude = candidate.longitude
        row.tags_json = _json(list(candidate.tags))
        row.opening_hours_json = _json(opening_hours)
        row.metadata_json = _json(
            {**candidate.metadata, "discovery_mode": mode, "cost_evidence": cost_evidence}
        )
        row.captured_at = captured_at
        row.expires_at = expires_at
        row.distance_m = distance
        row.evidence_json = _json(
            {
                "provider": candidate.provider_key,
                "captured_at": captured_at,
                "ttl_seconds": settings.real_city_cache_ttl_seconds,
                "provenance": (
                    "SEALED_REAL_REPLAY"
                    if mode == "captured_replay"
                    else ("REPLAY" if mode in {"replay", "replay-fallback"} else "LIVE_PROVIDER")
                ),
                "opening_hours": opening_hours,
                "cost_evidence": cost_evidence,
                "evidence_completion": candidate.metadata.get("evidence_completion")
                if isinstance(candidate.metadata, dict)
                else None,
            }
        )
        row.status = "DISCOVERED"

        completion = candidate.metadata.get("evidence_completion") if isinstance(candidate.metadata, dict) else None
        if isinstance(completion, dict):
            observation_ids: list[str] = []
            for observation in completion.get("observations", []):
                if not isinstance(observation, dict) or not observation.get("url"):
                    continue
                fingerprint = hashlib.sha256(
                    _json(
                        {
                            "candidate": external_id,
                            "url": observation.get("url"),
                            "title": observation.get("title"),
                            "excerpt": observation.get("excerpt"),
                        }
                    ).encode("utf-8")
                ).hexdigest()
                existing_observation = session.scalar(
                    select(WebObservation).where(
                        WebObservation.journey_id == journey.id,
                        WebObservation.evidence_fingerprint == fingerprint,
                    )
                )
                if existing_observation is None:
                    existing_observation = WebObservation(
                        id=str(uuid4()),
                        journey_id=journey.id,
                        query=candidate.name,
                        url=str(observation["url"]),
                        domain=str(observation.get("domain") or ""),
                        title=str(observation.get("title") or candidate.name),
                        source_class=str(observation.get("source_class") or "OPEN_WEB"),
                        provider_key="sealed-provider-evidence",
                        model_key="provider-capture",
                        captured_at=captured_at,
                        evidence_fingerprint=fingerprint,
                        content_excerpt=str(observation.get("excerpt") or "")[:2000],
                        authority_status="CAPTURED_SOURCE",
                        created_at=captured_at,
                    )
                    session.add(existing_observation)
                observation_ids.append(existing_observation.id)
            if observation_ids:
                completion["web_observation_ids"] = observation_ids
                evidence_payload = _load_json(row.evidence_json, {})
                evidence_payload["web_observation_ids"] = observation_ids
                row.evidence_json = _json(evidence_payload)

        place = session.scalar(
            select(Place).where(
                Place.provider_key == candidate.provider_key,
                Place.external_id == external_id,
            )
        )
        if place is None:
            place = Place(
                id=f"real-place-{hashlib.sha1(f'{candidate.provider_key}|{external_id}'.encode()).hexdigest()[:24]}",
                provider_key=candidate.provider_key,
                external_id=external_id,
                city_code=journey.city_code,
                name=candidate.name,
                category=candidate.category,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                opening_hours_json=_json(opening_hours),
                tags_json=_json(list(candidate.tags)),
                metadata_json=_json(
                    {**candidate.metadata, "discovery_mode": mode, "cost_evidence": cost_evidence}
                ),
                updated_at=captured_at,
            )
            session.add(place)
        else:
            place.city_code = journey.city_code
            place.name = candidate.name
            place.category = candidate.category
            place.latitude = candidate.latitude
            place.longitude = candidate.longitude
            place.opening_hours_json = _json(opening_hours)
            place.tags_json = _json(list(candidate.tags))
            place.metadata_json = _json(
                {**candidate.metadata, "discovery_mode": mode, "cost_evidence": cost_evidence}
            )
            place.updated_at = captured_at
        session.flush()
        row.materialized_place_id = place.id
        service = session.scalar(
            select(CityService).where(
                CityService.provider_key == candidate.provider_key,
                CityService.external_id == f"service:{external_id}",
            )
        )
        if service is None:
            session.add(
                CityService(
                    id=f"service-{hashlib.sha1(f'{candidate.provider_key}|{external_id}'.encode()).hexdigest()[:24]}",
                    provider_key=candidate.provider_key,
                    external_id=f"service:{external_id}",
                    place_id=place.id,
                    city_code=journey.city_code,
                    service_type=candidate.category,
                    name=candidate.name,
                    availability_json=_json(opening_hours),
                    metadata_json=_json(candidate.metadata),
                    updated_at=captured_at,
                )
            )
        result.append(
            {
                **candidate.payload(),
                "opening_hours": opening_hours,
                "cost_evidence": cost_evidence,
                "id": place.id,
                "materialized_place_id": place.id,
            }
        )
    session.flush()
    return result


def capture_real_city_candidates(
    session: Session,
    journey: Journey,
    *,
    query: str,
    radius_m: int = 2500,
    limit: int = 8,
    mode: str = "replay",
) -> dict[str, Any]:
    captured_at = _now()
    mode = mode.lower()
    requested_mode = mode
    provider_status: dict[str, Any]
    candidates: list[DiscoveryCandidate]
    if mode == "captured_replay" and not _is_tianjin_replay_city(journey.city_code):
        raise ValueError(
            f"CAPTURED_REPLAY_CITY_MISMATCH: Tianjin replay cannot be used for {journey.city_code}"
        )
    snapshot = _load_replay_snapshot() if mode == "captured_replay" else {}
    journey_anchor = derive_search_anchor(session, journey)
    if mode == "live":
        live_error: str | None = None
        candidates = []
        anchor = journey_anchor
        if not settings.real_city_enabled:
            live_error = "REAL_CITY_DISABLED"
        else:
            geocoder = NominatimGeocoder()
            poi = OverpassPOIProvider()
            try:
                # Nominatim grounds the Journey/city anchor and names; Overpass
                # owns bounded category discovery around that server-derived anchor.
                city_label = _city_label(journey.city_code)
                context = session.get(JourneyTripContext, journey.id)
                arrival = _load_json(context.arrival_anchor_json if context else None, {})
                anchor_query = str(arrival.get("location") or city_label)
                grounded = (
                    geocoder.search(anchor_query, city=city_label, limit=1)
                    if anchor is None
                    else []
                )
                if anchor is None and grounded:
                    anchor = {
                        "latitude": grounded[0].latitude,
                        "longitude": grounded[0].longitude,
                        "source": "nominatim_city_anchor",
                    }
                if anchor is None:
                    raise RuntimeError("NO_JOURNEY_DERIVED_CITY_ANCHOR")
                candidates = poi.search(
                    query,
                    latitude=float(anchor["latitude"]),
                    longitude=float(anchor["longitude"]),
                    radius_m=radius_m,
                    limit=limit,
                )
                if not candidates:
                    candidates = geocoder.search(query, city=journey.city_code, limit=limit)
                provider_status = {
                    "nominatim": "CAPTURED",
                    "overpass": "CAPTURED"
                    if candidates and candidates[0].provider_key == "overpass"
                    else "NO_RESULTS",
                    "anchor": anchor,
                }
            except (
                httpx.HTTPError,
                KeyError,
                TypeError,
                ValueError,
                AttributeError,
                RuntimeError,
            ) as exc:
                live_error = type(exc).__name__
            finally:
                geocoder.close()
                poi.close()
        if live_error or not candidates:
            if _is_tianjin_replay_city(journey.city_code):
                candidates = _replay_candidates(query, limit=limit)
                mode = "replay-fallback"
                provider_status = {
                    "nominatim": "REPLAY_FALLBACK",
                    "overpass": "REPLAY_FALLBACK",
                    "anchor": journey_anchor,
                    "fallback_reason": live_error or "LIVE_NO_RESULTS",
                }
            else:
                # A generic-city trial must fail visibly rather than importing
                # Tianjin demo facts into another city's Journey.
                candidates = []
                mode = "live-unavailable"
                provider_status = {
                    "nominatim": "UNAVAILABLE",
                    "overpass": "UNAVAILABLE",
                    "anchor": journey_anchor,
                    "fallback_reason": live_error or "LIVE_NO_RESULTS",
                    "wrong_city_replay_blocked": True,
                }
    else:
        candidates = (
            _captured_replay_candidates(
                query,
                limit=limit,
                anchor=journey_anchor,
                snapshot=snapshot,
            )
            if mode == "captured_replay"
            else _replay_candidates(query, limit=limit)
        )
        provider_status = {
            "nominatim": "REPLAY_NOT_CALLED",
            "overpass": "REPLAY_NOT_CALLED",
            "openstreetmap_replay": "SEALED_REAL_REPLAY"
            if mode == "captured_replay"
            else "CAPTURED",
            "anchor": journey_anchor or snapshot.get("anchor"),
            "snapshot_anchor": snapshot.get("anchor"),
            "evidence_completion": sum(
                1
                for item in candidates
                if isinstance(item.metadata, dict) and item.metadata.get("evidence_completion")
            ),
        }
    request_payload = {
        "query": query,
        "city_code": journey.city_code,
        "radius_m": radius_m,
        "limit": limit,
        "mode": mode,
        "requested_mode": requested_mode,
    }
    session.add(
        ProviderCall(
            # Provider calls are audit events, not idempotency keys. Re-running
            # the same request must append a new event instead of colliding.
            id=str(uuid4()),
            provider_key=(
                "openstreetmap-replay"
                if mode in {"replay", "captured_replay", "replay-fallback"}
                else "real-city-provider-mesh"
            ),
            operation="discover_city_services",
            request_json=_json(request_payload),
            response_json=_json({"providers": provider_status, "count": len(candidates)}),
            status="SUCCESS",
            latency_ms=0,
            created_at=captured_at,
        )
    )
    materialized = materialize_candidates(
        session, journey, candidates, captured_at=captured_at, mode=mode
    )
    return {
        "journey_id": journey.id,
        "city_code": journey.city_code,
        "city_context": journey.city_code,
        "mode": mode,
        "captured_at": captured_at,
        "expires_at": (
            datetime.fromisoformat(captured_at)
            + timedelta(seconds=settings.real_city_cache_ttl_seconds)
        ).isoformat(),
        "provider_status": provider_status,
        "provider_evidence": {
            "snapshot_schema": snapshot.get("schema_version") if snapshot else None,
            "capture_anchor": snapshot.get("anchor") if snapshot else None,
            "mobility": snapshot.get("mobility") if snapshot else None,
            "weather": snapshot.get("weather") if snapshot else None,
        },
        # Keep the historical direct-discovery field for V7/V8 clients while
        # exposing the authoritative V13.4 runtime label separately.  The
        # orchestration contract consumes runtime_provenance, so new plans do
        # not inherit the legacy alias.
        "provenance": "SEALED_LIVE_CAPTURE"
        if mode == "captured_replay"
        else ("REPLAY" if mode in {"replay", "replay-fallback"} else "LIVE_PROVIDER"),
        "runtime_provenance": "SEALED_REAL_REPLAY"
        if mode == "captured_replay"
        else ("REPLAY" if mode in {"replay", "replay-fallback"} else "LIVE_PROVIDER"),
        "candidates": materialized,
    }
