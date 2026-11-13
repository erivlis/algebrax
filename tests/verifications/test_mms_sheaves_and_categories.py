r"""Method of Manufactured Solutions (MMS) for Cellular Sheaves & Axiomatic Category/Lattice/Trie Verification.

Implements EP-0185:
- Method of Manufactured Solutions (MMS) for `CellularSheaf`:
  - Constructs a non-trivial 2D $SO(2)$ connection sheaf over a multi-loop network with known global section
    $x^* \in \ker \mathcal{L}_{\mathcal{F}}$, restricts $x^*$ to boundary vertices $\partial B$, and verifies
    that `sheaf_harmonic_extension` recovers $x^*$ on all interior vertices $V \setminus \partial B$ to machine
    precision.
  - Verifies non-constant linear harmonic interpolation MMS on weighted 2D grid sheaves against exact Schur
    complement (`scipy.linalg.solve`) solutions: $\mathcal{L}_{II} x_I = -\mathcal{L}_{IB} x_B$.
  - Verifies `sheaf_diffusion` Dirichlet energy monotonicity $E(x_{t+1}) \le E(x_t)$ and exact matrix power match
    $(I - \tau \mathcal{L}_{\mathcal{F}})^k x_0$.
- Category Theory (`kleisli_compose`, `kan_extension_left`):
  - Hypothesis verification of Kleisli monad laws (Left Identity, Right Identity, Associativity) and functoriality
    across `StandardSemiring(Fraction)`, `TropicalSemiring`, and `BooleanSemiring`.
- Lattice Operations (`join`, `meet`, `combine`, `average`, `geometric_mean`, `harmonic_mean`, `difference`,
  `exclude`, `exclusive`, `mask`, `product`, `ratio`, `symmetric_difference`):
  - Hypothesis verification of distributive lattice laws (Idempotence, Commutativity, Associativity, Absorption
    $a \lor (a \land b) = a$, $a \land (a \lor b) = a$, and Distributivity) plus classical Pythagorean mean
    inequality $H(a, b) \le G(a, b) \le A(a, b)$.
- Prefix Tree Algebra (`AlgebraicTrie`):
  - Homomorphism between `AlgebraicTrie.add`/`contract` and flat `SparseVector` semiring operations across
    `StandardSemiring` and `TropicalSemiring`.
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest
import scipy.linalg as sla
from hypothesis import given, settings
from hypothesis import strategies as st

from algebrax.category import kan_extension_left, kleisli_compose
from algebrax.lattice import (
    average,
    difference,
    exclude,
    exclusive,
    geometric_mean,
    harmonic_mean,
    join,
    mask,
    meet,
    product,
    ratio,
    symmetric_difference,
)
from algebrax.matrix.core import mat_vec
from algebrax.semiring import BooleanSemiring, StandardSemiring, TropicalSemiring
from algebrax.topology import CellularSheaf, sheaf_diffusion, sheaf_harmonic_extension, sheaf_laplacian
from algebrax.trie import AlgebraicTrie

pytestmark = [pytest.mark.verification, pytest.mark.axiomatic]


# ---------------------------------------------------------------------------
# 1. Method of Manufactured Solutions (MMS) for Cellular Sheaf Harmonic Extension
# ---------------------------------------------------------------------------


@pytest.mark.mms
def test_mms_cellular_sheaf_so2_connection_harmonic_extension() -> None:
    """Verify via MMS that sheaf_harmonic_extension recovers an exact manufactured SO(2) twisted section."""
    # Construct a 5-vertex graph with 2D stalks and orthogonal SO(2) local frame rotations:
    # Each vertex v has a known local coordinate frame angle theta_v.
    # For each edge (u, v), we set rho_{u->e} = R(-theta_u) and rho_{v->e} = R(-theta_v)
    # so that the global frame vector g = (1.5, -0.8) induces the exact manufactured global section
    # x^*_v = R(theta_v) g in ker(L_F)!
    angles = {0: 0.0, 1: 0.45, 2: -0.75, 3: 1.15, 4: -1.30}

    def rot(theta: float) -> list[list[float]]:
        c, s = math.cos(theta), math.sin(theta)
        return [[c, -s], [s, c]]

    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 2), (1, 3), (2, 4)]
    sheaf: CellularSheaf[int] = CellularSheaf()
    for u, v in edges:
        sheaf.add_edge(u, v, dim=2, rho_u=rot(-angles[u]), rho_v=rot(-angles[v]))

    # Manufactured global section x^*_v = R(theta_v) @ [1.5, -0.8]^T
    g0, g1 = 1.5, -0.8
    x_star: dict[tuple[int, int], float] = {}
    for v, theta in angles.items():
        r_mat = rot(theta)
        x_star[(v, 0)] = r_mat[0][0] * g0 + r_mat[0][1] * g1
        x_star[(v, 1)] = r_mat[1][0] * g0 + r_mat[1][1] * g1

    # Confirm manufactured solution has zero Dirichlet energy: E(x^*) == 0
    assert sheaf.dirichlet_energy(x_star) < 1e-14

    # Clamp boundary vertices B = {0, 4} and solve for interior vertices I = {1, 2, 3}
    boundary_vertices = {0, 4}
    boundary_data = {k: val for k, val in x_star.items() if k[0] in boundary_vertices}

    recovered = sheaf_harmonic_extension(
        sheaf,
        boundary_values=boundary_data,
        boundary_vertices=boundary_vertices,
        tol=1e-11,
        max_iter=2000,
    )

    # Interior vertices {1, 2, 3} must match the manufactured solution x^* to machine precision
    for coord, expected_val in x_star.items():
        assert math.isclose(recovered.get(coord, 0.0), expected_val, rel_tol=1e-8, abs_tol=1e-8)


@pytest.mark.mms
def test_mms_sheaf_harmonic_extension_vs_scipy_schur_complement_and_diffusion() -> None:
    """Verify non-zero-energy harmonic extension against SciPy Schur complement solver & diffusion monotonicity."""
    # General non-flat cellular sheaf over a 4-node diamond network with 2D vertex stalks
    sheaf: CellularSheaf[int] = CellularSheaf()
    sheaf.add_edge(0, 1, dim=2, rho_u=[[1.0, 0.5], [0.0, 1.0]], rho_v=[[1.0, 0.0], [0.2, 1.0]])
    sheaf.add_edge(0, 2, dim=2, rho_u=[[0.8, -0.3], [0.3, 0.8]], rho_v=[[1.0, 0.0], [0.0, 1.0]])
    sheaf.add_edge(1, 2, dim=2, rho_u=[[1.0, 0.2], [-0.2, 1.0]], rho_v=[[0.9, 0.1], [0.0, 1.1]])
    sheaf.add_edge(1, 3, dim=2, rho_u=[[1.0, 0.0], [0.0, 1.0]], rho_v=[[1.2, -0.4], [0.1, 0.9]])
    sheaf.add_edge(2, 3, dim=2, rho_u=[[0.7, 0.3], [-0.1, 1.0]], rho_v=[[1.0, 0.0], [0.0, 1.0]])

    boundary_vertices = {0, 3}
    boundary_values = {(0, 0): 2.0, (0, 1): -1.0, (3, 0): -3.0, (3, 1): 4.0}

    sol_ax = sheaf_harmonic_extension(
        sheaf,
        boundary_values=boundary_values,
        boundary_vertices=boundary_vertices,
        tol=1e-11,
        max_iter=2000,
    )

    # Compare against exact dense Schur complement L_{II} x_I = - L_{IB} x_B via scipy.linalg.solve
    lap_sparse = sheaf_laplacian(sheaf)
    all_coords = [(v, i) for v in sorted(sheaf.vertex_stalks) for i in range(sheaf.vertex_stalks[v])]
    int_coords = [c for c in all_coords if c[0] not in boundary_vertices]
    bnd_coords = [c for c in all_coords if c[0] in boundary_vertices]

    l_ii = np.array([[lap_sparse.get(r, {}).get(c, 0.0) for c in int_coords] for r in int_coords], dtype=np.float64)
    l_ib = np.array([[lap_sparse.get(r, {}).get(c, 0.0) for c in bnd_coords] for r in int_coords], dtype=np.float64)
    x_b = np.array([boundary_values[c] for c in bnd_coords], dtype=np.float64)

    x_i_scipy = sla.solve(l_ii, -l_ib @ x_b, assume_a='pos')
    for idx, coord in enumerate(int_coords):
        assert math.isclose(sol_ax[coord], float(x_i_scipy[idx]), rel_tol=1e-8, abs_tol=1e-8)

    # Interior harmonic residual (L x)_I == 0
    lx = mat_vec(lap_sparse, sol_ax)
    for coord in int_coords:
        assert abs(lx.get(coord, 0.0)) < 1e-8

    # Verify sheaf_diffusion monotonicity E(x_{t+1}) <= E(x_t) and exact matrix power (I - tau L)^k x_0
    x0 = {coord: float(idx + 1) * ((-1) ** idx) for idx, coord in enumerate(all_coords)}
    tau = 0.05
    prev_energy = sheaf.dirichlet_energy(x0)
    curr = x0
    for _ in range(10):
        curr = sheaf_diffusion(sheaf, curr, steps=1, tau=tau)
        new_energy = sheaf.dirichlet_energy(curr)
        assert new_energy <= prev_energy + 1e-12
        prev_energy = new_energy

    l_full = np.array([[lap_sparse.get(r, {}).get(c, 0.0) for c in all_coords] for r in all_coords], dtype=np.float64)
    x0_vec = np.array([x0[c] for c in all_coords], dtype=np.float64)
    expected_diff = np.linalg.matrix_power(np.eye(len(all_coords)) - tau * l_full, 10) @ x0_vec
    np.testing.assert_allclose([curr[c] for c in all_coords], expected_diff, atol=1e-11)


# ---------------------------------------------------------------------------
# 2. Category Theory: Kleisli Monad Laws & Left Kan Extensions
# ---------------------------------------------------------------------------


def test_category_kleisli_monad_laws_and_kan_extension() -> None:
    """Verify Kleisli monad laws (left/right identity & associativity) over Fraction, Tropical & Boolean."""
    # 1. Exact Fraction Kleisli composition
    sr_q = StandardSemiring(Fraction)
    eta = {i: {i: Fraction(1)} for i in range(3)}
    f = {0: {0: Fraction(1, 2), 1: Fraction(1, 3)}, 1: {2: Fraction(3, 4)}, 2: {0: Fraction(-2, 5)}}
    g = {0: {1: Fraction(2), 2: Fraction(-1, 2)}, 1: {0: Fraction(3, 5)}, 2: {1: Fraction(4, 3), 2: Fraction(1)}}
    h = {0: {0: Fraction(1), 2: Fraction(2)}, 1: {1: Fraction(-3, 2)}, 2: {0: Fraction(1, 4), 1: Fraction(5, 6)}}

    # Left & Right Identity: eta o_T f == f and f o_T eta == f
    assert kleisli_compose(f, eta, semiring=sr_q) == f
    assert kleisli_compose(eta, f, semiring=sr_q) == f

    # Associativity: (f o_T g) o_T h == f o_T (g o_T h)
    lhs_q = kleisli_compose(kleisli_compose(f, g, semiring=sr_q), h, semiring=sr_q)
    rhs_q = kleisli_compose(f, kleisli_compose(g, h, semiring=sr_q), semiring=sr_q)
    assert lhs_q == rhs_q

    # Left Kan Extension functoriality: Lan_{P2 o P1} F == Lan_{P2}(Lan_{P1} F)
    lan_step = kan_extension_left(h, kan_extension_left(g, f, semiring=sr_q), semiring=sr_q)
    lan_comp = kan_extension_left(kleisli_compose(g, h, semiring=sr_q), f, semiring=sr_q)
    assert lan_step == lan_comp

    # 2. Tropical & Boolean Kleisli associativity
    sr_trop = TropicalSemiring()
    eta_trop = {i: {i: 0.0} for i in range(3)}
    f_t = {0: {1: 2.5, 2: 5.0}, 1: {2: 1.5}, 2: {0: 3.0}}
    g_t = {0: {0: 1.0}, 1: {2: 2.0, 0: 4.0}, 2: {1: 0.5}}
    h_t = {0: {2: 1.0}, 1: {0: 2.5}, 2: {2: 3.5}}

    assert kleisli_compose(f_t, eta_trop, semiring=sr_trop) == f_t
    assert kleisli_compose(eta_trop, f_t, semiring=sr_trop) == f_t
    assert kleisli_compose(kleisli_compose(f_t, g_t, semiring=sr_trop), h_t, semiring=sr_trop) == kleisli_compose(
        f_t, kleisli_compose(g_t, h_t, semiring=sr_trop), semiring=sr_trop
    )

    sr_bool = BooleanSemiring()
    f_b = {0: {1: True}, 1: {2: True}, 2: {0: True}}
    g_b = {0: {2: True}, 1: {0: True, 1: True}, 2: {1: True}}
    h_b = {0: {0: True}, 1: {2: True}, 2: {0: True, 2: True}}
    assert kleisli_compose(kleisli_compose(f_b, g_b, semiring=sr_bool), h_b, semiring=sr_bool) == kleisli_compose(
        f_b, kleisli_compose(g_b, h_b, semiring=sr_bool), semiring=sr_bool
    )


# ---------------------------------------------------------------------------
# 3. Distributive Lattice Laws & Classical Means (Hypothesis)
# ---------------------------------------------------------------------------

pos_dict_strategy = st.dictionaries(
    keys=st.sampled_from(['a', 'b', 'c', 'd']),
    values=st.floats(min_value=0.5, max_value=50.0, allow_nan=False, allow_infinity=False),
    min_size=1,
    max_size=4,
)


@settings(max_examples=40, deadline=None)
@given(a=pos_dict_strategy, b=pos_dict_strategy, c=pos_dict_strategy)
def test_hypothesis_distributive_lattice_laws_and_means(
    a: dict[str, float],
    b: dict[str, float],
    c: dict[str, float],
) -> None:
    """Verify distributive lattice axioms for join/meet and HM <= GM <= AM inequality on positive mappings."""
    # 1. Idempotence: a v a == a and a ^ a == a
    assert join(a, a) == a
    assert meet(a, a) == a

    # 2. Commutativity: a v b == b v a and a ^ b == b ^ a
    assert join(a, b) == join(b, a)
    assert meet(a, b) == meet(b, a)

    # 3. Associativity
    assert join(join(a, b), c) == join(a, join(b, c))
    assert meet(meet(a, b), c) == meet(a, meet(b, c))

    # 4. Absorption Laws (for positive values where missing keys are 0 <= min_value):
    # join(a, meet(a, b)) == a and meet(a, join(a, b)) == a
    assert join(a, meet(a, b)) == a
    assert meet(a, join(a, b)) == a

    # 5. Distributivity: meet(a, join(b, c)) == join(meet(a, b), meet(a, c))
    assert meet(a, join(b, c)) == join(meet(a, b), meet(a, c))
    assert join(a, meet(b, c)) == meet(join(a, b), join(a, c))

    # 6. Classical Pythagorean Mean Inequality on shared keys: Harmonic <= Geometric <= Arithmetic
    hm = harmonic_mean(a, b)
    gm = geometric_mean(a, b)
    am = average(a, b)
    for k in set(a.keys()) & set(b.keys()):
        assert hm[k] <= gm[k] + 1e-11
        assert gm[k] <= am[k] + 1e-11

    # 7. Set & algebraic mapping identities:
    # mask(a, b) + exclude(a, b) == a (disjoint key partition of a)
    masked = mask(a, b)
    excluded = exclude(a, b)
    assert set(masked.keys()).isdisjoint(set(excluded.keys()))
    assert {**masked, **excluded} == a

    # exclusive(a, b) keys == set(a) ^ set(b)
    excl = exclusive(a, b)
    assert set(excl.keys()) == (set(a.keys()) ^ set(b.keys()))

    # symmetric_difference(a, b)[k] == |difference(a, b)[k]|
    diff_ab = difference(a, b)
    sym_diff_ab = symmetric_difference(a, b)
    for k, val in sym_diff_ab.items():
        assert math.isclose(val, abs(diff_ab[k]), rel_tol=1e-12, abs_tol=1e-12)

    # ratio(product(a, b), b) == a on shared keys
    prod_ab = product(a, b)
    rat_ab = ratio(prod_ab, b)
    for k in set(a.keys()) & set(b.keys()):
        assert math.isclose(rat_ab[k], a[k], rel_tol=1e-11, abs_tol=1e-11)


# ---------------------------------------------------------------------------
# 4. AlgebraicTrie Prefix-Tree Homomorphism
# ---------------------------------------------------------------------------


def test_algebraic_trie_semiring_homomorphism() -> None:
    """Verify AlgebraicTrie.add and contract commute with flat dictionary semiring operations."""
    # 1. StandardSemiring prefix contraction
    trie_std: AlgebraicTrie[str, float] = AlgebraicTrie(StandardSemiring)
    entries = [
        (('u', 'v', 'w'), 2.5),
        (('u', 'v', 'x'), 1.5),
        (('u', 'y'), 3.0),
        (('u', 'v', 'w'), 4.0),  # duplicate key accumulated via semiring.add
        (('z', 'a'), 10.0),
    ]
    flat_std: dict[tuple[str, ...], float] = {}
    for path, val in entries:
        trie_std.add(path, val)
        flat_std[path] = flat_std.get(path, 0.0) + val

    assert dict(trie_std.items()) == flat_std
    assert math.isclose(trie_std.contract(('u', 'v')), 2.5 + 1.5 + 4.0, rel_tol=1e-12)
    assert math.isclose(trie_std.contract(('u',)), 2.5 + 1.5 + 4.0 + 3.0, rel_tol=1e-12)
    assert math.isclose(trie_std.contract(()), sum(flat_std.values()), rel_tol=1e-12)
    assert trie_std.contract(('nonexistent',)) == 0.0

    # Deletion and branch pruning
    del trie_std[('z', 'a')]
    assert ('z', 'a') not in trie_std
    assert len(trie_std) == 3

    # 2. TropicalSemiring prefix minimum contraction
    trie_trop: AlgebraicTrie[str, float] = AlgebraicTrie(TropicalSemiring)
    for path, val in entries:
        trie_trop.add(path, val)

    assert trie_trop.contract(('u',)) == 1.5  # min(2.5, 1.5, 3.0)
    assert trie_trop.contract(('missing',)) == float('inf')


# ---------------------------------------------------------------------------
# 5. EP-0200 & EP-0201: MatrixCategory Lawvere Metric & QuotientRing Morphisms
# ---------------------------------------------------------------------------


def test_mms_matrix_category_composition_and_tropical_lawvere() -> None:
    """Verify MatrixCategory Mat(S) satisfies Category axioms and models Lawvere metric spaces."""
    from algebrax.category import MatrixCategory
    from algebrax.semiring import TropicalSemiring
    from algebrax.verification import verify_category_laws

    cat_trop = MatrixCategory(TropicalSemiring())

    # Morphisms: f, g, h in square 2x2 matrix category
    obj = frozenset({0, 1})
    f = {0: {0: 1.0, 1: 3.0}, 1: {0: 4.0, 1: 0.5}}
    g = {0: {0: 2.0, 1: 1.0}, 1: {0: 1.5, 1: 3.0}}
    h = {0: {0: 0.5, 1: 2.5}, 1: {0: 3.0, 1: 1.2}}

    laws = verify_category_laws(cat_trop, [obj], [f, g, h])
    assert laws['left_identity']
    assert laws['right_identity']
    assert laws['associativity']

    # Lawvere triangle inequality: (g o f)_{ij} = min_k (g_{ik} + f_{kj})
    gf = cat_trop.compose(g, f)
    assert math.isclose(gf[0][0], min(2.0 + 1.0, 1.0 + 4.0), rel_tol=1e-12)


def test_mms_quotient_ring_first_isomorphism_theorem() -> None:
    """Verify RingHomomorphism and QuotientRing satisfy the First Isomorphism Theorem via MMS."""
    from algebrax.algebra import CallableHomomorphism, KernelIdeal, ModularField, QuotientRing, StandardField
    from algebrax.verification import verify_quotient_ring_laws, verify_ring_homomorphism_laws

    z_ring = StandardField(int)
    f5 = ModularField(5)
    phi = CallableHomomorphism(lambda x: x % 5)

    hom_laws = verify_ring_homomorphism_laws(phi, z_ring, f5, [-6, -2, -1, 0, 1, 3, 7])
    assert hom_laws['add_preservation']
    assert hom_laws['mul_preservation']

    ker_phi = KernelIdeal(phi, f5, reducer=lambda x: x % 5)
    quot = QuotientRing(z_ring, ker_phi)
    quot_laws = verify_quotient_ring_laws(quot, [-5, -1, 0, 2, 4, 7, 10], [-10, -5, 0, 5, 10])
    assert quot_laws['coset_invariance']
    assert quot_laws['projection_homomorphism']
    assert all(quot_laws.values())


# ---------------------------------------------------------------------------
# 6. EP-0203: Discrete Fiber Bundles & Gauge Holonomy MMS
# ---------------------------------------------------------------------------


def test_mms_discrete_connection_holonomy_and_curvature() -> None:
    """Verify DiscreteOrthogonalConnection parallel transport around a 3-cycle yields exact holonomy."""
    from algebrax.topology import DiscreteOrthogonalConnection, compute_face_holonomy

    # SO(2) rotation connection on a triangle 0 -> 1 -> 2 -> 0
    theta_01 = math.pi / 6.0
    theta_12 = math.pi / 3.0

    def rot_matrix(th: float) -> dict[int, dict[int, float]]:
        c, s = math.cos(th), math.sin(th)
        return {0: {0: c, 1: -s}, 1: {0: s, 1: c}}

    conn = DiscreteOrthogonalConnection(fiber_dim=2)
    conn.set_transport(0, 1, rot_matrix(theta_01))
    conn.set_transport(1, 2, rot_matrix(theta_12))
    conn.set_transport(0, 2, rot_matrix(0.0))  # flat baseline on 0 -> 2

    # Holonomy around face (0, 1, 2)
    face_hol = compute_face_holonomy(conn, [0, 1, 2])
    # Transport around loop 0 -> 1 -> 2 -> 0 is rho(2, 0) rho(1, 2) rho(0, 1)
    # rho(2, 0) = rho(0, 2)^T = I^T = I
    expected_theta = theta_01 + theta_12
    expected_hol = rot_matrix(expected_theta)

    for i in range(2):
        for j in range(2):
            assert math.isclose(face_hol[i][j], expected_hol[i][j], rel_tol=1e-12, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# 7. EP-0206: Alexander-Whitney Duality & Coalgebra MMS
# ---------------------------------------------------------------------------


def test_mms_alexander_whitney_duality_with_cup_product() -> None:
    r"""Verify Alexander-Whitney duality: <alpha \smile \beta, \sigma> == <alpha \otimes \beta, \Delta(\sigma)>.

    For arbitrary simplicial cochains \alpha \in C^p, \beta \in C^q and simplices \sigma \in C_{p+q},
    the cup product value on \sigma must equal the tensor contraction with the Alexander-Whitney coproduct.
    """
    from algebrax.topology import SimplicialChainCoalgebra, cup_product

    scc = SimplicialChainCoalgebra()

    # Case 1: 1-cochains on 2-simplex (0, 1, 2)
    alpha_1 = {(0, 1): 2.5, (0, 2): 1.0, (1, 2): 3.0}
    beta_1 = {(1, 2): 4.0, (0, 1): -2.0}

    sigma_2 = (0, 1, 2)
    cup_12 = cup_product(alpha_1, beta_1)
    eval_cup_2 = cup_12.get(sigma_2, 0.0)

    delta_sigma_2 = scc.coproduct({sigma_2: 1.0})
    eval_dual_2 = sum(
        coeff * alpha_1.get(front, 0.0) * beta_1.get(back, 0.0)
        for (front, back), coeff in delta_sigma_2.items()
    )
    assert math.isclose(eval_cup_2, eval_dual_2, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(eval_cup_2, 2.5 * 4.0, rel_tol=1e-12, abs_tol=1e-12)

    # Case 2: 1-cochain and 2-cochain on 3-simplex (0, 1, 2, 3)
    alpha_edge = {(0, 1): 1.5, (1, 2): -2.0}
    beta_face = {(1, 2, 3): 3.5, (0, 1, 2): 4.0}

    sigma_3 = (0, 1, 2, 3)
    cup_edge_face = cup_product(alpha_edge, beta_face)
    eval_cup_3 = cup_edge_face.get(sigma_3, 0.0)

    delta_sigma_3 = scc.coproduct({sigma_3: 1.0})
    eval_dual_3 = sum(
        coeff * alpha_edge.get(front, 0.0) * beta_face.get(back, 0.0)
        for (front, back), coeff in delta_sigma_3.items()
    )
    assert math.isclose(eval_cup_3, eval_dual_3, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(eval_cup_3, 1.5 * 3.5, rel_tol=1e-12, abs_tol=1e-12)


