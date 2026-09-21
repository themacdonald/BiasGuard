# BiasGuard

Evidence-driven evaluation and governance toolkit for AI decision systems.

## Architecture

Deterministic Measurement → Structured Evaluation → Uncertainty → Governance → Human Adjudication → Remediation → Re-evaluation → Verification

## v0.6 foundation

- Deterministic fairness audit from CSV
- Validated protected/reference group splitting
- Exact DIR calculation with explicit undefined semantics
- SPD and EOD with denominator validation
- JSON and Markdown audit reporting
- Structured Noul / Score / Choice evaluation layer
- TypeSafe adapter
- Calibration and threshold analysis
- Governance protocol and append-only ledger prototype
- Governance dashboard prototype

The deterministic audit layer intentionally measures observed outcomes before any evaluator or governance interpretation is applied.

See `AUDIT_FOUNDATION.md` and `GOVERNANCE_PROTOCOL.md`.
