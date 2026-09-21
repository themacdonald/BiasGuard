from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .typesafe_adapter import TypeSafeClient, TypeSafeObservation, normalize_observation


@dataclass(frozen=True)
class PolicyThresholds:
    """Operational thresholds. These are policy inputs, not universal standards."""

    bias_yes: float = 0.80
    bias_no: float = 0.20
    block_at_severity: float = 3.0
    review_at_severity: float = 2.0
    min_severity_confidence: float = 0.55


@dataclass(frozen=True)
class EvaluationPolicy:
    thresholds: PolicyThresholds = field(default_factory=PolicyThresholds)
    severity_weight: float = 0.60
    harm_weight: float = 0.30
    detector_weight: float = 0.10
    version: str = "policy-v1"


@dataclass(frozen=True)
class EvaluationResult:
    action: str
    reason: str
    priority: float
    top_bias_probability: float
    severity: float | None
    severity_confidence: float | None
    human_review: bool


@dataclass(frozen=True)
class EvaluationRecord:
    timestamp: str
    model: str
    policy_version: str
    state_hash: str
    judgments: Mapping[str, Mapping[str, Any]]
    result: Mapping[str, Any]


def build_state(
    decision: Any,
    *,
    biasguard_flags: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
    mitigations: Sequence[Mapping[str, Any]] | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "decision": decision,
        "biasguard_flags": dict(biasguard_flags or {}),
        "policy": dict(policy or {}),
        "mitigations": list(mitigations or []),
        "context": dict(context or {}),
    }


def state_hash(state: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        state,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _question(
    question_id: str,
    kind: str,
    prompt: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": question_id,
        "type": kind,
        "prompt": prompt,
        **extra,
    }


def build_questions(
    protected_groups: Sequence[str],
    biasguard_flags: Sequence[str] = (),
) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = [
        _question(
            "protected_reference",
            "noul",
            "Does the decision explicitly or implicitly use a protected characteristic?",
        ),
        _question(
            "severity",
            "score",
            "How severe is the identified issue?",
            levels=[
                "no identified issue",
                "minor",
                "moderate",
                "severe",
                "systemic",
            ],
        ),
        _question(
            "harm",
            "score",
            "How much potential harm could this issue cause?",
            levels=[
                "negligible",
                "limited",
                "moderate",
                "serious",
                "systemic",
            ],
        ),
        _question(
            "review_track",
            "choice",
            "What review track is appropriate?",
            options=["pass", "log_only", "human_review", "block"],
        ),
        _question(
            "root_cause",
            "choice",
            "What is the most likely root cause?",
            options=["data", "model", "proxy", "policy", "output", "unknown"],
        ),
        _question(
            "proxy_influence",
            "noul",
            "Could a non-protected feature act as a proxy for a protected characteristic?",
        ),
    ]

    for group in protected_groups:
        questions.append(
            _question(
                f"bias_{group}",
                "noul",
                f"Does the decision show evidence of unfair treatment related to {group}?",
            )
        )

    for flag in biasguard_flags:
        questions.append(
            _question(
                f"verify_{flag}",
                "noul",
                f"Is the BiasGuard detector flag '{flag}' supported by the decision evidence?",
            )
        )

    return questions


class BiasGuardEvaluator:
    """Compose structured evaluator observations into an explicit policy result."""

    def __init__(
        self,
        client: TypeSafeClient | None = None,
        *,
        policy: EvaluationPolicy | None = None,
        model: str = "unknown",
    ) -> None:
        self.client = client
        self.policy = policy or EvaluationPolicy()
        self.model = model

    def compose(
        self,
        observations: Sequence[TypeSafeObservation],
    ) -> EvaluationResult:
        thresholds = self.policy.thresholds
        by_id = {obs.question_id: obs for obs in observations}

        bias_probs = [
            float(obs.probability)
            for obs in observations
            if obs.question_id.startswith("bias_") and obs.probability is not None
        ]
        top_bias = max(bias_probs, default=0.0)

        severity_obs = by_id.get("severity")
        harm_obs = by_id.get("harm")

        severity = self._numeric_value(severity_obs)
        harm = self._numeric_value(harm_obs)
        severity_conf = severity_obs.confidence if severity_obs else None

        uncertain_bias = any(
            thresholds.bias_no < p < thresholds.bias_yes for p in bias_probs
        )
        low_severity_conf = (
            severity is not None
            and severity_conf is not None
            and severity_conf < thresholds.min_severity_confidence
        )

        shaky = uncertain_bias or low_severity_conf
        detector = min(top_bias, 1.0)
        priority = (
            self.policy.severity_weight * ((severity or 0.0) / 4.0)
            + self.policy.harm_weight * ((harm or 0.0) / 4.0)
            + self.policy.detector_weight * detector
        )

        if severity is not None and severity >= thresholds.block_at_severity and not shaky:
            return EvaluationResult(
                action="block",
                reason="severity reached the configured block threshold",
                priority=priority,
                top_bias_probability=top_bias,
                severity=severity,
                severity_confidence=severity_conf,
                human_review=False,
            )

        if (
            shaky
            or (severity is not None and severity >= thresholds.review_at_severity)
            or top_bias >= thresholds.bias_yes
        ):
            reason = (
                "ambiguous or low-confidence evaluation"
                if shaky
                else "evaluation reached the configured human-review threshold"
            )
            return EvaluationResult(
                action="human_review",
                reason=reason,
                priority=priority,
                top_bias_probability=top_bias,
                severity=severity,
                severity_confidence=severity_conf,
                human_review=True,
            )

        if top_bias >= thresholds.bias_no:
            return EvaluationResult(
                action="log_only",
                reason="evaluation indicates a concern below the review threshold",
                priority=priority,
                top_bias_probability=top_bias,
                severity=severity,
                severity_confidence=severity_conf,
                human_review=False,
            )

        return EvaluationResult(
            action="pass",
            reason="no configured policy threshold was reached",
            priority=priority,
            top_bias_probability=top_bias,
            severity=severity,
            severity_confidence=severity_conf,
            human_review=False,
        )

    @staticmethod
    def _numeric_value(observation: TypeSafeObservation | None) -> float | None:
        if observation is None:
            return None
        value = observation.value
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def evaluate(
        self,
        state: Mapping[str, Any],
        questions: Sequence[Mapping[str, Any]],
    ) -> EvaluationRecord:
        if self.client is None:
            raise RuntimeError(
                "No structured evaluator is configured. "
                "Use a TypeSafeClient implementation before calling evaluate()."
            )

        raw = self.client.evaluate(state, questions)
        raw_answers = raw.get("answers", raw)

        observations: list[TypeSafeObservation] = []
        for question in questions:
            question_id = str(question["id"])
            answer = raw_answers.get(question_id)
            if isinstance(answer, Mapping):
                observations.append(
                    normalize_observation(
                        question_id,
                        str(question["type"]),
                        answer,
                    )
                )

        result = self.compose(observations)
        record = EvaluationRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=self.model,
            policy_version=self.policy.version,
            state_hash=state_hash(state),
            judgments={
                obs.question_id: asdict(obs)
                for obs in observations
            },
            result=asdict(result),
        )
        return record
