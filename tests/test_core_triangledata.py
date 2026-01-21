import math
import pytest

from pathagoras import core


def test_compute_hypotenuse_ok_sets_flags():
    t = core.TriangleData(a=3.0, b=4.0)
    t.compute_hypotenuse()

    assert t.c == pytest.approx(5.0)
    assert t.is_valid is True
    assert t.is_right is True


@pytest.mark.parametrize(
    "a,b",
    [
        (None, 4.0),
        (3.0, None),
        (None, None),
    ],
)
def test_compute_hypotenuse_missing_raises(a, b):
    t = core.TriangleData(a=a, b=b)
    with pytest.raises(ValueError):
        t.compute_hypotenuse()


@pytest.mark.parametrize(
    "c,a,b,expected_a,expected_b",
    [
        (5.0, 3.0, None, 3.0, 4.0),
        (5.0, None, 4.0, 3.0, 4.0),
        (13.0, 5.0, None, 5.0, 12.0),
        (13.0, None, 12.0, 5.0, 12.0),
    ],
)
def test_compute_leg_ok(c, a, b, expected_a, expected_b):
    t = core.TriangleData(a=a, b=b, c=c)
    t.compute_leg()

    assert t.a == pytest.approx(expected_a)
    assert t.b == pytest.approx(expected_b)
    assert t.is_valid is True
    assert t.is_right is True


def test_compute_leg_missing_c_raises():
    t = core.TriangleData(a=3.0, b=None, c=None)
    with pytest.raises(ValueError):
        t.compute_leg()


@pytest.mark.parametrize(
    "a,b,c",
    [
        (None, None, 5.0),   # both legs missing
        (3.0, 4.0, 5.0),     # both legs provided
    ],
)
def test_compute_leg_wrong_leg_count_raises(a, b, c):
    t = core.TriangleData(a=a, b=b, c=c)
    with pytest.raises(ValueError):
        t.compute_leg()


def test_compute_leg_known_greater_than_hypotenuse_raises():
    t = core.TriangleData(a=6.0, b=None, c=5.0)
    with pytest.raises(ValueError):
        t.compute_leg()


def test_normalise_sorts_sides():
    t = core.TriangleData(a=4.0, b=5.0, c=3.0)
    t.normalise()
    assert (t.a, t.b, t.c) == (3.0, 4.0, 5.0)


def test_normalise_missing_raises():
    t = core.TriangleData(a=3.0, b=None, c=5.0)
    with pytest.raises(ValueError):
        t.normalise()


@pytest.mark.parametrize(
    "a,b,c,should_raise",
    [
        (3.0, 4.0, 5.0, False),
        (1.0, 2.0, 3.0, True),   # a+b == c
        (1.0, 1.0, 2.0, True),   # a+b == c
        (1.0, 1.0, 3.0, True),   # a+b < c
    ],
)
def test_is_triangle_possible(a, b, c, should_raise):
    t = core.TriangleData(a=a, b=b, c=c)
    t.normalise()  # intended usage
    if should_raise:
        with pytest.raises(ValueError):
            t.is_triangle_possible()
    else:
        t.is_triangle_possible()
        assert t.is_valid is True


def test_is_right_triangle_exact_right():
    t = core.TriangleData(a=3.0, b=4.0, c=5.0)
    t.is_right_triangle()
    assert t.is_right is True


def test_is_right_triangle_not_right():
    t = core.TriangleData(a=2.0, b=3.0, c=4.0)
    t.is_right_triangle()
    assert t.is_right is False


def test_is_right_triangle_requires_all_sides():
    t = core.TriangleData(a=3.0, b=4.0, c=None)
    with pytest.raises(ValueError):
        t.is_right_triangle()


def test_is_right_triangle_tolerance_large_scale():
    # близько до sqrt(2)*1e9, перевіряємо що толеранс не “ламає” істинний right
    a = 1e9
    b = 1e9
    c = math.sqrt(2) * 1e9
    t = core.TriangleData(a=a, b=b, c=c)
    t.is_right_triangle()
    assert t.is_right is True
