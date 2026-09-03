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
#    `simulate_dfa` evaluates state transitions (Cash $\\to$ Invested $\\to$ Risk_Hedge).
#
# 2. **Spectral Asset Centrality (`algebrax.matrix.academic.eigen_centrality`)**:
#    Computes dominant eigenvector centrality ($v = \\lambda_{\\max} M v$) of cross-asset
#    correlation matrices to pinpoint systemic risk hubs.
#
# 3. **Joint Expectation & Uncertainty Variance Paths (`VarianceSemiring`)**:
#    Tracks second-order moments to compute expected return $E[X] = m_1 / p$
#    and path return variance $\\text{Var}(X) = (m_2 / p) - (E[X])^2$.

# %%
from typing import Any

import algebrax as ax


def simulate_trading_strategy(
    signals: list[str],
    dfa: dict[Any, dict[str, Any]] | None = None,
    initial_state: Any = 'Cash',
) -> Any:
    """Execute trading state transitions over market signals."""
    if dfa is None:
        dfa = {
            'Cash': {'buy_signal': 'Invested', 'hold': 'Cash', 'risk_alert': 'Risk_Hedge'},
            'Invested': {'sell_signal': 'Cash', 'risk_alert': 'Risk_Hedge', 'hold': 'Invested'},
            'Risk_Hedge': {'clear_alert': 'Cash', 'hold': 'Risk_Hedge'},
        }
    return ax.automata.simulate_dfa(initial_state, signals, dfa)


def compute_portfolio_centralities(
    correlation_matrix: dict[Any, dict[Any, float]],
) -> dict[Any, float]:
    """Calculate dominant eigenvector centrality across cross-asset correlations."""
    return ax.matrix.academic.eigen_centrality(correlation_matrix)


def evaluate_portfolio_path_variance(
    market_graph: dict[int, dict[int, tuple[float, float, float]]] | None = None,
    steps: int = 2,
    start_node: int = 0,
    end_node: int = 3,
) -> dict[str, Any]:
    """Calculate multi-step path raw moments, expected return, and variance."""
    sem = ax.semiring.VarianceSemiring()
    if market_graph is None:
        market_graph = {
            0: {1: (0.6, 2.4, 9.6), 2: (0.4, 4.8, 57.6)},
            1: {3: (1.0, 5.0, 25.0)},
            2: {3: (1.0, 15.0, 225.0)},
            3: {},
        }
    m_pow = ax.matrix.power(market_graph, steps, semiring=sem)
    bundle = m_pow.get(start_node, {}).get(end_node, sem.zero)
    mean_val = sem.mean(bundle)
    var_val = sem.variance(bundle)
    return {
        'moments': bundle,
        'mean': mean_val,
        'variance': var_val,
        'volatility': var_val**0.5,
    }


# %% [markdown]
# ## Step 1: Algorithmic Trade State Machine (`simulate_dfa`)
#
# ## Step 2: Systemic Risk Asset Centrality (`eigen_centrality`)
#
# ## Step 3: Multi-Step Return Expectation & Variance (`VarianceSemiring`)


def run_demo() -> None:
    """Run interactive portfolio risk and trade state machine demonstrations."""
    trading_dfa = {
        0: {'buy_signal': 1, 'hold': 0, 'risk_alert': 2},
        1: {'sell_signal': 0, 'risk_alert': 2, 'hold': 1},
        2: {'clear_alert': 0, 'hold': 2},
    }

    market_signal_stream = ['buy_signal', 'hold', 'risk_alert', 'hold', 'clear_alert', 'buy_signal']
    print(f'Market Signal Stream: {market_signal_stream}')

    initial_state = 0
    final_state = simulate_trading_strategy(market_signal_stream, dfa=trading_dfa, initial_state=initial_state)
    state_labels = {0: 'Cash', 1: 'Invested', 2: 'Risk_Hedge'}
    print(f'Final Execution State: State {final_state} [{state_labels.get(final_state, "Unknown")}]')
    assert final_state == 1

    asset_correlation = {
        0: {0: 1.0, 1: 0.2, 2: 0.6, 3: 0.8},
        1: {0: 0.2, 1: 1.0, 2: 0.3, 3: 0.1},
        2: {0: 0.6, 1: 0.3, 2: 1.0, 3: 0.5},
        3: {0: 0.8, 1: 0.1, 2: 0.5, 3: 1.0},
    }

    asset_names = {0: 'Tech ETF', 1: 'Bond Index', 2: 'Commodities', 3: 'Crypto Index'}
    centrality_scores = compute_portfolio_centralities(asset_correlation)

    print('\nAsset Spectral Centrality Scores:')
    for asset_id, score in sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True):
        print(f'  Asset {asset_id} [{asset_names[asset_id]}]: Centrality = {score:.4f}')

    market_graph = {
        0: {1: (0.6, 2.4, 9.6), 2: (0.4, 4.8, 57.6)},
        1: {3: (1.0, 5.0, 25.0)},
        2: {3: (1.0, 15.0, 225.0)},
        3: {},
    }

    risk_res = evaluate_portfolio_path_variance(market_graph, steps=2)
    print(f'\n2-Step Portfolio Path Raw Moments (p, m1, m2): {risk_res["moments"]}')
    print(f'Expected Return E[X]: {risk_res["mean"]:.2f}%')
    print(f'Return Variance Var(X): {risk_res["variance"]:.2f} (%^2)')
    print(f'Volatility StdDev sigma: {risk_res["volatility"]:.2f}%')


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Financial Risk Engineering Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()

