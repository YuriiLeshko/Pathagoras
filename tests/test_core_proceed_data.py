import pytest

from pathagoras import core


def test_proceed_data_rejects_wrong_keys_but_does_not_raise():
    result = core.proceed_data({"a": "3", "b": "4"})  # missing c key
    assert result.is_valid is False
    assert result.is_right is False
    assert "Data must contain exactly keys" in result.message


@pytest.mark.parametrize(
    "data",
    [
        {"a": "", "b": "", "c": ""},                 # 0 values
        {"a": "3", "b": "", "c": ""},                # 1 value
        {"a": "", "b": "4", "c": ""},                # 1 value
        {"a": "", "b": "", "c": "5"},                # 1 value
        {"a": "3", "b": "4", "c": "5", "d": "1"},    # extra key
    ],
)

def test_proceed_data_invalid_input_returns_message_no_raise(data):
    result = core.proceed_data(dict(data))

    assert isinstance(result, core.TriangleData)
    assert result.is_valid is False
    assert result.is_right is False
    assert isinstance(result.message, str) and result.message


def test_proceed_data_more_than_one_missing_rejected():
    result = core.proceed_data({"a": "", "b": "", "c": "5"})
    assert result.is_valid is False
    assert "Enter exactly two values" in result.message


def test_proceed_data_calculate_hypotenuse_missing_c():
    result = core.proceed_data({"a": "3", "b": "4", "c": ""})
    assert result.is_valid is True
    assert result.is_right is True
    assert result.c == pytest.approx(5.0)
    assert result.message == "Hypotenuse calculated"


def test_proceed_data_calculate_leg_missing_a():
    result = core.proceed_data({"a": "", "b": "4", "c": "5"})
    assert result.is_valid is True
    assert result.is_right is True
    assert result.a == pytest.approx(3.0)
    assert result.message == "Leg calculated"


def test_proceed_data_calculate_leg_missing_b():
    result = core.proceed_data({"a": "3", "b": "", "c": "5"})
    assert result.is_valid is True
    assert result.is_right is True
    assert result.b == pytest.approx(4.0)
    assert result.message == "Leg calculated"


def test_proceed_data_calculate_leg_known_greater_than_c_is_error():
    result = core.proceed_data({"a": "6", "b": "", "c": "5"})
    assert result.is_valid is False
    assert result.is_right is False
    assert "Hypotenuse c must be greater" in result.message


def test_proceed_data_verify_right_triangle_with_mixed_order():
    # input is not in a/b legs, c hypotenuse order
    result = core.proceed_data({"a": "4", "b": "5", "c": "3"})
    assert result.is_valid is True
    assert result.is_right is True
    # normalise should make (3,4,5)
    assert (result.a, result.b, result.c) == (3.0, 4.0, 5.0)
    assert "Triangle is RIGHT" in result.message


def test_proceed_data_verify_not_right_triangle():
    result = core.proceed_data({"a": "2", "b": "3", "c": "4"})
    assert result.is_valid is True
    assert result.is_right is False
    assert "Triangle is NOT right" in result.message


def test_proceed_data_verify_impossible_triangle():
    result = core.proceed_data({"a": "1", "b": "2", "c": "3"})
    assert result.is_valid is False
    assert result.is_right is False
    assert "Triangle is impossible" in result.message


@pytest.mark.parametrize(
    "data, expected_substring",
    [
        ({"a": "0", "b": "4", "c": ""}, "greater than zero"),
        ({"a": "-1", "b": "4", "c": ""}, "greater than zero"),
        ({"a": "nan", "b": "4", "c": ""}, "finite"),
        ({"a": "inf", "b": "4", "c": ""}, "finite"),
        ({"a": "abc", "b": "4", "c": ""}, "must be a number"),
        ({"a": "3,5", "b": "4", "c": ""}, "must be a number"),  # comma is invalid in core
    ],
)
def test_proceed_data_invalid_values_return_error(data, expected_substring):
    result = core.proceed_data(data)
    assert result.is_valid is False
    assert result.is_right is False
    assert expected_substring in result.message
