r"""
Semiring, StarSemiring, and KleeneAlgebra protocols for two-operation algebraic structures.

Algebraic Signatures (EP-0150, EP-0197):
    Semiring:      $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$
    StarSemiring:  $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$
    KleeneAlgebra: $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$ with $a \oplus a = a$
"""

from functools import cache
from typing import Any, Literal, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._helpers import nsum as _nsum
from algebrax.algebra._helpers import power as _power
from algebrax.algebra._mixins import HasAdd, HasMul, HasOne, HasPlus, HasStar, HasZero, LawIdempotent

V = TypeVar('V')


@runtime_checkable
class Semiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], Protocol):
    r"""A mathematical Semiring (Rig / Hemiring) $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$.

    Combines an additive commutative monoid $\langle V, \mathbf{0}, + \rangle$
    and a multiplicative monoid $\langle V, \mathbf{1}, \cdot \rangle$ satisfying:
    - Distributivity: $a \cdot (b + c) = (a \cdot b) + (a \cdot c)$
                      $(a + b) \cdot c = (a \cdot c) + (b \cdot c)$
    - Annihilation:   $\mathbf{0} \cdot a = a \cdot \mathbf{0} = \mathbf{0}$

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative multiplication (`HasMul[V]`).
    """

    def nsum(self, a: V, n: int) -> V:
        r"""The $n$-fold sum of a value ($a \oplus a \oplus \cdots \oplus a$).

        Equivalent to scalar multiplication in a module.
        $n$ must be non-negative for semirings that are not rings.
        """
        return _nsum(self, a, n)

    def power(self, a: V, n: int) -> V:
        r"""The $n$-th power of a value ($a \otimes a \otimes \cdots \otimes a$).

        $n$ must be non-negative.
        """
        return _power(self, a, n)

    def _repr_latex_(self) -> str:
        """Return LaTeX representation for rich display in Jupyter Notebooks."""
        from algebrax.display import extract_algebraic_signature

        sig = extract_algebraic_signature(self)
        return f'$${sig}$$' if sig else ''

    def _repr_html_(self) -> str:
        """Return HTML representation for rich display in Jupyter Notebooks."""
        from algebrax.display import semiring_card

        return semiring_card(self)

    @staticmethod
    @cache
    def registry() -> dict[str, Any]:
        """Return a registry of all built-in semirings with parsed AMDS metadata."""
        from algebrax.display import get_algebraic_metadata

        cat = Semiring.catalog()
        return {name: get_algebraic_metadata(cls) for name, cls in cat.items()}

    @staticmethod
    @cache
    def catalog() -> dict[str, type['Semiring']]:
        """Return a discoverable registry of all built-in semiring types.

        Returns:
            A dictionary mapping human-readable semiring names to their class types.
        """
        from algebrax.algebra._dual import DualNumberAlgebra
        from algebrax.algebra._polynomial import PolynomialAlgebra
        from algebrax.clifford import (
            CliffordAlgebra,
            GeneralizedCliffordAlgebra,
            QuantumCliffordAlgebra,
        )
        from algebrax.semiring.algebraic import (
            BinomialConvolutionSemiring,
            GaloisFieldSemiring,
            KnotSemiring,
            MonoidAlgebraSemiring,
            MultivariateBinomialConvolutionSemiring,
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
            BivariateVarianceSemiring,
            ExpectationSemiring,
            KurtosisSemiring,
            LogSemiring,
            MultivariateMomentSemiring,
            SkewnessSemiring,
            StatisticalMomentSemiring,
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
            'BivariateVariance': BivariateVarianceSemiring,
            'Skewness': SkewnessSemiring,
            'Kurtosis': KurtosisSemiring,
            'StatisticalMoment': StatisticalMomentSemiring,
            'BinomialConvolution': BinomialConvolutionSemiring,
            'MultivariateBinomialConvolution': MultivariateBinomialConvolutionSemiring,
            'MultivariateMoment': MultivariateMomentSemiring,
            'DualNumber': DualNumberAlgebra,
            'String': StringSemiring,
            'KCollapsed': KCollapsedSemiring,
            'Digital': DigitalSemiring,
            'MonoidAlgebra': MonoidAlgebraSemiring,
            'Knot': KnotSemiring,
            'Polynomial': PolynomialAlgebra,
            'Provenance': ProvenanceSemiring,
            'QuotientMonoidAlgebra': QuotientMonoidAlgebraSemiring,
            'Clifford': CliffordAlgebra,
            'GaloisField': GaloisFieldSemiring,
            'GeneralizedClifford': GeneralizedCliffordAlgebra,
            'QuantumClifford': QuantumCliffordAlgebra,
        }

    @classmethod
    def default(cls) -> 'Semiring[Any]':
        """Return the canonical default semiring instance (StandardSemiring)."""
        from algebrax.semiring.arithmetic import StandardSemiring

        return StandardSemiring()

    @classmethod
    def normalize(
        cls,
        s: 'Semiring[V] | type[Semiring[V]] | str | None' = None,
    ) -> 'Semiring[V]':
        """Normalize a semiring argument to a concrete instance.

        Handles None (returns default), class types (instantiates),
        string catalog keys (e.g. 'Tropical', 'boolean'), or existing instances.
        """
        if s is None:
            return cls.default()  # type: ignore[return-value]

        if isinstance(s, str):
            cat = cls.catalog()
            lookup = {k.lower(): v for k, v in cat.items()}
            key = s.lower().removesuffix('semiring')
            if key not in lookup:
                raise KeyError(f"Unknown semiring '{s}'. Available: {list(cat.keys())}")
            return lookup[key]()  # type: ignore[return-value]

        return s() if isinstance(s, type) else s

    create = normalize

    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        if cls is Semiring:
            attrs = {'zero', 'one', 'add', 'mul'}
            return all(
                any(attr in B.__dict__ or attr in getattr(B, '__annotations__', {}) for B in subclass.__mro__)
                for attr in attrs
            )
        return NotImplemented


# Explicitly restrict structural protocol attrs to pure algebraic operations,
# excluding utility classmethods/staticmethods (normalize, catalog, default, etc.)
Semiring.__protocol_attrs__ = frozenset({'zero', 'one', 'add', 'mul'})


@runtime_checkable
class StarSemiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], HasPlus[V], Protocol):
    r"""A Star Semiring (Closed / Conway Semiring) $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$.

    Equipped with a unary Kleene star closure operation $*: V \to V$ satisfying:
        $a^* = \mathbf{1} + a \cdot a^* = \mathbf{1} + a^* \cdot a$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative multiplication (`HasMul[V]`).
        - `star(a)`: Kleene closure $\mathbf{1} + a + a^2 + \cdots$ (`HasStar[V]`).
        - `plus(a)`: Strict positive iteration $a \cdot a^* = a^* \cdot a$ (`HasPlus[V]`).
    """

    def plus(self, a: V) -> V:
        r"""Strict positive iteration: $a^+ = a \cdot a^*$.

        In any unital star semiring, $a^+ = a \cdot a^* = a^* \cdot a$.
        """
        return self.mul(a, self.star(a))


# Canonical mathematical synonyms:
ClosedSemiring = StarSemiring
ConwaySemiring = StarSemiring


@runtime_checkable
class KleeneAlgebra(
    HasZero[V],
    HasAdd[V],
    HasOne[V],
    HasMul[V],
    HasStar[V],
    HasPlus[V],
    LawIdempotent,
    Protocol,
):
    r"""A Kleene Algebra $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$ with $a \oplus a = a$.

    An idempotent star semiring ($a \oplus a = a$) satisfying Kozen's induction axioms:
        $\mathbf{1} + a \cdot a^* \le a^*, \quad b + a \cdot x \le x \implies a^* \cdot b \le x$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$ with $a \oplus a = a$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Idempotent, commutative, associative addition (`HasAdd[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative multiplication (`HasMul[V]`).
        - `star(a)`: Kleene closure $\mathbf{1} + a + a^2 + \cdots$ (`HasStar[V]`).
        - `plus(a)`: Strict positive iteration $a \cdot a^*$ (`HasPlus[V]`).
    """

    def plus(self, a: V) -> V:
        r"""Strict positive iteration: $a^+ = a \cdot a^*$.

        In any unital star semiring, $a^+ = a \cdot a^* = a^* \cdot a$.
        """
        return self.mul(a, self.star(a))

    @property
    def is_idempotent(self) -> Literal[True]:
        return True


__all__ = [
    'ClosedSemiring',
    'ConwaySemiring',
    'KleeneAlgebra',
    'Semiring',
    'StarSemiring',
]
