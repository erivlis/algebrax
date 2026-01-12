---
icon: lucide/square-pi
---

# Algebra

!!! Abstract
The `algebrax` library provides mathematical primitives for sparse data structures, treating Python's
native `dict` as a first-class algebraic object.

## Semirings

A **Semiring** is an algebraic structure equipped with two operations: Addition ($\oplus$) and
Multiplication ($\otimes$).
By swapping the semiring, you can reuse the same algorithm (e.g., matrix multiplication) to solve different problems.

### Standard Semiring (Linear Algebra)

The default semiring uses standard arithmetic ($+, \times$).

<!-- name: test_standard_semiring -->

```python linenums="1"
from algebrax.semiring import StandardSemiring
from algebrax.matrix import dot

# Sparse Matrices
A = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
B = {0: {0: 5, 1: 6}, 1: {0: 7, 1: 8}}

# Standard Matrix Multiplication
C = dot(A, B, semiring=StandardSemiring())
print(C)
# output: {0: {0: 19.0, 1: 22.0}, 1: {0: 43.0, 1: 50.0}}
```

### Tropical Semiring (Shortest Path)

The **Tropical Semiring** uses $(\min, +)$. Matrix multiplication becomes the shortest path algorithm.

<!-- name: test_tropical_semiring -->

```python linenums="1"
from algebrax.semiring import TropicalSemiring
from algebrax.matrix import dot

# Graph Adjacency Matrix (Weights = Costs)
# 0 -> 1 (cost 2)
# 1 -> 2 (cost 3)
# 0 -> 2 (cost 10)
graph = {
    0: {1: 2.0, 2: 10.0},
    1: {2: 3.0}
}

# Shortest path of length 2
# path(0->2) = min(
#   cost(0->1) + cost(1->2),  # 2 + 3 = 5
#   cost(0->2) + cost(2->2)   # 10 + inf = inf
# )
paths_len_2 = dot(graph, graph, semiring=TropicalSemiring())
print(paths_len_2[0][2])
# output: 5.0
```

### Provenance Semiring (History Tracking)

The **Provenance Semiring** ($N[X]$) tracks *which* facts contributed to a result and *how many times*.
Values are polynomials where variables represent edges or facts.

<!-- name: test_provenance_semiring -->

```python linenums="1"
from algebrax.semiring import ProvenanceSemiring
from algebrax.matrix import dot

# Graph with labeled edges
# 0 -> 1 (label 'x')
# 1 -> 2 (label 'y')
# 0 -> 2 (label 'z')
graph = {
    0: {1: {('x',): 1}, 2: {('z',): 1}},
    1: {2: {('y',): 1}}
}

# Paths of length 2
# 0->1->2: x * y = xy
# 0->2: (length 1, not in result)
paths_len_2 = dot(graph, graph, semiring=ProvenanceSemiring())

print(paths_len_2[0][2])
# output: {('x', 'y'): 1}
```

### Digital Semiring (Post-Quantum Cryptography)

The **Digital Semiring** uses the sum of decimal digits to determine order.
It is used in cryptographic protocols (Huang et al., 2024).

* **Add:** Larger digit sum wins.
* **Mul:** Smaller digit sum wins.

<!-- name: test_digital_semiring -->

```python linenums="1"
from algebrax.semiring import DigitalSemiring

S = DigitalSemiring()

# (123) = 6, (45) = 9
# Add: 9 > 6 -> 45
print(S.add(123, 45))
# output: 45

# Mul: 6 < 9 -> 123
print(S.mul(123, 45))
# output: 123
```

### Custom Semiring: Convex Hull

You can define your own semiring to solve specialized problems.

Here is an example of the **Convex Hull Semiring** (Dyer, 2013, http://arxiv.org/pdf/1307.3675.pdf),
used for multi-objective optimization.

* **Values:** Sets of points (polytopes).
* **Add:** Convex Hull of Union.
* **Mul:** Minkowski Sum ($A + B = \{a+b \mid a \in A, b \in B\}$).

<!-- name: test_convex_hull_semiring -->

```python linenums="1"
from typing import Set
from algebrax.semiring import Semiring

# Simple 1D Convex Hull (Intervals)
# Value is a tuple (min, max) representing the interval [min, max]
Interval = tuple[float, float]


class IntervalSemiring:
    @property
    def zero(self) -> Interval:
        return (float('inf'), float('-inf'))  # Empty set

    @property
    def one(self) -> Interval:
        return (0.0, 0.0)  # The point {0}

    def add(self, a: Interval, b: Interval) -> Interval:
        # Convex Hull of Union: [min(a_min, b_min), max(a_max, b_max)]
        return (min(a[0], b[0]), max(a[1], b[1]))

    def mul(self, a: Interval, b: Interval) -> Interval:
        # Minkowski Sum: [a_min + b_min, a_max + b_max]
        return (a[0] + b[0], a[1] + b[1])


# Usage
semiring = IntervalSemiring()

# Set A: Interval [1, 2]
A = (1.0, 2.0)
# Set B: Interval [3, 4]
B = (3.0, 4.0)

# Union (Hull): [1, 4]
print(semiring.add(A, B))
# output: (1.0, 4.0)

# Sum: [1+3, 2+4] = [4, 6]
print(semiring.mul(A, B))
# output: (4.0, 6.0)
```

## Algebraic Trie

The `AlgebraicTrie` is a generalization of a Trie (Prefix Tree) that behaves as a Sparse Tensor over a Semiring.

<!-- name: test_algebraic_trie -->

```python linenums="1"
from algebrax.trie import AlgebraicTrie
from algebrax.semiring import StandardSemiring

# Create a Trie that sums values (Standard Semiring)
trie = AlgebraicTrie(StandardSemiring)

# Add paths
trie.add(["home", "user", "docs"], 1)
trie.add(["home", "user", "pics"], 1)
trie.add(["home", "bin"], 1)

# Contract (Sum) over a prefix
# Sum of all paths starting with "home/user"
count = trie.contract(["home", "user"])
print(count)
# output: 2.0
```

## Performance

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

## Advanced Semirings (Matrix / Fiber Bundles)

These semirings use **Matrices** as values, allowing for non-commutative operations. This models **Gauge Theory**, *
*Robotics Kinematics**, and **Currency Arbitrage**.

!!! note "Dependency"
This example requires `numpy`.

<!-- name: test_matrix_semiring -->

```python linenums="1"
import numpy as np
from algebrax.semiring import Semiring


class MatrixSemiring(Semiring[np.ndarray]):
    """
    Models a Vector Bundle connection (Parallel Transport).
    Elements are matrices.
    Plus: Element-wise Min (Aggregation).
    Times: Matrix Multiplication (Composition).
    """

    def __init__(self, dim: int):
        self.dim = dim

    @property
    def zero(self) -> np.ndarray:
        # Identity for 'Plus' (Infinity for distance)
        return np.full((self.dim, self.dim), np.inf)

    @property
    def one(self) -> np.ndarray:
        # Identity for 'Times' (Identity Matrix)
        return np.eye(self.dim)

    def add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.minimum(a, b)

    def mul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        # Non-Commutative! Order matters.
        return a @ b

    def nsum(self, a: np.ndarray, n: int) -> np.ndarray:
        # Scalar multiplication in Min-Plus is just 'a' (idempotent)
        # But for matrices, it's element-wise min n times... which is just 'a'.
        return a

    def power(self, a: np.ndarray, n: int) -> np.ndarray:
        # Matrix power using binary exponentiation
        if n == 0: return self.one
        res = self.one
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: np.ndarray) -> np.ndarray:
        # Kleene star for matrices (I + A + A^2 + ...)
        # In Tropical Matrix semiring, this solves All-Pairs Shortest Path
        # Usually implemented via Floyd-Warshall, but here's the series definition.
        # For small N, we can just sum powers up to N.
        res = self.one
        term = a
        for _ in range(self.dim):  # A^dim is usually enough for convergence in graphs
            res = self.add(res, term)
            term = self.mul(term, a)
        return res


# Usage: Currency Arbitrage / Coordinate Transform
dim = 2
ms = MatrixSemiring(dim)


# Transformation A -> B (e.g., Rotate 90 degrees)
# In Tropical context, this would be costs. Let's use standard matrix mul for rotation.
# Wait, MatrixSemiring above is Min-Plus. Let's define a Standard Matrix Semiring for Rotation.

class StandardMatrixSemiring(MatrixSemiring):
    @property
    def zero(self): return np.zeros((self.dim, self.dim))

    def add(self, a, b): return a + b

    def mul(self, a, b): return a @ b


sms = StandardMatrixSemiring(2)
rot90 = np.array([[0, -1], [1, 0]])
rot180 = sms.mul(rot90, rot90)

print("Rotation 180:\n", rot180)
# [[-1, 0], [0, -1]]
```

## Physics & Signal Processing

Using algebraic concepts to analyze graph stability and flow.

### Graph Reynolds Number

A metric derived from Fluid Dynamics (Rayleigh-Plesset) to predict "Turbulence" (Congestion) in a network.
$Re_G = \frac{\text{Momentum}}{\text{Viscosity}} = \frac{\text{Total Flow}}{\text{Algebraic Connectivity}}$

!!! note "Dependency"
This example requires `networkx` and `numpy`.

<!-- name: test_graph_reynolds -->

```python linenums="1"
import networkx as nx
import numpy as np


def calculate_graph_reynolds(G: nx.Graph, flow_dict: dict) -> float:
    """
    Calculates the 'Rivlis-Plesset Number' (Rp) for a network.
    """
    # 1. Momentum (Total Flow)
    total_flow = sum(flow_dict.values())
    if total_flow == 0: return 0.0

    # 2. Viscosity (Algebraic Connectivity / Fiedler Value)
    # High connectivity = Low drag (fluid moves easily).
    try:
        # weight='capacity' if edges have capacity
        viscosity = nx.algebraic_connectivity(G)
    except:
        viscosity = 0.001  # Disconnected graph

    # 3. Reynolds Calculation
    return total_flow / (viscosity + 1e-9)


def analyze_stability(rp: float) -> str:
    if rp < 1000:
        return "Laminar Flow (Stable)"
    elif 1000 <= rp < 2000:
        return "Transitional (Wobbling)"
    else:
        return "Turbulent (Cavitation Imminent!)"


# Simulation
G = nx.grid_2d_graph(5, 5)
flow_laminar = {e: 0.1 for e in G.edges()}
flow_turbulent = {e: 5000.0 for e in G.edges()}

rp_lam = calculate_graph_reynolds(G, flow_laminar)
rp_turb = calculate_graph_reynolds(G, flow_turbulent)

print(f"Scenario A: {analyze_stability(rp_lam)}")
print(f"Scenario B: {analyze_stability(rp_turb)}")
```

### Fenchel-Legendre Transform (Tropical Fourier)

The "Fourier Transform" for the Min-Plus semiring. It analyzes the "slope content" of a signal.

<!-- name: test_fenchel_transform -->

```python linenums="1"
from algebrax.analysis import fenchel_legendre_transform

# A convex signal (like a potential well)
signal = {0: 0, 1: 1, 2: 4, 3: 9}  # f(x) = x^2

# Analyze slope at s=2
# f*(s) = sup(s*x - f(x))
# at s=2: max(2*0-0, 2*1-1, 2*2-4, 2*3-9) = max(0, 1, 0, -3) = 1
val = fenchel_legendre_transform(signal, slope=2)
print(f"Convex Conjugate at slope 2: {val}")
```
