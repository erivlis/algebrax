"""
Bounded structures semirings.
"""

from algebrax.semiring._base import Semiring


class StringSemiring(Semiring[set[str]]):
    r"""The Formal Language semiring over sets of strings.

    Algebraic Signature:
        $\langle \mathcal{P}(\Sigma^*), \cup, \cdot, \emptyset, \{\epsilon\} \rangle$

    Carrier:
        `set[str]` (Subsets of strings over an alphabet $\Sigma^*$).

    Operations:
        - Addition ($\cup$): Set union $A \cup B$.
        - Multiplication ($\cdot$): Language concatenation $\{u v \mid u \in A, v \in B\}$.
        - Zero Element ($\mathbb{0}$): $\emptyset$ (`set()`).
        - One Element ($\mathbb{1}$): $\{\epsilon\}$ (`{""}`).

    Properties:
        Idempotent addition, non-commutative multiplication in general, distributive.

    Applications:
        Formal language theory, regular expression equivalence, path language enumeration in state machines.
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
    r"""The $K$-Collapsed Bounded Counting Semiring.

    Algebraic Signature:
        $\langle \{0, 1, \dots, K\}, \min(K, a+b), \min(K, a \cdot b), 0, 1 \rangle$

    Carrier:
        `int` (Bounded non-negative integers in range $[0, K]$).

    Operations:
        - Addition ($\oplus$): Saturated sum $\min(K, a + b)$.
        - Multiplication ($\otimes$): Saturated product $\min(K, a \cdot b)$.
        - Zero Element ($\mathbb{0}$): $0$.
        - One Element ($\mathbb{1}$): $1$.

    Properties:
        Commutative, associative, saturated arithmetic with absorption at $K$.

    Applications:
        Bounded path counting, cycle threshold detection, finite-capacity resource tracking.
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
