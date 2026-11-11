"""
Univariate polynomial algebra and commutative ring R[x].
"""

from __future__ import annotations

import operator
from typing import TypeVar

from algebrax.algebra._monoid_algebra import MonoidAlgebra
from algebrax.algebra._semiring import Semiring

T = TypeVar('T', bound=float | int | complex)


class PolynomialAlgebra(MonoidAlgebra[int, T]):
    r"""The Univariate Polynomial Algebra and Commutative Ring $R[x]$ over coefficient ring $R$.

    Algebraic Signature:
        $\langle R, R[x], \cdot_s, \emptyset, +, -, \{0: 1_R\}, \cdot \rangle$

    Carrier:
        `dict[int, T]` (Sparse mapping from degree $k \in \mathbb{N}_0$ to coefficient $c_k \in R$).

    Operations:
        - Addition ($+$): Elementwise polynomial addition (inherited from `MonoidAlgebraSemiring`).
        - Multiplication ($\cdot$): Cauchy polynomial product $(a \cdot b)_k = \sum_{j=0}^k a_j b_{k-j}$.
        - Negation ($-a$): Degree-wise coefficient negation (inherited from `MonoidAlgebra`).
        - Subtraction ($a - b$): Direct polynomial difference (inherited from `MonoidAlgebra`).
        - Scalar Multiplication ($r \cdot_s m$): Scaling by scalar $r \in R$ (inherited from `MonoidAlgebraSemiring`).
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{0: 1_R}` ($x^0 = 1$).

    Properties:
        Associative, distributive; commutative if $R$ is commutative.
        Fulfills `Algebra`, `CommRing`, `Ring`, `Module`, and `Semiring`.

    Applications:
        Generating functions, algebraic combinatorics, spectral graph polynomials.
    """

    def __init__(self, coeff_semiring: Semiring[T]):
        super().__init__(coeff_semiring, key_op=operator.add, zero_key=0)


__all__ = [
    'PolynomialAlgebra',
]
