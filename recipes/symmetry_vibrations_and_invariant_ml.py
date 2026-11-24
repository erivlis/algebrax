# %%
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Symmetry-Reduced Structural Vibrations & Equivariant ML Descriptors
#
# ## Schur-Maschke SALC Projectors, Frobenius Induction & Molien Invariant Bases
# Physical assemblies—from trigonal molecules ($\text{BF}_3$, $\text{H}_3^+$) and triangular spacecraft trusses to
# 4-fold symmetric crystal plates—commute with finite point-group symmetries. Exploiting symmetry block-diagonalizes
# coupled dynamics and guarantees rotation/reflection invariance in machine-learned interatomic potentials:
#
# 1. **Symmetry-Adapted Linear Combinations (`isotypic_projector`, `reynolds_average`)**: Repairs noisy asymmetric
#    stiffness estimates into exact $S_3$-equivariant operators and projects coupled vibrations onto decoupled
#    breathing ($A_1$) and doubly degenerate shear ($E$) normal-mode sectors.
# 2. **Local-to-Global Mode Lifting (`induced_representation`, `character_inner_product`)**: Lifts local single-site
#    stabilizer modes ($H \le S_3$) to the full 3-node assembly and predicts global mode multiplicities via Frobenius
#    reciprocity without assembling global eigenvectors.
# 3. **Exact Equivariant ML Feature Bases (`compute_molien_series`, `invariant_basis_at_degree`)**: Computes the
#    Hilbert-Poincare Molien series of a $D_8$ square sensor plate and extracts exact polynomial invariants
#    ($r^2 = x^2 + y^2$, $x^4 + y^4$, $x^2 y^2$) for symmetry-preserving potential energy surfaces.

# %%
from __future__ import annotations

import math

import algebrax as ax
from algebrax.group import dihedral_group, symmetric_group
from algebrax.rep import (
    character_inner_product,
    compute_molien_series,
    dihedral_rep,
    evaluate_sparse_polynomial,
    induced_representation,
    invariant_basis_at_degree,
    is_intertwiner,
    isotypic_projector,
    mackey_intertwining_number,
    restrict_representation,
    reynolds_average,
    s3_character_table,
    symmetric_defining_rep,
    symmetric_sign_rep,
    symmetric_standard_rep,
    trivial_rep,
)
from algebrax.verification import (
    verify_frobenius_reciprocity,
    verify_molien_expansion,
    verify_polynomial_invariance,
    verify_schur_orthogonality,
)

# %% [markdown]
# ## 1. Block-Diagonalizing a Coupled $S_3$ Triangular Truss via Isotypic Projectors
#
# Consider three identical masses at the vertices of an equilateral triangle coupled by identical springs. Under vertex
# permutations $S_3$, any physically symmetric stiffness matrix $K$ must commute with the 3D defining permutation
# representation $\rho_{\text{perm}}$. If empirical system identification introduces slight measurement asymmetry into
# $K_{\text{raw}}$, `reynolds_average` projects it onto the exact $S_3$-equivariant stiffness matrix $K_{\text{sym}}$,
# and `isotypic_projector` splits $\mathbb{R}^3 = V_{A_1} \oplus V_E$ into decoupled normal-mode subspaces.

# %%
s3 = symmetric_group(3)
perm_rep = symmetric_defining_rep(3)
irrep_a1 = trivial_rep(s3)
irrep_a2 = symmetric_sign_rep(3)
irrep_e = symmetric_standard_rep(3)

s3_table = s3_character_table()
assert all(verify_schur_orthogonality(s3_table).values())

# Empirical stiffness matrix with slight calibration noise breaking S_3 symmetry
k_raw: dict[int, dict[int, float]] = {
    0: {0: 5.10, 1: -1.45, 2: -1.55},
    1: {0: -1.50, 1: 4.95, 2: -1.50},
    2: {0: -1.50, 1: -1.50, 2: 4.95},
}
assert not is_intertwiner(k_raw, perm_rep, perm_rep, s3)

# Symmetrize via the Reynolds intertwiner projector
k_sym_complex = reynolds_average(k_raw, perm_rep, perm_rep, s3)
k_sym: dict[int, dict[int, float]] = {
    r: {c: val.real for c, val in row.items()} for r, row in k_sym_complex.items()
}
assert is_intertwiner(k_sym, perm_rep, perm_rep, s3)

# Construct canonical Schur-Maschke projectors onto A1 (breathing), A2 (chiral), and E (shear)
proj_a1 = isotypic_projector(perm_rep, s3, irrep_a1.trace, irrep_a1.dimension)
proj_a2 = isotypic_projector(perm_rep, s3, irrep_a2.trace, irrep_a2.dimension)
proj_e = isotypic_projector(perm_rep, s3, irrep_e.trace, irrep_e.dimension)

mult_a1 = round(ax.matrix.trace(proj_a1).real / irrep_a1.dimension)
mult_a2 = round(ax.matrix.trace(proj_a2).real / irrep_a2.dimension)
mult_e = round(ax.matrix.trace(proj_e).real / irrep_e.dimension)

print('S_3 Triangular Truss Normal-Mode Decomposition:')
print(f'  Multiplicities in 3D coordinate space: m(A1)={mult_a1}, m(A2)={mult_a2}, m(E)={mult_e}')
assert (mult_a1, mult_a2, mult_e) == (1, 0, 1)
assert proj_a2 == {}

# Extract exact decoupled stiffness eigenvalues Directly from K_sym @ P_chi = lambda_chi * P_chi
kp_a1 = ax.matrix.dot(k_sym, proj_a1)
kp_e = ax.matrix.dot(k_sym, proj_e)
lambda_a1 = kp_a1[0][0].real / proj_a1[0][0].real
lambda_e = kp_e[0][0].real / proj_e[0][0].real

print(f'  Breathing mode eigenvalue lambda(A1) = {lambda_a1:.4f} N/m (1D non-degenerate)')
print(f'  Shear doublet eigenvalue  lambda(E)  = {lambda_e:.4f} N/m (2D doubly degenerate)')

assert math.isclose(lambda_a1, 2.0, abs_tol=1e-9)
assert math.isclose(lambda_e, 6.5, abs_tol=1e-9)

# Verify completeness P_A1 + P_E = I_3 and orthogonality P_A1 @ P_E = 0
proj_sum = ax.matrix.add(proj_a1, proj_e)
for i in range(3):
    for j in range(3):
        expected = 1.0 if i == j else 0.0
        assert math.isclose(proj_sum.get(i, {}).get(j, 0.0).real, expected, abs_tol=1e-12)
assert all(
    abs(v) < 1e-12 for row in ax.matrix.dot(proj_a1, proj_e).values() for v in row.values()
)

# %% [markdown]
# ## 2. Lifting Local Single-Site Sensors/Modes via Frobenius Induction
#
# Each vertex of the triangle is stabilized by a reflection subgroup $H \cong C_2$ of order 2 (index $[S_3 : H] = 3$).
# A local sensor or displacement at vertex `0` transforms either **symmetrically** ($W_+$, radial stretch) or
# **antisymmetrically** ($W_-$, tangential wag) under the reflection $(1\ 2)$ swapping vertices `1` and `2`:
# - Inducing the radial stretch $\operatorname{Ind}_H^{S_3}(W_+)$ spans $A_1 \oplus E$ (breathing + shear).
# - Inducing the tangential wag $\operatorname{Ind}_H^{S_3}(W_-)$ spans $A_2 \oplus E$ (pure rotation + shear)!

# %%
h_refl = (0, 2, 1)  # Reflection fixing vertex 0 and swapping vertices 1 <-> 2
h_sub = s3.subgroup([s3.identity, h_refl])

local_radial = trivial_rep(h_sub)
local_tangential = restrict_representation(irrep_a2, h_sub)

ind_radial = induced_representation(local_radial, s3, h_sub)
ind_tangential = induced_representation(local_tangential, s3, h_sub)
assert ind_radial.dimension == 3
assert ind_tangential.dimension == 3

char_a1 = {g: irrep_a1.trace(g) for g in s3.elements}
char_a2 = {g: irrep_a2.trace(g) for g in s3.elements}
char_e = {g: irrep_e.trace(g) for g in s3.elements}
char_ind_rad = {g: ind_radial.trace(g) for g in s3.elements}
char_ind_tan = {g: ind_tangential.trace(g) for g in s3.elements}

rad_decomp = (
    round(character_inner_product(char_ind_rad, char_a1, s3).real),
    round(character_inner_product(char_ind_rad, char_a2, s3).real),
    round(character_inner_product(char_ind_rad, char_e, s3).real),
)
tan_decomp = (
    round(character_inner_product(char_ind_tan, char_a1, s3).real),
    round(character_inner_product(char_ind_tan, char_a2, s3).real),
    round(character_inner_product(char_ind_tan, char_e, s3).real),
)

print('\nInduced Assembly Representations from Vertex-0 Stabilizer H <= S_3:')
print(f'  Ind(W_radial)     -> (A1, A2, E) multiplicities = {rad_decomp}')
print(f'  Ind(W_tangential) -> (A1, A2, E) multiplicities = {tan_decomp}')
assert rad_decomp == (1, 0, 1)
assert tan_decomp == (0, 1, 1)

# Verify Frobenius reciprocity and Mackey intertwining count between radial and tangential bundles
char_w_tan = {h: local_tangential.trace(h) for h in h_sub.elements}
assert all(verify_frobenius_reciprocity(char_w_tan, char_e, s3, h_sub).values())

shared_intertwiners = mackey_intertwining_number(
    {h: local_radial.trace(h) for h in h_sub.elements},
    char_w_tan,
    s3,
    h_sub,
    h_sub,
)
print(f'  Mackey Hom_S3(Ind(W_radial), Ind(W_tangential)) dimension = {shared_intertwiners} (shared E mode)')
assert shared_intertwiners == 1

# %% [markdown]
# ## 3. Exact $D_8$-Invariant Descriptors for Equivariant Potential Energy Surfaces
#
# When fitting a machine-learned potential energy surface $V(x, y)$ for an adatom on a 4-fold square crystal lattice
# ($D_8$, order 8), arbitrary polynomial features violate lattice symmetry. Computing `compute_molien_series` reveals
# the exact primary generator degrees `(2, 4)`, and `invariant_basis_at_degree` extracts a complete RREF polynomial
# feature basis guaranteed to be invariant under all 8 rotations and reflections.

# %%
d8 = dihedral_group(4)
square_rep = dihedral_rep(4)

molien = compute_molien_series(square_rep, d8)
dims_0_to_6 = [len(invariant_basis_at_degree(square_rep, d8, deg)) for deg in range(7)]
assert all(verify_molien_expansion(molien, dims_0_to_6).values())

basis_deg2 = invariant_basis_at_degree(square_rep, d8, 2)
basis_deg4 = invariant_basis_at_degree(square_rep, d8, 4)

print('\nD_8 Square-Lattice Equivariant ML Feature Basis:')
print(f'  Molien numerator={molien.numerator_coeffs}, primary denominator degrees={molien.denominator_factors}')
print(f'  Homogeneous invariant dimensions (deg 0..6): {dims_0_to_6}')
print(f'  Degree-2 invariant  I_2   = {basis_deg2[0]}')
print(f'  Degree-4 invariants I_4,a = {basis_deg4[0]}')
print(f'                      I_4,b = {basis_deg4[1]}')

assert len(basis_deg2) == 1
assert len(basis_deg4) == 2
for poly in (*basis_deg2, *basis_deg4):
    assert all(verify_polynomial_invariance(poly, square_rep, d8).values())

# Build a 4-fold anisotropic Ginzburg-Landau / ML potential V(x, y) = -1.2 * I_2 + 0.5 * I_4,a + 1.8 * I_4,b
weights = (-1.2, 0.5, 1.8)
features = (basis_deg2[0], basis_deg4[0], basis_deg4[1])


def crystal_potential(pt: tuple[float, float]) -> float:
    return sum(
        w * float(evaluate_sparse_polynomial(feat, pt).real)
        for w, feat in zip(weights, features)
    )


probe_pt = (0.65, -0.35)
v_ref = crystal_potential(probe_pt)
for g in d8.elements:
    mat = square_rep(g)
    gx = mat.get(0, {}).get(0, 0.0) * probe_pt[0] + mat.get(0, {}).get(1, 0.0) * probe_pt[1]
    gy = mat.get(1, {}).get(0, 0.0) * probe_pt[0] + mat.get(1, {}).get(1, 0.0) * probe_pt[1]
    assert math.isclose(crystal_potential((gx, gy)), v_ref, abs_tol=1e-12)

print(f'  Verified exact D_8 potential invariance across all 8 group actions at {probe_pt}: V = {v_ref:+.6f}')
