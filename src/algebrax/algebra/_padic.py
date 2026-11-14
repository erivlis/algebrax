r"""
Unboxed $p$-adic field $\mathbb{Q}_p$ and non-archimedean tropical valuation.

Algebraic Signatures:
    p-Adic Field:           $\langle \mathbb{Q}_p, \mathbf{0}, +, -, \mathbf{1}, \cdot, ^{-1}, v_p, |\cdot|_p \rangle$
    Tropical Valuation:     $v_p(x \cdot y) = v_p(x) + v_p(y), \quad v_p(x + y) \ge \min(v_p(x), v_p(y))$
    Ultrametric Norm:       $|x|_p = p^{-v_p(x)}, \quad |x + y|_p \le \max(|x|_p, |y|_p)$
"""

from __future__ import annotations

from algebrax.algebra._field import Field
from algebrax.algebra._mixins import HasNorm


class PAdicField(Field[dict[int, int]], HasNorm[dict[int, int]]):
    r"""The $p$-adic field $\mathbb{Q}_p$ operating on unboxed sparse $p$-adic expansions `dict[int, int]`.

    Algebraic Signature:
        $\langle \mathbb{Q}_p, \mathbf{0}, +, -, \mathbf{1}, \cdot, ^{-1}, v_p, |\cdot|_p \rangle$

    Carrier:
        `dict[int, int]` — unboxed sparse mapping $\{k: a_k\}$ representing the truncated $p$-adic
        Laurent series:
        $$x = \sum_{k=v}^{M-1} a_k p^k \pmod{p^M}, \quad a_k \in \{1, \dots, p - 1\}$$
        Zero is represented by the empty dictionary `{}`.

    Properties:
        - Exact Tropical Valuation Homomorphism:
          $v_p : (\mathbb{Q}_p, +, \cdot) \to (\mathbb{R} \cup \{\infty\}, \min, +)$
          maps multiplication to tropical addition ($v_p(xy) = v_p(x) + v_p(y)$) and satisfies tropical
          min-plus superadditivity ($v_p(x + y) \ge \min(v_p(x), v_p(y))$).
        - Non-Archimedean Ultrametric: $|x + y|_p \le \max(|x|_p, |y|_p)$, with strict equality
          $|x + y|_p = \max(|x|_p, |y|_p)$ whenever $|x|_p \ne |y|_p$.
    """

    def __init__(self, p: int, precision: int = 16) -> None:
        if p < 2 or not self._is_prime(p):
            raise ValueError(f'p must be a prime integer >= 2, got {p}.')
        if precision < 1:
            raise ValueError(f'precision must be >= 1, got {precision}.')
        self._p = p
        self._precision = precision

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n in (2, 3):
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        d = 5
        while d * d <= n:
            if n % d == 0 or n % (d + 2) == 0:
                return False
            d += 6
        return True

    @property
    def p(self) -> int:
        r"""Prime base $p$ of the $p$-adic field $\mathbb{Q}_p$."""
        return self._p

    @property
    def precision(self) -> int:
        r"""Absolute exponent cutoff $M$ ($p^M$ modulus)."""
        return self._precision

    @property
    def zero(self) -> dict[int, int]:
        r"""Additive identity $\mathbf{0}$ (`{}`)."""
        return {}

    @property
    def one(self) -> dict[int, int]:
        r"""Multiplicative identity $\mathbf{1}$ (`{0: 1}`)."""
        return {0: 1}

    def is_zero(self, a: dict[int, int]) -> bool:
        r"""Test whether a $p$-adic expansion is zero modulo $p^M$."""
        return len(self._normalize(a)) == 0

    def _normalize(self, raw: dict[int, int], cutoff: int | None = None) -> dict[int, int]:
        """Canonicalize a sparse base-p digit mapping with carry propagation modulo p^cutoff."""
        cap = self._precision if cutoff is None else cutoff
        non_zero = {k: v for k, v in raw.items() if v != 0 and k < cap}
        if not non_zero:
            return {}
        v_min = min(non_zero.keys())
        p = self._p
        span = cap - v_min
        if span <= 0:
            return {}
        modulus = p**span
        total = 0
        for k, digit in non_zero.items():
            total += digit * (p ** (k - v_min))
        total %= modulus
        if total == 0:
            return {}

        out: dict[int, int] = {}
        exp = v_min
        while total > 0 and exp < cap:
            total, rem = divmod(total, p)
            if rem != 0:
                out[exp] = rem
            exp += 1
        return out

    def from_int(self, n: int) -> dict[int, int]:
        r"""Embed a Python integer $n \in \mathbb{Z}$ into $\mathbb{Q}_p$."""
        if n == 0:
            return {}
        return self._normalize({0: n})

    def from_rational(self, numerator: int, denominator: int = 1) -> dict[int, int]:
        r"""Embed a rational number $\frac{\text{numerator}}{\text{denominator}} \in \mathbb{Q}$ into $\mathbb{Q}_p$."""
        if denominator == 0:
            raise ZeroDivisionError('Rational denominator cannot be zero.')
        if numerator == 0:
            return {}
        p = self._p
        v_num = 0
        num_unit = numerator
        while num_unit != 0 and num_unit % p == 0:
            num_unit //= p
            v_num += 1

        v_den = 0
        den_unit = denominator
        while den_unit != 0 and den_unit % p == 0:
            den_unit //= p
            v_den += 1

        v = v_num - v_den
        span = self._precision - v
        if span <= 0:
            return {}
        modulus = p**span
        inv_den = pow(den_unit % modulus, -1, modulus)
        unit_prod = ((num_unit % modulus) * inv_den) % modulus
        return self._normalize({v: unit_prod})

    def valuation(self, x: dict[int, int]) -> float:
        r"""Compute the tropical min-plus $p$-adic valuation $v_p(x) = \min\{k \mid a_k \ne 0\}$ ($\infty$ for $0$)."""
        norm_x = self._normalize(x)
        if not norm_x:
            return float('inf')
        return float(min(norm_x.keys()))

    def norm(self, x: dict[int, int]) -> float:
        r"""Compute the non-archimedean $p$-adic absolute value $|x|_p = p^{-v_p(x)}$ ($0.0$ for $0$)."""
        norm_x = self._normalize(x)
        if not norm_x:
            return 0.0
        v = min(norm_x.keys())
        return float(self._p ** (-v))

    def distance(self, x: dict[int, int], y: dict[int, int]) -> float:
        r"""Compute the ultrametric $p$-adic distance $d_p(x, y) = |x - y|_p$."""
        return self.norm(self.sub(x, y))

    def add(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        r"""Add two $p$-adic numbers with base-$p$ carry propagation."""
        if not a:
            return self._normalize(b)
        if not b:
            return self._normalize(a)
        combined = dict(a)
        for k, v in b.items():
            combined[k] = combined.get(k, 0) + v
        return self._normalize(combined)

    def neg(self, a: dict[int, int]) -> dict[int, int]:
        r"""Compute additive inverse $-a$ in $\mathbb{Q}_p$."""
        norm_a = self._normalize(a)
        if not norm_a:
            return {}
        return self._normalize({k: -v for k, v in norm_a.items()})

    def sub(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        r"""Compute difference $a - b$ in $\mathbb{Q}_p$."""
        return self.add(a, self.neg(b))

    def mul(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        r"""Multiply two $p$-adic numbers via Cauchy series convolution modulo $p^M$."""
        if not a or not b:
            return {}
        prod: dict[int, int] = {}
        for ka, val_a in a.items():
            if val_a == 0:
                continue
            for kb, val_b in b.items():
                if val_b == 0:
                    continue
                k = ka + kb
                if k < self._precision:
                    prod[k] = prod.get(k, 0) + val_a * val_b
        return self._normalize(prod)

    def inv(self, a: dict[int, int]) -> dict[int, int]:
        r"""Compute multiplicative inverse $a^{-1}$ in $\mathbb{Q}_p$ via Hensel lifting."""
        norm_a = self._normalize(a)
        if not norm_a:
            raise ZeroDivisionError('Cannot invert zero element in PAdicField.')
        v = min(norm_a.keys())
        p = self._p
        v_inv = -v
        cutoff_inv = max(self._precision, self._precision - v)
        work_span = max(cutoff_inv - v_inv, self._precision + abs(v), 1)
        modulus = p**work_span
        u_int = sum(digit * (p ** (k - v)) for k, digit in norm_a.items()) % modulus
        u_inv = pow(u_int, -1, modulus)
        return self._normalize({v_inv: u_inv}, cutoff=cutoff_inv)

    def div(self, a: dict[int, int], b: dict[int, int]) -> dict[int, int]:
        r"""Compute quotient $a \cdot b^{-1}$ in $\mathbb{Q}_p$."""
        return self.mul(a, self.inv(b))


__all__ = ['PAdicField']
