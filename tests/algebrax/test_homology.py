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
