"""Algebraic hierarchy, ring/field/module, ideal/quotient, non-associative,
normed, Hopf, and Grothendieck verifiers.
"""

from __future__ import annotations

import cmath
import itertools
import math
from collections.abc import Callable, Iterable, Sequence
from typing import Any, TypeVar

from algebrax.algebra import (
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
    Semiring,
    VectorSpace,
)
from algebrax.algebra._grothendieck import GrothendieckGroup
from algebrax.algebra._homomorphisms import RingHom
from algebrax.algebra._hopf import Bialgebra, Coalgebra, HopfAlgebra
from algebrax.algebra._ideals import GroebnerIdeal, Ideal
from algebrax.algebra._normed import InnerProductSpace, NormedSpace
from algebrax.algebra._polynomial import MultivariatePolynomialAlgebra, SparseMPoly, monomial_divides
from algebrax.algebra._quotient import CommQuotientRing, QuotientRing
from algebrax.verification._common import _float_equal, _require_samples, semiring_elements_equal

C = TypeVar('C')
Cod = TypeVar('Cod')
Dom = TypeVar('Dom')
G = TypeVar('G')
M = TypeVar('M')
R = TypeVar('R')
V = TypeVar('V')
X = TypeVar('X')

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
# Ring, Field, Module, and Algebra Law Verifiers
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


def _check_groebner_basis_structure(
    ring: MultivariatePolynomialAlgebra[V],
    basis: Sequence[SparseMPoly[V]],
    tol: float,
) -> tuple[bool, bool, bool]:
    """Verify monicity, reducedness, and Buchberger's S-polynomial criterion for a basis."""
    basis_monic = True
    lms: list[tuple[int, ...]] = []
    for g in basis:
        if not g:
            return False, False, False
        if not semiring_elements_equal(ring.lc(g), ring.field.one, tol):
            basis_monic = False
        lms.append(ring.lm(g))

    basis_reduced = True
    for i, g_i in enumerate(basis):
        for j, lm_j in enumerate(lms):
            if i == j:
                continue
            if any(monomial_divides(lm_j, mon) for mon in g_i):
                basis_reduced = False
                break
        if not basis_reduced:
            break

    buchberger = True
    for i in range(len(basis)):
        for j in range(i + 1, len(basis)):
            if len(ring.reduce_poly(ring.s_poly(basis[i], basis[j]), basis)) != 0:
                buchberger = False
                break
        if not buchberger:
            break

    return basis_monic, basis_reduced, buchberger


def verify_groebner_basis_laws(
    ring: MultivariatePolynomialAlgebra[V],
    ideal: GroebnerIdeal[V],
    samples: Iterable[SparseMPoly[V]] | None = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Test exact reduced Gröbner basis laws and `QuotientRing(ring, ideal)` coordinate ring axioms:
    - Generator Reduction: every original generator reduces to `{}` modulo `ideal.basis`.
    - Buchberger's Criterion: $\forall g_i, g_j \in G,\; \mathrm{reduce}(S(g_i, g_j)) == \{\}$.
    - Monicity: every $g \in G$ has leading coefficient $\operatorname{LC}(g) = \mathbf{1}_k$.
    - Reducedness: no term of any $g_i \in G$ is divisible by $\operatorname{LM}(g_j)$ for $j \ne i$.
    - Quotient CommRing Laws: $k[x_1, \dots, x_n] / I$ satisfies all `CommRing` and quotient projection laws.
    """
    basis = ideal.basis
    generators_reduced = all(len(ideal.reduce(g)) == 0 for g in ideal.generators)
    basis_monic, basis_reduced, buchberger = _check_groebner_basis_structure(ring, basis, tol)

    if samples is None:
        r_samples: list[SparseMPoly[V]] = [ring.zero, ring.one]
        r_samples.extend(ring.gen(i) for i in range(min(ring.n_vars, 3)))
        if ring.n_vars >= 2:
            r_samples.append(ring.add(ring.gen(0), ring.gen(1)))
    else:
        r_samples = _require_samples(samples)

    i_samples: list[SparseMPoly[V]] = list(basis[:3]) if basis else [ring.zero]
    quotient: CommQuotientRing[SparseMPoly[V]] = CommQuotientRing(ring, ideal)
    q_res = verify_quotient_ring_laws(quotient, r_samples, i_samples, tol=tol)
    comm_res = verify_comm_ring_laws(quotient, [quotient.project(r) for r in r_samples], tol=tol)

    return {
        'generators_reduced': generators_reduced,
        'buchberger_criterion': buchberger,
        'basis_monic': basis_monic,
        'basis_reduced': basis_reduced,
        'quotient_ring_laws': all(q_res.values()) and all(comm_res.values()),
    }


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
# Normed Spaces, Inner Products & Banach Contractions
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
# Coalgebra, Bialgebra & Hopf Algebra Axiom Verifiers
# =============================================================================

C = TypeVar('C')


def _carrier_basis(val: Any) -> Any:
    if isinstance(val, dict):
        return val
    return {val: 1.0}


def _to_scalar(val: Any) -> float | complex:
    if isinstance(val, complex):
        return val
    return float(val)


def _scalar_close(a: Any, b: Any, tol: float) -> bool:
    return cmath.isclose(complex(a), complex(b), rel_tol=tol, abs_tol=tol)


def verify_coassociativity(
    coalgebra: Coalgebra[Any, C],
    samples: Iterable[C],
    tol: float = 1e-9,
) -> bool:
    r"""Verify that $(\Delta \otimes \mathrm{id}) \circ \Delta(c) == (\mathrm{id} \otimes \Delta) \circ \Delta(c)$."""
    for c in samples:
        delta_c = coalgebra.coproduct(c)

        # 1. Left parenthesization: (Delta (x) id) Delta(c)
        tensor_left: dict[tuple[Any, Any, Any], float | complex] = {}
        for (u, v), alpha in delta_c.items():
            af = _to_scalar(alpha)
            u_basis = _carrier_basis(u)
            delta_u = coalgebra.coproduct(u_basis)
            for (x, y), beta in delta_u.items():
                key = (x, y, v)
                tensor_left[key] = tensor_left.get(key, 0.0) + af * _to_scalar(beta)

        # 2. Right parenthesization: (id (x) Delta) Delta(c)
        tensor_right: dict[tuple[Any, Any, Any], float | complex] = {}
        for (u, v), alpha in delta_c.items():
            af = _to_scalar(alpha)
            v_basis = _carrier_basis(v)
            delta_v = coalgebra.coproduct(v_basis)
            for (y, z), gamma in delta_v.items():
                key = (u, y, z)
                tensor_right[key] = tensor_right.get(key, 0.0) + af * _to_scalar(gamma)

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
            scaled_v = coalgebra.smul(_to_scalar(alpha) * _to_scalar(eps_u), v_basis)
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
            scaled_u = coalgebra.smul(_to_scalar(alpha) * _to_scalar(eps_v), u_basis)
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
            scaled = hopf.smul(_to_scalar(alpha), prod)
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
            scaled = hopf.smul(_to_scalar(alpha), prod)
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
    if not _scalar_close(eps_one, 1.0, tol):
        counit_hom = False

    for a, b in itertools.combinations(c_elements, 2):
        eps_ab = bialgebra.counit(bialgebra.mul(a, b))
        eps_a_eps_b = _to_scalar(bialgebra.counit(a)) * _to_scalar(bialgebra.counit(b))
        if not _scalar_close(eps_ab, eps_a_eps_b, tol):
            counit_hom = False
            break

    # Coproduct unit preservation: Delta(1) has sum of coeffs 1
    delta_one = bialgebra.coproduct(one)
    coprod_unit = len(delta_one) >= 1 and _scalar_close(sum(delta_one.values()), 1.0, tol)

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
