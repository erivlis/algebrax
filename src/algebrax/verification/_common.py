"""Shared equality helpers and sample guards for the verification engine."""

from __future__ import annotations

import cmath
import math
from collections.abc import Iterable
from typing import Any


def _float_equal(a: float, b: float, tol: float) -> bool:
    if math.isinf(a) and math.isinf(b):
        return (a > 0) == (b > 0)
    if math.isnan(a) and math.isnan(b):
        return True
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def _dict_equal(a: dict[Any, Any], b: dict[Any, Any], tol: float) -> bool:
    if set(a.keys()) != set(b.keys()):
        return False
    return all(semiring_elements_equal(a[k], b[k], tol) for k in a)


def semiring_elements_equal(a: Any, b: Any, tol: float = 1e-7) -> bool:
    """
    Compare two semiring values for algebraic equality, supporting exact,
    floating-point tolerance, complex tolerance, tuple, set, and sparse mapping comparisons.
    """
    if a == b:
        return True
    if (
        isinstance(a, (int, float, complex))
        and isinstance(b, (int, float, complex))
        and not isinstance(a, bool)
        and not isinstance(b, bool)
    ):
        if isinstance(a, complex) or isinstance(b, complex):
            return cmath.isclose(complex(a), complex(b), rel_tol=tol, abs_tol=tol)
        return _float_equal(float(a), float(b), tol)
    if isinstance(a, tuple) and isinstance(b, tuple):
        if len(a) != len(b):
            return False
        return all(semiring_elements_equal(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return _dict_equal(a, b, tol)
    return False


def _require_samples(samples: Iterable[Any], min_count: int = 3) -> list[Any]:
    el = list(samples)
    if len(el) < min_count:
        raise ValueError(
            f'Axiom verification requires at least {min_count} sample elements to test non-trivial laws, got {len(el)}.'
        )
    return el
