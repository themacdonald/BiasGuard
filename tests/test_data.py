from pathlib import Path

import pytest

from biasguard.data import AuditDataError, load_csv_audit_data


def write_csv(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "audit.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_csv_loader_splits_groups(tmp_path):
    path = write_csv(
        tmp_path,
        "truth,pred,gender\n1,1,F\n1,0,F\n0,0,M\n1,1,M\n",
    )
    data = load_csv_audit_data(
        path,
        y_true="truth",
        y_pred="pred",
        group="gender",
        protected="F",
        reference="M",
    )
    assert data.y_true_protected == [1, 1]
    assert data.y_pred_protected == [1, 0]
    assert data.y_true_reference == [0, 1]
    assert data.y_pred_reference == [0, 1]


def test_missing_columns_are_rejected(tmp_path):
    path = write_csv(tmp_path, "truth,pred\n1,1\n")
    with pytest.raises(AuditDataError, match="Missing required"):
        load_csv_audit_data(
            path, y_true="truth", y_pred="pred", group="gender",
            protected="F", reference="M",
        )


def test_missing_values_require_explicit_opt_in(tmp_path):
    path = write_csv(
        tmp_path,
        "truth,pred,gender\n1,1,F\n,0,M\n0,1,M\n",
    )
    with pytest.raises(AuditDataError, match="allow-missing"):
        load_csv_audit_data(
            path, y_true="truth", y_pred="pred", group="gender",
            protected="F", reference="M",
        )

    data = load_csv_audit_data(
        path, y_true="truth", y_pred="pred", group="gender",
        protected="F", reference="M", allow_missing=True,
    )
    assert data.excluded_rows == 1
    assert data.included_rows == 2


def test_invalid_binary_values_are_rejected(tmp_path):
    path = write_csv(
        tmp_path,
        "truth,pred,gender\n1,maybe,F\n0,0,M\n",
    )
    with pytest.raises(AuditDataError, match="Invalid binary"):
        load_csv_audit_data(
            path, y_true="truth", y_pred="pred", group="gender",
            protected="F", reference="M",
        )


def test_empty_group_is_rejected(tmp_path):
    path = write_csv(tmp_path, "truth,pred,gender\n1,1,F\n")
    with pytest.raises(AuditDataError, match="reference group"):
        load_csv_audit_data(
            path, y_true="truth", y_pred="pred", group="gender",
            protected="F", reference="M",
        )
