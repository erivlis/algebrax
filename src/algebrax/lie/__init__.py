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

from typing import TYPE_CHECKING, Any

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
from algebrax.lie.langlands import (
    IwahoriHeckeAlgebra,
    coroot_in_dual,
    langlands_dual_root_system,
    root_inner_product,
)
from algebrax.lie.roots import (
    RootSystem,
    chevalley_lie_algebra,
)

if TYPE_CHECKING:
    from algebrax.rep.lie import (
        adjoint_representation,
        defining_representation,
        quadratic_casimir,
        spin_representation,
    )

_REP_LIE_EXPORTS = frozenset({
    'adjoint_representation',
    'defining_representation',
    'quadratic_casimir',
    'spin_representation',
})


def __getattr__(name: str) -> Any:
    if name in _REP_LIE_EXPORTS:
        from algebrax.rep import lie as _rep_lie

        return getattr(_rep_lie, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


__all__ = [
    'ConvergenceWarning',
    'IwahoriHeckeAlgebra',
    'LieAlgebra',
    'LieElement',
    'RootSystem',
    'StructureConstants',
    'adjoint_representation',
    'chevalley_lie_algebra',
    'clifford_lie_algebra',
    'coroot_in_dual',
    'defining_representation',
    'e6',
    'e7',
    'e8',
    'f4',
    'g2',
    'langlands_dual_root_system',
    'quadratic_casimir',
    'root_inner_product',
    'se_n',
    'sl_n',
    'so_n',
    'sp_n',
    'spin_representation',
    'su_n',
    'u_n',
]
