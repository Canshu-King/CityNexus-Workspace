"""Historical duplicate confirmation identity detection / quarantine.

The unique index ``(journey_id, confirmation_ref)`` on
``transport_reservations`` is the real serialization point for concurrent C4
confirmation.  Before it can be enforced, any pre-existing duplicate identity
must be detected, reported and quarantined rather than silently collapsing two
different bookings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Commitment, Event, Journey, TransportReservation

QUARANTINE_EVENT = "RESERVATION_IDENTITY_DUPLICATE"
QUARANTINE_MARKER = "QUARANTINED_DUPLICATE_IDENTITY"


@dataclass(frozen=True)
class DuplicateReport:
    journey_id: str
    confirmation_ref: str
    reservation_ids: tuple[str, ...]
    winner_id: str
    quarantined_ids: tuple[str, ...]
    repaired: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "confirmation_ref": self.confirmation_ref,
            "reservation_ids": list(self.reservation_ids),
            "winner_id": self.winner_id,
            "quarantined_ids": list(self.quarantined_ids),
            "repaired": self.repaired,
        }


def detect_duplicate_confirmation_identities(
    session: Session, journey_id: str | None = None
) -> list[DuplicateReport]:
    """Report every historical duplicate ``(journey_id, confirmation_ref)``."""

    query = (
        select(
            TransportReservation.journey_id,
            TransportReservation.confirmation_ref,
            func.count(TransportReservation.id),
        )
        .where(
            TransportReservation.confirmation_ref.is_not(None),
            TransportReservation.status != QUARANTINE_MARKER,
        )
        .group_by(TransportReservation.journey_id, TransportReservation.confirmation_ref)
        .having(func.count(TransportReservation.id) > 1)
    )
    if journey_id is not None:
        query = query.where(TransportReservation.journey_id == journey_id)
    reports: list[DuplicateReport] = []
    for row_journey, reference, _count in session.execute(query).all():
        rows = session.scalars(
            select(TransportReservation)
            .where(
                TransportReservation.journey_id == row_journey,
                TransportReservation.confirmation_ref == reference,
                TransportReservation.status != QUARANTINE_MARKER,
            )
            .order_by(TransportReservation.captured_at, TransportReservation.id)
        ).all()
        winner, *losers = rows
        reports.append(
            DuplicateReport(
                journey_id=str(row_journey),
                confirmation_ref=str(reference),
                reservation_ids=tuple(item.id for item in rows),
                winner_id=winner.id,
                quarantined_ids=tuple(item.id for item in losers),
                repaired=False,
            )
        )
    return reports


def quarantine_duplicate_confirmation_identities(
    session: Session, journey_id: str | None = None
) -> list[DuplicateReport]:
    """Quarantine losers so the unique identity can be enforced.

    The earliest reservation remains authoritative; later duplicates are marked
    ``QUARANTINED_DUPLICATE_IDENTITY``, their draft pointer is released, and a
    durable Event records the repair.  Nothing is deleted.
    """

    reports = detect_duplicate_confirmation_identities(session, journey_id)
    repaired: list[DuplicateReport] = []
    now = datetime.now(timezone.utc).isoformat()
    for report in reports:
        losers = [
            session.get(TransportReservation, item_id)
            for item_id in report.quarantined_ids
        ]
        quarantined: list[str] = []
        for row in losers:
            if row is None:
                continue
            row.status = QUARANTINE_MARKER
            row.draft_id = None
            quarantined.append(row.id)
        session.add(
            Event(
                id=str(uuid4()),
                journey_id=report.journey_id,
                provider_key="citynexus-reservation",
                provenance="SYSTEM_DERIVED",
                event_type="USER_CHANGE",
                severity="MAJOR",
                status="RESOLVED",
                affected_activity_id=None,
                occurred_at=now,
                detected_at=now,
                resolved_at=now,
                payload_json=_json(
                    {
                        "kind": QUARANTINE_EVENT,
                        "confirmation_ref": report.confirmation_ref,
                        "winner_id": report.winner_id,
                        "quarantined_ids": quarantined,
                        "policy": QUARANTINE_MARKER,
                    }
                ),
                created_at=now,
            )
        )
        repaired.append(
            DuplicateReport(
                journey_id=report.journey_id,
                confirmation_ref=report.confirmation_ref,
                reservation_ids=report.reservation_ids,
                winner_id=report.winner_id,
                quarantined_ids=tuple(quarantined),
                repaired=True,
            )
        )
    return repaired


def _json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
