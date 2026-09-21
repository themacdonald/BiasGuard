# Implementation Notes

## Why this is the first milestone

The repository already has deterministic fairness metrics. The next architectural boundary is the evaluation layer.

The implementation intentionally keeps three concerns separate:

1. `metrics.py` measures observed group-level behavior.
2. `typesafe_adapter.py` represents the external evaluator contract.
3. `evaluation.py` owns BiasGuard policy composition and audit records.

## What is intentionally not included yet

- Direct dependency on a TypeSafe SDK.
- Automatic mitigation.
- Automatic threshold calibration.
- Persistent database storage.
- Dashboard UI.
- Human-review UI.

Those should be implemented after the evaluation contract is stable.

## Policy behavior

The default policy is deliberately conservative:

- High-confidence severe issues can produce `block`.
- Ambiguous or low-confidence evaluations route to `human_review`.
- Moderate concerns route to `human_review`.
- Lower-level concerns can produce `log_only`.
- Otherwise the result is `pass`.

Thresholds are configuration, not universal fairness standards.
