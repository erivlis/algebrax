r"""
Field protocol and implementations for algebraic structures with multiplicative division.

Algebraic Signatures (EP-0150 AMDS):
    Field: $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, ^{-1} \rangle$
           with $a \cdot b = b \cdot a$
"""

import math
from collections.abc import Iterable
from fractions import Fraction
from typing import Literal, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import (
    HasAdd,
    HasInv,
    HasMul,
    HasNeg,
    HasOne,
    HasZero,
    HasZeroPred,
    LawAssociative,
    LawCommutative,
)
from algebrax.algebra._monoid_algebra import QuotientMonoidAlgebraSemiring

V = TypeVar('V')


@runtime_checkable
class Field(
    HasZero[V],
    HasZeroPred[V],
    HasAdd[V],
    HasNeg[V],
    HasOne[V],
    HasMul[V],
    HasInv[V],
    LawAssociative,
    LawCommutative,
    Protocol,
):
    r"""A commutative division ring where every non-zero element has a multiplicative inverse.

    Combines an additive abelian group $\langle V, \mathbf{0}, +, - \rangle$
    and a multiplicative abelian group on non-zero elements $\langle V^\times, \mathbf{1}, \cdot, ^{-1} \rangle$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, ^{-1} \rangle$
        with $a \cdot b = b \cdot a$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `is_zero(a)`: Test whether $a == \mathbf{0}$ (`HasZeroPred[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `neg(a)`: Additive inverse $-a$ (`HasNeg[V]`).
        - `sub(a, b)`: Derived difference $a - b = a + (-b)$ (`HasNeg[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Commutative, associative multiplication (`HasMul[V]`).
        - `inv(a)`: Multiplicative inverse $a^{-1}$ for $a \ne \mathbf{0}$ (`HasInv[V]`).
        - `div(a, b)`: Derived quotient $a \cdot b^{-1}$ for $b \ne \mathbf{0}$ (`HasInv[V]`).

    Applications:
        Rational arithmetic ($\mathbb{Q}$), real analysis ($\mathbb{R}$), complex calculus ($\mathbb{C}$),
        finite Galois fields ($\mathbb{F}_p, \operatorname{GF}(p^m)$), Gaussian elimination, exact matrix solvers.
    """

    @property
    def is_associative(self) -> Literal[True]:
        return True

    @property
    def is_commutative(self) -> Literal[True]:
        return True


# =============================================================================
# Concrete Field Implementations
# =============================================================================


class StandardField(Field[V]):
    r"""Typeclass implementation of `Field` for standard numeric types.

    Supports `float`, `Fraction`, `complex`, and arbitrary floating-point/exact types.
    """

    def __init__(self, dtype: type[V] = float, tol: float = 1e-12) -> None:  # type: ignore[assignment]
        self._dtype = dtype
        self._tol = tol
        self._zero = dtype(0)  # type: ignore[call-arg]
        self._one = dtype(1)  # type: ignore[call-arg]

    @property
    def zero(self) -> V:
        return self._zero

    @property
    def one(self) -> V:
        return self._one

    def add(self, a: V, b: V) -> V:
        return a + b  # type: ignore[operator]

    def sub(self, a: V, b: V) -> V:
        return a - b  # type: ignore[operator]

    def neg(self, a: V) -> V:
        return -a  # type: ignore[operator]

    def mul(self, a: V, b: V) -> V:
        return a * b  # type: ignore[operator]

    def is_zero(self, a: V) -> bool:
        if isinstance(a, float):
            return math.isclose(a, 0.0, abs_tol=self._tol)
        if isinstance(a, complex):
            return abs(a) <= self._tol
        if isinstance(a, Fraction):
            return a.numerator == 0
        return a == self._zero

    def inv(self, a: V) -> V:
        if self.is_zero(a):
            raise ZeroDivisionError('Cannot invert field zero element.')
        return self._one / a  # type: ignore[operator]

    def div(self, a: V, b: V) -> V:
        if self.is_zero(b):
            raise ZeroDivisionError('Cannot divide by field zero element.')
        return a / b  # type: ignore[operator]


RationalField = Field[Fraction]
RealField = Field[float]
ComplexField = Field[complex]


def _is_prime(n: int) -> bool:
    """Return True iff n is a prime integer >= 2 (rejecting bools)."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    limit = math.isqrt(n)
    d = 5
    while d <= limit:
        if n % d == 0 or n % (d + 2) == 0:
            return False
        d += 6
    return True


class ModularField(Field[int]):
    r"""Finite Galois field $\mathbb{F}_p = \mathbb{Z}/p\mathbb{Z}$ for prime $p$.

    Carriers are unboxed native Python integers $0 \le k < p$.
    Arithmetic is performed strictly modulo $p$ with zero object allocation.
    """

    def __init__(self, p: int) -> None:
        if not _is_prime(p):
            raise ValueError(f'Field characteristic must be a prime >= 2, got {p!r}.')
        self._p = p

    @property
    def p(self) -> int:
        return self._p

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, a: int, b: int) -> int:
        return (a + b) % self._p

    def sub(self, a: int, b: int) -> int:
        return (a - b) % self._p

    def neg(self, a: int) -> int:
        return (-a) % self._p

    def mul(self, a: int, b: int) -> int:
        return (a * b) % self._p

    def is_zero(self, a: int) -> bool:
        return (a % self._p) == 0

    def inv(self, a: int) -> int:
        a_mod = a % self._p
        if a_mod == 0:
            raise ZeroDivisionError('Cannot invert zero element in finite field.')
        return pow(a_mod, -1, self._p)

    def div(self, a: int, b: int) -> int:
        b_mod = b % self._p
        if b_mod == 0:
            raise ZeroDivisionError('Cannot divide by zero element in finite field.')
        return (a * pow(b_mod, -1, self._p)) % self._p


def _gf_poly_mod(
    exp: int, coeff: int, p: int = 2, irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1)
) -> list[tuple[int, int]]:
    """
    Reduce polynomial term coeff * x^exp modulo irreducible polynomial irreduc_poly in GF(p).
    Default irreduc_poly: x^8 + x^4 + x^3 + x + 1 (AES GF(2^8) field).
    """
    m = len(irreduc_poly) - 1
    c = coeff % p
    if c == 0:
        return []

    if exp < m:
        return [(exp, c)]

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


def _gf_reduce_dict(
    a: dict[int, int],
    p: int,
    irreduc_poly: tuple[int, ...],
) -> dict[int, int]:
    """Reduce a sparse GF(p^m) polynomial dict canonically modulo p and irreduc_poly."""
    if not a:
        return {}
    m = len(irreduc_poly) - 1
    res: dict[int, int] = {}
    for deg, coeff in a.items():
        if deg < 0:
            raise ValueError(f'Negative degree {deg} is invalid in GF(p^m).')
        c = coeff % p
        if c == 0:
            continue
        if deg < m:
            nv = (res.get(deg, 0) + c) % p
            if nv == 0:
                res.pop(deg, None)
            else:
                res[deg] = nv
        else:
            for r_deg, r_coeff in _gf_poly_mod(deg, c, p=p, irreduc_poly=irreduc_poly):
                nv = (res.get(r_deg, 0) + r_coeff) % p
                if nv == 0:
                    res.pop(r_deg, None)
                else:
                    res[r_deg] = nv
    return res


def _gf_poly_trim(poly: list[int], p: int) -> list[int]:
    """Normalize polynomial coefficient list modulo p by stripping trailing zeros."""
    res = [c % p for c in poly]
    while res and res[-1] == 0:
        res.pop()
    return res


def _gf_poly_divmod(a: list[int], b: list[int], p: int) -> tuple[list[int], list[int]]:
    """Euclidean division of polynomials over F_p returning (quotient, remainder)."""
    rem = _gf_poly_trim(a, p)
    div = _gf_poly_trim(b, p)
    if not div:
        raise ZeroDivisionError('Cannot divide by zero polynomial in GF(p^m).')
    deg_b = len(div) - 1
    inv_lc = pow(div[-1], -1, p)
    if len(rem) - 1 < deg_b:
        return [], rem
    quot = [0] * (len(rem) - deg_b)
    while len(rem) - 1 >= deg_b:
        shift = len(rem) - 1 - deg_b
        factor = (rem[-1] * inv_lc) % p
        quot[shift] = factor
        for i, coeff in enumerate(div):
            rem[shift + i] = (rem[shift + i] - factor * coeff) % p
        rem = _gf_poly_trim(rem, p)
    return _gf_poly_trim(quot, p), rem


def _gf_poly_sub_mul(a: list[int], q: list[int], b: list[int], p: int) -> list[int]:
    """Compute a - q * b in F_p[x]."""
    prod_len = len(q) + len(b) - 1 if q and b else 0
    out_len = max(len(a), prod_len)
    res = [a[i] if i < len(a) else 0 for i in range(out_len)]
    for i, cq in enumerate(q):
        if cq:
            for j, cb in enumerate(b):
                if cb:
                    res[i + j] = (res[i + j] - cq * cb) % p
    return _gf_poly_trim(res, p)


def _gf_poly_inv(a: dict[int, int], p: int, irreduc_poly: tuple[int, ...]) -> dict[int, int]:
    """Compute multiplicative inverse of non-zero element a in GF(p^m) via Extended Euclidean Algorithm."""
    reduced = _gf_reduce_dict(a, p, irreduc_poly)
    max_deg = max(reduced.keys(), default=-1)
    if max_deg < 0:
        raise ZeroDivisionError('Cannot invert zero element in Galois field.')
    r0 = [0] * (max_deg + 1)
    for d, c in reduced.items():
        r0[d] = c
    r0 = _gf_poly_trim(r0, p)
    r1 = _gf_poly_trim(list(irreduc_poly), p)
    s0: list[int] = [1]
    s1: list[int] = []
    while r1:
        q, r2 = _gf_poly_divmod(r0, r1, p)
        s2 = _gf_poly_sub_mul(s0, q, s1, p)
        r0, r1 = r1, r2
        s0, s1 = s1, s2
    if len(r0) != 1:
        raise ZeroDivisionError('Element is not invertible modulo the configured polynomial.')
    inv_g = pow(r0[0], -1, p)
    scaled = [(c * inv_g) % p for c in s0]
    _, rem = _gf_poly_divmod(scaled, list(irreduc_poly), p)
    return {deg: coeff for deg, coeff in enumerate(rem) if coeff != 0}


class GaloisField(QuotientMonoidAlgebraSemiring[int, int], Field[dict[int, int]]):
    r"""Finite Galois extension field $\mathrm{GF}(p^m) \cong \mathbb{F}_p[x] / \langle P(x) \rangle$.

    Algebraic Signature:
        $\langle \mathrm{GF}(p^m), \emptyset, \operatorname{is\_zero}, +, -, \{0: 1\}, \cdot, ^{-1} \rangle$

    Carrier:
        `dict[int, int]` (Sparse polynomial remainder vectors modulo irreducible polynomial $P(x)$ over $\mathbb{F}_p$).

    Operations:
        - Addition ($+$): Elementwise polynomial addition in $\mathbb{F}_p$ reduced modulo $P(x)$.
        - Negation ($-$) / Subtraction: Modular coefficient negation in $\mathbb{F}_p$ reduced modulo $P(x)$.
        - Multiplication ($\cdot$): Polynomial multiplication reduced modulo irreducible polynomial $P(x)$.
        - Inverse ($^{-1}$) / Division: Extended Euclidean inverse modulo $P(x)$ over $\mathbb{F}_p$.
        - Zero Element ($\mathbb{0}$): `{}` (empty polynomial).
        - One Element ($\mathbb{1}$): `{0: 1}` ($x^0 = 1$).

    Properties:
        Exact finite `Field` (and `Semiring`), commutative, associative, distributive.

    Applications:
        Error-correcting codes (Reed-Solomon), cryptography (AES $\mathrm{GF}(2^8)$),
        and multivariate polynomials / Gröbner bases over $\mathrm{GF}(p^m)$.
    """

    def __init__(self, p: int = 2, irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1)):
        if not _is_prime(p):
            raise ValueError(f'Field characteristic must be a prime >= 2, got {p!r}.')
        if len(irreduc_poly) < 2 or (irreduc_poly[-1] % p) == 0:
            raise ValueError(
                'irreduc_poly must have degree >= 1 with a non-zero leading coefficient modulo p.'
            )
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

    @property
    def is_associative(self) -> Literal[True]:
        return True

    @property
    def is_commutative(self) -> Literal[True]:
        return True

    def is_zero(self, a: dict[int, int]) -> bool:
        """Return True iff `a` reduces to zero modulo p and `irreduc_poly`."""
        return not _gf_reduce_dict(a, self.p, self.irreduc_poly)

    def add(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        """Return canonical sum a + b in GF(p^m)."""
        if not a:
            return _gf_reduce_dict(b, self.p, self.irreduc_poly)
        if not b:
            return _gf_reduce_dict(a, self.p, self.irreduc_poly)
        combined = dict(a)
        for d, c in b.items():
            combined[d] = combined.get(d, 0) + c
        return _gf_reduce_dict(combined, self.p, self.irreduc_poly)

    def neg(self, a: dict[int, int]) -> dict[int, int]:
        """Return canonical additive inverse -a in GF(p^m)."""
        red = _gf_reduce_dict(a, self.p, self.irreduc_poly)
        return {d: (-c) % self.p for d, c in red.items()}

    def sub(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        """Return canonical difference a - b in GF(p^m)."""
        return self.add(a, self.neg(b))

    def inv(self, a: dict[int, int]) -> dict[int, int]:
        """Return multiplicative inverse a^{-1} in GF(p^m)."""
        return _gf_poly_inv(a, self.p, self.irreduc_poly)

    def div(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        """Return quotient a / b = a * b^{-1} in GF(p^m)."""
        return self.mul(a, self.inv(b))


__all__ = [
    'ComplexField',
    'Field',
    'GaloisField',
    'ModularField',
    'RationalField',
    'RealField',
    'StandardField',
]
