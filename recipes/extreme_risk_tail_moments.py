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
# # Extreme Tail Risk & Multivariate Moment Propagation
#
# ## Theory & Mathematical Foundation
#
# 1. **Beyond Mean-Variance: Higher-Order Tail Risk (`KurtosisSemiring` / `StatisticalMomentSemiring`)**:
#    In heavy-tailed financial markets, telecommunication latency, and physical turbulence,
#    two stochastic paths can have identical expected returns $\\mathbb{E}[X]$ and volatility $\\text{Var}(X)$,
#    yet possess drastically different crash probabilities.
#    - **Skewness ($\\gamma_1 = \\mu_3 / \\sigma^3$)**: Directional tail asymmetry (negative indicates crash risk).
#    - **Kurtosis ($\\beta_2 = \\mu_4 / \\sigma^4$)**: Tail heaviness and outlier peakedness (fat tails $\\beta_2 > 3$).
#    - **Hyperskewness ($\\tilde{\\mu}_5 = \\mu_5 / \\sigma^5$)**: 5th-order sensitivity under cascading shocks.
#
# 2. **Multi-Objective Risk & Joint Covariance Tensors (`MultivariateMomentSemiring`)**:
#    When tracking multiple interacting random variables (e.g. monetary cost $X_1$ and execution latency $X_2$),
#    `MultivariateMomentSemiring(num_vars=2, order=2)` propagates the joint distribution over graphs,
#    yielding the exact $d \\times d$ **Covariance Matrix $\\boldsymbol{\\Sigma}$** and mean vector in a single pass.

# %%
from typing import Any

import algebrax as ax


def audit_tail_risk_comparison(
    kurt_sem: ax.semiring.KurtosisSemiring | None = None,
) -> dict[str, dict[str, float]]:
    """Compare Gaussian stability vs. Black-Swan jump risk using KurtosisSemiring.

    Returns:
        Mapping of route name to moment metrics: mean, variance, skewness, kurtosis.
    """
    sem = kurt_sem if kurt_sem is not None else ax.semiring.KurtosisSemiring()

    # Route A (Gaussian Stability)
    route_a_b1 = (0.5, 0.5 * 8.0, 0.5 * 64.0, 0.5 * 512.0, 0.5 * 4096.0)
    route_a_b2 = (0.5, 0.5 * 12.0, 0.5 * 144.0, 0.5 * 1728.0, 0.5 * 20736.0)
    route_a = sem.add(route_a_b1, route_a_b2)

    # Route B (Black-Swan Jump Risk)
    w1, w2 = 10.666666666666666, 4.0
    p1, p2 = 0.9, 0.1
    route_b_b1 = (p1, p1 * w1, p1 * (w1**2), p1 * (w1**3), p1 * (w1**4))
    route_b_b2 = (p2, p2 * w2, p2 * (w2**2), p2 * (w2**3), p2 * (w2**4))
    route_b = sem.add(route_b_b1, route_b_b2)

    return {
        'Route A (Gaussian Stability)': {
            'mean': sem.mean(route_a),
            'variance': sem.variance(route_a),
            'skewness': sem.skewness(route_a),
            'kurtosis': sem.kurtosis(route_a),
        },
        'Route B (Jump / Crash Risk)': {
            'mean': sem.mean(route_b),
            'variance': sem.variance(route_b),
            'skewness': sem.skewness(route_b),
            'kurtosis': sem.kurtosis(route_b),
        },
    }


def propagate_cascading_moments(
    network: dict[int, dict[int, tuple[float, ...]]] | None = None,
    order: int = 5,
    steps: int = 3,
    start_node: int = 0,
    end_node: int = 4,
) -> dict[str, Any]:
    """Propagate higher-order moments across multi-hop stochastic transitions."""
    sem = ax.semiring.StatisticalMomentSemiring(order=order)

    if network is None:

        def make_moments(p: float, w: float) -> tuple[float, ...]:
            return tuple(p * (w**k) for k in range(order + 1))

        network = {
            0: {1: make_moments(0.8, 2.0), 2: make_moments(0.2, 4.0)},
            1: {3: make_moments(1.0, 2.0)},
            2: {3: make_moments(1.0, 5.0)},
            3: {4: make_moments(1.0, 5.0)},
            4: {},
        }

    power_mat = ax.matrix.power(network, steps, semiring=sem)
    bundle: tuple[float, ...] = power_mat.get(start_node, {}).get(end_node, sem.zero)
    cm = sem.central_moments(bundle)
    mean_val = sem.mean(bundle)
    var_val = sem.variance(bundle)
    sigma_val = var_val**0.5
    hyperskewness = cm[5] / (sigma_val**5) if len(cm) > 5 and sigma_val > 0 else 0.0

    return {
        'bundle': bundle,
        'central_moments': cm,
        'mean': mean_val,
        'variance': var_val,
        'skewness': sem.skewness(bundle),
        'kurtosis': sem.kurtosis(bundle) if order >= 4 else 0.0,
        'hyperskewness': hyperskewness,
    }


def evaluate_multivariate_joint_risk(
    joint_network: dict[int, dict[int, dict[tuple[int, ...], float]]] | None = None,
    num_vars: int = 2,
    order: int = 2,
    steps: int = 2,
    start_node: int = 0,
    end_node: int = 3,
) -> dict[str, Any]:
    """Propagate joint multivariate moments and extract mean vector and covariance matrix."""
    multi_sem = ax.semiring.MultivariateMomentSemiring(num_vars=num_vars, order=order)

    if joint_network is None:
        joint_network = {
            0: {
                1: {(0, 0): 1.0, (1, 0): 2.0, (0, 1): 3.0, (2, 0): 4.0, (0, 2): 9.0, (1, 1): 6.0},
                2: {(0, 0): 1.0, (1, 0): 4.0, (0, 1): 2.0, (2, 0): 16.0, (0, 2): 4.0, (1, 1): 8.0},
            },
            1: {
                3: {(0, 0): 1.0, (1, 0): 3.0, (0, 1): 4.0, (2, 0): 9.0, (0, 2): 16.0, (1, 1): 12.0},
            },
            2: {
                3: {(0, 0): 1.0, (1, 0): 2.0, (0, 1): 8.0, (2, 0): 4.0, (0, 2): 64.0, (1, 1): 16.0},
            },
            3: {},
        }

    m_power = ax.matrix.power(joint_network, steps, semiring=multi_sem)
    final_bundle = m_power.get(start_node, {}).get(end_node, multi_sem.zero)

    mean_vec = multi_sem.mean_vector(final_bundle)
    cov_mat = multi_sem.covariance_matrix(final_bundle)
    denom = (cov_mat[0][0] * cov_mat[1][1]) ** 0.5
    corr_12 = cov_mat[0][1] / denom if denom > 0.0 else 0.0

    return {
        'bundle': final_bundle,
        'mean_vector': mean_vec,
        'covariance_matrix': cov_mat,
        'correlation': corr_12,
    }


# %% [markdown]
# ## Step 1: Identifying Fat-Tail Jump Risks via 4th-Order Moments
# We analyze two distinct financial execution routes:
# - **Route A (Gaussian Stability)**: Small, symmetric price movements ($\\mu=10, \\sigma^2=4$).
# - **Route B (Black-Swan Jump Risk)**: Catastrophic drawdown jumps, engineered with identical Mean and Variance.
#
# ## Step 2: Multi-Hop Cascading Shock Propagation (5th-Order Hyperskewness)
# Using `StatisticalMomentSemiring(order=5)`, we propagate multi-step transition paths
# to detect cascading asymmetric shocks across 3 network hops ($M^3$).
#
# ## Step 3: Multi-Objective Risk & Joint Covariance Matrix (MultivariateMomentSemiring)
# We track two joint variables across a multi-hop routing network:
# - $X_1$: Execution Monetary Cost ($)
# - $X_2$: Packet Network Latency (ms)


def run_demo() -> None:
    """Run interactive risk audits and moment propagation demonstrations."""
    print('==========================================================================')
    print('Step 1: Comparative Tail Risk Audit (KurtosisSemiring)')
    print('==========================================================================')
    comparison = audit_tail_risk_comparison()
    for r_name, stats in comparison.items():
        print(
            f'{r_name:<28} -> Mean: {stats["mean"]:.2f}, Var: {stats["variance"]:.2f}, '
            f'Skewness: {stats["skewness"]:+.2f}, Kurtosis: {stats["kurtosis"]:.2f}'
        )
    print('Insight: While Mean and Variance are identical, Route B displays severe negative skewness')
    print('         and elevated kurtosis, warning risk managers of hidden tail disaster.')

    print('\n==========================================================================')
    print('Step 2: 3-Hop Cascading Moment Propagation (Order K=5)')
    print('==========================================================================')
    res2 = propagate_cascading_moments(order=5, steps=3)
    print(f'Destination Bundle (m0..m5): {[round(x, 2) for x in res2["bundle"]]}')
    print(f'Path Mean (μ):              {res2["mean"]:.2f}')
    print(f'Path Variance (σ²):         {res2["variance"]:.2f}')
    print(f'Path Skewness (γ1):         {res2["skewness"]:+.4f} (Asymmetric burst)')
    print(f'Path Kurtosis (β2):         {res2["kurtosis"]:.4f} (Heavy tail)')
    print(f'Path Hyperskewness (μ5/σ5): {res2["hyperskewness"]:+.4f} (5th-order shock sensitivity)')

    print('\n==========================================================================')
    print('Step 3: Multi-Objective Risk Matrix (Multivariate Moment Semiring)')
    print('==========================================================================')
    res3 = evaluate_multivariate_joint_risk(num_vars=2, order=2, steps=2)
    mean_vec = res3['mean_vector']
    cov_matrix = res3['covariance_matrix']
    corr_12 = res3['correlation']
    print(f'Mean Vector [E[Cost], E[Latency]]: [{mean_vec[0]:.2f} $, {mean_vec[1]:.2f} ms]')
    print('Covariance Matrix Σ (2x2):')
    print(f'  [ {cov_matrix[0][0]:+8.4f} (Var Cost),    {cov_matrix[0][1]:+8.4f} (Cov Cost,Lat) ]')
    print(f'  [ {cov_matrix[1][0]:+8.4f} (Cov Lat,Cost), {cov_matrix[1][1]:+8.4f} (Var Lat)      ]')
    print(f'Cross-Feature Correlation ρ(Cost, Latency): {corr_12:+.4f}')


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('\n==========================================================================')
    print('Recipe: Extreme Tail Risk & Multivariate Moment Propagation Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
