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
# # Financial Risk Engineering & Portfolio Management
#
# ## Theory & Mathematical Foundation
#
# 1. **Algorithmic Trade Execution via State Machines (`algebrax.automata.simulate_dfa`)**:
#    Automated trading strategies are modeled as Deterministic Finite Automata (DFA).
#    Given market indicator sequences ("buy_signal", "hold", "risk_alert"),
#    `simulate_dfa` evaluates state transitions (Cash $\to$ Invested $\to$ Risk_Hedge).
#
# 2. **Spectral Asset Centrality (`algebrax.matrix.academic.eigen_centrality`)**:
#    Computes dominant eigenvector centrality ($v = \lambda_{\max} M v$) of cross-asset
#    correlation matrices to pinpoint systemic risk hubs.
#
# 3. **Joint Expectation & Uncertainty Variance Paths (`VarianceSemiring`)**:
#    Tracks second-order moments to compute expected return $E[X] = r / p$
#    and path return variance $\text{Var}(X) = (t / p) - (E[X])^2$.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Algorithmic Trade State Machine (`simulate_dfa`)

# %%
trading_dfa = {
    0: {'buy_signal': 1, 'hold': 0, 'risk_alert': 2},
    1: {'sell_signal': 0, 'risk_alert': 2, 'hold': 1},
    2: {'clear_alert': 0, 'hold': 2},
}

market_signal_stream = ['buy_signal', 'hold', 'risk_alert', 'hold', 'clear_alert', 'buy_signal']
print(f'Market Signal Stream: {market_signal_stream}')

initial_state = 0
final_state = ax.automata.simulate_dfa(initial_state, market_signal_stream, trading_dfa)
state_labels = {0: 'Cash', 1: 'Invested', 2: 'Risk_Hedge'}
print(f'Final Execution State: State {final_state} [{state_labels.get(final_state, "Unknown")}]')
assert final_state == 1

# %% [markdown]
# ## Step 2: Systemic Risk Asset Centrality (`eigen_centrality`)

# %%
asset_correlation = {
    0: {0: 1.0, 1: 0.2, 2: 0.6, 3: 0.8},
    1: {0: 0.2, 1: 1.0, 2: 0.3, 3: 0.1},
    2: {0: 0.6, 1: 0.3, 2: 1.0, 3: 0.5},
    3: {0: 0.8, 1: 0.1, 2: 0.5, 3: 1.0},
}

asset_names = {0: 'Tech ETF', 1: 'Bond Index', 2: 'Commodities', 3: 'Crypto Index'}
centrality_scores = ax.matrix.academic.eigen_centrality(asset_correlation)

print('\nAsset Spectral Centrality Scores:')
for asset_id, score in sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True):
    print(f'  Asset {asset_id} [{asset_names[asset_id]}]: Centrality = {score:.4f}')

# %% [markdown]
# ## Step 3: Multi-Step Return Expectation & Variance (`VarianceSemiring`)

# %%
variance_semiring = ax.semiring.VarianceSemiring()

# 3-tuple: (p, m1, m2) where m1 = E[X]*p and m2 = E[X^2]*p
market_graph = {
    0: {1: (0.6, 2.4, 9.6),
        2: (0.4, 4.8, 57.6)},
    1: {3: (1.0, 5.0, 25.0)},
    2: {3: (1.0, 15.0, 225.0)},
    3: {},
}

m2 = ax.matrix.power(market_graph, 2, semiring=variance_semiring)
path_stats = m2.get(0, {}).get(3, variance_semiring.zero)

exp_return = variance_semiring.mean(path_stats)
var_return = variance_semiring.variance(path_stats)

print(f'\n2-Step Portfolio Path Raw Moments (p, m1, m2): {path_stats}')
print(f'Expected Return E[X]: {exp_return:.2f}%')
print(f'Return Variance Var(X): {var_return:.2f} (%^2)')
print(f'Volatility StdDev sigma: {var_return**0.5:.2f}%')


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Financial Risk Engineering Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
