"""
Algebraic Law Verification Engine.

This module provides tools for testing and verifying that semiring implementations
adhere to formal algebraic axioms (associativity, commutativity, distributivity,
identity, and annihilation).
"""

import cmath
import itertools
import math
from collections.abc import Iterable
from typing import Any, TypeVar

from algebrax.semiring import Semiring

V = TypeVar('V')


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
    if isinstance(a, float) and isinstance(b, float):
        return _float_equal(a, b, tol)
    if isinstance(a, complex) and isinstance(b, complex):
        return cmath.isclose(a, b, rel_tol=tol, abs_tol=tol)
    if isinstance(a, tuple) and isinstance(b, tuple):
        if len(a) != len(b):
            return False
        return all(semiring_elements_equal(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return _dict_equal(a, b, tol)
    return False


def _check_identities_and_annihilation(
    semiring: Semiring[V],
    elements: list[V],
    tol: float,
) -> dict[str, bool]:
    """Verify additive/multiplicative identities and left/right annihilation."""
    zero = semiring.zero
    one = semiring.one
    res = {
        'add_identity': True,
        'mul_identity': True,
        'left_annihilation': True,
        'right_annihilation': True,
    }
    for a in elements:
        if res['add_identity']:
            left_ok = semiring_elements_equal(semiring.add(zero, a), a, tol)
            right_ok = semiring_elements_equal(semiring.add(a, zero), a, tol)
            if not (left_ok and right_ok):
                res['add_identity'] = False

        if res['mul_identity']:
            left_ok = semiring_elements_equal(semiring.mul(one, a), a, tol)
            right_ok = semiring_elements_equal(semiring.mul(a, one), a, tol)
            if not (left_ok and right_ok):
                res['mul_identity'] = False

        if res['left_annihilation'] and not semiring_elements_equal(semiring.mul(zero, a), zero, tol):
            res['left_annihilation'] = False

        if res['right_annihilation'] and not semiring_elements_equal(semiring.mul(a, zero), zero, tol):
            res['right_annihilation'] = False

    return res


def _check_add_commutativity(
    semiring: Semiring[V],
    elements: list[V],
    tol: float,
) -> bool:
    """Verify additive commutativity a + b = b + a over all element pairs."""
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(semiring.add(a, b), semiring.add(b, a), tol):
            return False
    return True


def _check_associativity(
    semiring: Semiring[V],
    elements: list[V],
    tol: float,
) -> tuple[bool, bool]:
    """Verify additive and multiplicative associativity over all triplets."""
    add_assoc = True
    mul_assoc = True

    for a, b, c in itertools.product(elements, repeat=3):
        if add_assoc:
            lhs = semiring.add(semiring.add(a, b), c)
            rhs = semiring.add(a, semiring.add(b, c))
            if not semiring_elements_equal(lhs, rhs, tol):
                add_assoc = False

        if mul_assoc:
            lhs = semiring.mul(semiring.mul(a, b), c)
            rhs = semiring.mul(a, semiring.mul(b, c))
            if not semiring_elements_equal(lhs, rhs, tol):
                mul_assoc = False

        if not add_assoc and not mul_assoc:
            break

    return add_assoc, mul_assoc


def _check_distributivity(
    semiring: Semiring[V],
    elements: list[V],
    tol: float,
) -> tuple[bool, bool]:
    """Verify left and right distributivity over all triplets."""
    left_dist = True
    right_dist = True

    for a, b, c in itertools.product(elements, repeat=3):
        if left_dist:
            lhs = semiring.mul(a, semiring.add(b, c))
            rhs = semiring.add(semiring.mul(a, b), semiring.mul(a, c))
            if not semiring_elements_equal(lhs, rhs, tol):
                left_dist = False

        if right_dist:
            lhs = semiring.mul(semiring.add(a, b), c)
            rhs = semiring.add(semiring.mul(a, c), semiring.mul(b, c))
            if not semiring_elements_equal(lhs, rhs, tol):
                right_dist = False

        if not left_dist and not right_dist:
            break

    return left_dist, right_dist


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
    results = _check_identities_and_annihilation(semiring, elements, tol)
    results['add_commutativity'] = _check_add_commutativity(semiring, elements, tol)
    results['add_associativity'], results['mul_associativity'] = _check_associativity(semiring, elements, tol)
    results['left_distributivity'], results['right_distributivity'] = _check_distributivity(semiring, elements, tol)
    return results


def get_semiring_samples(semiring_name: str) -> tuple[Semiring, list[Any]]:
    """
    Helper to instantiate a semiring by name and return a set of valid sample elements
    for property-based law testing.
    """
    from algebrax.semiring import (
        ArcticSemiring,
        BinomialConvolutionSemiring,
        BivariateCovarianceSemiring,
        BivariateVarianceSemiring,
        BooleanSemiring,
        BottleneckSemiring,
        CliffordSemiring,
        DigitalSemiring,
        DualNumberSemiring,
        ExpectationSemiring,
        GaloisFieldSemiring,
        GeneralizedCliffordSemiring,
        KCollapsedSemiring,
        KnotSemiring,
        KurtosisSemiring,
        LogSemiring,
        LukasiewiczSemiring,
        MinTimesSemiring,
        ModularSemiring,
        MonoidAlgebraSemiring,
        MultivariateBinomialConvolutionSemiring,
        MultivariateMomentSemiring,
        PolynomialSemiring,
        ProvenanceSemiring,
        QuantumCliffordSemiring,
        QuotientMonoidAlgebraSemiring,
        ReliabilitySemiring,
        SkewnessSemiring,
        StandardSemiring,
        StatisticalMomentSemiring,
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
        'Variance': (
            VarianceSemiring(),
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 1.0, 2.0), (0.8, 0.5, 1.5)],
        ),
        'BivariateVariance': (
            BivariateVarianceSemiring(),
            [(0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.5, 1.0, 1.0, 2.0)],
        ),
        'BivariateCovariance': (
            BivariateCovarianceSemiring(),
            [(0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.5, 1.0, 1.0, 2.0)],
        ),
        'Skewness': (
            SkewnessSemiring(),
            [(0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.5, 1.0, 2.0, 3.0), (0.8, 0.5, 1.5, 2.5)],
        ),
        'Kurtosis': (
            KurtosisSemiring(),
            [(0.0, 0.0, 0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0, 0.0), (0.5, 1.0, 2.0, 3.0, 4.0)],
        ),
        'StatisticalMoment': (
            StatisticalMomentSemiring(order=2),
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 1.0, 2.0), (0.8, 0.5, 1.5)],
        ),
        'BinomialConvolution': (
            BinomialConvolutionSemiring(order=2),
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 1.0, 2.0), (0.8, 0.5, 1.5)],
        ),
        'MultivariateBinomialConvolution': (
            MultivariateBinomialConvolutionSemiring(num_vars=2, order=2),
            [{}, {(0, 0): 1.0}, {(1, 0): 0.5, (0, 1): 1.0}, {(0, 0): 0.5, (1, 1): 0.2}],
        ),
        'MultivariateMoment': (
            MultivariateMomentSemiring(num_vars=2, order=2),
            [{}, {(0, 0): 1.0}, {(1, 0): 0.5, (0, 1): 1.0}, {(0, 0): 0.5, (1, 1): 0.2}],
        ),
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
        'GeneralizedClifford': (
            GeneralizedCliffordSemiring(n_order=3, num_generators=2),
            [{}, {(0, 0): 1.0 + 0j}, {(1, 0): 1.0 + 0j}, {(0, 1): 2.0 + 0j}, {(1, 1): 1.0 + 0.5j}],
        ),
        'QuantumClifford': (
            QuantumCliffordSemiring(q=0.5, num_generators=2, signatures=(0.0, 0.0)),
            [{}, {(0, 0): 1.0 + 0j}, {(1, 0): 1.0 + 0j}, {(0, 1): 2.0 + 0j}, {(1, 1): 1.0 + 0.5j}],
        ),
    }

    if semiring_name not in catalog_map:
        raise ValueError(f"Unknown semiring name '{semiring_name}'. Available: {list(catalog_map.keys())}")

    return catalog_map[semiring_name]
