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

__all__ = [
    'get_semiring_samples',
    'semiring_elements_equal',
    'verify_add_comm_group_laws',
    'verify_add_comm_monoid_laws',
    'verify_add_group_laws',
    'verify_add_magma_laws',
    'verify_add_monoid_laws',
    'verify_add_semigroup_laws',
    'verify_algebra_laws',
    'verify_band_laws',
    'verify_boolean_algebra_laws',
    'verify_bounded_lattice_laws',
    'verify_category_laws',
    'verify_coboundary_nilpotency',
    'verify_comm_group_laws',
    'verify_comm_monoid_laws',
    'verify_comm_ring_laws',
    'verify_distributive_lattice_laws',
    'verify_division_ring_laws',
    'verify_field_laws',
    'verify_functor_laws',
    'verify_group_action_laws',
    'verify_group_laws',
    'verify_ideal_absorption_laws',
    'verify_join_semilattice_laws',
    'verify_lattice_laws',
    'verify_lie_algebra_laws',
    'verify_magma_laws',
    'verify_meet_semilattice_laws',
    'verify_module_laws',
    'verify_monoid_laws',
    'verify_non_assoc_algebra_laws',
    'verify_non_assoc_ring_laws',
    'verify_quotient_ring_laws',
    'verify_ring_homomorphism_laws',
    'verify_ring_laws',
    'verify_semigroup_laws',
    'verify_semimodule_laws',
    'verify_semiring_laws',
    'verify_sheaf_functoriality',
    'verify_sheaf_laplacian_properties',
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
    tol: float = 1e-7,
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
    tol: float = 1e-7,
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


def verify_semimodule_laws(
    smodule: Semimodule[R, M],
    semiring: AddCommMonoid[R],
    r_samples: Iterable[R],
    m_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Semimodule laws: additive commutative monoid on M plus scalar distributivity."""
    r_elements = _require_samples(r_samples)
    m_elements = _require_samples(m_samples)

    res = verify_add_comm_monoid_laws(smodule, m_elements, tol)
    smul = smodule.smul
    add_m = smodule.add
    m_zero = smodule.zero

    left_dist = True
    for r in r_elements:
        for m1, m2 in itertools.combinations(m_elements, 2):
            lhs = smul(r, add_m(m1, m2))
            rhs = add_m(smul(r, m1), smul(r, m2))
            if not semiring_elements_equal(lhs, rhs, tol):
                left_dist = False
                break
        if not left_dist:
            break

    annihil_m = True
    for r in r_elements:
        if not semiring_elements_equal(smul(r, m_zero), m_zero, tol):
            annihil_m = False
            break

    res['scalar_left_distributivity'] = left_dist
    res['scalar_module_zero_annihilation'] = annihil_m
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
    smul = module.smul
    add_m = module.add
    m_zero = module.zero
    r_one = ring.one
    r_zero = ring.zero
    add_r = ring.add
    mul_r = ring.mul

    left_dist = True
    for r in r_elements:
        for m1, m2 in itertools.combinations(m_elements, 2):
            lhs = smul(r, add_m(m1, m2))
            rhs = add_m(smul(r, m1), smul(r, m2))
            if not semiring_elements_equal(lhs, rhs, tol):
                left_dist = False
                break
        if not left_dist:
            break

    right_dist = True
    for r1, r2 in itertools.combinations(r_elements, 2):
        for m in m_elements:
            lhs = smul(add_r(r1, r2), m)
            rhs = add_m(smul(r1, m), smul(r2, m))
            if not semiring_elements_equal(lhs, rhs, tol):
                right_dist = False
                break
        if not right_dist:
            break

    assoc = True
    for r1, r2 in itertools.product(r_elements, repeat=2):
        for m in m_elements:
            lhs = smul(mul_r(r1, r2), m)
            rhs = smul(r1, smul(r2, m))
            if not semiring_elements_equal(lhs, rhs, tol):
                assoc = False
                break
        if not assoc:
            break

    id_scalar = True
    for m in m_elements:
        if not semiring_elements_equal(smul(r_one, m), m, tol):
            id_scalar = False
            break

    annihil = True
    for m in m_elements:
        if not semiring_elements_equal(smul(r_zero, m), m_zero, tol):
            annihil = False
            break
    for r in r_elements:
        if not semiring_elements_equal(smul(r, m_zero), m_zero, tol):
            annihil = False
            break

    res['scalar_left_distributivity'] = left_dist
    res['scalar_right_distributivity'] = right_dist
    res['scalar_associativity'] = assoc
    res['scalar_identity'] = id_scalar
    res['scalar_annihilation'] = annihil
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

from collections.abc import Callable  # noqa: E402

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
