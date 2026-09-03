"""
Algebraic, monoid algebra, quotient, Clifford, and Galois semirings.
"""

import cmath
import functools
import math
import operator
from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

from algebrax.semiring._base import Semiring
from algebrax.semiring.arithmetic import StandardSemiring
from algebrax.typing import K, SparseVector

T = TypeVar('T', bound=float | int | complex)


class MonoidAlgebraSemiring(Semiring[SparseVector[K, T]], Generic[K, T]):
    """
    The Monoid Algebra Semiring R[M] over a generic coefficient semiring R and monoid M.
    Values are formal linear combinations sum_{m in M} a_m m, represented as sparse mappings
    from key (monoid element m) to coefficient (a_m in R).

    - Addition: Elementwise coefficient addition in R.
    - Multiplication: Convolution using monoid multiplication (key_op) and coefficient multiplication in R.
    - Additive Identity (zero): The empty mapping {}.
    - Multiplicative Identity (one): {zero_key: coeff_semiring.one}.
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


class KnotSemiring(MonoidAlgebraSemiring[str, T], Generic[T]):
    """
    The Knot Semiring (Skein Module) over a generic coefficient semiring.
    Subclass of MonoidAlgebraSemiring where keys are knot strings and multiplication is the connected sum (#).
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


class PolynomialSemiring(MonoidAlgebraSemiring[int, T], Generic[T]):
    """
    Univariate Polynomial Semiring R[x] over a coefficient semiring R.
    Specialized subclass of MonoidAlgebraSemiring where keys are non-negative integer exponents (N_0, +).
    """

    def __init__(self, coeff_semiring: Semiring[T]):
        super().__init__(coeff_semiring, key_op=operator.add, zero_key=0)


class ProvenanceSemiring(MonoidAlgebraSemiring[tuple[str, ...], int]):
    """
    The Polynomial Provenance Semiring N[X].
    Subclass of MonoidAlgebraSemiring where keys are sorted tuples of variable names (monomials)
    and coefficients are occurrence counts in N.
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

    def mul(self, a: dict[tuple[str, ...], int], b: dict[tuple[str, ...], int]) -> dict[tuple[str, ...], int]:
        result: dict[tuple[str, ...], int] = {}
        if not a or not b:
            return {}

        for term1, coeff1 in a.items():
            for term2, coeff2 in b.items():
                new_term = tuple(sorted(term1 + term2))
                new_coeff = coeff1 * coeff2
                val = result.get(new_term, 0) + new_coeff
                if val == 0:
                    result.pop(new_term, None)
                else:
                    result[new_term] = val
        return result


class QuotientMonoidAlgebraSemiring(MonoidAlgebraSemiring[K, T], Generic[K, T]):
    """
    The Quotient Monoid Algebra Semiring R[M] / I over a generic coefficient semiring R, monoid M,
    and a quotient canonical reduction rule `quotient_fn`.
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


def _clifford_blade_mul(
    k1: tuple[int, ...], k2: tuple[int, ...], p: int = 3, q: int = 0, r: int = 0
) -> list[tuple[tuple[int, ...], float]]:
    """
    Canonical blade reduction for Clifford Algebra Cl(p, q, r).
    e_i^2 = +1 (i <= p), -1 (p < i <= p+q), 0 (i > p+q).
    """
    combined = list(k1 + k2)
    n = len(combined)
    sign = 1.0

    # Insertion sort to count inversions (sign flips)
    for i in range(n):
        for j in range(i + 1, n):
            if combined[i] > combined[j]:
                combined[i], combined[j] = combined[j], combined[i]
                sign = -sign

    # Reduce adjacent pairs (e_i * e_i)
    canonical: list[int] = []
    i = 0
    while i < len(combined):
        if i + 1 < len(combined) and combined[i] == combined[i + 1]:
            idx = combined[i]
            if idx <= p:
                sign *= 1.0
            elif idx <= p + q:
                sign *= -1.0
            else:
                return []  # e_k^2 = 0 degenerate
            i += 2
        else:
            canonical.append(combined[i])
            i += 1

    return [(tuple(canonical), sign)]


class CliffordSemiring(QuotientMonoidAlgebraSemiring[tuple[int, ...], float]):
    """
    Clifford Geometric Algebra Cl(p, q, r) Semiring.
    Values are multivectors represented as dict[tuple[int, ...], float].
    """

    def __init__(self, p: int = 3, q: int = 0, r: int = 0):
        self.p = p
        self.q = q
        self.r = r

        def key_op(k1: tuple[int, ...], k2: tuple[int, ...]) -> tuple[int, ...]:
            return k1 + k2

        def quotient_fn(key: tuple[int, ...], coeff: float) -> Iterable[tuple[tuple[int, ...], float]]:
            reds = _clifford_blade_mul(key, (), p=self.p, q=self.q, r=self.r)
            return [(k, c * coeff) for k, c in reds]

        super().__init__(
            coeff_semiring=StandardSemiring[float](),
            key_op=key_op,
            zero_key=(),
            quotient_fn=quotient_fn,
        )


def _gca_blade_mul(
    k1: tuple[int, ...],
    k2: tuple[int, ...],
    n_order: int = 3,
    num_generators: int = 2,
    signatures: tuple[complex, ...] | None = None,
) -> list[tuple[tuple[int, ...], complex]]:
    """
    Canonical basis reduction for Generalized Clifford Algebra C_n^(m).
    Generators satisfy:
        e_j * e_k = omega * e_k * e_j  (for j < k, omega = exp(2*pi*i / n))
        e_j^n = alpha_j * 1  (default alpha_j = 1.0)
    Keys are non-negative integer exponent tuples (k_1, ..., k_m) with 0 <= k_j < n.
    """
    m = num_generators
    sigs = tuple([1.0 + 0j] * m) if signatures is None else signatures
    k1_pad = tuple(k1) + (0,) * max(0, m - len(k1))
    k2_pad = tuple(k2) + (0,) * max(0, m - len(k2))

    phase_exp = 0
    scalar_mult = 1.0 + 0j
    res_k: list[int] = []

    for j in range(m):
        for k in range(j + 1, m):
            phase_exp = (phase_exp - k1_pad[k] * k2_pad[j]) % n_order

    for j in range(m):
        tot = k1_pad[j] + k2_pad[j]
        res_k.append(tot % n_order)
        if tot >= n_order:
            scalar_mult *= sigs[j] ** (tot // n_order)

    omega = cmath.exp(2j * cmath.pi / n_order)
    phase_factor = (omega**phase_exp) * scalar_mult
    return [(tuple(res_k), phase_factor)]


class GeneralizedCliffordSemiring(QuotientMonoidAlgebraSemiring[tuple[int, ...], complex]):
    """
    Generalized Clifford Algebra C_n^(m) Semiring (Clock-and-Shift Algebra / Generalized Dirac Algebra).

    Generators e_1, ..., e_m satisfy the commutation relation:
        e_j * e_k = omega * e_k * e_j  (for 1 <= j < k <= m)
    where omega = exp(2*pi*i / n) is a primitive n-th root of unity, and:
        e_j^n = alpha_j * 1

    Elements are sparse multivectors mapping exponent multi-indices (k_1, ..., k_m) in Z_n^m to complex coefficients.
    """

    def __init__(
        self,
        n_order: int = 3,
        num_generators: int = 2,
        signatures: tuple[complex, ...] | None = None,
    ):
        self.n_order = n_order
        self.num_generators = num_generators
        self.signatures = signatures

        def key_op(k1: tuple[int, ...], k2: tuple[int, ...]) -> tuple[int, ...]:
            k1_p = tuple(k1) + (0,) * max(0, self.num_generators - len(k1))
            k2_p = tuple(k2) + (0,) * max(0, self.num_generators - len(k2))
            return k1_p + k2_p

        def quotient_fn(key: tuple[int, ...], coeff: complex) -> Iterable[tuple[tuple[int, ...], complex]]:
            k1 = key[: self.num_generators]
            k2 = key[self.num_generators :]
            reds = _gca_blade_mul(
                k1, k2, n_order=self.n_order, num_generators=self.num_generators, signatures=self.signatures
            )
            return [(k, c * coeff) for k, c in reds]

        super().__init__(
            coeff_semiring=StandardSemiring[complex](),
            key_op=key_op,
            zero_key=tuple([0] * num_generators),
            quotient_fn=quotient_fn,
        )


def _quantum_clifford_blade_mul(
    k1: tuple[int, ...],
    k2: tuple[int, ...],
    q: complex = 1.0 + 0j,
    num_generators: int = 2,
    signatures: tuple[complex, ...] | None = None,
) -> list[tuple[tuple[int, ...], complex]]:
    """
    Canonical basis reduction for q-Deformed Quantum Clifford Algebra Cl_q(m).
    Generators satisfy:
        e_j * e_k = -q * e_k * e_j  (for j < k)
        e_j^2 = alpha_j * 1  (default alpha_j = 1.0)
    Keys are binary index tuples (k_1, ..., k_m) with k_j in {0, 1}.
    """
    m = num_generators
    sigs = tuple([1.0 + 0j] * m) if signatures is None else signatures
    k1_pad = tuple(k1) + (0,) * max(0, m - len(k1))
    k2_pad = tuple(k2) + (0,) * max(0, m - len(k2))

    inversions = 0
    scalar_mult = 1.0 + 0j
    res_k: list[int] = []

    for j in range(m):
        for k in range(j + 1, m):
            inversions += k1_pad[k] * k2_pad[j]

    for j in range(m):
        tot = k1_pad[j] + k2_pad[j]
        res_k.append(tot % 2)
        if tot >= 2:
            scalar_mult *= sigs[j] ** (tot // 2)

    phase_factor = ((-q) ** inversions) * scalar_mult
    return [(tuple(res_k), phase_factor)]


class QuantumCliffordSemiring(QuotientMonoidAlgebraSemiring[tuple[int, ...], complex]):
    """
    q-Deformed Quantum Clifford Algebra Cl_q(m) Semiring.

    Generators e_1, ..., e_m satisfy the braided commutation relation:
        e_j * e_k = -q * e_k * e_j  (for 1 <= j < k <= m)
        e_j^2 = alpha_j * 1

    When q = 1.0, this recovers standard orthogonal Clifford anticommutation.
    """

    def __init__(
        self,
        q: complex = 1.0 + 0j,
        num_generators: int = 2,
        signatures: tuple[complex, ...] | None = None,
    ):
        self.q = q
        self.num_generators = num_generators
        self.signatures = signatures

        def key_op(k1: tuple[int, ...], k2: tuple[int, ...]) -> tuple[int, ...]:
            k1_p = tuple(k1) + (0,) * max(0, self.num_generators - len(k1))
            k2_p = tuple(k2) + (0,) * max(0, self.num_generators - len(k2))
            return k1_p + k2_p

        def quotient_fn(key: tuple[int, ...], coeff: complex) -> Iterable[tuple[tuple[int, ...], complex]]:
            k1 = key[: self.num_generators]
            k2 = key[self.num_generators :]
            reds = _quantum_clifford_blade_mul(
                k1, k2, q=self.q, num_generators=self.num_generators, signatures=self.signatures
            )
            return [(k, c * coeff) for k, c in reds]

        super().__init__(
            coeff_semiring=StandardSemiring[complex](),
            key_op=key_op,
            zero_key=tuple([0] * num_generators),
            quotient_fn=quotient_fn,
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
    """
    Galois Finite Field GF(p^m) Semiring.
    Values are field elements represented as sparse polynomial vectors dict[int, int].
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

    def add(self, a: SparseVector[int, int], b: SparseVector[int, int]) -> SparseVector[int, int]:
        """
        Elementwise addition in GF(p).
        """
        result = dict(a)
        p = self.p
        for exp, coeff in b.items():
            sum_val = (result.get(exp, 0) + coeff) % p
            if sum_val == 0:
                result.pop(exp, None)
            else:
                result[exp] = sum_val
        return result


class DualNumberSemiring(Semiring[tuple[float, float]]):
    """
    The Dual Number Semiring (Quotient Ring R[ε]/(ε^2)).
    Values are pairs (val, der) representing dual numbers a + b*ε where ε^2 = 0.

    Algebraic Operations:
    - Addition: (a1, b1) + (a2, b2) = (a1 + a2, b1 + b2)
    - Multiplication: (a1, b1) * (a2, b2) = (a1 * a2, a1 * b2 + a2 * b1)  [Leibniz Product Rule]
    - Zero: (0.0, 0.0)
    - One: (1.0, 0.0)

    Used for: Forward-Mode Automatic Differentiation, tangent bundle propagation,
    and first-order gradient accumulation over graphs.
    """

    @property
    def zero(self) -> tuple[float, float]:
        return 0.0, 0.0

    @property
    def one(self) -> tuple[float, float]:
        return 1.0, 0.0

    def add(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        return a[0] + b[0], a[1] + b[1]

    def mul(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        # Leibniz Product Rule: (u*v, u*v' + v*u')
        return a[0] * b[0], a[0] * b[1] + b[0] * a[1]

    def nsum(self, a: tuple[float, float], n: int) -> tuple[float, float]:
        if n == 0:
            return 0.0, 0.0
        return a[0] * n, a[1] * n

    def power(self, a: tuple[float, float], n: int) -> tuple[float, float]:
        p, v = a
        if n == 0:
            return 1.0, 0.0
        return p**n, n * (p ** (n - 1)) * v

    def star(self, a: tuple[float, float]) -> tuple[float, float]:
        p, v = a
        if p >= 1.0:
            return float('inf'), float('inf')
        p_star = 1.0 / (1.0 - p)
        v_star = v * (p_star**2)
        return p_star, v_star


@functools.lru_cache(maxsize=32)
def _get_pascal_table(order: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(math.comb(n, k) for k in range(n + 1)) for n in range(order + 1))


class BinomialConvolutionSemiring(Semiring[tuple[float, ...]]):
    """
    Universal 1D Binomial Convolution Semiring over the Divided Power Quotient Ring R[ε] / (ε^{K+1}).
    Values are (K+1)-tuples (m_0, m_1, ..., m_K) where m_k represents the k-th raw derivative/moment.

    - Addition: Component-wise addition.
    - Multiplication: Binomial convolution (u ⊗ v)_k = sum_{j=0}^k binom(k, j) u_j v_{k-j}.
    - Zero: (0.0, ..., 0.0) of length K+1.
    - One: (1.0, 0.0, ..., 0.0) of length K+1.
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
        if n == 0:
            return self._one
        res = self._one
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: tuple[float, ...]) -> tuple[float, ...]:
        dim = self._dim
        if len(a) != dim:
            raise ValueError(f'Operand must have length {dim}')
        p = a[0]
        if p >= 1.0:
            return (float('inf'),) * dim
        if self.order == 0:
            return (1.0 / (1.0 - p),)
        if self.order == 1:
            p_star = 1.0 / (1.0 - p)
            v_star = a[1] * (p_star**2)
            return p_star, v_star

        scale = 1.0 / (1.0 - p)
        scaled_nil = (0.0, *(val * scale for val in a[1:]))
        cur_nil = self._one
        nil_sum = [0.0] * dim
        for _ in range(dim):
            for k in range(dim):
                nil_sum[k] += cur_nil[k]
            cur_nil = self.mul(cur_nil, scaled_nil)
        return tuple(val * scale for val in nil_sum)


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
    """
    Universal Multivariate Binomial Convolution Semiring over the Total Degree Quotient Ring
    R[ε1, ..., εd] / <ε^β : |β| = K+1>.

    Carrier is a sparse dict mapping multi-index tuple alpha in N_0^d (with sum(alpha) <= K)
    to real coefficient m_alpha.
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

    def power(self, a: dict[tuple[int, ...], float], n: int) -> dict[tuple[int, ...], float]:
        if n == 0:
            return self.one
        res = self.one
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

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
