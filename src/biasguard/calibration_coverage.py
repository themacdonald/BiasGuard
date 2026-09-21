from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class CoverageReport:
    supplied: int
    valid: int
    invalid: int
    unmatched: int
    missing_answer: int
    evaluated: int


@dataclass(frozen=True)
class PairingResult:
    pairs: tuple[tuple[float, int], ...]
    invalid: int
    unmatched: int
    missing_answer: int


def pair_binary_records(
    judgments: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]],
    question_id: str,
) -> PairingResult:
    """Pair calibration observations while making dropped records visible."""
    by_hash: dict[str, Mapping[str, Any]] = {}
    invalid = 0

    for row in judgments:
        state_hash = row.get("state_hash")
        if not isinstance(state_hash, str) or not state_hash:
            invalid += 1
            continue
        if state_hash in by_hash:
            invalid += 1
            continue
        by_hash[state_hash] = row

    pairs: list[tuple[float, int]] = []
    unmatched = 0
    missing_answer = 0

    for label in labels:
        state_hash = label.get("state_hash")
        if not isinstance(state_hash, str) or not state_hash:
            invalid += 1
            continue

        row = by_hash.get(state_hash)
        if row is None:
            unmatched += 1
            continue

        answer = row.get("judgments", {}).get(question_id)
        target = label.get("binary", {}).get(question_id)

        if not isinstance(answer, Mapping) or target is None:
            missing_answer += 1
            continue

        probability = answer.get("probability")
        try:
            probability = float(probability)
            target = int(target)
        except (TypeError, ValueError):
            invalid += 1
            continue

        if not 0.0 <= probability <= 1.0 or target not in (0, 1):
            invalid += 1
            continue

        pairs.append((probability, target))

    return PairingResult(
        pairs=tuple(pairs),
        invalid=invalid,
        unmatched=unmatched,
        missing_answer=missing_answer,
    )


def coverage_from_pairing(
    result: PairingResult,
    supplied: int,
) -> CoverageReport:
    return CoverageReport(
        supplied=supplied,
        valid=len(result.pairs),
        invalid=result.invalid,
        unmatched=result.unmatched,
        missing_answer=result.missing_answer,
        evaluated=len(result.pairs),
    )
