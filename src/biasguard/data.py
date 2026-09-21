from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class AuditDataError(ValueError):
    """Raised when an audit dataset cannot be safely interpreted."""


@dataclass(frozen=True)
class AuditDataset:
    y_true_protected: list[int]
    y_pred_protected: list[int]
    y_true_reference: list[int]
    y_pred_reference: list[int]
    protected_group: str
    reference_group: str
    total_rows: int
    included_rows: int
    excluded_rows: int
    excluded_row_numbers: tuple[int, ...] = ()


def _parse_binary(value: str, column: str, row_number: int) -> int:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "positive"}:
        return 1
    if normalized in {"0", "false", "no", "negative"}:
        return 0
    raise AuditDataError(
        f"Invalid binary value {value!r} in column {column!r} at CSV row {row_number}. "
        "Expected 0/1, true/false, yes/no, or positive/negative."
    )


def load_csv_audit_data(
    path: str | Path,
    *,
    y_true: str,
    y_pred: str,
    group: str,
    protected: str,
    reference: str,
    allow_missing: bool = False,
) -> AuditDataset:
    """Load and safely split a CSV into protected/reference audit samples.

    Missing required values are excluded only when allow_missing=True.
    Otherwise the first missing row is reported as an actionable error.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise AuditDataError(f"Dataset not found: {file_path}")

    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        required = [y_true, y_pred, group]
        missing_columns = [name for name in required if name not in columns]
        if missing_columns:
            raise AuditDataError(
                "Missing required column(s): " + ", ".join(repr(x) for x in missing_columns)
            )

        protected_rows: list[tuple[int, int, int]] = []
        reference_rows: list[tuple[int, int, int]] = []
        excluded: list[int] = []
        total = 0

        for row_number, row in enumerate(reader, start=2):
            total += 1
            values = [row.get(y_true), row.get(y_pred), row.get(group)]
            if any(value is None or not str(value).strip() for value in values):
                if allow_missing:
                    excluded.append(row_number)
                    continue
                raise AuditDataError(
                    f"Missing required value at CSV row {row_number}. "
                    "Use --allow-missing to exclude incomplete rows explicitly."
                )

            group_value = str(row[group]).strip()
            if group_value not in {protected, reference}:
                continue

            yt = _parse_binary(str(row[y_true]), y_true, row_number)
            yp = _parse_binary(str(row[y_pred]), y_pred, row_number)

            if group_value == protected:
                protected_rows.append((yt, yp, row_number))
            else:
                reference_rows.append((yt, yp, row_number))

    if not protected_rows:
        raise AuditDataError(f"No usable rows found for protected group {protected!r}.")
    if not reference_rows:
        raise AuditDataError(f"No usable rows found for reference group {reference!r}.")

    return AuditDataset(
        y_true_protected=[row[0] for row in protected_rows],
        y_pred_protected=[row[1] for row in protected_rows],
        y_true_reference=[row[0] for row in reference_rows],
        y_pred_reference=[row[1] for row in reference_rows],
        protected_group=protected,
        reference_group=reference,
        total_rows=total,
        included_rows=len(protected_rows) + len(reference_rows),
        excluded_rows=len(excluded),
        excluded_row_numbers=tuple(excluded),
    )
