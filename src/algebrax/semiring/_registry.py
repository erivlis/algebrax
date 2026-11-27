"""Built-in semiring catalog registry and domain taxonomy metadata.

Centralizes Layer-3 semiring discovery and domain tags so Layer-2 protocols
in `algebrax.algebra` remain decoupled from concrete semiring modules.
"""

from __future__ import annotations

from functools import cache
from typing import Any

from algebrax.algebra._dual import DualNumberAlgebra
from algebrax.algebra._field import GaloisField
from algebrax.algebra._polynomial import PolynomialAlgebra
from algebrax.algebra._semiring import Semiring
from algebrax.clifford import (
    CliffordAlgebra,
    GeneralizedCliffordAlgebra,
    QuantumCliffordAlgebra,
)
from algebrax.semiring.algebraic import (
    BinomialConvolutionSemiring,
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

DOMAIN_TAGS: dict[str, str] = {
    'Standard': 'arithmetic',
    'Modular': 'arithmetic',
    'Tropical': 'optimization',
    'Arctic': 'optimization',
    'Viterbi': 'optimization',
    'Reliability': 'optimization',
    'Bottleneck': 'optimization',
    'MinTimes': 'optimization',
    'Boolean': 'logic',
    'Lukasiewicz': 'logic',
    'Digital': 'logic',
    'Log': 'statistical',
    'Expectation': 'statistical',
    'Variance': 'statistical',
    'BivariateVariance': 'statistical',
    'Skewness': 'statistical',
    'Kurtosis': 'statistical',
    'StatisticalMoment': 'statistical',
    'MultivariateMoment': 'statistical',
    'String': 'structures',
    'KCollapsed': 'structures',
    'BinomialConvolution': 'algebraic',
    'MultivariateBinomialConvolution': 'algebraic',
    'DualNumber': 'algebraic',
    'MonoidAlgebra': 'algebraic',
    'Knot': 'algebraic',
    'Polynomial': 'algebraic',
    'Provenance': 'algebraic',
    'QuotientMonoidAlgebra': 'algebraic',
    'GaloisField': 'algebraic',
    'Clifford': 'clifford',
    'GeneralizedClifford': 'clifford',
    'QuantumClifford': 'clifford',
}


@cache
def semiring_catalog() -> dict[str, type[Semiring[Any]]]:
    """Return a discoverable registry of all built-in semiring types."""
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
        'GaloisField': GaloisField,
        'GeneralizedClifford': GeneralizedCliffordAlgebra,
        'QuantumClifford': QuantumCliffordAlgebra,
    }


__all__ = [
    'DOMAIN_TAGS',
    'semiring_catalog',
]
