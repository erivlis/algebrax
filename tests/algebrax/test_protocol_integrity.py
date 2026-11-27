"""Dedicated protocol integrity, law witness, and algebraic soundness test suite.

Covers all 9 Acceptance Criteria for protocol soundness, law witnesses,
domain bug fixes, convention unification, and Layer-2/Layer-3 boundary integrity.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path
from types import MappingProxyType

import pytest

from algebrax.algebra import (
    Algebra,
    Bialgebra,
    CommGrothendieckRing,
    CommMonoidAlgebra,
    CommQuotientRing,
    CommRing,
    CommSemiring,
    GaloisField,
    GrothendieckRing,
    GroupHopfAlgebra,
    HasResiduals,
    HasStar,
    HopfAlgebra,
    InnerProductSpace,
    IntegerModuloIdeal,
    KleeneAlgebra,
    LawAnticommutative,
    LawAssociative,
    LawCommutative,
    LawLie,
    ModularField,
    MonoidAlgebra,
    MultivariatePolynomialAlgebra,
    NilpotentIdeal,
    NonAssocAlgebra,
    NormedSpace,
    PathAlgebra,
    PoissonAlgebra,
    PolynomialAlgebra,
    Quasigroup,
    QuotientAlgebra,
    QuotientRing,
    RelationActionAlgebra,
    Ring,
    Semiring,
    StandardField,
    StarSemiring,
    SubspaceLieIdeal,
)
from algebrax.algebra import _normed as normed_mod
from algebrax.category import Groupoid, HasMorInv
from algebrax.category import Quiver as CategoryQuiver
from algebrax.clifford import CliffordAlgebra
from algebrax.group import compose as perm_compose
from algebrax.group import cyclic_group, symmetric_group, symmetric_mul
from algebrax.lie import LieAlgebra, clifford_lie_algebra, se_n, so_n
from algebrax.rep import (
    ExplicitLieRep,
    FiniteQuiver,
    GroupRepresentation,
    LieRepresentation,
    dynkin_quiver,
    spin_representation,
)
from algebrax.semiring import (
    ArcticSemiring,
    BivariateVarianceSemiring,
    BooleanSemiring,
    BottleneckSemiring,
    DigitalSemiring,
    KCollapsedSemiring,
    LogSemiring,
    LukasiewiczSemiring,
    MinTimesSemiring,
    ReliabilitySemiring,
    StandardSemiring,
    StringSemiring,
    TropicalSemiring,
    ViterbiSemiring,
)
from algebrax.semiring._registry import DOMAIN_TAGS
from algebrax.topology import SimplicialPathGroupoid
from algebrax.verification import (
    verify_category_laws,
    verify_field_laws,
    verify_path_groupoid_laws,
)

# =============================================================================
# AC 1: Commutativity & Associativity Witness Soundness
# =============================================================================


class _NonCommSemiring(Semiring[int]):
    """Minimal non-commutative semiring marker (no LawCommutative)."""

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, a: int, b: int) -> int:
        return a + b

    def mul(self, a: int, b: int) -> int:
        return a * b


class _CommNatMonoid(LawCommutative):
    """Minimal additive commutative monoid witnessing LawCommutative."""

    @property
    def is_commutative(self) -> bool:
        return True

    @property
    def zero(self) -> int:
        return 0

    def add(self, a: int, b: int) -> int:
        return a + b


class _NonCommMonoid:
    """Minimal monoid without LawCommutative."""

    @property
    def one(self) -> str:
        return ''

    def mul(self, a: str, b: str) -> str:
        return a + b


def test_ac1_non_commutative_and_non_associative_witnesses() -> None:
    """AC 1: Non-commutative structures must NOT satisfy CommRing; QuotientAlgebra must NOT satisfy LawAssociative."""
    cl3 = CliffordAlgebra(3, 0, 0)
    assert isinstance(cl3, Ring)
    assert isinstance(cl3, Algebra)
    assert not isinstance(cl3, CommRing)

    q_a2 = dynkin_quiver('A', 2)
    path_alg = PathAlgebra(q_a2, StandardField(float))
    assert isinstance(path_alg, Ring)
    assert not isinstance(path_alg, CommRing)

    z_ring = StandardField(int)
    ideal_6 = IntegerModuloIdeal(6)
    q_ring = QuotientRing(z_ring, ideal_6)
    assert isinstance(q_ring, Ring)
    assert not isinstance(q_ring, CommRing)

    comm_q_ring = CommQuotientRing(z_ring, ideal_6)
    assert isinstance(comm_q_ring, Ring)
    assert isinstance(comm_q_ring, CommRing)
    with pytest.raises(TypeError, match='CommRing'):
        CommQuotientRing(cl3, ideal_6)  # type: ignore[arg-type]

    # QuotientAlgebra drops CommRing & LawAssociative, inherits NonAssocAlgebra
    g_se3 = se_n(3)
    trans_ideal = SubspaceLieIdeal({3, 4, 5})
    q_alg = QuotientAlgebra(g_se3, trans_ideal)
    assert isinstance(q_alg, NonAssocAlgebra)
    assert not isinstance(q_alg, LawAssociative)
    assert not isinstance(q_alg, CommRing)

    # MonoidAlgebra vs CommMonoidAlgebra
    ma = MonoidAlgebra(z_ring)
    assert isinstance(ma, Ring)
    assert not isinstance(ma, CommRing)

    cma = CommMonoidAlgebra(z_ring, monoid=_CommNatMonoid())
    assert isinstance(cma, CommRing)
    with pytest.raises(TypeError, match='CommRing'):
        CommMonoidAlgebra(cl3)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match='LawCommutative'):
        CommMonoidAlgebra(z_ring, monoid=_NonCommMonoid())
    with pytest.raises(ValueError, match='commutative monoid'):
        CommMonoidAlgebra(z_ring, commutative_monoid=False)

    # GrothendieckRing vs CommGrothendieckRing
    non_comm_s = _NonCommSemiring()
    assert not isinstance(non_comm_s, CommSemiring)
    gr = GrothendieckRing(non_comm_s)
    assert isinstance(gr, Ring)
    assert not isinstance(gr, CommRing)
    with pytest.raises(TypeError, match='CommSemiring'):
        CommGrothendieckRing(non_comm_s)  # type: ignore[arg-type]

    # PolynomialAlgebra vs MultivariatePolynomialAlgebra & conditional Poisson LawLie
    p_uni = PolynomialAlgebra(StandardSemiring(float))
    assert not isinstance(p_uni, CommRing)

    mp_even = MultivariatePolynomialAlgebra(StandardField(float), n_vars=2)
    assert isinstance(mp_even, CommRing)
    assert isinstance(mp_even, PoissonAlgebra)
    assert isinstance(mp_even, LawLie)

    mp_odd = MultivariatePolynomialAlgebra(StandardField(float), n_vars=3)
    assert isinstance(mp_odd, CommRing)
    assert not isinstance(mp_odd, LawLie)
    assert not isinstance(mp_odd, PoissonAlgebra)


# =============================================================================
# AC 2: Missing Protocol Witnesses & Generic Parameter Ordering
# =============================================================================


def test_ac2_lie_hopf_and_normed_protocol_integrity() -> None:
    """AC 2: LieAlgebra law witnesses, HopfAlgebra/Bialgebra LawAssociative, NormedSpace(R, V) order."""
    g = so_n(3)
    assert isinstance(g, LieAlgebra)
    assert isinstance(g, LawAnticommutative)
    assert isinstance(g, LawLie)
    assert g.is_anticommutative is True
    assert g.is_lie is True

    hopf = GroupHopfAlgebra(cyclic_group(3), StandardField(float))
    assert isinstance(hopf, Algebra)
    assert isinstance(hopf, Bialgebra)
    assert isinstance(hopf, HopfAlgebra)
    assert isinstance(hopf, LawAssociative)
    assert hopf.is_associative is True

    assert NormedSpace.__parameters__ == (normed_mod.R, normed_mod.V)
    assert InnerProductSpace.__parameters__ == (normed_mod.R, normed_mod.V)


# =============================================================================
# AC 3: GaloisField Non-Monic Reduction & Irreducibility Validation
# =============================================================================


def test_ac3_galois_field_non_monic_and_irreducibility() -> None:
    """AC 3: Non-monic irreducible 2x^2 + 2 over F_3 passes field laws; reducible polynomials raise ValueError."""
    # 2x^2 + 2 = 2(x^2 + 1) is irreducible over F_3 (no roots: 2, 1, 1 mod 3)
    gf9_nonmonic = GaloisField(3, [2, 0, 2])
    assert gf9_nonmonic.irreduc_poly == (1, 0, 1)
    samples: list[dict[int, int]] = []
    for c0 in range(3):
        for c1 in range(3):
            elem: dict[int, int] = {}
            if c0:
                elem[0] = c0
            if c1:
                elem[1] = c1
            samples.append(elem)
    laws = verify_field_laws(gf9_nonmonic, samples)
    assert all(laws.values()), f'Failed field laws on non-monic GF(3^2): {laws}'

    # 2x^2 + 1 over F_3 has root x = 1 (2 + 1 = 3 === 0 mod 3) -> reducible!
    with pytest.raises(ValueError, match='reducible'):
        GaloisField(3, [1, 0, 2])

    # x^2 + 1 = (x + 1)^2 over F_2 -> reducible!
    with pytest.raises(ValueError, match='reducible'):
        GaloisField(2, [1, 0, 1])

    # x^4 + x^2 + 1 = (x^2 + x + 1)^2 over F_2 -> degree-4 reducible without linear roots!
    with pytest.raises(ValueError, match='reducible'):
        GaloisField(2, [1, 0, 1, 0, 1])

    # Escape hatch: validate_irreducible=False allows constructing quotient ring explicitly
    quot_ring = GaloisField(2, [1, 0, 1], validate_irreducible=False)
    assert quot_ring.irreduc_poly == (1, 0, 1)

    # ModularField.nsum handles positive, zero, and negative multipliers
    f5 = ModularField(5)
    assert f5.nsum(3, 0) == 0
    assert f5.nsum(3, 4) == 2
    assert f5.nsum(3, -1) == 2


# =============================================================================
# AC 4: Clifford 1-Based Blade Bounds & Lie Algebra Indexing
# =============================================================================


def test_ac4_clifford_blade_bounds_and_lie_algebra() -> None:
    """AC 4: CliffordAlgebra(0, 1, 0) enforces 1-based bounds and computes e_1^2 = -1."""
    cl_010 = CliffordAlgebra(0, 1, 0)
    assert cl_010.mul({(1,): 1.0}, {(1,): 1.0}) == {(): -1.0}

    # Index 0 and index > p+q+r must raise ValueError (both paired and unpaired!)
    with pytest.raises(ValueError, match='out of range'):
        cl_010.mul({(0,): 1.0}, {(0,): 1.0})
    with pytest.raises(ValueError, match='out of range'):
        cl_010.mul({(0,): 1.0}, {(): 1.0})
    with pytest.raises(ValueError, match='out of range'):
        cl_010.mul({(2,): 1.0}, {(2,): 1.0})
    with pytest.raises(ValueError, match='out of range'):
        cl_010.mul({(): 1.0}, {(2,): 1.0})

    # clifford_lie_algebra uses 1-based bivector blades (1, 2), (1, 3), (2, 3)
    spin_so3 = clifford_lie_algebra(3, 0, 0)
    assert spin_so3.dim == 3
    assert isinstance(spin_so3, LieAlgebra)
    assert isinstance(spin_so3, LawLie)


# =============================================================================
# AC 5: IEEE 754 Zero-Annihilation & KCollapsedSemiring Edge Cases
# =============================================================================


def test_ac5_ieee754_zero_annihilation_and_kcollapsed() -> None:
    """AC 5: Zero annihilation never returns NaN; KCollapsedSemiring handles k=0 and rejects k<0."""
    mt = MinTimesSemiring()
    assert mt.mul(0.0, float('inf')) == float('inf')
    assert mt.mul(float('inf'), 0.0) == float('inf')

    trop = TropicalSemiring()
    assert trop.mul(float('inf'), float('-inf')) == float('inf')
    assert trop.mul(float('-inf'), float('inf')) == float('inf')
    assert not math.isnan(trop.mul(float('inf'), float('-inf')))

    arc = ArcticSemiring()
    assert arc.mul(float('-inf'), float('inf')) == float('-inf')
    assert arc.mul(float('inf'), float('-inf')) == float('-inf')
    assert not math.isnan(arc.mul(float('-inf'), float('inf')))

    log_s = LogSemiring()
    assert log_s.mul(float('-inf'), float('inf')) == float('-inf')
    assert log_s.mul(float('inf'), float('-inf')) == float('-inf')
    assert not math.isnan(log_s.mul(float('-inf'), float('inf')))

    k0 = KCollapsedSemiring(0)
    assert k0.zero == 0
    assert k0.one == 0
    assert k0.power(0, 0) == 0
    assert k0.star(0) == 0

    with pytest.raises(ValueError, match='non-negative'):
        KCollapsedSemiring(-1)


# =============================================================================
# AC 6: KleeneAlgebra vs StarSemiring Partition & HasStar Stub Removal
# =============================================================================


def test_ac6_star_and_kleene_partition() -> None:
    """AC 6: Stubless non-star semirings; 8 KleeneAlgebras; KCollapsed/Log StarSemirings; Standard neither."""
    for non_star in (DigitalSemiring(), StringSemiring(), BivariateVarianceSemiring()):
        assert not isinstance(non_star, HasStar)
        assert not hasattr(non_star, 'star')

    kleene_instances = [
        TropicalSemiring(),
        BooleanSemiring(),
        ArcticSemiring(),
        ViterbiSemiring(),
        ReliabilitySemiring(),
        BottleneckSemiring(),
        MinTimesSemiring(),
        LukasiewiczSemiring(),
    ]
    for ks in kleene_instances:
        assert isinstance(ks, KleeneAlgebra), f'{type(ks).__name__} must satisfy KleeneAlgebra'
        assert isinstance(ks, StarSemiring), f'{type(ks).__name__} must satisfy StarSemiring'

    for star_only in (KCollapsedSemiring(3), LogSemiring()):
        assert isinstance(star_only, StarSemiring), f'{type(star_only).__name__} must satisfy StarSemiring'
        assert not isinstance(star_only, KleeneAlgebra), f'{type(star_only).__name__} must NOT satisfy KleeneAlgebra'

    std = StandardSemiring(float)
    assert not isinstance(std, StarSemiring)
    assert not isinstance(std, KleeneAlgebra)


# =============================================================================
# AC 7: Diagrammatic Composition, HasMorInv.inv, and Quasigroup.rdiv
# =============================================================================


class _AsymmetricQuasigroup(Quasigroup[int]):
    """Non-commutative, asymmetric quasigroup over Z/5Z: a * b = (2a + b) mod 5.

    - ldiv(a, b) solves a * x = b  => 2a + x === b => x = (b - 2a) mod 5.
    - rdiv(a, b) solves x * b = a  => 2x + b === a => x = 3 * (a - b) mod 5.
    Notice rdiv(a, b) != rdiv(b, a), distinguishing x * b = a from x * a = b!
    """

    def mul(self, a: int, b: int) -> int:
        return (2 * a + b) % 5

    def ldiv(self, a: int, b: int) -> int:
        return (b - 2 * a) % 5

    def rdiv(self, a: int, b: int) -> int:
        return (3 * (a - b)) % 5


def test_ac7_diagrammatic_composition_inv_and_rdiv() -> None:
    """AC 7: SimplicialPathGroupoid diagrammatic compose + inv; S_3 compose == symmetric_mul; Quasigroup rdiv."""
    g = SimplicialPathGroupoid(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        triangles=[(0, 1, 2)],
    )
    assert isinstance(g, Groupoid)
    assert isinstance(g, HasMorInv)
    assert not hasattr(g, 'invert_path')

    # Diagrammatic composition: (0 -> 1) then (1 -> 2) gives (0 -> 1 -> 2)
    assert g.compose((0, 1), (1, 2)) == (0, 1, 2)
    assert g.inv((0, 1, 2)) == (2, 1, 0)

    cat_laws = verify_category_laws(g, objects=[0, 1, 2], morphisms=[(0, 1), (1, 2), (0, 2)])
    assert all(cat_laws.values()), f'Failed category laws: {cat_laws}'

    pg_laws = verify_path_groupoid_laws(g, sample_paths=[(0, 1), (1, 2), (0, 2)])
    assert all(pg_laws.values()), f'Failed path groupoid laws: {pg_laws}'

    # group.compose and group.symmetric_mul agree on ALL pairs in S_3 (including non-commuting pairs)
    s3 = symmetric_group(3)
    non_commuting_checked = 0
    for p in s3.elements:
        for q in s3.elements:
            p_map = dict(enumerate(p))
            q_map = dict(enumerate(q))
            comp_map = perm_compose(p_map, q_map)
            comp_tuple = tuple(comp_map.get(i, i) for i in range(3))
            assert symmetric_mul(p, q) == comp_tuple
            if symmetric_mul(p, q) != symmetric_mul(q, p):
                non_commuting_checked += 1
    assert non_commuting_checked > 0

    # Quasigroup composes HasResiduals and rdiv(a, b) solves x * b = a
    qg = _AsymmetricQuasigroup()
    assert isinstance(qg, Quasigroup)
    assert isinstance(qg, HasResiduals)
    for a in range(5):
        for b in range(5):
            assert qg.mul(qg.rdiv(a, b), b) == a
            assert qg.rdiv(qg.mul(a, b), b) == a
            assert qg.mul(a, qg.ldiv(a, b)) == b
            assert qg.ldiv(a, qg.mul(a, b)) == b
    # Confirm RelationActionAlgebra shares the same rdiv(a, b) signature
    assert hasattr(RelationActionAlgebra, 'rdiv')


# =============================================================================
# AC 8: FiniteQuiver Conformance, NilpotentIdeal, Flat Representation Protocols
# =============================================================================


def test_ac8_finite_quiver_nilpotent_ideal_and_flat_reps() -> None:
    """AC 8: FiniteQuiver conforms to category.Quiver; NilpotentIdeal reduces dicts & degrees; flat rep protocols."""
    fq = FiniteQuiver(
        vertices=('a', 'b'),
        edges=('e1',),
        source_map={'e1': 'a'},
        target_map={'e1': 'b'},
    )
    assert isinstance(fq, CategoryQuiver)
    assert fq.source('e1') == 'a'
    assert fq.target('e1') == 'b'
    assert isinstance(fq.source_map, MappingProxyType)
    assert isinstance(fq.target_map, MappingProxyType)
    with pytest.raises(TypeError):
        fq.source_map['e2'] = 'a'  # type: ignore[index]

    nil = NilpotentIdeal(2)
    assert nil.generator == {2: 1.0}
    assert nil.reduce({0: 1.0, 1: 2.0, 2: 3.0}) == {0: 1.0, 1: 2.0}
    assert nil.reduce_degree(2) is None
    assert nil.reduce_degree(1) == 1

    # Flat representation protocols (no GroupHom inheritance on GroupRepresentation)
    rep = spin_representation(1, form='su2')
    assert isinstance(rep, ExplicitLieRep)
    assert isinstance(rep, LieRepresentation)
    assert rep({0: 1.0}) == rep.generator_matrix(0)
    with pytest.raises(TypeError, match='generator_matrix'):
        rep(0)  # type: ignore[arg-type]

    assert 'GroupHom' not in [b.__name__ for b in GroupRepresentation.__mro__]
    assert 'LieAlgebraHom' not in [b.__name__ for b in LieRepresentation.__mro__]


# =============================================================================
# AC 9: Layer-2 Import Hygiene & Centralized Registry Coverage
# =============================================================================


def test_ac9_zero_top_level_upward_imports_and_registry_completeness() -> None:
    """AC 9: Zero top-level upward imports from src/algebrax/algebra/ into Layer-3 modules; DOMAIN_TAGS complete."""
    algebra_dir = Path(__file__).resolve().parents[2] / 'src' / 'algebrax' / 'algebra'
    forbidden_prefixes = (
        'algebrax.semiring',
        'algebrax.matrix',
        'algebrax.rep',
        'algebrax.clifford',
        'algebrax.display',
    )

    violations: list[str] = []
    for py_file in sorted(algebra_dir.glob('*.py')):
        tree = ast.parse(py_file.read_text(encoding='utf-8'), filename=str(py_file))
        for node in tree.body:
            # Inspect top-level statements and top-level if blocks (including TYPE_CHECKING)
            stmts = [node]
            if isinstance(node, ast.If):
                stmts.extend(node.body)
                stmts.extend(node.orelse)
            for stmt in stmts:
                if isinstance(stmt, ast.Import):
                    for alias in stmt.names:
                        if alias.name.startswith(forbidden_prefixes):
                            violations.append(f'{py_file.name}:{stmt.lineno}: import {alias.name}')
                elif isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.module.startswith(forbidden_prefixes):
                    violations.append(f'{py_file.name}:{stmt.lineno}: from {stmt.module} import ...')

    assert not violations, f'Found forbidden top-level Layer-2 -> Layer-3 imports: {violations}'

    # Registry completeness: DOMAIN_TAGS covers 100% of Semiring.catalog() keys
    catalog_keys = set(Semiring.catalog().keys())
    assert catalog_keys == set(DOMAIN_TAGS.keys())
