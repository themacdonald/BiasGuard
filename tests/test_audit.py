from biasguard.audit import audit_csv


def test_audit_returns_metrics(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text(
        "truth,pred,gender\n"
        "1,1,F\n"
        "1,0,F\n"
        "0,0,F\n"
        "1,1,M\n"
        "1,1,M\n"
        "0,0,M\n",
        encoding="utf-8",
    )
    report = audit_csv(
        str(path),
        y_true="truth",
        y_pred="pred",
        group="gender",
        protected="F",
        reference="M",
    )
    assert report["metrics"]["dir"] == 0.5
    assert report["metrics"]["spd"] == -1 / 3
    assert report["metrics"]["eod"] == -0.5
    assert report["method_version"] == "fairness-v1"
