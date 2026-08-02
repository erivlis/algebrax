"""
Standard arithmetic semirings.
"""

import operator
from typing import Generic, TypeVar

from algebrax.semiring._base import Semiring

T_num = TypeVar('T_num', bound=float | int | complex)


class StandardSemiring(Semiring[T_num], Generic[T_num]):
    """
    The standard algebra over real numbers, integers, or complex numbers.
    (R, +, *, 0, 1)
    Used for: Standard Linear Algebra, Physics.
    """

    def __init__(self, dtype: type[T_num] = float):
        self._dtype = dtype
        self._zero = self._dtype(0)
        self._one = self._dtype(1)

    @property
    def zero(self) -> T_num:
        return self._zero

    @property
    def one(self) -> T_num:
        return self._one

    add = staticmethod(operator.add)
    mul = staticmethod(operator.mul)

    def nsum(self, a: T_num, n: int) -> T_num:
        # Standard semiring is a Ring, so negative n is allowed (subtraction).
        if n == 0:
            return self.zero
        return a * n

    def power(self, a: T_num, n: int) -> T_num:
        return a ** n

    def star(self, a: T_num) -> T_num:
        """
        Geometric series sum: 1 / (1 - a).
        Converges for |a| < 1.
        """
        if self._dtype is int:
            if a == 0:
                return 1
            raise ValueError('Star operation on StandardSemiring[int] is only defined for a=0.')

        if abs(a) >= 1:
            return self._dtype('inf') if self._dtype is float else complex('inf')

        return self.one / (self.one - a)
