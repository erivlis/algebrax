"""
Semiring namespace — all classes available from algebrax.semiring.
"""

from algebrax.algebra._dual import DualNumberAlgebra, DualNumberRing, DualNumberSemiring
from algebrax.algebra._polynomial import PolynomialAlgebra, PolynomialRing, PolynomialSemiring
from algebrax.algebra._semiring import Semiring
from algebrax.clifford import (
    CliffordAlgebra,
    CliffordSemiring,
    GeneralizedCliffordAlgebra,
    GeneralizedCliffordSemiring,
    QuantumCliffordAlgebra,
    QuantumCliffordSemiring,
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
    BivariateCovarianceSemiring,
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

__all__ = [
    'ArcticSemiring',
    'BinomialConvolutionSemiring',
    'BivariateCovarianceSemiring',
    'BivariateVarianceSemiring',
    'BooleanSemiring',
    'BottleneckSemiring',
    'CliffordAlgebra',
    'CliffordSemiring',
    'DigitalSemiring',
    'DualNumberAlgebra',
    'DualNumberRing',
    'DualNumberSemiring',
    'ExpectationSemiring',
    'GaloisFieldSemiring',
    'GeneralizedCliffordSemiring',
    'KCollapsedSemiring',
    'KnotSemiring',
    'KurtosisSemiring',
    'LogSemiring',
    'LukasiewiczSemiring',
    'MinTimesSemiring',
    'ModularSemiring',
    'MonoidAlgebraSemiring',
    'MultivariateBinomialConvolutionSemiring',
    'MultivariateMomentSemiring',
    'PolynomialAlgebra',
    'PolynomialRing',
    'PolynomialSemiring',
    'ProvenanceSemiring',
    'QuantumCliffordSemiring',
    'QuotientMonoidAlgebraSemiring',
    'ReliabilitySemiring',
    'Semiring',
    'SkewnessSemiring',
    'StandardSemiring',
    'StatisticalMomentSemiring',
    'StringSemiring',
    'TropicalSemiring',
    'VarianceSemiring',
    'ViterbiSemiring',
]
