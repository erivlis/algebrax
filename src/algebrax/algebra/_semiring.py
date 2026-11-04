r"""
Semiring protocol for two-operation algebraic structures.

Algebraic Signature (EP-0150 AMDS):
    Semiring: $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$
"""

from functools import cache
from typing import Any, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._helpers import nsum as _nsum
from algebrax.algebra._helpers import power as _power
from algebrax.algebra._mixins import HasAdd, HasMul, HasOne, HasStar, HasZero

V = TypeVar('V')


@runtime_checkable
class Semiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], Protocol):
    r"""A mathematical Semiring $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$.

    Combines an additive commutative monoid $\langle V, \mathbf{0}, + \rangle$
    and a multiplicative monoid $\langle V, \mathbf{1}, \cdot \rangle$ equipped with Kleene closure $a^*$, satisfying:
    - Distributivity: $a \cdot (b + c) = (a \cdot b) + (a \cdot c)$
                      $(a + b) \cdot c = (a \cdot c) + (b \cdot c)$
    - Annihilation:   $\mathbf{0} \cdot a = a \cdot \mathbf{0} = \mathbf{0}$

    Algebraic Signature:
        $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative multiplication (`HasMul[V]`).
        - `star(a)`: Kleene closure $\mathbf{1} + a + a^2 + \cdots$ (`HasStar[V]`).
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
