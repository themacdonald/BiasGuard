import pytest

from biasguard.metrics import (
    disparate_impact_ratio,
    equal_opportunity_difference,
    selection_rate,
    statistical_parity_difference,
    true_positive_rate,
)


def test_selection_rate():
    assert selection_rate([1, 0, 1, 0]) == 0.5


def test_dir_uses_exact_rates_without_integer_rounding():
    p = [1, 0, 0, 0, 1, 0, 0]  # 2/7
    r = [1, 1, 0, 0, 1, 0, 0, 0, 1]  # 4/9
    assert disparate_impact_ratio(p, r) == pytest.approx((2 / 7) / (4 / 9))


def test_dir_undefined_when_reference_rate_is_zero():
    assert disparate_impact_ratio([1, 0], [0, 0]) is None


def test_empty_selection_rate_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        selection_rate([])


def test_invalid_binary_values_are_rejected():
    with pytest.raises(ValueError, match="0/1"):
        selection_rate([1, 2])


def test_spd():
    assert statistical_parity_difference([1, 0, 0, 0], [1, 1, 0, 0]) == -0.25


def test_tpr():
    assert true_positive_rate([1, 1, 0, 0], [1, 0, 1, 0]) == 0.5


def test_tpr_undefined_without_positive_examples():
    assert true_positive_rate([0, 0], [0, 1]) is None


def test_eod():
    assert equal_opportunity_difference(
        [1, 1, 0, 0], [1, 0, 0, 0],
        [1, 1, 0, 0], [1, 1, 0, 0],
    ) == -0.5


def test_eod_undefined_when_group_has_no_positives():
    assert equal_opportunity_difference(
        [0, 0], [0, 0], [1, 0], [1, 0]
    ) is None
