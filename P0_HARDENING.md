# v0.6 P0 Trust-Boundary Hardening

This increment hardens the two external-data boundaries identified in review:

1. Structured evaluator payloads are validated before normalization.
2. Calibration pairing reports invalid, unmatched, and missing records.

## Evaluator contract

`BiasGuardEvaluator.evaluate()` now:

- rejects non-mapping responses;
- validates the `answers` mapping;
- validates question definitions;
- validates confidence and probability ranges;
- validates score values;
- counts missing expected answers;
- counts unknown extra answer IDs;
- stores validation diagnostics in the auditable evaluation record.

Unknown IDs are not fatal because forward-compatible providers may add fields.
Expected-question contract violations remain fatal.

## Calibration contract

Calibration reports now expose:

- `supplied`
- `valid`
- `invalid`
- `unmatched`
- `missing_answer`
- `evaluated`

This prevents malformed or unmatched records from silently disappearing from
the denominator.

## Metric semantics

The deterministic fairness layer continues to represent undefined DIR/EOD as
`None` rather than converting an undefined ratio into a numeric result.
