r"""
Action Algebra protocol and residuated structures (EP-0198).

An Action Algebra \langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^*, \backslash, / \rangle
is a Kleene algebra equipped with left and right residuals (Galois adjoints to multiplication)
satisfying Pratt's equational axiomatization:
    - $a \cdot (a \backslash b) \le b$
    - $b \le a \backslash (a \cdot b)$
    - $(b / a) \cdot a \le b$
    - $b \le (b \cdot a) / a$
    - $(a \backslash a)^* \le a \backslash a$ and $(a / a)^* \le a / a$ (pure induction)
where the natural partial order is $x \le y \iff x + y = y$.
"""

from collections.abc import Iterable
from typing import Generic, Literal, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import (
    HasAdd,
    HasMul,
    HasOne,
    HasPlus,
    HasResiduals,
    HasStar,
    HasZero,
    LawIdempotent,
)

V = TypeVar('V')
T = TypeVar('T')


@runtime_checkable
class ActionAlgebra(
    HasZero[V],
    HasAdd[V],
    HasOne[V],
    HasMul[V],
    HasStar[V],
    HasPlus[V],
    HasResiduals[V],
    LawIdempotent,
    Protocol,
):
    r"""An Action Algebra $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^*, \backslash, / \rangle$.

    An action algebra (Pratt, 1991) is a Kleene algebra equipped with left and right residuals
    satisfying:
        - Left residuation: $a \cdot (a \backslash b) \le b$ and $b \le a \backslash (a \cdot b)$
        - Right residuation: $(b / a) \cdot a \le b$ and $b \le (b \cdot a) / a$
        - Pure induction: $(a \backslash a)^* \le a \backslash a$ and $(a / a)^* \le a / a$

    Operations:
        - `zero`: Additive neutral element ($\mathbf{0}$).
        - `add(a, b)`: Idempotent addition ($a \oplus b$).
        - `one`: Multiplicative identity element ($\mathbf{1}$).
        - `mul(a, b)`: Associative multiplication ($a \cdot b$).
        - `star(a)`: Kleene closure ($a^*$).
        - `plus(a)`: Strict positive iteration ($a^+ = a \cdot a^*$).
        - `ldiv(a, b)`: Left residual ($a \backslash b$).
        - `rdiv(a, b)`: Right residual ($a / b$).
    """

    def plus(self, a: V) -> V:
        r"""Strict positive iteration: $a^+ = a \cdot a^*$.

        In any unital star semiring, $a^+ = a \cdot a^* = a^* \cdot a$.
        """
        return self.mul(a, self.star(a))

    @property
    def is_idempotent(self) -> Literal[True]:
        return True


class RelationActionAlgebra(ActionAlgebra[frozenset[tuple[T, T]]], Generic[T]):
    r"""Concrete Action Algebra of binary relations over a finite domain $T$.

    Elements are binary relations represented as `frozenset[tuple[T, T]]`.
    Operations:
        - $R + S = R \cup S$
        - $R \cdot S = R \circ S = \{(x, z) \mid \exists y: (x, y) \in R, (y, z) \in S\}$
        - $\mathbf{0} = \emptyset$
        - $\mathbf{1} = \{(x, x) \mid x \in \text{domain}\}$
        - $R^* = \bigcup_{k \ge 0} R^k$ (reflexive-transitive closure)
        - $R^+ = R \circ R^*$ (strict transitive closure)
        - $R \backslash S = \{(y, z) \mid \forall x: (x, y) \in R \implies (x, z) \in S\}$
        - $S / R = \{(x, y) \mid \forall z: (y, z) \in R \implies (x, z) \in S\}$
    """

    def __init__(self, domain: Iterable[T]) -> None:
        self.domain: tuple[T, ...] = tuple(domain)

    @property
    def zero(self) -> frozenset[tuple[T, T]]:
        return frozenset()

    @property
    def one(self) -> frozenset[tuple[T, T]]:
        return frozenset((x, x) for x in self.domain)

    def add(
        self,
        a: frozenset[tuple[T, T]],
        b: frozenset[tuple[T, T]],
    ) -> frozenset[tuple[T, T]]:
        return a | b

    def mul(
        self,
        a: frozenset[tuple[T, T]],
        b: frozenset[tuple[T, T]],
    ) -> frozenset[tuple[T, T]]:
        # Index b by first component for fast join
        b_index: dict[T, list[T]] = {}
        for y, z in b:
            b_index.setdefault(y, []).append(z)

        res: set[tuple[T, T]] = set()
        for x, y in a:
            if y in b_index:
                for z in b_index[y]:
                    res.add((x, z))
        return frozenset(res)

    def star(self, a: frozenset[tuple[T, T]]) -> frozenset[tuple[T, T]]:
        curr = self.one | a
        while True:
            nxt = curr | self.mul(curr, a)
            if nxt == curr:
                return curr
            curr = nxt

    def plus(self, a: frozenset[tuple[T, T]]) -> frozenset[tuple[T, T]]:
        curr = a
        while True:
            nxt = curr | self.mul(curr, a)
            if nxt == curr:
                return curr
            curr = nxt

    def ldiv(
        self,
        a: frozenset[tuple[T, T]],
        b: frozenset[tuple[T, T]],
    ) -> frozenset[tuple[T, T]]:
        r"""Left residual $a \backslash b = \{(y, z) \mid \forall x: (x, y) \in a \implies (x, z) \in b\}$."""
        # For each y, find all x such that (x, y) in a
        incoming_a: dict[T, set[T]] = {}
        for x, y in a:
            incoming_a.setdefault(y, set()).add(x)

        # Index b for fast lookup
        b_set = set(b)

        res: set[tuple[T, T]] = set()
        for y in self.domain:
            req_xs = incoming_a.get(y, set())
            for z in self.domain:
                if all((x, z) in b_set for x in req_xs):
                    res.add((y, z))
        return frozenset(res)

    def rdiv(
        self,
        b: frozenset[tuple[T, T]],
        a: frozenset[tuple[T, T]],
    ) -> frozenset[tuple[T, T]]:
        r"""Right residual $b / a = \{(x, y) \mid \forall z: (y, z) \in a \implies (x, z) \in b\}$."""
        # For each y, find all z such that (y, z) in a
        outgoing_a: dict[T, set[T]] = {}
        for y, z in a:
            outgoing_a.setdefault(y, set()).add(z)

        b_set = set(b)

        res: set[tuple[T, T]] = set()
        for y in self.domain:
            req_zs = outgoing_a.get(y, set())
            for x in self.domain:
                if all((x, z) in b_set for z in req_zs):
                    res.add((x, y))
        return frozenset(res)

    @property
    def is_idempotent(self) -> Literal[True]:
        return True


__all__ = [
    'ActionAlgebra',
    'RelationActionAlgebra',
]
