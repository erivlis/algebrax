# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Urban Traffic Network Resilience & Bottleneck Analysis Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Tropical Semiring Shortest Paths (algebrax.semiring.TropicalSemiring):
   The Tropical Semiring (min, +) replaces standard (+, *) matrix multiplication with:
     (A (x) B)[i, j] = min_k (A[i, k] + B[k, j])
   Evaluating matrix powers M^k over the Tropical semiring computes the shortest travel
   time between all pairs of nodes using paths of exactly length k.

2. Forman-Ricci Curvature Bottlenecks (algebrax.analysis.forman_ricci_curvature):
   Forman-Ricci curvature measures local graph geometry:
     F(e) = w(e) * ( [sum_{e' ~ e} w(e')] - ... )
   Edges with negative curvature (K < 0) represent hyperbolic bridges and critical choke
   points where traffic from multiple clusters funnels through a single bottleneck.

3. Markov Steady State Flow Equilibrium (algebrax.probability.markov_steady_state):
   By normalizing outgoing edge travel times into transition probabilities P(u -> v),
   the stationary distribution pi satisfies pi = pi * P. This predicts the long-term
   percentage of active vehicles stationed at each intersection hub.
================================================================================
"""

from algebrax.analysis import forman_ricci_curvature
from algebrax.matrix.core import power
from algebrax.probability import markov_steady_state
from algebrax.semiring import TropicalSemiring


def main() -> None:
    print('==========================================================================')
    print('Use Case: Urban Traffic Network Resilience & Bottleneck Analysis')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to evaluate network')
    print('      latencies, isolate critical choke points, and compute traffic equilibrium.')

    # 1. Define a City Road Network Adjacency Graph (Travel Times in Minutes)
    print('\n[Step 0] Initializing City Transportation Graph (5 Hubs)...')
    city_network = {
        0: {1: 8.0, 2: 12.0, 3: 15.0},
        1: {0: 8.0, 2: 6.0, 4: 20.0},
        2: {0: 12.0, 1: 6.0, 3: 5.0},
        3: {0: 15.0, 2: 5.0, 4: 10.0},
        4: {1: 20.0, 3: 10.0},
    }

    hub_names = {
        0: 'Downtown Hub',
        1: 'North Suburb',
        2: 'East Industrial',
        3: 'South Port',
        4: 'West Airport',
    }

    for u in sorted(city_network.keys()):
        connections = ', '.join([f'{v} ({w:.1f}m)' for v, w in city_network[u].items()])
        print(f'  Hub {u} [{hub_names[u]}]: Connects to -> {connections}')

    # --- Step 1: Tropical Semiring Shortest Travel Time Latency ---
    print('\n[Step 1] Multi-Step Shortest Path Latencies (Tropical Semiring)...')
    print('Explanation: Tropical matrix multiplication (A x B)[i, j] = min_k (A[i,k] + B[k,j])')
    print('             computes global minimal travel times without exhaustive Dijkstra loops.')
    tropical_semiring = TropicalSemiring()

    latency_2step = power(city_network, 2, semiring=tropical_semiring)
    latency_3step = power(city_network, 3, semiring=tropical_semiring)

    print('\n2-Step Shortest Path Travel Times Matrix (Minutes):')
    for u in sorted(latency_2step.keys()):
        for v, time_val in sorted(latency_2step[u].items()):
            if time_val != float('inf'):
                print(f'  Hub {u} [{hub_names[u]}] -> Hub {v} [{hub_names[v]}]: {time_val:.1f} min')

    print('\nSpecific Routing Example:')
    dt_to_airport = latency_3step.get(0, {}).get(4, float('inf'))
    print(f'  Downtown (Hub 0) -> West Airport (Hub 4) 3-step shortest travel time: {dt_to_airport:.1f} minutes')

    # --- Step 2: Forman-Ricci Network Curvature Analysis ---
    print('\n[Step 2] Isolating Structural Choke Points (Forman-Ricci Edge Curvature)...')
    print('Explanation: Forman-Ricci curvature detects discrete geometric bottlenecks.')
    print('             Negative curvature (K < 0) pinpoints bridge roads where traffic funnels.')
    edge_curvatures = forman_ricci_curvature(city_network)

    print('\nEdge Curvature Audit Results:')
    for (u, v), k_val in sorted(edge_curvatures.items()):
        classification = 'CRITICAL CHOKE POINT (Bridge)' if k_val < 0 else 'Cluster / Well-Connected'
        print(f'  Road ({u} <-> {v}) [{hub_names[u]} <-> {hub_names[v]}]: K = {k_val:+.4f} [{classification}]')

    # --- Step 3: Markov Steady State Equilibrium Traffic Density ---
    print('\n[Step 3] Long-Term Traffic Equilibrium (Markov Steady State)...')
    print('Explanation: Normalizes inverse travel times into transition probabilities P(u -> v).')
    print('             Solves pi = pi * P for the stationary distribution of active vehicles.')
    markov_transition = {}
    for u, neighbors in city_network.items():
        total_inv_weight = sum(1.0 / w for w in neighbors.values())
        markov_transition[u] = {v: (1.0 / w) / total_inv_weight for v, w in neighbors.items()}

    steady_state = markov_steady_state(markov_transition)

    print('\nStationary Vehicle Distribution Across City Hubs:')
    for node, prob in sorted(steady_state.items()):
        print(f'  Hub {node} [{hub_names[node]}]: {prob * 100:.2f}% of total city traffic')

    print('\n==========================================================================')
    print('Recipe Completed: Urban Traffic Network Analysis Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
