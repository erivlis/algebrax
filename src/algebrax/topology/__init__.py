"""
Unified Algebraic Topology, Homology, Cohomology, Persistent Homology, DEC & Cellular Sheaves.

Summary:
    Provides simplicial and chain homology, cochain ring algebra (Alexander-Whitney cup and cap products),
    multiscale persistent homology and cohomology over Z_2, Discrete Exterior Calculus (DEC),
    Helmholtz-Hodge decomposition, and cellular sheaf cohomology.

Submodules:
    - `homology`: `SparseChainComplex`, `SimplicialComplex`, Betti numbers.
    - `cohomology`: `Cochain`, `coboundary`, `cohomology_rank`, `cup_product`, `cap_product`.
    - `persistence`: `FilteredSimplicialComplex`, `PersistenceInterval`, `persistent_homology`,
      `persistent_cohomology`, `betti_curve`, `persistence_entropy`, `bottleneck_distance`.
    - `dec`: `exterior_derivative`, `codifferential`, `hodge_star`, `hodge_laplacian`,
      `helmholtz_hodge_decomposition`, `HodgeDecomposition`.
    - `sheaf`: `CellularSheaf`, `sheaf_laplacian`, `sheaf_diffusion`, `sheaf_harmonic_extension`.
"""

from __future__ import annotations

from algebrax.topology import bundle, coalgebra, cohomology, dec, homology, k_theory, persistence, sheaf
from algebrax.topology.bundle import (
    DiscreteConnection,
    DiscreteOrthogonalConnection,
    apply_gauge_transformation,
    build_connection_laplacian,
    compute_face_holonomy,
    covariant_exterior_derivative,
    is_flat_bundle,
)
from algebrax.topology.coalgebra import (
    SimplicialChainCoalgebra,
)
from algebrax.topology.cohomology import (
    Cochain,
    CochainAlgebra,
    DiscreteForm,
    canonicalize_form,
    cap_product,
    coboundary,
    cochain_to_flow,
    cohomology_rank,
    cup_product,
    flow_to_cochain,
)
from algebrax.topology.dec import (
    HodgeDecomposition,
    codifferential,
    exterior_derivative,
    helmholtz_hodge_decomposition,
    hodge_laplacian,
    hodge_star,
)
from algebrax.topology.homology import (
    SimplicialComplex,
    SparseChainComplex,
)
from algebrax.topology.k_theory import (
    TopologicalKTheoryRing,
    bundle_direct_sum,
    bundle_tensor_product,
    chern_character,
    compute_chern_character_1,
    compute_chern_character_2,
    compute_face_curvature_angle,
    first_chern_number,
    trivial_bundle,
)
from algebrax.topology.persistence import (
    FilteredSimplicialComplex,
    PersistenceInterval,
    betti_curve,
    bottleneck_distance,
    persistence_entropy,
    persistent_cohomology,
    persistent_homology,
)
from algebrax.topology.sheaf import (
    CellStalkCoord,
    CellularSheaf,
    ConstantSheaf,
    EdgeStalkCoord,
    FunctorialSheaf,
    RestrictionMap,
    StalkCoord,
    build_sheaf_coboundary_matrix,
    build_sheaf_laplacian,
    sheaf_diffusion,
    sheaf_harmonic_extension,
    sheaf_laplacian,
)

__all__ = [
    'CellStalkCoord',
    'CellularSheaf',
    'Cochain',
    'CochainAlgebra',
    'ConstantSheaf',
    'DiscreteConnection',
    'DiscreteForm',
    'DiscreteOrthogonalConnection',
    'EdgeStalkCoord',
    'FilteredSimplicialComplex',
    'FunctorialSheaf',
    'HodgeDecomposition',
    'PersistenceInterval',
    'RestrictionMap',
    'SimplicialChainCoalgebra',
    'SimplicialComplex',
    'SparseChainComplex',
    'StalkCoord',
    'TopologicalKTheoryRing',
    'apply_gauge_transformation',
    'betti_curve',
    'bottleneck_distance',
    'build_connection_laplacian',
    'build_sheaf_coboundary_matrix',
    'build_sheaf_laplacian',
    'bundle',
    'bundle_direct_sum',
    'bundle_tensor_product',
    'canonicalize_form',
    'cap_product',
    'chern_character',
    'coalgebra',
    'coboundary',
    'cochain_to_flow',
    'codifferential',
    'cohomology',
    'cohomology_rank',
    'compute_chern_character_1',
    'compute_chern_character_2',
    'compute_face_curvature_angle',
    'compute_face_holonomy',
    'covariant_exterior_derivative',
    'cup_product',
    'dec',
    'exterior_derivative',
    'first_chern_number',
    'flow_to_cochain',
    'helmholtz_hodge_decomposition',
    'hodge_laplacian',
    'hodge_star',
    'homology',
    'is_flat_bundle',
    'k_theory',
    'persistence',
    'persistence_entropy',
    'persistent_cohomology',
    'persistent_homology',
    'sheaf',
    'sheaf_diffusion',
    'sheaf_harmonic_extension',
    'sheaf_laplacian',
    'trivial_bundle',
]

