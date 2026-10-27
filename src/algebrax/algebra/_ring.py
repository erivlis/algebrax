r"""
Ring protocols for two-operation algebraic structures with additive inverses.

Algebraic Signatures (EP-0150 AMDS):
    Non-Associative Ring: $\langle R, +, \cdot, \mathbf{0}, - \rangle$
    Ring:                 $\langle R, +, \cdot, \mathbf{0}, \mathbf{1}, - \rangle$
    Commutative Ring:     $\langle R, +, \cdot, \mathbf{0}, \mathbf{1}, - \rangle$ with $a \cdot b = b \cdot a$
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._group import AddCommGroup
from algebrax.algebra._magma import Magma
from algebrax.algebra._monoid import Monoid

V = TypeVar('V')


@runtime_checkable
class NonAssocRing(AddCommGroup[V], Magma[V], Protocol[V]):
    r"""Carrier set equipped with abelian addition and possibly non-associative distributive multiplication.

    Algebraic Signature:
        $\langle R, +, \cdot, \mathbf{0}, - \rangle$

    Properties:
        - Additive Abelian Group: $\langle R, +, \mathbf{0}, - \rangle$.
        - Magma Multiplication: $\cdot: R \times R \to R$.
        - Left Distributivity: $a \cdot (b + c) = (a \cdot b) + (a \cdot c)$.
        - Right Distributivity: $(a + b) \cdot c = (a \cdot c) + (b \cdot c)$.

    Applications:
        Lie algebras (with Lie bracket $[x, y]$), Jordan algebras, octonions.
    """

    ...


@runtime_checkable
class Ring(NonAssocRing[V], Monoid[V], Protocol[V]):
    r"""An associative unital ring $\langle R, +, \cdot, \mathbf{0}, \mathbf{1}, - \rangle$.

    Combines an additive abelian group $\langle R, +, \mathbf{0}, - \rangle$
    and a multiplicative monoid $\langle R, \cdot, \mathbf{1} \rangle$ satisfying two-sided distributivity.

    Algebraic Signature:
        $\langle R, +, \cdot, \mathbf{0}, \mathbf{1}, - \rangle$

    Operations:
        - `add(a, b)`: Commutative, associative addition.
        - `zero`: Additive neutral element ($\mathbf{0}$).
        - `neg(a)`: Additive inverse ($-a$).
        - `sub(a, b)`: Difference $a - b = a + (-b)$.
        - `mul(a, b)`: Associative multiplication.
        - `one`: Multiplicative identity element ($\mathbf{1}$).

    Applications:
        Polynomial rings $R[x]$, matrix rings $M_n(R)$, integer arithmetic $\mathbb{Z}$, Clifford algebras.
    """

    ...


@runtime_checkable
class CommRing(Ring[V], Protocol[V]):
    r"""A commutative ring whose multiplication is commutative: $a \cdot b = b \cdot a$.

    Algebraic Signature:
        $\langle R, +, \cdot, \mathbf{0}, \mathbf{1}, - \rangle$ with $a \cdot b = b \cdot a$
    """

    ...


AbelianRing = CommRing
CommutativeRing = CommRing  # Canonical alias



@runtime_checkable
class DivisionRing(Ring[V], Protocol[V]):
    r"""A unital ring where every non-zero element has a two-sided multiplicative inverse.

    Note: Following Emmy Noether's guidance, `DivisionRing` inherits from `Ring`,
    *not* from `Group`, because the additive neutral element $\mathbf{0}$ has no
    multiplicative inverse. Its non-zero elements form the multiplicative group of units:
    $D^\times = D \setminus \{\mathbf{0}\}$.

    Algebraic Signature:
        $\langle D, +, \cdot, \mathbf{0}, \mathbf{1}, -, ^{-1} \rangle$

    Operations:
        - `inv(a)`: Multiplicative inverse $a^{-1}$ for $a \ne \mathbf{0}$.
        - `div(a, b)`: Quotient $a \cdot b^{-1}$ for $b \ne \mathbf{0}$.
        - `is_zero(a)`: Test whether $a == \mathbf{0}$.

    Contracts:
        - If `is_zero(b)` is true, `div(a, b)` and `inv(b)` MUST raise `ZeroDivisionError`.
    """

    def inv(self, a: V) -> V:
        r"""Compute multiplicative inverse $a^{-1}$."""
        ...

    def div(self, a: V, b: V) -> V:
        r"""Compute quotient $a \cdot b^{-1}$."""
        return self.mul(a, self.inv(b))

    def is_zero(self, a: V) -> bool:
        """Return True if element is the additive zero."""
        return a == self.zero


__all__ = [
    'CommRing',
    'CommutativeRing',
    'DivisionRing',
    'NonAssocRing',
    'Ring',
]

