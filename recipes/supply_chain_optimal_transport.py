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
# # Supply Chain Logistics & Demand Distribution Analysis
#
# ## Theory & Mathematical Foundation
#
# 1. **Multidimensional Tensor Contraction (`algebrax.trie.AlgebraicTrie`)**:
#    An `AlgebraicTrie` acts as a multi-dimensional sparse tensor. Setting 3D paths
#    (Warehouse, Region, Season) $\to$ Volume and calling `trie.contract((Warehouse,))`
#    sums subtree quantities over the `StandardSemiring` to yield regional demand totals.
#
# 2. **Bounded Lattice Operations (`algebrax.lattice.join` & `algebrax.lattice.meet`)**:
#    Given regional demand vectors $P$ and $Q$ across product categories:
#    - **Join** ($\text{LUB} / P \lor Q$): Computes peak capacity requirements $\max_k(P[k], Q[k])$.
#    - **Meet** ($\text{GLB} / P \land Q$): Computes minimum baseline requirements $\min_k(P[k], Q[k])$.
#
# 3. **Relative Entropy Divergence (`algebrax.probability.kl_divergence`)**:
#    Kullback-Leibler divergence $D_{\text{KL}}(\text{Demand} \parallel \text{Supply}) = \sum d_i \ln(d_i / s_i)$
#    quantifies distribution mismatch between inventory allocations and customer demand.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Multidimensional Demand Tensor Contraction (`AlgebraicTrie`)

# %%
trie = ax.trie.AlgebraicTrie(ax.semiring.StandardSemiring)

trie.add((0, 101, "Summer"), 500.0)
trie.add((0, 101, "Winter"), 300.0)
trie.add((0, 102, "Summer"), 200.0)
trie.add((1, 101, "Summer"), 400.0)
trie.add((1, 103, "Winter"), 600.0)

print(f"Total Unique Tensor Entry Paths: {len(trie)}")
print(f"Exact Demand at (Warehouse 0, Region 101, Summer): {trie[(0, 101, 'Summer')]:.1f} units")

wh0_total = trie.contract((0,))
wh1_total = trie.contract((1,))
print(f"Contracted Total Demand for Warehouse 0: {wh0_total:.1f} units")
print(f"Contracted Total Demand for Warehouse 1: {wh1_total:.1f} units")

# %% [markdown]
# ## Step 2: Peak & Baseline Capacity Bounds (Lattice Join & Meet)

# %%
category_a_demand = {"Region_North": 1200.0, "Region_South": 800.0, "Region_East": 1500.0}
category_b_demand = {"Region_North": 950.0, "Region_South": 1100.0, "Region_East": 1300.0}

peak_capacity_join = ax.lattice.join(category_a_demand, category_b_demand)
baseline_stock_meet = ax.lattice.meet(category_a_demand, category_b_demand)

print("\nCategory A Demand: ", category_a_demand)
print("Category B Demand: ", category_b_demand)

print("\nPeak Capacity Requirements (Lattice Join):")
for reg, val in sorted(peak_capacity_join.items()):
    print(f"  {reg}: {val:.1f} units")

print("\nBaseline Safety Stock Requirements (Lattice Meet):")
for reg, val in sorted(baseline_stock_meet.items()):
    print(f"  {reg}: {val:.1f} units")

# %% [markdown]
# ## Step 3: Inventory Allocation Divergence (`kl_divergence`)

# %%
actual_demand_dist = {"Region_North": 0.40, "Region_South": 0.25, "Region_East": 0.35}
inventory_alloc_dist = {"Region_North": 0.30, "Region_South": 0.30, "Region_East": 0.40}

kl_div_score = ax.probability.kl_divergence(actual_demand_dist, inventory_alloc_dist)

print("\nActual Demand Distribution:     ", actual_demand_dist)
print("Warehouse Inventory Allocation: ", inventory_alloc_dist)
print(f"\nInventory Allocation Divergence D_KL(Demand || Supply): {kl_div_score:.6f} nats")

if kl_div_score < 0.05:
    print("Audit Verdict: EXCELLENT ALIGNMENT - Minimal distribution mismatch.")
else:
    print("Audit Verdict: MISMATCH DETECTED - Rebalancing recommended.")


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Supply Chain Logistics Analysis Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
