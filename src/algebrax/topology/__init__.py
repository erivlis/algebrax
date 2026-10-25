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

from algebrax.topology import cohomology, dec, homology, persistence, sheaf
from algebrax.topology.cohomology import (
    Cochain,
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
    CellularSheaf,
    EdgeStalkCoord,
    RestrictionMap,
    StalkCoord,
    sheaf_diffusion,
    sheaf_harmonic_extension,
    sheaf_laplacian,
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
    'betti_curve',
    'bottleneck_distance',
    'canonicalize_form',
    'cap_product',
    'coboundary',
    'cochain_to_flow',
    'codifferential',
    'cohomology',
    'cohomology_rank',
    'cup_product',
    'dec',
    'exterior_derivative',
    'flow_to_cochain',
    'helmholtz_hodge_decomposition',
    'hodge_laplacian',
    'hodge_star',
    'homology',
    'persistence',
    'persistence_entropy',
    'persistent_cohomology',
    'persistent_homology',
    'sheaf',
    'sheaf_diffusion',
    'sheaf_harmonic_extension',
    'sheaf_laplacian',
]
