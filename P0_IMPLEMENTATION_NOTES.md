# BiasGuard v0.6 P0 Hardening Patch

This patch is intentionally narrow. It hardens two trust boundaries without
adding new product features.

## Included

- `validation.py`
  - strict evaluator response contract
  - explicit missing answers
  - unknown answer counting
  - confidence/probability bounds
  - scalar score/choice validation
  - duplicate question detection

- `calibration_coverage.py`
  - typed pairing result
  - invalid/unmatched/missing-answer accounting
  - explicit coverage report

## Important integration note

These modules are delivered as a patch for manual upload/merge because the
connected GitHub integration currently rejects repository writes.

The existing `evaluation.py` and `calibration.py` should be integrated with
these modules in the next commit rather than silently replacing their public
APIs. This bundle does not claim that integration has already happened.

## Design decision

Unknown evaluator question IDs are counted as `unknown` rather than treated as
fatal. Expected questions that are malformed, and expected answers that violate
the contract, are fatal. Missing expected answers remain explicit diagnostics.

This keeps the evaluator boundary strict without making forward-compatible
responses impossible.
