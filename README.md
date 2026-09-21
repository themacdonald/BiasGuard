# BiasGuard

**BiasGuard is an open-source evaluation and governance toolkit for auditing AI-driven decisions.**

It combines deterministic fairness metrics with structured AI evaluation, calibrated judgments, explicit policy thresholds, and human review to make AI decisions more measurable, auditable, and accountable.

BiasGuard is designed around a simple principle:

> **AI judgments should be evaluated, not blindly trusted.**

## What BiasGuard Does

BiasGuard evaluates AI-driven decisions from multiple perspectives:

* **Deterministic Fairness Analysis:** Compute established fairness metrics such as Disparate Impact Ratio, Statistical Parity Difference, and Equal Opportunity Difference.
* **Structured AI Evaluation:** Use typed evaluations such as yes/no judgments, categorical classifications, and ordered severity scores to examine potential bias, framing, evidence, and other decision risks.
* **Policy-Based Decision Routing:** Convert evaluation results into explicit outcomes such as `pass`, `log_only`, `human_review`, or `block` using configurable thresholds.
* **Uncertainty Handling:** Treat ambiguous or low-confidence judgments as signals for human review rather than forcing an automated decision.
* **Calibration:** Evaluate whether evaluator probabilities correspond to observed outcomes using stored judgments and human-adjudicated labels.
* **Audit Trail:** Record evaluator outputs, model versions, state hashes, policy results, and relevant metadata so decisions can be inspected retrospectively.
* **Counterfactual Testing:** Support controlled tests that change selected attributes while holding other inputs constant to investigate potential sensitivity to protected characteristics.
* **Evaluation Analytics:** Compare evaluator performance, policy outcomes, confidence, error rates, and calibration across questions, datasets, and model versions.

## Architecture

BiasGuard separates **evaluation** from **decision policy**.

```text
                 AI Decision / Output
                         │
                         ▼
                ┌───────────────────┐
                │     BiasGuard     │
                │   Evaluation      │
                └─────────┬─────────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
     Deterministic Metrics       Structured Evaluation
     ───────────────────         ─────────────────────
     • Disparate Impact          • Noul
     • Statistical Parity        • Choice
     • Equal Opportunity         • Score
             │                         │
             └────────────┬────────────┘
                          ▼
                 ┌─────────────────┐
                 │  Policy Engine  │
                 │                 │
                 │ thresholds      │
                 │ uncertainty     │
                 │ risk rules      │
                 └────────┬────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
           PASS       HUMAN REVIEW    BLOCK
                          │
                          ▼
                  ┌───────────────┐
                  │   Audit Log   │
                  └───────┬───────┘
                          │
                          ▼
                    Calibration
```

The important boundary is that **structured AI evaluation does not become the source of truth by itself**.

A high-confidence evaluator judgment can still be wrong. BiasGuard therefore separates:

```text
evaluation
    ↓
calibration
    ↓
policy
    ↓
action
```

## Evaluation Layer

BiasGuard can use structured evaluation questions for different types of judgments.

### Noul

Binary propositions such as:

* Does the output rely on an unfair generalization?
* Does the visualization make an unsupported claim?
* Does the output use color to imply an undefined judgment?
* Does a protected characteristic plausibly influence the recommendation?

### Choice

Categorical judgments such as:

* What type of bias is implicated?
* What review track is appropriate?
* What is the likely source of an identified issue?

### Score

Ordered judgments such as:

* Severity of unfair treatment
* Potential harm
* Degree of visualization distortion

Complex judgments are intentionally separated into independent questions instead of being compressed into a single opaque "is this biased?" score.

## Calibration

BiasGuard supports **offline calibration over stored judgments**.

Calibration uses human-adjudicated cases to evaluate whether structured evaluator outputs are reliable.

For binary judgments, BiasGuard can measure:

* Brier score
* Expected Calibration Error
* Reliability by probability bin
* False positives
* False negatives
* Precision
* Recall
* Human-review volume

For ordered scores, BiasGuard can measure:

* Exact agreement
* Agreement within one level
* Mean Absolute Error
* Confidence behavior

For categorical judgments, BiasGuard can measure:

* Overall agreement
* Per-class accuracy

The calibration system does not automatically choose policy thresholds. It provides evidence that can be used to evaluate threshold choices.

## Policy and Human Review

BiasGuard does not assume that every evaluation should result in an automated action.

A judgment can produce:

```text
PASS
LOG_ONLY
HUMAN_REVIEW
BLOCK
```

Low-confidence or conflicting evaluations can be routed to human review.

Thresholds are configurable and should be validated against an organization's labeled evaluation data, error costs, review capacity, and applicable requirements.

## Auditability

Each evaluation can preserve information such as:

```json
{
  "state_hash": "…",
  "model": "…",
  "judgments": {},
  "result": {},
  "policy_version": "…"
}
```

This makes it possible to investigate:

* What was evaluated?
* Which evaluator/model produced the judgment?
* What probabilities and confidence values were returned?
* Which policy was applied?
* Why was the case passed, reviewed, or blocked?
* How reliable was that evaluator historically?

## Fairness Metrics

The current fairness engine includes:

* **Disparate Impact Ratio**
* **Statistical Parity Difference**
* **Equal Opportunity Difference**

These measurements remain deterministic and independent of structured evaluator judgments.

BiasGuard does not treat a single fairness metric as a universal definition of fairness. Different metrics measure different properties and should be interpreted within the relevant decision context.

## Quick Start

Install the package in editable mode:

```sh
pip install -e .
```

Run the current demonstration:

```sh
biasguard --demo
```

The demo generates a small fairness report at:

```text
reports/report.json
```

## Project Direction

BiasGuard is being developed toward a broader evaluation and governance framework for AI-driven decisions.

The long-term architecture is intended to support:

```text
Data / Model Output
        ↓
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

The goal is not to build another model that simply declares an AI system "biased."

The goal is to build infrastructure that can answer:

> **What was evaluated, how was it evaluated, how uncertain was the evaluation, what evidence supported the decision, what policy was applied, and how reliable has that evaluation been historically?**

## License

BiasGuard is released under the MIT License.
