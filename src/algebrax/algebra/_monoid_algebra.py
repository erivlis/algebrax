"""
Monoid algebra and quotient monoid algebra structures R[M] and R[M]/I.
"""

from __future__ import annotations

import operator
from collections.abc import Callable, Iterable
from typing import TypeVar

from algebrax.algebra._semiring import Semiring
from algebrax.typing import K, SparseVector

T = TypeVar('T', bound=float | int | complex)


class MonoidAlgebraSemiring(Semiring[SparseVector[K, T]]):
    r"""The Monoid Algebra Semiring $R[M]$ over coefficient semiring $R$ and monoid $M$.

    Algebraic Signature:
        $\langle R[M], +, \ast, \emptyset, \{e_M: 1_R\} \rangle$

    Carrier:
        `dict[K, T]` (Sparse mapping from monoid elements $m \in M$ to non-zero coefficients $a_m \in R$).

    Operations:
        - Addition ($+$): Elementwise coefficient addition in $R$.
        - Multiplication ($\ast$): Algebraic convolution $(a \ast b)_m = \sum_{u \cdot v = m} a_u b_v$.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{e_M: 1_R}` (monoid identity mapped to coefficient one).

    Properties:
        Associative, distributive; commutative if both $R$ and $M$ are commutative.

    Applications:
        Polynomial rings, formal power series, group algebras, path algebras, knot invariants.
    """

    def __init__(
        self,
        coeff_semiring: Semiring[T],
        key_op: Callable[[K, K], K] = operator.add,
        zero_key: K = 0,
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

    def star(self, a: SparseVector[K, T]) -> SparseVector[K, T]:
        raise NotImplementedError('Kleene star not implemented for MonoidAlgebraSemiring')


class QuotientMonoidAlgebraSemiring(MonoidAlgebraSemiring[K, T]):
    r"""The Quotient Monoid Algebra Semiring $R[M] / I$.

    Algebraic Signature:
        $\langle R[M]/I, +, \ast_{\mathrm{quot}}, \emptyset, \{e_M: 1_R\} \rangle$

    Carrier:
        `dict[K, T]` (Sparse mapping reduced to canonical basis representatives modulo ideal $I$).

    Operations:
        - Addition ($+$): Elementwise coefficient addition modulo $I$.
        - Multiplication ($\ast_{\mathrm{quot}}$): Monoid convolution followed by canonical reduction `quotient_fn`.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{e_M: 1_R}`.

    Properties:
        Associative quotient algebra; algebraic structure determined by reduction rule.

    Applications:
        Clifford algebras, truncated polynomials, finite fields, quantum groups.
    """

    def __init__(
        self,
        coeff_semiring: Semiring[T],
        key_op: Callable[[K, K], K] = operator.add,
        zero_key: K = 0,  # type: ignore[assignment]
        quotient_fn: Callable[[K, T], Iterable[tuple[K, T]]] | None = None,
    ):
        super().__init__(coeff_semiring, key_op, zero_key)
        self.quotient_fn = quotient_fn

    def mul(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        if not a or not b:
            return {}

        if self.quotient_fn is None:
            return super().mul(a, b)

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
        return result


__all__ = [
    'MonoidAlgebraSemiring',
    'QuotientMonoidAlgebraSemiring',
]
