r"""
Canonical universal quotient constructions $S / I$, $R / I$, and $A / I$.

Algebraic Signatures:
    QuotientSemiring:  $\langle S / I, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$
    QuotientRing:      $\langle R / I, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$
    CommQuotientRing:  $\langle R / I, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ with $a \cdot b = b \cdot a$
    QuotientAlgebra:   $\langle R, A / I, \cdot_s, \mathbf{0}, +, -, (\mathbf{1}), \cdot \rangle$
"""

from __future__ import annotations

from typing import Generic, TypeVar

from algebrax.algebra._ideals import Ideal
from algebrax.algebra._module import NonAssocAlgebra
from algebrax.algebra._ring import CommRing, Ring
from algebrax.algebra._semiring import Semiring

V = TypeVar('V')
R = TypeVar('R')


class QuotientSemiring(Semiring[V], Generic[V]):
    r"""Canonical quotient semiring $S / I$ reduced modulo an ideal or congruence reducer $I$.

    All operations are evaluated in the ambient `base_semiring` and immediately projected
    to canonical normal form via `ideal.reduce(x)` with zero wrapper allocation.
    """

    def __init__(self, base_semiring: Semiring[V], ideal: Ideal[V]) -> None:
        self.base_semiring = base_semiring
        self.ideal = ideal

    @property
    def zero(self) -> V:
        return self.ideal.reduce(self.base_semiring.zero)

    @property
    def one(self) -> V:
        return self.ideal.reduce(self.base_semiring.one)

    def add(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_semiring.add(self.ideal.reduce(a), self.ideal.reduce(b)))

    def mul(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_semiring.mul(self.ideal.reduce(a), self.ideal.reduce(b)))

    def eq(self, a: V, b: V) -> bool:
        r"""Check coset equality $[a] = [b] \iff \mathrm{reduce}(a) == \mathrm{reduce}(b)$."""
        return self.ideal.reduce(a) == self.ideal.reduce(b)

    def project(self, x: V) -> V:
        r"""Canonical quotient projection homomorphism $\pi: S \to S / I$."""
        return self.ideal.reduce(x)


class QuotientRing(QuotientSemiring[V], Ring[V], Generic[V]):
    r"""Canonical quotient ring $R / I$ of a ring $R$ modulo a two-sided ideal $I \triangleleft R$.

    Algebraic Signature:
        $\langle R / I, \mathbf{0}_{R/I}, +_{R/I}, -_{R/I}, \mathbf{1}_{R/I}, \cdot_{R/I} \rangle$

    Carrier:
        Unboxed canonical coset representatives $V$ computed via `ideal.reduce(x)`.

    Operations:
        - $[a] + [b] = \mathrm{reduce}(a + b)$ (inherited from `QuotientSemiring`)
        - $[a] \cdot [b] = \mathrm{reduce}(a \cdot b)$ (inherited from `QuotientSemiring`)
        - $-[a] = \mathrm{reduce}(-a)$
        - $[a] - [b] = \mathrm{reduce}(a - b)$

    Properties:
        Nominally and structurally satisfies `Ring[V]` and `Semiring[V]`.
        For provably commutative quotients witnessing `CommRing[V]`, use `CommQuotientRing`.
        The canonical projection $\pi(x) = \mathrm{ideal.reduce}(x)$ is a surjective `RingHom`
        with $\ker \pi = I$.
    """

    def __init__(self, base_ring: Ring[V] | CommRing[V], ideal: Ideal[V]) -> None:
        super().__init__(base_ring, ideal)  # type: ignore[arg-type]
        self.base_ring = base_ring

    def neg(self, a: V) -> V:
        return self.ideal.reduce(self.base_ring.neg(self.ideal.reduce(a)))

    def sub(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_ring.sub(self.ideal.reduce(a), self.ideal.reduce(b)))


class CommQuotientRing(QuotientRing[V], CommRing[V], Generic[V]):
    r"""Canonical commutative quotient ring $R / I$ of a commutative ring $R$ modulo an ideal $I \triangleleft R$.

    Algebraic Signature:
        $\langle R / I, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ with $[a][b] = [b][a]$

    Carrier:
        Unboxed canonical coset representatives $V$ computed via `ideal.reduce(x)`.

    Properties:
        Validates that `base_ring` satisfies `CommRing` at construction time, and nominally
        witnesses `CommRing[V]`, `QuotientRing[V]`, `Ring[V]`, and `Semiring[V]`.
    """

    def __init__(self, base_ring: CommRing[V], ideal: Ideal[V]) -> None:
        if not isinstance(base_ring, CommRing):
            raise TypeError(f'CommQuotientRing requires a CommRing base_ring, got {type(base_ring).__name__}.')
        super().__init__(base_ring, ideal)


class QuotientAlgebra(QuotientSemiring[V], NonAssocAlgebra[R, V], Generic[R, V]):
    r"""Canonical quotient algebra $A / I$ over scalar ring $R$.

    Algebraic Signature:
        $\langle R, A / I, \cdot_s, \mathbf{0}, +, -, (\mathbf{1}), \cdot \rangle$

    Inherits quotient addition, multiplication, equality, and projection from `QuotientSemiring[V]`
    without falsely claiming associativity (`LawAssociative`) or commutativity (`CommRing`), and
    supports non-unital algebras such as Lie algebras modulo a `LieIdeal`.
    """

    def __init__(self, base_algebra: NonAssocAlgebra[R, V], ideal: Ideal[V]) -> None:
        super().__init__(base_algebra, ideal)  # type: ignore[arg-type]
        self.base_algebra = base_algebra

    @property
    def one(self) -> V:
        one_val = getattr(self.base_algebra, 'one', None)
        if one_val is None:
            raise AttributeError('Underlying non-associative algebra does not define a multiplicative identity one.')
        return self.ideal.reduce(one_val)

    def neg(self, a: V) -> V:
        return self.ideal.reduce(self.base_algebra.neg(self.ideal.reduce(a)))

    def sub(self, a: V, b: V) -> V:
        ra = self.ideal.reduce(a)
        rb = self.ideal.reduce(b)
        sub_fn = getattr(self.base_algebra, 'sub', None)
        if sub_fn is not None:
            return self.ideal.reduce(sub_fn(ra, rb))
        return self.ideal.reduce(self.base_algebra.add(ra, self.base_algebra.neg(rb)))

    def smul(self, r: R, m: V) -> V:
        return self.ideal.reduce(self.base_algebra.smul(r, self.ideal.reduce(m)))


__all__ = [
    'CommQuotientRing',
    'QuotientAlgebra',
    'QuotientRing',
    'QuotientSemiring',
]
