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
# # Sensor Network Reliability & Spatial Heat Gradient
#
# ## Theory & Mathematical Foundation
#
# 1. **Maximum Path Link Reliability (`algebrax.semiring.ViterbiSemiring` & `ax.matrix.power`)**:
#    `ViterbiSemiring` is the Max-Product semiring ($[0, 1], \max, \times$).
#    Matrix powers $M^k$ over `ViterbiSemiring` evaluate multi-hop network paths, returning
#    the maximum end-to-end transmission success probability $P_{\max}(u \to v)$.
#
# 2. **Spatial RBF Kernel & Thermal Gradient (`algebrax.analysis.gaussian_kernel` & `ax.analysis.gradient`)**:
#    - **Gaussian RBF Kernel** $K_{ij} = \exp\left(-\frac{d_{ij}^2}{2\sigma^2}\right)$: Converts
#      sensor distances into spatial similarity weights.
#    - **Gradient** $\text{grad}(T)_{ij} = T_j - T_i$: Computes node-to-edge temperature differences.
#
# 3. **Structural Sparsity Metrics (`algebrax.metrics.sparsity` & `ax.metrics.density`)**:
#    Quantifies active communication link proportion in large IoT sensor topologies.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Multi-Hop Max-Product Reliability (`ViterbiSemiring`)

# %%
link_probabilities = {
    0: {1: 0.90, 2: 0.70},
    1: {2: 0.85, 3: 0.95},
    2: {3: 0.60},
    3: {},
}

viterbi = ax.semiring.ViterbiSemiring()
rel_2step = ax.matrix.power(link_probabilities, 2, semiring=viterbi)
rel_3step = ax.matrix.power(link_probabilities, 3, semiring=viterbi)

p_03_via_2 = rel_2step.get(0, {}).get(3, 0.0)
p_03_via_3 = rel_3step.get(0, {}).get(3, 0.0)
best_p = max(p_03_via_2, p_03_via_3)

print("Link Success Probabilities Graph: ", link_probabilities)
print(f"2-Hop Max Reliability (Node 0 -> Node 3): {p_03_via_2 * 100:.2f}%")
print(f"3-Hop Max Reliability (Node 0 -> Node 3): {p_03_via_3 * 100:.2f}%")
print(f"Optimal End-to-End Reliability P_max(0 -> 3): {best_p * 100:.2f}%")

# %% [markdown]
# ## Step 2: Spatial RBF Gaussian Kernel & Sparsity Audit (`gaussian_kernel`)

# %%
sensor_distances = {
    0: {1: 1.5, 2: 3.0},
    1: {0: 1.5, 2: 1.0, 3: 4.0},
    2: {0: 3.0, 1: 1.0, 3: 2.0},
    3: {1: 4.0, 2: 2.0},
}

rbf_similarity = ax.analysis.gaussian_kernel(sensor_distances, sigma=2.0)
net_density = ax.metrics.density(rbf_similarity, capacity=16)
net_sparsity = ax.metrics.sparsity(rbf_similarity, capacity=16)

print("\nSpatial Gaussian RBF Similarity Matrix (sigma=2.0):")
for r in sorted(rbf_similarity.keys()):
    print(f"  Sensor {r}: {rbf_similarity[r]}")

print(f"\nNetwork Connectivity Density:  {net_density * 100:.1f}%")
print(f"Network Structural Sparsity:   {net_sparsity * 100:.1f}%")

# %% [markdown]
# ## Step 3: Discrete Thermal Flux Gradient (`analysis.gradient`)

# %%
temp_field = {0: 22.0, 1: 45.0, 2: 48.0, 3: 23.0}
topology_graph = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1, 3], 3: [1, 2]}

temp_grad = ax.analysis.gradient(temp_field, topology_graph)

print("\nSensor Thermal Readings (°C): ", temp_field)
print("\nNode-to-Edge Thermal Gradient grad(T)_ij (°C):")
for u in sorted(temp_grad.keys()):
    for v, grad_val in sorted(temp_grad[u].items()):
        tag = " <== THERMAL FLUX BOUNDARY" if abs(grad_val) > 20.0 else ""
        print(f"  Edge ({u} -> {v}): Delta T = {grad_val:+6.1f} °C{tag}")


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Sensor Network Reliability Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
