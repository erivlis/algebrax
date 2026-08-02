"""
Algebraic, monoid algebra, quotient, Clifford, and Galois semirings.
"""

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

    def __init__(
        self, p: int = 2, irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1)
    ):
        self.p = p
        self.irreduc_poly = irreduc_poly

        def key_op(k1: int, k2: int) -> int:
            return k1 + k2

        def quotient_fn(key: int, coeff: int) -> Iterable[tuple[int, int]]:
            return _gf_poly_mod(key, coeff, p=self.p, irreduc_poly=self.irreduc_poly)

        super().__init__(
            coeff_semiring=StandardSemiring[int](),
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
