# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Topological Homology, Boundary Nilpotency & Betti Barcode Invariants
#
# ## Theoretical Foundations & Physics
# 1. **Simplicial Boundary Operators ($D_k$)**: Maps $k$-simplices to $(k-1)$-simplices via alternating sum faces.
# 2. **Homological Nilpotency Invariant**: $D_{k-1} \\circ D_k = 0$ across all topological dimensions.
# 3. **Betti Numbers ($\\beta_k$)**: Invariant counts of topological holes.

# %%
from typing import Any

import algebrax as ax


def get_homology_preset(preset: str) -> tuple[list[tuple[int, ...]], dict[int, tuple[int, int]], int]:
    """Return simplices, 2D display coordinates, and max dimension for standard topological manifolds."""
    if preset == '1D Circle (S^1)':
        simplices = [(0, 1), (1, 2), (2, 3), (0, 3)]
        coords = {0: (200, 70), 1: (330, 200), 2: (200, 330), 3: (70, 200)}
        max_k = 1
    elif preset == 'Solid Triangle (2-Simplex)':
        simplices = [(0, 1, 2)]
        coords = {0: (200, 60), 1: (340, 320), 2: (60, 320)}
        max_k = 2
    elif preset == 'Double Loop (Figure 8)':
        simplices = [(0, 1), (1, 2), (0, 2), (0, 3), (3, 4), (0, 4)]
        coords = {0: (200, 200), 1: (100, 100), 2: (100, 300), 3: (300, 100), 4: (300, 300)}
        max_k = 1
    elif preset == '3D Solid Tetrahedron':
        simplices = [(0, 1, 2, 3)]
        coords = {0: (200, 50), 1: (350, 300), 2: (50, 300), 3: (200, 210)}
        max_k = 2
    else:  # Hollow Sphere S^2
        simplices = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
        coords = {0: (200, 50), 1: (350, 300), 2: (50, 300), 3: (200, 210)}
        max_k = 2
    return simplices, coords, max_k


def evaluate_simplicial_complex(
    simplices: list[tuple[int, ...]],
    max_k: int = 2,
) -> dict[str, Any]:
    """Compute simplicial homology, Betti numbers, and boundary nilpotency."""
    sc = ax.homology.SimplicialComplex(simplices)
    betti = sc.betti_numbers(max_k=max_k)
    nilpotency = sc.verify_nilpotency(1) if max_k >= 1 else True
    return {
        'complex': sc,
        'betti': betti,
        'nilpotency': nilpotency,
        'num_vertices': len(sc._simplices.get(0, set())),
        'num_edges': len(sc._simplices.get(1, set())),
    }

# %% [markdown]
# ## Step 1: 1D Hollow Ring Topological Complex ($S^1$)
#
# ## Step 2: 3D Solid Tetrahedron Complex


def run_demo() -> None:
    """Run simplicial complex evaluations, Betti numbers, and boundary nilpotency."""
    simplices_ring, _, max_k_ring = get_homology_preset('1D Circle (S^1)')
    res_ring = evaluate_simplicial_complex(simplices_ring, max_k=max_k_ring)
    betti_ring = res_ring['betti']

    print('1D Hollow Ring Topological Complex (S^1):')
    print(f'  Vertices: {res_ring["num_vertices"]}, Edges: {res_ring["num_edges"]}')
    print(f'  Betti Numbers: beta_0 = {betti_ring[0]} (components), beta_1 = {betti_ring[1]} (1D loop holes)')
    print(f'  Boundary Nilpotency Verified: {res_ring["nilpotency"]}')
    assert betti_ring[0] == 1
    assert betti_ring[1] == 1

    simplices_tet, _, max_k_tet = get_homology_preset('3D Solid Tetrahedron')
    res_tet = evaluate_simplicial_complex(simplices_tet, max_k=max_k_tet)
    betti_tet = res_tet['betti']

    print('\n3D Solid Tetrahedron Complex:')
    print(f'  Betti Numbers: beta_0 = {betti_tet[0]}, beta_1 = {betti_tet[1]}, beta_2 = {betti_tet.get(2, 0)}')
    assert betti_tet[0] == 1
    assert betti_tet[1] == 0


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Topological Homology & Betti Barcodes Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
