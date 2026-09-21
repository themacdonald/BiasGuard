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

## 2. Current Project Status

BiasGuard is currently in an **early implementation stage**.

The repository should distinguish between functionality that is implemented, functionality currently being developed, and longer-term capabilities.

### Implemented

The current repository includes:

* Deterministic fairness metrics
* Disparate Impact Ratio
* Statistical Parity Difference
* Equal Opportunity Difference
* A basic fairness report structure
* CLI demonstration workflow
* Automated tests for the fairness metrics
* Python packaging configuration
* Continuous integration configuration

### In Development

The current architecture is being extended with:

* Structured AI evaluation
* TypeSafe integration through an adapter
* Noul, Choice, and Score evaluation primitives
* Deterministic policy composition
* Confidence-aware routing
* Human-review routing
* Evaluation state hashing
* Evaluation audit records
* Calibration utilities
* Policy threshold analysis

### Planned

Longer-term work includes:

* Counterfactual testing at scale
* Interactive dashboards
* Human adjudication interfaces
* Persistent evaluation storage
* Model/evaluator drift monitoring
* Mitigation workflows
* Re-evaluation pipelines
* Governance reporting
* Additional fairness metrics
* Production deployment infrastructure

The distinction is intentional. BiasGuard should not claim production capabilities that are not yet implemented in the repository.

---

## 3. Background and Rationale

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

## 4. Core Design Philosophy

### 4.1 Measurement and Judgment Are Different

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

### 4.2 Evaluator Confidence Is Not Truth

A structured evaluator may report high confidence and still be wrong.

BiasGuard therefore treats evaluator confidence as a measurable property rather than proof of correctness.

Stored judgments can subsequently be compared against human-adjudicated labels through calibration.

---

### 4.3 Policy Is Explicit

Operational thresholds should exist in configuration rather than being hidden inside an evaluator.

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

### 4.4 Uncertainty Can Trigger Human Review

Ambiguous cases should not necessarily be forced into an automated outcome.

BiasGuard can route cases to human review when:

* Confidence is low
* Evaluations conflict
* Evidence is incomplete
* Severity is uncertain
* A configured review threshold is reached

Human adjudication can subsequently become part of the calibration dataset.

---

## 5. Target Audience

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

## 6. Core Use Cases

### 6.1 Dataset Analysis

**Status: Implemented at the metric layer; broader ingestion planned.**

Load decision data and calculate:

* Group distributions
* Selection rates
* Outcome differences
* Fairness metrics

Broader schema validation, preprocessing, and dataset management remain future work.

---

### 6.2 Counterfactual Testing

**Status: Planned.**

Create controlled variations of an input while changing selected attributes.

```text
Original
Gender = Male
        ↓
Counterfactual
Gender = Female
```

The system can eventually compare model outputs and identify whether the decision changes.

Counterfactual differences should be treated as evidence for investigation rather than automatic proof of discrimination.

---

### 6.3 Fairness Measurement

**Status: Implemented.**

The current fairness engine includes:

* Disparate Impact Ratio
* Statistical Parity Difference
* Equal Opportunity Difference

These metrics are implemented as deterministic functions and have automated tests.

Additional metrics can be added without changing the overall architecture.

---

### 6.4 Structured Decision Evaluation

**Status: In development.**

The planned evaluation layer uses structured questions for individual AI outputs.

Examples include:

**Binary**

> Does the output rely on an unfair generalization?

**Categorical**

> What type of issue is present?

**Ordered**

> How severe is the identified issue?

The evaluation adapter is designed to isolate the external structured-evaluation provider from the core BiasGuard architecture.

---

### 6.5 Evaluator Calibration

**Status: In development.**

Stored evaluator judgments can be compared with human-adjudicated labels.

For binary questions:

* Brier score
* Expected Calibration Error
* Reliability by probability bin
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

Calibration is intended to provide evidence about evaluator reliability rather than automatically selecting policy thresholds.

---

### 6.6 Policy Simulation

**Status: In development.**

BiasGuard is being designed to analyze how different policy thresholds affect:

* Cases flagged
* Cases missed
* False positives
* False negatives
* Human-review volume
* Automated blocks

Threshold analysis should expose trade-offs rather than automatically declaring a threshold correct.

---

### 6.7 Human Review

**Status: In development.**

Cases that meet configured review conditions can be routed for human adjudication.

The resulting decision can be stored as an auditable label and subsequently used for calibration.

```text
AI Evaluation
      ↓
Human Review
      ↓
Adjudicated Label
      ↓
Calibration
      ↓
Evaluator Reliability Analysis
```

---

### 6.8 Mitigation and Re-evaluation

**Status: Planned.**

Potential interventions include:

* Re-weighting
* Resampling
* Feature review
* Threshold adjustment
* Model retraining
* Output revision
* Counterfactual testing

Mitigation should be followed by re-evaluation.

The system should compare the original and remediated results rather than assuming that an intervention succeeded because one metric improved.

---

### 6.9 Governance and Audit Reporting

**Status: Partially implemented / in development.**

The current evaluation architecture includes the foundations for recording:

* Evaluation state
* Evaluator/model identifier
* Structured judgments
* Policy result
* State hash
* Timestamp

A complete governance reporting system remains under development.

---

## 7. Proposed Architecture

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

The important architectural boundary is:

```text
TypeSafe / evaluator
        ↓
    evaluates
        ↓
BiasGuard
        ↓
    governs
```

The evaluator is not the policy authority.

---

## 8. Project Plan

### Phase 1: Deterministic Measurement

**Status: Implemented / stabilization**

* Fairness metric implementations
* Metric validation
* Automated tests
* Basic CLI demonstration
* Python packaging

### Phase 2: Structured Evaluation

**Status: In development**

* Structured evaluation adapter
* Binary judgments
* Categorical judgments
* Ordered severity judgments
* Confidence handling
* Deterministic policy composition

### Phase 3: Calibration

**Status: In development**

* Judgment storage
* Human-adjudicated labels
* Binary calibration
* Score calibration
* Categorical evaluation analysis
* Threshold trade-off analysis
* Evaluator/model version comparison

### Phase 4: Human Review & Audit

**Status: In development**

* Human-review routing
* Adjudication storage
* State hashes
* Policy versioning
* Audit records
* Reproducible evaluation

### Phase 5: Reporting & Visualization

**Status: Planned**

* Fairness dashboards
* Calibration dashboards
* Confidence visualization
* Model/evaluator comparisons
* Policy outcome visualization
* Audit reports

### Phase 6: Mitigation & Re-evaluation

**Status: Planned**

* Mitigation strategies
* Before/after comparison
* Re-evaluation
* Regression detection
* Unintended-impact analysis

---

## 9. Deliverables

### Current

* Python fairness metric library
* Metric test suite
* CLI demonstration
* Package configuration
* Project documentation

### In Development

* Structured evaluation layer
* TypeSafe adapter
* Policy evaluation
* Calibration toolkit
* Evaluation audit records

### Planned

* Interactive dashboard
* Counterfactual testing framework
* Human-review interface
* Mitigation workflows
* Governance reporting
* Production deployment components

---

## 10. Repository Architecture

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

The external structured-evaluation provider is isolated behind an adapter so that BiasGuard's policy and governance architecture does not become dependent on a single provider.

---

## 11. Success Criteria

BiasGuard should ultimately allow a user to answer, programmatically and reproducibly:

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

## 12. Long-Term Direction

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

BiasGuard is therefore being developed from a fairness-metrics toolkit toward an infrastructure layer for evaluating and governing AI-driven decisions.

The project's long-term value lies in preserving the distinction between **evidence, judgment, policy, and action**.

---

## 13. Success Definition

The project reaches its intended maturity when the evaluation lifecycle is reproducible:

```text
Input
  ↓
Measurement
  ↓
Structured Evaluation
  ↓
Calibration
  ↓
Policy
  ↓
Action
  ↓
Human Review, when required
  ↓
Audit
  ↓
Re-evaluation
```

Each stage should have a defined input, output, version, and testable behavior.

This makes BiasGuard extensible beyond hiring while preserving a concrete initial application domain.
