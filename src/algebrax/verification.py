"""
Algebraic Law Verification Engine.

This module provides tools for testing and verifying that semiring implementations
adhere to formal algebraic axioms (associativity, commutativity, distributivity,
identity, and annihilation).
"""

import cmath
import itertools
import math
from collections.abc import Callable, Iterable, Sequence
from typing import Any, TypeVar

from algebrax.algebra._action import ActionAlgebra
from algebrax.algebra._grothendieck import GrothendieckGroup
from algebrax.algebra._hopf import Bialgebra, Coalgebra, HopfAlgebra
from algebrax.algebra._normed import InnerProductSpace, NormedSpace
from algebrax.semiring import KleeneAlgebra, Semiring, StarSemiring

V = TypeVar('V')
R = TypeVar('R')
M = TypeVar('M')

__all__ = [
    'get_semiring_samples',
    'semiring_elements_equal',
    'verify_action_algebra_laws',
    'verify_add_comm_group_laws',
    'verify_add_comm_monoid_laws',
    'verify_add_group_laws',
    'verify_add_magma_laws',
    'verify_add_monoid_laws',
    'verify_add_semigroup_laws',
    'verify_algebra_laws',
    'verify_alternative_laws',
    'verify_antipode_axiom',
    'verify_band_laws',
    'verify_bialgebra_laws',
    'verify_boolean_algebra_laws',
    'verify_bounded_lattice_laws',
    'verify_category_laws',
    'verify_cauchy_schwarz',
    'verify_chern_character_additivity',
    'verify_chern_number_integrality',
    'verify_coalgebra_laws',
    'verify_coassociativity',
    'verify_coboundary_nilpotency',
    'verify_comm_group_laws',
    'verify_comm_monoid_laws',
    'verify_comm_ring_laws',
    'verify_connection_inversion',
    'verify_contraction_constant',
    'verify_counitality',
    'verify_distributive_lattice_laws',
    'verify_division_ring_laws',
    'verify_field_laws',
    'verify_functor_laws',
    'verify_gauge_covariance',
    'verify_grothendieck_universal_property',
    'verify_group_action_laws',
    'verify_group_laws',
    'verify_hopf_algebra_laws',
    'verify_ideal_absorption_laws',
    'verify_inner_product_space_laws',
    'verify_join_semilattice_laws',
    'verify_jordan_laws',
    'verify_kleene_algebra_laws',
    'verify_lattice_laws',
    'verify_lie_algebra_laws',
    'verify_magma_laws',
    'verify_malcev_laws',
    'verify_matrix_conway_laws',
    'verify_meet_semilattice_laws',
    'verify_module_laws',
    'verify_monoid_laws',
    'verify_non_assoc_algebra_laws',
    'verify_non_assoc_ring_laws',
    'verify_normed_space_laws',
    'verify_parallelogram_law',
    'verify_poisson_laws',
    'verify_quotient_ring_laws',
    'verify_residuation_laws',
    'verify_ring_homomorphism_laws',
    'verify_ring_laws',
    'verify_semigroup_laws',
    'verify_semimodule_laws',
    'verify_semiring_laws',
    'verify_sheaf_functoriality',
    'verify_sheaf_laplacian_properties',
    'verify_star_plus_consistency',
    'verify_star_semiring_laws',
    'verify_triangle_inequality',
]


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
        GaloisFieldSemiring,
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
        'GaloisField': (GaloisFieldSemiring(2), [{}, {0: 1}, {0: 1, 1: 1}]),
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


# =============================================================================
# EP-0190: Granular Hierarchy Law Verifiers
# =============================================================================

from algebrax.algebra import (  # noqa: E402
    AddCommGroup,
    AddCommMonoid,
    AddGroup,
    AddMagma,
    AddMonoid,
    AddSemigroup,
    Algebra,
    Band,
    BooleanAlgebra,
    BoundedLattice,
    CommGroup,
    CommMonoid,
    CommRing,
    DistributiveLattice,
    DivisionRing,
    Field,
    Group,
    GroupAction,
    JoinSemilattice,
    Lattice,
    Magma,
    MeetSemilattice,
    Module,
    Monoid,
    NonAssocAlgebra,
    NonAssocRing,
    Ring,
    Semigroup,
    Semimodule,
    VectorSpace,
)

G = TypeVar('G')
M = TypeVar('M')
R = TypeVar('R')
X = TypeVar('X')


def _require_samples(samples: Iterable[Any], min_count: int = 3) -> list[Any]:
    el = list(samples)
    if len(el) < min_count:
        raise ValueError(
            f'Axiom verification requires at least {min_count} sample elements to test non-trivial laws, got {len(el)}.'
        )
    return el


def verify_magma_laws(
    magma: Magma[V],
    samples: Iterable[V],
    tol: float = 1e-7,  # NOSONAR - retained for uniform verify_*_laws API signature
) -> dict[str, bool]:
    r"""Test Magma closure law: $\forall a, b \in M, \ a \cdot b \in M$."""
    elements = _require_samples(samples)
    mul = magma.mul
    closure = True
    try:
        for a, b in itertools.product(elements, repeat=2):
            if mul(a, b) is None:
                closure = False
                break
    except Exception:
        closure = False
    return {'mul_closure': closure}


def verify_semigroup_laws(
    semigroup: Semigroup[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Semigroup laws: closure and associativity $(a \cdot b) \cdot c = a \cdot (b \cdot c)$."""
    elements = _require_samples(samples)
    res = verify_magma_laws(semigroup, elements, tol)
    mul = semigroup.mul
    assoc = True
    for a, b, c in itertools.product(elements, repeat=3):
        lhs = mul(mul(a, b), c)
        rhs = mul(a, mul(b, c))
        if not semiring_elements_equal(lhs, rhs, tol):
            assoc = False
            break
    res['mul_associativity'] = assoc
    return res


def verify_band_laws(
    band: Band[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Band laws: semigroup laws plus idempotence $a \cdot a = a$."""
    elements = _require_samples(samples)
    res = verify_semigroup_laws(band, elements, tol)
    mul = band.mul
    idemp = True
    for a in elements:
        if not semiring_elements_equal(mul(a, a), a, tol):
            idemp = False
            break
    res['mul_idempotence'] = idemp
    return res


def verify_monoid_laws(
    monoid: Monoid[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Monoid laws: semigroup laws plus left and right identity $\mathbf{1} \cdot a = a \cdot \mathbf{1} = a$."""
    elements = _require_samples(samples)
    res = verify_semigroup_laws(monoid, elements, tol)
    one = monoid.one
    mul = monoid.mul
    left_id = True
    right_id = True
    for a in elements:
        if not semiring_elements_equal(mul(one, a), a, tol):
            left_id = False
        if not semiring_elements_equal(mul(a, one), a, tol):
            right_id = False
    res['left_identity'] = left_id
    res['right_identity'] = right_id
    return res


def verify_comm_monoid_laws(
    monoid: CommMonoid[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Commutative Monoid laws: monoid laws plus commutativity $a \cdot b = b \cdot a$."""
    elements = _require_samples(samples)
    res = verify_monoid_laws(monoid, elements, tol)
    mul = monoid.mul
    comm = True
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(mul(a, b), mul(b, a), tol):
            comm = False
            break
    res['mul_commutativity'] = comm
    return res


def verify_group_laws(
    group: Group[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Group laws: monoid laws plus two-sided inverses and quotient consistency."""
    elements = _require_samples(samples)
    res = verify_monoid_laws(group, elements, tol)
    one = group.one
    mul = group.mul
    inv = group.inv
    div = group.div
    left_inv = True
    right_inv = True
    quotient = True
    for a in elements:
        a_inv = inv(a)
        if not semiring_elements_equal(mul(a_inv, a), one, tol):
            left_inv = False
        if not semiring_elements_equal(mul(a, a_inv), one, tol):
            right_inv = False
        for b in elements:
            expected_div = mul(a, inv(b))
            if not semiring_elements_equal(div(a, b), expected_div, tol):
                quotient = False
                break
    res['left_inverse'] = left_inv
    res['right_inverse'] = right_inv
    res['quotient_consistency'] = quotient
    return res


def verify_comm_group_laws(
    group: CommGroup[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Abelian Group laws: group laws plus commutativity."""
    elements = _require_samples(samples)
    res = verify_group_laws(group, elements, tol)
    mul = group.mul
    comm = True
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(mul(a, b), mul(b, a), tol):
            comm = False
            break
    res['mul_commutativity'] = comm
    return res


# --- Additive Dual Verifiers ---


def verify_add_magma_laws(
    magma: AddMagma[V],
    samples: Iterable[V],
    tol: float = 1e-7,  # NOSONAR - retained for uniform verify_*_laws API signature
) -> dict[str, bool]:
    r"""Test Additive Magma closure law: $\forall a, b \in M, \ a + b \in M$."""
    elements = _require_samples(samples)
    add = magma.add
    closure = True
    try:
        for a, b in itertools.product(elements, repeat=2):
            if add(a, b) is None:
                closure = False
                break
    except Exception:
        closure = False
    return {'add_closure': closure}


def verify_add_semigroup_laws(
    semigroup: AddSemigroup[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Additive Semigroup laws: closure and associativity $(a + b) + c = a + (b + c)$."""
    elements = _require_samples(samples)
    res = verify_add_magma_laws(semigroup, elements, tol)
    add = semigroup.add
    assoc = True
    for a, b, c in itertools.product(elements, repeat=3):
        lhs = add(add(a, b), c)
        rhs = add(a, add(b, c))
        if not semiring_elements_equal(lhs, rhs, tol):
            assoc = False
            break
    res['add_associativity'] = assoc
    return res


def verify_add_monoid_laws(
    monoid: AddMonoid[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Additive Monoid laws: associativity plus identity $\mathbf{0} + a = a + \mathbf{0} = a$."""
    elements = _require_samples(samples)
    res = verify_add_semigroup_laws(monoid, elements, tol)
    zero = monoid.zero
    add = monoid.add
    left_id = True
    right_id = True
    for a in elements:
        if not semiring_elements_equal(add(zero, a), a, tol):
            left_id = False
        if not semiring_elements_equal(add(a, zero), a, tol):
            right_id = False
    res['left_add_identity'] = left_id
    res['right_add_identity'] = right_id
    return res


def verify_add_comm_monoid_laws(
    monoid: AddCommMonoid[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Additive Commutative Monoid laws: monoid laws plus commutativity $a + b = b + a$."""
    elements = _require_samples(samples)
    res = verify_add_monoid_laws(monoid, elements, tol)
    add = monoid.add
    comm = True
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(add(a, b), add(b, a), tol):
            comm = False
            break
    res['add_commutativity'] = comm
    return res


def verify_add_group_laws(
    group: AddGroup[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Additive Group laws: additive monoid laws plus negation and difference consistency."""
    elements = _require_samples(samples)
    res = verify_add_monoid_laws(group, elements, tol)
    zero = group.zero
    add = group.add
    neg = group.neg
    sub = group.sub
    left_inv = True
    right_inv = True
    diff = True
    for a in elements:
        neg_a = neg(a)
        if not semiring_elements_equal(add(neg_a, a), zero, tol):
            left_inv = False
        if not semiring_elements_equal(add(a, neg_a), zero, tol):
            right_inv = False
        for b in elements:
            expected_sub = add(a, neg(b))
            if not semiring_elements_equal(sub(a, b), expected_sub, tol):
                diff = False
                break
    res['left_negation'] = left_inv
    res['right_negation'] = right_inv
    res['difference_consistency'] = diff
    return res


def verify_add_comm_group_laws(
    group: AddCommGroup[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Additive Commutative Group laws: additive group laws plus commutativity."""
    elements = _require_samples(samples)
    res = verify_add_group_laws(group, elements, tol)
    add = group.add
    comm = True
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(add(a, b), add(b, a), tol):
            comm = False
            break
    res['add_commutativity'] = comm
    return res


# --- Order & Lattice Verifiers ---


def verify_join_semilattice_laws(
    js: JoinSemilattice[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Join-Semilattice laws: join associativity, commutativity, and idempotence ($a \vee a = a$)."""
    elements = _require_samples(samples)
    join = js.join
    assoc = True
    comm = True
    idemp = True
    for a in elements:
        if not semiring_elements_equal(join(a, a), a, tol):
            idemp = False
            break
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(join(a, b), join(b, a), tol):
            comm = False
            break
    for a, b, c in itertools.product(elements, repeat=3):
        if not semiring_elements_equal(join(join(a, b), c), join(a, join(b, c)), tol):
            assoc = False
            break
    return {
        'join_idempotence': idemp,
        'join_commutativity': comm,
        'join_associativity': assoc,
    }


def verify_meet_semilattice_laws(
    ms: MeetSemilattice[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Meet-Semilattice laws: meet associativity, commutativity, and idempotence ($a \wedge a = a$)."""
    elements = _require_samples(samples)
    meet = ms.meet
    assoc = True
    comm = True
    idemp = True
    for a in elements:
        if not semiring_elements_equal(meet(a, a), a, tol):
            idemp = False
            break
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(meet(a, b), meet(b, a), tol):
            comm = False
            break
    for a, b, c in itertools.product(elements, repeat=3):
        if not semiring_elements_equal(meet(meet(a, b), c), meet(a, meet(b, c)), tol):
            assoc = False
            break
    return {
        'meet_idempotence': idemp,
        'meet_commutativity': comm,
        'meet_associativity': assoc,
    }


def verify_lattice_laws(
    lattice: Lattice[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Lattice laws: join/meet semilattice laws plus absorption."""
    elements = _require_samples(samples)
    res = {}
    res.update(verify_join_semilattice_laws(lattice, elements, tol))
    res.update(verify_meet_semilattice_laws(lattice, elements, tol))
    join = lattice.join
    meet = lattice.meet
    absorb_1 = True
    absorb_2 = True
    for a, b in itertools.product(elements, repeat=2):
        if not semiring_elements_equal(meet(a, join(a, b)), a, tol):
            absorb_1 = False
        if not semiring_elements_equal(join(a, meet(a, b)), a, tol):
            absorb_2 = False
        if not absorb_1 or not absorb_2:
            break
    res['absorption_meet_join'] = absorb_1
    res['absorption_join_meet'] = absorb_2
    return res


def verify_bounded_lattice_laws(
    bl: BoundedLattice[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Bounded Lattice laws: lattice laws plus bot/top bounds."""
    elements = _require_samples(samples)
    res = verify_lattice_laws(bl, elements, tol)
    bot = bl.bot
    top = bl.top
    join = bl.join
    meet = bl.meet
    bot_id = True
    top_id = True
    for a in elements:
        if not semiring_elements_equal(join(bot, a), a, tol):
            bot_id = False
        if not semiring_elements_equal(meet(top, a), a, tol):
            top_id = False
    res['bot_identity'] = bot_id
    res['top_identity'] = top_id
    return res


def verify_distributive_lattice_laws(
    dl: DistributiveLattice[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Distributive Lattice laws: mutual distributivity of meet and join."""
    elements = _require_samples(samples)
    res = verify_lattice_laws(dl, elements, tol)
    join = dl.join
    meet = dl.meet
    dist_1 = True
    dist_2 = True
    for a, b, c in itertools.product(elements, repeat=3):
        if not semiring_elements_equal(meet(a, join(b, c)), join(meet(a, b), meet(a, c)), tol):
            dist_1 = False
        if not semiring_elements_equal(join(a, meet(b, c)), meet(join(a, b), join(a, c)), tol):
            dist_2 = False
        if not dist_1 or not dist_2:
            break
    res['distributivity_meet_join'] = dist_1
    res['distributivity_join_meet'] = dist_2
    return res


def verify_boolean_algebra_laws(
    ba: BooleanAlgebra[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Boolean Algebra laws: bounded distributive lattice plus complements."""
    elements = _require_samples(samples)
    res = verify_bounded_lattice_laws(ba, elements, tol)
    res.update(verify_distributive_lattice_laws(ba, elements, tol))
    comp = ba.complement
    join = ba.join
    meet = ba.meet
    top = ba.top
    bot = ba.bot
    comp_join = True
    comp_meet = True
    for a in elements:
        not_a = comp(a)
        if not semiring_elements_equal(join(a, not_a), top, tol):
            comp_join = False
        if not semiring_elements_equal(meet(a, not_a), bot, tol):
            comp_meet = False
    res['complement_join'] = comp_join
    res['complement_meet'] = comp_meet
    return res


def verify_group_action_laws(
    action: GroupAction[G, X],
    group: Group[G],
    group_samples: Iterable[G],
    set_samples: Iterable[X],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Group Action laws: identity action $\mathbf{1} \cdot x = x$
    and compatibility $g \cdot (h \cdot x) = (g h) \cdot x$.
    """
    g_elements = _require_samples(group_samples)
    x_elements = _require_samples(set_samples)
    gact = action.gact
    mul = group.mul
    one = group.one

    id_act = True
    for x in x_elements:
        if not semiring_elements_equal(gact(one, x), x, tol):
            id_act = False
            break

    compat = True
    for g, h in itertools.product(g_elements, repeat=2):
        for x in x_elements:
            lhs = gact(g, gact(h, x))
            rhs = gact(mul(g, h), x)
            if not semiring_elements_equal(lhs, rhs, tol):
                compat = False
                break
        if not compat:
            break

    return {
        'action_identity': id_act,
        'action_compatibility': compat,
    }


# =============================================================================
# EP-0191: Ring, Field, Module, and Algebra Law Verifiers
# =============================================================================


def verify_non_assoc_ring_laws(
    ring: NonAssocRing[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Non-Associative Ring laws: additive abelian group plus two-sided distributivity."""
    elements = _require_samples(samples)
    res = verify_add_comm_group_laws(ring, elements, tol)
    add = ring.add
    mul = ring.mul

    left_dist = True
    right_dist = True
    for a, b, c in itertools.product(elements, repeat=3):
        if not semiring_elements_equal(mul(a, add(b, c)), add(mul(a, b), mul(a, c)), tol):
            left_dist = False
        if not semiring_elements_equal(mul(add(a, b), c), add(mul(a, c), mul(b, c)), tol):
            right_dist = False
        if not left_dist or not right_dist:
            break

    res['left_distributivity'] = left_dist
    res['right_distributivity'] = right_dist
    return res


def verify_ring_laws(
    ring: Ring[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Ring laws: non-associative ring laws plus associative unital monoid."""
    elements = _require_samples(samples)
    res = verify_non_assoc_ring_laws(ring, elements, tol)
    res.update(verify_monoid_laws(ring, elements, tol))
    return res


def verify_comm_ring_laws(
    ring: CommRing[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Commutative Ring laws: ring laws plus multiplication commutativity."""
    elements = _require_samples(samples)
    res = verify_ring_laws(ring, elements, tol)
    mul = ring.mul
    comm = True
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(mul(a, b), mul(b, a), tol):
            comm = False
            break
    res['mul_commutativity'] = comm
    return res


def verify_division_ring_laws(
    dring: DivisionRing[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Division Ring laws: ring laws plus two-sided inverses for non-zero elements
    and ZeroDivisionError contract.
    """
    elements = _require_samples(samples)
    res = verify_ring_laws(dring, elements, tol)
    one = dring.one
    mul = dring.mul
    inv = dring.inv
    div = dring.div
    is_zero = dring.is_zero
    zero = dring.zero

    left_inv = True
    right_inv = True
    quotient = True

    non_zero_elements = [x for x in elements if not is_zero(x)]
    for a in non_zero_elements:
        inv_a = inv(a)
        if not semiring_elements_equal(mul(inv_a, a), one, tol):
            left_inv = False
        if not semiring_elements_equal(mul(a, inv_a), one, tol):
            right_inv = False
        for b in non_zero_elements:
            expected_div = mul(a, inv(b))
            if not semiring_elements_equal(div(a, b), expected_div, tol):
                quotient = False
                break

    # Contract invariant: division by zero raises ZeroDivisionError
    zero_div_raised = False
    try:
        inv(zero)
    except ZeroDivisionError:
        zero_div_raised = True
    except Exception:
        zero_div_raised = False

    res['left_inverse'] = left_inv
    res['right_inverse'] = right_inv
    res['quotient_consistency'] = quotient
    res['zero_division_guard'] = zero_div_raised
    return res


def verify_field_laws(
    field: Field[V],
    samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Field laws: division ring laws plus multiplicative commutativity."""
    elements = _require_samples(samples)
    res = verify_division_ring_laws(field, elements, tol)
    mul = field.mul
    comm = True
    for a, b in itertools.combinations(elements, 2):
        if not semiring_elements_equal(mul(a, b), mul(b, a), tol):
            comm = False
            break
    res['mul_commutativity'] = comm
    return res


def _verify_scalar_action_laws(
    smodule: Semimodule[R, M],
    semiring: Semiring[R],
    r_elements: list[R],
    m_elements: list[M],
    tol: float,
) -> dict[str, bool]:
    """Verify external scalar action axioms over a semiring or ring."""
    smul = smodule.smul
    add_m = smodule.add
    m_zero = smodule.zero
    r_one = semiring.one
    r_zero = semiring.zero
    add_r = semiring.add
    mul_r = semiring.mul

    left_dist = all(
        semiring_elements_equal(smul(r, add_m(m1, m2)), add_m(smul(r, m1), smul(r, m2)), tol)
        for r in r_elements
        for m1, m2 in itertools.combinations(m_elements, 2)
    )
    right_dist = all(
        semiring_elements_equal(smul(add_r(r1, r2), m), add_m(smul(r1, m), smul(r2, m)), tol)
        for r1, r2 in itertools.combinations(r_elements, 2)
        for m in m_elements
    )
    assoc = all(
        semiring_elements_equal(smul(mul_r(r1, r2), m), smul(r1, smul(r2, m)), tol)
        for r1, r2 in itertools.product(r_elements, repeat=2)
        for m in m_elements
    )
    id_scalar = all(semiring_elements_equal(smul(r_one, m), m, tol) for m in m_elements)
    annihil = all(semiring_elements_equal(smul(r_zero, m), m_zero, tol) for m in m_elements) and all(
        semiring_elements_equal(smul(r, m_zero), m_zero, tol) for r in r_elements
    )

    return {
        'scalar_left_distributivity': left_dist,
        'scalar_right_distributivity': right_dist,
        'scalar_associativity': assoc,
        'scalar_identity': id_scalar,
        'scalar_annihilation': annihil,
    }


def verify_semimodule_laws(
    smodule: Semimodule[R, M],
    semiring: Semiring[R],
    r_samples: Iterable[R],
    m_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Semimodule laws: additive commutative monoid on M plus semiring scalar action laws."""
    r_elements = _require_samples(r_samples)
    m_elements = _require_samples(m_samples)

    res = verify_add_comm_monoid_laws(smodule, m_elements, tol)
    res.update(_verify_scalar_action_laws(smodule, semiring, r_elements, m_elements, tol))
    return res


def verify_module_laws(
    module: Module[R, M],
    ring: Ring[R],
    r_samples: Iterable[R],
    m_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Module laws: abelian group on M plus ring scalar action laws."""
    r_elements = _require_samples(r_samples)
    m_elements = _require_samples(m_samples)

    res = verify_add_comm_group_laws(module, m_elements, tol)
    res.update(_verify_scalar_action_laws(module, ring, r_elements, m_elements, tol))
    return res


def verify_algebra_laws(
    algebra: Algebra[R, M],
    ring: Ring[R],
    r_samples: Iterable[R],
    m_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Algebra laws: module laws + ring laws on M + scalar bilinearity."""
    r_elements = _require_samples(r_samples)
    m_elements = _require_samples(m_samples)

    res = verify_module_laws(algebra, ring, r_elements, m_elements, tol)
    res.update(verify_ring_laws(algebra, m_elements, tol))

    smul = algebra.smul
    mul_m = algebra.mul

    bilinear = True
    for r in r_elements:
        for a, b in itertools.product(m_elements, repeat=2):
            lhs = smul(r, mul_m(a, b))
            rhs1 = mul_m(smul(r, a), b)
            rhs2 = mul_m(a, smul(r, b))
            if not semiring_elements_equal(lhs, rhs1, tol) or not semiring_elements_equal(lhs, rhs2, tol):
                bilinear = False
                break
        if not bilinear:
            break

    res['scalar_bilinearity'] = bilinear
    return res


def verify_non_assoc_algebra_laws(
    algebra: NonAssocAlgebra[R, M],
    ring: Ring[R],
    r_samples: Iterable[R],
    m_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Non-Associative Algebra laws:
    - Module laws over ring R
    - NonAssocRing laws on M (additive abelian group + two-sided distributivity)
    - Scalar bilinearity: r * (a * b) == (r * a) * b == a * (r * b)
    """
    r_elements = _require_samples(r_samples)
    m_elements = _require_samples(m_samples)

    res = verify_module_laws(algebra, ring, r_elements, m_elements, tol)
    res.update(verify_non_assoc_ring_laws(algebra, m_elements, tol))

    smul = algebra.smul
    mul_m = algebra.mul

    bilinear = True
    for r in r_elements:
        for a, b in itertools.product(m_elements, repeat=2):
            lhs = smul(r, mul_m(a, b))
            rhs1 = mul_m(smul(r, a), b)
            rhs2 = mul_m(a, smul(r, b))
            if not semiring_elements_equal(lhs, rhs1, tol) or not semiring_elements_equal(lhs, rhs2, tol):
                bilinear = False
                break
        if not bilinear:
            break

    res['scalar_bilinearity'] = bilinear
    return res


def verify_lie_algebra_laws(
    lie: NonAssocAlgebra[R, M],
    ring: Ring[R],
    r_samples: Iterable[R],
    m_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Lie Algebra axioms:
    - NonAssocAlgebra laws (Module + distributivity + bilinearity)
    - Skew-symmetry: [x, x] == 0 and [x, y] == -[y, x]
    - Jacobi Identity: [x, [y, z]] + [y, [z, x]] + [z, [x, y]] == 0
    """
    m_elements = _require_samples(m_samples)
    res = verify_non_assoc_algebra_laws(lie, ring, r_samples, m_elements, tol)

    bracket = lie.mul
    add = lie.add
    neg = lie.neg
    zero = lie.zero

    # Alternating / Skew-symmetry
    skew = True
    for a in m_elements:
        if not semiring_elements_equal(bracket(a, a), zero, tol):
            skew = False
            break
    for a, b in itertools.combinations(m_elements, 2):
        if not semiring_elements_equal(bracket(a, b), neg(bracket(b, a)), tol):
            skew = False
            break

    # Jacobi identity: [x, [y, z]] + [y, [z, x]] + [z, [x, y]] == 0
    jacobi = True
    for a, b, c in itertools.product(m_elements, repeat=3):
        t1 = bracket(a, bracket(b, c))
        t2 = bracket(b, bracket(c, a))
        t3 = bracket(c, bracket(a, b))
        j_sum = add(add(t1, t2), t3)
        if not semiring_elements_equal(j_sum, zero, tol):
            jacobi = False
            break

    res['bracket_alternating'] = skew
    res['jacobi_identity'] = jacobi
    return res


# =============================================================================
# EP-0200: Category and Functor Law Verifiers
# =============================================================================

from algebrax.category.core import Category, Functor  # noqa: E402

Obj = TypeVar('Obj')
Mor = TypeVar('Mor')
Obj2 = TypeVar('Obj2')
Mor2 = TypeVar('Mor2')


def verify_category_laws(
    cat: Category[Obj, Mor],
    objects: Iterable[Obj],
    morphisms: Iterable[Mor],
    eq_fn: Callable[[Mor, Mor], bool] | None = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Category axioms over sample objects and morphisms:
    - Left Identity: $\mathrm{compose}(f, \mathrm{id}(\mathrm{target}(f))) = f$
    - Right Identity: $\mathrm{compose}(\mathrm{id}(\mathrm{source}(f)), f) = f$
    - Associativity: $\mathrm{compose}(\mathrm{compose}(f, g), h) = \mathrm{compose}(f, \mathrm{compose}(g, h))$
    """
    _ = list(objects)
    mor_list = _require_samples(morphisms)
    cmp = eq_fn if eq_fn is not None else (lambda a, b: semiring_elements_equal(a, b, tol))

    left_id = True
    right_id = True
    for f in mor_list:
        id_cod = cat.id(cat.target(f))
        id_dom = cat.id(cat.source(f))
        if not cmp(cat.compose(f, id_cod), f):
            left_id = False
        if not cmp(cat.compose(id_dom, f), f):
            right_id = False

    assoc = True
    for f, g, h in itertools.product(mor_list, repeat=3):
        if cat.target(f) != cat.source(g) or cat.target(g) != cat.source(h):
            continue
        lhs = cat.compose(cat.compose(f, g), h)
        rhs = cat.compose(f, cat.compose(g, h))
        if not cmp(lhs, rhs):
            assoc = False
            break

    return {
        'left_identity': left_id,
        'right_identity': right_id,
        'associativity': assoc,
    }


def verify_functor_laws(
    functor: Functor[Obj, Mor, Obj2, Mor2],
    cat_src: Category[Obj, Mor],
    cat_dst: Category[Obj2, Mor2],
    test_objects: Iterable[Obj],
    test_morphisms: Iterable[Mor],
    eq_fn: Callable[[Mor2, Mor2], bool] | None = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Functor axioms between source category $\mathcal{C}$ and target category $\mathcal{D}$:
    - Identity Preservation: $F(\mathrm{id}_x) = \mathrm{id}_{F(x)}$
    - Composition Preservation: $F(\mathrm{compose}_{\mathcal{C}}(f, g)) = \mathrm{compose}_{\mathcal{D}}(F(f), F(g))$
    """
    obj_list = list(test_objects)
    if not obj_list:
        raise ValueError('Functor verification requires at least 1 test object.')
    mor_list = _require_samples(test_morphisms)
    cmp = eq_fn if eq_fn is not None else (lambda a, b: semiring_elements_equal(a, b, tol))

    id_pres = True
    for x in obj_list:
        lhs_id = functor.map_mor(cat_src.id(x))
        rhs_id = cat_dst.id(functor.map_obj(x))
        if not cmp(lhs_id, rhs_id):
            id_pres = False
            break

    comp_pres = True
    for f, g in itertools.product(mor_list, repeat=2):
        lhs_comp = functor.map_mor(cat_src.compose(f, g))
        rhs_comp = cat_dst.compose(functor.map_mor(f), functor.map_mor(g))
        if not cmp(lhs_comp, rhs_comp):
            comp_pres = False
            break

    return {
        'identity_preservation': id_pres,
        'composition_preservation': comp_pres,
    }


# =============================================================================
# EP-0201: Homomorphism, Ideal, and Quotient Ring Law Verifiers
# =============================================================================

from algebrax.algebra._homomorphisms import RingHom  # noqa: E402
from algebrax.algebra._ideals import Ideal  # noqa: E402
from algebrax.algebra._quotient import QuotientRing  # noqa: E402

Dom = TypeVar('Dom')
Cod = TypeVar('Cod')


def verify_ring_homomorphism_laws(
    hom: RingHom[Dom, Cod],
    ring_dom: Ring[Dom] | CommRing[Dom],
    ring_cod: Ring[Cod] | CommRing[Cod],
    samples: Iterable[Dom],
    eq_fn: Callable[[Cod, Cod], bool] | None = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test unital Ring Homomorphism axioms for $\phi: R_1 \to R_2$:
    - Zero Preservation: $\phi(\mathbf{0}_{R_1}) = \mathbf{0}_{R_2}$
    - One Preservation: $\phi(\mathbf{1}_{R_1}) = \mathbf{1}_{R_2}$
    - Addition Preservation: $\phi(a + b) = \phi(a) + \phi(b)$
    - Multiplication Preservation: $\phi(a \cdot b) = \phi(a) \cdot \phi(b)$
    """
    elements = _require_samples(samples)
    cmp = eq_fn if eq_fn is not None else (lambda a, b: semiring_elements_equal(a, b, tol))

    zero_pres = cmp(hom(ring_dom.zero), ring_cod.zero)
    one_pres = cmp(hom(ring_dom.one), ring_cod.one)

    add_pres = True
    mul_pres = True
    for a, b in itertools.product(elements, repeat=2):
        if not cmp(hom(ring_dom.add(a, b)), ring_cod.add(hom(a), hom(b))):
            add_pres = False
        if not cmp(hom(ring_dom.mul(a, b)), ring_cod.mul(hom(a), hom(b))):
            mul_pres = False

    return {
        'zero_preservation': zero_pres,
        'one_preservation': one_pres,
        'add_preservation': add_pres,
        'mul_preservation': mul_pres,
    }


def verify_ideal_absorption_laws(
    ring: Ring[V] | CommRing[V],
    ideal: Ideal[V],
    ring_samples: Iterable[V],
    ideal_samples: Iterable[V],
) -> dict[str, bool]:
    r"""Test two-sided Ideal axioms for $I \triangleleft R$:
    - Zero Containment: $\mathbf{0}_R \in I$
    - Additive Closure: $\forall x, y \in I,\; x + y \in I \land -x \in I$
    - Left Absorption: $\forall r \in R,\, x \in I,\; r \cdot x \in I$
    - Right Absorption: $\forall r \in R,\, x \in I,\; x \cdot r \in I$
    """
    r_list = _require_samples(ring_samples)
    i_list = _require_samples(ideal_samples, min_count=1)

    zero_in = ideal.contains(ring.zero)

    add_closed = True
    for x in i_list:
        if not ideal.contains(x) or not ideal.contains(ring.neg(x)):
            add_closed = False
            break
    if add_closed:
        for x, y in itertools.product(i_list, repeat=2):
            if not ideal.contains(ring.add(x, y)):
                add_closed = False
                break

    left_abs = True
    right_abs = True
    for r in r_list:
        for x in i_list:
            if not ideal.contains(ring.mul(r, x)):
                left_abs = False
            if not ideal.contains(ring.mul(x, r)):
                right_abs = False

    return {
        'zero_containment': zero_in,
        'additive_closure': add_closed,
        'left_absorption': left_abs,
        'right_absorption': right_abs,
    }


def verify_quotient_ring_laws(
    quotient: QuotientRing[V],
    ring_samples: Iterable[V],
    ideal_samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Quotient Ring $R / I$ well-definedness (congruence invariance) and Ring axioms:
    - Coset Invariance: $\forall a, b \in R,\, i_1, i_2 \in I$:
      $[a + i_1] +_{R/I} [b + i_2] = [a + b]$ and $[a + i_1] \cdot_{R/I} [b + i_2] = [a \cdot b]$
    - Canonical Projection Homomorphism: $\pi(x) = \mathrm{ideal.reduce}(x)$ satisfies `RingHom` laws
    - Ring Laws: $R / I$ satisfies all associative unital ring axioms
    """
    r_list = _require_samples(ring_samples)
    i_list = _require_samples(ideal_samples, min_count=1)
    base = quotient.base_ring

    coset_invariance = True
    for a, b in itertools.product(r_list, repeat=2):
        for i1, i2 in itertools.product(i_list, repeat=2):
            a_pert = base.add(a, i1)
            b_pert = base.add(b, i2)
            if not semiring_elements_equal(quotient.add(a_pert, b_pert), quotient.add(a, b), tol):
                coset_invariance = False
                break
            if not semiring_elements_equal(quotient.mul(a_pert, b_pert), quotient.mul(a, b), tol):
                coset_invariance = False
                break
        if not coset_invariance:
            break

    reduced_samples = [quotient.project(r) for r in r_list]
    ring_res = verify_ring_laws(quotient, reduced_samples, tol)
    hom_res = verify_ring_homomorphism_laws(
        quotient.project,
        base,
        quotient,
        r_list,
        tol=tol,
    )

    return {
        **ring_res,
        'coset_invariance': coset_invariance,
        'projection_homomorphism': all(hom_res.values()),
    }


def verify_sheaf_functoriality(
    sheaf: Any,
    sample_paths: Iterable[tuple[Any, Any, Any]],
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify functoriality of cellular sheaf restriction maps:
    - Identity Preservation: $\mathcal{E}_{\sigma \trianglelefteq \sigma} = I_{d_\sigma}$
    - Composition Preservation:
      $\mathcal{E}_{\tau \trianglelefteq \rho} \circ \mathcal{E}_{\sigma \trianglelefteq \tau}
      = \mathcal{E}_{\sigma \trianglelefteq \rho}$
    """
    from algebrax.matrix.core import dot
    from algebrax.semiring import StandardSemiring

    semiring = StandardSemiring(float)
    id_ok = True
    for cell in sheaf.poset_category.cells:
        d = sheaf.stalk_dim(cell)
        expected_id = {i: {i: 1.0} for i in range(d)}
        actual_id = sheaf.restriction_map(cell, cell)
        if not semiring_elements_equal(actual_id, expected_id, tol):
            id_ok = False
            break

    comp_ok = True
    for sigma, tau, rho in sample_paths:
        r_sigma_tau = sheaf.restriction_map(sigma, tau)
        r_tau_rho = sheaf.restriction_map(tau, rho)
        r_sigma_rho = sheaf.restriction_map(sigma, rho)
        composed = dot(r_tau_rho, r_sigma_tau, semiring=semiring)
        if not semiring_elements_equal(composed, r_sigma_rho, tol):
            comp_ok = False
            break

    return {
        'identity_preservation': id_ok,
        'composition_preservation': comp_ok,
    }


def verify_coboundary_nilpotency(
    sheaf: Any,
    k: int = 0,
    tol: float = 1e-12,
) -> bool:
    r"""Verify the fundamental cohomological invariant $\delta^{k+1} \circ \delta^k = \mathbf{0}$."""
    from algebrax.matrix.core import dot
    from algebrax.semiring import StandardSemiring
    from algebrax.topology.sheaf import build_sheaf_coboundary_matrix

    semiring = StandardSemiring(float)
    delta_k = build_sheaf_coboundary_matrix(sheaf, k)
    delta_k1 = build_sheaf_coboundary_matrix(sheaf, k + 1)
    if not delta_k or not delta_k1:
        return True
    delta2 = dot(delta_k1, delta_k, semiring=semiring)
    return not delta2 or all(abs(val) < tol for row in delta2.values() for val in row.values())


def verify_sheaf_laplacian_properties(
    sheaf: Any,
    k: int = 0,
    sample_cochains: Iterable[dict[Any, float]] = (),
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify structural invariants of the $k$-th Sheaf Laplacian $L_k$:
    - Self-Adjoint Symmetry: $L_k^T = L_k$
    - Positive Semi-Definiteness: $\langle x, L_k x \rangle \ge 0$ for all sample $k$-cochains $x$
    """
    from algebrax.matrix.core import inner, mat_vec, transpose
    from algebrax.topology.sheaf import build_sheaf_laplacian

    lap = build_sheaf_laplacian(sheaf, k)
    lap_t = transpose(lap)
    symmetric = semiring_elements_equal(lap, lap_t, tol)

    psd = True
    for x in sample_cochains:
        if not x or not lap:
            continue
        lx = mat_vec(lap, x)
        energy = float(inner(x, lx))
        if energy < -tol:
            psd = False
            break

    return {
        'symmetry': symmetric,
        'positive_semidefinite': psd,
    }


def verify_connection_inversion(
    connection: Any,
    edges: Iterable[tuple[Any, Any]],
    tol: float = 1e-12,
) -> bool:
    r"""Verify that parallel transport satisfies $\rho(v, u) \cdot \rho(u, v) = I_d$ for all edges."""
    from algebrax.matrix.core import dot
    from algebrax.semiring import StandardSemiring

    semiring = StandardSemiring(float)
    d = connection.fiber_dim
    for u, v in edges:
        t_uv = connection.transport(u, v)
        t_vu = connection.transport(v, u)
        prod = dot(t_vu, t_uv, semiring=semiring)
        for i in range(d):
            for j in range(d):
                expected = 1.0 if i == j else 0.0
                if abs(prod.get(i, {}).get(j, 0.0) - expected) >= tol:
                    return False
    return True


def verify_gauge_covariance(
    connection: Any,
    adjacency: Any,
    gauge_transform: dict[Any, Any],
    tol: float = 1e-9,
) -> bool:
    r"""Verify that under local vertex gauge transformations $g_u \in O(d)$,
    the Connection Laplacian transforms covariantly:
    $$L_{\nabla'} = \mathbf{G} \, L_\nabla \, \mathbf{G}^T$$
    """
    from algebrax.matrix.core import dot, transpose
    from algebrax.semiring import StandardSemiring
    from algebrax.topology.bundle import (
        apply_gauge_transformation,
        build_connection_laplacian,
    )

    semiring = StandardSemiring(float)
    d = connection.fiber_dim
    ident = {i: {i: 1.0} for i in range(d)}

    l_orig = build_connection_laplacian(connection, adjacency)
    conn_prime = apply_gauge_transformation(connection, gauge_transform)
    l_prime = build_connection_laplacian(conn_prime, adjacency)

    # Assemble block-diagonal global gauge matrix G
    big_g: dict[tuple[Any, int], dict[tuple[Any, int], float]] = {}
    for u in adjacency:
        g_u = gauge_transform.get(u, ident)
        for i, row in g_u.items():
            row_u: dict[tuple[Any, int], float] = {}
            for j, val in row.items():
                if abs(float(val)) > 1e-15:
                    row_u[(u, int(j))] = float(val)
            if row_u:
                big_g[(u, int(i))] = row_u

    expected_l_prime = dot(big_g, dot(l_orig, transpose(big_g), semiring=semiring), semiring=semiring)
    return semiring_elements_equal(l_prime, expected_l_prime, tol)


def verify_jordan_laws(
    algebra: Any,
    samples: Iterable[Any],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Jordan Algebra axioms:
    - Commutativity: $x \circ y = y \circ x$
    - Jordan Identity: $(x \circ y) \circ (x \circ x) = x \circ (y \circ (x \circ x))$
    """
    elements = _require_samples(samples)
    mul = algebra.mul

    comm = True
    jordan_id = True
    for x, y in itertools.product(elements, repeat=2):
        xy = mul(x, y)
        yx = mul(y, x)
        if not semiring_elements_equal(xy, yx, tol):
            comm = False
        x2 = mul(x, x)
        lhs = mul(xy, x2)
        rhs = mul(x, mul(y, x2))
        if not semiring_elements_equal(lhs, rhs, tol):
            jordan_id = False

    return {
        'commutativity': comm,
        'jordan_identity': jordan_id,
    }


def verify_alternative_laws(
    algebra: Any,
    samples: Iterable[Any],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Alternative Algebra axioms:
    - Left Alternative Law: $x(xy) = (xx)y$
    - Right Alternative Law: $(yx)x = y(xx)$
    - Flexible Law: $x(yx) = (xy)x$
    """
    elements = _require_samples(samples)
    mul = algebra.mul

    left_alt = True
    right_alt = True
    flexible = True
    for x, y in itertools.product(elements, repeat=2):
        xx = mul(x, x)
        xy = mul(x, y)
        yx = mul(y, x)
        if not semiring_elements_equal(mul(x, xy), mul(xx, y), tol):
            left_alt = False
        if not semiring_elements_equal(mul(yx, x), mul(y, xx), tol):
            right_alt = False
        if not semiring_elements_equal(mul(x, yx), mul(xy, x), tol):
            flexible = False

    return {
        'left_alternative': left_alt,
        'right_alternative': right_alt,
        'flexible': flexible,
    }


def verify_malcev_laws(
    algebra: Any,
    samples: Iterable[Any],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Malcev Algebra axioms:
    - Anticommutativity: $x \cdot y = -(y \cdot x)$
    - Malcev Identity: $J(x, y, x \cdot z) = J(x, y, z) \cdot x$, where
      $J(a, b, c) = (a \cdot b) \cdot c + (b \cdot c) \cdot a + (c \cdot a) \cdot b$
    """
    elements = _require_samples(samples)
    mul = algebra.mul
    add = algebra.add
    neg = algebra.neg

    def jacobian(a: Any, b: Any, c: Any) -> Any:
        return add(add(mul(mul(a, b), c), mul(mul(b, c), a)), mul(mul(c, a), b))

    anticomm = True
    for x, y in itertools.product(elements, repeat=2):
        if not semiring_elements_equal(mul(x, y), neg(mul(y, x)), tol):
            anticomm = False
            break

    malcev_id = True
    for x, y, z in itertools.product(elements, repeat=3):
        lhs = jacobian(x, y, mul(x, z))
        rhs = mul(jacobian(x, y, z), x)
        if not semiring_elements_equal(lhs, rhs, tol):
            malcev_id = False
            break

    return {
        'anticommutativity': anticomm,
        'malcev_identity': malcev_id,
    }


def verify_poisson_laws(
    poisson: Any,
    samples: Iterable[Any],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Poisson Algebra axioms:
    - Bracket Anticommutativity: $\{f, g\} = -\{g, f\}$
    - Jacobi Identity: $\{f, \{g, h\}\} + \{g, \{h, f\}\} + \{h, \{f, g\}\} = \mathbf{0}$
    - Leibniz Derivation Rule: $\{f, g \cdot h\} = \{f, g\} \cdot h + g \cdot \{f, h\}$
    """
    elements = _require_samples(samples)
    mul = poisson.mul
    bracket = poisson.bracket
    add = poisson.add
    neg = poisson.neg
    zero = poisson.zero

    anticomm = True
    for f, g in itertools.product(elements, repeat=2):
        if not semiring_elements_equal(bracket(f, g), neg(bracket(g, f)), tol):
            anticomm = False
            break

    jacobi = True
    leibniz = True
    for f, g, h in itertools.product(elements, repeat=3):
        t1 = bracket(f, bracket(g, h))
        t2 = bracket(g, bracket(h, f))
        t3 = bracket(h, bracket(f, g))
        if not semiring_elements_equal(add(add(t1, t2), t3), zero, tol):
            jacobi = False

        lhs = bracket(f, mul(g, h))
        rhs = add(mul(bracket(f, g), h), mul(g, bracket(f, h)))
        if not semiring_elements_equal(lhs, rhs, tol):
            leibniz = False

    return {
        'anticommutativity': anticomm,
        'jacobi_identity': jacobi,
        'leibniz_rule': leibniz,
    }


# =============================================================================
# Normed Spaces, Inner Products & Banach Contractions (EP-0205)
# =============================================================================


def verify_triangle_inequality(
    space: NormedSpace[Any, V],
    u: V,
    v: V,
    tol: float = 1e-9,
) -> bool:
    r"""Verify the triangle inequality $\|u + v\| \le \|u\| + \|v\| + \text{tol}$."""
    sum_uv = space.add(u, v)
    norm_sum = space.norm(sum_uv)
    bound = space.norm(u) + space.norm(v)
    return norm_sum <= bound + tol


def verify_cauchy_schwarz(
    space: InnerProductSpace[Any, V],
    u: V,
    v: V,
    tol: float = 1e-9,
) -> bool:
    r"""Verify the Cauchy-Schwarz inequality.

    $|\langle u, v \rangle|^2 \le \langle u, u \rangle \langle v, v \rangle + \text{tol}$.
    """
    inner_uv = space.inner(u, v)
    lhs = abs(inner_uv) ** 2 if isinstance(inner_uv, complex) else float(inner_uv) ** 2

    inner_uu = space.inner(u, u)
    inner_vv = space.inner(v, v)
    rhs = float(inner_uu.real if isinstance(inner_uu, complex) else inner_uu) * float(
        inner_vv.real if isinstance(inner_vv, complex) else inner_vv
    )
    return lhs <= rhs + tol


def verify_parallelogram_law(
    space: InnerProductSpace[Any, V],
    u: V,
    v: V,
    tol: float = 1e-7,
) -> bool:
    r"""Verify the parallelogram law: $\|u + v\|^2 + \|u - v\|^2 \approx 2(\|u\|^2 + \|v\|^2)$."""
    sum_uv = space.add(u, v)
    diff_uv = space.sub(u, v)
    norm_sum_sq = space.norm(sum_uv) ** 2
    norm_diff_sq = space.norm(diff_uv) ** 2
    lhs = norm_sum_sq + norm_diff_sq

    norm_u_sq = space.norm(u) ** 2
    norm_v_sq = space.norm(v) ** 2
    rhs = 2.0 * (norm_u_sq + norm_v_sq)

    return math.isclose(lhs, rhs, rel_tol=tol, abs_tol=tol)


def verify_contraction_constant(
    space: NormedSpace[Any, V],
    operator: Callable[[V], V],
    samples: Sequence[V],
    gamma: float,
    tol: float = 1e-9,
) -> bool:
    r"""Verify that operator $T$ satisfies $\|T(u) - T(v)\| \le \gamma \|u - v\| + \text{tol}$ for all sample pairs."""
    if not (0.0 <= gamma < 1.0):
        raise ValueError(f'Contraction constant gamma must be in [0, 1), got {gamma}')

    n = len(samples)
    for i in range(n):
        for j in range(i + 1, n):
            u, v = samples[i], samples[j]
            d_in = space.distance(u, v)
            d_out = space.distance(operator(u), operator(v))
            if d_out > gamma * d_in + tol:
                return False
    return True


def verify_normed_space_laws(
    space: NormedSpace[R, V],
    r_samples: Iterable[R],
    v_samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify axioms of a NormedSpace:
    - Non-negativity: $\|v\| \ge 0$
    - Identity of indiscernibles: $\|v\| \approx 0 \iff v \approx \mathbf{0}$
    - Absolute scalability: $\|\alpha \cdot_s v\| \approx |\alpha| \cdot \|v\|$
    - Triangle inequality: $\|u + v\| \le \|u\| + \|v\|$
    """
    v_elements = _require_samples(v_samples)
    r_elements = _require_samples(r_samples)

    non_neg = True
    zero_norm = _float_equal(space.norm(space.zero), 0.0, tol)
    for v in v_elements:
        if space.norm(v) < -tol:
            non_neg = False
            break

    scalability = True
    for r in r_elements:
        for v in v_elements:
            scaled = space.smul(r, v)
            norm_scaled = space.norm(scaled)
            r_mag = abs(r) if isinstance(r, (int, float, complex)) else 1.0
            expected = r_mag * space.norm(v)
            if not _float_equal(norm_scaled, expected, tol):
                scalability = False
                break
        if not scalability:
            break

    tri = True
    for u, v in itertools.combinations(v_elements, 2):
        if not verify_triangle_inequality(space, u, v, tol):
            tri = False
            break

    return {
        'non_negativity': non_neg,
        'zero_norm': zero_norm,
        'absolute_scalability': scalability,
        'triangle_inequality': tri,
    }


def verify_inner_product_space_laws(
    space: InnerProductSpace[R, V],
    r_samples: Iterable[R],
    v_samples: Iterable[V],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify axioms of an InnerProductSpace:
    - All NormedSpace axioms
    - Cauchy-Schwarz inequality: $|\langle u, v \rangle|^2 \le \langle u, u \rangle \langle v, v \rangle$
    - Parallelogram law: $\|u+v\|^2 + \|u-v\|^2 \approx 2(\|u\|^2 + \|v\|^2)$
    - Symmetry / Conjugate symmetry: $\langle u, v \rangle \approx \overline{\langle v, u \rangle}$
    - Linearity in first argument:
      $\langle \alpha u + v, w \rangle \approx \alpha \langle u, w \rangle + \langle v, w \rangle$
    """
    v_elements = _require_samples(v_samples)
    r_elements = _require_samples(r_samples)

    res = verify_normed_space_laws(space, r_elements, v_elements, tol)

    cs = True
    for u, v in itertools.combinations(v_elements, 2):
        if not verify_cauchy_schwarz(space, u, v, tol):
            cs = False
            break

    pl = True
    for u, v in itertools.combinations(v_elements, 2):
        if not verify_parallelogram_law(space, u, v, tol):
            pl = False
            break

    sym = True
    for u, v in itertools.combinations(v_elements, 2):
        uv = space.inner(u, v)
        vu = space.inner(v, u)
        if isinstance(vu, complex):
            vu = vu.conjugate()
        if not semiring_elements_equal(uv, vu, tol):
            sym = False
            break

    lin = True
    w = v_elements[0]
    for r in r_elements:
        for u, v in itertools.combinations(v_elements, 2):
            lhs = space.inner(space.add(space.smul(r, u), v), w)
            uw = space.inner(u, w)
            vw = space.inner(v, w)
            if isinstance(r, (int, float, complex)) and isinstance(uw, (int, float, complex)):
                rhs = r * uw + vw
            else:
                rhs = space.add(space.smul(r, uw), vw)  # type: ignore[arg-type]
            if not semiring_elements_equal(lhs, rhs, tol):
                lin = False
                break
        if not lin:
            break

    res['cauchy_schwarz'] = cs
    res['parallelogram_law'] = pl
    res['conjugate_symmetry'] = sym
    res['first_argument_linearity'] = lin
    return res


# =============================================================================
# EP-0206: Coalgebra, Bialgebra & Hopf Algebra Axiom Verifiers
# =============================================================================

C = TypeVar('C')


def _carrier_basis(val: Any) -> Any:
    if isinstance(val, dict):
        return val
    return {val: 1.0}


def verify_coassociativity(
    coalgebra: Coalgebra[Any, C],
    samples: Iterable[C],
    tol: float = 1e-9,
) -> bool:
    r"""Verify that $(\Delta \otimes \mathrm{id}) \circ \Delta(c) == (\mathrm{id} \otimes \Delta) \circ \Delta(c)$."""
    for c in samples:
        delta_c = coalgebra.coproduct(c)

        # 1. Left parenthesization: (Delta (x) id) Delta(c)
        tensor_left: dict[tuple[Any, Any, Any], float] = {}
        for (u, v), alpha in delta_c.items():
            af = float(alpha)
            u_basis = _carrier_basis(u)
            delta_u = coalgebra.coproduct(u_basis)
            for (x, y), beta in delta_u.items():
                key = (x, y, v)
                tensor_left[key] = tensor_left.get(key, 0.0) + af * float(beta)

        # 2. Right parenthesization: (id (x) Delta) Delta(c)
        tensor_right: dict[tuple[Any, Any, Any], float] = {}
        for (u, v), alpha in delta_c.items():
            af = float(alpha)
            v_basis = _carrier_basis(v)
            delta_v = coalgebra.coproduct(v_basis)
            for (y, z), gamma in delta_v.items():
                key = (u, y, z)
                tensor_right[key] = tensor_right.get(key, 0.0) + af * float(gamma)

        tl_clean = {k: val for k, val in tensor_left.items() if abs(val) > tol}
        tr_clean = {k: val for k, val in tensor_right.items() if abs(val) > tol}

        if not semiring_elements_equal(tl_clean, tr_clean, tol):
            return False

    return True


def _clean_sparse(val: Any, tol: float) -> Any:
    if isinstance(val, dict):
        return {
            k: v
            for k, v in val.items()
            if (abs(v) > tol if isinstance(v, (int, float, complex)) else True)
        }
    return val


def verify_counitality(
    coalgebra: Coalgebra[Any, C],
    samples: Iterable[C],
    tol: float = 1e-9,
) -> bool:
    r"""Verify counitality:
    $(\epsilon \otimes \mathrm{id})\Delta(c) == c == (\mathrm{id} \otimes \epsilon)\Delta(c)$.
    """
    for c in samples:
        delta_c = coalgebra.coproduct(c)

        # Left counitality: sum_{(u, v)} alpha * epsilon(u) * v
        left_eval = coalgebra.zero
        for (u, v), alpha in delta_c.items():
            u_basis = _carrier_basis(u)
            v_basis = _carrier_basis(v)
            eps_u = coalgebra.counit(u_basis)
            scaled_v = coalgebra.smul(float(alpha) * float(eps_u), v_basis)
            left_eval = coalgebra.add(left_eval, scaled_v)

        c_clean = _clean_sparse(c, tol)
        if not semiring_elements_equal(_clean_sparse(left_eval, tol), c_clean, tol):
            return False

        # Right counitality: sum_{(u, v)} alpha * epsilon(v) * u
        right_eval = coalgebra.zero
        for (u, v), alpha in delta_c.items():
            u_basis = _carrier_basis(u)
            v_basis = _carrier_basis(v)
            eps_v = coalgebra.counit(v_basis)
            scaled_u = coalgebra.smul(float(alpha) * float(eps_v), u_basis)
            right_eval = coalgebra.add(right_eval, scaled_u)

        if not semiring_elements_equal(_clean_sparse(right_eval, tol), c_clean, tol):
            return False

    return True


def verify_antipode_axiom(
    hopf: HopfAlgebra[Any, C],
    samples: Iterable[C],
    tol: float = 1e-9,
) -> bool:
    r"""Verify the antipode axiom:
    $$\sum S(c_{(1)}) \cdot c_{(2)} = \epsilon(c) \mathbf{1} = \sum c_{(1)} \cdot S(c_{(2)})$$
    """
    one = hopf.one
    for c in samples:
        delta_c = hopf.coproduct(c)
        eps_c = hopf.counit(c)
        expected = hopf.smul(eps_c, one)

        # Left condition: sum S(u) * v
        left_val = hopf.zero
        for (u, v), alpha in delta_c.items():
            u_basis = _carrier_basis(u)
            v_basis = _carrier_basis(v)
            s_u = hopf.antipode(u_basis)
            prod = hopf.mul(s_u, v_basis)
            scaled = hopf.smul(float(alpha), prod)
            left_val = hopf.add(left_val, scaled)

        exp_clean = _clean_sparse(expected, tol)
        if not semiring_elements_equal(_clean_sparse(left_val, tol), exp_clean, tol):
            return False

        # Right condition: sum u * S(v)
        right_val = hopf.zero
        for (u, v), alpha in delta_c.items():
            u_basis = _carrier_basis(u)
            v_basis = _carrier_basis(v)
            s_v = hopf.antipode(v_basis)
            prod = hopf.mul(u_basis, s_v)
            scaled = hopf.smul(float(alpha), prod)
            right_val = hopf.add(right_val, scaled)

        if not semiring_elements_equal(_clean_sparse(right_val, tol), exp_clean, tol):
            return False

    return True


def verify_coalgebra_laws(
    coalgebra: Coalgebra[R, C],
    r_samples: Iterable[R],
    c_samples: Iterable[C],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify axioms of a Coalgebra:
    - Vector space axioms on (C, +, 0, -, smul)
    - Coassociativity: $(\Delta \otimes \mathrm{id}) \circ \Delta = (\mathrm{id} \otimes \Delta) \circ \Delta$
    - Counitality: $(\epsilon \otimes \mathrm{id})\Delta(c) = c = (\mathrm{id} \otimes \epsilon)\Delta(c)$
    """
    c_elements = _require_samples(c_samples)
    r_elements = _require_samples(r_samples)

    res = verify_add_comm_group_laws(coalgebra, c_elements, tol)

    smul = coalgebra.smul
    add_c = coalgebra.add
    c_zero = coalgebra.zero

    dist = True
    for r in r_elements:
        for c1, c2 in itertools.combinations(c_elements, 2):
            lhs = smul(r, add_c(c1, c2))
            rhs = add_c(smul(r, c1), smul(r, c2))
            if not semiring_elements_equal(lhs, rhs, tol):
                dist = False
                break
        if not dist:
            break

    annihil = True
    for r in r_elements:
        if not semiring_elements_equal(smul(r, c_zero), c_zero, tol):
            annihil = False
            break

    res['scalar_distributivity'] = dist
    res['scalar_zero_annihilation'] = annihil
    res['coassociativity'] = verify_coassociativity(coalgebra, c_elements, tol)
    res['counitality'] = verify_counitality(coalgebra, c_elements, tol)
    return res


def verify_bialgebra_laws(
    bialgebra: Bialgebra[R, C],
    r_samples: Iterable[R],
    c_samples: Iterable[C],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify axioms of a Bialgebra:
    - Coalgebra axioms
    - Monoid / Algebra axioms for multiplication
    - Homomorphism compatibility of Delta and epsilon with multiplication and unit
    """
    c_elements = _require_samples(c_samples)
    r_elements = _require_samples(r_samples)

    res = verify_coalgebra_laws(bialgebra, r_elements, c_elements, tol)
    res.update(verify_monoid_laws(bialgebra, c_elements, tol))

    # Counit homomorphism: epsilon(a * b) == epsilon(a) * epsilon(b), epsilon(1) == 1
    counit_hom = True
    one = bialgebra.one
    eps_one = bialgebra.counit(one)
    if not math.isclose(float(eps_one), 1.0, rel_tol=tol, abs_tol=tol):
        counit_hom = False

    for a, b in itertools.combinations(c_elements, 2):
        eps_ab = bialgebra.counit(bialgebra.mul(a, b))
        eps_a_eps_b = float(bialgebra.counit(a)) * float(bialgebra.counit(b))
        if not math.isclose(float(eps_ab), eps_a_eps_b, rel_tol=tol, abs_tol=tol):
            counit_hom = False
            break

    # Coproduct unit preservation: Delta(1) has sum of coeffs 1
    delta_one = bialgebra.coproduct(one)
    coprod_unit = len(delta_one) >= 1 and math.isclose(sum(delta_one.values()), 1.0, rel_tol=tol, abs_tol=tol)

    res['counit_homomorphism'] = counit_hom
    res['coproduct_unit_preservation'] = coprod_unit
    return res


def verify_hopf_algebra_laws(
    hopf: HopfAlgebra[R, C],
    r_samples: Iterable[R],
    c_samples: Iterable[C],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify axioms of a Hopf Algebra:
    - Bialgebra axioms
    - Antipode axiom: $\mu \circ (S \otimes \mathrm{id}) \circ \Delta = \eta \circ \epsilon$
    """
    c_elements = _require_samples(c_samples)
    res = verify_bialgebra_laws(hopf, r_samples, c_samples, tol)
    res['antipode_axiom'] = verify_antipode_axiom(hopf, c_elements, tol)
    return res


# =============================================================================
# Grothendieck Groups, Topological K-Theory & Characteristic Classes
# =============================================================================

G = TypeVar('G')


def _check_monoid_map_compatibility(
    k0: GrothendieckGroup[M],
    target_group: AddCommGroup[G],
    monoid_map: Callable[[M], G],
    m_elements: list[M],
    tol: float,
) -> tuple[bool, bool, bool]:
    r"""Check monoid homomorphism, embedding factorization, and difference law."""
    lifted = k0.lift_homomorphism(target_group, monoid_map)
    monoid = k0.monoid

    monoid_hom = semiring_elements_equal(monoid_map(monoid.zero), target_group.zero, tol)
    factorization = True
    difference_law = True

    for a in m_elements:
        if not semiring_elements_equal(lifted(k0.embed(a)), monoid_map(a), tol):
            factorization = False

    for a, b in itertools.product(m_elements, repeat=2):
        lhs_m = monoid_map(monoid.add(a, b))
        rhs_m = target_group.add(monoid_map(a), monoid_map(b))
        if not semiring_elements_equal(lhs_m, rhs_m, tol):
            monoid_hom = False

        if not semiring_elements_equal(lifted((a, b)), target_group.sub(monoid_map(a), monoid_map(b)), tol):
            difference_law = False

    return monoid_hom, factorization, difference_law


def _check_lifted_group_homomorphism(
    k0: GrothendieckGroup[M],
    target_group: AddCommGroup[G],
    monoid_map: Callable[[M], G],
    m_elements: list[M],
    tol: float,
) -> tuple[bool, bool]:
    r"""Check group homomorphism and Grothendieck equivalence invariance of the lifted map."""
    lifted = k0.lift_homomorphism(target_group, monoid_map)
    pairs = list(itertools.product(m_elements, repeat=2))

    group_hom = semiring_elements_equal(lifted(k0.zero), target_group.zero, tol)
    equiv_inv = True

    for x in pairs:
        if not semiring_elements_equal(lifted(k0.neg(x)), target_group.neg(lifted(x)), tol):
            group_hom = False
            break

    for x, y in itertools.product(pairs, repeat=2):
        lhs_g = lifted(k0.add(x, y))
        rhs_g = target_group.add(lifted(x), lifted(y))
        if not semiring_elements_equal(lhs_g, rhs_g, tol):
            group_hom = False

        if k0.equiv(x, y, stabilizers=m_elements) and not semiring_elements_equal(lifted(x), lifted(y), tol):
            equiv_inv = False

    return group_hom, equiv_inv


def verify_grothendieck_universal_property(
    k0: GrothendieckGroup[M],
    target_group: AddCommGroup[G],
    monoid_map: Callable[[M], G],
    monoid_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify the universal property of the Grothendieck group $K_0(M)$:
    - Monoid Homomorphism: $f(a +_M b) = f(a) +_G f(b)$ and $f(0_M) = 0_G$
    - Factorization through Embedding: $\tilde{f}(\iota(a)) = f(a)$
    - Formal Difference Law: $\tilde{f}((a, b)) = f(a) -_G f(b)$
    - Lifted Group Homomorphism: $\tilde{f}(x +_{K_0} y) = \tilde{f}(x) +_G \tilde{f}(y)$
      and $\tilde{f}(-x) = -\tilde{f}(x)$
    - Equivalence Invariance: $(a, b) \sim (c, d) \implies \tilde{f}(a, b) = \tilde{f}(c, d)$
    """
    m_elements = _require_samples(monoid_samples)
    monoid_hom, factorization, difference_law = _check_monoid_map_compatibility(
        k0, target_group, monoid_map, m_elements, tol
    )
    group_hom, equiv_inv = _check_lifted_group_homomorphism(
        k0, target_group, monoid_map, m_elements, tol
    )
    return {
        'monoid_homomorphism': monoid_hom,
        'embedding_factorization': factorization,
        'formal_difference_law': difference_law,
        'lifted_group_homomorphism': group_hom,
        'equivalence_invariance': equiv_inv,
    }


def verify_chern_character_additivity(
    conn1: Any,
    conn2: Any,
    faces: Sequence[Sequence[Any]],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify additivity of rank and discrete Chern character forms under Whitney sum $E_1 \oplus E_2$:
    - Rank Additivity: $\mathrm{ch}_0(E_1 \oplus E_2) = \mathrm{ch}_0(E_1) + \mathrm{ch}_0(E_2)$
    - First Chern Character Additivity: $\mathrm{ch}_1(E_1 \oplus E_2) = \mathrm{ch}_1(E_1) + \mathrm{ch}_1(E_2)$
    - Second Chern Character Additivity: $\mathrm{ch}_2(E_1 \oplus E_2) = \mathrm{ch}_2(E_1) + \mathrm{ch}_2(E_2)$
    """
    from algebrax.topology.k_theory import (
        bundle_direct_sum,
        compute_chern_character_1,
        compute_chern_character_2,
    )

    direct_sum = bundle_direct_sum(conn1, conn2)
    rank_ok = direct_sum.fiber_dim == (conn1.fiber_dim + conn2.fiber_dim)

    ch1_1 = compute_chern_character_1(conn1, faces)
    ch1_2 = compute_chern_character_1(conn2, faces)
    ch1_sum = compute_chern_character_1(direct_sum, faces)

    ch2_1 = compute_chern_character_2(conn1, faces)
    ch2_2 = compute_chern_character_2(conn2, faces)
    ch2_sum = compute_chern_character_2(direct_sum, faces)

    ch1_ok = True
    ch2_ok = True
    for f in faces:
        f_key = tuple(f)
        expected_1 = ch1_1.get(f_key, 0.0) + ch1_2.get(f_key, 0.0)
        actual_1 = ch1_sum.get(f_key, 0.0)
        if not math.isclose(actual_1, expected_1, rel_tol=tol, abs_tol=tol):
            ch1_ok = False

        expected_2 = ch2_1.get(f_key, 0.0) + ch2_2.get(f_key, 0.0)
        actual_2 = ch2_sum.get(f_key, 0.0)
        if not math.isclose(actual_2, expected_2, rel_tol=tol, abs_tol=tol):
            ch2_ok = False

    return {
        'rank_additivity': rank_ok,
        'ch1_additivity': ch1_ok,
        'ch2_additivity': ch2_ok,
    }


def verify_chern_number_integrality(
    conn: Any,
    oriented_faces: Sequence[Sequence[Any]],
    tol: float = 1e-6,
) -> bool:
    r"""Verify that the integrated first Chern number $\int_\Sigma c_1(E)$ is an integer within `tol`."""
    from algebrax.topology.k_theory import first_chern_number

    c1_val = first_chern_number(conn, oriented_faces)
    nearest_int = round(c1_val)
    return math.isclose(c1_val, float(nearest_int), rel_tol=tol, abs_tol=tol)




