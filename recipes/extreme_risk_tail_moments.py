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
#    two stochastic paths can have identical expected returns $\mathbb{E}[X]$ and volatility $\text{Var}(X)$,
#    yet possess drastically different crash probabilities.
#    - **Skewness ($\gamma_1 = \mu_3 / \sigma^3$)**: Directional tail asymmetry (negative indicates crash risk).
#    - **Kurtosis ($\beta_2 = \mu_4 / \sigma^4$)**: Tail heaviness and outlier peakedness (fat tails $\beta_2 > 3$).
#    - **Hyperskewness ($\tilde{\mu}_5 = \mu_5 / \sigma^5$)**: 5th-order sensitivity under cascading shocks.
#
# 2. **Multi-Objective Risk & Joint Covariance Tensors (`MultivariateMomentSemiring`)**:
#    When tracking multiple interacting random variables (e.g. monetary cost $X_1$ and execution latency $X_2$),
#    `MultivariateMomentSemiring(num_vars=2, order=2)` propagates the joint distribution over graphs,
#    yielding the exact $d \times d$ **Covariance Matrix $\boldsymbol{\Sigma}$** and mean vector in a single pass.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Identifying Fat-Tail Jump Risks via 4th-Order Moments
# We analyze two distinct financial execution routes:
# - **Route A (Gaussian Stability)**: Small, symmetric price movements ($\mu=10, \sigma^2=4$).
# - **Route B (Black-Swan Jump Risk)**: Catastrophic drawdown jumps, engineered with identical Mean and Variance.

# %%
kurt_sem = ax.semiring.KurtosisSemiring()

# Route A: 50% probability cost 8.0, 50% probability cost 12.0
# Moments up to order 4: (p, p*w, p*w^2, p*w^3, p*w^4)
route_a_branch1 = (0.5, 0.5 * 8.0, 0.5 * 64.0, 0.5 * 512.0, 0.5 * 4096.0)
route_a_branch2 = (0.5, 0.5 * 12.0, 0.5 * 144.0, 0.5 * 1728.0, 0.5 * 20736.0)
route_a = kurt_sem.add(route_a_branch1, route_a_branch2)

# Route B: 90% probability cost 10.67, 10% probability catastrophic jump cost 4.0
w1, w2 = 10.666666666666666, 4.0
p1, p2 = 0.9, 0.1
route_b_branch1 = (p1, p1 * w1, p1 * (w1**2), p1 * (w1**3), p1 * (w1**4))
route_b_branch2 = (p2, p2 * w2, p2 * (w2**2), p2 * (w2**3), p2 * (w2**4))
route_b = kurt_sem.add(route_b_branch1, route_b_branch2)

print('==========================================================================')
print('Step 1: Comparative Tail Risk Audit (KurtosisSemiring)')
print('==========================================================================')
print(
    f'Route A (Symmetric)  -> Mean: {kurt_sem.mean(route_a):.2f}, Var: {kurt_sem.variance(route_a):.2f}, '
    f'Skewness: {kurt_sem.skewness(route_a):+.2f}, Kurtosis: {kurt_sem.kurtosis(route_a):.2f}'
)
print(
    f'Route B (Jump Risk)  -> Mean: {kurt_sem.mean(route_b):.2f}, Var: {kurt_sem.variance(route_b):.2f}, '
    f'Skewness: {kurt_sem.skewness(route_b):+.2f}, Kurtosis: {kurt_sem.kurtosis(route_b):.2f}'
)
print('Insight: While Mean and Variance are identical, Route B displays severe negative skewness')
print('         and elevated kurtosis, warning risk managers of hidden tail disaster.')

# %% [markdown]
# ## Step 2: Multi-Hop Cascading Shock Propagation (5th-Order Hyperskewness)
# Using `StatisticalMomentSemiring(order=5)`, we propagate multi-step transition paths
# to detect cascading asymmetric shocks across 3 network hops ($M^3$).

# %%
moment5_sem = ax.semiring.StatisticalMomentSemiring(order=5)


# Stochastic Transition Graph with 5th-order raw moment bundles:
# Edge (u -> v): 6-tuple (p, m1, m2, m3, m4, m5)
# Path 1 (prob 0.8): 2.0 -> 2.0 -> 5.0 (Total cost = 9.0)
# Path 2 (prob 0.2): 4.0 -> 5.0 -> 5.0 (Total cost = 14.0)
def make_moments(p: float, w: float) -> tuple[float, ...]:
    return tuple(p * (w**k) for k in range(6))


stochastic_network: dict[int, dict[int, tuple[float, ...]]] = {
    0: {1: make_moments(0.8, 2.0), 2: make_moments(0.2, 4.0)},
    1: {3: make_moments(1.0, 2.0)},
    2: {3: make_moments(1.0, 5.0)},
    3: {4: make_moments(1.0, 5.0)},
    4: {},
}

m3 = ax.matrix.power(stochastic_network, 3, semiring=moment5_sem)
node_0_to_4: tuple[float, ...] = m3.get(0, {}).get(4, moment5_sem.zero)

cm = moment5_sem.central_moments(node_0_to_4)
mean_val = moment5_sem.mean(node_0_to_4)
var_val = moment5_sem.variance(node_0_to_4)
sigma_val = var_val**0.5
hyperskewness = cm[5] / (sigma_val**5) if sigma_val > 0 else 0.0

print('\n==========================================================================')
print('Step 2: 3-Hop Cascading Moment Propagation (Order K=5)')
print('==========================================================================')
print(f'Destination Bundle (m0..m5): {[round(x, 2) for x in node_0_to_4]}')
print(f'Path Mean (μ):              {mean_val:.2f}')
print(f'Path Variance (σ²):         {var_val:.2f}')
print(f'Path Skewness (γ1):         {moment5_sem.skewness(node_0_to_4):+.4f} (Asymmetric burst)')
print(f'Path Kurtosis (β2):         {moment5_sem.kurtosis(node_0_to_4):.4f} (Heavy tail)')
print(f'Path Hyperskewness (μ5/σ5): {hyperskewness:+.4f} (5th-order shock sensitivity)')

# %% [markdown]
# ## Step 3: Multi-Objective Risk & Joint Covariance Matrix (MultivariateMomentSemiring)
# We track two joint variables across a multi-hop routing network:
# - $X_1$: Execution Monetary Cost ($)
# - $X_2$: Packet Network Latency (ms)
#
# `MultivariateMomentSemiring(num_vars=2, order=2)` automatically extracts the
# complete $2 \times 2$ **Covariance Matrix $\boldsymbol{\Sigma}$** and mean vector $\boldsymbol{\mu}$.

# %%
multi_sem = ax.semiring.MultivariateMomentSemiring(num_vars=2, order=2)

# Multi-index keys: (alpha_1, alpha_2)
# (0, 0) = mass p
# (1, 0) = E[X1]*p, (0, 1) = E[X2]*p
# (2, 0) = E[X1^2]*p, (0, 2) = E[X2^2]*p, (1, 1) = E[X1*X2]*p
# Path A (0 -> 1 -> 3): Cost = 2 + 3 = 5, Latency = 3 + 4 = 7
# Path B (0 -> 2 -> 3): Cost = 4 + 2 = 6, Latency = 2 + 8 = 10
joint_network: dict[int, dict[int, dict[tuple[int, ...], float]]] = {
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

m2_joint = ax.matrix.power(joint_network, 2, semiring=multi_sem)
final_joint_bundle: dict[tuple[int, ...], float] = m2_joint.get(0, {}).get(3, multi_sem.zero)

mean_vec = multi_sem.mean_vector(final_joint_bundle)
cov_matrix = multi_sem.covariance_matrix(final_joint_bundle)

print('\n==========================================================================')
print('Step 3: Multi-Objective Risk Matrix (Multivariate Moment Semiring)')
print('==========================================================================')
print(f'Mean Vector [E[Cost], E[Latency]]: [{mean_vec[0]:.2f} $, {mean_vec[1]:.2f} ms]')
print('Covariance Matrix Σ (2x2):')
print(f'  [ {cov_matrix[0][0]:+8.4f} (Var Cost),    {cov_matrix[0][1]:+8.4f} (Cov Cost,Lat) ]')
print(f'  [ {cov_matrix[1][0]:+8.4f} (Cov Lat,Cost), {cov_matrix[1][1]:+8.4f} (Var Lat)      ]')

denom = (cov_matrix[0][0] * cov_matrix[1][1]) ** 0.5
corr_12 = cov_matrix[0][1] / denom if denom > 0.0 else 0.0
print(f'Cross-Feature Correlation ρ(Cost, Latency): {corr_12:+.4f}')


def main() -> None:
    """Entry point for CLI execution."""
    print('\n==========================================================================')
    print('Recipe: Extreme Tail Risk & Multivariate Moment Propagation Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
