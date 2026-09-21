from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class Evidence:
    """Immutable evidence object.

    Evidence describes an observation. It does not itself establish causality,
    legal liability, or policy authority.
    """

    evidence_id: str
    kind: str
    claim: str
    value: Any
    confidence: float | None = None
    source: str = "biasguard"
    created_at: str = field(default_factory=utc_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class GovernanceCase:
    """Canonical case container for one decision under review."""

    case_id: str
    decision: Mapping[str, Any]
    context: Mapping[str, Any] = field(default_factory=dict)
    protected_attributes: Sequence[str] = field(default_factory=tuple)
    evidence: Sequence[Evidence] = field(default_factory=tuple)
    evaluator_model: str | None = None
    policy_version: str = "policy-v1"
    created_at: str = field(default_factory=utc_now)

    @property
    def state_hash(self) -> str:
        return canonical_hash({
            "case_id": self.case_id,
            "decision": self.decision,
            "context": self.context,
            "protected_attributes": list(self.protected_attributes),
            "evidence": [asdict(item) for item in self.evidence],
            "evaluator_model": self.evaluator_model,
            "policy_version": self.policy_version,
        })

    def with_evidence(self, *new_evidence: Evidence) -> "GovernanceCase":
        return GovernanceCase(
            case_id=self.case_id,
            decision=self.decision,
            context=self.context,
            protected_attributes=self.protected_attributes,
            evidence=tuple(self.evidence) + tuple(new_evidence),
            evaluator_model=self.evaluator_model,
            policy_version=self.policy_version,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class CounterfactualResult:
    """Records sensitivity, not causality."""

    feature: str
    original_value: Any
    counterfactual_value: Any
    original_outcome: Any
    counterfactual_outcome: Any
    outcome_changed: bool
    held_constant: Sequence[str] = field(default_factory=tuple)
    limitations: Sequence[str] = field(default_factory=tuple)

    @property
    def evidence(self) -> Evidence:
        return Evidence(
            evidence_id=f"cf-{canonical_hash(asdict(self))[:12]}",
            kind="counterfactual_sensitivity",
            claim=f"Outcome changed when '{self.feature}' was changed in the specified counterfactual.",
            value=asdict(self),
            source="biasguard.counterfactual",
            metadata={
                "interpretation": "sensitivity_signal",
                "not_causal_proof": True,
            },
        )


def run_counterfactual(
    *,
    feature: str,
    original_input: Mapping[str, Any],
    counterfactual_value: Any,
    predict: Callable[[Mapping[str, Any]], Any],
    held_constant: Sequence[str] = (),
    limitations: Sequence[str] = (),
) -> CounterfactualResult:
    """Run a paired counterfactual experiment.

    The caller supplies the prediction function. BiasGuard does not assume
    that changing one attribute establishes a causal effect.
    """
    original_value = original_input.get(feature)
    original_outcome = predict(dict(original_input))

    changed = dict(original_input)
    changed[feature] = counterfactual_value
    counterfactual_outcome = predict(changed)

    return CounterfactualResult(
        feature=feature,
        original_value=original_value,
        counterfactual_value=counterfactual_value,
        original_outcome=original_outcome,
        counterfactual_outcome=counterfactual_outcome,
        outcome_changed=original_outcome != counterfactual_outcome,
        held_constant=tuple(held_constant),
        limitations=tuple(limitations),
    )


@dataclass(frozen=True)
class GovernanceRecommendation:
    action: str
    rationale: str
    evidence_ids: Sequence[str]
    authority_required: str = "human_or_institutional_policy"
    reversible: bool = True


@dataclass(frozen=True)
class Adjudication:
    case_id: str
    reviewer_id: str
    outcome: str
    rationale: str
    evidence_ids: Sequence[str]
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class Remediation:
    remediation_id: str
    description: str
    owner: str
    status: str = "proposed"
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class ReEvaluation:
    case_id: str
    before_state_hash: str
    after_state_hash: str
    resolved_evidence_ids: Sequence[str]
    remaining_evidence_ids: Sequence[str]
    information_preserved: bool
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class GovernanceEvent:
    event_type: str
    case_id: str
    actor: str
    payload: Mapping[str, Any]
    created_at: str = field(default_factory=utc_now)
    event_hash: str = ""

    def __post_init__(self) -> None:
        if not self.event_hash:
            object.__setattr__(
                self,
                "event_hash",
                canonical_hash({
                    "event_type": self.event_type,
                    "case_id": self.case_id,
                    "actor": self.actor,
                    "payload": self.payload,
                    "created_at": self.created_at,
                }),
            )


class GovernanceLedger:
    """Append-only in-memory event ledger for the prototype.

    Production persistence should use an append-only database/event store.
    """

    def __init__(self) -> None:
        self._events: list[GovernanceEvent] = []

    def append(
        self, event_type: str, case_id: str, actor: str, payload: Mapping[str, Any]
    ) -> GovernanceEvent:
        event = GovernanceEvent(event_type, case_id, actor, dict(payload))
        self._events.append(event)
        return event

    def events(self, case_id: str | None = None) -> list[GovernanceEvent]:
        if case_id is None:
            return list(self._events)
        return [event for event in self._events if event.case_id == case_id]

    def verify_chain(self) -> bool:
        """Verify that recorded event fingerprints remain internally consistent."""
        for event in self._events:
            expected = canonical_hash({
                "event_type": event.event_type,
                "case_id": event.case_id,
                "actor": event.actor,
                "payload": event.payload,
                "created_at": event.created_at,
            })
            if event.event_hash != expected:
                return False
        return True
