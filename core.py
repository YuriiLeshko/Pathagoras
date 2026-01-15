from dataclasses import dataclass
import math
from typing import Optional


@dataclass
class TriangleData:
    """
    Container for triangle inputs and computed/verified results.

    Semantics
    ---------
    - a, b: legs (catheti)
    - c: hypotenuse

    Flags
    -----
    is_valid:
        True if the triangle is geometrically possible (triangle inequality holds)
        in the context where the check is performed.
    is_right:
        True if the triangle satisfies the Pythagorean theorem within tolerance.

    message:
        UI-friendly message set by the orchestration layer (proceed_data).
    """
    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None
    is_right: bool = False
    is_valid: bool = False
    message: str = ""

    def compute_hypotenuse(self):
        """
        Compute hypotenuse c from legs a and b using the Pythagorean theorem.

        Preconditions
        -------------
        - Both legs (a and b) must be provided (not None).

        Effects
        -------
        - Sets c to sqrt(a^2 + b^2).
        - Sets is_valid = True and is_right = True (right-angled by definition).

        Raises
        ------
        ValueError
            If a or b is missing.
        """
        if self.a is None or self.b is None:
            raise ValueError("Both legs a and b are required to compute hypotenuse c.")

        self.c = math.sqrt(self.a * self.a + self.b * self.b)

        self.is_valid = True
        self.is_right = True

    def compute_leg(self):
        """
        Compute the missing leg from hypotenuse c and the other (known) leg.

        Preconditions
        -------------
        - Hypotenuse c must be provided (not None).
        - Exactly one leg must be provided:
          * a is provided and b is missing, OR
          * b is provided and a is missing.
        - The known leg must not exceed the hypotenuse (known <= c).

        Effects
        -------
        - Sets the missing leg (a or b).
        - Sets is_valid = True and is_right = True (right-angled by definition).

        Raises
        ------
        ValueError
            If c is missing.
            If both legs are missing or both legs are provided.
            If the known leg is greater than the hypotenuse.
        """
        if self.c is None:
            raise ValueError("Hypotenuse c is required to compute a leg.")
        if (self.a is None) == (self.b is None):  # both None or both provided
            raise ValueError("Exactly one leg (a or b) must be provided to compute the other.")
        known = self.a if self.a is not None else self.b
        if known > self.c:
            raise ValueError("Hypotenuse c must be greater than the known leg.")

        if self.a is not None:
            self.b = math.sqrt(self.c * self.c - self.a * self.a)
        else:
            self.a = math.sqrt(self.c * self.c - self.b * self.b)

        self.is_valid = True
        self.is_right = True

    def is_right_triangle(self):
        """
        Verify whether the triangle is right-angled (Pythagorean theorem).

        Notes
        -----
        Expects current semantics: a and b are legs, c is hypotenuse.
        In verification mode, call normalise() first so that the largest side
        is treated as hypotenuse candidate.

        Effects
        -------
        - Updates is_right (True/False).

        Raises
        ------
        ValueError
            If any side is missing.
        """
        if self.a is None or self.b is None or self.c is None:
            raise ValueError("All three sides are required to verify a triangle.")

        a, b, c = self.a, self.b, self.c

        lhs = a * a + b * b
        rhs = c * c

        self.is_right = abs(lhs - rhs) <= max(
            1e-12,
            1e-9 * max(lhs, rhs)
        )

    def is_triangle_possible(self):
        """
        Check whether the triangle is geometrically possible (triangle inequality).

        Preconditions
        -------------
        Intended to be called after normalise(), so that c is the largest side.

        Effects
        -------
        - Sets is_valid = True if valid.

        Raises
        ------
        ValueError
            If a + b <= c (triangle inequality violated).
        """
        if self.a + self.b <= self.c:
            raise ValueError("Input sorted: largest treated as hypotenuse. Triangle is impossible: a + b <= c .")
        else:
            self.is_valid = True

    def normalise(self):
        """
        Normalise side ordering for verification.

        Behaviour
        ---------
        Sorts the three sides in ascending order and assigns:
        - a = smallest
        - b = middle
        - c = largest

        Rationale
        ---------
        In verification mode, user input may not follow the a/b/c semantics.
        After normalisation, the largest side is treated as the hypotenuse candidate.

        Effects
        -------
        - Updates a, b, c in-place.

        Raises
        ------
        ValueError
            If any side is missing.
        """
        if self.a is None or self.b is None or self.c is None:
            raise ValueError("All three sides are required to validate a triangle.")

        self.a, self.b, self.c = sorted([self.a, self.b, self.c])


def validate_required_keys(data: dict[str, str | None]):
    """
    Validate that the input dictionary contains exactly the required keys.

    Parameters
    ----------
    data:
        Input mapping expected to contain exactly {'a', 'b', 'c'}.

    Raises
    ------
    ValueError
        If keys are missing or extra keys are present.
    """
    required_keys = {"a", "b", "c"}
    if set(data.keys()) != required_keys:
        raise ValueError("Data must contain exactly keys: a, b, c")


def validate_value(key: str, value: str | None) -> float | None:
    """
    Parse and validate a single UI-provided field value.

    Rules
    -----
    - None or empty/whitespace string -> returns None (meaning "missing")
    - Otherwise:
      * must be convertible to float
      * must be finite (not NaN, not +/-inf)
      * must be > 0

    Parameters
    ----------
    key:
        Field name used to enrich error messages (e.g. 'a', 'b', 'c').
    value:
        Raw UI text or None.

    Returns
    -------
    float | None
        Parsed float if provided, otherwise None.

    Raises
    ------
    ValueError
        If the value is present but invalid.
    """
    if value is None or isinstance(value, str) and value.strip() == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Field {key}: value must be a number.")

    if not math.isfinite(number):
        raise ValueError(f"Field {key}: value must be finite (not NaN or infinity).")

    if number <= 0:
        raise ValueError(f"Field {key}: value must be greater than zero.")

    return number


def proceed_data(data: dict[str, str | None]):
    """
    Main orchestration function for UI integration.

    Input contract
    --------------
    data must contain keys {'a', 'b', 'c'} with values:
    - None or empty string -> treated as missing
    - otherwise -> parsed to positive finite float

    Modes
    -----
    Solve mode:
        Exactly one of a/b/c is missing.
        - missing 'c' -> compute hypotenuse from two legs
        - missing 'a' or 'b' -> compute missing leg from c and the other leg
    Verify mode:
        No values are missing.
        - normalises side order (largest treated as hypotenuse candidate)
        - checks triangle inequality
        - checks right-angled property

    Error handling policy
    ---------------------
    This function never propagates ValueError to the UI.
    All errors are captured and returned as TriangleData.message, with flags reset.

    Returns
    -------
    TriangleData
        Filled triangle object with computed/verified values and UI message.
    """
    triangle = TriangleData()

    try:
        validate_required_keys(data)
        for key, value in data.items():
            data[key] = validate_value(key, value)
            setattr(triangle, key, data[key])

        missing_keys = [k for k, v in data.items() if v is None]
        if len(missing_keys) > 1:
            raise ValueError("Enter exactly two values to compute the missing one, or all three values to verify.")
        elif len(missing_keys) == 1:
            if "c" in missing_keys:
                triangle.compute_hypotenuse()
                triangle.message = "Hypotenuse calculated"
            else:
                triangle.compute_leg()
                triangle.message = "Leg calculated"
        else:
            triangle.normalise()
            triangle.is_triangle_possible()
            triangle.is_right_triangle()
            if not triangle.is_right:
                triangle.message = "Input sorted: largest treated as hypotenuse. Triangle is NOT right"
            else:
                triangle.message = "Input sorted: largest treated as hypotenuse. Triangle is RIGHT"

        return triangle

    except ValueError as e:
        triangle.message = str(e)
        triangle.is_valid = False
        triangle.is_right = False
        return triangle
