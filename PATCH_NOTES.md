# BiasGuard v0.6 Foundation Patch

This patch addresses the two highest-priority repository concerns before further
governance work:

1. Correct and harden fairness metric calculations.
2. Add the CSV/group-split foundation for the original audit issues.

## Changed files

- `src/biasguard/metrics.py`
- `src/biasguard/data.py`
- `src/biasguard/audit.py`
- `src/biasguard/cli.py`
- `tests/test_metrics.py`
- `tests/test_data.py`
- `tests/test_audit.py`
- `AUDIT_FOUNDATION.md`

## Important behavior changes

- DIR is calculated directly from exact selection rates.
- Undefined DIR is represented as `None`, not `0.0`.
- EOD is `None` when either group's TPR is undefined.
- Empty samples are rejected.
- Non-binary labels are rejected.
- Required CSV columns are validated.
- Missing required values require explicit `--allow-missing`.
- Missing protected/reference groups fail the audit.
- Audit output includes sample counts and warnings.
- The audit layer remains deterministic and independent of TypeSafe/LLMs.

## Validation

The deterministic foundation suite passes independently.

The CLI file is syntax-checked in isolation because this patch is intended to be
applied on top of the current repository, whose existing evaluation/calibration
modules are intentionally not duplicated here.
