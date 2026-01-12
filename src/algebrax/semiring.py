import math
from typing import Protocol, TypeVar

V = TypeVar('V')

__all__ = [
    'ArcticSemiring',
    'BooleanSemiring',
    'BottleneckSemiring',
    'DigitalSemiring',
    'DualNumberSemiring',
    'ExpectationSemiring',
    'KCollapsedSemiring',
    'LogSemiring',
    'LukasiewiczSemiring',
    'MinTimesSemiring',
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


class Semiring(Protocol[V]):
    """
    A Protocol defining a Semiring (S, +, *, 0, 1).
    Used to generalize linear algebra operations.
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


class StandardSemiring:
    """
    The standard algebra over real numbers.
    (R, +, *, 0, 1)
    Used for: Standard Linear Algebra, Physics.
    """

    @property
    def zero(self) -> float:
        return 0.0

    @property
    def one(self) -> float:
        return 1.0

    @staticmethod
    def add(a: float, b: float) -> float:
        return a + b

    @staticmethod
    def mul(a: float, b: float) -> float:
        return a * b

    @staticmethod
    def nsum(a: float, n: int) -> float:
        # Standard semiring is a Ring, so negative n is allowed (subtraction).
        if n == 0:
            return 0.0
        return a * n

    @staticmethod
    def power(a: float, n: int) -> float:
        return a**n

    @staticmethod
    def star(a: float) -> float:
        if a >= 1.0:
            return float('inf')
        return 1.0 / (1.0 - a)


# endregion


# region Optimization


class TropicalSemiring:
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

    @staticmethod
    def add(a: float, b: float) -> float:
        return min(a, b)

    @staticmethod
    def mul(a: float, b: float) -> float:
        return a + b

    @staticmethod
    def nsum(a: float, n: int) -> float:
        if n < 0:
            raise ValueError('TropicalSemiring does not support negative nsum')
        # Idempotent: min(a, a) = a
        if n == 0:
            return float('inf')
        return a

    @staticmethod
    def power(a: float, n: int) -> float:
        return a * n

    @staticmethod
    def star(a: float) -> float:
        if a < 0.0:
            return float('-inf')
        return 0.0


class ArcticSemiring:
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

    @staticmethod
    def add(a: float, b: float) -> float:
        return max(a, b)

    @staticmethod
    def mul(a: float, b: float) -> float:
        return a + b

    @staticmethod
    def nsum(a: float, n: int) -> float:
        if n < 0:
            raise ValueError('ArcticSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return float('-inf')
        return a

    @staticmethod
    def power(a: float, n: int) -> float:
        return a * n

    @staticmethod
    def star(a: float) -> float:
        if a > 0.0:
            return float('inf')
        return 0.0


class ViterbiSemiring:
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

    @staticmethod
    def add(a: float, b: float) -> float:
        return max(a, b)

    @staticmethod
    def mul(a: float, b: float) -> float:
        return a * b

    @staticmethod
    def nsum(a: float, n: int) -> float:
        if n < 0:
            raise ValueError('ViterbiSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return 0.0
        return a

    @staticmethod
    def power(a: float, n: int) -> float:
        return a**n

    @staticmethod
    def star(a: float) -> float:
        return 1.0


class ReliabilitySemiring(ViterbiSemiring):
    """
    Alias for ViterbiSemiring.
    Used for: Reliability analysis (max probability path).
    """


class BottleneckSemiring:
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

    @staticmethod
    def add(a: float, b: float) -> float:
        return max(a, b)

    @staticmethod
    def mul(a: float, b: float) -> float:
        return min(a, b)

    @staticmethod
    def nsum(a: float, n: int) -> float:
        if n < 0:
            raise ValueError('BottleneckSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return float('-inf')
        return a

    @staticmethod
    def power(a: float, n: int) -> float:
        if n == 0:
            return float('inf')
        return a

    @staticmethod
    def star(a: float) -> float:
        return float('inf')


class MinTimesSemiring:
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

    @staticmethod
    def add(a: float, b: float) -> float:
        return min(a, b)

    @staticmethod
    def mul(a: float, b: float) -> float:
        return a * b

    @staticmethod
    def nsum(a: float, n: int) -> float:
        if n < 0:
            raise ValueError('MinTimesSemiring does not support negative nsum')
        # Idempotent: min(a, a) = a
        if n == 0:
            return float('inf')
        return a

    @staticmethod
    def power(a: float, n: int) -> float:
        return a**n

    @staticmethod
    def star(a: float) -> float:
        if a < 1.0:
            return 0.0
        return 1.0


# endregion


# region Logic


class BooleanSemiring:
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

    @staticmethod
    def add(a: bool, b: bool) -> bool:
        return a or b

    @staticmethod
    def mul(a: bool, b: bool) -> bool:
        return a and b

    @staticmethod
    def nsum(a: bool, n: int) -> bool:
        if n < 0:
            raise ValueError('BooleanSemiring does not support negative nsum')
        # Idempotent: a or a = a
        if n == 0:
            return False
        return a

    @staticmethod
    def power(a: bool, n: int) -> bool:
        if n == 0:
            return True
        return a

    @staticmethod
    def star(a: bool) -> bool:
        return True


class LukasiewiczSemiring:
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

    @staticmethod
    def add(a: float, b: float) -> float:
        return max(a, b)

    @staticmethod
    def mul(a: float, b: float) -> float:
        return max(0.0, a + b - 1.0)

    @staticmethod
    def nsum(a: float, n: int) -> float:
        if n < 0:
            raise ValueError('LukasiewiczSemiring does not support negative nsum')
        # Idempotent: max(a, a) = a
        if n == 0:
            return 0.0
        return a

    @staticmethod
    def power(a: float, n: int) -> float:
        if n == 0:
            return 1.0
        return max(0.0, n * a - (n - 1))

    @staticmethod
    def star(a: float) -> float:
        return 1.0


# endregion


# region Probability & Statistics


class LogSemiring:
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

    @staticmethod
    def add(a: float, b: float) -> float:
        # log(exp(a) + exp(b))
        if a == float('-inf'):
            return b
        if b == float('-inf'):
            return a

        # Numerical stability: log(exp(a) + exp(b)) = max + log(exp(a-max) + exp(b-max))
        max_val = max(a, b)
        return max_val + math.log(math.exp(a - max_val) + math.exp(b - max_val))

    @staticmethod
    def mul(a: float, b: float) -> float:
        # log(exp(a) * exp(b)) = a + b
        return a + b

    @staticmethod
    def nsum(a: float, n: int) -> float:
        if n < 0:
            raise ValueError('LogSemiring does not support negative nsum')
        # log(n * exp(a)) = log(n) + a
        if n == 0:
            return float('-inf')
        if a == float('-inf'):
            return float('-inf')
        return a + math.log(n)

    @staticmethod
    def power(a: float, n: int) -> float:
        return a * n

    @staticmethod
    def star(a: float) -> float:
        if a >= 0.0:
            return float('inf')
        return -math.log1p(-math.exp(a))


class ExpectationSemiring:
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

    @staticmethod
    def add(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        return a[0] + b[0], a[1] + b[1]

    @staticmethod
    def mul(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        # Product rule: E[XY] = E[X]Y + X E[Y] (sort of)
        # Actually: (p1*p2, p1*v2 + p2*v1)
        return a[0] * b[0], a[0] * b[1] + b[0] * a[1]

    @staticmethod
    def nsum(a: tuple[float, float], n: int) -> tuple[float, float]:
        # Expectation semiring is a Ring (component-wise addition)
        # So negative n is allowed.
        if n == 0:
            return 0.0, 0.0
        return a[0] * n, a[1] * n

    @staticmethod
    def power(a: tuple[float, float], n: int) -> tuple[float, float]:
        p, v = a
        if n == 0:
            return 1.0, 0.0
        return p**n, n * (p ** (n - 1)) * v

    @staticmethod
    def star(a: tuple[float, float]) -> tuple[float, float]:
        p, v = a
        if p >= 1.0:
            return float('inf'), float('inf')
        p_star = 1.0 / (1.0 - p)
        v_star = v * (p_star**2)
        return p_star, v_star


class VarianceSemiring:
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

    @staticmethod
    def add(
        a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        return a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3]

    @staticmethod
    def mul(
        a: tuple[float, float, float, float], b: tuple[float, float, float, float]
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

    @staticmethod
    def nsum(a: tuple[float, float, float, float], n: int) -> tuple[float, float, float, float]:
        if n == 0:
            return 0.0, 0.0, 0.0, 0.0
        return a[0] * n, a[1] * n, a[2] * n, a[3] * n

    @staticmethod
    def power(a: tuple[float, float, float, float], n: int) -> tuple[float, float, float, float]:
        if n == 0:
            return 1.0, 0.0, 0.0, 0.0
        res = (1.0, 0.0, 0.0, 0.0)
        base = a
        while n > 0:
            if n % 2 == 1:
                res = VarianceSemiring.mul(res, base)
            base = VarianceSemiring.mul(base, base)
            n //= 2
        return res

    @staticmethod
    def star(a: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        raise NotImplementedError('Kleene star not implemented for VarianceSemiring')


class DualNumberSemiring(ExpectationSemiring):
    """
    Alias for ExpectationSemiring.
    Used for: Automatic Differentiation (Forward Mode).
    Values are (value, derivative).
    """


# endregion


# region Structures


class StringSemiring:
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

    @staticmethod
    def add(a: set[str], b: set[str]) -> set[str]:
        return a | b

    @staticmethod
    def mul(a: set[str], b: set[str]) -> set[str]:
        # Concatenation of sets: {xy | x in a, y in b}
        if not a or not b:
            return set()
        return {x + y for x in a for y in b}

    @staticmethod
    def nsum(a: set[str], n: int) -> set[str]:
        if n < 0:
            raise ValueError('StringSemiring does not support negative nsum')
        # Idempotent: a | a = a
        if n == 0:
            return set()
        return a

    @staticmethod
    def power(a: set[str], n: int) -> set[str]:
        if n == 0:
            return {''}
        if n == 1:
            return a
        res = {''}
        base = a
        while n > 0:
            if n % 2 == 1:
                res = StringSemiring.mul(res, base)
            base = StringSemiring.mul(base, base)
            n //= 2
        return res

    @staticmethod
    def star(a: set[str]) -> set[str]:
        raise NotImplementedError('Kleene star not supported for StringSemiring')


class ProvenanceSemiring:
    """
    The Polynomial Provenance Semiring N[X].
    Values are dictionaries mapping monomials (tuples of variables) to coefficients (counts).
    Example: {('x', 'y'): 2, ('z',): 1} represents 2xy + z.

    Used for: Tracking which facts contributed to a result and how many times.
    """

    @property
    def zero(self) -> dict[tuple[str, ...], int]:
        return {}

    @property
    def one(self) -> dict[tuple[str, ...], int]:
        return {(): 1}

    @staticmethod
    def add(a: dict[tuple[str, ...], int], b: dict[tuple[str, ...], int]) -> dict[tuple[str, ...], int]:
        # Polynomial addition: sum coefficients of like terms
        result = a.copy()
        for term, coeff in b.items():
            result[term] = result.get(term, 0) + coeff
        return result

    @staticmethod
    def mul(a: dict[tuple[str, ...], int], b: dict[tuple[str, ...], int]) -> dict[tuple[str, ...], int]:
        # Polynomial multiplication: convolution of terms
        result = {}
        for term1, coeff1 in a.items():
            for term2, coeff2 in b.items():
                # Multiply terms: concatenate tuples (sorted for canonical form)
                new_term = tuple(sorted(term1 + term2))
                new_coeff = coeff1 * coeff2
                result[new_term] = result.get(new_term, 0) + new_coeff
        return result

    @staticmethod
    def nsum(a: dict[tuple[str, ...], int], n: int) -> dict[tuple[str, ...], int]:
        if n < 0:
            raise ValueError('ProvenanceSemiring does not support negative nsum')
        if n == 0:
            return {}
        return {term: coeff * n for term, coeff in a.items()}

    @staticmethod
    def power(a: dict[tuple[str, ...], int], n: int) -> dict[tuple[str, ...], int]:
        if n == 0:
            return {(): 1}
        res = {(): 1}
        base = a
        while n > 0:
            if n % 2 == 1:
                res = ProvenanceSemiring.mul(res, base)
            base = ProvenanceSemiring.mul(base, base)
            n //= 2
        return res

    @staticmethod
    def star(a: dict[tuple[str, ...], int]) -> dict[tuple[str, ...], int]:
        raise NotImplementedError('Kleene star not implemented for ProvenanceSemiring')


class KCollapsedSemiring:
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
        return min(self.k, a**n)

    def star(self, a: int) -> int:
        # 1 + a + a^2 + ...
        # If a >= 1, sum diverges to infinity, so clamped to k.
        # If a = 0, sum is 1.
        if a == 0:
            return 1
        return self.k


class DigitalSemiring:
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


# endregion
