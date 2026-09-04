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
# # Matrix Fiber Bundles, Parallel Transport & Gauge Holonomy
#
# ## Theory & Mathematical Foundation
#
# 1. **Matrix-Valued Semirings (`ax.semiring.Semiring[np.ndarray]`)**:
#    In Yang-Mills gauge theory, differential geometry, and robotics kinematics, states along
#    network paths are not mere scalars, but linear transformations $U_e \\in \\text{GL}(d, \\mathbb{R})$.
#    Matrix Semirings embed $d \\times d$ linear maps directly as carrier values.
#
# 2. **Non-Commutative Composition & Parallel Transport**:
#    Path traversal corresponds to non-commutative matrix composition (path-ordered product):
#    $$U_{\\gamma} = \\prod_{i=1}^k A_i = A_k \\cdots A_2 A_1$$
#
# 3. **Curvature & Wilson Loop Holonomy**:
#    Parallel transport around a closed cycle $\\partial \\Sigma$ measures localized curvature $F_{\\mu\\nu}$.
#    The Wilson loop observable $W = \\text{Tr}(U_{\\partial \\Sigma})$ quantifies gauge field holonomy.
#
# 4. **Tropical Matrix Connection (Currency Arbitrage & Bottlenecks)**:
#    Replacing standard $(+, @)$ with $(\\min, @)$ or $(-\\ln, @)$ solves multi-asset optimal parallel
#    arbitrage across foreign exchange networks.

# %%
import math
from typing import Any

import numpy as np

import algebrax as ax


class MatrixSemiring(ax.semiring.Semiring[np.ndarray]):
    """Min-Plus Matrix Semiring modeling vector bundle connections and parallel transport."""

    def __init__(self, dim: int):
        self.dim = dim

    @property
    def zero(self) -> np.ndarray:
        return np.full((self.dim, self.dim), np.inf)

    @property
    def one(self) -> np.ndarray:
        return np.eye(self.dim)

    def add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.minimum(a, b)

    def mul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a @ b

    def power(self, a: np.ndarray, n: int) -> np.ndarray:
        if n == 0:
            return self.one
        res = self.one
        base = a.copy()
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: np.ndarray) -> np.ndarray:
        res = self.one.copy()
        term = a.copy()
        for _ in range(self.dim):
            res = self.add(res, term)
            term = self.mul(term, a)
        return res


class StandardMatrixSemiring(ax.semiring.Semiring[np.ndarray]):
    """Standard (+, @) Matrix Semiring for linear forward kinematics and rotation groups."""

    def __init__(self, dim: int):
        self.dim = dim

    @property
    def zero(self) -> np.ndarray:
        return np.zeros((self.dim, self.dim))

    @property
    def one(self) -> np.ndarray:
        return np.eye(self.dim)

    def add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a + b

    def mul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a @ b

    def power(self, a: np.ndarray, n: int) -> np.ndarray:
        if n == 0:
            return self.one
        res = self.one
        base = a.copy()
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res


def compute_parallel_transport(
    connection_matrices: list[np.ndarray],
    semiring: ax.semiring.Semiring[np.ndarray] | None = None,
) -> np.ndarray:
    """Compute cumulative parallel transport along a sequential path of connection links."""
    if not connection_matrices:
        raise ValueError('connection_matrices must not be empty')
    dim = connection_matrices[0].shape[0]
    sem = semiring if semiring is not None else StandardMatrixSemiring(dim)
    curr = sem.one
    for mat in connection_matrices:
        curr = sem.mul(curr, mat)
    return curr


def evaluate_wilson_loop_holonomy(loop_connections: list[np.ndarray]) -> tuple[np.ndarray, float]:
    """Calculate closed-loop parallel transport holonomy matrix U and trace defect Tr(I - U)."""
    holonomy_matrix = compute_parallel_transport(loop_connections)
    dim = holonomy_matrix.shape[0]
    trace_defect = float(np.trace(np.eye(dim) - holonomy_matrix))
    return holonomy_matrix, trace_defect


def solve_currency_arbitrage(rate_matrix: np.ndarray) -> dict[str, Any]:
    """Audit non-commutative currency conversion arbitrage cycles using logarithmic matrix transport."""
    log_matrix = -np.log(rate_matrix)
    dim = rate_matrix.shape[0]
    sem = MatrixSemiring(dim)
    star_closure = sem.star(log_matrix)
    arbitrage_detected = bool(np.any(np.diagonal(star_closure) < -1e-6))
    return {
        'log_distance_matrix': log_matrix,
        'closure': star_closure,
        'arbitrage_detected': arbitrage_detected,
    }


# %% [markdown]
# ## Step 1: Sequential Parallel Transport & Forward Kinematics
#
# ## Step 2: Wilson Loop Curvature Holonomy ($U_{\\partial \\Sigma}$)
#
# ## Step 3: Currency Arbitrage Cycle Audit via Tropical Matrix Star


def run_demo() -> None:
    """Execute matrix bundle parallel transport, holonomy, and arbitrage audits."""
    print('==========================================================================')
    print('Step 1: Serial 2D Robot Arm Kinematic Parallel Transport')
    print('==========================================================================')
    theta1 = math.pi / 4.0
    theta2 = math.pi / 6.0
    r1 = np.array([[math.cos(theta1), -math.sin(theta1)], [math.sin(theta1), math.cos(theta1)]])
    r2 = np.array([[math.cos(theta2), -math.sin(theta2)], [math.sin(theta2), math.cos(theta2)]])

    total_rotation = compute_parallel_transport([r1, r2])
    print(f'Link 1 Rotation (45 deg):\n{r1}')
    print(f'Link 2 Rotation (30 deg):\n{r2}')
    print(f'Cumulative End-Effector Orientation (75 deg):\n{total_rotation}')
    expected_angle = theta1 + theta2
    assert math.isclose(total_rotation[0, 0], math.cos(expected_angle), abs_tol=1e-5)

    print('\n==========================================================================')
    print('Step 2: Gauge Field Wilson Loop Holonomy Curvature Audit')
    print('==========================================================================')
    rot90 = np.array([[0.0, -1.0], [1.0, 0.0]])
    loop = [rot90, rot90, rot90, rot90]  # 4 * 90 deg = 360 deg = identity loop
    holonomy_matrix, defect = evaluate_wilson_loop_holonomy(loop)
    print(f'Closed 4-Hop Wilson Loop Matrix U:\n{holonomy_matrix}')
    print(f'Holonomy Trace Defect Tr(I - U): {defect:.6f} (Zero Curvature Closed Loop)')
    assert math.isclose(defect, 0.0, abs_tol=1e-5)

    print('\n==========================================================================')
    print('Step 3: Multi-Currency Foreign Exchange Arbitrage Audit')
    print('==========================================================================')
    rates = np.array(
        [
            [1.0, 0.85, 130.0],
            [1.18, 1.0, 153.0],
            [0.0077, 0.0065, 1.0],
        ]
    )
    arb_res = solve_currency_arbitrage(rates)
    print('Spot Currency Exchange Rate Matrix (USD, EUR, JPY):\n', rates)
    print(f'Arbitrage Cycle Detected: {arb_res["arbitrage_detected"]}')


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('\n==========================================================================')
    print('Recipe: Matrix Fiber Bundles & Parallel Transport Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
