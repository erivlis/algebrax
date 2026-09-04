"""
Optimization and path problems semirings.
"""

from algebrax.semiring._base import Semiring


class TropicalSemiring(Semiring[float]):
    r"""The Min-Plus semiring for shortest path problems.

    Algebraic Signature:
        $\langle \mathbb{R} \cup \{+\infty\}, \min, +, +\infty, 0 \rangle$

    Carrier:
        `float` (real numbers with `float('inf')` as additive identity).

    Operations:
        - Addition ($\oplus$): $\min(a, b)$
        - Multiplication ($\otimes$): $a + b$
        - Zero Element ($\mathbb{0}$): $+\infty$
        - One Element ($\mathbb{1}$): $0.0$

    Properties:
        Idempotent, Commutative, Dioid, Path Semiring.

    Applications:
        Shortest path routing (Dijkstra, Bellman-Ford, Floyd-Warshall),
        tropical geometry, dynamic programming.
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
    r"""The Max-Plus semiring for longest path and scheduling problems.

    Algebraic Signature:
        $\langle \mathbb{R} \cup \{-\infty\}, \max, +, -\infty, 0 \rangle$

    Carrier:
        `float` (real numbers with `float('-inf')` as additive identity).

    Operations:
        - Addition ($\oplus$): $\max(a, b)$
        - Multiplication ($\otimes$): $a + b$
        - Zero Element ($\mathbb{0}$): $-\infty$
        - One Element ($\mathbb{1}$): $0.0$

    Properties:
        Idempotent, Commutative, Dioid.

    Applications:
        Longest path routing, critical path method (CPM), Viterbi decoding in log domain.
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
    r"""The Max-Product semiring for probabilistic path decoding.

    Algebraic Signature:
        $\langle [0, 1], \max, \times, 0, 1 \rangle$

    Carrier:
        `float` in unit interval $[0, 1]$.

    Operations:
        - Addition ($\oplus$): $\max(a, b)$
        - Multiplication ($\otimes$): $a \times b$
        - Zero Element ($\mathbb{0}$): $0.0$
        - One Element ($\mathbb{1}$): $1.0$

    Properties:
        Idempotent addition, Commutative, Selective.

    Applications:
        Most likely state path decoding in Hidden Markov Models (Viterbi algorithm),
        probabilistic parsing, maximum a posteriori (MAP) estimation.
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
        return a**n

    def star(self, a: float) -> float:
        return 1.0


class ReliabilitySemiring(ViterbiSemiring):
    r"""The Reliability semiring for maximum-probability path analysis.

    Algebraic Signature:
        $\langle [0, 1], \max, \times, 0, 1 \rangle$

    Carrier:
        `float` in unit interval $[0, 1]$ representing component survival probabilities.

    Operations:
        - Addition ($\oplus$): $\max(a, b)$
        - Multiplication ($\otimes$): $a \times b$
        - Zero Element ($\mathbb{0}$): $0.0$
        - One Element ($\mathbb{1}$): $1.0$

    Properties:
        Idempotent addition, Commutative, Isomorphic to ViterbiSemiring.

    Applications:
        Network link reliability, redundant system survival probability, fault tolerance.
    """


class BottleneckSemiring(Semiring[float]):
    r"""The Max-Min (capacity / widest-path) semiring.

    Algebraic Signature:
        $\langle \mathbb{R} \cup \{\pm\infty\}, \max, \min, -\infty, +\infty \rangle$

    Carrier:
        `float` (real numbers extended with $\pm\infty$ as bounds).

    Operations:
        - Addition ($\oplus$): $\max(a, b)$
        - Multiplication ($\otimes$): $\min(a, b)$
        - Zero Element ($\mathbb{0}$): $-\infty$
        - One Element ($\mathbb{1}$): $+\infty$

    Properties:
        Fully Idempotent (Distributive Lattice), Dioid, Commutative.

    Applications:
        Maximum capacity path (widest path problem), network bandwidth allocation,
        minimax routing.
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
    r"""The Min-Times semiring for least-probable and multiplicative cost paths.

    Algebraic Signature:
        $\langle \mathbb{R} \cup \{+\infty\}, \min, \times, +\infty, 1 \rangle$

    Carrier:
        `float` (non-negative real numbers with $+\infty$ as additive identity).

    Operations:
        - Addition ($\oplus$): $\min(a, b)$
        - Multiplication ($\otimes$): $a \times b$
        - Zero Element ($\mathbb{0}$): $+\infty$
        - One Element ($\mathbb{1}$): $1.0$

    Properties:
        Idempotent addition, Commutative multiplication.

    Applications:
        Least-probable path search, vulnerability analysis, multiplicative failure risk.
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
        return a**n

    def star(self, a: float) -> float:
        if a < 1.0:
            return 0.0
        return 1.0
