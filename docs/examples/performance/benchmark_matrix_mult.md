# Performance

The `mappingtools.algebra` module is optimized for **Sparse Data**.
While Python dictionaries have overhead compared to C-arrays, the algorithmic advantage of sparsity often outweighs the
constant-factor overhead.

### The Crossover Point

Below is a benchmark comparing `algebrax.matrix.dot` against a naive $O(N^3)$ list-of-lists multiplication
across varying densities and matrix sizes.

**Scenario:** Matrix Multiplication ($N \times N$).

| Density | Speedup ($N=50$) | Speedup ($N=100$) | Speedup ($N=200$) | Speedup ($N=500$) | Speedup ($N=1000$) |
|:--------|:-----------------|:------------------|:------------------|:------------------|:-------------------|
| **1%**  | **502x**         | **970x**          | **1294x**         | **1649x**         | **1742x**          |
| **5%**  | **53x**          | **60x**           | **72x**           | **85x**           | **122x**           |
| **10%** | **18x**          | **19x**           | **25x**           | **34x**           | **36x**            |
| **20%** | **6x**           | **7x**            | **7.5x**          | **6.8x**          | **10x**            |
| **50%** | **1.25x**        | **1.5x**          | **1.35x**         | **1.13x**         | **2.2x**           |
| **60%** | 0.93x            | 0.8x              | 0.98x             | 1.06x             | 1.35x              |

!!! tip "Conclusion"
Use `mappingtools` when your data density is **below 50%**.
For dense data, the overhead of dictionary hashing outweighs the benefit of skipping zeros.

### Benchmark Code

<!-- name: benchmark_matrix_multiplication -->

```python linenums="1"
import timeit
import random
from algebrax.semiring import StandardSemiring
from algebrax.matrix import dot
from algebrax.converters import sparse_to_dense_matrix
from algebrax.sparsity import density as calculate_density


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


def naive_multiply(A, B):
    """Standard O(N^3) list-of-lists multiplication."""
    rows_A = len(A)
    cols_A = len(A[0])
    rows_B = len(B)
    cols_B = len(B[0])

    if cols_A != rows_B:
        raise ValueError("Incompatible dimensions")

    C = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]

    for i in range(rows_A):
        for j in range(cols_B):
            total = 0.0
            for k in range(cols_A):
                total += A[i][k] * B[k][j]
            C[i][j] = total
    return C


def run_benchmark(N, target_density, iterations):
    # Setup Data (Apples to Apples)
    sparse_A = generate_sparse_matrix(N, N, target_density)
    sparse_B = generate_sparse_matrix(N, N, target_density)

    # Use library converter
    dense_A = sparse_to_dense_matrix(sparse_A, shape=(N, N))
    dense_B = sparse_to_dense_matrix(sparse_B, shape=(N, N))

    # Calculate actual density using library function
    actual_density_A = calculate_density(sparse_A, capacity=N * N)
    actual_density_B = calculate_density(sparse_B, capacity=N * N)
    avg_density = (actual_density_A + actual_density_B) / 2

    # 1. Naive List-of-Lists
    t_naive = timeit.timeit(lambda: naive_multiply(dense_A, dense_B), number=iterations)
    avg_naive = t_naive / iterations

    # 2. MappingTools Sparse
    t_sparse = timeit.timeit(lambda: dot(sparse_A, sparse_B, semiring=StandardSemiring()), number=iterations)
    avg_sparse = t_sparse / iterations

    speedup = avg_naive / avg_sparse

    print(f"{avg_density * 100:6.2f}% | {avg_naive:8.6f}s | {avg_sparse:8.6f}s | {speedup:6.2f}x")


def benchmark():
    # Run for different sizes
    for N in [50, 100, 200, 500, 1000]:
        iterations = 100 if N == 50 else 50 if N == 100 else 5 if N == 200 else 1
        densities = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

        print(f"Benchmark: Matrix Multiplication ({N}x{N})")
        print(f"Iterations: {iterations}")
        print("-" * 60)
        print(f"{'Density':8} | {'Naive':10} | {'Sparse':10} | {'Speedup':7}")
        print("-" * 60)

        for d in densities:
            run_benchmark(N, d, iterations)


if __name__ == "__main__":
    benchmark()
```
