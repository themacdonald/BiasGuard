# Proposal: BiasGuard

## 1. Objective

BiasGuard is an open-source evaluation and governance toolkit for auditing AI-driven decisions.

The project began with a focus on AI-assisted hiring systems, where statistical fairness measurements can reveal differences in outcomes across demographic groups. BiasGuard is evolving toward a broader framework that combines:

* Deterministic fairness measurement
* Structured AI evaluation
* Counterfactual testing
* Evaluator calibration
* Explicit policy rules
* Human review
* Mitigation and re-evaluation
* Reproducible audit trails

The central objective is not to produce a single "bias score."

Instead, BiasGuard aims to answer:

> **What was evaluated, what evidence was observed, how was the judgment produced, how reliable was that judgment, what policy was applied, and what action followed?**

---

## 2. Background and Rationale

AI systems can produce unequal or problematic outcomes because of training data, model behavior, feature selection, proxy variables, decision thresholds, or the way outputs are interpreted and operationalized.

Aggregate fairness metrics provide an important way to measure observed differences between groups.

For example:

* **Disparate Impact Ratio** compares selection rates between a protected and reference group.
* **Statistical Parity Difference** measures the difference between selection rates.
* **Equal Opportunity Difference** compares true-positive rates between groups.

However, aggregate metrics cannot answer every question about an individual AI decision.

For example, a fairness metric may identify an outcome disparity without explaining:

* What caused a particular decision?
* Whether a generated rationale contains an unfair generalization?
* How severe a particular issue is?
* Whether the available evidence is sufficient?
* Whether an evaluator is uncertain?
* Whether a case should be escalated for human review?

BiasGuard therefore separates **measurement** from **structured judgment**.

```text
Deterministic Measurement
          +
Structured Evaluation
          ↓
      Calibration
          ↓
        Policy
          ↓
   Human Oversight
          ↓
       Auditability
```

This separation is a fundamental architectural principle of the project.

---

## 3. Core Design Philosophy

BiasGuard is built around several principles.

### 3.1 Measurement and Judgment Are Different

Deterministic statistical measurements and structured evaluator judgments answer different questions.

```text
Fairness metrics:
"What does the observed data show?"

Structured evaluation:
"What does the evaluator judge about this case?"

Policy:
"What should happen given this evidence?"
```

Neither layer should silently replace the other.

---

### 3.2 Evaluator Confidence Is Not Truth

A structured evaluator may report high confidence and still be wrong.

BiasGuard therefore treats evaluator confidence as a measurable property rather than proof of correctness.

Stored judgments can subsequently be compared against human-adjudicated labels through calibration.

---

### 3.3 Policy Is Explicit

Operational thresholds should exist in configuration rather than being hidden inside an evaluator.

For example:

```text
evaluation
    ↓
confidence
    ↓
severity
    ↓
policy thresholds
    ↓
pass / log / review / block
```

The evaluator provides evidence. The policy determines the operational response.

---

### 3.4 Uncertainty Can Trigger Human Review

Ambiguous cases should not necessarily be forced into an automated outcome.

BiasGuard can route cases to human review when:

* Confidence is low
* Evaluations conflict
* Evidence is incomplete
* Severity is uncertain
* A configured review threshold is reached

Human adjudication can then become part of the calibration dataset.

---

## 4. Target Audience

BiasGuard is intended for:

* AI/ML engineers auditing model behavior
* Data scientists and data analysts working with AI evaluation
* Responsible AI and AI governance teams
* ML quality and evaluation teams
* Researchers studying algorithmic fairness
* Organizations deploying AI-assisted decision systems
* Developers building evaluation and oversight infrastructure

Hiring remains an important initial use case because fairness auditing is especially relevant to automated or AI-assisted recruitment decisions.

The underlying architecture is not restricted to hiring.

---

## 5. Core Use Cases

### 5.1 Dataset Analysis

Load historical decision data and calculate:

* Group distributions
* Selection rates
* Outcome differences
* Fairness metrics
* Data-quality indicators

---

### 5.2 Counterfactual Testing

Create controlled variations of an input while changing selected attributes.

For example:

```text
Original
Gender = Male
        ↓
Counterfactual
Gender = Female
```

The system can then compare model outputs and identify whether the decision changes.

Counterfactual differences are treated as evidence for further investigation rather than automatic proof of discrimination.

---

### 5.3 Fairness Measurement

BiasGuard currently supports:

* Disparate Impact Ratio
* Statistical Parity Difference
* Equal Opportunity Difference

Additional metrics can be added without changing the overall architecture.

---

### 5.4 Structured Decision Evaluation

Individual AI outputs can be evaluated using structured questions.

Examples include:

**Binary**

> Does the output rely on an unfair generalization?

**Categorical**

> What type of issue is present?

**Ordered**

> How severe is the identified issue?

This allows BiasGuard to evaluate dimensions that aggregate statistical metrics cannot directly capture.

---

### 5.5 Evaluator Calibration

Stored evaluator judgments can be compared with human-adjudicated labels.

For binary questions:

* Brier score
* Expected Calibration Error
* Reliability curves
* Precision
* Recall
* False positives
* False negatives

For ordered scores:

* Exact agreement
* Within-one-level agreement
* Mean Absolute Error
* Confidence behavior

For categorical judgments:

* Overall agreement
* Per-class accuracy

Calibration results provide evidence for evaluating the reliability of the evaluation system.

---

### 5.6 Policy Simulation

BiasGuard can analyze how different policy thresholds affect:

* Cases flagged
* Cases missed
* False positives
* False negatives
* Human-review volume
* Automated blocks

This makes policy trade-offs visible without embedding a universal threshold into the evaluator.

---

### 5.7 Human Review

Cases that meet configured review conditions can be routed for human adjudication.

The resulting decision can be stored as an auditable label and reused for calibration.

This creates a feedback loop:

```text
AI Evaluation
      ↓
Human Review
      ↓
Adjudicated Label
      ↓
Calibration
      ↓
Evaluation Reliability Analysis
```

---

### 5.8 Mitigation and Re-evaluation

When an issue is identified, organizations can apply an appropriate intervention.

Possible interventions include:

* Re-weighting
* Resampling
* Feature review
* Threshold adjustment
* Model retraining
* Output revision
* Counterfactual testing

Mitigation is followed by re-evaluation.

The system should compare the original and remediated results rather than assuming that an intervention succeeded because one metric improved.

---

### 5.9 Governance and Audit Reporting

BiasGuard can generate reports containing:

* Dataset information
* Model/evaluator version
* Fairness measurements
* Structured judgments
* Confidence information
* Calibration results
* Policy version
* Final action
* Human-review outcome
* Mitigation history

The objective is to make an AI evaluation reproducible and inspectable after the fact.

---

## 6. Proposed Architecture

The high-level architecture is:

```text
                    AI System / Dataset
                           │
                           ▼
                  ┌──────────────────┐
                  │ Data Validation  │
                  └────────┬─────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
   Deterministic Measurement     Structured Evaluation
             │                    Noul / Choice / Score
             │                           │
             └─────────────┬─────────────┘
                           ▼
                      Calibration
                           │
                           ▼
                     Policy Engine
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
           PASS        HUMAN REVIEW      BLOCK
                           │
                           ▼
                    Human Adjudication
                           │
                           ▼
                     Audit Record
                           │
                           ▼
                      Calibration
```

For remediation:

```text
Original System
      ↓
Evaluation
      ↓
Issue Identified
      ↓
Mitigation
      ↓
Re-evaluation
      ↓
Comparison
      ↓
Audit
```

---

## 7. Project Plan

The original project plan focused on implementing the fairness and mitigation modules first.

The updated roadmap expands this into a layered evaluation and governance system.

### Phase 1: Deterministic Measurement

* Stabilize fairness metric implementations
* Add input validation
* Add group-level reporting
* Expand metric test coverage
* Define consistent metric interfaces

### Phase 2: Structured Evaluation

* Integrate the structured evaluation adapter
* Implement binary, categorical, and ordered judgments
* Define evaluation state schemas
* Add confidence and uncertainty handling
* Add deterministic policy composition

### Phase 3: Calibration

* Store evaluator judgments
* Create human-adjudicated labels
* Implement binary calibration
* Implement score calibration
* Implement categorical evaluation analysis
* Add model/evaluator version comparisons
* Separate calibration from policy threshold selection

### Phase 4: Human Review & Audit

* Add human-review routing
* Store adjudication results
* Implement audit records
* Add state hashes
* Version policies and evaluators
* Support reproducible evaluation

### Phase 5: Reporting & Visualization

* Build evaluation dashboards
* Visualize fairness metrics
* Visualize confidence and calibration
* Compare model/evaluator versions
* Visualize policy outcomes
* Show human-review volume
* Generate audit reports

### Phase 6: Mitigation & Re-evaluation

* Add selected mitigation strategies
* Compare pre- and post-mitigation metrics
* Re-run structured evaluation
* Test whether identified issues were reduced
* Detect unintended changes introduced by mitigation

---

## 8. Deliverables

The project is intended to produce:

### Core Library

Python modules for:

* Fairness metrics
* Evaluation
* TypeSafe integration
* Policy routing
* Calibration
* Audit logging
* Counterfactual testing

### Evaluation Layer

A structured interface capable of representing:

* Binary judgments
* Categorical judgments
* Ordered severity judgments
* Confidence
* Evaluator metadata

### Calibration Toolkit

Utilities for:

* Reliability analysis
* Threshold analysis
* Score agreement
* Evaluator comparison
* Human-adjudicated validation

### Reporting Layer

Reports and visualizations for:

* Fairness metrics
* Evaluation results
* Calibration
* Policy decisions
* Human review
* Mitigation outcomes

### Documentation

Documentation covering:

* Architecture
* Installation
* Configuration
* Evaluation methodology
* Calibration methodology
* Policy design
* Auditability
* Extension points

---

## 9. Repository Architecture

The proposed repository structure is:

```text
BiasGuard/
├── src/
│   └── biasguard/
│       ├── metrics.py
│       ├── evaluation.py
│       ├── typesafe_adapter.py
│       ├── cli.py
│       └── __init__.py
│
├── tests/
│   ├── test_metrics.py
│   └── test_evaluation.py
│
├── reports/
│
├── README.md
├── TECHNICAL_SPEC.md
├── PROPOSAL.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CITATION.cff
└── pyproject.toml
```

The external structured-evaluation provider should remain isolated behind an adapter.

This prevents the core policy and governance architecture from becoming dependent on a single evaluator implementation.

---

## 10. Alignment with Current AI Evaluation Practice

BiasGuard is designed around a broader shift from simply asking whether an AI system is "biased" toward evaluating the complete decision lifecycle.

The system therefore emphasizes:

* Structured evaluation
* Calibration
* Uncertainty
* Human oversight
* Reproducibility
* Policy transparency
* Auditability
* Continuous evaluation

Rather than producing a single opaque score, BiasGuard preserves the evidence and reasoning path behind an operational decision.

---

## 11. Long-Term Direction

The long-term objective is to evolve BiasGuard into a general-purpose governance and evaluation infrastructure layer for AI-driven decisions.

The initial hiring domain provides a concrete environment for developing:

* Fairness measurement
* Counterfactual testing
* Structured evaluation
* Calibration
* Human review
* Policy routing
* Auditability

The same architecture could eventually be applied to other decision systems where AI outputs require measurable evaluation and controlled oversight.

The core abstraction is:

```text
                 AI Decision
                     │
                     ▼
                Measurement
                     +
                Evaluation
                     │
                     ▼
                Calibration
                     │
                     ▼
                  Policy
                     │
                     ▼
             Human Oversight
                     │
                     ▼
                 Audit Log
```

BiasGuard therefore aims to become more than a fairness-metrics library.

Its objective is to provide an infrastructure layer for understanding **what an AI system decided, why the evaluation considered it problematic or acceptable, how reliable that evaluation was, what policy was applied, and what happened afterward.**

---

## 12. Success Criteria

The project should be considered successful when a user can take an AI-driven decision system and answer, programmatically and reproducibly:

1. **What happened?**
2. **What statistical evidence exists?**
3. **What structured judgments were made?**
4. **How confident were those judgments?**
5. **How reliable has the evaluator historically been?**
6. **What policy was applied?**
7. **Why was the case passed, logged, reviewed, or blocked?**
8. **Was a human involved?**
9. **What changed after mitigation?**
10. **Can the complete evaluation be audited later?**

These criteria define BiasGuard as an evaluation and governance system rather than simply a collection of fairness metrics.

---

## References

The project should maintain references for:

* Fairness metric definitions
* Counterfactual testing methodology
* Structured evaluation methodology
* Calibration methodology
* Human-review practices
* Applicable responsible-AI and regulatory guidance

References should be maintained as implementation-specific sources are incorporated into the project documentation.
