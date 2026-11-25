r"""
Atomic geometric capability mixins and flat protocols for algebraic and tropical varieties.

Follows the Law of Flat Protocol Composition:
- Layer 1 atomic mixins define single geometric capabilities (`HasPointLocus`,
  `HasDimension`, `HasCoordinateRing`, `HasTangentLocus`).
- Layer 2 protocols compose Layer 1 mixins flatly with zero Layer-2-to-Layer-2 inheritance
  (`GeometricVariety`, `SmoothableVariety`).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra import GroebnerIdeal, QuotientRing, SparseMPoly
from algebrax.typing import SparseMatrix

P = TypeVar('P')
V = TypeVar('V')


@runtime_checkable
class HasPointLocus(Protocol[P]):
    r"""Ambient point-membership capability $p \in X \subseteq \mathbb{A}^n$.

    Algebraic Signature:
        $\langle \mathbb{A}^n, X, \operatorname{ambient\_dimension}, \operatorname{contains\_point} \rangle$
    """

    @property
    def ambient_dimension(self) -> int: ...

    def contains_point(self, point: Sequence[P]) -> bool: ...


@runtime_checkable
class HasDimension(Protocol):
    r"""Intrinsic geometric dimension capability $\dim X$ (Krull or polyhedral dimension).

    Algebraic Signature:
        $\langle X, \operatorname{dimension} \rangle$
    """

    def dimension(self) -> int: ...


@runtime_checkable
class HasCoordinateRing(Protocol[V]):
    r"""Noetherian algebra-geometry duality capability pairing $V(I)$ with $I$ and $k[V] = k[X]/I$.

    Algebraic Signature:
        $\langle V(I), I, k[V] \rangle$
    """

    @property
    def ideal(self) -> GroebnerIdeal[V]: ...

    @property
    def coordinate_ring(self) -> QuotientRing[SparseMPoly[V]]: ...


@runtime_checkable
class HasTangentLocus(Protocol[V]):
    r"""Differential-geometric capability providing the Jacobian $J(p)$ and smoothness predicate.

    Algebraic Signature:
        $\langle X, J(p), \operatorname{is\_smooth\_at} \rangle$
    """

    def jacobian_at(self, point: Sequence[V]) -> SparseMatrix[int, V]: ...

    def is_smooth_at(self, point: Sequence[V]) -> bool: ...


# =============================================================================
# Layer 2 Flat Geometric Protocols (Zero Layer-2-to-Layer-2 Inheritance)
# =============================================================================


@runtime_checkable
class GeometricVariety(HasPointLocus[P], HasDimension, Protocol[P]):
    r"""Flat protocol satisfied by both classical `AffineVariety[V]` and tropical varieties.

    Algebraic Signature:
        $\langle \mathbb{A}^n, X, \operatorname{ambient\_dimension},
        \operatorname{contains\_point}, \operatorname{dimension} \rangle$

    Operations:
        - `ambient_dimension`: Ambient affine space dimension $n$ (`HasPointLocus[P]`).
        - `contains_point(point)`: Point-locus membership test $p \in X$ (`HasPointLocus[P]`).
        - `dimension()`: Intrinsic geometric dimension $\dim X$ (`HasDimension`).
    """

    ...


@runtime_checkable
class SmoothableVariety(
    HasPointLocus[V],
    HasDimension,
    HasCoordinateRing[V],
    HasTangentLocus[V],
    Protocol[V],
):
    r"""Flat protocol for algebraic varieties equipped with coordinate rings and Jacobian tangent spaces.

    Algebraic Signature:
        $\langle \mathbb{A}^n, V(I), I, k[V], J(p), \operatorname{is\_smooth\_at}, \operatorname{dimension} \rangle$

    Operations:
        - `ambient_dimension`: Ambient affine space dimension $n$ (`HasPointLocus[V]`).
        - `contains_point(point)`: Point-locus membership test $p \in V(I)$ (`HasPointLocus[V]`).
        - `dimension()`: Intrinsic Krull dimension $\dim V(I)$ (`HasDimension`).
        - `ideal`: Defining Gröbner ideal $I(V)$ (`HasCoordinateRing[V]`).
        - `coordinate_ring`: Quotient coordinate ring $k[V] = k[X]/I$ (`HasCoordinateRing[V]`).
        - `jacobian_at(point)`: Sparse algebraic Jacobian matrix $J(p)$ (`HasTangentLocus[V]`).
        - `is_smooth_at(point)`: Exact local regularity / smoothness test at $p$ (`HasTangentLocus[V]`).
    """

    ...


__all__ = [
    'GeometricVariety',
    'HasCoordinateRing',
    'HasDimension',
    'HasPointLocus',
    'HasTangentLocus',
    'SmoothableVariety',
]
