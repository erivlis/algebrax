r"""
Field protocol and implementations for algebraic structures with multiplicative division.

Algebraic Signatures (EP-0150 AMDS):
    Field: $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, ^{-1} \rangle$
           with $a \cdot b = b \cdot a$
"""

import math
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


IntegerField = Field[int]
RationalField = Field[Fraction]
RealField = Field[float]
ComplexField = Field[complex]


class ModularField(Field[int]):
    r"""Finite Galois field $\mathbb{F}_p = \mathbb{Z}/p\mathbb{Z}$ for prime $p$.

    Carriers are unboxed native Python integers $0 \le k < p$.
    Arithmetic is performed strictly modulo $p$ with zero object allocation.
    """

    def __init__(self, p: int) -> None:
        if p < 2:
            raise ValueError(f'Field characteristic must be a prime >= 2, got {p}.')
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


__all__ = [
    'ComplexField',
    'Field',
    'IntegerField',
    'ModularField',
    'RationalField',
    'RealField',
    'StandardField',
]
