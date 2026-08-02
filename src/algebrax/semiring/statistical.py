"""
Probability, expectation, and moment semirings.
"""

import math

from algebrax.semiring._base import Semiring


class LogSemiring(Semiring[float]):
    """
    The Log-Sum-Exp algebra.
    (R U {-inf}, logaddexp, +, -inf, 0)
    Used for: Probabilistic inference in log-domain (avoids underflow).
    Values represent log-probabilities.
    """

    @property
    def zero(self) -> float:
        return float('-inf')

    @property
    def one(self) -> float:
        return 0.0

    def add(self, a: float, b: float) -> float:
        # log(exp(a) + exp(b))
        if a == float('-inf'):
            return b
        if b == float('-inf'):
            return a

        # Numerical stability: log(exp(a) + exp(b)) = max + log(exp(a-max) + exp(b-max))
        max_val = max(a, b)
        return max_val + math.log(math.exp(a - max_val) + math.exp(b - max_val))

    def mul(self, a: float, b: float) -> float:
        # log(exp(a) * exp(b)) = a + b
        return a + b

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('LogSemiring does not support negative nsum')
        # log(n * exp(a)) = log(n) + a
        if n == 0:
            return float('-inf')
        if a == float('-inf'):
            return float('-inf')
        return a + math.log(n)

    def power(self, a: float, n: int) -> float:
        return a * n

    def star(self, a: float) -> float:
        if a >= 0.0:
            return float('inf')
        return -math.log1p(-math.exp(a))


class ExpectationSemiring(Semiring[tuple[float, float]]):
    """
    The First-Order Expectation Semiring.
    Values are pairs (prob, contribution).
    Used for: Computing expected values and gradients.

    IMPORTANT:
    The tuple (p, v) represents a probability `p` and a contribution `v = p * w`.
    If you have a weight `w` with probability `p`, you must initialize the value as `(p, p * w)`.

    Operations:
    (p1, v1) + (p2, v2) = (p1 + p2, v1 + v2)
    (p1, v1) * (p2, v2) = (p1 * p2, p1 * v2 + p2 * v1)
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
        # Product rule: E[XY] = E[X]Y + X E[Y] (sort of)
        # Actually: (p1*p2, p1*v2 + p2*v1)
        return a[0] * b[0], a[0] * b[1] + b[0] * a[1]

    def nsum(self, a: tuple[float, float], n: int) -> tuple[float, float]:
        # Expectation semiring is a Ring (component-wise addition)
        # So negative n is allowed.
        if n == 0:
            return 0.0, 0.0
        return a[0] * n, a[1] * n

    def power(self, a: tuple[float, float], n: int) -> tuple[float, float]:
        p, v = a
        if n == 0:
            return 1.0, 0.0
        return p ** n, n * (p ** (n - 1)) * v

    def star(self, a: tuple[float, float]) -> tuple[float, float]:
        p, v = a
        if p >= 1.0:
            return float('inf'), float('inf')
        p_star = 1.0 / (1.0 - p)
        v_star = v * (p_star ** 2)
        return p_star, v_star


class VarianceSemiring(Semiring[tuple[float, float, float, float]]):
    """
    The Second-Order Expectation Semiring (Li & Eisner, 2009).
    Values are 4-tuples (p, r, s, t).
    Used for: Computing Variance, Covariance, and Hessians.

    If r and s track the same variable (e.g., length), then:
    - p: Total probability (Z)
    - r: First moment (E[X] * Z)
    - s: First moment (E[X] * Z)
    - t: Second moment (E[X^2] * Z)

    Variance = (t/p) - (r/p)^2.

    Initialization:
    For a weight w with probability p:
    (p, p*w, p*w, p*w*w)
    """

    @property
    def zero(self) -> tuple[float, float, float, float]:
        return 0.0, 0.0, 0.0, 0.0

    @property
    def one(self) -> tuple[float, float, float, float]:
        return 1.0, 0.0, 0.0, 0.0

    def add(
            self, a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        return a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3]

    def mul(
            self, a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        p1, r1, s1, t1 = a
        p2, r2, s2, t2 = b

        # p = p1 * p2
        p = p1 * p2

        # r = p1*r2 + p2*r1
        r = p1 * r2 + p2 * r1

        # s = p1*s2 + p2*s1
        s = p1 * s2 + p2 * s1

        # t = p1*t2 + p2*t1 + r1*s2 + r2*s1
        t = p1 * t2 + p2 * t1 + r1 * s2 + r2 * s1

        return p, r, s, t

    def nsum(self, a: tuple[float, float, float, float], n: int) -> tuple[float, float, float, float]:
        if n == 0:
            return 0.0, 0.0, 0.0, 0.0
        return a[0] * n, a[1] * n, a[2] * n, a[3] * n

    def power(self, a: tuple[float, float, float, float], n: int) -> tuple[float, float, float, float]:
        if n == 0:
            return 1.0, 0.0, 0.0, 0.0
        res = (1.0, 0.0, 0.0, 0.0)
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        raise NotImplementedError('Kleene star not implemented for VarianceSemiring')


class DualNumberSemiring(ExpectationSemiring):
    """
    Alias for ExpectationSemiring.
    Used for: Automatic Differentiation (Forward Mode).
    Values are (value, derivative).
    """
