"""
Real-World Use Case: Topological Homology, Boundary Nilpotency & Betti Barcode Invariants.

Theoretical Foundations & Physics:
1. Simplicial Boundary Operators (D_k): Maps k-simplices to (k-1)-simplices via alternating sum faces.
2. Homological Nilpotency Invariant: D_{k-1} o D_k = 0 across all topological dimensions.
3. Betti Numbers (beta_k): Invariant counts of topological holes
   (beta_0 = components, beta_1 = 1D loops, beta_2 = 2D voids).
"""

from algebrax.homology import SimplicialComplex


def main() -> None:
    print('--- Topological Homology & Betti Barcode Analysis ---')

    # Construct an empty 1D ring (cycle S^1 with 4 vertices)
    ring_edges = [(0, 1), (1, 2), (2, 3), (0, 3)]
    sc_ring = SimplicialComplex(ring_edges)

    print('\n[1] 1D Hollow Ring Topological Complex (S^1):')
    print('  Simplices 0D (vertices):', len(sc_ring._simplices.get(0, set())))
    print('  Simplices 1D (edges):', len(sc_ring._simplices.get(1, set())))

    assert sc_ring.verify_nilpotency(k=1)
    betti_ring = sc_ring.betti_numbers(max_k=1)
    print(f'  Betti Numbers: beta_0 = {betti_ring[0]} (components), beta_1 = {betti_ring[1]} (1D loop holes)')

    assert betti_ring[0] == 1
    assert betti_ring[1] == 1

    # Construct a filled 2D tetrahedron complex (S^2 boundary / filled volume)
    sc_tet = SimplicialComplex([(0, 1, 2, 3)])
    print('\n[2] 3D Solid Tetrahedron Complex:')
    print('  Simplices 0D:', len(sc_tet._simplices.get(0, set())))
    print('  Simplices 1D:', len(sc_tet._simplices.get(1, set())))
    print('  Simplices 2D:', len(sc_tet._simplices.get(2, set())))
    print('  Simplices 3D:', len(sc_tet._simplices.get(3, set())))

    assert sc_tet.verify_nilpotency(k=2)
    assert sc_tet.verify_nilpotency(k=3)

    betti_tet = sc_tet.betti_numbers(max_k=2)
    print(f'  Betti Numbers: beta_0 = {betti_tet[0]}, beta_1 = {betti_tet[1]}, beta_2 = {betti_tet[2]}')

    assert betti_tet[0] == 1
    assert betti_tet[1] == 0
    assert betti_tet[2] == 0

    print('\nSuccessfully verified Simplicial Homology & Betti Barcode Invariants!')


if __name__ == '__main__':
    main()
