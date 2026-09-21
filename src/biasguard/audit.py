from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .data import AuditDataset, load_csv_audit_data
from .metrics import (
    FairnessReport,
    disparate_impact_ratio,
    equal_opportunity_difference,
    selection_rate,
    statistical_parity_difference,
    true_positive_rate,
)


def build_fairness_report(dataset: AuditDataset) -> dict[str, Any]:
    report = FairnessReport(
        dir=disparate_impact_ratio(dataset.y_pred_protected, dataset.y_pred_reference),
        spd=statistical_parity_difference(
            dataset.y_pred_protected, dataset.y_pred_reference
        ),
        eod=equal_opportunity_difference(
            dataset.y_true_protected,
            dataset.y_pred_protected,
            dataset.y_true_reference,
            dataset.y_pred_reference,
        ),
    )

    warnings: list[str] = []
    if report.dir is None:
        warnings.append(
            "DIR is undefined because the reference group selection rate is zero."
        )
    if report.eod is None:
        warnings.append(
            "EOD is undefined because at least one group has no positive ground-truth examples."
        )

    return {
        "groups": {
            "protected": dataset.protected_group,
            "reference": dataset.reference_group,
        },
        "sample": {
            "total_rows": dataset.total_rows,
            "included_rows": dataset.included_rows,
            "excluded_rows": dataset.excluded_rows,
        },
        "selection_rates": {
            "protected": selection_rate(dataset.y_pred_protected),
            "reference": selection_rate(dataset.y_pred_reference),
        },
        "true_positive_rates": {
            "protected": true_positive_rate(
                dataset.y_true_protected, dataset.y_pred_protected
            ),
            "reference": true_positive_rate(
                dataset.y_true_reference, dataset.y_pred_reference
            ),
        },
        "metrics": asdict(report),
        "warnings": warnings,
        "method_version": "fairness-v1",
    }


def audit_csv(
    path: str,
    *,
    y_true: str,
    y_pred: str,
    group: str,
    protected: str,
    reference: str,
    allow_missing: bool = False,
) -> dict[str, Any]:
    dataset = load_csv_audit_data(
        path,
        y_true=y_true,
        y_pred=y_pred,
        group=group,
        protected=protected,
        reference=reference,
        allow_missing=allow_missing,
    )
    return build_fairness_report(dataset)


def render_markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    groups = report["groups"]
    sample = report["sample"]
    lines = [
        "# BiasGuard Fairness Audit",
        "",
        f"- Protected group: `{groups['protected']}`",
        f"- Reference group: `{groups['reference']}`",
        f"- Rows included: `{sample['included_rows']}` / `{sample['total_rows']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Disparate Impact Ratio | {metrics['dir'] if metrics['dir'] is not None else 'undefined'} |",
        f"| Statistical Parity Difference | {metrics['spd']:.6f} |",
        f"| Equal Opportunity Difference | {metrics['eod'] if metrics['eod'] is not None else 'undefined'} |",
    ]
    if report["warnings"]:
        lines += ["", "## Warnings", ""]
        lines += [f"- {warning}" for warning in report["warnings"]]
    return "\n".join(lines) + "\n"
