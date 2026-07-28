# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Supply Chain Logistics & Demand Analysis Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Multidimensional Tensor Contraction (algebrax.trie.AlgebraicTrie):
   An AlgebraicTrie acts as a multi-dimensional sparse tensor. Setting 3D paths
   (Warehouse, Region, Season) -> Volume and calling `trie.contract((Warehouse,))`
   sums subtree quantities over the StandardSemiring to yield regional demand totals.

2. Bounded Lattice Operations (algebrax.lattice.join & algebrax.lattice.meet):
   Given regional demand vectors P and Q across two product categories:
   - Join (LUB / P v Q): Computes peak capacity requirements (max_k(P[k], Q[k])).
   - Meet (GLB / P ^ Q): Computes minimum baseline requirements (min_k(P[k], Q[k])).

3. Relative Entropy Divergence (algebrax.probability.kl_divergence):
   Kullback-Leibler divergence D_KL(Demand || Supply) = sum d_i * ln(d_i / s_i)
   quantifies distribution mismatch between inventory allocations and customer demand.
================================================================================
"""

from algebrax.lattice import join, meet
from algebrax.probability import kl_divergence
from algebrax.semiring import StandardSemiring
from algebrax.trie import AlgebraicTrie


def main() -> None:
    print('==========================================================================')
    print('Use Case: Supply Chain Logistics & Demand Distribution Analysis')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to aggregate sparse')
    print('      tensors, compute lattice demand bounds, and audit inventory KL divergence.')

    # --- Step 1: Multidimensional Tensor Contraction via AlgebraicTrie ---
    print('\n[Step 1] Multidimensional Demand Tensor Contraction (AlgebraicTrie)...')
    print('Explanation: AlgebraicTrie acts as a sparse tensor over StandardSemiring.')
    print('             Storing 3D paths (Warehouse, Region, Season) -> Volume allows')
    print('             fast subtree summation via `trie.contract(prefix)`.')

    trie = AlgebraicTrie(StandardSemiring)

    # Insert demand points: (Warehouse_ID, Region_ID, Season) -> Units
    trie.add((0, 101, 'Summer'), 500.0)
    trie.add((0, 101, 'Winter'), 300.0)
    trie.add((0, 102, 'Summer'), 200.0)
    trie.add((1, 101, 'Summer'), 400.0)
    trie.add((1, 103, 'Winter'), 600.0)

    print(f'Total Unique Tensor Entry Paths: {len(trie)}')
    print(f'Exact Demand at (Warehouse 0, Region 101, Summer): {trie[(0, 101, "Summer")]:.1f} units')

    # Contract subtree totals per warehouse
    wh0_total = trie.contract((0,))
    wh1_total = trie.contract((1,))
    print(f'Contracted Total Demand for Warehouse 0: {wh0_total:.1f} units')
    print(f'Contracted Total Demand for Warehouse 1: {wh1_total:.1f} units')

    # --- Step 2: Bounded Lattice Join & Meet Operations ---
    print('\n[Step 2] Peak & Baseline Capacity Bounds (Lattice Join & Meet)...')
    print('Explanation: Lattice Join (LUB / v) extracts peak capacity requirements.')
    print('             Lattice Meet (GLB / ^) extracts baseline safety stock requirements.')

    category_a_demand = {'Region_North': 1200.0, 'Region_South': 800.0, 'Region_East': 1500.0}
    category_b_demand = {'Region_North': 950.0, 'Region_South': 1100.0, 'Region_East': 1300.0}

    peak_capacity_join = join(category_a_demand, category_b_demand)
    baseline_stock_meet = meet(category_a_demand, category_b_demand)

    print('\nCategory A Demand: ', category_a_demand)
    print('Category B Demand: ', category_b_demand)

    print('\nPeak Capacity Requirements (Lattice Join):')
    for reg, val in sorted(peak_capacity_join.items()):
        print(f'  {reg}: {val:.1f} units')

    print('\nBaseline Safety Stock Requirements (Lattice Meet):')
    for reg, val in sorted(baseline_stock_meet.items()):
        print(f'  {reg}: {val:.1f} units')

    # --- Step 3: Inventory Allocation Divergence Audit ---
    print('\n[Step 3] Inventory Allocation Divergence (KL Divergence)...')
    print('Explanation: KL Divergence D_KL(Demand || Supply) measures relative entropy')
    print('             mismatch between actual demand and warehouse stock distribution.')

    # Normalized demand probability distribution vs inventory allocation
    actual_demand_dist = {'Region_North': 0.40, 'Region_South': 0.25, 'Region_East': 0.35}
    inventory_alloc_dist = {'Region_North': 0.30, 'Region_South': 0.30, 'Region_East': 0.40}

    kl_div_score = kl_divergence(actual_demand_dist, inventory_alloc_dist)

    print('\nActual Demand Distribution:     ', actual_demand_dist)
    print('Warehouse Inventory Allocation: ', inventory_alloc_dist)
    print(f'\nInventory Allocation Divergence D_KL(Demand || Supply): {kl_div_score:.6f} nats')

    if kl_div_score < 0.05:
        print('Audit Verdict: EXCELLENT ALIGNMENT - Minimal distribution mismatch.')
    else:
        print('Audit Verdict: MISMATCH DETECTED - Rebalancing recommended.')

    print('\n==========================================================================')
    print('Use Case Completed: Supply Chain Logistics Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
