r"""
Module, VectorSpace, and Algebra protocols for two-sorted algebraic structures.

Algebraic Signatures:
    Semimodule:          $\langle R, M, \cdot_s, \mathbf{0}, + \rangle$ where $R$ is a Semiring
    Module:              $\langle R, M, \cdot_s, \mathbf{0}, +, - \rangle$ where $R$ is a Ring
    Vector Space:        $\langle R, M, \cdot_s, \mathbf{0}, +, - \rangle$ where $R$ is a Field
    Non-Assoc Algebra:   $\langle R, M, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$
                         where $M$ is an $R$-module and non-associative ring
    Associative Algebra: $\langle R, M, \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$
                         where $M$ is an associative unital ring and $R$-module
"""

from typing import Literal, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import (
    HasAdd,
    HasMul,
    HasNeg,
    HasOne,
    HasScale,
    HasZero,
    LawAssociative,
)

R = TypeVar('R')
M = TypeVar('M')


@runtime_checkable
class Semimodule(HasScale[R, M], HasZero[M], HasAdd[M], Protocol[R, M]):
    r"""A commutative additive monoid $M$ with external scalar action by a semiring $R$: $R \times M \to M$.

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, + \rangle$

    Operations:
        - `smul(r, m)`: External scalar multiplication $r \cdot_s m$ (`HasScale[R, M]`).
        - `zero`: Additive neutral element $\mathbf{0}_M$ (`HasZero[M]`).
        - `add(a, b)`: Commutative, associative addition on $M$ (`HasAdd[M]`).

    Properties:
        - Additive Commutative Monoid on $M$: $\langle M, \mathbf{0}, + \rangle$.
        - Left Distributivity: $r \cdot_s (m_1 + m_2) = (r \cdot_s m_1) + (r \cdot_s m_2)$.
        - Right Distributivity: $(r_1 + r_2) \cdot_s m = (r_1 \cdot_s m) + (r_2 \cdot_s m)$.
        - Scalar Associativity: $(r_1 \cdot r_2) \cdot_s m = r_1 \cdot_s (r_2 \cdot_s m)$.
        - Scalar Identity: $\mathbf{1}_R \cdot_s m = m$.
        - Zero Annihilation: $\mathbf{0}_R \cdot_s m = \mathbf{0}_M$ and $r \cdot_s \mathbf{0}_M = \mathbf{0}_M$.
    """

    ...


@runtime_checkable
class Module(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], Protocol[R, M]):
    r"""An additive abelian group $M$ equipped with external scalar action by a ring $R$.

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, +, - \rangle$

    Operations:
        - `smul(r, m)`: External scalar multiplication $r \cdot_s m$ (`HasScale[R, M]`).
        - `zero`: Additive neutral element $\mathbf{0}_M$ (`HasZero[M]`).
        - `add(a, b)`: Commutative, associative addition on $M$ (`HasAdd[M]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[M]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[M]`).

    Applications:
        Free modules over commutative rings, sparse integer vectors $\mathbb{Z}^n$, homology chain groups $C_k(K, R)$.
    """

    ...


@runtime_checkable
class VectorSpace(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], Protocol[R, M]):
    r"""A module $M$ over a field $R$ (scalars form a Field).

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, +, - \rangle$

    Operations:
        - `smul(r, m)`: External scalar multiplication $r \cdot_s m$ (`HasScale[R, M]`).
        - `zero`: Zero vector $\mathbf{0}_M$ (`HasZero[M]`).
        - `add(a, b)`: Vector addition (`HasAdd[M]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[M]`).
        - `sub(a, b)`: Derived vector subtraction $a - b$ (`HasNeg[M]`).

    Applications:
        Classical linear algebra, coordinate-sparse vectors $\mathbb{R}^n$, differential 1-forms, tangent spaces.
    """

    ...


@runtime_checkable
class NonAssocAlgebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M]):
    r"""An $R$-module $M$ equipped with a bilinear (possibly non-associative) multiplication.

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$

    Operations:
        - `smul(r, m)`: External scalar multiplication $r \cdot_s m$ (`HasScale[R, M]`).
        - `zero`: Additive neutral element $\mathbf{0}_M$ (`HasZero[M]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[M]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[M]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[M]`).
        - `mul(a, b)`: Bilinear algebra product $a \cdot b$ (`HasMul[M]`).

    Properties:
        - Bilinearity: $r \cdot_s (a \cdot b) = (r \cdot_s a) \cdot b = a \cdot (r \cdot_s b)$.

    Applications:
        Lie algebras $\mathfrak{g}$ (where bracket $[x, y]$ is bilinear), Jordan algebras, octonions $\mathbb{O}$.
    """

    ...


@runtime_checkable
class Algebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasOne[M], HasMul[M], LawAssociative, Protocol[R, M]):
    r"""An associative unital ring $M$ equipped with a compatible $R$-module scalar action.

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$

    Operations:
        - `smul(r, m)`: External scalar multiplication $r \cdot_s m$ (`HasScale[R, M]`).
        - `zero`: Additive neutral element $\mathbf{0}_M$ (`HasZero[M]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[M]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[M]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[M]`).
        - `one`: Multiplicative identity element $\mathbf{1}_M$ (`HasOne[M]`).
        - `mul(a, b)`: Associative bilinear multiplication $a \cdot b$ (`HasMul[M]`).

    Applications:
        Matrix algebras $M_n(F)$, group algebras $F[G]$, monoid algebras, Clifford geometric algebras.
    """

    @property
    def is_associative(self) -> Literal[True]:
        return True
