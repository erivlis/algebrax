r"""
Module, VectorSpace, and Algebra protocols for two-sorted algebraic structures.

Algebraic Signatures (EP-0150 AMDS):
    Semimodule:          $\langle M, R, +, \mathbf{0}, \cdot \rangle$ where $R$ is a Semiring
    Module:              $\langle M, R, +, \mathbf{0}, -, \cdot \rangle$ where $R$ is a Ring and $M$ is an AddCommGroup
    Vector Space:        $\langle V, F, +, \mathbf{0}, -, \cdot \rangle$ where $F$ is a Field
    Non-Assoc Algebra:   $\langle A, R, +, \mathbf{0}, -, \cdot, \times \rangle$
                         where $A$ is an $R$-module and non-associative ring
    Associative Algebra: $\langle A, R, +, \mathbf{0}, -, \cdot, \times, \mathbf{1} \rangle$
                         where $A$ is an associative ring and $R$-module
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._group import AddCommGroup
from algebrax.algebra._monoid import AddCommMonoid
from algebrax.algebra._ring import NonAssocRing, Ring

R = TypeVar('R')
M = TypeVar('M')


@runtime_checkable
class Semimodule(AddCommMonoid[M], Protocol[R, M]):
    r"""A commutative additive monoid $M$ with scalar action by a semiring $R$: $R \times M \to M$.

    Algebraic Signature:
        $\langle M, R, +, \mathbf{0}, \cdot \rangle$

    Properties:
        - Additive Commutative Monoid on $M$.
        - Left Distributivity: $r \cdot (m_1 + m_2) = (r \cdot m_1) + (r \cdot m_2)$.
        - Right Distributivity: $(r_1 + r_2) \cdot m = (r_1 \cdot m) + (r_2 \cdot m)$.
        - Scalar Associativity: $(r_1 \cdot r_2) \cdot m = r_1 \cdot (r_2 \cdot m)$.
        - Scalar Identity: $\mathbf{1}_R \cdot m = m$.
        - Zero Annihilation: $\mathbf{0}_R \cdot m = \mathbf{0}_M$ and $r \cdot \mathbf{0}_M = \mathbf{0}_M$.
    """

    def smul(self, r: R, m: M) -> M:
        r"""Scalar multiplication $r \cdot m \in M$."""
        ...


@runtime_checkable
class Module(Semimodule[R, M], AddCommGroup[M], Protocol[R, M]):
    r"""An additive abelian group $M$ equipped with scalar action by a ring $R$.

    Algebraic Signature:
        $\langle M, R, +, \mathbf{0}, -, \cdot \rangle$

    Applications:
        Free modules over commutative rings, sparse integer vectors $\mathbb{Z}^n$, homology chain groups $C_k(K, R)$.
    """

    ...


@runtime_checkable
class VectorSpace(Module[R, M], Protocol[R, M]):
    r"""A module $M$ over a field $R$ (scalars form a Field).

    Algebraic Signature:
        $\langle V, F, +, \mathbf{0}, -, \cdot \rangle$

    Applications:
        Classical linear algebra, coordinate-sparse vectors $\mathbb{R}^n$, differential 1-forms, tangent spaces.
    """

    ...


@runtime_checkable
class NonAssocAlgebra(Module[R, M], NonAssocRing[M], Protocol[R, M]):
    r"""A module $M$ that is also a non-associative ring satisfying scalar bilinearity.

    Properties:
        - Bilinearity: $r \cdot (a \cdot b) = (r \cdot a) \cdot b = a \cdot (r \cdot b)$.

    Applications:
        Lie algebras $\mathfrak{g}$ (where bracket $[x, y]$ is bilinear), Jordan algebras, octonions $\mathbb{O}$.
    """

    ...


@runtime_checkable
class Algebra(NonAssocAlgebra[R, M], Ring[M], Protocol[R, M]):
    r"""An associative unital ring $M$ that is also an $R$-module satisfying bilinearity.

    Algebraic Signature:
        $\langle A, R, +, \mathbf{0}, -, \cdot, \times, \mathbf{1} \rangle$

    Applications:
        Matrix algebras $M_n(F)$, group algebras $F[G]$, monoid algebras, Clifford geometric algebras.
    """

    ...
