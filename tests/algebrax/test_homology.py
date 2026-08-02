"""
Tests for SimplicialComplex and Betti Numbers (EP-0110).
"""

from algebrax.homology import SimplicialComplex, coboundary, cohomology_rank


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

