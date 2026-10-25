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
    'verify_band_laws',
    'verify_boolean_algebra_laws',
    'verify_bounded_lattice_laws',
    'verify_comm_group_laws',
    'verify_comm_monoid_laws',
    'verify_distributive_lattice_laws',
    'verify_group_action_laws',
    'verify_group_laws',
    'verify_join_semilattice_laws',
    'verify_lattice_laws',
    'verify_magma_laws',
    'verify_meet_semilattice_laws',
    'verify_monoid_laws',
    'verify_semigroup_laws',
    'verify_semiring_laws',
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
    Band,
    BooleanAlgebra,
    BoundedLattice,
    CommGroup,
    CommMonoid,
    DistributiveLattice,
    Group,
    GroupAction,
    JoinSemilattice,
    Lattice,
    Magma,
    MeetSemilattice,
    Monoid,
    Semigroup,
)

G = TypeVar('G')
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
