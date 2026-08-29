# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Relativistic Dirac Spinors & Clifford Spacetime Algebra $Cl(1, 3)$
#
# ## Abstract & Physical Motivation
# In standard quantum mechanics, the Dirac equation describes relativistic spin-$\frac{1}{2}$ fermions
# (electrons, positrons, quarks) using $4 \times 4$ complex matrix representations of the gamma matrices
# $\gamma^\mu$.
#
# In David Hestenes' **Spacetime Algebra (STA)**, the Dirac matrix formalism is revealed to be a matrix
# representation of the real **Clifford Geometric Algebra $Cl(1, 3)$** over Minkowski spacetime $\mathbb{R}^{1,3}$.
# In STA:
# 1. The Dirac gamma matrices $\gamma_0, \gamma_1, \gamma_2, \gamma_3$ are not abstract matrices, but
#    **orthogonal unit spacetime basis vectors** satisfying $\{\gamma_\mu, \gamma_\nu\} = 2 \eta_{\mu\nu}$.
# 2. Dirac 4-spinors $\Psi$ are isomorphic to **even multivectors** $\psi \in Cl^+(1, 3)$ (8 real dimensions).
# 3. Spatial rotations and Lorentz boosts act natively as bilateral rotor transformations:
#    $$\psi' = R \, \psi \, R^\dagger$$
# 4. The conserved Dirac probability current $J = \psi \gamma_0 \psi^\dagger$ is a physical future-directed
#    timelike 4-vector directly representing particle probability density and velocity flow.
#
# In this recipe, we implement relativistic Dirac spinors directly on top of AlgebraX's native
# `CliffordSemiring(p=1, q=3)`.
#
# ---
#
# ## Theoretical Foundations & Algebraic Rigor
#
# ### 1. Spacetime Algebra Grading in $Cl(1, 3)$
# The Minkowski metric signature is $\eta = \text{diag}(+1, -1, -1, -1)$:
# * $\gamma_0^2 = +1$ &nbsp; *(Timelike unit vector)*
# * $\gamma_1^2 = \gamma_2^2 = \gamma_3^2 = -1$ &nbsp; *(Spacelike unit vectors)*
#
# The 16-dimensional Clifford algebra $Cl(1, 3)$ is graded into 5 subspaces:
# * **Grade 0 (1 scalar):** $1$ (identity)
# * **Grade 1 (4 vectors):** $\gamma_0, \gamma_1, \gamma_2, \gamma_3$
# * **Grade 2 (6 bivectors):**
#   * 3 Spatial Rotations: $\mathbf{B}_{jk} = \gamma_j \wedge \gamma_k$ (e.g. $\gamma_{12}, \gamma_{23}, \gamma_{31}$)
#   * 3 Lorentz Boosts: $\mathbf{B}_{0k} = \gamma_0 \wedge \gamma_k$ (e.g. $\gamma_{01}, \gamma_{02}, \gamma_{03}$)
# * **Grade 3 (4 pseudovectors):** $\gamma_{012}, \gamma_{023}, \gamma_{031}, \gamma_{123}$
# * **Grade 4 (1 pseudoscalar):** $I = \gamma_0 \gamma_1 \gamma_2 \gamma_3$ with $I^2 = -1$
#
# ### 2. The Even Subalgebra $Cl^+(1, 3)$ as the Dirac Spinor Space
# Every Dirac spinor $\psi \in Cl^+(1, 3)$ is an 8-dimensional even multivector:
# $$\psi = \alpha + \sum_{\mu < \nu} B_{\mu\nu} \gamma_\mu \gamma_\nu + \beta I$$
#
# Under a spatial rotation of angle $\theta$ in the $(x, y)$-plane, the spinor rotor is:
# $$R_{\text{rot}} = \cos\left(\frac{\theta}{2}\right) - \sin\left(\frac{\theta}{2}\right) \gamma_1 \gamma_2$$
#
# * **The $4\pi$ Spinor Periodicity:**
#   * A rotation of $\theta = 2\pi$ yields $R = -1 \implies \psi \to -\psi$ (Sign flip)
#   * A rotation of $\theta = 4\pi$ yields $R = +1 \implies \psi \to +\psi$ (True physical identity)
#
# Under a Lorentz boost with rapidity $\xi = \tanh^{-1}(v/c)$ along the $x$-axis:
# $$R_{\text{boost}} = \cosh\left(\frac{\xi}{2}\right) - \sinh\left(\frac{\xi}{2}\right) \gamma_0 \gamma_1$$

# %%
import math
from collections.abc import Mapping
from functools import cache
from typing import Any

import algebrax as ax
from algebrax.semiring.algebraic import CliffordSemiring
from algebrax.typing import SparseVector


# %%
@cache
def get_sta_semiring() -> CliffordSemiring:
    """Returns the Spacetime Algebra Cl(1, 3) CliffordSemiring with signature (+ - - -)."""
    return CliffordSemiring(p=1, q=3, r=0)


def create_dirac_basis() -> dict[str, dict[tuple[int, ...], float]]:
    r"""Generates the 16 orthogonal basis blades for Spacetime Algebra Cl(1, 3)."""
    return {
        '1': {(): 1.0},
        'gamma_0': {(1,): 1.0},
        'gamma_1': {(2,): 1.0},
        'gamma_2': {(3,): 1.0},
        'gamma_3': {(4,): 1.0},
        'gamma_01': {(1, 2): 1.0},
        'gamma_02': {(1, 3): 1.0},
        'gamma_03': {(1, 4): 1.0},
        'gamma_12': {(2, 3): 1.0},
        'gamma_23': {(3, 4): 1.0},
        'gamma_31': {(2, 4): 1.0},
        'gamma_012': {(1, 2, 3): 1.0},
        'gamma_023': {(1, 3, 4): 1.0},
        'gamma_031': {(1, 2, 4): 1.0},
        'gamma_123': {(2, 3, 4): 1.0},
        'I': {(1, 2, 3, 4): 1.0},
    }


def clifford_reverse(mv: SparseVector[tuple[int, ...], float]) -> dict[tuple[int, ...], float]:
    r"""Computes the Clifford reversion (dagger) involution: \psi^\dagger.

    For blade e_{i_1 ... i_k}, the reversion sign is (-1)^{k(k-1)/2}.
    """
    res: dict[tuple[int, ...], float] = {}
    for blade, coeff in mv.items():
        k = len(blade)
        sign = -1.0 if ((k * (k - 1)) // 2) % 2 == 1 else 1.0
        val = coeff * sign
        if not math.isclose(val, 0.0, abs_tol=1e-12):
            res[blade] = val
    return res


# %% [markdown]
# ## Step 1: Dirac Spinor Creation and Even Subalgebra Representation
#
# A general Dirac spinor $\psi \in Cl^+(1, 3)$ is specified by 8 real coefficients:
# * Scalar component (1): $\alpha$
# * Spatial bivectors ($\gamma_{12}, \gamma_{23}, \gamma_{31}$): spin / magnetic components $\mathbf{B}$
# * Timelike bivectors ($\gamma_{01}, \gamma_{02}, \gamma_{03}$): electric / boost components $\mathbf{E}$
# * Pseudoscalar ($I = \gamma_{0123}$): chiral / phase component $\beta$

# %%
def create_dirac_spinor(
    scalar: float = 1.0,
    bivector_12: float = 0.0,
    bivector_23: float = 0.0,
    bivector_31: float = 0.0,
    bivector_01: float = 0.0,
    bivector_02: float = 0.0,
    bivector_03: float = 0.0,
    pseudoscalar: float = 0.0,
) -> dict[tuple[int, ...], float]:
    """Constructs a normalized or unnormalized Dirac spinor as an even multivector."""
    raw = {
        (): scalar,
        (2, 3): bivector_12,
        (3, 4): bivector_23,
        (2, 4): bivector_31,
        (1, 2): bivector_01,
        (1, 3): bivector_02,
        (1, 4): bivector_03,
        (1, 2, 3, 4): pseudoscalar,
    }
    return {k: v for k, v in raw.items() if not math.isclose(v, 0.0, abs_tol=1e-12)}


# %% [markdown]
# ## Step 2: Spinor Spatial Rotation & $4\pi$ Periodicity Proof
#
# We apply spatial rotor $R(\theta) = \cos(\theta/2) - \sin(\theta/2) \gamma_{12}$ to rotate
# a spinor $\psi$ in the $(x, y)$-plane:
# $$\psi' = R \, \psi$$
#
# We verify that $\psi(2\pi) = -\psi(0)$ and $\psi(4\pi) = +\psi(0)$, establishing the
# fundamental spin-$\frac{1}{2}$ topological character.

# %%
def rotate_spinor(
    psi: dict[tuple[int, ...], float],
    angle_rad: float,
    plane: tuple[int, int] = (2, 3),
) -> dict[tuple[int, ...], float]:
    """Rotates a Dirac spinor in a given spatial plane by angle_rad."""
    cs = get_sta_semiring()
    half_angle = angle_rad / 2.0

    # Rotor R = cos(theta/2) - sin(theta/2) * (plane bivector)
    rotor = {
        (): math.cos(half_angle),
        plane: -math.sin(half_angle),
    }
    return cs.mul(rotor, psi)


# %% [markdown]
# ## Step 3: Relativistic Lorentz Boost on Dirac Spinors
#
# A Lorentz boost with velocity $v = c \tanh(\xi)$ along spatial axis $k$ corresponds to the hyperbolic rotor:
# $$L(\xi) = \cosh\left(\frac{\xi}{2}\right) - \sinh\left(\frac{\xi}{2}\right) \gamma_0 \gamma_k$$

# %%
def boost_spinor(
    psi: dict[tuple[int, ...], float],
    rapidity: float,
    axis: int = 1,
) -> dict[tuple[int, ...], float]:
    """Applies a relativistic Lorentz boost of rapidity xi along spatial axis k (1=x, 2=y, 3=z)."""
    cs = get_sta_semiring()
    half_xi = rapidity / 2.0
    boost_bivector = (1, 1 + axis)

    rotor = {
        (): math.cosh(half_xi),
        boost_bivector: -math.sinh(half_xi),
    }
    return cs.mul(rotor, psi)


# %% [markdown]
# ## Step 4: Conserved Dirac Probability Current Vector ($J = \psi \gamma_0 \psi^\dagger$)
#
# In Spacetime Algebra, the probability density $\rho$ and spatial 3-current $\mathbf{j}$ form the
# conserved 4-vector:
# $$J = \psi \gamma_0 \psi^\dagger = J^0 \gamma_0 + J^1 \gamma_1 + J^2 \gamma_2 + J^3 \gamma_3$$
#
# Because $\gamma_0^2 = +1$ and $\psi \psi^\dagger \ge 0$, the time component $J^0 = \rho \ge 0$ is
# strictly positive-definite, and $J$ is everywhere **future-directed and timelike** ($J^2 \ge 0$).

# %%
def compute_dirac_current(
    psi: dict[tuple[int, ...], float],
) -> dict[tuple[int, ...], float]:
    r"""Computes the conserved Dirac probability 4-current vector: J = \psi \gamma_0 \psi^\dagger."""
    cs = get_sta_semiring()
    gamma_0 = {(1,): 1.0}
    psi_dag = clifford_reverse(psi)

    # J = psi * gamma_0 * psi_dag
    psi_gamma0 = cs.mul(psi, gamma_0)
    j_vector = cs.mul(psi_gamma0, psi_dag)

    # Extract only vector (grade 1) components
    return {k: v for k, v in j_vector.items() if len(k) == 1 and not math.isclose(v, 0.0, abs_tol=1e-12)}


# %% [markdown]
# ## Step 5: Causal Minkowski Graph Propagation of Dirac Spinors
#
# We evaluate the multi-hop transmission of a Dirac spinor wavepacket across a discrete Minkowski
# causal diamond grid from emission event `Origin` through intermediate spacetime nodes to detector `Target`.

# %%
def propagate_dirac_causal_graph(
    initial_spinor: dict[tuple[int, ...], float],
    mass: float = 1.0,
    delta_tau: float = 0.5,
) -> dict[str, dict[tuple[int, ...], float]]:
    """Propagates a Dirac spinor across a discrete 2-hop causal spacetime network."""
    cs = get_sta_semiring()

    # Discrete Dirac propagator edge weights: e^(-i m delta_tau) ~ cos(m dt) - sin(m dt) * I
    prop_forward = {
        (): math.cos(mass * delta_tau),
        (1, 2, 3, 4): -math.sin(mass * delta_tau),
    }

    # Spacetime diamond routing network:
    # Origin -> Event_Left (deflected via gamma_12 rotor) & Event_Right (deflected via gamma_01 boost)
    # Both converge at Target
    rotor_left = {(): math.cos(0.2), (2, 3): -math.sin(0.2)}
    boost_right = {(): math.cosh(0.3), (1, 2): -math.sinh(0.3)}

    edge_origin_left = cs.mul(prop_forward, rotor_left)
    edge_origin_right = cs.mul(prop_forward, boost_right)

    network_l1 = {
        'Origin': {'Event_Left': edge_origin_left, 'Event_Right': edge_origin_right}
    }
    network_l2 = {
        'Event_Left': {'Target': prop_forward},
        'Event_Right': {'Target': prop_forward},
    }

    # Matrix contraction: Transfer operator from Origin to Target
    transfer = ax.matrix.dot(network_l1, network_l2, semiring=cs)
    origin_to_target_prop = transfer.get('Origin', {}).get('Target', {})

    # Final spinor at detector: psi_target = Transfer * psi_initial
    final_spinor = cs.mul(origin_to_target_prop, initial_spinor)
    return {
        'Transfer_Operator': origin_to_target_prop,
        'Final_Spinor': final_spinor,
    }


# %%
def run_demo() -> None:
    """Executes verification and walkthrough demonstrations for Dirac spinors."""
    print("=== Step 1: Dirac Basis Verification ===")
    basis = create_dirac_basis()
    cs = get_sta_semiring()

    # Verify gamma_0^2 = +1, gamma_1^2 = -1
    g0_sq = cs.mul(basis['gamma_0'], basis['gamma_0'])
    g1_sq = cs.mul(basis['gamma_1'], basis['gamma_1'])
    print(f"  gamma_0^2 = {g0_sq.get((), 0.0):+.1f} (Timelike +1)")
    print(f"  gamma_1^2 = {g1_sq.get((), 0.0):+.1f} (Spacelike -1)")
    assert math.isclose(g0_sq.get((), 0.0), 1.0)
    assert math.isclose(g1_sq.get((), 0.0), -1.0)

    print("\n=== Step 2: Spinor 4π Periodicity Verification ===")
    psi_rest = create_dirac_spinor(scalar=1.0, bivector_12=0.5)

    psi_2pi = rotate_spinor(psi_rest, 2.0 * math.pi)
    psi_4pi = rotate_spinor(psi_rest, 4.0 * math.pi)

    print(f"  Initial Spinor:     {psi_rest}")
    print(f"  Rotated by 2π:      {psi_2pi} (Sign flipped!)")
    print(f"  Rotated by 4π:      {psi_4pi} (Identity restored!)")

    assert math.isclose(psi_2pi.get((), 0.0), -psi_rest.get((), 0.0), abs_tol=1e-7)
    assert math.isclose(psi_4pi.get((), 0.0), +psi_rest.get((), 0.0), abs_tol=1e-7)

    print("\n=== Step 3: Conserved Dirac 4-Current J ===")
    j_curr = compute_dirac_current(psi_rest)
    print(f"  Probability Density J^0: {j_curr.get((1,), 0.0):.4f}")
    print(f"  Spatial Flow Vector J:   {j_curr}")
    assert j_curr.get((1,), 0.0) > 0.0  # Positive probability density

    print("\n=== Step 4: Spacetime Diamond Graph Propagation ===")
    res_prop = propagate_dirac_causal_graph(psi_rest)
    final_sp = res_prop['Final_Spinor']
    print(f"  Detected Spinor at Target: {final_sp}")
    j_target = compute_dirac_current(final_sp)
    print(f"  Target Current Density J^0: {j_target.get((1,), 0.0):.4f}")
    assert j_target.get((1,), 0.0) > 0.0


def main() -> None:
    """Entry point for CLI and script execution."""
    run_demo()
    print("==========================================================================")
    print("Recipe: Relativistic Dirac Spinors Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
