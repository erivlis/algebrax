"""
Tests for the Granular Pure-Algebraic Hierarchy (EP-0190).

Tests Magmas, Semigroups, Bands, Monoids, Groups, Additive Duals,
Lattices, Boolean Algebras, Helpers, and the Granular Verification Engine.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from algebrax.algebra import (
    AbelianGroup,
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
    OpCommMonoid,
    OpMagma,
    OpMonoid,
    OpSemigroup,
    Quasigroup,
    Semigroup,
    fold_add,
    fold_mul,
    fold_op,
    nsum,
    power,
    zpow,
    zsmul,
)
from algebrax.semiring import StandardSemiring
from algebrax.verification import (
    verify_add_comm_group_laws,
    verify_add_comm_monoid_laws,
    verify_add_group_laws,
    verify_add_magma_laws,
    verify_add_monoid_laws,
    verify_add_semigroup_laws,
    verify_band_laws,
    verify_boolean_algebra_laws,
    verify_bounded_lattice_laws,
    verify_comm_group_laws,
    verify_comm_monoid_laws,
    verify_distributive_lattice_laws,
    verify_group_action_laws,
    verify_group_laws,
    verify_join_semilattice_laws,
    verify_lattice_laws,
    verify_magma_laws,
    verify_meet_semilattice_laws,
    verify_monoid_laws,
    verify_semigroup_laws,
)

# =============================================================================
# 1. Multiplicative Hierarchy: Magmas, Semigroups, Bands, Monoids, Groups
# =============================================================================


class StringConcatSemigroup:
    """String concatenation: associative, non-commutative, no general inverse."""

    def mul(self, a: str, b: str) -> str:
        return a + b


class StringConcatMonoid(StringConcatSemigroup):
    """String concatenation with empty string as identity."""

    @property
    def one(self) -> str:
        return ''


class SubtractionMagma:
    """Subtraction magma (a - b): non-associative, non-commutative."""

    def mul(self, a: int, b: int) -> int:
        return a - b


class MinBand:
    """Idempotent band under minimum: min(a, a) == a."""

    def mul(self, a: int, b: int) -> int:
        return min(a, b)


class ModularSubtractionQuasigroup:
    """Quasigroup over Z/5Z with operation a - b (mod 5)."""

    def mul(self, a: int, b: int) -> int:
        return (a - b) % 5

    def ldiv(self, a: int, b: int) -> int:
        # a - x = b (mod 5) => x = a - b (mod 5)
        return (a - b) % 5

    def rdiv(self, a: int, b: int) -> int:
        # y - a = b (mod 5) => y = a + b (mod 5)
        return (a + b) % 5


class NonZeroFloatMultiplicativeGroup:
    """Multiplicative abelian group of non-zero floats (R*, *, 1, 1/x)."""

    @property
    def one(self) -> float:
        return 1.0

    def mul(self, a: float, b: float) -> float:
        return a * b

    def inv(self, a: float) -> float:
        if a == 0.0:
            raise ValueError('Zero has no multiplicative inverse.')
        return 1.0 / a

    def div(self, a: float, b: float) -> float:
        return a / b


class MinimalGroup(Group[float]):
    """Group relying on protocol default div implementation."""

    @property
    def one(self) -> float:
        return 1.0

    def mul(self, a: float, b: float) -> float:
        return a * b

    def inv(self, a: float) -> float:
        return 1.0 / a


class MinimalAddGroup(AddGroup[int]):
    """AddGroup relying on protocol default sub implementation."""

    @property
    def zero(self) -> int:
        return 0

    def add(self, a: int, b: int) -> int:
        return a + b

    def neg(self, a: int) -> int:
        return -a


class PermutationGroup:
    """
    Symmetric group S_3 represented as unboxed dictionaries {int: int}.
    Zero boxing: carrier elements are raw dicts.
    """

    @property
    def one(self) -> dict[int, int]:
        return {0: 0, 1: 1, 2: 2}

    def mul(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        # Composition (a o b)(x) = a(b(x))
        return {k: a[v] for k, v in b.items()}

    def inv(self, a: dict[int, int]) -> dict[int, int]:
        return {v: k for k, v in a.items()}

    def div(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        return self.mul(a, self.inv(b))


def test_multiplicative_protocols_runtime_checkable():
    """Verify structural subtyping and protocol checks for multiplicative branch."""
    magma = SubtractionMagma()
    assert isinstance(magma, Magma)

    sg = StringConcatSemigroup()
    assert isinstance(sg, Magma)
    assert isinstance(sg, Semigroup)

    band = MinBand()
    assert isinstance(band, Magma)
    assert isinstance(band, Semigroup)
    assert isinstance(band, Band)

    qg = ModularSubtractionQuasigroup()
    assert isinstance(qg, Magma)
    assert isinstance(qg, Quasigroup)

    mon = StringConcatMonoid()
    assert isinstance(mon, Magma)
    assert isinstance(mon, Semigroup)
    assert isinstance(mon, Monoid)
    assert isinstance(mon, CommMonoid)  # Structurally identical signatures

    grp = NonZeroFloatMultiplicativeGroup()
    assert isinstance(grp, Magma)
    assert isinstance(grp, Semigroup)
    assert isinstance(grp, Monoid)
    assert isinstance(grp, Group)
    assert isinstance(grp, CommGroup)
    assert isinstance(grp, AbelianGroup)

    perm_grp = PermutationGroup()
    assert isinstance(perm_grp, Group)

    min_grp = MinimalGroup()
    assert min_grp.div(6.0, 2.0) == 3.0

    min_add = MinimalAddGroup()
    assert min_add.sub(10, 3) == 7


def test_multiplicative_verifiers():
    """Verify law verification functions on multiplicative structures."""
    # Subtraction magma: closed, but fails associativity
    sub = SubtractionMagma()
    assert verify_magma_laws(sub, [1, 2, 3]) == {'mul_closure': True}
    res_sub_sg = verify_semigroup_laws(sub, [1, 2, 3])
    assert res_sub_sg['mul_closure'] is True
    assert res_sub_sg['mul_associativity'] is False

    # String semigroup: associative, but not idempotent
    sg = StringConcatSemigroup()
    assert verify_semigroup_laws(sg, ['a', 'b', 'c']) == {'mul_closure': True, 'mul_associativity': True}
    res_sg_band = verify_band_laws(sg, ['a', 'b', 'c'])
    assert res_sg_band['mul_idempotence'] is False

    # Min band: associative and idempotent
    band = MinBand()
    assert verify_band_laws(band, [1, 5, 10, 20]) == {
        'mul_closure': True,
        'mul_associativity': True,
        'mul_idempotence': True,
    }

    # String monoid: non-commutative
    mon = StringConcatMonoid()
    res_mon = verify_monoid_laws(mon, ['x', 'y', 'z'])
    assert res_mon['left_identity'] is True
    assert res_mon['right_identity'] is True
    res_comm_mon = verify_comm_monoid_laws(mon, ['x', 'y', 'z'])
    assert res_comm_mon['mul_commutativity'] is False

    # Float multiplicative group: abelian group
    grp = NonZeroFloatMultiplicativeGroup()
    res_grp = verify_comm_group_laws(grp, [1.0, 2.0, 0.5, 4.0])
    for k, v in res_grp.items():
        assert v is True, f'Law {k} failed'

    # S_3 Permutation group: non-abelian group
    perm_grp = PermutationGroup()
    e = {0: 0, 1: 1, 2: 2}
    r = {0: 1, 1: 2, 2: 0}  # (0 1 2)
    s = {0: 1, 1: 0, 2: 2}  # (0 1)
    res_perm = verify_group_laws(perm_grp, [e, r, s])
    assert res_perm['left_inverse'] is True
    assert res_perm['right_inverse'] is True
    assert res_perm['quotient_consistency'] is True
    # Verify non-commutativity is caught
    res_perm_comm = verify_comm_group_laws(perm_grp, [e, r, s])
    assert res_perm_comm['mul_commutativity'] is False


# =============================================================================
# 2. Additive Dual Hierarchy & Sparse Dictionary Vector Carrier
# =============================================================================


class SparseVectorGroup:
    """
    Additive abelian group of sparse vectors over R.
    Core Architectural Principle: carrier elements are unboxed raw dict[str, float].
    Zero is the empty dictionary {}.
    """

    @property
    def zero(self) -> dict[str, float]:
        return {}

    def add(self, u: dict[str, float], v: dict[str, float]) -> dict[str, float]:
        keys = set(u.keys()) | set(v.keys())
        res: dict[str, float] = {}
        for k in keys:
            val = u.get(k, 0.0) + v.get(k, 0.0)
            if not math.isclose(val, 0.0, abs_tol=1e-12):
                res[k] = val
        return res

    def neg(self, u: dict[str, float]) -> dict[str, float]:
        return {k: -val for k, val in u.items() if not math.isclose(val, 0.0, abs_tol=1e-12)}

    def sub(self, u: dict[str, float], v: dict[str, float]) -> dict[str, float]:
        return self.add(u, self.neg(v))


def test_sparse_vector_additive_group():
    """Verify raw sparse dict[str, float] acts as a first-class AddCommGroup."""
    svg = SparseVectorGroup()
    assert isinstance(svg, AddMagma)
    assert isinstance(svg, AddSemigroup)
    assert isinstance(svg, AddMonoid)
    assert isinstance(svg, AddCommMonoid)
    assert isinstance(svg, AddGroup)
    assert isinstance(svg, AddCommGroup)

    v0: dict[str, float] = {}
    v1: dict[str, float] = {'x': 1.0, 'y': 2.0}
    v2: dict[str, float] = {'y': -2.0, 'z': 3.5}
    v3: dict[str, float] = {'x': -0.5, 'w': 4.0}

    samples = [v0, v1, v2, v3]

    res = verify_add_comm_group_laws(svg, samples)
    for law, passed in res.items():
        assert passed is True, f'Sparse vector failed additive law {law}'

    # Check subtraction consistency
    assert svg.sub(v1, v1) == {}
    diff = svg.sub(v1, v2)
    assert diff == {'x': 1.0, 'y': 4.0, 'z': -3.5}


# =============================================================================
# 3. Domain-Agnostic Single-Operation Protocols
# =============================================================================


class XorMonoid:
    """Domain-agnostic commutative monoid: bitwise XOR with 0 identity."""

    @property
    def identity(self) -> int:
        return 0

    def op(self, a: int, b: int) -> int:
        return a ^ b


def test_domain_agnostic_protocols():
    """Verify OpMagma, OpSemigroup, OpMonoid, OpCommMonoid."""
    xor_mon = XorMonoid()
    assert isinstance(xor_mon, OpMagma)
    assert isinstance(xor_mon, OpSemigroup)
    assert isinstance(xor_mon, OpMonoid)
    assert isinstance(xor_mon, OpCommMonoid)

    # Test fold_op
    assert fold_op(xor_mon, []) == 0
    assert fold_op(xor_mon, [1, 2, 4]) == 7
    assert fold_op(xor_mon, [1, 2, 1]) == 2


# =============================================================================
# 4. Group Action Protocols
# =============================================================================


class PermutationActionOnIndex:
    """Permutation group action on coordinate index x in {0, 1, 2}."""

    def gact(self, g: dict[int, int], x: int) -> int:
        return g.get(x, x)


class PermutationActionOnVector:
    """Permutation group action on sparse dictionary vector."""

    def gact(self, g: dict[int, int], v: dict[int, float]) -> dict[int, float]:
        # (g . v)[i] = v[g^{-1}(i)] => or permute keys
        return {g[k]: val for k, val in v.items()}


def test_group_action():
    """Verify GroupAction protocol and law verification."""
    perm_grp = PermutationGroup()
    action = PermutationActionOnIndex()
    assert isinstance(action, GroupAction)

    e = {0: 0, 1: 1, 2: 2}
    r = {0: 1, 1: 2, 2: 0}
    s = {0: 1, 1: 0, 2: 2}

    g_samples = [e, r, s]
    x_samples = [0, 1, 2]

    res = verify_group_action_laws(action, perm_grp, g_samples, x_samples)
    assert res == {'action_identity': True, 'action_compatibility': True}


# =============================================================================
# 5. Order & Lattice Hierarchy: Semilattices, Lattices, Boolean Algebras
# =============================================================================


class SetSubsetBooleanAlgebra:
    """
    Power set Boolean algebra over a fixed universe U = frozenset({1, 2, 3}).
    Unboxed carrier is frozenset[int].
    """

    def __init__(self, universe: frozenset[int]) -> None:
        self.universe = universe

    @property
    def bot(self) -> frozenset[int]:
        return frozenset()

    @property
    def top(self) -> frozenset[int]:
        return self.universe

    def join(self, a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
        return a | b

    def meet(self, a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
        return a & b

    def complement(self, a: frozenset[int]) -> frozenset[int]:
        return self.universe - a


class DivisorLattice:
    """
    Distributive bounded lattice of divisors of 60.
    join = lcm, meet = gcd, bot = 1, top = 60.
    """

    @property
    def bot(self) -> int:
        return 1

    @property
    def top(self) -> int:
        return 60

    def join(self, a: int, b: int) -> int:
        return (a * b) // math.gcd(a, b)

    def meet(self, a: int, b: int) -> int:
        return math.gcd(a, b)


def test_lattice_hierarchy_protocols():
    """Verify structural subtyping of lattice hierarchy."""
    u = frozenset({1, 2, 3})
    ba = SetSubsetBooleanAlgebra(u)
    assert isinstance(ba, JoinSemilattice)
    assert isinstance(ba, MeetSemilattice)
    assert isinstance(ba, Lattice)
    assert isinstance(ba, BoundedLattice)
    assert isinstance(ba, DistributiveLattice)
    assert isinstance(ba, BooleanAlgebra)

    divs = DivisorLattice()
    assert isinstance(divs, JoinSemilattice)
    assert isinstance(divs, MeetSemilattice)
    assert isinstance(divs, Lattice)
    assert isinstance(divs, BoundedLattice)
    assert isinstance(divs, DistributiveLattice)


def test_lattice_verifiers():
    """Verify law verification functions on lattice structures."""
    u = frozenset({1, 2, 3})
    ba = SetSubsetBooleanAlgebra(u)
    samples = [
        frozenset(),
        frozenset({1}),
        frozenset({2, 3}),
        frozenset({1, 2, 3}),
    ]

    res_js = verify_join_semilattice_laws(ba, samples)
    assert all(res_js.values())

    res_ms = verify_meet_semilattice_laws(ba, samples)
    assert all(res_ms.values())

    res_lat = verify_lattice_laws(ba, samples)
    assert all(res_lat.values())

    res_ba = verify_boolean_algebra_laws(ba, samples)
    for k, v in res_ba.items():
        assert v is True, f'Boolean algebra failed law {k}'

    divs = DivisorLattice()
    div_samples = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
    res_divs = verify_distributive_lattice_laws(divs, div_samples)
    assert all(res_divs.values())


# =============================================================================
# 6. Helpers: power, zpow, nsum, zsmul, fold_*
# =============================================================================


def test_helpers():
    """Test polymorphic exponentiation, scalar multiples, and folds."""
    # power on StringConcatMonoid
    smon = StringConcatMonoid()
    assert power(smon, 'ab', 0) == ''
    assert power(smon, 'ab', 1) == 'ab'
    assert power(smon, 'ab', 3) == 'ababab'
    with pytest.raises(ValueError, match='non-negative'):
        power(smon, 'ab', -1)

    # power on OpMonoid
    xmon = XorMonoid()
    assert power(xmon, 5, 0) == 0
    assert power(xmon, 5, 1) == 5
    assert power(xmon, 5, 2) == 0  # 5 ^ 5 = 0
    assert power(xmon, 5, 3) == 5

    # zpow on NonZeroFloatMultiplicativeGroup
    grp = NonZeroFloatMultiplicativeGroup()
    assert zpow(grp, 2.0, 0) == 1.0
    assert zpow(grp, 2.0, 3) == 8.0
    assert zpow(grp, 2.0, -3) == 0.125

    # nsum and zsmul on SparseVectorGroup
    svg = SparseVectorGroup()
    v = {'x': 2.0, 'y': -1.0}
    assert nsum(svg, v, 0) == {}
    assert nsum(svg, v, 1) == {'x': 2.0, 'y': -1.0}
    assert nsum(svg, v, 4) == {'x': 8.0, 'y': -4.0}
    with pytest.raises(ValueError, match='non-negative'):
        nsum(svg, v, -2)

    assert zsmul(svg, v, 0) == {}
    assert zsmul(svg, v, 3) == {'x': 6.0, 'y': -3.0}
    assert zsmul(svg, v, -3) == {'x': -6.0, 'y': 3.0}

    # folds
    assert fold_mul(grp, []) == 1.0
    assert fold_mul(grp, [2.0, 3.0, 4.0]) == 24.0

    assert fold_add(svg, []) == {}
    assert fold_add(svg, [{'x': 1.0}, {'y': 2.0}, {'x': 3.0}]) == {'x': 4.0, 'y': 2.0}


# =============================================================================
# 7. Verification Invariant (Popper Guard) & Falsification
# =============================================================================


def test_popper_minimum_witness_guard():
    """Verify that fewer than 3 samples raises ValueError to prevent trivial passes."""
    sub = SubtractionMagma()
    with pytest.raises(ValueError, match='at least 3 sample elements'):
        verify_magma_laws(sub, [1, 2])

    with pytest.raises(ValueError, match='at least 3 sample elements'):
        verify_semigroup_laws(sub, [])


def test_falsification_detects_broken_laws():
    """Verify that broken algebraic structures are systematically falsified."""

    class BrokenInverseGroup(NonZeroFloatMultiplicativeGroup):
        def inv(self, a: float) -> float:
            return a  # Broken inverse: inv(a) != 1/a

    bg = BrokenInverseGroup()
    res = verify_group_laws(bg, [2.0, 3.0, 4.0])
    assert res['left_inverse'] is False
    assert res['right_inverse'] is False

    class BrokenAbsorptionLattice(SetSubsetBooleanAlgebra):
        def meet(self, a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
            return a | b  # Broken meet: causes absorption to fail

    u = frozenset({1, 2, 3})
    blat = BrokenAbsorptionLattice(u)
    res_lat = verify_lattice_laws(blat, [frozenset(), frozenset({1}), frozenset({2})])
    assert res_lat['absorption_meet_join'] is False

    class BrokenComplementBooleanAlgebra(SetSubsetBooleanAlgebra):
        def complement(self, a: frozenset[int]) -> frozenset[int]:
            return a  # Broken complement: a | a != top

    bba = BrokenComplementBooleanAlgebra(u)
    res_ba = verify_boolean_algebra_laws(bba, [frozenset(), frozenset({1}), frozenset({2})])
    assert res_ba['complement_join'] is False


# =============================================================================
# 8. AMDS Semiring Compatibility (Zero Adapter Boxing)
# =============================================================================


def test_semiring_fulfills_additive_and_multiplicative_monoids():
    """
    Verify that StandardSemiring[float]() fulfills AddCommMonoid and Monoid
    purely structurally without any wrapping or boxing.
    """
    s = StandardSemiring[float]()
    assert isinstance(s, AddMagma)
    assert isinstance(s, AddSemigroup)
    assert isinstance(s, AddMonoid)
    assert isinstance(s, AddCommMonoid)

    assert isinstance(s, Magma)
    assert isinstance(s, Semigroup)
    assert isinstance(s, Monoid)
    assert isinstance(s, CommMonoid)

    # Law verifiers should pass on semiring operators
    samples = [0.0, 1.0, 2.5, -3.0, 0.5]
    assert verify_add_comm_monoid_laws(s, samples)['add_associativity'] is True
    assert verify_add_comm_monoid_laws(s, samples)['add_commutativity'] is True
    assert verify_comm_monoid_laws(s, samples)['mul_associativity'] is True
    assert verify_comm_monoid_laws(s, samples)['mul_commutativity'] is True
