"""Semiring, star-semiring, Kleene algebra, Conway matrix star, and action algebra verifiers."""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Sequence
from typing import Any, TypeVar

from algebrax.algebra._action import ActionAlgebra
from algebrax.semiring import KleeneAlgebra, Semiring, StarSemiring
from algebrax.verification._common import semiring_elements_equal

V = TypeVar('V')

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


def verify_star_semiring_laws(
    semiring: StarSemiring[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test all semiring axioms plus Conway star closure axioms.

    Validates:
      - All 9 semiring axioms
      - 'left_conway':  $a^* \approx \mathbf{1} + a \cdot a^*$
      - 'right_conway': $a^* \approx \mathbf{1} + a^* \cdot a$
    """
    results = verify_semiring_laws(semiring, samples, tol)
    elements = list(samples)
    one = semiring.one

    left_conway = True
    right_conway = True
    for a in elements:
        try:
            a_star = semiring.star(a)
            # Skip infinite/overflow values in numerical semirings
            if isinstance(a_star, float) and (math.isinf(a_star) or math.isnan(a_star)):
                continue
            lhs_left = semiring.add(one, semiring.mul(a, a_star))
            if not semiring_elements_equal(a_star, lhs_left, tol):
                left_conway = False
                break
            rhs_right = semiring.add(one, semiring.mul(a_star, a))
            if not semiring_elements_equal(a_star, rhs_right, tol):
                right_conway = False
                break
        except (ValueError, ZeroDivisionError, OverflowError, NotImplementedError):
            continue

    results['left_conway'] = left_conway
    results['right_conway'] = right_conway
    return results


def verify_kleene_algebra_laws(
    semiring: KleeneAlgebra[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test all star semiring axioms plus addition idempotency ($a \oplus a \approx a$)."""
    results = verify_star_semiring_laws(semiring, samples, tol)
    elements = list(samples)
    idempotent = True
    for a in elements:
        if not semiring_elements_equal(semiring.add(a, a), a, tol):
            idempotent = False
            break
    results['add_idempotence'] = idempotent
    return results


def verify_star_plus_consistency(
    semiring: StarSemiring[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test consistency of Kleene star and strict plus operators:
    - Left Star-Plus:  $a^+ \approx a \cdot a^*$
    - Right Star-Plus: $a^+ \approx a^* \cdot a$
    """
    elements = list(samples)
    mul = semiring.mul
    star_fn = semiring.star
    plus_fn = getattr(semiring, 'plus', lambda a: mul(a, star_fn(a)))

    left_plus = True
    right_plus = True
    for a in elements:
        try:
            a_star = star_fn(a)
            if isinstance(a_star, float) and (math.isinf(a_star) or math.isnan(a_star)):
                continue
            a_plus = plus_fn(a)
            if isinstance(a_plus, float) and (math.isinf(a_plus) or math.isnan(a_plus)):
                continue

            expected_left = mul(a, a_star)
            expected_right = mul(a_star, a)
            if not semiring_elements_equal(a_plus, expected_left, tol):
                left_plus = False
            if not semiring_elements_equal(a_plus, expected_right, tol):
                right_plus = False
            if not left_plus or not right_plus:
                break
        except (ValueError, ZeroDivisionError, OverflowError, NotImplementedError):
            continue

    return {
        'left_star_plus': left_plus,
        'right_star_plus': right_plus,
    }


def verify_residuation_laws(
    algebra: Any,
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test left and right residuation adjoint laws:
    - Left Soundness:     $a \cdot (a \backslash b) \le b \iff a \cdot (a \backslash b) + b \approx b$
    - Left Completeness:  $b \le a \backslash (a \cdot b)$
                          $\iff b + a \backslash (a \cdot b) \approx a \backslash (a \cdot b)$
    - Right Soundness:    $(b / a) \cdot a \le b \iff (b / a) \cdot a + b \approx b$
    - Right Completeness: $b \le (b \cdot a) / a \iff b + (b \cdot a) / a \approx (b \cdot a) / a$
    where the order in an idempotent semiring is $x \le y \iff x + y \approx y$.
    """
    elements = list(samples)
    mul = algebra.mul
    add = algebra.add
    ldiv = algebra.ldiv
    rdiv = algebra.rdiv

    left_sound = True
    left_comp = True
    right_sound = True
    right_comp = True

    for a, b in itertools.product(elements, repeat=2):
        try:
            # 1. Left soundness: a · (a \ b) <= b
            a_ldiv_b = ldiv(a, b)
            prod_left = mul(a, a_ldiv_b)
            if not semiring_elements_equal(add(prod_left, b), b, tol):
                left_sound = False

            # 2. Left completeness: b <= a \ (a · b)
            a_mul_b = mul(a, b)
            ldiv_prod = ldiv(a, a_mul_b)
            if not semiring_elements_equal(add(b, ldiv_prod), ldiv_prod, tol):
                left_comp = False

            # 3. Right soundness: (b / a) · a <= b
            b_rdiv_a = rdiv(b, a)
            prod_right = mul(b_rdiv_a, a)
            if not semiring_elements_equal(add(prod_right, b), b, tol):
                right_sound = False

            # 4. Right completeness: b <= (b · a) / a
            b_mul_a = mul(b, a)
            rdiv_prod = rdiv(b_mul_a, a)
            if not semiring_elements_equal(add(b, rdiv_prod), rdiv_prod, tol):
                right_comp = False

            if not (left_sound and left_comp and right_sound and right_comp):
                break
        except (ValueError, ZeroDivisionError, OverflowError, NotImplementedError):
            continue

    return {
        'left_residuation_soundness': left_sound,
        'left_residuation_completeness': left_comp,
        'right_residuation_soundness': right_sound,
        'right_residuation_completeness': right_comp,
    }


def verify_action_algebra_laws(
    algebra: ActionAlgebra[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test all Action Algebra axioms:
    - Kleene Algebra axioms (semiring + star + addition idempotence)
    - Star-Plus consistency: $a^+ = a \cdot a^* = a^* \cdot a$
    - Left and right residuation laws
    - Action induction axiom: $a^* \le (a \backslash a)^* \iff a^* + (a \backslash a)^* \approx (a \backslash a)^*$
    """
    res = verify_kleene_algebra_laws(algebra, samples, tol)
    res.update(verify_star_plus_consistency(algebra, samples, tol))
    res.update(verify_residuation_laws(algebra, samples, tol))

    elements = list(samples)
    add = algebra.add
    star_fn = algebra.star
    ldiv = algebra.ldiv
    rdiv = algebra.rdiv

    action_ind = True
    for a in elements:
        try:
            # Pure Induction Axiom (Pratt 1990): (a \ a)* <= a \ a and (a / a)* <= a / a
            a_ldiv_a = ldiv(a, a)
            a_ldiv_a_star = star_fn(a_ldiv_a)
            if not semiring_elements_equal(add(a_ldiv_a_star, a_ldiv_a), a_ldiv_a, tol):
                action_ind = False
                break

            a_rdiv_a = rdiv(a, a)
            a_rdiv_a_star = star_fn(a_rdiv_a)
            if not semiring_elements_equal(add(a_rdiv_a_star, a_rdiv_a), a_rdiv_a, tol):
                action_ind = False
                break
        except (ValueError, ZeroDivisionError, OverflowError, NotImplementedError):
            continue

    res['action_induction'] = action_ind
    return res


def verify_matrix_conway_laws(
    matrix: Any,
    semiring: Any = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Conway block matrix closure axioms for a matrix A over a StarSemiring:
    - Left Conway identity:  $A^* \approx I + A \cdot A^*$
    - Right Conway identity: $A^* \approx I + A^* \cdot A$
    - Plus consistency:      $A^+ \approx A \cdot A^*$
    """
    from algebrax.matrix.closure import matrix_plus, matrix_star
    from algebrax.matrix.core import add, dot

    sr = Semiring.normalize(semiring)
    all_keys: set[Any] = set(matrix.keys())
    for row in matrix.values():
        all_keys.update(row.keys())

    # Build identity matrix I over all keys
    ident: dict[Any, dict[Any, Any]] = {k: {k: sr.one} for k in all_keys}

    a_star = matrix_star(matrix, sr)
    a_plus = matrix_plus(matrix, sr)

    # 1. Left Conway: I + A · A*
    a_dot_astar = dot(matrix, a_star, semiring=sr)
    left_expected = add(ident, a_dot_astar, semiring=sr)

    # 2. Right Conway: I + A* · A
    astar_dot_a = dot(a_star, matrix, semiring=sr)
    right_expected = add(ident, astar_dot_a, semiring=sr)

    # 3. Plus consistency: A+ == A · A*
    left_conway = semiring_elements_equal(a_star, left_expected, tol)
    right_conway = semiring_elements_equal(a_star, right_expected, tol)
    plus_cons = semiring_elements_equal(a_plus, a_dot_astar, tol)

    return {
        'matrix_left_conway': left_conway,
        'matrix_right_conway': right_conway,
        'matrix_plus_consistency': plus_cons,
    }


def get_semiring_samples(semiring_name: str) -> tuple[Semiring, list[Any]]:
    """
    Helper to instantiate a semiring by name and return a set of valid sample elements
    for property-based law testing.
    """
    from algebrax.semiring import (
        ArcticSemiring,
        BinomialConvolutionSemiring,
        BivariateVarianceSemiring,
        BooleanSemiring,
        BottleneckSemiring,
        CliffordAlgebra,
        DigitalSemiring,
        DualNumberAlgebra,
        ExpectationSemiring,
        GaloisField,
        GeneralizedCliffordAlgebra,
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
        PolynomialAlgebra,
        ProvenanceSemiring,
        QuantumCliffordAlgebra,
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
        'DualNumber': (DualNumberAlgebra(), [(0.0, 0.0), (1.0, 0.0), (2.0, 1.0), (3.5, 0.5)]),
        'String': (StringSemiring(), [set(), {''}, {'a'}, {'b'}, {'a', 'b'}]),
        'KCollapsed': (KCollapsedSemiring(k=5), [0, 1, 2, 5]),
        'Digital': (DigitalSemiring(), [0, float('inf'), 12, 34, 105]),
        'MonoidAlgebra': (MonoidAlgebraSemiring(StandardSemiring[int]()), [{}, {0: 1}, {0: 2, 1: 3}, {1: 4}]),
        'Knot': (KnotSemiring(), [{}, {'U': 1}, {'3_1': 2}, {'U': 1, '3_1': 1}]),
        'Polynomial': (PolynomialAlgebra(StandardSemiring[int]()), [{}, {0: 1}, {0: 2, 1: 3, 2: 1}]),
        'Provenance': (ProvenanceSemiring(), [{}, {(): 1}, {('x',): 2}, {('x', 'y'): 1}]),
        'QuotientMonoidAlgebra': (
            QuotientMonoidAlgebraSemiring(StandardSemiring[int]()),
            [{}, {0: 1}, {1: 2}],
        ),
        'Clifford': (CliffordAlgebra(3, 0, 0), [{}, {(): 1.0}, {(1,): 2.0}, {(1, 2): 3.0}]),
        'GaloisField': (GaloisField(2), [{}, {0: 1}, {0: 1, 1: 1}]),
        'GeneralizedClifford': (
            GeneralizedCliffordAlgebra(n_order=3, num_generators=2),
            [{}, {(0, 0): 1.0 + 0j}, {(1, 0): 1.0 + 0j}, {(0, 1): 2.0 + 0j}, {(1, 1): 1.0 + 0.5j}],
        ),
        'QuantumClifford': (
            QuantumCliffordAlgebra(q=0.5, num_generators=2, signatures=(0.0, 0.0)),
            [{}, {(0, 0): 1.0 + 0j}, {(1, 0): 1.0 + 0j}, {(0, 1): 2.0 + 0j}, {(1, 1): 1.0 + 0.5j}],
        ),
    }

    if semiring_name not in catalog_map:
        raise ValueError(f"Unknown semiring name '{semiring_name}'. Available: {list(catalog_map.keys())}")

    return catalog_map[semiring_name]
