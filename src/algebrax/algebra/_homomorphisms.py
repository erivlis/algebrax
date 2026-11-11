r"""
Algebraic homomorphisms (structure-preserving maps) between algebraic structures.

Algebraic Signatures (EP-0201 / EP-0150 AMDS):
    Homomorphism:     $\phi: \mathrm{Dom} \to \mathrm{Cod}$
    GroupHom:         $\phi(a \cdot b) = \phi(a) \cdot \phi(b), \quad \phi(e) = e$
    RingHom:          $\phi(a + b) = \phi(a) + \phi(b), \; \phi(a b) = \phi(a)\phi(b), \; \phi(0)=0, \; \phi(1)=1$
    LinearMap:        $\phi(u + v) = \phi(u) + \phi(v), \quad \phi(c \cdot v) = c \cdot \phi(v)$
    LieAlgebraHom:    $\phi([x, y]) = [\phi(x), \phi(y)]$
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, Protocol, TypeVar, runtime_checkable

R = TypeVar('R')
Dom = TypeVar('Dom', contravariant=True)
Cod = TypeVar('Cod', covariant=True)
K = TypeVar('K')
V = TypeVar('V')
W = TypeVar('W')


@runtime_checkable
class Homomorphism(Protocol[Dom, Cod]):
    r"""Base protocol for a mathematical homomorphism $\phi: \mathrm{Dom} \to \mathrm{Cod}$.

    Any callable object or function mapping elements of the domain carrier to the
    codomain carrier satisfies this structural protocol.
    """

    def __call__(self, x: Dom) -> Cod:
        """Apply the homomorphism to an element of the domain."""
        ...


@runtime_checkable
class GroupHom(Protocol[Dom, Cod]):
    r"""A group homomorphism $\phi: G_1 \to G_2$.

    Algebraic Laws:
        - Operation Preservation: $\phi(a \cdot b) = \phi(a) \cdot \phi(b)$
        - Identity Preservation: $\phi(e_{G_1}) = e_{G_2}$
        - Inverse Preservation: $\phi(a^{-1}) = \phi(a)^{-1}$
    """

    def __call__(self, x: Dom) -> Cod:
        """Apply the group homomorphism to an element of the domain group."""
        ...


@runtime_checkable
class RingHom(Protocol[Dom, Cod]):
    r"""A unital ring homomorphism $\phi: R_1 \to R_2$.

    Algebraic Laws:
        - Addition Preservation: $\phi(a + b) = \phi(a) + \phi(b)$
        - Multiplication Preservation: $\phi(a \cdot b) = \phi(a) \cdot \phi(b)$
        - Zero Preservation: $\phi(\mathbf{0}_{R_1}) = \mathbf{0}_{R_2}$
        - One Preservation: $\phi(\mathbf{1}_{R_1}) = \mathbf{1}_{R_2}$
    """

    def __call__(self, x: Dom) -> Cod:
        """Apply the ring homomorphism to an element of the domain ring."""
        ...


@runtime_checkable
class LinearMap(Protocol[R, Dom, Cod]):
    r"""A module or vector-space linear map $\phi: V \to W$ over scalar ring/field $R$.

    Algebraic Laws:
        - Additivity: $\phi(u + v) = \phi(u) + \phi(v)$
        - Homogeneity (Scalar Equivariance): $\phi(r \cdot_s v) = r \cdot_s \phi(v)$
    """

    def __call__(self, x: Dom) -> Cod:
        """Apply the linear map to a vector/module element of the domain."""
        ...


@runtime_checkable
class LieAlgebraHom(Protocol[Dom, Cod]):
    r"""A Lie algebra homomorphism $\phi: \mathfrak{g}_1 \to \mathfrak{g}_2$.

    Algebraic Laws:
        - Linearity: $\phi(u + v) = \phi(u) + \phi(v)$ and $\phi(c \cdot v) = c \cdot \phi(v)$
        - Bracket Preservation: $\phi([x, y]_{\mathfrak{g}_1}) = [\phi(x), \phi(y)]_{\mathfrak{g}_2}$
    """

    def __call__(self, x: Dom) -> Cod:
        """Apply the Lie algebra homomorphism to a Lie element."""
        ...


class CallableHomomorphism(Homomorphism[V, W], Generic[V, W]):
    r"""Lightweight wrapper turning any `Callable[[V], W]` into an explicit homomorphism with composition."""

    def __init__(self, fn: Callable[[V], W]) -> None:
        self._fn = fn

    def __call__(self, x: V) -> W:
        return self._fn(x)

    def compose(self, other: Homomorphism[K, V]) -> CallableHomomorphism[K, W]:
        r"""Compose homomorphisms: $(\mathrm{self} \circ \mathrm{other})(x) = \mathrm{self}(\mathrm{other}(x))$."""
        return CallableHomomorphism(lambda x: self._fn(other(x)))


__all__ = [
    'CallableHomomorphism',
    'GroupHom',
    'Homomorphism',
    'LieAlgebraHom',
    'LinearMap',
    'RingHom',
]
