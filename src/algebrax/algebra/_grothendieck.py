r"""
Universal Grothendieck Group Construction $K_0(M)$.

Formalizes the left adjoint functor from commutative monoids $\mathbf{CommMonoid}$ to abelian
groups $\mathbf{Ab}$ via formal difference classes $[a - b]$, together with the universal
extension of monoid homomorphisms $f: M \to G$ to group homomorphisms $\tilde{f}: K_0(M) \to G$.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar

from algebrax.algebra._group import AddCommGroup
from algebrax.algebra._monoid import AddCommMonoid
from algebrax.algebra._ring import CommRing
from algebrax.algebra._semiring import Semiring

M = TypeVar('M')
G = TypeVar('G')


class GrothendieckGroup(AddCommGroup[tuple[M, M]], Generic[M]):
    r"""The universal Grothendieck group $K_0(M)$ of an additive commutative monoid $M$.

    Algebraic Signature:
        $\langle M \times M / \sim, \mathbf{0}, +, - \rangle$

    Elements are formal difference pairs $(a, b) \in M \times M$ representing $[a] - [b]$,
    under the stabilized equivalence relation:
        $$(a, b) \sim (c, d) \iff \exists k \in M \text{ such that } a + d + k = b + c + k$$

    When the underlying monoid is cancellative (such as $(\mathbb{N}, +, 0)$ or direct-sum vector
    bundle dimensions), equivalence simplifies to the cross-addition identity $a + d = b + c$.

    Properties:
        - Canonical Embedding: $\iota(a) = (a, 0_M)$ satisfies $\iota(a + b) = \iota(a) + \iota(b)$.
        - Universal Property: Any monoid homomorphism $f: M \to G$ into an abelian group $G$
          factors uniquely through $\iota$ via $\tilde{f}(a, b) = f(a) -_G f(b)$.
    """

    def __init__(
        self,
        monoid: AddCommMonoid[M],
        *,
        eq_fn: Callable[[M, M], bool] | None = None,
        normalize_fn: Callable[[tuple[M, M]], tuple[M, M]] | None = None,
    ) -> None:
        self.monoid = monoid
        self._eq_fn = eq_fn
        self._normalize_fn = normalize_fn

    def _normalize(self, pair: tuple[M, M]) -> tuple[M, M]:
        if self._normalize_fn is not None:
            return self._normalize_fn(pair)
        return pair

    @property
    def zero(self) -> tuple[M, M]:
        r"""Additive identity $(0_M, 0_M)$ representing $[0_M] - [0_M]$."""
        z = self.monoid.zero
        return self._normalize((z, z))

    def embed(self, a: M) -> tuple[M, M]:
        r"""Canonical monoid-to-group embedding $\iota(a) = (a, 0_M)$."""
        return self._normalize((a, self.monoid.zero))

    def add(self, a: tuple[M, M], b: tuple[M, M]) -> tuple[M, M]:
        r"""Componentwise formal sum $(a_1 - a_2) + (b_1 - b_2) = (a_1 + b_1, a_2 + b_2)$."""
        return self._normalize(
            (
                self.monoid.add(a[0], b[0]),
                self.monoid.add(a[1], b[1]),
            )
        )

    def neg(self, a: tuple[M, M]) -> tuple[M, M]:
        r"""Formal additive inverse $-(a_1 - a_2) = (a_2, a_1)$."""
        return self._normalize((a[1], a[0]))

    def sub(self, a: tuple[M, M], b: tuple[M, M]) -> tuple[M, M]:
        r"""Formal difference $(a_1 - a_2) - (b_1 - b_2) = (a_1 + b_2, a_2 + b_1)$."""
        return self.add(a, self.neg(b))

    def equiv(
        self,
        x: tuple[M, M],
        y: tuple[M, M],
        stabilizers: Iterable[M] | None = None,
    ) -> bool:
        r"""Test Grothendieck equivalence $(a, b) \sim (c, d)$.

        Checks whether $a + d + k = b + c + k$ for $k = 0_M$ or any $k \in \text{stabilizers}$.
        """
        a, b = x
        c, d = y
        lhs_base = self.monoid.add(a, d)
        rhs_base = self.monoid.add(b, c)
        eq = self._eq_fn if self._eq_fn is not None else (lambda u, v: u == v)

        if eq(lhs_base, rhs_base):
            return True

        if stabilizers is not None:
            for k in stabilizers:
                if eq(self.monoid.add(lhs_base, k), self.monoid.add(rhs_base, k)):
                    return True

        return False

    def lift_homomorphism(
        self,
        target_group: AddCommGroup[G],
        monoid_map: Callable[[M], G],
    ) -> Callable[[tuple[M, M]], G]:
        r"""Universal property of $K_0(M)$: lift a monoid map $f: M \to G$ to $\tilde{f}: K_0(M) \to G$.

        Returns:
            The unique group homomorphism $\tilde{f}(a, b) = f(a) -_G f(b)$ satisfying
            $\tilde{f} \circ \iota = f$.
        """

        def lifted(pair: tuple[M, M]) -> G:
            return target_group.sub(monoid_map(pair[0]), monoid_map(pair[1]))

        return lifted


class GrothendieckRing(GrothendieckGroup[M], CommRing[tuple[M, M]], Generic[M]):
    r"""The universal Grothendieck ring $K_0(S)$ of a commutative semiring $S$.

    Extends `GrothendieckGroup` with formal difference multiplication:
        $$(a - b) \cdot (c - d) = (a c + b d, a d + b c)$$
    and multiplicative identity $\mathbf{1}_{K_0} = (1_S, 0_S)$.
    """

    def __init__(
        self,
        semiring: Semiring[M],
        *,
        eq_fn: Callable[[M, M], bool] | None = None,
        normalize_fn: Callable[[tuple[M, M]], tuple[M, M]] | None = None,
    ) -> None:
        super().__init__(semiring, eq_fn=eq_fn, normalize_fn=normalize_fn)
        self.semiring = semiring

    @property
    def one(self) -> tuple[M, M]:
        r"""Multiplicative identity $(1_S, 0_S)$."""
        return self._normalize((self.semiring.one, self.semiring.zero))

    def mul(self, a: tuple[M, M], b: tuple[M, M]) -> tuple[M, M]:
        r"""Formal difference product $(a_1 - a_2)(b_1 - b_2) = (a_1 b_1 + a_2 b_2, a_1 b_2 + a_2 b_1)$."""
        a1, a2 = a
        b1, b2 = b
        s = self.semiring
        pos = s.add(s.mul(a1, b1), s.mul(a2, b2))
        neg = s.add(s.mul(a1, b2), s.mul(a2, b1))
        return self._normalize((pos, neg))


__all__ = [
    'GrothendieckGroup',
    'GrothendieckRing',
]
