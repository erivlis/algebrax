"""
Standard arithmetic semirings.
"""

import operator
from numbers import Number
from typing import Generic, TypeVar

from algebrax.semiring._base import Semiring

T_num = TypeVar('T_num', bound=float | int | complex | Number)


class StandardSemiring(Semiring[T_num], Generic[T_num]):
    r"""The standard arithmetic semiring (unital ring) over numbers.

    Algebraic Signature:
        $\langle \mathbb{K}, +, \times, 0, 1 \rangle$

    Carrier:
        `float`, `int`, `complex`, or numeric types ($\mathbb{K} \in \{\mathbb{R}, \mathbb{Z}, \mathbb{C}\}$).

    Operations:
        - Addition ($\oplus$): Standard addition $a + b$
        - Multiplication ($\otimes$): Standard multiplication $a \times b$
        - Zero Element ($\mathbb{0}$): $0$
        - One Element ($\mathbb{1}$): $1$

    Properties:
        Commutative, Associative, Distributive, Ring (supports additive inverses).

    Applications:
        Classical linear algebra, quantum state amplitudes, numerical simulations.
    """

    def __init__(self, dtype: type[T_num] = float) -> None:
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
        return a**n

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


class ModularSemiring(Semiring[int]):
    r"""The modular integer ring $\mathbb{Z}/p\mathbb{Z}$.

    Algebraic Signature:
        $\langle \mathbb{Z}_p, + \pmod p, \times \pmod p, 0, 1 \rangle$

    Carrier:
        `int` in residue class $\{0, 1, \dots, p-1\}$.

    Operations:
        - Addition ($\oplus$): $(a + b) \pmod p$
        - Multiplication ($\otimes$): $(a \times b) \pmod p$
        - Zero Element ($\mathbb{0}$): $0$
        - One Element ($\mathbb{1}$): $1 \pmod p$

    Properties:
        Commutative, Associative, Finite Ring (Field if $p$ is prime).

    Applications:
        Modular arithmetic, cyclic groups, finite fields, cryptography.
    """

    def __init__(self, p: int = 2):
        if p <= 0:
            raise ValueError('ModularSemiring modulus p must be positive')
        self.p = p

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1 % self.p

    def add(self, a: int, b: int) -> int:
        return (a + b) % self.p

    def mul(self, a: int, b: int) -> int:
        return (a * b) % self.p

    def nsum(self, a: int, n: int) -> int:
        return (a * n) % self.p

    def power(self, a: int, n: int) -> int:
        return pow(a, n, self.p)
