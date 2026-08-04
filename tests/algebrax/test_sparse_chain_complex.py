"""
Tests for SparseChainComplex (EP-0101).
"""

from algebrax.homology import SparseChainComplex


def test_triangle_chain_complex_nilpotency_and_laplacian():
    """
    Test SparseChainComplex over a 2-simplex (Triangle (0, 1, 2)):
    - D1 (edges to vertices): maps 1D edges (0,1), (1,2), (0,2) to 0D vertices.
    - D2 (triangles to edges): maps 2D triangle (0,1,2) to 1D edges.
    Verify D1 o D2 == 0 (Nilpotency) and compute Hodge-Laplacians Delta_0 and Delta_1.
    """
    # 0D vertices: (0,), (1,), (2,)
    # 1D edges: (0, 1), (1, 2), (0, 2)
    # 2D triangle: (0, 1, 2)

    # D1: d(v0, v1) = (v1) - (v0)
    d1 = {
        (0,): {(0, 1): -1.0, (0, 2): -1.0},
        (1,): {(0, 1): 1.0, (1, 2): -1.0},
        (2,): {(0, 2): 1.0, (1, 2): 1.0},
    }

    # D2: d(0, 1, 2) = (1, 2) - (0, 2) + (0, 1)
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
