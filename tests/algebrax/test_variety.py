"""Unit, protocol, and falsification tests for algebrax.variety."""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

import algebrax as ax
from algebrax.algebra import (
    Algebra,
    CommRing,
    GaloisField,
    HopfAlgebra,
    ModularField,
    MultivariatePolynomialAlgebra,
    QuotientRing,
    RingHom,
    StandardField,
)
from algebrax.variety import (
    AffineVariety,
    CoordinateHopfAlgebra,
    GeometricVariety,
    HasCoordinateRing,
    HasDimension,
    HasPointLocus,
    HasTangentLocus,
    PolynomialMap,
    SmoothableVariety,
    boolean_variety,
    companion_matrix,
    coordinate_ring_unit_inverse,
    enum_variety_points,
    is_serre_swan_projective_bundle,
    milnor_symbol_conic_variety,
    motivic_point_count_homomorphism,
    plucker_grassmannian_variety,
    schubert_chern_cohomology_ring,
    solve_exact_rational,
    solve_f2_sat,
    solve_zero_dimensional,
    syzygy_variety,
    tame_symbol_padic,
)
from algebrax.variety.stickelberger import _solve_lex_pure_python_numeric
from algebrax.verification import (
    verify_affine_variety_laws,
    verify_coordinate_hopf_laws,
    verify_polynomial_map_laws,
    verify_stickelberger_laws,
)


def _q_ring(n_vars: int, order: str = 'grevlex') -> MultivariatePolynomialAlgebra[Fraction]:
    return MultivariatePolynomialAlgebra(StandardField(Fraction), n_vars=n_vars, order=order)  # type: ignore[arg-type]


# =============================================================================
# 1. Layer 1 / Layer 2 Geometric Protocol Architecture
# =============================================================================


def test_variety_protocol_hierarchy_is_flat() -> None:
    """Layer 2 geometric protocols must compose only Layer 1 mixins (zero L2-to-L2 inheritance)."""
    assert GeometricVariety not in SmoothableVariety.__mro__
    assert SmoothableVariety not in GeometricVariety.__mro__

    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    var = AffineVariety(r2, [r2.sub(r2.add(r2.mul(x, x), r2.mul(y, y)), r2.one)])

    assert isinstance(var, HasPointLocus)
    assert isinstance(var, HasDimension)
    assert isinstance(var, HasCoordinateRing)
    assert isinstance(var, HasTangentLocus)
    assert isinstance(var, GeometricVariety)
    assert isinstance(var, SmoothableVariety)
    assert isinstance(var.coordinate_ring, QuotientRing)
    assert isinstance(var.coordinate_ring, CommRing)


# =============================================================================
# 2. AffineVariety: Dimension, Hilbert Function, Smoothness, Set Operations
# =============================================================================


def test_affine_variety_empty_and_full_space() -> None:
    r2 = _q_ring(2)
    x = r2.gen(0)

    # Empty variety: x = 0 and x = 1 => 1 in I
    empty = AffineVariety(r2, [x, r2.sub(x, r2.one)])
    assert empty.is_empty_over_closure()
    assert not empty.is_zero_dimensional()
    assert empty.krull_dimension() == -1
    assert empty.dimension() == -1
    assert empty.quotient_basis() == []
    assert empty.hilbert_function(0) == 0
    assert empty.hilbert_function(3) == 0
    assert not empty.contains_point((Fraction(0), Fraction(0)))
    assert not empty.is_smooth_at((Fraction(0), Fraction(0)))
    assert all(verify_affine_variety_laws(empty, [(Fraction(0), Fraction(0))]).values())

    # Full affine space A^2: I = (0)
    full = AffineVariety(r2, [])
    assert not full.is_empty_over_closure()
    assert not full.is_zero_dimensional()
    assert full.krull_dimension() == 2
    assert full.quotient_basis() is None
    for d in range(5):
        assert full.hilbert_function(d) == math.comb(d + 2, 2)
    assert full.contains_point((Fraction(3), Fraction(-7)))
    assert full.is_smooth_at((Fraction(3), Fraction(-7)))
    assert all(verify_affine_variety_laws(full, [(Fraction(1), Fraction(2))]).values())


def test_affine_variety_cuspidal_and_nodal_singularities() -> None:
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)

    # Cuspidal cubic y^2 - x^3 = 0: singular at (0, 0), smooth at (1, 1)
    cusp_poly = r2.sub(r2.mul(y, y), r2.mul(r2.mul(x, x), x))
    cusp = AffineVariety(r2, [cusp_poly])
    assert cusp.krull_dimension() == 1
    assert not cusp.is_zero_dimensional()
    assert cusp.contains_point((Fraction(0), Fraction(0)))
    assert not cusp.is_smooth_at((Fraction(0), Fraction(0)))
    assert cusp.contains_point((Fraction(1), Fraction(1)))
    assert cusp.is_smooth_at((Fraction(1), Fraction(1)))
    assert not cusp.is_smooth_at((Fraction(1), Fraction(2)))  # off variety
    assert all(
        verify_affine_variety_laws(
            cusp,
            [(Fraction(0), Fraction(0)), (Fraction(1), Fraction(1)), (Fraction(2), Fraction(3))],
        ).values()
    )

    # Nodal cubic y^2 - x^3 - x^2 = 0: singular at (0, 0), smooth at (3, 6)
    node_poly = r2.sub(r2.sub(r2.mul(y, y), r2.mul(r2.mul(x, x), x)), r2.mul(x, x))
    node = AffineVariety(r2, [node_poly])
    assert node.krull_dimension() == 1
    assert not node.is_smooth_at((Fraction(0), Fraction(0)))
    assert node.is_smooth_at((Fraction(3), Fraction(6)))


def test_affine_variety_hilbert_function_is_order_invariant() -> None:
    """Affine Hilbert function HF_{k[V]}(d) must match under lex and grevlex orders."""
    r_grev = _q_ring(2, order='grevlex')
    r_lex = _q_ring(2, order='lex')

    # Parabola x - y^2 = 0 (classic lex-order trap: LT_lex = x has deg 1, LT_grevlex = y^2 has deg 2)
    p_grev = r_grev.sub(r_grev.gen(0), r_grev.mul(r_grev.gen(1), r_grev.gen(1)))
    p_lex = r_lex.sub(r_lex.gen(0), r_lex.mul(r_lex.gen(1), r_lex.gen(1)))

    v_grev = AffineVariety(r_grev, [p_grev])
    v_lex = AffineVariety(r_lex, [p_lex])

    assert v_grev.krull_dimension() == 1
    assert v_lex.krull_dimension() == 1
    # At d=1, no linear polynomial is in <x - y^2>, so HF(1) == 3 in BOTH orders!
    for d in range(6):
        assert v_grev.hilbert_function(d) == v_lex.hilbert_function(d)
    assert v_lex.hilbert_function(1) == 3
    assert v_lex.hilbert_function(2) == 5


def test_affine_variety_intersect_union_and_eliminate() -> None:
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)

    line_x = AffineVariety(r2, [x])  # V(x): y-axis
    line_y = AffineVariety(r2, [y])  # V(y): x-axis

    origin = line_x.intersect(line_y)
    assert origin.krull_dimension() == 0
    assert origin.contains_point((Fraction(0), Fraction(0)))
    assert not origin.contains_point((Fraction(1), Fraction(0)))

    axes = line_x.union(line_y)
    assert axes.krull_dimension() == 1
    assert axes.ideal.contains(r2.mul(x, y))
    assert axes.contains_point((Fraction(5), Fraction(0)))
    assert axes.contains_point((Fraction(0), Fraction(-3)))
    assert not axes.contains_point((Fraction(1), Fraction(1)))
    assert not axes.is_smooth_at((Fraction(0), Fraction(0)))  # crossing singularity
    assert axes.is_smooth_at((Fraction(2), Fraction(0)))

    # Elimination on twisted cubic V(x^2 - y, x^3 - z): eliminate x => V(y^3 - z^2)
    r3 = _q_ring(3, order='grevlex')
    x3, y3, z3 = r3.gen(0), r3.gen(1), r3.gen(2)
    tc = AffineVariety(
        r3,
        [
            r3.sub(r3.mul(x3, x3), y3),
            r3.sub(r3.mul(r3.mul(x3, x3), x3), z3),
        ],
    )
    assert tc.krull_dimension() == 1
    proj = tc.eliminate(1)  # eliminate x => coordinates (y, z)
    assert proj.ambient_dimension == 2
    assert proj.krull_dimension() == 1
    py, pz = proj.ring.gen(0), proj.ring.gen(1)
    assert proj.ideal.contains(proj.ring.sub(proj.ring.mul(proj.ring.mul(py, py), py), proj.ring.mul(pz, pz)))


def test_radical_zero_dim_seidenberg_char0_and_char_p() -> None:
    # Characteristic 0: double point <(x - 1)^2, (y - 2)^2> -> <x - 1, y - 2>
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    xm1 = r2.sub(x, r2.one)
    ym2 = r2.sub(y, r2.const(Fraction(2)))
    non_rad = AffineVariety(r2, [r2.mul(xm1, xm1), r2.mul(ym2, ym2)])
    assert len(non_rad.quotient_basis() or []) == 4
    assert not non_rad.is_smooth_at((Fraction(1), Fraction(2)))

    rad = non_rad.radical_zero_dim()
    assert len(rad.quotient_basis() or []) == 1
    assert rad.ideal.contains(xm1)
    assert rad.ideal.contains(ym2)
    assert rad.is_smooth_at((Fraction(1), Fraction(2)))

    # Characteristic 3: pure p-th power <(x - 1)^3, (y - 2)^3> over F_3 -> <x - 1, y - 2>
    f3_ring = MultivariatePolynomialAlgebra(ModularField(3), n_vars=2)
    xf, yf = f3_ring.gen(0), f3_ring.gen(1)
    g1 = f3_ring.sub(f3_ring.mul(f3_ring.mul(xf, xf), xf), f3_ring.one)  # x^3 - 1 = (x - 1)^3 mod 3
    g2 = f3_ring.sub(f3_ring.mul(f3_ring.mul(yf, yf), yf), f3_ring.const(2))  # y^3 - 2 = (y - 2)^3 mod 3
    non_rad_f3 = AffineVariety(f3_ring, [g1, g2])
    assert len(non_rad_f3.quotient_basis() or []) == 9
    rad_f3 = non_rad_f3.radical_zero_dim()
    assert len(rad_f3.quotient_basis() or []) == 1
    assert rad_f3.contains_point((1, 2))


# =============================================================================
# 3. Stickelberger Companion Matrix & Exact Rational Solvers
# =============================================================================


def test_stickelberger_conic_intersection_and_exact_rational() -> None:
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    circle = r2.sub(r2.add(r2.mul(x, x), r2.mul(y, y)), r2.const(Fraction(5)))
    hyperb = r2.sub(r2.mul(x, y), r2.const(Fraction(2)))
    var = AffineVariety(r2, [circle, hyperb])

    assert var.is_zero_dimensional()
    assert len(var.quotient_basis() or []) == 4
    assert all(verify_stickelberger_laws(var).values())

    roots_num = solve_zero_dimensional(var)
    expected = [(-2.0, -1.0), (-1.0, -2.0), (1.0, 2.0), (2.0, 1.0)]
    assert len(roots_num) == 4
    for got, exp in zip(roots_num, expected, strict=True):
        assert math.isclose(float(got[0].real), exp[0], abs_tol=1e-7)
        assert math.isclose(float(got[1].real), exp[1], abs_tol=1e-7)

    # Pure-Python exact rational solver (zero NumPy)
    roots_rat = solve_exact_rational(var)
    assert roots_rat == [
        (Fraction(-2), Fraction(-1)),
        (Fraction(-1), Fraction(-2)),
        (Fraction(1), Fraction(2)),
        (Fraction(2), Fraction(1)),
    ]


def test_stickelberger_2r_robot_inverse_kinematics_and_complex_roots() -> None:
    # 2R planar robot arm: L1=2, L2=1, target=(2, 1) -> 2 exact poses
    r4 = _q_ring(4)
    ik_gens = [
        {(2, 0, 0, 0): Fraction(1), (0, 2, 0, 0): Fraction(1), (0, 0, 0, 0): Fraction(-1)},
        {(0, 0, 2, 0): Fraction(1), (0, 0, 0, 2): Fraction(1), (0, 0, 0, 0): Fraction(-1)},
        {(1, 0, 0, 0): Fraction(2), (1, 0, 1, 0): Fraction(1), (0, 1, 0, 1): Fraction(-1), (0, 0, 0, 0): Fraction(-2)},
        {(0, 1, 0, 0): Fraction(2), (0, 1, 1, 0): Fraction(1), (1, 0, 0, 1): Fraction(1), (0, 0, 0, 0): Fraction(-1)},
    ]
    ik_var = AffineVariety(r4, ik_gens)
    assert ik_var.is_zero_dimensional()
    assert len(ik_var.quotient_basis() or []) == 2
    assert all(verify_stickelberger_laws(ik_var).values())

    poses = solve_zero_dimensional(ik_var)
    assert len(poses) == 2
    # Pure-Python fallback (quadratic triangular lex) also extracts both poses cleanly
    poses_pure = _solve_lex_pure_python_numeric(ik_var)
    assert len(poses_pure) == 2
    for p1, p2 in zip(poses, poses_pure, strict=True):
        for c1, c2 in zip(p1, p2, strict=True):
            assert abs(complex(c1) - complex(c2)) < 1e-7

    # Complex conjugate roots: x^2 + 1 = 0, y - 2x = 0 -> (-i, -2i), (i, 2i)
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    cvar = AffineVariety(r2, [r2.add(r2.mul(x, x), r2.one), r2.sub(y, r2.smul(Fraction(2), x))])
    croots = solve_zero_dimensional(cvar)
    assert len(croots) == 2
    assert all(verify_stickelberger_laws(cvar, croots).values())

    # Repeated root system handled cleanly via Seidenberg radicalization
    rep_var = AffineVariety(
        r2,
        [
            r2.mul(r2.sub(x, r2.one), r2.sub(x, r2.one)),
            r2.sub(y, r2.const(Fraction(3))),
        ],
    )
    rep_roots = solve_zero_dimensional(rep_var, use_radical=True)
    assert len(rep_roots) == 1
    assert math.isclose(float(rep_roots[0][0].real), 1.0, abs_tol=1e-7)
    assert math.isclose(float(rep_roots[0][1].real), 3.0, abs_tol=1e-7)


def test_companion_matrix_rejects_positive_dimensional_variety() -> None:
    r2 = _q_ring(2)
    line = AffineVariety(r2, [r2.sub(r2.gen(0), r2.gen(1))])
    with pytest.raises(ValueError, match='zero-dimensional'):
        companion_matrix(line, 0)
    with pytest.raises(ValueError, match='zero-dimensional'):
        solve_zero_dimensional(line)


# =============================================================================
# 4. Finite-Field Varieties, Elliptic Curves & F_2 Algebraic SAT
# =============================================================================


@pytest.mark.parametrize('prime', [5, 7, 11])
def test_finite_field_elliptic_curve_hasse_bound(prime: int) -> None:
    fp_ring = MultivariatePolynomialAlgebra(ModularField(prime), n_vars=2)
    x, y = fp_ring.gen(0), fp_ring.gen(1)
    # y^2 - x^3 - x - 1 = 0 over F_p
    ec_poly = fp_ring.sub(
        fp_ring.mul(y, y),
        fp_ring.add(fp_ring.add(fp_ring.mul(fp_ring.mul(x, x), x), x), fp_ring.one),
    )
    ec_var = AffineVariety(fp_ring, [ec_poly])
    pts = enum_variety_points(ec_var)
    assert all(ec_var.contains_point(pt) for pt in pts)
    # Projective count includes point at infinity
    n_proj = len(pts) + 1
    assert abs(n_proj - (prime + 1)) <= 2.0 * math.sqrt(prime) + 1e-9


def test_finite_field_galois_extension_enumeration() -> None:
    # GF(2^2) modulo x^2 + x + 1
    gf4 = GaloisField(2, (1, 1, 1))
    ring = MultivariatePolynomialAlgebra(gf4, n_vars=2)
    x, y = ring.gen(0), ring.gen(1)
    # Line x + y = 0 over GF(4) has exactly 4 rational points (a, a)
    var = AffineVariety(ring, [ring.add(x, y)])
    pts = enum_variety_points(var)
    assert len(pts) == 4
    assert all(pt[0] == pt[1] for pt in pts)


def test_boolean_variety_and_f2_sat() -> None:
    # Satisfiable 3-SAT: (x1 OR x2) AND (NOT x1 OR x3) AND (NOT x2 OR NOT x3) AND (x1 OR NOT x3)
    sols = solve_f2_sat(3, [[1, 2], [-1, 3], [-2, -3], [1, -3]])
    assert sols == [(0, 1, 0), (1, 0, 1)]

    # Unsatisfiable 2-SAT: (x1) AND (NOT x1)
    assert solve_f2_sat(1, [[1], [-1]]) == []

    # Direct boolean_variety check
    f2_ring = MultivariatePolynomialAlgebra(ModularField(2), n_vars=2)
    x0, x1 = f2_ring.gen(0), f2_ring.gen(1)
    # x0 XOR x1 = 1 => x0 + x1 + 1 = 0 mod 2
    bvar = boolean_variety(2, [f2_ring.add(f2_ring.add(x0, x1), f2_ring.one)])
    assert enum_variety_points(bvar) == [(0, 1), (1, 0)]


# =============================================================================
# 5. Contravariant Morphisms, GIT Syzygies, Grassmannians & Coordinate Hopf
# =============================================================================


def test_polynomial_map_pullback_and_composition() -> None:
    r1 = _q_ring(1)
    r2 = _q_ring(2)
    r3 = _q_ring(3)
    t = r1.gen(0)
    x, y = r2.gen(0), r2.gen(1)
    u, v, w = r3.gen(0), r3.gen(1), r3.gen(2)

    line = AffineVariety(r1, [])
    parabola = AffineVariety(r2, [r2.sub(y, r2.mul(x, x))])
    twisted_cubic = AffineVariety(
        r3,
        [r3.sub(v, r3.mul(u, u)), r3.sub(w, r3.mul(r3.mul(u, u), u))],
    )

    # phi: A^1 -> parabola, t -> (t, t^2)
    phi = PolynomialMap(line, parabola, [t, r1.mul(t, t)])
    assert isinstance(phi, RingHom)
    assert phi.eval_point((Fraction(3),)) == (Fraction(3), Fraction(9))
    assert phi(y) == r1.mul(t, t)
    assert all(
        verify_polynomial_map_laws(
            phi,
            [r2.one, x, y, r2.add(x, y), r2.mul(x, y)],
            [(Fraction(-2),), (Fraction(0),), (Fraction(3),)],
        ).values()
    )

    # psi: parabola -> twisted cubic, (x, y) -> (x, y, x*y)
    psi = PolynomialMap(parabola, twisted_cubic, [x, y, r2.mul(x, y)])
    comp = psi.compose(phi)
    assert comp.eval_point((Fraction(2),)) == (Fraction(2), Fraction(4), Fraction(8))
    assert comp(w) == r1.mul(r1.mul(t, t), t)

    # Ill-defined map rejected
    with pytest.raises(ValueError, match='not well-defined'):
        PolynomialMap(line, parabola, [t, t])


def test_syzygy_variety_z2_invariants() -> None:
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    # Z_2 acts by (x, y) -> (-x, -y); fundamental invariants pi_1=x^2, pi_2=y^2, pi_3=xy
    syz = syzygy_variety(r2, [r2.mul(x, x), r2.mul(y, y), r2.mul(x, y)])
    assert syz.ambient_dimension == 3
    assert syz.krull_dimension() == 2
    y1, y2, y3 = syz.ring.gen(0), syz.ring.gen(1), syz.ring.gen(2)
    # Exact syzygy y_1 * y_2 - y_3^2 = 0
    assert syz.ideal.contains(syz.ring.sub(syz.ring.mul(y1, y2), syz.ring.mul(y3, y3)))
    assert len(syz.ideal.basis) == 1


def test_plucker_grassmannian_variety_gr24_and_gr25() -> None:
    q = StandardField(Fraction)

    # Gr(2, 4): 6 Plucker coords, 1 quadratic relation p_01*p_23 - p_02*p_13 + p_03*p_12 = 0
    gr24 = plucker_grassmannian_variety(q, 2, 4)
    assert gr24.ambient_dimension == 6
    assert len(gr24.ideal.basis) == 1
    assert gr24.krull_dimension() == 5  # affine cone over 4D projective Gr(2, 4)
    r6 = gr24.ring
    p01, p02, p03, p12, p13, p23 = (r6.gen(i) for i in range(6))
    quadric = r6.add(r6.sub(r6.mul(p01, p23), r6.mul(p02, p13)), r6.mul(p03, p12))
    assert gr24.ideal.contains(quadric)
    # Decomposable 2-blade (1,0,0,0) ^ (0,1,1,0) => p01=1, p02=1, others 0 -> lies on Gr(2,4)
    assert gr24.contains_point((Fraction(1), Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(0)))
    # Non-decomposable 2-form e_0^e_1 + e_2^e_3 => p01=1, p23=1 -> NOT on Gr(2,4)
    assert not gr24.contains_point((Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(1)))

    # Gr(2, 5): 10 Plucker coords, affine cone dim = 2*(5-2) + 1 = 7
    gr25 = plucker_grassmannian_variety(q, 2, 5)
    assert gr25.ambient_dimension == 10
    assert gr25.krull_dimension() == 7


def test_coordinate_hopf_algebra_sl2_and_so2() -> None:
    # SL_2(Q): ad - bc - 1 = 0
    r4 = _q_ring(4)
    a, b, c, d = (r4.gen(i) for i in range(4))
    det_minus_1 = r4.sub(r4.sub(r4.mul(a, d), r4.mul(b, c)), r4.one)
    sl2 = AffineVariety(r4, [det_minus_1])
    hopf_sl2 = CoordinateHopfAlgebra(2, sl2)

    assert isinstance(hopf_sl2, HopfAlgebra)
    assert hopf_sl2.counit(a) == Fraction(1)
    assert hopf_sl2.counit(b) == Fraction(0)
    assert hopf_sl2.antipode(a) == d
    assert hopf_sl2.antipode(b) == r4.neg(b)
    assert hopf_sl2.antipode(c) == r4.neg(c)
    assert hopf_sl2.antipode(d) == a
    assert hopf_sl2.comultiply_generator(0, 0) == [(a, a), (b, c)]

    samples = [r4.one, a, b, c, d, r4.add(a, d), r4.mul(a, b)]
    assert all(verify_coordinate_hopf_laws(hopf_sl2, samples).values())

    # SL_2(F_7) works identically over a finite field
    f7_ring = MultivariatePolynomialAlgebra(ModularField(7), n_vars=4)
    af, bf, cf, df = (f7_ring.gen(i) for i in range(4))
    sl2_f7 = AffineVariety(
        f7_ring,
        [f7_ring.sub(f7_ring.sub(f7_ring.mul(af, df), f7_ring.mul(bf, cf)), f7_ring.one)],
    )
    hopf_f7 = CoordinateHopfAlgebra(2, sl2_f7)
    assert all(verify_coordinate_hopf_laws(hopf_f7, [f7_ring.one, af, bf, cf, df]).values())


# =============================================================================
# 6. Algebraic & Higher K-Theory Bridges (K_0, K_1, K_2^M)
# =============================================================================


def test_k0_serre_swan_tangent_bundle_projector_on_s2() -> None:
    r3 = _q_ring(3)
    x, y, z = r3.gen(0), r3.gen(1), r3.gen(2)
    sphere = AffineVariety(
        r3,
        [r3.sub(r3.add(r3.add(r3.mul(x, x), r3.mul(y, y)), r3.mul(z, z)), r3.one)],
    )
    ambient = AffineVariety(r3, [])

    # Tangent bundle projector P = I_3 - v v^T
    coords = (x, y, z)
    proj: dict[int, dict[int, dict[tuple[int, ...], Fraction]]] = {}
    for i in range(3):
        proj[i] = {}
        for j in range(3):
            entry = r3.sub(r3.one, r3.mul(coords[i], coords[j])) if i == j else r3.neg(r3.mul(coords[i], coords[j]))
            proj[i][j] = entry

    assert is_serre_swan_projective_bundle(sphere, proj)
    # Falsification: NOT idempotent on ambient A^3 without the sphere relation
    assert not is_serre_swan_projective_bundle(ambient, proj)


def test_k0_schubert_chern_cohomology_ring() -> None:
    q = StandardField(Fraction)
    cohom = schubert_chern_cohomology_ring(q, 2, 4)
    assert isinstance(cohom, QuotientRing)
    # Associated variety has dim_Q H*(Gr(2,4); Q) == C(4, 2) == 6
    ring = cohom.base_ring
    assert isinstance(ring, MultivariatePolynomialAlgebra)
    var = AffineVariety(ring, cohom.ideal.basis)  # type: ignore[attr-defined]
    assert len(var.quotient_basis() or []) == 6

    # Classic Schubert calculus: c_1^4 == 2 * c_2^2 in H*(Gr(2, 4); Q)
    c1, c2 = ring.gen(0), ring.gen(1)
    c1_4 = cohom.power(c1, 4)
    c2_2 = cohom.power(c2, 2)
    assert c1_4 == cohom.project(ring.smul(Fraction(2), c2_2))
    assert c1_4 != {}


def test_k0_motivic_point_count_scissor_congruence() -> None:
    f5_ring = MultivariatePolynomialAlgebra(ModularField(5), n_vars=2)
    x, y = f5_ring.gen(0), f5_ring.gen(1)
    plane = AffineVariety(f5_ring, [])  # 25 points
    line = AffineVariety(f5_ring, [y])  # 5 points
    origin = AffineVariety(f5_ring, [x, y])  # 1 point

    # [A^2] - [L] = 25 - 5 = 20, [L] - [pt] = 5 - 1 = 4
    assert motivic_point_count_homomorphism((plane, line)) == 20
    assert motivic_point_count_homomorphism((line, origin)) == 4
    assert motivic_point_count_homomorphism((plane, origin)) == 24


def test_k1_coordinate_ring_unit_inverse() -> None:
    # 1. Hyperbola xy = 1: x is a unit with inverse y
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    gm = AffineVariety(r2, [r2.sub(r2.mul(x, y), r2.one)])
    inv_x = coordinate_ring_unit_inverse(gm, x)
    assert inv_x == y

    # 2. Quadratic extension Q[x]/<x^2 - 2>: (x + 1)^{-1} = x - 1
    r1 = _q_ring(1)
    t = r1.gen(0)
    quad = AffineVariety(r1, [r1.sub(r1.mul(t, t), r1.const(Fraction(2)))])
    inv_tp1 = coordinate_ring_unit_inverse(quad, r1.add(t, r1.one))
    assert inv_tp1 == r1.sub(t, r1.one)

    # 3. Nilpotent thickening Q[x]/<x^3>: (1 - x)^{-1} = 1 + x + x^2
    nilp = AffineVariety(r1, [r1.mul(r1.mul(t, t), t)])
    inv_1mt = coordinate_ring_unit_inverse(nilp, r1.sub(r1.one, t))
    expected_geom = r1.add(r1.add(r1.one, t), r1.mul(t, t))
    assert inv_1mt == expected_geom
    assert coordinate_ring_unit_inverse(nilp, t) is None

    # 4. Popper falsification: zero divisor t in Q[t]/<t(t-1)> is NOT a unit
    two_pts = AffineVariety(r1, [r1.mul(t, r1.sub(t, r1.one))])
    assert coordinate_ring_unit_inverse(two_pts, t) is None


def test_k2_tame_symbol_padic_and_milnor_conic() -> None:
    # Steinberg relation T_p(a, 1 - a) == 1 mod p across primes and positive/negative valuations
    test_vals = [
        Fraction(2),
        Fraction(3, 5),
        Fraction(-7, 5),
        Fraction(1, 25),
        Fraction(5, 3),
        Fraction(7, 11),
    ]
    for prime in (2, 3, 5, 7, 11):
        for a in test_vals:
            assert tame_symbol_padic(a, 1 - a, prime) == 1
            assert tame_symbol_padic(a, -a, prime) == 1

    # Bimultiplicativity & skew-symmetry mod 7
    a, b, c = Fraction(14, 3), Fraction(5, 7), Fraction(2, 5)
    assert (tame_symbol_padic(a, c, 7) * tame_symbol_padic(b, c, 7)) % 7 == tame_symbol_padic(a * b, c, 7)
    assert (tame_symbol_padic(a, b, 7) * tame_symbol_padic(b, a, 7)) % 7 == 1

    # Explicit known value: T_5(5, 2) = (-1)^0 * 5^0 / 2^1 = 1/2 = 3 mod 5
    assert tame_symbol_padic(5, 2, 5) == 3

    # Milnor-Voevodsky conic variety witnessing {a, 1-a} = 0 via rational point (1, 1)
    r2 = _q_ring(2)
    conic = milnor_symbol_conic_variety(r2, Fraction(3, 7), Fraction(4, 7))
    assert conic.krull_dimension() == 1
    assert conic.contains_point((Fraction(1), Fraction(1)))

    # Non-split quaternion conic over R: -x^2 - y^2 = 1 has no point at (1, 1)
    neg_conic = milnor_symbol_conic_variety(r2, Fraction(-1), Fraction(-1))
    assert not neg_conic.contains_point((Fraction(1), Fraction(1)))

    # Top-level module export check
    assert ax.variety.AffineVariety is AffineVariety


# =============================================================================
# 7. Council Regression, Edge-Case & Falsification Suite
# =============================================================================


def test_tame_symbol_padic_rejects_invalid_primes_and_zeros() -> None:
    for bad_prime in (1, 0, -1, -7, 4, 9):
        with pytest.raises(ValueError):
            tame_symbol_padic(2, 3, bad_prime)
    for bad_type in (True, False):
        with pytest.raises(TypeError):
            tame_symbol_padic(2, 3, bad_type)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match='non-zero'):
        tame_symbol_padic(0, 3, 5)
    with pytest.raises(ValueError, match='non-zero'):
        tame_symbol_padic(2, 0, 5)


def test_plucker_grassmannian_over_galois_field_gf4() -> None:
    gf4 = GaloisField(2, (1, 1, 1))
    gr24 = plucker_grassmannian_variety(gf4, 2, 4)
    assert gr24.ambient_dimension == 6
    assert len(gr24.ideal.basis) == 1
    assert gr24.krull_dimension() == 5


def test_is_smooth_at_reducible_mixed_dimension_and_char_p() -> None:
    # 1. Line y=0 union isolated point (0, 1): V(xy, y^2 - y)
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    line_plus_pt = AffineVariety(r2, [r2.mul(x, y), r2.sub(r2.mul(y, y), y)])
    assert line_plus_pt.krull_dimension() == 1
    assert line_plus_pt.is_smooth_at((Fraction(0), Fraction(1)))  # smooth isolated point (local dim 0)
    assert line_plus_pt.is_smooth_at((Fraction(0), Fraction(0)))  # smooth point on line y=0
    assert line_plus_pt.is_smooth_at((Fraction(3), Fraction(0)))

    # 2. Plane z=0 union z-axis x=y=0: V(xz, yz)
    r3 = _q_ring(3)
    x3, y3, z3 = r3.gen(0), r3.gen(1), r3.gen(2)
    plane_union_line = AffineVariety(r3, [r3.mul(x3, z3), r3.mul(y3, z3)])
    assert plane_union_line.krull_dimension() == 2
    assert plane_union_line.is_smooth_at((Fraction(0), Fraction(0), Fraction(1)))  # smooth on z-axis
    assert plane_union_line.is_smooth_at((Fraction(1), Fraction(0), Fraction(0)))  # smooth on xy-plane
    assert not plane_union_line.is_smooth_at((Fraction(0), Fraction(0), Fraction(0)))  # intersection singularity

    # 3. Cusp on z=0 union plane z=1: V(z(z-1), (y^2 - x^3)(z - 1))
    zm1 = r3.sub(z3, r3.one)
    cusp3 = r3.sub(r3.mul(y3, y3), r3.mul(r3.mul(x3, x3), x3))
    cusp_union_plane = AffineVariety(r3, [r3.mul(z3, zm1), r3.mul(cusp3, zm1)])
    assert not cusp_union_plane.is_smooth_at((Fraction(0), Fraction(0), Fraction(0)))  # cusp singularity
    assert cusp_union_plane.is_smooth_at((Fraction(1), Fraction(1), Fraction(0)))  # smooth on cusp
    assert cusp_union_plane.is_smooth_at((Fraction(0), Fraction(0), Fraction(1)))  # smooth on plane z=1

    # 4. Positive characteristic smoothness: x^2 + y^2 - 1 = 0 over F_5
    f5_ring = MultivariatePolynomialAlgebra(ModularField(5), n_vars=2)
    xf, yf = f5_ring.gen(0), f5_ring.gen(1)
    circle_f5 = AffineVariety(
        f5_ring,
        [f5_ring.sub(f5_ring.add(f5_ring.mul(xf, xf), f5_ring.mul(yf, yf)), f5_ring.one)],
    )
    assert circle_f5.is_smooth_at((1, 0))
    assert not circle_f5.is_smooth_at((1, 1))


def test_field_compatibility_guards_across_operations() -> None:
    r_f5 = MultivariatePolynomialAlgebra(ModularField(5), n_vars=2)
    r_f7 = MultivariatePolynomialAlgebra(ModularField(7), n_vars=2)
    v5 = AffineVariety(r_f5, [r_f5.gen(0)])
    v7 = AffineVariety(r_f7, [r_f7.gen(0)])

    with pytest.raises(TypeError, match='Incompatible'):
        v5.intersect(v7)
    with pytest.raises(TypeError, match='Incompatible'):
        v5.union(v7)
    with pytest.raises(TypeError, match='Incompatible'):
        PolynomialMap(v5, v7, [r_f5.gen(0), r_f5.gen(1)])
    with pytest.raises(TypeError, match='Incompatible'):
        motivic_point_count_homomorphism((v5, v7))

    # Distinct Galois extension fields GF(4) vs GF(8) must also be rejected
    r_gf4 = MultivariatePolynomialAlgebra(GaloisField(2, (1, 1, 1)), n_vars=1)
    r_gf8 = MultivariatePolynomialAlgebra(GaloisField(2, (1, 1, 0, 1)), n_vars=1)
    vg4 = AffineVariety(r_gf4, [r_gf4.gen(0)])
    vg8 = AffineVariety(r_gf8, [r_gf8.gen(0)])
    with pytest.raises(TypeError, match='Incompatible'):
        vg4.intersect(vg8)


def test_coordinate_hopf_algebra_protocols_o2_sl3_and_non_group_rejection() -> None:
    # 1. O_2(Q): X^T X = I_2 (det = +/-1, disconnected group!)
    r4 = _q_ring(4)
    a, b, c, d = (r4.gen(i) for i in range(4))
    o2 = AffineVariety(
        r4,
        [
            r4.sub(r4.add(r4.mul(a, a), r4.mul(c, c)), r4.one),
            r4.sub(r4.add(r4.mul(b, b), r4.mul(d, d)), r4.one),
            r4.add(r4.mul(a, b), r4.mul(c, d)),
        ],
    )
    hopf_o2 = CoordinateHopfAlgebra(2, o2)
    assert isinstance(hopf_o2, HopfAlgebra)
    assert isinstance(hopf_o2, Algebra)
    assert isinstance(hopf_o2, CommRing)
    # Orthogonal matrix inverse is transpose: S(b) == c, S(c) == b
    assert hopf_o2.antipode(b) == c
    assert hopf_o2.antipode(c) == b
    o2_res = verify_coordinate_hopf_laws(hopf_o2, [r4.one, a, b, c, d, r4.mul(a, b)])
    assert all(o2_res.values())
    assert 'coproduct_homomorphism' in o2_res
    assert 'antipode_antihomomorphism' in o2_res

    # 2. SL_3(Q): 3x3 determinant = 1
    r9 = _q_ring(9)
    m = [[r9.gen(3 * r + col) for col in range(3)] for r in range(3)]
    det3 = r9.add(
        r9.sub(
            r9.mul(m[0][0], r9.sub(r9.mul(m[1][1], m[2][2]), r9.mul(m[1][2], m[2][1]))),
            r9.mul(m[0][1], r9.sub(r9.mul(m[1][0], m[2][2]), r9.mul(m[1][2], m[2][0]))),
        ),
        r9.mul(m[0][2], r9.sub(r9.mul(m[1][0], m[2][1]), r9.mul(m[1][1], m[2][0]))),
    )
    sl3 = AffineVariety(r9, [r9.sub(det3, r9.one)])
    hopf_sl3 = CoordinateHopfAlgebra(3, sl3)
    assert hopf_sl3.counit(m[0][0]) == Fraction(1)
    assert hopf_sl3.counit(m[0][1]) == Fraction(0)
    assert all(verify_coordinate_hopf_laws(hopf_sl3, [r9.one, m[0][0], m[0][1], m[2][2]]).values())

    # 3. Falsification: non-group variety containing I_2 with det=1 must be rejected!
    # V(a - 1, d - 1, c, b^2 - b) = { [[1,0],[0,1]], [[1,1],[0,1]] } — NOT closed under squaring (b=2)!
    not_closed_mul = AffineVariety(
        r4,
        [r4.sub(a, r4.one), r4.sub(d, r4.one), c, r4.sub(r4.mul(b, b), b)],
    )
    with pytest.raises(ValueError, match='not closed under matrix multiplication'):
        CoordinateHopfAlgebra(2, not_closed_mul)

    # V(ad - bc - 1, a - 1) — contains I_2, det=1, NOT closed under multiplication or inversion!
    not_subgroup = AffineVariety(
        r4,
        [r4.sub(r4.sub(r4.mul(a, d), r4.mul(b, c)), r4.one), r4.sub(a, r4.one)],
    )
    with pytest.raises(ValueError, match='not closed'):
        CoordinateHopfAlgebra(2, not_subgroup)


def test_stickelberger_and_pure_python_edge_cases() -> None:
    # 1. Reject finite fields cleanly in solve_zero_dimensional
    f5_ring = MultivariatePolynomialAlgebra(ModularField(5), n_vars=1)
    v_f5 = AffineVariety(f5_ring, [f5_ring.sub(f5_ring.mul(f5_ring.gen(0), f5_ring.gen(0)), f5_ring.one)])
    with pytest.raises(TypeError, match='enum_variety_points'):
        solve_zero_dimensional(v_f5)

    gf4_ring = MultivariatePolynomialAlgebra(GaloisField(2, (1, 1, 1)), n_vars=1)
    v_gf4 = AffineVariety(gf4_ring, [gf4_ring.gen(0)])
    with pytest.raises(TypeError, match='enum_variety_points'):
        solve_zero_dimensional(v_gf4)

    # 2. Pure-Python numeric solver: mixed rational + quadratic (x - 1)(x^2 + 1) = x^3 - x^2 + x - 1
    r1 = _q_ring(1)
    x = r1.gen(0)
    mixed = r1.mul(r1.sub(x, r1.one), r1.add(r1.mul(x, x), r1.one))
    v_mixed = AffineVariety(r1, [mixed])
    pts_mixed = _solve_lex_pure_python_numeric(v_mixed)
    assert len(pts_mixed) == 3

    # 3. Pure-Python numeric solver: tiny exact rational 10^-12 * x - 10^-12 = 0 => x = 1
    tiny = Fraction(1, 10**12)
    v_tiny = AffineVariety(r1, [r1.sub(r1.smul(tiny, x), r1.const(tiny))])
    pts_tiny = _solve_lex_pure_python_numeric(v_tiny)
    assert len(pts_tiny) == 1
    assert math.isclose(float(pts_tiny[0][0].real), 1.0, abs_tol=1e-9)

    # 4. Pure-Python numeric solver deduplicates double root (x - 2)^2 = 0
    v_dup = AffineVariety(r1, [r1.mul(r1.sub(x, r1.const(Fraction(2))), r1.sub(x, r1.const(Fraction(2))))])
    pts_dup = _solve_lex_pure_python_numeric(v_dup)
    assert len(pts_dup) == 1
    assert math.isclose(float(pts_dup[0][0].real), 2.0, abs_tol=1e-9)

    # 5. solve_exact_rational with fractional roots, shared trailing coords, and empty Q-locus
    r2 = _q_ring(2)
    x2, y2 = r2.gen(0), r2.gen(1)
    v_frac = AffineVariety(
        r2,
        [
            r2.sub(r2.smul(Fraction(7), x2), r2.const(Fraction(3))),
            r2.add(r2.smul(Fraction(4), y2), r2.const(Fraction(5))),
        ],
    )
    assert solve_exact_rational(v_frac) == [(Fraction(3, 7), Fraction(-5, 4))]

    # Three points {(0,0), (1,0), (0,1)} sharing trailing y=0
    v_tri = AffineVariety(
        r2,
        [r2.mul(x2, y2), r2.sub(r2.mul(x2, x2), x2), r2.sub(r2.mul(y2, y2), y2)],
    )
    assert solve_exact_rational(v_tri) == [
        (Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1)),
        (Fraction(1), Fraction(0)),
    ]

    # Empty Q-rational locus: x^2 + 1 = 0
    v_no_q = AffineVariety(r1, [r1.add(r1.mul(x, x), r1.one)])
    assert solve_exact_rational(v_no_q) == []


def test_finite_enum_lex_pruning_galois_copy_and_sat_edge_cases() -> None:
    # 1. n=15 Boolean equivalence chain in lex order must solve instantaneously via reverse pruning
    n = 15
    chain_clauses = []
    for i in range(1, n):
        chain_clauses.append([-i, i + 1])
        chain_clauses.append([i, -(i + 1)])
    sols = solve_f2_sat(n, chain_clauses)
    assert sols == [(0,) * n, (1,) * n]

    # 2. SAT edge cases: empty formula, empty clause, tautology, duplicate literal, invalid literal after empty
    assert solve_f2_sat(2, []) == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert solve_f2_sat(2, [[]]) == []
    assert solve_f2_sat(2, [[1, -1]]) == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert solve_f2_sat(2, [[1, 1], [-2, -2]]) == [(1, 0)]
    with pytest.raises(ValueError, match='Literal'):
        solve_f2_sat(2, [[], [99]])

    # 3. GF(2^3) non-aliased dict points
    gf8 = GaloisField(2, (1, 1, 0, 1))
    r2_gf8 = MultivariatePolynomialAlgebra(gf8, n_vars=2)
    x, y = r2_gf8.gen(0), r2_gf8.gen(1)
    v_gf8 = AffineVariety(r2_gf8, [r2_gf8.add(x, y)])
    pts = enum_variety_points(v_gf8)
    assert len(pts) == 8
    # Mutating one returned dict must not corrupt another tuple
    pts[0][0][99] = 1
    assert all(99 not in pt[1] for pt in pts)


def test_k_theory_and_morphism_edge_cases() -> None:
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)

    # milnor_symbol_conic_variety rejects zero a or b
    with pytest.raises(ValueError, match='non-zero'):
        milnor_symbol_conic_variety(r2, Fraction(0), Fraction(1))
    with pytest.raises(ValueError, match='non-zero'):
        milnor_symbol_conic_variety(r2, Fraction(1), Fraction(0))

    # PolynomialMap.identity and disjoint composition rejection
    v_x1 = AffineVariety(r2, [r2.sub(x, r2.one)])
    v_x2 = AffineVariety(r2, [r2.sub(x, r2.const(Fraction(2)))])
    id1 = PolynomialMap.identity(v_x1)
    assert id1.eval_point((Fraction(1), Fraction(5))) == (Fraction(1), Fraction(5))
    id2 = PolynomialMap.identity(v_x2)
    with pytest.raises(ValueError, match='not contained'):
        id2.compose(id1)

    # Schubert cohomology ring dimensions for Gr(1, 4) -> 4 and Gr(2, 5) -> 10
    q = StandardField(Fraction)
    for k_sub, n_amb, expected_dim in ((1, 4, 4), (2, 5, 10)):
        cohom = schubert_chern_cohomology_ring(q, k_sub, n_amb)
        base_r = cohom.base_ring
        assert isinstance(base_r, MultivariatePolynomialAlgebra)
        v_cohom = AffineVariety(base_r, cohom.ideal.basis)  # type: ignore[attr-defined]
        assert len(v_cohom.quotient_basis() or []) == expected_dim

    # Constant unit O(1) fast path
    gm = AffineVariety(r2, [r2.sub(r2.mul(x, y), r2.one)])
    assert coordinate_ring_unit_inverse(gm, r2.const(Fraction(3, 5))) == r2.const(Fraction(5, 3))


def test_verifiers_reject_vacuous_inputs_and_support_finite_stickelberger() -> None:
    r2 = _q_ring(2)
    x, y = r2.gen(0), r2.gen(1)
    v_pt = AffineVariety(r2, [r2.sub(x, r2.one), r2.sub(y, r2.const(Fraction(2)))])
    id_map = PolynomialMap.identity(v_pt)

    # Empty poly_samples raises ValueError
    with pytest.raises(ValueError, match='at least 1'):
        verify_polynomial_map_laws(id_map, [])

    # Off-variety point_samples fails pointwise_adjunction instead of vacuously passing
    res_off = verify_polynomial_map_laws(id_map, [x, y], [(Fraction(99), Fraction(99))])
    assert res_off['pointwise_adjunction'] is False

    # Empty roots=() fails root_residuals instead of vacuously passing
    res_empty_roots = verify_stickelberger_laws(v_pt, roots=())
    assert res_empty_roots['root_residuals'] is False

    # Finite-field 0-dimensional variety works cleanly with verify_stickelberger_laws
    f5_ring = MultivariatePolynomialAlgebra(ModularField(5), n_vars=2)
    xf, yf = f5_ring.gen(0), f5_ring.gen(1)
    v_f5_0d = AffineVariety(
        f5_ring,
        [f5_ring.sub(f5_ring.mul(xf, xf), f5_ring.one), f5_ring.sub(yf, f5_ring.const(2))],
    )
    assert all(verify_stickelberger_laws(v_f5_0d).values())

    # Empty samples raises ValueError in verify_coordinate_hopf_laws
    r4 = _q_ring(4)
    a, b, c, d = (r4.gen(i) for i in range(4))
    sl2 = AffineVariety(r4, [r4.sub(r4.sub(r4.mul(a, d), r4.mul(b, c)), r4.one)])
    hopf_sl2 = CoordinateHopfAlgebra(2, sl2)
    with pytest.raises(ValueError, match='at least 1'):
        verify_coordinate_hopf_laws(hopf_sl2, [])


def test_modular_and_galois_field_primality_and_unreduced_normalization() -> None:
    for bad_p in (0, 1, -3, 4, 6, 9, True, False):
        with pytest.raises(ValueError, match='prime'):
            ModularField(bad_p)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match='prime'):
            GaloisField(bad_p, (1, 1, 1))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match='irreduc_poly'):
        GaloisField(2, (1,))
    with pytest.raises(ValueError, match='irreduc_poly'):
        GaloisField(2, (1, 1, 2))

    # Symmetric unreduced normalization in GF(2^2) mod x^2 + x + 1
    gf4 = GaloisField(2, (1, 1, 1))
    assert gf4.is_zero({0: 2})
    assert gf4.is_zero({0: 1, 1: 1, 2: 1})  # P(x) == 0
    assert gf4.add({0: 2}, {}) == {}
    assert gf4.add({}, {0: 2}) == {}
    assert gf4.add({0: 1, 1: 1, 2: 1}, {}) == {}
    assert gf4.neg({0: 2, 1: 3}) == {1: 1}

