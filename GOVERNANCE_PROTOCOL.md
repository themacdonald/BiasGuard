# BiasGuard Governance Protocol

BiasGuard is organized around a case lifecycle rather than a single model score. The v0.6 deterministic audit layer supplies validated fairness evidence before structured evaluation or governance interpretation.

## 1. Case

A `GovernanceCase` is the canonical identity of a decision under review.

It includes:

- decision
- context
- protected attributes under analysis
- evaluator model
- policy version
- evidence
- immutable state hash

## 2. Evidence

Evidence is an observation with provenance.

Examples:

- deterministic fairness metric
- structured evaluator judgment
- counterfactual sensitivity result
- data-quality finding
- human-provided evidence

Evidence does not automatically establish causality or legal liability.

## 3. Attribution

BiasGuard may record hypotheses such as proxy influence or root cause.

A hypothesis is not silently promoted to fact.

## 4. Counterfactual sensitivity

A paired intervention can test whether an outcome changes when one input is changed while specified inputs are held constant.

The result is explicitly labelled a **sensitivity signal**, not causal proof.

## 5. Governance recommendation

The policy engine produces a recommendation such as:

- pass
- log_only
- human_review
- block

The recommendation is not institutional authority. A deployment owner, reviewer, or other authorized governance mechanism determines the actual action.

## 6. Human adjudication

Adjudication is an independent event containing:

- reviewer
- outcome
- rationale
- supporting evidence IDs
- timestamp

The original evaluator output remains intact.

## 7. Remediation

A remediation describes the intervention applied to the system, process, data, or policy.

Examples:

- rebalance data
- remove or transform a proxy feature
- change decision threshold
- revise policy
- retrain model

## 8. Re-evaluation

After remediation, BiasGuard compares the new case state with the original state.

The system should report:

- resolved evidence
- remaining evidence
- information preservation
- before/after metrics
- counterfactual sensitivity before/after
- policy action before/after

## 9. Audit ledger

Each lifecycle transition becomes an append-only event.

The prototype uses an in-memory ledger. Production deployment should use durable append-only storage.

## Core principle

```text
Measure
  ↓
Explain / attribute
  ↓
Assess uncertainty
  ↓
Recommend governance action
  ↓
Human adjudication where required
  ↓
Remediate
  ↓
Re-evaluate
  ↓
Verify
```

BiasGuard is therefore not a bias score generator. It is a reproducible evidence-and-remediation loop.
