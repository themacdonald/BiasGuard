from biasguard.metrics import (
    disparate_impact_ratio,
    equal_opportunity_difference,
    selection_rate,
    statistical_parity_difference,
    true_positive_rate,
)


def test_selection_rate():
    assert selection_rate([1, 0, 1, 0]) == 0.5


def test_spd():
    p = [1, 0, 0, 0]  # 0.25
    r = [1, 1, 0, 0]  # 0.5
    assert statistical_parity_difference(p, r) == 0.25 - 0.5


def test_tpr():
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 1, 0]
    assert true_positive_rate(y_true, y_pred) == 0.5


def test_eod():
    y_true_p = [1, 1, 0, 0]
    y_pred_p = [1, 0, 0, 0]  # TPR 0.5
    y_true_r = [1, 1, 0, 0]
    y_pred_r = [1, 1, 0, 0]  # TPR 1.0
    assert equal_opportunity_difference(y_true_p, y_pred_p, y_true_r, y_pred_r) == -0.5


def test_dir_nonzero_ref():
    p = [1, 0, 0, 0]  # 0.25
    r = [1, 1, 0, 0]  # 0.5
    # expected 0.25 / 0.5 = 0.5
    assert abs(disparate_impact_ratio(p, r) - 0.5) < 1e-9
