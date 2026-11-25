# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
#     "numpy",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Robot Kinematics via Affine Algebraic Varieties & Stickelberger Solvers
#
# ## Theoretical Foundations
# 1. **Kinematic Closure Variety $V(I) \subseteq \mathbb{Q}^4$**: Parameterize planar 2R joint angles
#    $(\theta_1, \theta_2)$ algebraically via $(c_1, s_1, c_2, s_2) = (\cos\theta_1, \sin\theta_1,
#    \cos\theta_2, \sin\theta_2)$ subject to $c_i^2 + s_i^2 = 1$ and end-effector target equations.
# 2. **Stickelberger Companion Matrices**: Exact sparse multiplication operators $M_{c_1}, M_{s_1},
#    M_{c_2}, M_{s_2}$ on $k[V] = \mathbb{Q}[c_1, s_1, c_2, s_2] / I$ commute pairwise and extract
#    *all* inverse-kinematics poses (elbow-up and elbow-down) simultaneously without initial guesses.
# 3. **Kinematic Singularities via `is_smooth_at`**: At the fully extended boundary reach $r = L_1 + L_2$,
#    the Jacobian drops rank ($\operatorname{rank} J(p) < n - \dim V$), algebraically certifying a
#    kinematic singularity (double root) where `radical_zero_dim` isolates the unique outstretched pose.

# %%
import math
from fractions import Fraction

import algebrax as ax
from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
from algebrax.variety import (
    AffineVariety,
    companion_matrix,
    solve_exact_rational,
    solve_zero_dimensional,
)
from algebrax.verification import verify_affine_variety_laws, verify_stickelberger_laws


def build_2r_ik_variety(
    l1: Fraction,
    l2: Fraction,
    target_x: Fraction,
    target_y: Fraction,
) -> AffineVariety[Fraction]:
    """Construct the exact algebraic variety of a planar 2R manipulator reaching (target_x, target_y)."""
    q_field = StandardField(Fraction)
    ring = MultivariatePolynomialAlgebra(q_field, n_vars=4, order='grevlex')
    c1, s1, c2, s2 = (ring.gen(i) for i in range(4))

    # Unit-circle trigonometric constraints: c_1^2 + s_1^2 = 1, c_2^2 + s_2^2 = 1
    trig1 = ring.sub(ring.add(ring.mul(c1, c1), ring.mul(s1, s1)), ring.one)
    trig2 = ring.sub(ring.add(ring.mul(c2, c2), ring.mul(s2, s2)), ring.one)

    # End-effector position:
    # x = L1*c1 + L2*(c1*c2 - s1*s2)
    # y = L1*s1 + L2*(s1*c2 + c1*s2)
    cos_12 = ring.sub(ring.mul(c1, c2), ring.mul(s1, s2))
    sin_12 = ring.add(ring.mul(s1, c2), ring.mul(c1, s2))
    fk_x = ring.sub(ring.add(ring.smul(l1, c1), ring.smul(l2, cos_12)), ring.const(target_x))
    fk_y = ring.sub(ring.add(ring.smul(l1, s1), ring.smul(l2, sin_12)), ring.const(target_y))

    return AffineVariety(ring, [trig1, trig2, fk_x, fk_y])


# %% [markdown]
# ## Case 1: Regular Workspace Target — Simultaneous Elbow-Up & Elbow-Down Poses
#
# For a planar 2R arm with link lengths $L_1 = 2, L_2 = 1$ targeting $(2, 1)$ inside its reachable
# annulus $[1, 3]$, the kinematic variety is zero-dimensional with $\dim_{\mathbb{Q}} \mathbb{Q}[V] = 2$.
# Stickelberger companion matrices extract both inverse-kinematics solutions in one pass.

# %%
l1, l2 = Fraction(2), Fraction(1)

ik_regular = build_2r_ik_variety(l1, l2, Fraction(2), Fraction(1))
q_basis = ik_regular.quotient_basis()
assert q_basis is not None
assert len(q_basis) == 2

mc1 = companion_matrix(ik_regular, 0)
ms2 = companion_matrix(ik_regular, 3)
assert ax.matrix.commutator(mc1, ms2) == {}
assert all(verify_affine_variety_laws(ik_regular).values())
assert all(verify_stickelberger_laws(ik_regular).values())

poses = solve_zero_dimensional(ik_regular)
print('Case 1: Regular target (2, 1) with L1=2, L2=1')
print(f'  Quotient basis dim_Q(Q[V]) = {len(q_basis)} (elbow-up & elbow-down)')
for idx, pose in enumerate(poses, start=1):
    assert all(abs(complex(coord).imag) < 1e-7 for coord in pose)
    c1_val, s1_val, c2_val, s2_val = (float(complex(coord).real) for coord in pose)
    t1 = math.degrees(math.atan2(s1_val, c1_val))
    t2 = math.degrees(math.atan2(s2_val, c2_val))
    end_x = 2.0 * c1_val + (c1_val * c2_val - s1_val * s2_val)
    end_y = 2.0 * s1_val + (s1_val * c2_val + c1_val * s2_val)
    print(f'  Pose {idx}: theta1={t1:7.2f} deg, theta2={t2:7.2f} deg -> FK=({end_x:.6f}, {end_y:.6f})')
    assert math.isclose(end_x, 2.0, abs_tol=1e-6)
    assert math.isclose(end_y, 1.0, abs_tol=1e-6)

# %% [markdown]
# ## Case 2: Boundary Kinematic Singularity at Full Reach $(3, 0)$
#
# At the outer workspace boundary $r = L_1 + L_2 = 3$, elbow-up and elbow-down coalesce into a
# multiplicity-2 double point $(c_1, s_1, c_2, s_2) = (1, 0, 1, 0)$ ($\theta_1 = \theta_2 = 0$).
# `is_smooth_at` detects the Jacobian rank drop algebraically, and Seidenberg's radicalization
# (`radical_zero_dim`) reduces the scheme to a single smooth rational point.

# %%
ik_singular = build_2r_ik_variety(l1, l2, Fraction(3), Fraction(0))
boundary_pt = (Fraction(1), Fraction(0), Fraction(1), Fraction(0))
assert ik_singular.contains_point(boundary_pt)
assert not ik_singular.is_smooth_at(boundary_pt)  # Jacobian rank drop => kinematic singularity!
assert len(ik_singular.quotient_basis() or []) == 2  # Multiplicity-2 scheme

rad_singular = ik_singular.radical_zero_dim()
assert len(rad_singular.quotient_basis() or []) == 1
assert rad_singular.is_smooth_at(boundary_pt)
exact_pts = solve_exact_rational(ik_singular)
assert exact_pts == [boundary_pt]

pt_str = '(' + ', '.join(str(c) for c in exact_pts[0]) + ')'
print('\nCase 2: Boundary singularity at (3, 0) (fully outstretched)')
print(
    f'  Scheme multiplicity = {len(ik_singular.quotient_basis() or [])}, '
    f'is_smooth_at = {ik_singular.is_smooth_at(boundary_pt)}'
)
print(f'  Seidenberg radical exact point (c1, s1, c2, s2) = {pt_str}')

# %% [markdown]
# ## Case 3: Unreachable Target $(5, 0)$ Beyond Maximum Reach
#
# Beyond $L_1 + L_2 = 3$, the algebraic variety still has 2 solutions over $\mathbb{C}^4$ by Bézout's
# theorem, but none are real — certifying physical unreachability with zero numerical guesswork.

# %%
ik_far = build_2r_ik_variety(l1, l2, Fraction(5), Fraction(0))
far_roots = solve_zero_dimensional(ik_far)
has_real = any(all(abs(complex(c).imag) < 1e-7 for c in pt) for pt in far_roots)
assert not has_real
print('\nCase 3: Unreachable target (5, 0) beyond max radius L1+L2=3')
print(f'  Complex C^4 solutions = {len(far_roots)}, real physical poses = 0')
print('==========================================================================')
print('Recipe: Robot Kinematics Algebraic Variety Finished Successfully!')
print('==========================================================================')
