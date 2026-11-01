r"""
Ring protocols for two-operation algebraic structures with additive inverses.

Algebraic Signatures:
    Non-Associative Ring: $\langle V, \mathbf{0}, +, -, \cdot \rangle$
    Ring:                 $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$
    Commutative Ring:     $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ with $a \cdot b = b \cdot a$
    Division Ring:        $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, ^{-1} \rangle$
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import HasAdd, HasInv, HasMul, HasNeg, HasOne, HasZero, HasZeroPred

V = TypeVar('V')


@runtime_checkable
class NonAssocRing(HasZero[V], HasAdd[V], HasNeg[V], HasMul[V], Protocol):
    r"""Carrier set equipped with abelian addition and possibly non-associative distributive multiplication.

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, -, \cdot \rangle$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[V]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[V]`).
        - `mul(a, b)`: Distributive multiplication (`HasMul[V]`).

    Properties:
        - Additive Abelian Group: $\langle V, \mathbf{0}, +, - \rangle$.
        - Magma Multiplication: $\cdot: V \times V \to V$.
        - Left Distributivity: $a \cdot (b + c) = (a \cdot b) + (a \cdot c)$.
        - Right Distributivity: $(a + b) \cdot c = (a \cdot c) + (b \cdot c)$.

    Applications:
        Lie algebras (with Lie bracket $[x, y]$), Jordan algebras, octonions.
    """

    ...


@runtime_checkable
class Ring(HasZero[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], Protocol):
    r"""An associative unital ring $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$.

    Combines an additive abelian group $\langle V, \mathbf{0}, +, - \rangle$
    and a multiplicative monoid $\langle V, \mathbf{1}, \cdot \rangle$ satisfying two-sided distributivity.

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[V]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative multiplication (`HasMul[V]`).

    Applications:
        Polynomial rings $R[x]$, matrix rings $M_n(R)$, integer arithmetic $\mathbb{Z}$, Clifford algebras.
    """

    ...


@runtime_checkable
class CommRing(HasZero[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], Protocol):
    r"""A commutative ring whose multiplication is commutative: $a \cdot b = b \cdot a$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ with $a \cdot b = b \cdot a$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[V]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Commutative, associative multiplication (`HasMul[V]`).
    """

    ...


AbelianRing = CommRing
CommutativeRing = CommRing  # Canonical alias


@runtime_checkable
class DivisionRing(HasZero[V], HasZeroPred[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], HasInv[V], Protocol):
    r"""A unital ring where every non-zero element has a two-sided multiplicative inverse.

    Note: The additive neutral element $\mathbf{0}$ has no multiplicative inverse.
    Its non-zero elements form the multiplicative group of units:
    $D^\times = V \setminus \{\mathbf{0}\}$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, ^{-1} \rangle$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `is_zero(a)`: Test whether $a == \mathbf{0}$ (`HasZeroPred[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[V]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative multiplication (`HasMul[V]`).
        - `inv(a)`: Multiplicative inverse $a^{-1}$ for $a \ne \mathbf{0}$ (`HasInv[V]`).
        - `div(a, b)`: Derived quotient $a \cdot b^{-1}$ for $b \ne \mathbf{0}$ (`HasInv[V]`).

    Contracts:
        - If `is_zero(b)` is true, `div(a, b)` and `inv(b)` MUST raise `ZeroDivisionError`.
    """

    ...


__all__ = [
    'AbelianRing',
    'CommRing',
    'CommutativeRing',
    'DivisionRing',
    'NonAssocRing',
    'Ring',
]
