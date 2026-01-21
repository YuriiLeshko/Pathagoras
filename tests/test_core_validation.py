import pytest

from pathagoras import core


@pytest.mark.parametrize(
    "data",
    [
        {"a": "1", "b": "2", "c": "3"},
        {"b": "2", "c": "3", "a": "1"},
        {"a": None, "b": "", "c": "3"},
    ],
)
def test_validate_required_keys_ok(data):
    core.validate_required_keys(data)


@pytest.mark.parametrize(
    "data",
    [
        {"a": "1", "b": "2"},  # missing c
        {"a": "1", "c": "3"},  # missing b
        {"b": "2", "c": "3"},  # missing a
        {"a": "1", "b": "2", "c": "3", "d": "4"},  # extra key
        {"a": "1", "b": "2", "d": "4"},  # missing + extra
        {},  # none
    ],
)

def test_validate_required_keys_raises(data):
    with pytest.raises(ValueError):
        core.validate_required_keys(data)


@pytest.mark.parametrize("value", [None, "", "   ", "\t\n"])
def test_validate_value_empty_returns_none(value):
    assert core.validate_value("a", value) is None


@pytest.mark.parametrize(
    "value, expected",
    [
        ("3", 3.0),
        ("3.5", 3.5),
        ("  3.5  ", 3.5),
        ("1e-3", 0.001),
        (5, 5.0),  # TypeError не має бути, float(5) ок
    ],
)
def test_validate_value_valid_numbers(value, expected):
    out = core.validate_value("a", value)
    assert out == expected


@pytest.mark.parametrize("value", ["0", 0, "-1", "-0.0001"])
def test_validate_value_non_positive_raises(value):
    with pytest.raises(ValueError):
        core.validate_value("a", value)


@pytest.mark.parametrize("value", ["nan", "NaN", "inf", "+inf", "-inf"])
def test_validate_value_non_finite_raises(value):
    with pytest.raises(ValueError):
        core.validate_value("a", value)


@pytest.mark.parametrize("value", ["abc", "3,5", object()])
def test_validate_value_not_a_number_raises(value):
    with pytest.raises(ValueError):
        core.validate_value("a", value)
