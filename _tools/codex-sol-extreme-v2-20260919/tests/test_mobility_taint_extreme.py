"""Dynamic taint-lattice probes over production mobility normalization."""
from __future__ import annotations

import pytest

from app.replanning.provider_snapshots import (
    EXPLICIT_FROZEN_FIXTURE,
    LIVE_PROVIDER_CAPTURE,
    MobilitySnapshot,
)


@pytest.mark.parametrize(
    "quality",
    [None, "", "UNKNOWN", "SYNTHETIC_DEFAULT", "MOCK", "CAPTURED_REPLAY", "UNMAPPED_PROVIDER"],
)
def test_weak_quality_never_yields_hard_minutes(quality):
    snapshot = MobilitySnapshot.from_minutes(
        source_provider_key="trusted-looking-name", minutes={("a", "b"): 17}, fact_quality=quality
    )
    with pytest.raises(KeyError):
        snapshot.hard_minutes("a", "b")


@pytest.mark.parametrize("quality", [LIVE_PROVIDER_CAPTURE, EXPLICIT_FROZEN_FIXTURE])
def test_exact_allowlist_yields_hard_minutes(quality):
    snapshot = MobilitySnapshot.from_minutes(
        source_provider_key="provider", minutes={("a", "b"): 17}, fact_quality=quality
    )
    assert snapshot.hard_minutes("a", "b") == 17


def test_serialization_round_trip_does_not_infer_trust_from_provider_or_provenance():
    evidence = {
        "facts": [{"origin_key": "a", "destination_key": "b", "minutes": 9, "provider": "valhalla-http", "route_provenance": "CAPTURED_REPLAY", "fact_quality": None}]
    }
    snapshot = MobilitySnapshot.from_evidence(evidence)
    assert snapshot.facts[("a", "b")].fact_quality is None
    with pytest.raises(KeyError):
        snapshot.hard_minutes("a", "b")


def test_mixed_snapshot_cannot_let_one_hard_leg_bless_one_weak_leg():
    from app.replanning.provider_snapshots import TravelEstimateFact
    snapshot = MobilitySnapshot(
        facts={
            ("a", "b"): TravelEstimateFact("a", "b", 10, "provider", "now", fact_quality=LIVE_PROVIDER_CAPTURE),
            ("b", "c"): TravelEstimateFact("b", "c", 20, "mock", "now", fact_quality="SYNTHETIC_DEFAULT"),
        },
        source_provider_key="mixed",
        captured_at="now",
    )
    assert snapshot.hard_minutes("a", "b") == 10
    with pytest.raises(KeyError):
        snapshot.hard_minutes("b", "c")
