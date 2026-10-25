r"""
Group protocols for single-operation algebraic structures with two-sided inverses.

Algebraic Signatures (EP-0150 AMDS):
    Group:            $\langle G, \cdot, \mathbf{1}, ^{-1} \rangle$ with $a \cdot a^{-1} = a^{-1} \cdot a = \mathbf{1}$
    Commutative Group (Abelian): $\langle G, \cdot, \mathbf{1}, ^{-1} \rangle$ with $a \cdot b = b \cdot a$
    Additive Group:   $\langle G, +, \mathbf{0}, - \rangle$ with $a + (-a) = (-a) + a = \mathbf{0}$
    Group Action:     $\cdot: G \times X \to X$ with $g \cdot (h \cdot x) = (g h) \cdot x$ and $\mathbf{1} \cdot x = x$
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._monoid import AddCommMonoid, AddMonoid, CommMonoid, Monoid

G = TypeVar('G')
V = TypeVar('V')
X = TypeVar('X')


@runtime_checkable
class Group(Monoid[V], Protocol[V]):
    r"""A monoid where every element possesses a two-sided multiplicative inverse $a^{-1}$.

    Algebraic Signature:
        $\langle G, \cdot, \mathbf{1}, ^{-1} \rangle, \quad a \cdot a^{-1} = a^{-1} \cdot a = \mathbf{1}$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `mul(a, b)`: Associative group multiplication.
        - `one`: Neutral group identity element.
        - `inv(a)`: Multiplicative two-sided inverse $a^{-1}$.
        - `div(a, b)`: Quotient $a \cdot b^{-1}$.

    Properties:
        - Invertibility: $\forall a \in G, \ a \cdot a^{-1} = a^{-1} \cdot a = \mathbf{1}$.
        - Quotient Duality: $a / b = a \cdot b^{-1}$.

    Applications:
        Discrete and continuous symmetries, permutation groups, geometric rotations, ciphers, reversible computing.
    """

    def inv(self, a: V) -> V: ...

    def div(self, a: V, b: V) -> V:
        """Quotient a / b = a * inv(b)."""
        return self.mul(a, self.inv(b))


@runtime_checkable
class CommGroup(Group[V], CommMonoid[V], Protocol[V]):
    r"""An abelian group satisfying commutativity: $a \cdot b = b \cdot a$.

    Algebraic Signature:
        $\langle G, \cdot, \mathbf{1}, ^{-1} \rangle$ with $a \cdot b = b \cdot a$
    """

    ...


AbelianGroup = CommGroup  # Canonical alias


# --- Additive Dual Branch ---


@runtime_checkable
class AddGroup(AddMonoid[V], Protocol[V]):
    r"""An additive monoid where every element possesses an additive inverse (negation) $-a$.

    Algebraic Signature:
        $\langle G, +, \mathbf{0}, - \rangle, \quad a + (-a) = (-a) + a = \mathbf{0}$
    """

    def neg(self, a: V) -> V: ...

    def sub(self, a: V, b: V) -> V:
        """Difference a - b = a + neg(b)."""
        return self.add(a, self.neg(b))


@runtime_checkable
class AddCommGroup(AddGroup[V], AddCommMonoid[V], Protocol[V]):
    r"""An additive abelian group satisfying commutativity: $a + b = b + a$.

    Algebraic Signature:
        $\langle G, +, \mathbf{0}, - \rangle$ with $a + b = b + a$
    """

    ...


# --- Group Action Protocol ---


@runtime_checkable
class GroupAction(Protocol[G, X]):
    r"""Group $G$ acting on a set $X$ via a left action: $\cdot: G \times X \to X$.

    Algebraic Signature:
        $\cdot: G \times X \to X, \quad g \cdot (h \cdot x) = (g h) \cdot x, \quad \mathbf{1}_G \cdot x = x$
    """

    def gact(self, g: G, x: X) -> X: ...
