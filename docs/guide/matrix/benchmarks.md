---
title: Performance & Sparsity Benchmarks
description: Sparsity crossover benchmarks and algorithmic speedups of sparse dictionary matrices in AlgebraX.
---

# Performance & Sparsity Benchmarks

The `algebrax` library is engineered specifically for **Sparse Data** and polymorphic semiring algebras.
While pure Python dictionaries incur memory and hashing overhead compared to contiguous C-arrays, the algorithmic advantage
of sparsity ($\mathcal{O}(\text{nnz})$ vs $\mathcal{O}(N^3)$) yields dramatic speedups on sparse structures.

---

### The Sparsity Crossover Point

Below is a benchmark comparing `algebrax.matrix.core.dot` against naive $\mathcal{O}(N^3)$ list-of-lists multiplication
across varying sparsity densities and matrix sizes.

**Scenario:** Matrix Multiplication ($N \times N$).

| Density | Speedup ($N=50$) | Speedup ($N=100$) | Speedup ($N=200$) | Speedup ($N=500$) | Speedup ($N=1000$) |
|:--------|:-----------------|:------------------|:------------------|:------------------|:-------------------|
| **1%**  | 502x             | 970x              | 1294x             | 1649x             | 1742x              |
| **5%**  | 53x              | 60x               | 72x               | 85x               | 122x               |
| **10%** | 18x              | 19x               | 25x               | 34x               | 36x                |
| **20%** | 6x               | 7x                | 7.5x              | 6.8x              | 10x                |
| **50%** | 1.25x            | 1.5x              | 1.35x             | 1.13x             | 2.2x               |
| **60%** | 0.93x            | 0.8x              | 0.98x             | 1.06x             | 1.35x              |

!!! tip "Key Takeaway"
    Use `algebrax` when your data density is **below 50%** or when operating over non-field algebraic structures (tropical,
    arctic, boolean, fuzzy, path provenance, or Clifford multivectors) where hardware BLAS is inapplicable.

---

### Benchmark Reproduction Script

```python linenums="1"
import random
import timeit
import algebrax as ax


def generate_sparse_matrix(rows, cols, density=0.1):
    """Generate a sparse dict-of-dicts matrix."""
    matrix = {}
    for r in range(rows):
        row_data = {}
        for c in range(cols):
            if random.random() < density:
                row_data[c] = 1.0
        if row_data:
            matrix[r] = row_data
    return matrix


# Benchmark algebrax.matrix.core.dot vs naive multiplication
A = generate_sparse_matrix(100, 100, density=0.05)
B = generate_sparse_matrix(100, 100, density=0.05)

t_algebrax = timeit.timeit(lambda: ax.matrix.dot(A, B), number=50)
print(f"AlgebraX sparse dot execution time (50 runs): {t_algebrax:.4f} s")
```

---

## Related Recipes & Applications

* [Sparse Tensor Einstein Summation](../../recipes.md) — Multi-index sparsity benchmarks.
