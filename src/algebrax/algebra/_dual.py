"""
Dual number algebra R[eps]/(eps^2) for forward-mode automatic differentiation.
"""

from __future__ import annotations

from algebrax.algebra._semiring import Semiring


class DualNumberAlgebra(Semiring[tuple[float, float]]):
    r"""The Dual Number Algebra and Commutative Ring over $\mathbb{R}[\varepsilon]/(\varepsilon^2)$.

    Algebraic Signature:
        $\langle \mathbb{R}[\varepsilon]/(\varepsilon^2), +, \cdot, (0.0, 0.0), (1.0, 0.0) \rangle$

    Carrier:
        `tuple[float, float]` (Pair $(a, b)$ representing dual number $a + b\varepsilon$ where $\varepsilon^2 = 0$).

    Operations:
        - Addition ($+$): Elementwise addition $(a_1 + a_2, b_1 + b_2)$.
        - Multiplication ($\cdot$): Leibniz product rule $(a_1 a_2, a_1 b_2 + a_2 b_1)$.
        - Zero Element ($\mathbb{0}$): $(0.0, 0.0)$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0)$.

    Properties:
        Commutative, associative, ring quotient isomorphic to $\mathbb{R}[\varepsilon]/(\varepsilon^2)$.

    Applications:
        Forward-mode automatic differentiation, tangent bundle accumulation, first-order sensitivity analysis.
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

    def neg(self, a: tuple[float, float]) -> tuple[float, float]:
        """Additive inverse: -(u + v*eps) = -u - v*eps."""
        return -a[0], -a[1]

    def sub(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        """Difference: (u1 - u2, v1 - v2)."""
        return a[0] - b[0], a[1] - b[1]

    def smul(self, r: float, m: tuple[float, float]) -> tuple[float, float]:
        """Scalar scaling: r * (u, v) = (r*u, r*v)."""
        return r * m[0], r * m[1]

__all__ = [
    'DualNumberAlgebra',
]
