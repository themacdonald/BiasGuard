# Technical Specification: BiasGuard

This document defines the architecture, components, evaluation model, data flow, dependencies, and governance mechanisms for BiasGuard.

BiasGuard is an open-source evaluation and governance toolkit for auditing AI-driven decisions. It combines deterministic fairness measurements with structured AI evaluation, calibration, explicit policy rules, human review, and audit trails.

The system is designed around a core separation:

```text
Evaluation
    ↓
Calibration
    ↓
Policy
    ↓
Action
    ↓
Audit
```

BiasGuard does not treat an AI evaluator's judgment as ground truth. Evaluator outputs are evidence that must be measured, calibrated, and interpreted through explicit policy.

---

## 1. System Architecture

BiasGuard consists of the following major layers.

### 1.1 Data Ingestion & Preprocessing

The ingestion layer loads structured datasets and evaluation cases from supported sources such as CSV and JSON.

Responsibilities include:

* Dataset loading
* Schema validation
* Missing-value handling
* Feature identification
* Target-label identification
* Protected-attribute identification
* Group definition
* Basic data-quality validation
* Separation of sensitive attributes from model features where appropriate

The ingestion layer should preserve sufficient metadata to reproduce an evaluation.

---

### 1.2 Counterfactual & Sensitivity Testing

BiasGuard can generate controlled counterfactual cases in which selected attributes are changed while other relevant information remains constant.

Example:

```text
Candidate A
Gender = Male
        ↓
Candidate A'
Gender = Female
```

The purpose is to investigate whether a decision or model output changes when a selected attribute changes.

Counterfactual testing is an evaluation technique, not proof of discrimination by itself.

The system should record:

* Original state
* Modified state
* Attribute changed
* Model outputs
* Difference in outputs
* Evaluation context

---

### 1.3 Deterministic Fairness Measurement

The fairness engine provides deterministic statistical measurements over model predictions and labeled outcomes.

Current metrics include:

* Disparate Impact Ratio
* Statistical Parity Difference
* Equal Opportunity Difference

Additional metrics can be added through the same interface.

For example:

```text
Disparate Impact Ratio
    =
Selection Rate (Protected Group)
/
Selection Rate (Reference Group)
```

```text
Statistical Parity Difference
    =
Selection Rate (Protected Group)
-
Selection Rate (Reference Group)
```

```text
Equal Opportunity Difference
    =
TPR (Protected Group)
-
TPR (Reference Group)
```

These measurements remain independent from AI-generated judgments.

A structured evaluator cannot override a deterministic metric.

---

## 2. Structured Evaluation Layer

BiasGuard can use a typed evaluation layer to assess properties of individual decisions or outputs that are difficult to measure directly with aggregate statistical metrics.

The evaluation layer uses structured question types according to the shape of the judgment.

### 2.1 Binary Evaluation

Binary questions represent propositions that can be evaluated as yes/no.

Examples:

* Does the decision rely on an unfair generalization?
* Does the output contain a potentially discriminatory rationale?
* Does a protected characteristic plausibly influence the decision?
* Does the visualization imply a conclusion that the underlying data does not support?

Binary evaluations should contain one proposition per question.

---

### 2.2 Categorical Evaluation

Categorical evaluation is used when a case must be assigned to one category.

Examples:

* Bias type
* Root cause
* Review track
* Mitigation category

Possible output:

```text
gender
race
age
disability
proxy
none
other
```

---

### 2.3 Ordered Severity Evaluation

Ordered evaluation is used for concepts that exist on a meaningful spectrum.

Examples:

```text
0 = No identified issue
1 = Minor
2 = Moderate
3 = Severe
4 = Systemic
```

Potential dimensions include:

* Severity
* Potential harm
* Degree of decision distortion
* Visualization distortion

Complex judgments should be decomposed into separate dimensions rather than compressed into a single opaque score.

For example:

```text
Severity
+
Potential Harm
+
Evidence Strength
```

can be combined by deterministic policy code rather than asking an evaluator to produce one unexplained "risk score."

---

## 3. Evaluation Reliability & Calibration

Structured evaluation outputs are not assumed to be correct simply because the evaluator reports high confidence.

BiasGuard therefore provides an offline calibration layer.

Calibration uses stored evaluator judgments and human-adjudicated labels.

### 3.1 Binary Calibration

For binary judgments, BiasGuard can calculate:

* Brier score
* Expected Calibration Error
* Reliability by probability bin
* Precision
* Recall
* False-positive rate
* False-negative rate
* Human-review volume

Calibration should be evaluated independently for relevant questions and protected groups.

For example:

```text
bias_gender
bias_race
bias_age
```

should not automatically be collapsed into a single aggregate measurement.

---

### 3.2 Ordered Score Calibration

For severity or harm scores, BiasGuard can measure:

* Exact agreement
* Agreement within one level
* Mean Absolute Error
* Average confidence
* Low-confidence rate

This allows the system to determine whether evaluator confidence behaves consistently with observed agreement.

---

### 3.3 Categorical Calibration

For categorical judgments, BiasGuard can measure:

* Overall agreement
* Per-class accuracy
* Class distribution
* Confusion between categories

---

### 3.4 Policy Threshold Analysis

Calibration and policy selection are separate operations.

Calibration answers:

> How reliable is the evaluator?

Threshold analysis answers:

> What happens if this policy threshold is selected?

BiasGuard should therefore expose threshold trade-offs without automatically declaring a threshold to be correct.

For example:

```text
Threshold
Flagged Cases
Missed Issues
False Positives
False Negatives
Human Review Volume
```

Policy thresholds should ultimately be selected using relevant labeled data, organizational requirements, error costs, and review capacity.

---

## 4. Policy Engine

The policy engine converts evaluation evidence into an explicit operational outcome.

Possible outcomes include:

```text
PASS
LOG_ONLY
HUMAN_REVIEW
BLOCK
```

The policy engine can consider:

* Deterministic fairness metrics
* Structured evaluator judgments
* Confidence
* Severity
* Potential harm
* Detector evidence
* Review requirements
* Configured thresholds
* Policy version

Example conceptual routing:

```text
Evaluation
     │
     ├── High confidence + low risk ───────► PASS
     │
     ├── Moderate concern ─────────────────► LOG_ONLY
     │
     ├── Ambiguous / uncertain ─────────────► HUMAN_REVIEW
     │
     └── High severity + sufficient evidence ► BLOCK
```

The exact thresholds are configuration and policy decisions rather than universal constants.

---

## 5. Human Review

Human review is a first-class component of the architecture.

Cases may be routed to human reviewers when:

* Evaluator confidence is low
* Multiple evaluators disagree
* Evidence is incomplete
* Severity is uncertain
* A configured review threshold is reached
* The consequences of an incorrect automated decision are significant

The system should preserve the human adjudication result so that it can later be used for calibration.

This creates a feedback loop:

```text
Automated Evaluation
        ↓
Human Review
        ↓
Adjudicated Label
        ↓
Calibration Dataset
        ↓
Evaluator Analysis
```

Human review should therefore improve the evidence base without silently changing policy rules.

---

## 6. Audit Trail

Every evaluation should produce an auditable record.

A conceptual evaluation record is:

```json
{
  "state_hash": "...",
  "model": "...",
  "judgments": {},
  "result": {},
  "policy_version": "...",
  "timestamp": "..."
}
```

The audit trail should make it possible to determine:

* What was evaluated?
* What state was evaluated?
* Which evaluator/model was used?
* What judgments were produced?
* What probabilities and confidence values were returned?
* Which policy was applied?
* What action resulted?
* Was a human involved?
* What version of the policy produced the result?
* Can the evaluation be reproduced?

State hashes provide a mechanism for associating stored labels and later calibration results with the original evaluation state.

---

## 7. Mitigation

Mitigation is treated as a downstream intervention rather than an automatic consequence of a fairness metric.

Potential mitigation strategies include:

* Data re-weighting
* Re-sampling
* Feature review
* Threshold adjustment
* Model retraining
* Counterfactual testing
* Output or rationale revision

BiasGuard should distinguish between:

```text
Detection
    ↓
Evaluation
    ↓
Policy Decision
    ↓
Mitigation
    ↓
Re-evaluation
```

A mitigation should not be considered successful merely because one metric improved.

The remediated system should be evaluated again to determine whether:

* The original issue was reduced or resolved
* Other fairness metrics changed
* Model performance changed
* New issues were introduced
* Relevant information was preserved

---

## 8. Reporting & Visualization

BiasGuard should provide machine-readable and human-readable evaluation outputs.

Reporting should support:

* Fairness metrics
* Group-level comparisons
* Counterfactual differences
* Structured evaluator judgments
* Confidence distributions
* Calibration results
* Policy outcomes
* Human-review rates
* Model-version comparisons
* Before/after mitigation analysis
* Audit records

The visualization layer should distinguish between:

### Measurement

What the data and model outputs show.

### Evaluation

What a structured evaluator judged.

### Policy

What configured rules decided.

### Action

What happened as a result.

These categories should not be visually merged into a single "bias score."

---

## 9. Configuration

BiasGuard should use explicit configuration for:

* Protected attributes
* Reference groups
* Evaluation questions
* Policy thresholds
* Human-review thresholds
* Severity levels
* Mitigation rules
* Reporting options
* Model/evaluator identifiers

Example conceptual configuration:

```yaml
policy:
  review_at_severity: 2
  block_at_severity: 3
  min_severity_confidence: 0.55

evaluation:
  bias_yes: 0.80
  bias_no: 0.20

weights:
  severity: 0.60
  harm: 0.30
  detector: 0.10
```

These values are configuration examples, not universal fairness standards.

They should be validated against labeled evaluation data before being used operationally.

---

## 10. Dependencies

The current core package is intentionally lightweight.

### Required

* Python >= 3.10
* Standard Python library

### Development

* `pytest`
* `ruff`

### Optional / Future

Depending on the implementation layer:

* `pandas` for larger-scale dataset processing
* `numpy` for numerical workloads
* `scikit-learn` for model evaluation and preprocessing
* `fairlearn` for additional fairness analysis
* `aif360` for additional fairness and mitigation methods
* `plotly` for interactive visualization
* `streamlit` for an interactive dashboard
* TypeSafe SDK for structured evaluator integration

Optional dependencies should remain optional unless they become necessary for the core package.

---

## 11. Data Flow

The intended high-level data flow is:

```text
                    Dataset / AI Output
                           │
                           ▼
                  ┌─────────────────┐
                  │ Data Validation │
                  └────────┬────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      Fairness Measurement       Structured Evaluation
             │                           │
             │                    Noul / Choice / Score
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    Calibration Data
                           │
                           ▼
                     Policy Engine
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
           PASS        HUMAN REVIEW      BLOCK
             │             │
             │             ▼
             │       Human Adjudication
             │             │
             └─────────────┴─────────────┐
                                         ▼
                                   Audit Record
                                         │
                                         ▼
                                    Calibration
```

For mitigation workflows:

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
Compare Results
      ↓
Audit
```

---

## 12. Core Design Principles

### 12.1 Evaluation Is Not Truth

An evaluator can be confidently wrong.

Confidence therefore represents evaluator uncertainty, not guaranteed correctness.

---

### 12.2 Deterministic Measurements Remain Independent

Statistical fairness metrics should not be replaced by an AI-generated judgment.

The two layers answer different questions.

```text
Fairness metrics:
"What does the observed data show?"

Structured evaluation:
"What does the evaluator judge about this case?"

Policy:
"What should the system do given this evidence?"
```

---

### 12.3 Complex Judgments Should Be Decomposed

Instead of:

```text
"Is this decision biased?"
```

BiasGuard should prefer independent questions such as:

```text
Is there evidence of unfair treatment?
What type of issue is present?
How severe is it?
What potential harm exists?
How confident is the evaluation?
What review track is appropriate?
```

The final operational decision is then composed deterministically.

---

### 12.4 Uncertainty Should Be Actionable

Low confidence should not simply be discarded.

It can become a routing signal:

```text
Low confidence
      ↓
Human review
      ↓
Adjudicated result
      ↓
Calibration dataset
```

---

### 12.5 Calibration Is Evidence, Not Policy

Calibration results should inform policy design but should not silently modify policy thresholds.

This separation prevents the evaluator from becoming its own authority.

---

### 12.6 Every Decision Should Be Explainable Retrospectively

An auditor should be able to reconstruct:

```text
Input
  ↓
Evaluation
  ↓
Evidence
  ↓
Policy
  ↓
Action
```

without relying on undocumented assumptions.

---

## 13. Scalability & Deployment

BiasGuard is currently designed for local development, research, and open-source experimentation.

### Local

```text
Python package
    ↓
CLI / scripts
    ↓
JSON / JSONL audit records
```

### Interactive

```text
BiasGuard
    ↓
Streamlit / web interface
    ↓
Evaluation dashboards
```

### Larger Deployments

A future deployment can use:

* Docker
* Persistent storage
* Background evaluation workers
* Cached metric computations
* Centralized audit storage
* Versioned evaluation policies
* Model/evaluator registries

The architecture should allow the evaluation engine to remain independent from the user interface.

---

## 14. Repository Architecture

The intended repository structure is:

```text
biasguard/
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
├── TECHNICAL_SPEC.md
├── PROPOSAL.md
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CITATION.cff
└── pyproject.toml
```

The evaluation adapter should isolate the external structured-evaluation provider from the core BiasGuard logic.

This allows BiasGuard's policy and audit architecture to remain independent from any single evaluator implementation.

---

## 15. Future Extensions

Potential future capabilities include:

* Additional fairness metrics
* Fairness intersectionality analysis
* Model drift monitoring
* Evaluator drift monitoring
* Dataset shift detection
* Continuous calibration
* Human-review interfaces
* Policy simulation
* Counterfactual testing at scale
* Model comparison
* Evaluation reproducibility
* Signed audit records
* Versioned policy registries
* Governance dashboards
* Compliance-oriented reporting
* Additional structured evaluation providers

These extensions should preserve the central architecture:

```text
Measurement
    +
Evaluation
    ↓
Calibration
    ↓
Policy
    ↓
Human Oversight
    ↓
Auditability
```

---

## 16. Summary

BiasGuard is not intended to be a single "bias score" generator.

It is an evaluation and governance system designed to separate:

1. **What can be measured deterministically**
2. **What requires structured judgment**
3. **How reliable those judgments are**
4. **What policy should apply**
5. **When humans should intervene**
6. **What happened and why**

This separation is fundamental to the system's design.

The resulting architecture allows BiasGuard to evolve from a fairness-metrics library into a broader infrastructure layer for evaluating and governing AI-driven decisions.
