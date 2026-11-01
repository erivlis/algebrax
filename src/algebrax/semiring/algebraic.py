"""
Algebraic, monoid algebra, quotient, Clifford, and Galois semirings.
"""

import functools
import math
import operator
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from algebrax.algebra._monoid_algebra import MonoidAlgebraSemiring, QuotientMonoidAlgebraSemiring
from algebrax.algebra._semiring import Semiring
from algebrax.semiring.arithmetic import StandardSemiring
from algebrax.typing import K, SparseVector

T = TypeVar('T', bound=float | int | complex)


class KnotSemiring(MonoidAlgebraSemiring[str, T]):
    r"""The Knot Semiring (Skein Module algebra) under connected sum.

    Algebraic Signature:
        $\langle R[\mathcal{K}], +, \#, \emptyset, \{\text{'U'}: 1_R\} \rangle$

    Carrier:
        `dict[str, T]` (Sparse mapping from prime knot factorization strings to coefficients in $R$).

    Operations:
        - Addition ($+$): Formal linear combination addition.
        - Multiplication ($\#$): Knot connected sum (#) combining sorted prime knot components.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{'U': 1_R}` (the unknot 'U').

    Properties:
        Commutative, associative, monoid algebra over the abelian monoid of knots $(\mathcal{K}, \#, U)$.

    Applications:
        Topological quantum field theory, knot polynomials, Vassiliev invariants.
    """

    @staticmethod
    def _combine_knots(k1: str, k2: str) -> str:
        """Helper to compute the connected sum of two knot identifiers."""
        if k1 == 'U':
            return k2
        if k2 == 'U':
            return k1

        # For commutativity, sort the prime knot components.
        parts = k1.split('#') + k2.split('#')
        return '#'.join(sorted(parts))

    def __init__(self, coeff_semiring: Semiring[T] = StandardSemiring(int)):
        super().__init__(
            coeff_semiring=coeff_semiring,
            key_op=self._combine_knots,
            zero_key='U',
        )


class ProvenanceSemiring(MonoidAlgebraSemiring[tuple[str, ...], int]):
    r"""The Polynomial Provenance Semiring $\mathbb{N}[X]$ for data lineage.

    Algebraic Signature:
        $\langle \mathbb{N}[X], +, \cdot, \emptyset, \{(): 1\} \rangle$

    Carrier:
        `dict[tuple[str, ...], int]` (Sparse map from lineage variable tuples to counts in $\mathbb{N}$).

    Operations:
        - Addition ($+$): Alternative provenance pathways (OR / union).
        - Multiplication ($\cdot$): Joint provenance dependencies (AND / join).
        - Zero Element ($\mathbb{0}$): `{}` (no provenance).
        - One Element ($\mathbb{1}$): `{(): 1}` (empty lineage monomial with count 1).

    Properties:
        Commutative semiring over the free commutative monoid of annotation variables.

    Applications:
        Database provenance, security tracking, why-provenance, certainty annotations.
    """

    @staticmethod
    def _combine_monomials(t1: tuple[str, ...], t2: tuple[str, ...]) -> tuple[str, ...]:
        """Multiply two monomials by concatenating and sorting variable names."""
        return tuple(sorted(t1 + t2))

    def __init__(self, coeff_semiring: Semiring[int] = StandardSemiring(int)):
        super().__init__(
            coeff_semiring=coeff_semiring,
            key_op=self._combine_monomials,
            zero_key=(),
        )


def _gf_poly_mod(
    exp: int, coeff: int, p: int = 2, irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1)
) -> list[tuple[int, int]]:
    """
    Reduce polynomial term coeff * x^exp modulo irreducible polynomial irreduc_poly in GF(p).
    Default irreduc_poly: x^8 + x^4 + x^3 + x + 1 (AES GF(2^8) field).
    """
    m = len(irreduc_poly) - 1  # Degree of irreducible polynomial
    c = coeff % p
    if c == 0:
        return []

    # If exponent < m, no reduction needed
    if exp < m:
        return [(exp, c)]

    # Long division polynomial reduction in GF(p)
    poly = [0] * (exp + 1)
    poly[exp] = c

    for deg in range(exp, m - 1, -1):
        if poly[deg] != 0:
            factor = poly[deg]
            for i in range(len(irreduc_poly)):
                target_deg = deg - m + i
                poly[target_deg] = (poly[target_deg] - factor * irreduc_poly[i]) % p

    result: list[tuple[int, int]] = []
    for deg in range(m):
        if poly[deg] != 0:
            result.append((deg, poly[deg]))

    return result


class GaloisFieldSemiring(QuotientMonoidAlgebraSemiring[int, int]):
    r"""The Galois Finite Field $\mathrm{GF}(p^m)$ Semiring.

    Algebraic Signature:
        $\langle \mathrm{GF}(p^m), +, \cdot, \emptyset, \{0: 1\} \rangle$

    Carrier:
        `dict[int, int]` (Sparse polynomial remainder vectors modulo irreducible polynomial $P(x)$ over $\mathbb{Z}_p$).

    Operations:
        - Addition ($+$): Elementwise polynomial addition in $\mathbb{Z}_p$.
        - Multiplication ($\cdot$): Polynomial multiplication reduced modulo irreducible polynomial $P(x)$.
        - Zero Element ($\mathbb{0}$): `{}` (empty polynomial).
        - One Element ($\mathbb{1}$): `{0: 1}` ($x^0 = 1$).

    Properties:
        Commutative finite division ring (field), associative, distributive.

    Applications:
        Error-correcting codes (Reed-Solomon), cryptography (AES Galois Field), cryptographic hashing.
    """

    def __init__(self, p: int = 2, irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1)):
        self.p = p
        self.irreduc_poly = irreduc_poly

        def key_op(k1: int, k2: int) -> int:
            return k1 + k2

        def quotient_fn(key: int, coeff: int) -> Iterable[tuple[int, int]]:
            return _gf_poly_mod(key, coeff, p=self.p, irreduc_poly=self.irreduc_poly)

        from algebrax.semiring.arithmetic import ModularSemiring

        super().__init__(
            coeff_semiring=ModularSemiring(self.p),
            key_op=key_op,
            zero_key=0,
            quotient_fn=quotient_fn,
        )


@functools.lru_cache(maxsize=32)
def _get_pascal_table(order: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(math.comb(n, k) for k in range(n + 1)) for n in range(order + 1))


class BinomialConvolutionSemiring(Semiring[tuple[float, ...]]):
    r"""Universal 1D Binomial Convolution Semiring over $\mathbb{R}[\varepsilon]/(\varepsilon^{K+1})$.

    Algebraic Signature:
        $\langle \mathbb{R}^{K+1}, \oplus, \otimes_{\mathrm{binom}}, \mathbf{0}, \mathbf{e}_0 \rangle$

    Carrier:
        `tuple[float, ...]` ($(K+1)$-tuple $(m_0, m_1, \dots, m_K)$ of derivatives or unnormalized moments).

    Operations:
        - Addition ($\oplus$): Elementwise vector addition $(u + v)_k = u_k + v_k$.
        - Multiplication ($\otimes_{\mathrm{binom}}$): Convolution
          $(u \otimes v)_k = \sum_{j=0}^k \binom{k}{j} u_j v_{k-j}$.
        - Zero Element ($\mathbb{0}$): $(0.0, \dots, 0.0)$ of length $K+1$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0, \dots, 0.0)$ of length $K+1$.

    Properties:
        Commutative, associative, ring quotient isomorphic to Divided Power Algebra $\mathbb{R}[\varepsilon]/I$.

    Applications:
        Arbitrary-order forward-mode automatic differentiation, statistical moment tracking, path variance.
    """

    def __init__(self, order: int = 1) -> None:
        if order < 0:
            raise ValueError(f'order must be a non-negative integer, got {order}')
        self.order = order
        self._dim = order + 1
        self._zero = (0.0,) * self._dim
        self._one = (1.0, *(0.0 for _ in range(order)))
        self._pascal = _get_pascal_table(order)

    @property
    def zero(self) -> tuple[float, ...]:
        return self._zero

    @property
    def one(self) -> tuple[float, ...]:
        return self._one

    def add(self, a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
        dim = self._dim
        if len(a) != dim or len(b) != dim:
            raise ValueError(f'Operands must have length {dim}')
        return tuple(u + v for u, v in zip(a, b))

    def mul(self, a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
        dim = self._dim
        if len(a) != dim or len(b) != dim:
            raise ValueError(f'Operands must have length {dim}')
        pascal = self._pascal
        res = [0.0] * dim
        for k in range(dim):
            coeffs = pascal[k]
            acc = 0.0
            for j in range(k + 1):
                acc += coeffs[j] * a[j] * b[k - j]
            res[k] = acc
        return tuple(res)

    def nsum(self, a: tuple[float, ...], n: int) -> tuple[float, ...]:
        if len(a) != self._dim:
            raise ValueError(f'Operand must have length {self._dim}')
        if n == 0:
            return self._zero
        return tuple(val * n for val in a)

    def power(self, a: tuple[float, ...], n: int) -> tuple[float, ...]:
        if len(a) != self._dim:
            raise ValueError(f'Operand must have length {self._dim}')
        return super().power(a, n)

    def star(self, a: tuple[float, ...]) -> tuple[float, ...]:  # NOSONAR - can return order N result
        dim = self._dim
        if len(a) != dim:
            raise ValueError(f'Operand must have length {dim}')
        p = a[0]
        if p >= 1.0:
            return (float('inf'),) * dim
        if self.order == 0:
            return (1.0 / (1.0 - p),)  # NOSONAR - order 0 is 1D scalar
        if self.order == 1:
            p_star = 1.0 / (1.0 - p)
            v_star = a[1] * (p_star**2)
            return p_star, v_star  # NOSONAR - order 1 is 2D vector

        scale = 1.0 / (1.0 - p)
        scaled_nil = (0.0, *(val * scale for val in a[1:]))
        cur_nil = self._one
        nil_sum = [0.0] * dim
        for _ in range(dim):
            for k in range(dim):
                nil_sum[k] += cur_nil[k]
            cur_nil = self.mul(cur_nil, scaled_nil)
        return tuple(val * scale for val in nil_sum)  # order N > 1 result


@functools.lru_cache(maxsize=4096)
def _multivariate_transition(
    alpha: tuple[int, ...], beta: tuple[int, ...], order: int
) -> tuple[tuple[int, ...], int] | None:
    gamma = tuple(x + y for x, y in zip(alpha, beta))
    if sum(gamma) > order:
        return None
    coeff = math.prod(math.comb(g, a_i) for g, a_i in zip(gamma, alpha))
    return gamma, coeff


class MultivariateBinomialConvolutionSemiring(Semiring[dict[tuple[int, ...], float]]):
    r"""Multivariate Binomial Convolution Semiring over truncated polynomials.

    Algebraic Signature:
        $\langle \mathbb{R}^M, \oplus, \otimes_{\mathrm{multinom}}, \emptyset, \mathbf{1} \rangle$

    Carrier:
        `dict[tuple[int, ...], float]` (Sparse map from multi-index $\boldsymbol{\alpha}$ to coefficient).

    Operations:
        - Addition ($\oplus$): Sparse coefficient addition.
        - Multiplication ($\otimes_{\mathrm{multinom}}$): Multivariate binomial convolution over bounded degree.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{(0, ..., 0): 1.0}`.

    Properties:
        Commutative, associative, ring quotient isomorphic to truncated polynomial ring in $D$ variables.

    Applications:
        Multivariate Taylor series, joint moment tensors, gradient and Hessian path tracking.
    """

    def __init__(self, num_vars: int = 2, order: int = 1) -> None:
        if num_vars < 1:
            raise ValueError(f'num_vars must be >= 1, got {num_vars}')
        if order < 0:
            raise ValueError(f'order must be >= 0, got {order}')
        self.num_vars = num_vars
        self.order = order
        self._zero_key = (0,) * num_vars
        self._one = {self._zero_key: 1.0}

    @property
    def zero(self) -> dict[tuple[int, ...], float]:
        return {}

    @property
    def one(self) -> dict[tuple[int, ...], float]:
        return dict(self._one)

    def add(self, a: dict[tuple[int, ...], float], b: dict[tuple[int, ...], float]) -> dict[tuple[int, ...], float]:
        res = dict(a)
        num_vars = self.num_vars
        order = self.order
        for k, v in b.items():
            if len(k) != num_vars:
                raise ValueError(f'Multi-index {k} dimension does not match num_vars={num_vars}')
            if sum(k) <= order:
                res[k] = res.get(k, 0.0) + v
        return {k: v for k, v in res.items() if not math.isclose(v, 0.0, abs_tol=1e-15)}

    def mul(self, a: dict[tuple[int, ...], float], b: dict[tuple[int, ...], float]) -> dict[tuple[int, ...], float]:
        res: dict[tuple[int, ...], float] = {}
        order = self.order
        num_vars = self.num_vars
        for alpha, v1 in a.items():
            if len(alpha) != num_vars:
                raise ValueError(f'Multi-index {alpha} dimension does not match num_vars={num_vars}')
            for beta, v2 in b.items():
                if len(beta) != num_vars:
                    raise ValueError(f'Multi-index {beta} dimension does not match num_vars={num_vars}')
                trans = _multivariate_transition(alpha, beta, order)
                if trans is not None:
                    gamma, coeff = trans
                    res[gamma] = res.get(gamma, 0.0) + coeff * v1 * v2
        return {k: v for k, v in res.items() if not math.isclose(v, 0.0, abs_tol=1e-15)}

    def nsum(self, a: dict[tuple[int, ...], float], n: int) -> dict[tuple[int, ...], float]:
        if n == 0:
            return {}
        return {k: v * n for k, v in a.items() if not math.isclose(v * n, 0.0, abs_tol=1e-15)}

    def star(self, a: dict[tuple[int, ...], float]) -> dict[tuple[int, ...], float]:
        zero_key = self._zero_key
        p = a.get(zero_key, 0.0)
        if p >= 1.0:
            return {k: float('inf') for k in a}
        scale = 1.0 / (1.0 - p)
        scaled_nil = {k: v * scale for k, v in a.items() if k != zero_key and sum(k) <= self.order}
        cur_nil = self.one
        res: dict[tuple[int, ...], float] = {}
        for _ in range(self.order + 1):
            for k, v in cur_nil.items():
                res[k] = res.get(k, 0.0) + v
            cur_nil = self.mul(cur_nil, scaled_nil)
        return {k: v * scale for k, v in res.items() if not math.isclose(v * scale, 0.0, abs_tol=1e-15)}


# Canonical backwards-compatible dynamic re-exports from their primary domains
def __getattr__(name: str) -> Any:
    if name in ('PolynomialAlgebra', 'PolynomialRing', 'PolynomialSemiring'):
        from algebrax.algebra._polynomial import (
            PolynomialAlgebra,
            PolynomialRing,
            PolynomialSemiring,
        )

        mapping = {
            'PolynomialAlgebra': PolynomialAlgebra,
            'PolynomialRing': PolynomialRing,
            'PolynomialSemiring': PolynomialSemiring,
        }
        return mapping[name]
    if name in ('DualNumberAlgebra', 'DualNumberRing', 'DualNumberSemiring'):
        from algebrax.algebra._dual import (
            DualNumberAlgebra,
            DualNumberRing,
            DualNumberSemiring,
        )

        mapping = {
            'DualNumberAlgebra': DualNumberAlgebra,
            'DualNumberRing': DualNumberRing,
            'DualNumberSemiring': DualNumberSemiring,
        }
        return mapping[name]
    if name in (
        'CliffordAlgebra',
        'CliffordSemiring',
        'GeneralizedCliffordAlgebra',
        'GeneralizedCliffordSemiring',
        'QuantumCliffordAlgebra',
        'QuantumCliffordSemiring',
    ):
        import algebrax.clifford as cliff

        return getattr(cliff, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
