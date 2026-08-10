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
# # Urban Traffic Network Resilience & Bottleneck Analysis
#
# ## Theory & Mathematical Foundation
#
# 1. **Tropical Semiring Shortest Paths (`algebrax.semiring.TropicalSemiring`)**:
#    The Tropical Semiring $(\min, +)$ replaces standard $(+, \times)$ matrix multiplication with:
#    $$(A \otimes B)[i, j] = \min_k (A[i, k] + B[k, j])$$
#    Evaluating matrix powers $M^k$ over the Tropical semiring computes shortest travel
#    times between all node pairs using paths of length $k$.
#
# 2. **Forman-Ricci Curvature Bottlenecks (`algebrax.analysis.forman_ricci_curvature`)**:
#    Forman-Ricci curvature measures local graph geometry:
#    $$F(e) = w(e) \times \left( \sum_{e' \sim e} w(e') - \dots \right)$$
#    Edges with negative curvature ($K < 0$) represent hyperbolic bridges and critical choke
#    points where traffic funnels.
#
# 3. **Markov Steady State Flow Equilibrium (`algebrax.probability.markov_steady_state`)**:
#    Normalizes travel times into transition probabilities $P(u \to v)$
#    to solve $\pi = \pi P$ for the stationary traffic distribution.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Initializing City Transportation Graph (5 Hubs)

# %%
city_network = {
    0: {1: 8.0, 2: 12.0, 3: 15.0},
    1: {0: 8.0, 2: 6.0, 4: 20.0},
    2: {0: 12.0, 1: 6.0, 3: 5.0},
    3: {0: 15.0, 2: 5.0, 4: 10.0},
    4: {1: 20.0, 3: 10.0},
}

hub_names = {
    0: "Downtown Hub",
    1: "North Suburb",
    2: "East Industrial",
    3: "South Port",
    4: "West Airport",
}

for u in sorted(city_network.keys()):
    connections = ", ".join([f"{v} ({w:.1f}m)" for v, w in city_network[u].items()])
    print(f"  Hub {u} [{hub_names[u]}]: Connects to -> {connections}")

# %% [markdown]
# ## Step 2: Multi-Step Shortest Path Latencies (Tropical Semiring)
# Tropical matrix multiplication $(A \otimes B)[i, j] = \min_k (A[i,k] + B[k,j])$
# computes minimal travel times without exhaustive Dijkstra loops.

# %%
tropical_semiring = ax.semiring.TropicalSemiring()

latency_2step = ax.matrix.power(city_network, 2, semiring=tropical_semiring)
latency_3step = ax.matrix.power(city_network, 3, semiring=tropical_semiring)

print("\n2-Step Shortest Path Travel Times Matrix (Minutes):")
for u in sorted(latency_2step.keys()):
    for v, time_val in sorted(latency_2step[u].items()):
        if time_val != float("inf"):
            print(f"  Hub {u} [{hub_names[u]}] -> Hub {v} [{hub_names[v]}]: {time_val:.1f} min")

dt_to_airport = latency_3step.get(0, {}).get(4, float("inf"))
print(f"\nDowntown -> Airport 3-step travel time: {dt_to_airport:.1f} minutes")

# %% [markdown]
# ## Step 3: Isolating Structural Choke Points (Forman-Ricci Edge Curvature)
# Forman-Ricci curvature detects discrete geometric bottlenecks.
# Negative curvature ($K < 0$) pinpoints bridge roads where traffic funnels.

# %%
edge_curvatures = ax.analysis.forman_ricci_curvature(city_network)

print("\nEdge Curvature Audit Results:")
for (u, v), k_val in sorted(edge_curvatures.items()):
    classification = "CRITICAL CHOKE POINT (Bridge)" if k_val < 0 else "Cluster / Well-Connected"
    print(f"  Road ({u} <-> {v}) [{hub_names[u]} <-> {hub_names[v]}]: K = {k_val:+.4f} [{classification}]")

# %% [markdown]
# ## Step 4: Long-Term Traffic Equilibrium (Markov Steady State)
# Solves $\pi = \pi P$ for the stationary distribution of active vehicles across city hubs.

# %%
markov_transition = {}
for u, neighbors in city_network.items():
    total_inv_weight = sum(1.0 / w for w in neighbors.values())
    markov_transition[u] = {v: (1.0 / w) / total_inv_weight for v, w in neighbors.items()}

steady_state = ax.probability.markov_steady_state(markov_transition)

print("\nStationary Vehicle Distribution Across City Hubs:")
for node, prob in sorted(steady_state.items()):
    print(f"  Hub {node} [{hub_names[node]}]: {prob * 100:.2f}% of total city traffic")


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Urban Traffic Network Resilience & Bottleneck Analysis Finished!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
