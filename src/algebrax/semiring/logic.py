"""
Logic and fuzzy set semirings.
"""

from algebrax.semiring._base import Semiring


class BooleanSemiring(Semiring[bool]):
    """
    The Boolean algebra.
    ({T, F}, OR, AND, F, T)
    Used for: Reachability, Transitive Closure.
    """

    @property
    def zero(self) -> bool:
        return False

    @property
    def one(self) -> bool:
        return True

    def add(self, a: bool, b: bool) -> bool:
        return a or b

    def mul(self, a: bool, b: bool) -> bool:
        return a and b

    def nsum(self, a: bool, n: int) -> bool:
        if n < 0:
            raise ValueError('BooleanSemiring does not support negative nsum')
        # Idempotent: a or a = a
        if n == 0:
            return False
        return a

    def power(self, a: bool, n: int) -> bool:
        if n == 0:
            return True
        return a

    def star(self, a: bool) -> bool:
        return True


class LukasiewiczSemiring(Semiring[float]):
    """
    The Lukasiewicz algebra (Multi-valued Logic).
    ([0, 1], max, max(0, a+b-1), 0, 1)
    Used for: Fuzzy Logic.
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
        return max(0.0, a + b - 1.0)

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('LukasiewiczSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return 0.0
        return a

    def power(self, a: float, n: int) -> float:
        if n == 0:
            return 1.0
        return max(0.0, n * a - (n - 1))

    def star(self, a: float) -> float:
        return 1.0


class DigitalSemiring(Semiring[float | int]):
    """
    The Digital Semiring (W, (+), (*)).
    W = N U {inf}.
    (a) = sum of digits of a.

    Addition (+):
        If (a) > (b), return a.
        If (a) < (b), return b.
        If (a) == (b), return max(a, b).
        Identity: 0.

    Multiplication (*):
        If (a) < (b), return a.
        If (a) > (b), return b.
        If (a) == (b), return min(a, b).
        Identity: inf.

    Used for: Post-Quantum Cryptography (Huang et al., 2024).
    """

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> float:
        return float('inf')

    @staticmethod
    def _digit_sum(n: float | int) -> float:
        if n == float('inf'):
            return float('inf')
        if n == 0:
            return 0
        # Sum of digits
        s = 0
        temp = int(n)
        while temp > 0:
            s += temp % 10
            temp //= 10
        return s

    def add(self, a: float | int, b: float | int) -> float | int:
        da = self._digit_sum(a)
        db = self._digit_sum(b)

        if da > db:
            return a
        if da < db:
            return b
        # da == db
        return max(a, b)

    def mul(self, a: float | int, b: float | int) -> float | int:
        da = self._digit_sum(a)
        db = self._digit_sum(b)

        if da < db:
            return a
        if da > db:
            return b
        # da == db
        return min(a, b)

    def nsum(self, a: float | int, n: int) -> float | int:
        # Idempotent: a + a = a
        if n == 0:
            return 0
        return a

    def power(self, a: float | int, n: int) -> float | int:
        if n == 0:
            return float('inf')
        if n == 1:
            return a

        # Binary exponentiation
        res = float('inf')
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: float | int) -> float | int:
        raise NotImplementedError('Kleene star not implemented for DigitalSemiring')
