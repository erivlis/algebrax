"""
Topological Data Analysis, Homology & Cohomology (Backwards-Compatible Facade for `algebrax.topology`).

Summary:
    Counts connected components (beta_0) and multidimensional holes (beta_1, beta_2)
    in point clouds, meshes, and graph structures using boundary matrices, cochain ring products,
    persistent homology/cohomology, Discrete Exterior Calculus, and cellular sheaves.

All functionality is canonically organized under `algebrax.topology` (`homology`, `cohomology`,
`persistence`, `dec`, and `sheaf`) and re-exported here for full backwards compatibility.
"""

from __future__ import annotations

from algebrax.topology import (
    CellularSheaf,
    Cochain,
    DiscreteForm,
    EdgeStalkCoord,
    FilteredSimplicialComplex,
    HodgeDecomposition,
    PersistenceInterval,
    RestrictionMap,
    SimplicialComplex,
    SparseChainComplex,
    StalkCoord,
    betti_curve,
    bottleneck_distance,
    canonicalize_form,
    cap_product,
    coboundary,
    cochain_to_flow,
    codifferential,
    cohomology_rank,
    cup_product,
    exterior_derivative,
    flow_to_cochain,
    helmholtz_hodge_decomposition,
    hodge_laplacian,
    hodge_star,
    persistence_entropy,
    persistent_cohomology,
    persistent_homology,
    sheaf_diffusion,
    sheaf_harmonic_extension,
    sheaf_laplacian,
)
from algebrax.topology._core import (
    _canonicalize_simplex,
    _count_inversions_and_sort,
    _is_non_zero,
    _matrix_rank,
)

__all__ = [
    'CellularSheaf',
    'Cochain',
    'DiscreteForm',
    'EdgeStalkCoord',
    'FilteredSimplicialComplex',
    'HodgeDecomposition',
    'PersistenceInterval',
    'RestrictionMap',
    'SimplicialComplex',
    'SparseChainComplex',
    'StalkCoord',
    '_canonicalize_simplex',
    '_count_inversions_and_sort',
    '_is_non_zero',
    '_matrix_rank',
    'betti_curve',
    'bottleneck_distance',
    'canonicalize_form',
    'cap_product',
    'coboundary',
    'cochain_to_flow',
    'codifferential',
    'cohomology_rank',
    'cup_product',
    'exterior_derivative',
    'flow_to_cochain',
    'helmholtz_hodge_decomposition',
    'hodge_laplacian',
    'hodge_star',
    'persistence_entropy',
    'persistent_cohomology',
    'persistent_homology',
    'sheaf_diffusion',
    'sheaf_harmonic_extension',
    'sheaf_laplacian',
]
