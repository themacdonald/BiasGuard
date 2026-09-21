from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


class TypeSafeClient(Protocol):
    def evaluate(
        self, state: Mapping[str, Any], questions: Sequence[Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class TypeSafeObservation:
    question_id: str
    kind: str
    value: Any
    confidence: float | None = None
    probability: float | None = None
    raw: Mapping[str, Any] | None = None


def normalize_observation(
    question_id: str, kind: str, answer: Mapping[str, Any]
) -> TypeSafeObservation:
    confidence = answer.get("confidence")
    probability = answer.get("probability")
    value = answer.get("value")

    if confidence is not None:
        confidence = float(confidence)
    if probability is not None:
        probability = float(probability)

    # Some providers use score/noul aliases instead of a generic value.
    if value is None:
        if "score" in answer:
            value = answer["score"]
        elif kind == "noul" and probability is not None:
            value = probability

    return TypeSafeObservation(
        question_id=question_id,
        kind=kind,
        value=value,
        confidence=confidence,
        probability=probability,
        raw=dict(answer),
    )


class OfflineAnswersClient:
    """Development client for recorded answers; replace with the real evaluator adapter."""

    def __init__(self, answers: Mapping[str, Any]) -> None:
        self.answers = dict(answers)

    def evaluate(
        self, state: Mapping[str, Any], questions: Sequence[Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        del state, questions
        return {"answers": self.answers}
