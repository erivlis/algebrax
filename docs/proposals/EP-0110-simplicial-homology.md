---
title: "EP-0110: Simplicial Homology, Betti Numbers & Persistent Barcodes"
description: "High-dimensional topological hole invariants, Betti numbers beta_k, and persistent homology."
icon: lucide/shapes
status: final
---

# EP-0110: Simplicial Homology, Betti Numbers & Persistent Barcodes

| Field       | Value                                                    |
|:------------|:---------------------------------------------------------|
| **EP**      | 0110                                                     |
| **Title**   | Simplicial Homology, Betti Numbers & Persistent Barcodes |
| **Author**  | Eran Rivlis & Antigravity                                |
| **Status**  | Final                                                    |
| **Type**    | Standards Track                                          |
| **Created** | 2026-08-01                                               |
| **Updated** | 2026-08-01                                               |

## Abstract

This proposal specifies `algebrax.homology`, building upon the foundational `SparseChainComplex` (`EP-0101`). It introduces `SimplicialComplex` for $k$-simplices $(v_0, \dots, v_k)$, calculates topological hole invariants (Betti numbers $\beta_0, \beta_1, \beta_2$), and provides persistent homology filtration analysis for Topological Data Analysis (TDA).

---

## Specification

### 1. Simplicial Complex Construction
```python
class SimplicialComplex(SparseChainComplex):
    """
    Simplicial Complex built on SparseChainComplex (EP-0101).
    """
    def add_simplex(self, simplex: tuple[int, ...]) -> None:
        ...
```

### 2. Topological Betti Numbers $\beta_k$
$$\beta_k = \dim(\ker D_k) - \text{rank}(D_{k+1})$$

```python
def betti_numbers(complex: SimplicialComplex, max_k: int = 2) -> dict[int, int]:
    """
    Compute Betti numbers [beta_0, beta_1, ..., beta_max_k] for the complex.
    """
    ...
```

---

## Deliverables

1. **Core Implementation**: `src/algebrax/homology.py` (`SimplicialComplex`, `betti_numbers`, `persistent_homology`).
2. **Unit Tests**: `tests/algebrax/test_homology.py` (verifying Betti numbers for spheres, tori, and point clouds).
3. **Use Case Recipe**: `recipes/topological_homology_betti.py` & `.ipynb`.
4. **Graphical Laboratory View**: View 21 (`view_topological_homology_group`) in `recipes/lab.py`.
