"""
Continuous symmetry generators, Lie algebras, root systems, and BCH dynamics.

Summary:
    Finite-dimensional Lie algebras (g) equipped with alternating bilinear brackets,
    structure constants tensors, adjoint representations, Killing forms,
    Baker-Campbell-Hausdorff series, and crystallographic root systems.

Modules:
    - core: LieAlgebra carrier, StructureConstants, and BCH solver.
    - classical: Generalized classical matrix families (so_n, su_n, u_n, sp_n, sl_n, se_n, clifford).
    - roots: RootSystem, Weyl reflections, Euclidean embeddings, and ASCII Dynkin diagrams.
    - exceptional: Exceptional Lie algebras (g2, f4, e6, e7, e8).
"""

from algebrax.lie.classical import (
    clifford_lie_algebra,
    se_n,
    sl_n,
    so_n,
    sp_n,
    su_n,
    u_n,
)
from algebrax.lie.core import (
    ConvergenceWarning,
    LieAlgebra,
    LieElement,
    StructureConstants,
)
from algebrax.lie.exceptional import (
    e6,
    e7,
    e8,
    f4,
    g2,
)
from algebrax.lie.roots import (
    RootSystem,
    chevalley_lie_algebra,
)

__all__ = [
    'ConvergenceWarning',
    'LieAlgebra',
    'LieElement',
    'RootSystem',
    'StructureConstants',
    'chevalley_lie_algebra',
    'clifford_lie_algebra',
    'e6',
    'e7',
    'e8',
    'f4',
    'g2',
    'se_n',
    'sl_n',
    'so_n',
    'sp_n',
    'su_n',
    'u_n',
]
