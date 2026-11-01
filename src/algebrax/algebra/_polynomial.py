"""
Univariate polynomial algebra and commutative ring R[x].
"""

from __future__ import annotations

import operator
from typing import TypeVar

from algebrax.algebra._monoid_algebra import MonoidAlgebraSemiring
from algebrax.algebra._semiring import Semiring
from algebrax.typing import SparseVector

T = TypeVar('T', bound=float | int | complex)


class PolynomialAlgebra(MonoidAlgebraSemiring[int, T]):
    r"""The Univariate Polynomial Algebra and Commutative Ring $R[x]$ over coefficient ring $R$.

    Algebraic Signature:
        $\langle R[x], +, \cdot, \emptyset, \{0: 1_R\} \rangle$

    Carrier:
        `dict[int, T]` (Sparse mapping from degree $k \in \mathbb{N}_0$ to coefficient $c_k \in R$).

    Operations:
        - Addition ($+$): Elementwise polynomial addition.
        - Multiplication ($\cdot$): Cauchy polynomial product $(a \cdot b)_k = \sum_{j=0}^k a_j b_{k-j}$.
        - Negation ($-a$): Degree-wise coefficient negation.
        - Subtraction ($a - b$): Direct polynomial difference.
        - Scalar Multiplication ($r \cdot m$): Scaling polynomial by scalar $r \in R$.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{0: 1_R}` ($x^0 = 1$).

    Properties:
        Associative, distributive; commutative if $R$ is commutative. Fulfills Ring, CommRing, and Algebra.

    Applications:
        Generating functions, algebraic combinatorics, spectral graph polynomials.
    """

    def __init__(self, coeff_semiring: Semiring[T]):
        super().__init__(coeff_semiring, key_op=operator.add, zero_key=0)

    def neg(self, a: SparseVector[int, T]) -> SparseVector[int, T]:
        """Negate coefficients, delegating to coefficient ring if available."""
        neg_fn = getattr(self.coeff_semiring, 'neg', None)
        zero = self.coeff_semiring.zero
        if neg_fn is not None:
            return {deg: neg_fn(c) for deg, c in a.items() if c != zero}
        return {deg: -c for deg, c in a.items() if c != zero}  # type: ignore[operator]

    def sub(self, a: SparseVector[int, T], b: SparseVector[int, T]) -> SparseVector[int, T]:
        """Direct polynomial difference: a - b."""
        neg_b = self.neg(b)
        return self.add(a, neg_b)

    def smul(self, r: T, m: SparseVector[int, T]) -> SparseVector[int, T]:
        """Scale polynomial by scalar r: r * (c0 + c1*x + ...) = (r*c0) + (r*c1)*x + ..."""
        zero = self.coeff_semiring.zero
        mul_fn = self.coeff_semiring.mul
        if r == zero:
            return {}
        return {deg: mul_fn(r, c) for deg, c in m.items() if mul_fn(r, c) != zero}


# Canonical aliases
PolynomialRing = PolynomialAlgebra
PolynomialSemiring = PolynomialAlgebra

__all__ = [
    'PolynomialAlgebra',
    'PolynomialRing',
    'PolynomialSemiring',
]
