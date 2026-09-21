# BiasGuard Evaluation Layer

This patch adds the first executable layer of the BiasGuard architecture.

## What it adds

- `typesafe_adapter.py`
  - Defines a minimal `TypeSafeClient` protocol.
  - Normalizes evaluator observations.
  - Keeps the external TypeSafe SDK optional.
- `evaluation.py`
  - Defines policy thresholds.
  - Builds typed evaluation questions.
  - Composes Noul/Choice/Score observations into deterministic policy outcomes.
  - Generates stable state hashes.
  - Creates auditable evaluation records.
- `tests/test_evaluation.py`
  - Tests typed questions, policy routing, uncertainty handling, state hashing, and audit records.

## Important boundary

The adapter deliberately does not hard-code a TypeSafe SDK import or an undocumented API response shape.

BiasGuard owns:

```text
evaluation evidence
        ↓
policy composition
        ↓
action routing
        ↓
audit record
```

The external evaluator owns the structured judgment.

A concrete SDK adapter can implement:

```python
class MyTypeSafeClient:
    def evaluate(self, state, questions):
        ...
```

and return:

```python
{
    "answers": {
        "bias_gender": {
            "value": True,
            "probability": 0.92,
            "confidence": 0.90
        }
    }
}
```

The exact provider integration should be added only after the SDK contract is pinned to the actual installed TypeSafe package/API.

## Fail-closed behavior

`BiasGuardEvaluator.evaluate()` refuses to run without a configured structured evaluator. This prevents the system from silently presenting an unevaluated case as a valid automated judgment.

Policy composition itself remains dependency-free and fully testable.
