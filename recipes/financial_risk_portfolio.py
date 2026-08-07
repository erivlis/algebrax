# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Financial Risk Engineering & Portfolio Management Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Algorithmic Trade Execution via State Machines (algebrax.automata.simulate_dfa):
   Automated trading strategies are modeled as Deterministic Finite Automata (DFA).
   Given a sequence of market indicators ("bull_signal", "bear_signal", "risk_alert"),
   `ax.automata.simulate_dfa` evaluates state transitions (Accumulate -> Hold -> Liquidate).

2. Spectral Asset Centrality (algebrax.matrix.academic.eigen_centrality):
   Computes the dominant eigenvector centrality (v = lambda_max * M * v) of cross-asset
   correlation matrices. High centrality pinpoints systemic asset hubs whose price
   swings propagate risk across the entire portfolio.

3. Joint Expectation & Uncertainty Variance Paths (ax.semiring.ExpectationSemiring & ax.semiring.VarianceSemiring):
   - ax.semiring.ExpectationSemiring (p, p * w): Tracks joint transition probability p and expected return p * w.
   - ax.semiring.VarianceSemiring (p, r, s, t): Tracks second-order moments to compute expected
     return E[X] = r / p and path return variance Var(X) = (t / p) - (E[X])^2.
================================================================================
"""

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Financial Risk Engineering & Portfolio Management')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to execute trade DFAs,')
    print('      compute spectral asset centrality, and evaluate return expectation & variance.')

    # --- Step 1: Algorithmic Trade Execution State Machine ---
    print('\n[Step 1] Algorithmic Trade State Machine (ax.automata.simulate_dfa)...')
    print('Explanation: DFA state machine transitions evaluate market signals.')
    print("             States: 'Cash' (0), 'Invested' (1), 'Risk_Hedge' (2).")

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

    # --- Step 2: Spectral Asset Centrality ---
    print('\n[Step 2] Systemic Risk Asset Centrality (ax.matrix.eigen_centrality)...')
    print('Explanation: Computes dominant eigenvector centrality on asset correlation matrix.')
    print('             High centrality indicates systemic assets that drive market risk.')

    # Asset Correlation Matrix: 0 (Tech ETF), 1 (Bond Index), 2 (Commodities), 3 (Crypto Index)
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

    # --- Step 3: Joint Return Expectation & Uncertainty Variance ---
    print('\n[Step 3] Multi-Step Return Expectation & Variance (ax.semiring.VarianceSemiring)...')
    print('Explanation: Evaluates matrix powers over ax.semiring.VarianceSemiring to track path mean E[X]')
    print('             and variance Var(X) = E[X^2] - (E[X])^2 across market transition states.')

    variance_semiring = ax.semiring.VarianceSemiring()

    # Asset Transition Graph with (prob, p*w, p*w, p*w^2) tuples
    # Path 1 (Conservative): prob=0.6, return=4.0% -> tuple: (0.6, 2.4, 2.4, 9.6)
    # Path 2 (Aggressive):   prob=0.4, return=12.0% -> tuple: (0.4, 4.8, 4.8, 57.6)
    market_graph = {
        0: {1: (0.6, 2.4, 2.4, 9.6), 2: (0.4, 4.8, 4.8, 57.6)},
        1: {3: (1.0, 5.0, 5.0, 25.0)},
        2: {3: (1.0, 15.0, 15.0, 225.0)},
        3: {},
    }

    m2 = ax.matrix.power(market_graph, 2, semiring=variance_semiring)
    path_stats = m2.get(0, {}).get(3, variance_semiring.zero)

    p, r, _, t = path_stats
    exp_return = r / p if p else 0.0
    var_return = (t / p) - (exp_return**2) if p else 0.0

    print(f'\n2-Step Portfolio Path Raw Stats (p, r, s, t): {path_stats}')
    print(f'Expected Return E[X]: {exp_return:.2f}%')
    print(f'Return Variance Var(X): {var_return:.2f} (%^2)')
    print(f'Volatilty StdDev sigma: {var_return**0.5:.2f}%')

    print('\n==========================================================================')
    print('Use Case Completed: Financial Risk & Portfolio Management Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
