"""
Tests for SimplicialComplex and Betti Numbers.
"""

from algebrax.homology import SimplicialComplex, SparseChainComplex, coboundary, cohomology_rank


def test_betti_numbers_single_triangle():
    """
    A filled triangle (0, 1, 2) has 1 connected component (beta_0 = 1),
    no 1D loop holes (beta_1 = 0) because the interior is filled.
    """
    sc = SimplicialComplex([(0, 1, 2)])
    betti = sc.betti_numbers(max_k=2)

    assert betti[0] == 1  # 1 connected component
    assert betti[1] == 0  # No 1D hole (triangle is filled)
    assert betti[2] == 0  # No 2D void


def test_betti_numbers_empty_triangle_loop():
    """
    An empty triangle (circle topology S^1) with edges (0,1), (1,2), (0,2)
    has 1 connected component (beta_0 = 1) and 1 loop hole (beta_1 = 1).
    """
    sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
    betti = sc.betti_numbers(max_k=2)

    assert betti[0] == 1  # 1 connected component
    assert betti[1] == 1  # 1 1D loop hole!
    assert betti[2] == 0


def test_betti_numbers_disjoint_components():
    """
    Two disjoint edges: (0, 1) and (2, 3).
    beta_0 = 2 (two connected components), beta_1 = 0.
    """
    sc = SimplicialComplex([(0, 1), (2, 3)])
    betti = sc.betti_numbers(max_k=1)

    assert betti[0] == 2
    assert betti[1] == 0


def test_coboundary_operator():
    """Verify coboundary(complex, k) is the transpose of boundary matrix D_{k+1}."""
    sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
    d1 = sc.boundary_matrices[1]
    d0_co = coboundary(sc, 0)

    for edge in d1:
        for vertex, val in d1[edge].items():
            assert d0_co[vertex][edge] == val


def test_cohomology_rank():
    """Verify cohomology_rank matches betti_numbers for simplicial complex."""
    sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
    assert cohomology_rank(sc, 0) == 1
    assert cohomology_rank(sc, 1) == 1


def test_triangle_chain_complex_nilpotency_and_laplacian():
    """
    Test SparseChainComplex over a 2-simplex (Triangle (0, 1, 2)):
    - D1 (edges to vertices): maps 1D edges (0,1), (1,2), (0,2) to 0D vertices.
    - D2 (triangles to edges): maps 2D triangle (0,1,2) to 1D edges.
    Verify D1 o D2 == 0 (Nilpotency) and compute Hodge-Laplacians Delta_0 and Delta_1.
    """
    d1 = {
        (0,): {(0, 1): -1.0, (0, 2): -1.0},
        (1,): {(0, 1): 1.0, (1, 2): -1.0},
        (2,): {(0, 2): 1.0, (1, 2): 1.0},
    }

    d2 = {
        (0, 1): {(0, 1, 2): 1.0},
        (0, 2): {(0, 1, 2): -1.0},
        (1, 2): {(0, 1, 2): 1.0},
    }

    complex_sys = SparseChainComplex(boundary_matrices={1: d1, 2: d2})

    # Verify D1 o D2 == 0
    assert complex_sys.verify_nilpotency(k=2)

    # Compute Hodge-Laplacian Delta_0 (0D Laplacian on vertices)
    delta_0 = complex_sys.hodge_laplacian(k=0)
    assert (0,) in delta_0

    # Compute Hodge-Laplacian Delta_1 (1D Laplacian on edges)
    delta_1 = complex_sys.hodge_laplacian(k=1)
    assert (0, 1) in delta_1


def test_cochain_orientation_and_degenerate_simplices():
    import pytest

    from algebrax.homology import Cochain

    # 1-cochain initialized with uncanonical orientation and degenerate edge
    omega = Cochain({(1, 0): 5.0, (1, 2): -3.0, (2, 2): 99.0})
    assert omega.degree == 1
    assert omega.oriented is True
    assert len(omega) == 2
    assert list(omega) == [(0, 1), (1, 2)]

    # Canonical and reversed lookups flip sign
    assert omega[(0, 1)] == -5.0
    assert omega[(1, 0)] == 5.0
    assert omega.get((0, 1)) == -5.0
    assert omega.get((1, 0)) == 5.0
    assert omega.get((0, 99), 0.0) == 0.0
    assert omega.get('not-a-tuple', 'default') == 'default'

    # Degenerate simplex is annihilated
    assert omega.get((0, 0)) == 0.0
    with pytest.raises(KeyError):
        _ = omega[(0, 0)]
    with pytest.raises(KeyError):
        _ = omega['not-a-tuple']  # type: ignore[index]

    # 2-cochain permutation parity
    two_form = Cochain({(0, 1, 2): 4.0})
    assert two_form.degree == 2
    assert two_form[(0, 1, 2)] == 4.0
    assert two_form[(1, 2, 0)] == 4.0  # even permutation
    assert two_form[(2, 0, 1)] == 4.0  # even permutation
    assert two_form[(0, 2, 1)] == -4.0  # odd permutation
    assert two_form[(1, 0, 2)] == -4.0  # odd permutation
    assert two_form[(2, 1, 0)] == -4.0  # odd permutation

    # Unoriented cochain mode
    unoriented = Cochain({(1, 0): 5.0}, oriented=False)
    assert unoriented.oriented is False
    assert unoriented[(0, 1)] == 5.0
    assert unoriented[(1, 0)] == 5.0


def test_cochain_arithmetic_and_eval():
    import pytest

    from algebrax.homology import Cochain

    w1 = Cochain({(0, 1): 2.0, (1, 2): 3.0})
    w2 = Cochain({(1, 0): -1.0, (1, 2): -3.0, (0, 2): 4.0})  # (0, 1): +1.0

    # Addition with cancellation on (1, 2)
    w_sum = w1 + w2
    assert w_sum == Cochain({(0, 1): 3.0, (0, 2): 4.0})
    assert w_sum == {(0, 1): 3.0, (0, 2): 4.0}

    # Subtraction, negation, scalar multiplication
    w_diff = w1 - w2
    assert w_diff == Cochain({(0, 1): 1.0, (1, 2): 6.0, (0, 2): -4.0})
    assert (-w1)[(0, 1)] == -2.0
    assert (2.0 * w1)[(0, 1)] == 4.0
    assert (w1 * 0.5)[(1, 2)] == 1.5
    assert (0.0 * w1) == Cochain(degree=1)

    # Bilinear Kronecker pairing <omega, c>
    chain = {(0, 1): 2.0, (2, 1): -1.0}  # w1((0,1))*2 + w1((2,1))*(-1) = 2*2 + (-3)*(-1) = 7.0
    assert w1.eval(chain) == pytest.approx(7.0)

    # Degree validation error
    with pytest.raises(ValueError, match='expected degree'):
        Cochain({(0, 1): 1.0}, degree=2)


def test_cochain_bridges_and_coboundary_equivalence():
    import pytest

    from algebrax.analysis import cochain_to_flow, flow_to_cochain, gradient
    from algebrax.homology import Cochain, SimplicialComplex, coboundary
    from algebrax.matrix import mat_vec

    # 1. Node bridge round-trip (0-cochain <-> SparseVector)
    potential = {0: 1.0, 1: 4.0, 2: -2.0}
    c0 = Cochain.from_nodes(potential)
    assert c0.degree == 0
    assert c0[(1,)] == 4.0
    assert c0.to_nodes() == potential

    # 2. Flow bridge modes ('auto', 'net', 'half_skew')
    graph = {0: {1: 1.0, 2: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {0: 1.0, 1: 1.0}}
    grad_flow = gradient(potential, graph)
    c1_auto = Cochain.from_flow(grad_flow, mode='auto')
    c1_half = Cochain.from_flow(grad_flow, mode='half_skew')
    assert c1_auto == c1_half
    assert c1_auto[(0, 1)] == pytest.approx(3.0)
    assert c1_auto[(1, 0)] == pytest.approx(-3.0)

    # Reconstructed skew-symmetric flow matches original gradient flow
    assert c1_auto.to_flow(skew_symmetric=True) == grad_flow
    assert cochain_to_flow(flow_to_cochain(grad_flow), skew_symmetric=True) == grad_flow
    upper_flow = c1_auto.to_flow(skew_symmetric=False)
    assert upper_flow[0][1] == pytest.approx(3.0)
    assert 0 not in upper_flow.get(1, {})

    # Directed single-sided flow in 'auto' and 'net' modes
    directed_flow = {0: {1: 5.0}}
    assert Cochain.from_flow(directed_flow, mode='auto')[(0, 1)] == pytest.approx(5.0)
    assert Cochain.from_flow({0: {1: 7.0}, 1: {0: 2.0}}, mode='net')[(0, 1)] == pytest.approx(5.0)

    # 3. Coboundary d_0 equivalence: Cochain.from_flow(gradient(f, G)) == coboundary(K, 0) @ Cochain.from_nodes(f)
    sc = SimplicialComplex([(0, 1, 2)])
    d0 = coboundary(sc, 0)
    d0_c0 = Cochain(mat_vec(d0, c0), degree=1)
    assert d0_c0 == c1_auto

    # Error handling on wrong-degree conversions and invalid mode
    with pytest.raises(ValueError, match='0-cochain'):
        c1_auto.to_nodes()
    with pytest.raises(ValueError, match='1-cochain'):
        c0.to_flow()
    with pytest.raises(ValueError, match='Unknown mode'):
        Cochain.from_flow(grad_flow, mode='invalid')  # type: ignore[arg-type]


def test_dec_operators_and_hodge_star():
    import pytest

    from algebrax.analysis import (
        canonicalize_form,
        codifferential,
        exterior_derivative,
        hodge_laplacian,
        hodge_star,
    )
    from algebrax.homology import SimplicialComplex
    from algebrax.matrix import dot

    sc = SimplicialComplex([(0, 1, 2)])
    d0 = exterior_derivative(sc, 0)
    d1 = exterior_derivative(sc, 1)

    # Exact chain nilpotency: d1 o d0 == 0
    assert dot(d1, d0) == {}

    # Codifferential nilpotency: delta_1 o delta_2 == 0
    delta1 = codifferential(sc, 1)
    delta2 = codifferential(sc, 2)
    assert dot(delta1, delta2) == {}
    assert codifferential(sc, 99) == {}

    # Weighted codifferential and hodge_star
    w_edges = {(0, 1): 2.0, (0, 2): 4.0, (1, 2): 1.0}
    w_verts = {(0,): 1.0, (1,): 2.0, (2,): 2.0}
    delta1_w = codifferential(sc, 1, dual_weights_k=w_edges, dual_weights_km1=w_verts)
    assert delta1_w[(0,)][(0, 1)] == pytest.approx(-2.0)

    form = canonicalize_form({(1, 0): 3.0})
    assert form[(0, 1)] == -3.0
    starred = hodge_star(form, dual_weights=w_edges)
    assert starred[(0, 1)] == pytest.approx(-6.0)
    unstarred = hodge_star(starred, dual_weights=w_edges, inverse=True)
    assert unstarred == form
    assert hodge_star(form) == form

    with pytest.raises(ValueError, match='positive'):
        hodge_star(form, dual_weights={(0, 1): -1.0})

    # Functional hodge_laplacian matches SimplicialComplex.hodge_laplacian
    assert hodge_laplacian(sc, 1) == sc.hodge_laplacian(1)


def test_helmholtz_hodge_decomposition_topologies():
    import pytest

    from algebrax.analysis import (
        Cochain,
        codifferential,
        exterior_derivative,
        helmholtz_hodge_decomposition,
    )
    from algebrax.homology import SimplicialComplex
    from algebrax.matrix import inner, mat_vec

    # 1. Acyclic Tree (0 - 1 - 2): every flow is purely exact (coexact = 0, harmonic = 0)
    tree = SimplicialComplex([(0, 1), (1, 2)])
    tree_flow = {(0, 1): 4.0, (1, 2): -2.0}
    decomp_tree = helmholtz_hodge_decomposition(tree, tree_flow)
    assert decomp_tree.exact == Cochain(tree_flow)
    assert len(decomp_tree.coexact) == 0
    assert len(decomp_tree.harmonic) == 0

    # 2. Filled 2-Simplex Disc (0, 1, 2): closed cycle has beta_1 = 0 -> purely coexact!
    disc = SimplicialComplex([(0, 1, 2)])
    vortex_flow = {(0, 1): 2.0, (1, 2): 2.0, (2, 0): 2.0}  # boundary of 2*(0,1,2)
    decomp_disc = helmholtz_hodge_decomposition(disc, vortex_flow)
    assert len(decomp_disc.exact) == 0
    assert len(decomp_disc.harmonic) == 0
    assert decomp_disc.coexact == Cochain(vortex_flow)
    assert decomp_disc.stream[(0, 1, 2)] == pytest.approx(2.0, abs=1e-7)

    # 3. Hollow Ring S^1 (edges (0,1), (1,2), (0,2), no 2-simplex): cycle is purely harmonic!
    ring = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
    decomp_ring = helmholtz_hodge_decomposition(ring, vortex_flow)
    assert len(decomp_ring.exact) == 0
    assert len(decomp_ring.coexact) == 0
    assert decomp_ring.harmonic == Cochain(vortex_flow)

    # 4. Mixed Topology: filled triangle (0, 1, 2) + hollow handle loop (1, 2)-(2, 3)-(1, 3)
    mixed_sc = SimplicialComplex([(0, 1, 2), (1, 3), (2, 3)])
    d0 = exterior_derivative(mixed_sc, 0)
    d1 = exterior_derivative(mixed_sc, 1)
    delta1 = codifferential(mixed_sc, 1)

    # Synthesize a flow with all 3 components:
    # - gradient of alpha = {0: 1.0, 1: -2.0, 2: 3.0, 3: 0.5}
    # - curl around filled triangle (0, 1, 2)
    # - circulation around handle (1, 2) -> (2, 3) -> (3, 1)
    true_alpha = Cochain.from_nodes({0: 1.0, 1: -2.0, 2: 3.0, 3: 0.5})
    grad_part = Cochain(mat_vec(d0, true_alpha), degree=1)
    curl_part = Cochain({(0, 1): 1.5, (1, 2): 1.5, (2, 0): 1.5})
    handle_loop = Cochain({(1, 2): 2.0, (2, 3): 2.0, (3, 1): 2.0})
    combined_flow = grad_part + curl_part + handle_loop

    res = helmholtz_hodge_decomposition(mixed_sc, combined_flow)

    # Exact reconstruction: omega == exact + coexact + harmonic
    reconstructed = res.exact + res.coexact + res.harmonic
    for edge in combined_flow:
        assert reconstructed[edge] == pytest.approx(combined_flow[edge], abs=1e-7)

    # Mutual L2 orthogonality: <exact, coexact> == <exact, harmonic> == <coexact, harmonic> == 0
    assert inner(res.exact, res.coexact) == pytest.approx(0.0, abs=1e-7)
    assert inner(res.exact, res.harmonic) == pytest.approx(0.0, abs=1e-7)
    assert inner(res.coexact, res.harmonic) == pytest.approx(0.0, abs=1e-7)

    # Differential invariants:
    # - exact is curl-free (d_1(exact) == 0)
    # - coexact is divergence-free (delta_1(coexact) == 0)
    # - harmonic is both curl-free and divergence-free
    assert all(abs(v) < 1e-7 for v in mat_vec(d1, res.exact).values())
    assert all(abs(v) < 1e-7 for v in mat_vec(delta1, res.coexact).values())
    assert all(abs(v) < 1e-7 for v in mat_vec(d1, res.harmonic).values())
    assert all(abs(v) < 1e-7 for v in mat_vec(delta1, res.harmonic).values())

    # Nested SparseMatrix adjacency input produces identical decomposition
    nested_input = combined_flow.to_flow(skew_symmetric=True)
    res_nested = helmholtz_hodge_decomposition(mixed_sc, nested_input)
    for edge in res.exact:
        assert res_nested.exact[edge] == pytest.approx(res.exact[edge], abs=1e-7)
    assert helmholtz_hodge_decomposition(mixed_sc, {}).exact == Cochain(degree=1)


def test_cellular_sheaf_constant_equivalence():
    import pytest

    from algebrax.analysis import CellularSheaf, sheaf_laplacian
    from algebrax.matrix import laplacian_matrix

    # 1. Weighted triangle graph
    g = {
        0: {1: 2.5, 2: 1.0},
        1: {0: 2.5, 2: 3.5},
        2: {0: 1.0, 1: 3.5},
    }
    l_std = laplacian_matrix(g)
    sheaf = CellularSheaf.constant(g, stalk_dim=1)
    l_sheaf = sheaf.laplacian_matrix()

    for u in l_std:
        for v in l_std[u]:
            assert l_sheaf[(u, 0)][(v, 0)] == pytest.approx(l_std[u][v], abs=1e-13)

    assert sheaf_laplacian(sheaf) == l_sheaf
    assert sheaf.global_sections_dimension() == 1

    # 2. Multi-component graph with isolated node
    g_disjoint = {
        0: {1: 1.0},
        1: {0: 1.0},
        2: {3: 2.0},
        3: {2: 2.0},
        4: {},
    }
    sheaf_disjoint = CellularSheaf.constant(g_disjoint, stalk_dim=1)
    assert sheaf_disjoint.global_sections_dimension() == 3

    # 3. Higher stalk dimensions (stalk_dim = 2)
    sheaf_dim2 = CellularSheaf.constant(g, stalk_dim=2)
    l_dim2 = sheaf_dim2.laplacian_matrix()
    for u in l_std:
        for v in l_std[u]:
            for d in range(2):
                assert l_dim2[(u, d)][(v, d)] == pytest.approx(l_std[u][v], abs=1e-13)
            assert (v, 1) not in l_dim2.get((u, 0), {})

    with pytest.raises(ValueError, match='positive'):
        CellularSheaf.constant(g, stalk_dim=0)


def test_cellular_sheaf_connection_and_holonomy():
    import math

    import pytest

    from algebrax.analysis import CellularSheaf, sheaf_diffusion
    from algebrax.matrix import vec_norm

    def rot(theta: float) -> list[list[float]]:
        c, s = math.cos(theta), math.sin(theta)
        return [[c, -s], [s, c]]

    ident = [[1.0, 0.0], [0.0, 1.0]]

    # 1. Flat Connection: SO(2) rotation angles sum to 0 (holonomy I)
    sheaf_flat = CellularSheaf()
    sheaf_flat.add_edge(0, 1, dim=2, rho_u=rot(math.pi / 3), rho_v=ident)
    sheaf_flat.add_edge(1, 2, dim=2, rho_u=rot(math.pi / 6), rho_v=ident)
    sheaf_flat.add_edge(0, 2, dim=2, rho_u=rot(math.pi / 2), rho_v=ident)

    assert sheaf_flat.global_sections_dimension() == 2

    # A non-zero global section has zero Dirichlet energy and is invariant under diffusion
    x_flat = {
        (0, 0): 1.0,
        (0, 1): 0.0,
        (1, 0): math.cos(math.pi / 3),
        (1, 1): math.sin(math.pi / 3),
        (2, 0): math.cos(math.pi / 2),
        (2, 1): math.sin(math.pi / 2),
    }
    assert sheaf_flat.dirichlet_energy(x_flat) == pytest.approx(0.0, abs=1e-12)
    x_diff_flat = sheaf_diffusion(sheaf_flat, x_flat, steps=10, tau=0.1)
    for k, v in x_flat.items():
        assert x_diff_flat.get(k, 0.0) == pytest.approx(v, abs=1e-10)

    # 2. Frustrated Connection: loop holonomy is -I (discrete Mobius strip)
    sheaf_frustrated = CellularSheaf()
    sheaf_frustrated.add_edge(0, 1, dim=2, rho_u=ident, rho_v=ident)
    sheaf_frustrated.add_edge(1, 2, dim=2, rho_u=ident, rho_v=ident)
    sheaf_frustrated.add_edge(0, 2, dim=2, rho_u=rot(math.pi), rho_v=ident)

    assert sheaf_frustrated.global_sections_dimension() == 0

    x0 = {(0, 0): 1.0, (1, 0): 1.0, (2, 0): 1.0}
    e0 = sheaf_frustrated.dirichlet_energy(x0)
    assert e0 > 0.0

    x_decayed = sheaf_diffusion(sheaf_frustrated, x0, steps=80, tau=0.1)
    e_decayed = sheaf_frustrated.dirichlet_energy(x_decayed)
    assert e_decayed < e0 * 1e-4
    assert vec_norm(x_decayed) < 1e-3


def test_cellular_sheaf_dirichlet_energy_and_symmetry():
    import pytest

    from algebrax.analysis import CellularSheaf
    from algebrax.matrix import inner, mat_vec

    sheaf1 = CellularSheaf()
    sheaf1.add_edge('A', 'B', dim=2, rho_u=[[1.0, 2.0], [0.0, 1.0]], rho_v=[[2.0, 0.0], [1.0, 1.0]])

    sheaf2 = CellularSheaf()
    sheaf2.add_edge('B', 'A', dim=2, rho_u=[[2.0, 0.0], [1.0, 1.0]], rho_v=[[1.0, 2.0], [0.0, 1.0]])

    # Orientation Invariance
    l1 = sheaf1.laplacian_matrix()
    l2 = sheaf2.laplacian_matrix()
    assert l1 == l2

    # Self-Adjoint Symmetry of Laplacian: L[r][c] == L[c][r]
    for r, row in l1.items():
        for c, val in row.items():
            assert l1[c][r] == pytest.approx(val, abs=1e-14)

    # Energy Equivalence: 1/2 ||delta x||^2 == 1/2 <x, L x>
    test_sec = {('A', 0): 2.0, ('A', 1): -1.0, ('B', 0): 0.5, ('B', 1): 3.0}
    energy_coboundary = sheaf1.dirichlet_energy(test_sec)
    energy_laplacian = 0.5 * inner(test_sec, mat_vec(l1, test_sec))
    assert energy_coboundary == pytest.approx(energy_laplacian, abs=1e-12)
    assert energy_coboundary >= 0.0


def test_cellular_sheaf_harmonic_extension():
    import pytest

    from algebrax.analysis import CellularSheaf, sheaf_harmonic_extension
    from algebrax.matrix import mat_vec

    # 1. 1D Path 0 - 1 - 2 - 3 with fixed boundaries 0 and 3
    sheaf = CellularSheaf()
    sheaf.add_edge(0, 1, dim=1, rho_u=1.0, rho_v=1.0)
    sheaf.add_edge(1, 2, dim=1, rho_u=1.0, rho_v=1.0)
    sheaf.add_edge(2, 3, dim=1, rho_u=1.0, rho_v=1.0)

    boundary_vals = {(0, 0): 0.0, (3, 0): 3.0}
    sol = sheaf_harmonic_extension(sheaf, boundary_vals, boundary_vertices={0, 3})

    assert sol[(0, 0)] == pytest.approx(0.0, abs=1e-7)
    assert sol[(1, 0)] == pytest.approx(1.0, abs=1e-7)
    assert sol[(2, 0)] == pytest.approx(2.0, abs=1e-7)
    assert sol[(3, 0)] == pytest.approx(3.0, abs=1e-7)

    # Harmonicity test: (L x)_u == 0 on interior vertices 1 and 2
    lap = sheaf.laplacian_matrix()
    lx = mat_vec(lap, sol)
    assert lx.get((1, 0), 0.0) == pytest.approx(0.0, abs=1e-7)
    assert lx.get((2, 0), 0.0) == pytest.approx(0.0, abs=1e-7)

    # 2. Boundary edge cases
    all_b = sheaf_harmonic_extension(sheaf, boundary_vals, boundary_vertices={0, 1, 2, 3})
    assert all_b == boundary_vals

    no_b = sheaf_harmonic_extension(sheaf, {}, boundary_vertices=set())
    assert all(abs(v) < 1e-12 for v in no_b.values())


def test_cellular_sheaf_edge_cases_and_error_handling():
    import pytest

    from algebrax.analysis import CellularSheaf, sheaf_diffusion, sheaf_harmonic_extension

    # Empty sheaf
    empty = CellularSheaf()
    assert empty.coboundary_matrix() == {}
    assert empty.laplacian_matrix() == {}
    assert empty.global_sections_dimension() == 0
    assert empty.dirichlet_energy({}) == 0.0
    assert sheaf_diffusion(empty, {}) == {}
    assert sheaf_harmonic_extension(empty, {}, set()) == {}

    # Validation errors
    with pytest.raises(ValueError, match='positive'):
        empty.add_vertex('u', dim=0)
    with pytest.raises(ValueError, match='positive'):
        empty.add_edge('u', 'v', dim=-1, rho_u=1.0, rho_v=1.0)
    with pytest.raises(TypeError, match='Unsupported'):
        empty.add_edge('u', 'v', dim=1, rho_u='invalid', rho_v=1.0)  # type: ignore[arg-type]
