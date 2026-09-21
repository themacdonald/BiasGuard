from biasguard.governance import (
    Adjudication,
    Evidence,
    GovernanceCase,
    GovernanceLedger,
    Remediation,
    run_counterfactual,
)


def test_evidence_is_fingerprinted():
    evidence = Evidence(
        evidence_id="e1",
        kind="fairness_metric",
        claim="Selection rates differ.",
        value={"dir": 0.71},
    )
    assert evidence.fingerprint
    assert len(evidence.fingerprint) == 64


def test_case_hash_changes_when_evidence_changes():
    case = GovernanceCase(
        case_id="BG-1",
        decision={"outcome": "reject"},
        protected_attributes=["gender"],
    )
    updated = case.with_evidence(Evidence(
        evidence_id="e1",
        kind="metric",
        claim="DIR below threshold",
        value=0.71,
    ))
    assert case.state_hash != updated.state_hash


def test_counterfactual_records_sensitivity_not_causality():
    def predict(row):
        return "reject" if row["gender"] == "female" else "accept"

    result = run_counterfactual(
        feature="gender",
        original_input={"gender": "female", "experience": 6},
        counterfactual_value="male",
        predict=predict,
        held_constant=["experience"],
        limitations=["synthetic intervention"],
    )

    assert result.outcome_changed is True
    assert result.evidence.metadata["not_causal_proof"] is True


def test_ledger_is_append_only_and_verifiable():
    ledger = GovernanceLedger()
    ledger.append("evaluation", "BG-1", "system", {"action": "human_review"})
    ledger.append("adjudication", "BG-1", "reviewer-1", {
        "outcome": "confirm",
        "rationale": "Evidence supported finding.",
    })
    assert len(ledger.events("BG-1")) == 2
    assert ledger.verify_chain() is True


def test_governance_artifacts_have_distinct_roles():
    adjudication = Adjudication(
        case_id="BG-1",
        reviewer_id="r1",
        outcome="confirm",
        rationale="Supported by evidence.",
        evidence_ids=["e1"],
    )
    remediation = Remediation(
        remediation_id="m1",
        description="Reweight training samples.",
        owner="ml-team",
    )
    assert adjudication.outcome == "confirm"
    assert remediation.status == "proposed"
