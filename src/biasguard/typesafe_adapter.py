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

    # Native System One wire fields:
    # Noul -> noul, Score -> score, Choice -> choice.
    if kind == "noul" and "noul" in answer:
        probability = float(answer["noul"])
        value = probability
    elif kind == "score" and "score" in answer:
        value = float(answer["score"])
    elif kind == "choice" and "choice" in answer:
        value = answer["choice"]

    if confidence is not None:
        confidence = float(confidence)
    if probability is not None:
        probability = float(probability)

    # Generic aliases remain supported for offline fixtures.
    if value is None:
        value = answer.get("score") if "score" in answer else answer.get("choice")
        if value is None and probability is not None:
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
