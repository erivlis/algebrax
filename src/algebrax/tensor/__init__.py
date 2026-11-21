"""
Tensor algebra, Einstein summation, and sparse angular momentum coupling tensors.

Re-exports arbitrary-rank sparse tensor contractions (`einsum`, `outer_product`, `dot`,
`flatten_tensor`, `unflatten_tensor`, `permute_tensor`, `unpermute_tensor`) alongside
sparse Clebsch-Gordan coupling 3-tensors (`clebsch_gordan_coefficient`,
`clebsch_gordan_tensor`, `clebsch_gordan_matrix`).
"""

from algebrax.tensor import core, coupling
from algebrax.tensor.core import (
    dot,
    einsum,
    flatten_tensor,
    outer_product,
    permute_tensor,
    unflatten_tensor,
    unpermute_tensor,
)
from algebrax.tensor.coupling import (
    clebsch_gordan_coefficient,
    clebsch_gordan_matrix,
    clebsch_gordan_tensor,
)

__all__ = [
    'clebsch_gordan_coefficient',
    'clebsch_gordan_matrix',
    'clebsch_gordan_tensor',
    'core',
    'coupling',
    'dot',
    'einsum',
    'flatten_tensor',
    'outer_product',
    'permute_tensor',
    'unflatten_tensor',
    'unpermute_tensor',
]
