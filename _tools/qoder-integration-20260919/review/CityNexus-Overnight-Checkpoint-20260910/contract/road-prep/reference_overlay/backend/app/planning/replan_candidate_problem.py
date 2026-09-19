from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ReplanCandidateEvidence:
    key: str
    family: str
    feasible: bool
    utility_score: float
    disruption_count: int
    generation_rank: int


def rank_verified_candidates(
    candidates: Iterable[ReplanCandidateEvidence],
) -> tuple[ReplanCandidateEvidence, ...]:
    """Deterministically rank only already-gated candidates.

    OR-Tools may later generate candidates, but it must not bypass this verified
    evidence boundary or the authoritative CityNexus feasibility gate.
    """

    feasible = [item for item in candidates if item.feasible]
    feasible.sort(
        key=lambda item: (
            -item.utility_score,
            item.disruption_count,
            item.generation_rank,
            item.family,
            item.key,
        )
    )
    return tuple(feasible)


def take_feasible(
    candidates: Iterable[ReplanCandidateEvidence], *, candidate_count: int
) -> tuple[ReplanCandidateEvidence, ...]:
    if candidate_count < 1:
        raise ValueError("candidate_count must be positive")
    return rank_verified_candidates(candidates)[:candidate_count]
