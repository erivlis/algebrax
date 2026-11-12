"""
Monoid algebra semirings S[M], monoid algebras R[M], and their quotients S[M]/I and R[M]/I.
"""

from __future__ import annotations

import operator
from collections.abc import Callable, Iterable
from typing import TypeVar

from algebrax.algebra._ideals import Ideal
from algebrax.algebra._module import Algebra, Semimodule
from algebrax.algebra._ring import CommRing
from algebrax.algebra._semiring import Semiring
from algebrax.typing import K, SparseVector

T = TypeVar('T', bound=float | int | complex)


class MonoidAlgebraSemiring(Semiring[SparseVector[K, T]], Semimodule[T, SparseVector[K, T]]):
    r"""The Monoid Algebra Semiring $S[M]$ over coefficient semiring $S$ and monoid $M$.

    Algebraic Signature:
        $\langle S, S[M], \cdot_s, \emptyset, +, \{e_M: 1_S\}, \ast \rangle$

    Carrier:
        `dict[K, T]` (Sparse mapping from monoid elements $m \in M$ to non-zero coefficients $a_m \in S$).

    Operations:
        - Addition ($+$): Elementwise coefficient addition in $S$.
        - Multiplication ($\ast$): Algebraic convolution $(a \ast b)_m = \sum_{u \cdot v = m} a_u b_v$.
        - Scalar Multiplication ($r \cdot_s m$): Scaling coefficients by scalar $r \in S$.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{e_M: 1_S}` (monoid identity mapped to coefficient one).

    Properties:
        Satisfies `Semiring` and `Semimodule`. Valid for any coefficient semiring $S$
        (including idempotent/tropical/Boolean semirings without additive inverses).
    """

    def __init__(
        self,
        coeff_semiring: Semiring[T],
        key_op: Callable[[K, K], K] = operator.add,
        zero_key: K = 0,  # type: ignore[assignment]
    ):
        self.coeff_semiring = coeff_semiring
        self.key_op = key_op
        self.zero_key = zero_key

    @property
    def zero(self) -> SparseVector[K, T]:
        return {}

    @property
    def one(self) -> SparseVector[K, T]:
        return {self.zero_key: self.coeff_semiring.one}

    def add(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        result = dict(a)
        coeff_add = self.coeff_semiring.add
        zero = self.coeff_semiring.zero
        for exp, coeff in b.items():
            new_coeff = coeff_add(result.get(exp, zero), coeff)
            if new_coeff == zero:
                result.pop(exp, None)
            else:
                result[exp] = new_coeff
        return result

    def smul(self, r: T, m: SparseVector[K, T]) -> SparseVector[K, T]:
        """Scale monoid algebra element by scalar r in S."""
        zero = self.coeff_semiring.zero
        mul_fn = self.coeff_semiring.mul
        if r == zero:
            return {}
        return {k: prod for k, c in m.items() if (prod := mul_fn(r, c)) != zero}

    def mul(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        if not a or not b:
            return {}

        result: dict[K, T] = {}
        key_op = self.key_op
        coeff_mul = self.coeff_semiring.mul
        coeff_add = self.coeff_semiring.add
        zero = self.coeff_semiring.zero

        for e1, c1 in a.items():
            for e2, c2 in b.items():
                new_key = key_op(e1, e2)
                new_coeff = coeff_mul(c1, c2)

                current_coeff = result.get(new_key, zero)
                sum_coeff = coeff_add(current_coeff, new_coeff)

                if sum_coeff == zero:
                    result.pop(new_key, None)
                else:
                    result[new_key] = sum_coeff
        return result

    def nsum(self, a: SparseVector[K, T], n: int) -> SparseVector[K, T]:
        if n == 0:
            return {}
        result = {}
        coeff_nsum = self.coeff_semiring.nsum
        zero = self.coeff_semiring.zero
        for exp, coeff in a.items():
            scaled = coeff_nsum(coeff, n)
            if scaled != zero:
                result[exp] = scaled
        return result


class MonoidAlgebra(MonoidAlgebraSemiring[K, T], Algebra[T, SparseVector[K, T]], CommRing[SparseVector[K, T]]):
    r"""The Monoid Algebra (and Monoid Ring) $R[M]$ over coefficient ring $R$ and monoid $M$.

    Algebraic Signature:
        $\langle R, R[M], \cdot_s, \emptyset, +, -, \{e_M: 1_R\}, \ast \rangle$

    Carrier:
        `dict[K, T]` (Sparse mapping from monoid elements $m \in M$ to non-zero coefficients $a_m \in R$).

    Operations:
        - Addition ($+$), Multiplication ($\ast$), Scalar Action ($\cdot_s$): Inherited from `MonoidAlgebraSemiring`.
        - Negation ($-a$): Coefficient-wise additive inverse in $R$.
        - Subtraction ($a - b$): Direct sparse difference $a + (-b)$.

    Properties:
        Satisfies `Algebra`, `Module`, `CommRing` (when $R$ and $M$ are commutative), `Ring`, and `Semiring`.
    """

    def neg(self, a: SparseVector[K, T]) -> SparseVector[K, T]:
        """Negate coefficients, delegating to coefficient ring if available."""
        neg_fn = getattr(self.coeff_semiring, 'neg', None)
        zero = self.coeff_semiring.zero
        if neg_fn is not None:
            return {k: neg_fn(c) for k, c in a.items() if c != zero}
        return {k: -c for k, c in a.items() if c != zero}  # type: ignore[operator]

    def sub(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        """Direct sparse difference: a - b."""
        return self.add(a, self.neg(b))


class QuotientMonoidAlgebraSemiring(MonoidAlgebraSemiring[K, T]):
    r"""The Quotient Monoid Algebra Semiring $S[M] / I$.

    Algebraic Signature:
        $\langle S, S[M]/I, \cdot_s, \emptyset, +, \{e_M: 1_S\}, \ast_{\mathrm{quot}} \rangle$

    Carrier:
        `dict[K, T]` (Sparse mapping reduced to canonical basis representatives modulo $I$).

    Two-Level Quotient Mechanics (EP-0201):
        1. **In-Loop Basis-Pair Rewriting (`quotient_fn`)**: During convolution $a \ast b$, each raw
           basis product $(k_1 \cdot k_2, c_1 c_2)$ is expanded into canonical terms via
           `quotient_fn(raw_key, raw_coeff) -> Iterable[tuple[K, T]]`.
        2. **Whole-Element Ideal Reduction (`ideal`)**: Optional `Ideal[SparseVector[K, T]]` applied
           via `ideal.reduce(...)` to maintain canonical normal form across `add`, `smul`, and `mul`.
    """

    def __init__(
        self,
        coeff_semiring: Semiring[T],
        key_op: Callable[[K, K], K] = operator.add,
        zero_key: K = 0,  # type: ignore[assignment]
        quotient_fn: Callable[[K, T], Iterable[tuple[K, T]]] | None = None,
        ideal: Ideal[SparseVector[K, T]] | None = None,
    ):
        super().__init__(coeff_semiring, key_op, zero_key)
        self.quotient_fn = quotient_fn
        self.ideal = ideal

    def add(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        res = super().add(a, b)
        return self.ideal.reduce(res) if self.ideal is not None else res

    def smul(self, r: T, m: SparseVector[K, T]) -> SparseVector[K, T]:
        res = super().smul(r, m)
        return self.ideal.reduce(res) if self.ideal is not None else res

    def mul(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        if not a or not b:
            return {}

        if self.quotient_fn is None:
            res = super().mul(a, b)
            return self.ideal.reduce(res) if self.ideal is not None else res

        result: dict[K, T] = {}
        key_op = self.key_op
        coeff_mul = self.coeff_semiring.mul
        coeff_add = self.coeff_semiring.add
        zero = self.coeff_semiring.zero
        quotient_fn = self.quotient_fn

        for e1, c1 in a.items():
            for e2, c2 in b.items():
                raw_key = key_op(e1, e2)
                raw_coeff = coeff_mul(c1, c2)

                for red_key, red_coeff in quotient_fn(raw_key, raw_coeff):
                    current_coeff = result.get(red_key, zero)
                    sum_coeff = coeff_add(current_coeff, red_coeff)

                    if sum_coeff == zero:
                        result.pop(red_key, None)
                    else:
                        result[red_key] = sum_coeff
        return self.ideal.reduce(result) if self.ideal is not None else result


class QuotientMonoidAlgebra(QuotientMonoidAlgebraSemiring[K, T], MonoidAlgebra[K, T]):
    r"""The Quotient Monoid Algebra (and Quotient Monoid Ring) $R[M] / I$ over coefficient ring $R$.

    Algebraic Signature:
        $\langle R, R[M]/I, \cdot_s, \emptyset, +, -, \{e_M: 1_R\}, \ast_{\mathrm{quot}} \rangle$

    Inherits quotient convolution (`quotient_fn` and `ideal`) from `QuotientMonoidAlgebraSemiring`
    and additive inverses (`neg`, `sub`) from `MonoidAlgebra`.
    """

    def neg(self, a: SparseVector[K, T]) -> SparseVector[K, T]:
        res = super().neg(a)
        return self.ideal.reduce(res) if self.ideal is not None else res

    def sub(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        res = super().sub(a, b)
        return self.ideal.reduce(res) if self.ideal is not None else res


__all__ = [
    'MonoidAlgebra',
    'MonoidAlgebraSemiring',
    'QuotientMonoidAlgebra',
    'QuotientMonoidAlgebraSemiring',
]
