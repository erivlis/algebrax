"""
Bounded structures semirings.
"""

from algebrax.semiring._base import Semiring


class StringSemiring(Semiring[set[str]]):
    """
    The Formal Language algebra.
    (P(Sigma*), Union, Concatenation, {}, {""})
    Used for: Regular Expressions, Path Languages.
    Values are Sets of Strings.
    """

    @property
    def zero(self) -> set[str]:
        return set()

    @property
    def one(self) -> set[str]:
        return {''}

    def add(self, a: set[str], b: set[str]) -> set[str]:
        return a | b

    def mul(self, a: set[str], b: set[str]) -> set[str]:
        # Concatenation of sets: {xy | x in a, y in b}
        if not a or not b:
            return set()
        return {x + y for x in a for y in b}

    def nsum(self, a: set[str], n: int) -> set[str]:
        if n < 0:
            raise ValueError('StringSemiring does not support negative nsum')
        # Idempotent: a | a = a
        if n == 0:
            return set()
        return a

    def power(self, a: set[str], n: int) -> set[str]:
        if n == 0:
            return {''}
        if n == 1:
            return a
        res = {''}
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: set[str]) -> set[str]:
        raise NotImplementedError('Kleene star not supported for StringSemiring')


class KCollapsedSemiring(Semiring[int]):
    """
    The K-Collapsed Natural Numbers.
    Values are integers in [0, K].
    Used for: Bounded counting, cycle detection.
    """

    def __init__(self, k: int = 1):
        self.k = k

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, a: int, b: int) -> int:
        return min(self.k, a + b)

    def mul(self, a: int, b: int) -> int:
        return min(self.k, a * b)

    def nsum(self, a: int, n: int) -> int:
        if n < 0:
            raise ValueError('KCollapsedSemiring does not support negative nsum')
        if n == 0:
            return 0
        return min(self.k, a * n)

    def power(self, a: int, n: int) -> int:
        if n == 0:
            return 1
        # a^n in this semiring is min(k, a^n)
        # We can compute a^n normally and clamp.
        return min(self.k, a ** n)

    def star(self, a: int) -> int:
        # 1 + a + a^2 + ...
        # If a >= 1, sum diverges to infinity, so clamped to k.
        # If a = 0, sum is 1.
        if a == 0:
            return 1
        return self.k
