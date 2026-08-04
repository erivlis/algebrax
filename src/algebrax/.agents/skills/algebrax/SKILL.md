---
name: algebrax
description: >
  Perform mathematical operations on sparse and symbolic data using Python dictionaries. Use for tasks involving graph theory (curvature, laplacian), linear algebra (dot product, decompositions, transpose) with non-integer keys, or probabilistic modeling (Bayesian updates, entropy). This skill is ideal when working with adjacency matrices, word vectors, or other dictionary-based data structures, even if the user doesn't explicitly use the term 'sparse'.
---

# Using the algebrax Library

## Core Concept: Sparse, Symbolic Math on Dictionaries

`algebrax` performs mathematical operations directly on native Python dictionaries, treating them as sparse vectors or matrices. This is ideal for symbolic data where keys are strings, tuples, or other hashable objects, not just contiguous integer indices.

**DO NOT** convert sparse data to dense lists or numpy arrays unless explicitly requested. The library is designed to work directly with `dict` objects.

## Top-Level Idiomatic Import

Import `algebrax` using qualified submodule namespaces:

```python
import algebrax as ax

# Matrix multiplication over Tropical semiring
res = ax.matrix.dot(A, B, semiring=ax.semiring.TropicalSemiring())

# Simplicial homology Betti numbers
betti = ax.homology.betti_numbers(complex)
```

## Key Operations & Submodules

### 1. Linear Algebra (`algebrax.matrix`)

Use `dot` for matrix and vector multiplication. It supports custom `Semiring` objects for different algebraic structures.

```python
import algebrax as ax

# Standard dot product
v1 = {'a': 1, 'b': 2}
v2 = {'b': 3, 'c': 4}
result = ax.matrix.dot(v1, v2)  # -> 6

# Shortest-path multiplication using the Tropical Semiring
m1 = {0: {1: 2}, 1: {2: 3}}
m2 = {1: {2: 1}, 2: {0: 4}}
path_result = ax.matrix.dot(m1, m2, semiring=ax.semiring.TropicalSemiring)  # -> {0: {2: 3}}
```

### 2. Matrix Decompositions (`algebrax.matrix.decompose`)

Factorize sparse matrices with partial pivoting and QR/SVD/Cholesky algorithms:

```python
import algebrax as ax

A = {0: {0: 4.0, 1: 12.0}, 1: {0: 12.0, 1: 37.0}}

# LU, QR, SVD, Cholesky factorizations
p, l, u = ax.matrix.decompose.lu(A)
q, r = ax.matrix.decompose.qr(A)
u_svd, s, v_t = ax.matrix.decompose.svd(A)
l_chol = ax.matrix.decompose.cholesky(A)

# Recompose factorizations back to original matrix
assert ax.matrix.decompose.recompose_cholesky(l_chol) == A
```

### 3. Graph Analysis & Vector Calculus (`algebrax.analysis`)

Directly compute graph properties from adjacency matrices:

```python
import algebrax as ax

graph = {'A': {'B': 1, 'C': 1}, 'B': {'A': 1}, 'C': {'A': 1}}

# Get the graph Laplacian & Forman-Ricci edge curvature
laplacian_matrix = ax.analysis.laplacian(graph)
curvature = ax.analysis.forman_ricci_curvature(graph)

# Calculate eigenvector centrality
centrality_scores = ax.matrix.academic.eigen_centrality(graph)
```

### 4. Probability (`algebrax.probability`)

Work with probability distributions represented as dictionaries:

```python
import algebrax as ax

prior = {'sunny': 0.6, 'rainy': 0.4}
likelihood = {'sunny': 0.1, 'rainy': 0.8}  # P(cloudy | weather)

# Get the posterior probability of weather given clouds
posterior = ax.probability.bayes_update(prior, likelihood)
normalized_posterior = ax.probability.normalize(posterior)  # -> {'sunny': 0.157..., 'rainy': 0.842...}

# Calculate entropy
h = ax.probability.entropy(normalized_posterior)
```

### 5. Ecosystem Interop (`algebrax.converters`)

Convert between sparse `dict` matrices and PyData structures (NumPy / SciPy) with soft-dependency helpers:

```python
import algebrax as ax

m = {0: {0: 1.0, 2: 5.0}, 1: {1: 3.0}}

# Convert to/from NumPy ndarray
arr = ax.converters.to_numpy(m)
m_back = ax.converters.from_numpy(arr)

# Convert to/from SciPy sparse matrix
sp_mat = ax.converters.to_scipy(m, format='csr')
m_scipy_back = ax.converters.from_scipy(sp_mat)
```

### 6. Jupyter Notebook Rich Display (`algebrax.display`)

Format sparse matrices, vectors, and tries as HTML tables for Jupyter Notebook inspection:

```python
from algebrax.display import display_matrix, display_vector, display_trie

html_table = display_matrix(matrix, title="Adjacency Matrix")
```

## Advanced Semiring Usage

The power of `algebrax` comes from its flexible `Semiring` system. By changing the semiring, you solve completely different domain problems with the exact same `dot` operation.

### Provenance Semiring (History & Path Tracking)

Tracks *which* elements contributed to a result:

```python
import algebrax as ax

# Graph with labeled edges
graph = {0: {1: {('x',): 1}, 2: {('z',): 1}}, 1: {2: {('y',): 1}}}

# Find paths of length 2
paths_len_2 = ax.matrix.dot(graph, graph, semiring=ax.semiring.ProvenanceSemiring())
# paths_len_2[0][2] will be {('x', 'y'): 1}, showing path 0 -> 1 -> 2
```

## Algebraic Trie

The `AlgebraicTrie` is a sparse tensor that supports semiring operations and subtree contractions:

```python
from algebrax.trie import AlgebraicTrie
from algebrax.semiring import StandardSemiring

trie = AlgebraicTrie(StandardSemiring)
trie.add(['home', 'user', 'docs'], 1)
trie.add(['home', 'user', 'pics'], 1)

# Sum all paths under "home/user"
count = trie.contract(['home', 'user'])  # -> 2.0
```

## Theoretical Concepts

For deep mathematical background (e.g., "What is a semiring?", "How does Discrete Exterior Calculus relate to graphs?"), read the [`references/concepts.md`](file:///C:/dev/erivlis/algebrax/src/algebrax/.agents/skills/algebrax/references/concepts.md) file.

## Gotchas & Guidelines

- **Implicit Zeros**: Keys not present in a dictionary are treated as the additive identity (usually zero).
- **Symbolic Keys Matter**: Operations match by dictionary key identity, not contiguous memory position.
- **Key Collisions**: `flat_to_nested` raises `ValueError` if a key is used both as a leaf value and a branch container.
- **Performance**: `algebrax` is fastest for sparse data (density < 50%).