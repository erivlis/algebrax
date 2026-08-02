"""
Algebraic Law Verification Engine (EP-0131).

This module provides tools for testing and verifying that semiring implementations
adhere to formal algebraic axioms (associativity, commutativity, distributivity,
identity, and annihilation).
"""

import math
from collections.abc import Iterable
from typing import Any, TypeVar

from algebrax.semiring import Semiring

V = TypeVar('V')


def semiring_elements_equal(a: Any, b: Any, tol: float = 1e-7) -> bool:
    """
    Compare two semiring values for algebraic equality, supporting exact,
    floating-point tolerance, tuple, set, and sparse mapping comparisons.
    """
    if a == b:
        return True
    if isinstance(a, float) and isinstance(b, float):
        if math.isinf(a) and math.isinf(b):
            return (a > 0) == (b > 0)
        if math.isnan(a) and math.isnan(b):
            return True
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    if isinstance(a, tuple) and isinstance(b, tuple):
        if len(a) != len(b):
            return False
        return all(semiring_elements_equal(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for k in all_keys:
            v_a = a.get(k)
            v_b = b.get(k)
            if v_a is None or v_b is None:
                return False
            if not semiring_elements_equal(v_a, v_b, tol):
                return False
        return True
    return False


def verify_semiring_laws(
    semiring: Semiring[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    """
    Test all 9 semiring axioms with the given sample elements.

    Args:
        semiring: The semiring instance to audit.
        samples: An iterable of sample elements belonging to the semiring carrier set.
        tol: Numerical tolerance for floating point comparisons.

    Returns:
        A dictionary mapping each axiom name to a boolean pass/fail status:
          - 'add_associativity'
          - 'add_commutativity'
          - 'add_identity'
          - 'mul_associativity'
          - 'mul_identity'
          - 'left_distributivity'
          - 'right_distributivity'
          - 'left_annihilation'
          - 'right_annihilation'
    """
    elements = list(samples)
    zero = semiring.zero
    one = semiring.one

    results = {
        'add_associativity': True,
        'add_commutativity': True,
        'add_identity': True,
        'mul_associativity': True,
        'mul_identity': True,
        'left_distributivity': True,
        'right_distributivity': True,
        'left_annihilation': True,
        'right_annihilation': True,
    }

    # 1. Identity & Annihilation Checks
    for a in elements:
        # Add Identity: a + 0 = a, 0 + a = a
        if not semiring_elements_equal(semiring.add(a, zero), a, tol) or not semiring_elements_equal(
            semiring.add(zero, a), a, tol
        ):
            results['add_identity'] = False

        # Mul Identity: a * 1 = a, 1 * a = a
        if not semiring_elements_equal(semiring.mul(a, one), a, tol) or not semiring_elements_equal(
            semiring.mul(one, a), a, tol
        ):
            results['mul_identity'] = False

        # Annihilation: 0 * a = 0, a * 0 = 0
        if not semiring_elements_equal(semiring.mul(zero, a), zero, tol):
            results['left_annihilation'] = False
        if not semiring_elements_equal(semiring.mul(a, zero), zero, tol):
            results['right_annihilation'] = False

    # 2. Binary Checks (Commutativity)
    for a in elements:
        for b in elements:
            # Add Commutativity: a + b = b + a
            if not semiring_elements_equal(semiring.add(a, b), semiring.add(b, a), tol):
                results['add_commutativity'] = False

    # 3. Ternary Checks (Associativity & Distributivity)
    for a in elements:
        for b in elements:
            for c in elements:
                # Add Associativity: (a + b) + c = a + (b + c)
                if results['add_associativity']:
                    lhs = semiring.add(semiring.add(a, b), c)
                    rhs = semiring.add(a, semiring.add(b, c))
                    if not semiring_elements_equal(lhs, rhs, tol):
                        results['add_associativity'] = False

                # Mul Associativity: (a * b) * c = a * (b * c)
                if results['mul_associativity']:
                    lhs = semiring.mul(semiring.mul(a, b), c)
                    rhs = semiring.mul(a, semiring.mul(b, c))
                    if not semiring_elements_equal(lhs, rhs, tol):
                        results['mul_associativity'] = False

                # Left Distributivity: a * (b + c) = (a * b) + (a * c)
                if results['left_distributivity']:
                    lhs = semiring.mul(a, semiring.add(b, c))
                    rhs = semiring.add(semiring.mul(a, b), semiring.mul(a, c))
                    if not semiring_elements_equal(lhs, rhs, tol):
                        results['left_distributivity'] = False

                # Right Distributivity: (a + b) * c = (a * c) + (b * c)
                if results['right_distributivity']:
                    lhs = semiring.mul(semiring.add(a, b), c)
                    rhs = semiring.add(semiring.mul(a, c), semiring.mul(b, c))
                    if not semiring_elements_equal(lhs, rhs, tol):
                        results['right_distributivity'] = False

    return results


def get_semiring_samples(semiring_name: str) -> tuple[Semiring, list[Any]]:
    """
    Helper to instantiate a semiring by name and return a set of valid sample elements
    for property-based law testing.
    """
    from algebrax.semiring import (
        ArcticSemiring,
        BooleanSemiring,
        BottleneckSemiring,
        CliffordSemiring,
        DigitalSemiring,
        DualNumberSemiring,
        ExpectationSemiring,
        GaloisFieldSemiring,
        KCollapsedSemiring,
        KnotSemiring,
        LogSemiring,
        LukasiewiczSemiring,
        MinTimesSemiring,
        ModularSemiring,
        MonoidAlgebraSemiring,
        PolynomialSemiring,
        ProvenanceSemiring,
        QuotientMonoidAlgebraSemiring,
        ReliabilitySemiring,
        StandardSemiring,
        StringSemiring,
        TropicalSemiring,
        VarianceSemiring,
        ViterbiSemiring,
    )

    catalog_map = {
        'Standard': (StandardSemiring[float](), [0.0, 1.0, 2.5, -3.0, 0.5]),
        'Modular': (ModularSemiring(5), [0, 1, 2, 3, 4]),
        'Tropical': (TropicalSemiring(), [float('inf'), 0.0, 1.5, 4.0, 10.0]),
        'Arctic': (ArcticSemiring(), [float('-inf'), 0.0, 2.0, 5.5, 12.0]),
        'Viterbi': (ViterbiSemiring(), [0.0, 1.0, 0.5, 0.8, 0.2]),
        'Reliability': (ReliabilitySemiring(), [0.0, 1.0, 0.5, 0.8, 0.2]),
        'Bottleneck': (BottleneckSemiring(), [float('-inf'), float('inf'), 0.0, 3.5, 10.0]),
        'MinTimes': (MinTimesSemiring(), [float('inf'), 1.0, 0.5, 2.0, 3.0]),
        'Boolean': (BooleanSemiring(), [False, True]),
        'Lukasiewicz': (LukasiewiczSemiring(), [0.0, 1.0, 0.3, 0.7, 0.5]),
        'Log': (LogSemiring(), [float('-inf'), 0.0, -1.2, -0.5, -3.0]),
        'Expectation': (ExpectationSemiring(), [(0.0, 0.0), (1.0, 0.0), (0.5, 1.5), (0.8, 2.0)]),
        'Variance': (VarianceSemiring(), [(0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.5, 1.0, 1.0, 2.0)]),
        'DualNumber': (DualNumberSemiring(), [(0.0, 0.0), (1.0, 0.0), (2.0, 1.0), (3.5, 0.5)]),
        'String': (StringSemiring(), [set(), {''}, {'a'}, {'b'}, {'a', 'b'}]),
        'KCollapsed': (KCollapsedSemiring(k=5), [0, 1, 2, 5]),
        'Digital': (DigitalSemiring(), [0, float('inf'), 12, 34, 105]),
        'MonoidAlgebra': (MonoidAlgebraSemiring(StandardSemiring[int]()), [{}, {0: 1}, {0: 2, 1: 3}, {1: 4}]),
        'Knot': (KnotSemiring(), [{}, {'U': 1}, {'3_1': 2}, {'U': 1, '3_1': 1}]),
        'Polynomial': (PolynomialSemiring(StandardSemiring[int]()), [{}, {0: 1}, {0: 2, 1: 3, 2: 1}]),
        'Provenance': (ProvenanceSemiring(), [{}, {(): 1}, {('x',): 2}, {('x', 'y'): 1}]),
        'QuotientMonoidAlgebra': (
            QuotientMonoidAlgebraSemiring(StandardSemiring[int]()),
            [{}, {0: 1}, {1: 2}],
        ),
        'Clifford': (CliffordSemiring(3, 0, 0), [{}, {(): 1.0}, {(1,): 2.0}, {(1, 2): 3.0}]),
        'GaloisField': (GaloisFieldSemiring(2), [{}, {0: 1}, {0: 1, 1: 1}]),
    }

    if semiring_name not in catalog_map:
        raise ValueError(f"Unknown semiring name '{semiring_name}'. Available: {list(catalog_map.keys())}")

    return catalog_map[semiring_name]
