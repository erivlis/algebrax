"""
Logic and fuzzy set semirings.
"""

from algebrax.semiring._base import Semiring


class BooleanSemiring(Semiring[bool]):
    r"""The Boolean algebra semiring for reachability and connectivity.

    Algebraic Signature:
        $\langle \{0, 1\}, \lor, \land, 0, 1 \rangle$

    Carrier:
        `bool` (`True` or `False`).

    Operations:
        - Addition ($\oplus$): Logical Disjunction $a \lor b$
        - Multiplication ($\otimes$): Logical Conjunction $a \land b$
        - Zero Element ($\mathbb{0}$): `False`
        - One Element ($\mathbb{1}$): `True`

    Properties:
        Fully Idempotent, Distributive Lattice, Boolean Algebra, Dioid.

    Applications:
        Graph reachability, transitive closure (Warshall's algorithm), cycle detection,
        unweighted path connectivity.
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
    r"""The Łukasiewicz multi-valued logic semiring (t-norm algebra).

    Algebraic Signature:
        $\langle [0, 1], \max, \otimes_{\mathrm{Luk}}, 0, 1 \rangle$

    Carrier:
        `float` in unit interval $[0, 1]$.

    Operations:
        - Addition ($\oplus$): $\max(a, b)$
        - Multiplication ($\otimes$): Łukasiewicz t-norm $a \otimes_{\mathrm{Luk}} b = \max(0.0, a + b - 1.0)$.
        - Zero Element ($\mathbb{0}$): $0.0$
        - One Element ($\mathbb{1}$): $1.0$

    Properties:
        MV-Algebra, Commutative, Idempotent addition, Nilpotent t-norm.

    Applications:
        Fuzzy reasoning, continuous logic, soft constraint satisfaction, degree-of-truth networks.
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
    r"""The Digital Semiring based on digit-sum dominance.

    Algebraic Signature:
        $\langle \mathbb{N}_0 \cup \{\infty\}, \oplus_{\mathrm{dig}}, \otimes_{\mathrm{dig}}, 0, \infty \rangle$

    Carrier:
        `float | int` (non-negative integers extended with `float('inf')`).

    Operations:
        - Addition ($\oplus$): Dominant digit sum, ties broken by $\max(a, b)$
        - Multiplication ($\otimes$): Recessive digit sum, ties broken by $\min(a, b)$
        - Zero Element ($\mathbb{0}$): $0$
        - One Element ($\mathbb{1}$): $\infty$

    Properties:
        Idempotent addition and multiplication, Dioid, Selective.

    Applications:
        Digit-sum complexity analysis, non-standard digital signal networks, arithmetic encoding,
        post-quantum cryptography (Huang et al., 2024).
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
