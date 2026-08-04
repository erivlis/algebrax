from functools import cache
from typing import Protocol, TypeVar

V = TypeVar('V')


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

    @staticmethod
    @cache
    def catalog() -> dict[str, type['Semiring']]:
        """
        Return a discoverable registry of all built-in semiring types.

        Returns:
            A dictionary mapping human-readable semiring names to their class types.
        """
        from algebrax.semiring.algebraic import (
            CliffordSemiring,
            GaloisFieldSemiring,
            KnotSemiring,
            MonoidAlgebraSemiring,
            PolynomialSemiring,
            ProvenanceSemiring,
            QuotientMonoidAlgebraSemiring,
        )
        from algebrax.semiring.arithmetic import ModularSemiring, StandardSemiring
        from algebrax.semiring.logic import BooleanSemiring, DigitalSemiring, LukasiewiczSemiring
        from algebrax.semiring.optimization import (
            ArcticSemiring,
            BottleneckSemiring,
            MinTimesSemiring,
            ReliabilitySemiring,
            TropicalSemiring,
            ViterbiSemiring,
        )
        from algebrax.semiring.statistical import (
            DualNumberSemiring,
            ExpectationSemiring,
            LogSemiring,
            VarianceSemiring,
        )
        from algebrax.semiring.structures import KCollapsedSemiring, StringSemiring

        return {
            'Standard': StandardSemiring,
            'Modular': ModularSemiring,
            'Tropical': TropicalSemiring,
            'Arctic': ArcticSemiring,
            'Viterbi': ViterbiSemiring,
            'Reliability': ReliabilitySemiring,
            'Bottleneck': BottleneckSemiring,
            'MinTimes': MinTimesSemiring,
            'Boolean': BooleanSemiring,
            'Lukasiewicz': LukasiewiczSemiring,
            'Log': LogSemiring,
            'Expectation': ExpectationSemiring,
            'Variance': VarianceSemiring,
            'DualNumber': DualNumberSemiring,
            'String': StringSemiring,
            'KCollapsed': KCollapsedSemiring,
            'Digital': DigitalSemiring,
            'MonoidAlgebra': MonoidAlgebraSemiring,
            'Knot': KnotSemiring,
            'Polynomial': PolynomialSemiring,
            'Provenance': ProvenanceSemiring,
            'QuotientMonoidAlgebra': QuotientMonoidAlgebraSemiring,
            'Clifford': CliffordSemiring,
            'GaloisField': GaloisFieldSemiring,
        }


def _normalize_semiring(s: Semiring[V] | type[Semiring[V]] | None) -> Semiring[V]:
    """Normalize semiring argument to an instance, handling class factories and None."""
    if s is None:
        from algebrax.semiring.arithmetic import StandardSemiring

        return StandardSemiring()
    return s() if isinstance(s, type) else s
