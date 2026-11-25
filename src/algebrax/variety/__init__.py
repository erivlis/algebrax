r"""
Affine algebraic varieties, coordinate rings, Stickelberger solvers, morphisms, and K-theory bridges.

Provides the geometric dual to `MultivariatePolynomialAlgebra` and `GroebnerIdeal`:
- Atomic geometric mixins & flat protocols (`HasPointLocus`, `HasDimension`, `HasCoordinateRing`,
  `HasTangentLocus`, `GeometricVariety`, `SmoothableVariety`)
- Affine varieties & coordinate rings (`AffineVariety`)
- Stickelberger companion matrix & exact rational root solvers (`companion_matrix`,
  `solve_zero_dimensional`, `solve_exact_rational`)
- Finite-field varieties & Boolean $\mathbb{F}_2$ SAT (`enum_variety_points`, `boolean_variety`,
  `solve_f2_sat`)
- Contravariant polynomial morphisms, GIT syzygies, Grassmannians & matrix-group Hopf algebras
  (`PolynomialMap`, `syzygy_variety`, `plucker_grassmannian_variety`, `CoordinateHopfAlgebra`)
- Algebraic & higher K-theory bridges ($K_0, K_1, K_2^M$): `is_serre_swan_projective_bundle`,
  `schubert_chern_cohomology_ring`, `motivic_point_count_homomorphism`,
  `coordinate_ring_unit_inverse`, `tame_symbol_padic`, `milnor_symbol_conic_variety`
"""

from algebrax.variety._mixins import (
    GeometricVariety,
    HasCoordinateRing,
    HasDimension,
    HasPointLocus,
    HasTangentLocus,
    SmoothableVariety,
)
from algebrax.variety.affine import AffineVariety
from algebrax.variety.finite import (
    boolean_variety,
    enum_variety_points,
    solve_f2_sat,
)
from algebrax.variety.k_theory import (
    coordinate_ring_unit_inverse,
    is_serre_swan_projective_bundle,
    milnor_symbol_conic_variety,
    motivic_point_count_homomorphism,
    schubert_chern_cohomology_ring,
    tame_symbol_padic,
)
from algebrax.variety.morphism import (
    CoordinateHopfAlgebra,
    PolynomialMap,
    plucker_grassmannian_variety,
    syzygy_variety,
)
from algebrax.variety.stickelberger import (
    companion_matrix,
    solve_exact_rational,
    solve_zero_dimensional,
)

__all__ = [
    'AffineVariety',
    'CoordinateHopfAlgebra',
    'GeometricVariety',
    'HasCoordinateRing',
    'HasDimension',
    'HasPointLocus',
    'HasTangentLocus',
    'PolynomialMap',
    'SmoothableVariety',
    'boolean_variety',
    'companion_matrix',
    'coordinate_ring_unit_inverse',
    'enum_variety_points',
    'is_serre_swan_projective_bundle',
    'milnor_symbol_conic_variety',
    'motivic_point_count_homomorphism',
    'plucker_grassmannian_variety',
    'schubert_chern_cohomology_ring',
    'solve_exact_rational',
    'solve_f2_sat',
    'solve_zero_dimensional',
    'syzygy_variety',
    'tame_symbol_padic',
]
