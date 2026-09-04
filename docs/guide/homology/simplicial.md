---
title: Simplicial Complexes & Betti Numbers
description: Topological boundary operators, boundary nilpotency, and persistent Betti numbers.
---

# Simplicial Complexes (`algebrax.homology.SimplicialComplex`)

`algebrax.homology` computes topological invariants, boundary operators ($D_k$), and Betti numbers ($\beta_k$)
over abstract simplicial complexes.

## Theoretical Foundations

1. **Boundary Operator ($D_k$)**: Maps each $k$-simplex to its alternating sum of $(k-1)$-faces:
   $$D_k([v_0, \dots, v_k]) = \sum_{i=0}^k (-1)^i [v_0, \dots, \hat{v}_i, \dots, v_k]$$
2. **Homological Nilpotency**: The composition of consecutive boundaries is identically zero:
   $$D_{k-1} \circ D_k = 0$$
3. **Betti Numbers ($\beta_k$)**: The dimension of the $k$-th homology group $H_k = \ker(D_k) / \text{im}(D_{k+1})$:
   $$\beta_k = \dim(\ker D_k) - \text{rank}(D_{k+1})$$

## Usage Example

```python
import algebrax as ax

# Construct hollow circle S^1
edges = [(0, 1), (1, 2), (2, 3), (0, 3)]
sc = ax.homology.SimplicialComplex(edges)

# Verify nilpotency
assert sc.verify_nilpotency(k=1)

# Compute Betti numbers
betti = sc.betti_numbers(max_k=1)
print("Betti numbers:", betti)
# beta_0 = 1 (1 connected component), beta_1 = 1 (1 topological loop)
```

## Related Recipes & Applications

* [Topological Homology & Betti Barcodes](../../recipes.md) — Simplicial verification and Betti barcodes.
* [Topological Data Analysis](../../recipes.md) — Persistent homology over point clouds.
