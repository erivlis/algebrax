"""
A module that defines various semirings and their properties.

This module includes the implementation of the `Semiring` protocol,
as well as specific semiring implementations such as the Standard,
Tropical, Arctic, and Boolean semirings. These semirings generalize
algebraic operations for diverse mathematical and computational
purposes, including optimization, graph theory, and reliability
analysis.
"""

import math
import operator
from collections.abc import Callable
from typing import Generic, Protocol, TypeVar

from algebrax.typing import K, SparseVector

__all__ = [
    'ArcticSemiring',
    'BooleanSemiring',
    'BottleneckSemiring',
    'DigitalSemiring',
    'DualNumberSemiring',
    'ExpectationSemiring',
    'KCollapsedSemiring',
    'KnotSemiring',
    'LogSemiring',
    'LukasiewiczSemiring',
    'MinTimesSemiring',
    'MonoidAlgebraSemiring',
    'PolynomialSemiring',
    'ProvenanceSemiring',
    'ReliabilitySemiring',
    'Semiring',
    'StandardSemiring',
    'StringSemiring',
    'TropicalSemiring',
    'VarianceSemiring',
    'ViterbiSemiring',
]

# region Protocol

V = TypeVar('V')


class Semiring(Protocol[V]):
    """
    A Protocol defining a Semiring (S, +, *, 0, 1).
    Used to generalize linear algebrax operations.
    """

    @property
    def zero(self) -> V:
        """The additive identity element (e.g., 0)."""
        ...

    @property
    def one(self) -> V:
        """The multiplicative identity element (e.g., 1)."""
        ...

    def add(self, a: V, b: V) -> V:
        """The addition operation (commutative, associative)."""
        ...

    def mul(self, a: V, b: V) -> V:
        """The multiplication operation (associative, distributes over add)."""
        ...

    def nsum(self, a: V, n: int) -> V:
        """
        The n-fold sum of a value (a + a + ... + a).
        Equivalent to scalar multiplication in a module.
        n must be non-negative for semirings that are not rings.
        """
        if n < 0:
            raise ValueError('nsum requires non-negative n for general semirings')
        if n == 0:
            return self.zero

        # Binary exponentiation for addition (scalar multiplication)
        res = self.zero
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.add(res, base)
            base = self.add(base, base)
            n //= 2
        return res

    def power(self, a: V, n: int) -> V:
        """
        The n-th power of a value (a * a * ... * a).
        n must be non-negative.
        """
        if n < 0:
            raise ValueError('power requires non-negative n')
        if n == 0:
            return self.one

        # Binary exponentiation for multiplication
        res = self.one
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: V) -> V:
        """
        The Kleene star of a value (sum of all powers).
        star(a) = 1 + a + a^2 + ...
        """
        ...


# endregion


# region Arithmetic

T_num = TypeVar('T_num', bound=float | int | complex)


class StandardSemiring(Semiring[T_num], Generic[T_num]):
    """
    The standard algebrax over real numbers, integers, or complex numbers.
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


# endregion


# region Optimization


class TropicalSemiring(Semiring[float]):
    """
    The Min-Plus algebrax.
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
    The Max-Plus algebrax.
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
    The Max-Product algebrax.
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
    The Max-Min algebrax.
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
    The Min-Times algebrax.
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


# endregion


# region Logic


class BooleanSemiring(Semiring[bool]):
    """
    The Boolean algebrax.
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
    The Lukasiewicz algebrax (Multi-valued Logic).
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


# endregion


# region Probability & Statistics


class LogSemiring(Semiring[float]):
    """
    The Log-Sum-Exp algebrax.
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


# endregion


# region Structures


class StringSemiring(Semiring[set[str]]):
    """
    The Formal Language algebrax.
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


T = TypeVar('T', bound=float | int | complex)


class MonoidAlgebraSemiring(Semiring[SparseVector[K, T]], Generic[K, T]):
    """
    The Monoid Algebra Semiring R[M] over a generic coefficient semiring R and monoid M.
    Values are formal linear combinations sum_{m in M} a_m m, represented as sparse mappings
    from key (monoid element m) to coefficient (a_m in R).

    - Addition: Elementwise coefficient addition in R.
    - Multiplication: Convolution using monoid multiplication (key_op) and coefficient multiplication in R.
    - Additive Identity (zero): The empty mapping {}.
    - Multiplicative Identity (one): {zero_key: coeff_semiring.one}.
    """

    def __init__(
            self,
            coeff_semiring: Semiring[T],
            key_op: Callable[[K, K], K] = operator.add,
            zero_key: K = 0,
    ):
        self.coeff_semiring = coeff_semiring
        self.key_op = key_op
        self.zero_key = zero_key

    @property
    def zero(self) -> SparseVector[K, T]:
        return {}

    @property
    def one(self) -> SparseVector[K, T]:
        return {self.zero_key: self.coeff_semiring.one}

    def add(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        result = dict(a)
        coeff_add = self.coeff_semiring.add
        zero = self.coeff_semiring.zero
        for exp, coeff in b.items():
            new_coeff = coeff_add(result.get(exp, zero), coeff)
            if new_coeff == zero:
                result.pop(exp, None)
            else:
                result[exp] = new_coeff
        return result

    def mul(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        if not a or not b:
            return {}

        result: dict[K, T] = {}
        key_op = self.key_op
        coeff_mul = self.coeff_semiring.mul
        coeff_add = self.coeff_semiring.add
        zero = self.coeff_semiring.zero

        for e1, c1 in a.items():
            for e2, c2 in b.items():
                new_key = key_op(e1, e2)
                new_coeff = coeff_mul(c1, c2)

                current_coeff = result.get(new_key, zero)
                sum_coeff = coeff_add(current_coeff, new_coeff)

                if sum_coeff == zero:
                    result.pop(new_key, None)
                else:
                    result[new_key] = sum_coeff
        return result

    def nsum(self, a: SparseVector[K, T], n: int) -> SparseVector[K, T]:
        if n == 0:
            return {}
        result = {}
        coeff_nsum = self.coeff_semiring.nsum
        zero = self.coeff_semiring.zero
        for exp, coeff in a.items():
            scaled = coeff_nsum(coeff, n)
            if scaled != zero:
                result[exp] = scaled
        return result

    def star(self, a: SparseVector[K, T]) -> SparseVector[K, T]:
        raise NotImplementedError('Kleene star not implemented for MonoidAlgebraSemiring')


class KnotSemiring(MonoidAlgebraSemiring[str, T], Generic[T]):
    """
    The Knot Semiring (Skein Module) over a generic coefficient semiring.
    Subclass of MonoidAlgebraSemiring where keys are knot strings and multiplication is the connected sum (#).

    - Addition: Formal sum of knots.
    - Multiplication: Connected sum (#) distributed over formal sums.
    - Additive Identity (zero): Empty mapping (no knots).
    - Multiplicative Identity (one): The unknot 'U' with coefficient one.

    Knot Representation:
    - Prime knots are represented by their standard notation (e.g., '3_1', '4_1').
    - The unknot is 'U'.
    - Composite knots are represented by joining prime knot names with '#'.
      The order is canonicalized by sorting.
      Example: The connected sum of '3_1' and '4_1' is '3_1#4_1'.
    """

    @staticmethod
    def _combine_knots(k1: str, k2: str) -> str:
        """Helper to compute the connected sum of two knot identifiers."""
        if k1 == 'U':
            return k2
        if k2 == 'U':
            return k1

        # For commutativity, sort the prime knot components.
        parts = k1.split('#') + k2.split('#')
        return '#'.join(sorted(parts))

    def __init__(self, coeff_semiring: Semiring[T] = StandardSemiring(int)):
        super().__init__(
            coeff_semiring=coeff_semiring,
            key_op=self._combine_knots,
            zero_key='U',
        )


class PolynomialSemiring(MonoidAlgebraSemiring[int, T], Generic[T]):
    """
    Univariate Polynomial Semiring R[x] over a coefficient semiring R.
    Specialized subclass of MonoidAlgebraSemiring where keys are non-negative integer exponents (N_0, +).
    """

    def __init__(self, coeff_semiring: Semiring[T]):
        super().__init__(coeff_semiring, key_op=operator.add, zero_key=0)


class ProvenanceSemiring(MonoidAlgebraSemiring[tuple[str, ...], int]):
    """
    The Polynomial Provenance Semiring N[X].
    Subclass of MonoidAlgebraSemiring where keys are sorted tuples of variable names (monomials)
    and coefficients are occurrence counts in N.
    Example: {('x', 'y'): 2, ('z',): 1} represents 2xy + z.

    Used for: Tracking which facts contributed to a result and how many times.
    """

    @staticmethod
    def _combine_monomials(t1: tuple[str, ...], t2: tuple[str, ...]) -> tuple[str, ...]:
        """Multiply two monomials by concatenating and sorting variable names."""
        return tuple(sorted(t1 + t2))

    def __init__(self, coeff_semiring: Semiring[int] = StandardSemiring(int)):
        super().__init__(
            coeff_semiring=coeff_semiring,
            key_op=self._combine_monomials,
            zero_key=(),
        )

    def mul(self, a: dict[tuple[str, ...], int], b: dict[tuple[str, ...], int]) -> dict[tuple[str, ...], int]:
        result: dict[tuple[str, ...], int] = {}
        if not a or not b:
            return {}

        for term1, coeff1 in a.items():
            for term2, coeff2 in b.items():
                new_term = tuple(sorted(term1 + term2))
                new_coeff = coeff1 * coeff2
                val = result.get(new_term, 0) + new_coeff
                if val == 0:
                    result.pop(new_term, None)
                else:
                    result[new_term] = val
        return result

# endregion
