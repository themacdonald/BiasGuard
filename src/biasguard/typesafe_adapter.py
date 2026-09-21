from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


class TypeSafeClient(Protocol):
    """Minimal provider contract used by BiasGuard.

    A concrete TypeSafe SDK adapter can implement this protocol without
    making the TypeSafe SDK a mandatory BiasGuard dependency.
    """

    def evaluate(
        self,
        state: Mapping[str, Any],
        questions: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class TypeSafeObservation:
    """Normalized observation returned by a structured evaluator."""

    question_id: str
    kind: str
    value: Any
    confidence: float | None = None
    probability: float | None = None
    raw: Mapping[str, Any] | None = None


def normalize_observation(
    question_id: str,
    kind: str,
    answer: Mapping[str, Any],
) -> TypeSafeObservation:
    """Normalize common evaluator fields without assuming an SDK response shape."""

    confidence = answer.get("confidence")
    probability = answer.get("probability")

    if confidence is not None:
        confidence = float(confidence)
    if probability is not None:
        probability = float(probability)

    return TypeSafeObservation(
        question_id=question_id,
        kind=kind,
        value=answer.get("value"),
        confidence=confidence,
        probability=probability,
        raw=answer,
    )


class UnavailableTypeSafeClient:
    """Explicit fail-closed client used when no evaluator is configured."""

    def evaluate(
        self,
        state: Mapping[str, Any],
        questions: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        raise RuntimeError(
            "No structured evaluator is configured. "
            "Configure a TypeSafeClient before automated evaluation."
        )
