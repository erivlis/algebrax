"""
Optimization and path problems semirings.
"""

from algebrax.semiring._base import Semiring


class TropicalSemiring(Semiring[float]):
    """
    The Min-Plus algebra.
    (R U {inf}, min, +, inf, 0)
    Used for: Shortest Path problems (Graph Theory).
    """

    @property
    def zero(self) -> float:
        return float('inf')

    @property
    def one(self) -> float:
        return 0.0

    def add(self, a: float, b: float) -> float:
        return min(a, b)

    def mul(self, a: float, b: float) -> float:
        return a + b

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('TropicalSemiring does not support negative nsum')
        # Idempotent: min(a, a) = a
        if n == 0:
            return float('inf')
        return a

    def power(self, a: float, n: int) -> float:
        return a * n

    def star(self, a: float) -> float:
        if a < 0.0:
            return float('-inf')
        return 0.0


class ArcticSemiring(Semiring[float]):
    """
    The Max-Plus algebra.
    (R U {-inf}, max, +, -inf, 0)
    Used for: Longest Path problems, Viterbi decoding in log-domain.
    """

    @property
    def zero(self) -> float:
        return float('-inf')

    @property
    def one(self) -> float:
        return 0.0

    def add(self, a: float, b: float) -> float:
        return max(a, b)

    def mul(self, a: float, b: float) -> float:
        return a + b

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('ArcticSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return float('-inf')
        return a

    def power(self, a: float, n: int) -> float:
        return a * n

    def star(self, a: float) -> float:
        if a > 0.0:
            return float('inf')
        return 0.0


class ViterbiSemiring(Semiring[float]):
    """
    The Max-Product algebra.
    ([0, 1], max, *, 0, 1)
    Used for: Most Likely Path (HMMs).
    """

    @property
    def zero(self) -> float:
        return 0.0

    @property
    def one(self) -> float:
        return 1.0

    def add(self, a: float, b: float) -> float:
        return max(a, b)

    def mul(self, a: float, b: float) -> float:
        return a * b

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('ViterbiSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return 0.0
        return a

    def power(self, a: float, n: int) -> float:
        return a ** n

    def star(self, a: float) -> float:
        return 1.0


class ReliabilitySemiring(ViterbiSemiring):
    """
    Alias for ViterbiSemiring.
    Used for: Reliability analysis (max probability path).
    """


class BottleneckSemiring(Semiring[float]):
    """
    The Max-Min algebra.
    (R, max, min, -inf, +inf)
    Used for: Maximum Capacity Path (Widest Path).
    """

    @property
    def zero(self) -> float:
        return float('-inf')

    @property
    def one(self) -> float:
        return float('inf')

    def add(self, a: float, b: float) -> float:
        return max(a, b)

    def mul(self, a: float, b: float) -> float:
        return min(a, b)

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('BottleneckSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return float('-inf')
        return a

    def power(self, a: float, n: int) -> float:
        if n == 0:
            return float('inf')
        return a

    def star(self, a: float) -> float:
        return float('inf')


class MinTimesSemiring(Semiring[float]):
    """
    The Min-Times algebra.
    (R U {inf}, min, *, inf, 1)
    Used for: Finding the least probable path.
    """

    @property
    def zero(self) -> float:
        return float('inf')

    @property
    def one(self) -> float:
        return 1.0

    def add(self, a: float, b: float) -> float:
        return min(a, b)

    def mul(self, a: float, b: float) -> float:
        return a * b

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('MinTimesSemiring does not support negative nsum')
        # Idempotent: min(a, a) = a
        if n == 0:
            return float('inf')
        return a

    def power(self, a: float, n: int) -> float:
        return a ** n

    def star(self, a: float) -> float:
        if a < 1.0:
            return 0.0
        return 1.0
