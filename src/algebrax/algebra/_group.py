r"""
Group protocols for single-operation algebraic structures with two-sided inverses.

Algebraic Signatures:
    Group:                       $\langle V, \mathbf{1}, \cdot, ^{-1} \rangle$
                                 with $a \cdot a^{-1} = a^{-1} \cdot a = \mathbf{1}$
    Commutative Group (Abelian): $\langle V, \mathbf{1}, \cdot, ^{-1} \rangle$ with $a \cdot b = b \cdot a$
    Additive Group:              $\langle V, \mathbf{0}, +, - \rangle$ with $a + (-a) = (-a) + a = \mathbf{0}$
    Additive Commutative Group:  $\langle V, \mathbf{0}, +, - \rangle$ with $a + b = b + a$
    Group Action:                $\cdot: G \times X \to X$ with $g \cdot (h \cdot x) = (g h) \cdot x$
                                 and $\mathbf{1} \cdot x = x$
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import HasAdd, HasInv, HasMul, HasNeg, HasOne, HasZero

G = TypeVar('G')
V = TypeVar('V')
X = TypeVar('X')


@runtime_checkable
class Group(HasOne[V], HasMul[V], HasInv[V], Protocol):
    r"""A monoid where every element possesses a two-sided multiplicative inverse $a^{-1}$.

    Algebraic Signature:
        $\langle V, \mathbf{1}, \cdot, ^{-1} \rangle, \quad a \cdot a^{-1} = a^{-1} \cdot a = \mathbf{1}$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `one`: Neutral group identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative group multiplication (`HasMul[V]`).
        - `inv(a)`: Multiplicative two-sided inverse $a^{-1}$ (`HasInv[V]`).
        - `div(a, b)`: Derived quotient $a \cdot b^{-1}$ (`HasInv[V]`).

    Properties:
        - Invertibility: $\forall a \in V, \ a \cdot a^{-1} = a^{-1} \cdot a = \mathbf{1}$.
        - Quotient Duality: $a / b = a \cdot b^{-1}$.

    Applications:
        Discrete and continuous symmetries, permutation groups, geometric rotations, ciphers, reversible computing.
    """

    ...


@runtime_checkable
class CommGroup(HasOne[V], HasMul[V], HasInv[V], Protocol):
    r"""An abelian group satisfying commutativity: $a \cdot b = b \cdot a$.

    Algebraic Signature:
        $\langle V, \mathbf{1}, \cdot, ^{-1} \rangle$ with $a \cdot b = b \cdot a$

    Operations:
        - `one`: Neutral group identity element (`HasOne[V]`).
        - `mul(a, b)`: Commutative, associative multiplication (`HasMul[V]`).
        - `inv(a)`: Multiplicative two-sided inverse $a^{-1}$ (`HasInv[V]`).
        - `div(a, b)`: Derived quotient $a \cdot b^{-1}$ (`HasInv[V]`).
    """

    ...


AbelianGroup = CommGroup  # Canonical alias


# --- Additive Dual Branch ---


@runtime_checkable
class AddGroup(HasZero[V], HasAdd[V], HasNeg[V], Protocol):
    r"""An additive monoid where every element possesses an additive inverse (negation) $-a$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, - \rangle, \quad a + (-a) = (-a) + a = \mathbf{0}$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Associative addition (`HasAdd[V]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[V]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[V]`).
    """

    ...


@runtime_checkable
class AddCommGroup(HasZero[V], HasAdd[V], HasNeg[V], Protocol):
    r"""An additive abelian group satisfying commutativity: $a + b = b + a$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, - \rangle$ with $a + b = b + a$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[V]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[V]`).
    """

    ...


# --- Group Action Protocol ---


@runtime_checkable
class GroupAction(Protocol[G, X]):
    r"""Group $G$ acting on a set $X$ via a left action: $\cdot: G \times X \to X$.

    Algebraic Signature:
        $\langle G, X, \operatorname{gact} \rangle$
        with $g \cdot (h \cdot x) = (g h) \cdot x$ and $\mathbf{1}_G \cdot x = x$

    Operations:
        - `gact(g, x)`: Left action of $g \in G$ on $x \in X$.
    """

    def gact(self, g: G, x: X) -> X: ...
