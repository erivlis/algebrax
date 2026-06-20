---
name: algebrax
description: >
  Perform mathematical operations on sparse and symbolic data using Python dictionaries. Use for tasks involving graph theory (centrality, laplacian), linear algebra (dot product, transpose) with non-integer keys, or probabilistic modeling (Bayesian updates, entropy). This skill is ideal when working with adjacency matrices, word vectors, or other dictionary-based data structures, even if the user doesn't explicitly use the term 'sparse'.
---

# Using the algebrax Library

## Core Concept: Sparse, Symbolic Math on Dictionaries

`algebrax` performs mathematical operations directly on Python dictionaries, treating them as sparse vectors or matrices. This is ideal for symbolic data where keys are strings or other hashable objects, not just integer indices.

**DO NOT** convert sparse data to dense lists or numpy arrays. The library is designed to work with `dict` objects.

## Key Operations

### Linear Algebra (`algebrax.matrix`)

Use `dot` for matrix and vector multiplication. It supports custom `Semiring` objects for different algebraic structures.

```python
from algebrax.matrix import dot
from algebrax.semiring import StandardSemiring, TropicalSemiring

# Standard dot product
v1 = {'a': 1, 'b': 2}
v2 = {'b': 3, 'c': 4}
result = dot(v1, v2)  # -> 6

# Shortest-path-style multiplication using the Tropical Semiring
m1 = {0: {1: 2}, 1: {2: 3}}
m2 = {1: {2: 1}, 2: {0: 4}}
path_result = dot(m1, m2, semiring=TropicalSemiring) # -> {0: {2: 3}}
```

### Graph Analysis (`algebrax.analysis`)

Directly compute graph properties from adjacency matrices (represented as nested dicts).

```python
from algebrax.analysis import laplacian, eigen_centrality

graph = {'A': {'B': 1, 'C': 1}, 'B': {'A': 1}, 'C': {'A': 1}}

# Get the graph Laplacian
laplacian_matrix = laplacian(graph)

# Calculate eigenvector centrality
centrality_scores = eigen_centrality(graph)
```

### Probability (`algebrax.probability`)

Work with probability distributions represented as dictionaries.

```python
from algebrax.probability import normalize, bayes_update, entropy

prior = {'sunny': 0.6, 'rainy': 0.4}
likelihood = {'sunny': 0.1, 'rainy': 0.8} # P(cloudy | weather)

# Get the posterior probability of weather given clouds
posterior = bayes_update(prior, likelihood)
normalized_posterior = normalize(posterior) # -> {'sunny': 0.157..., 'rainy': 0.842...}

# Calculate entropy
h = entropy(normalized_posterior) # -> 0.63...
```

## Advanced Semiring Usage

The power of `algebrax` comes from its flexible `Semiring` system. By changing the semiring, you can solve different problems with the same `dot` operation.

### Provenance Semiring (History Tracking)

Tracks *which* elements contributed to a result.

```python
from algebrax.semiring import ProvenanceSemiring
from algebrax.matrix import dot

# Graph with labeled edges
graph = {
    0: {1: {('x',): 1}, 2: {('z',): 1}},
    1: {2: {('y',): 1}}
}

# Find paths of length 2
paths_len_2 = dot(graph, graph, semiring=ProvenanceSemiring())
# paths_len_2[0][2] will be {('x', 'y'): 1}, showing the path 0->1->2
```

## Algebraic Trie

The `AlgebraicTrie` is a sparse tensor that supports semiring operations.

```python
from algebrax.trie import AlgebraicTrie
from algebrax.semiring import StandardSemiring

trie = AlgebraicTrie(StandardSemiring)
trie.add(["home", "user", "docs"], 1)
trie.add(["home", "user", "pics"], 1)

# Sum all paths under "home/user"
count = trie.contract(["home", "user"]) # -> 2.0
```

## Theoretical Concepts

If you need to understand the underlying mathematical theory (e.g., "What is a semiring?", "How does Discrete Exterior Calculus relate to graphs?"), read the `references/concepts.md` file. This file contains detailed explanations of the algebraic structures and their applications in the library.

## Gotchas & Performance

- **Implicit Zeros**: Keys not present in a dictionary are treated as the additive identity (usually zero).
- **Symbolic Keys Matter**: Operations are based on key matching, not position.
- **Semiring Choice is Crucial**: The `dot` product's behavior changes completely based on the `semiring`.
- **Performance**: `algebrax` is fastest for sparse data (density < 50%). For dense data, `numpy` is generally faster.

## Practical Example: Item-Item Similarity

This example builds a simple recommendation engine by calculating item-item similarity from user ratings.

```python
from algebrax.matrix import dot, transpose
from algebrax.probability import normalize

# User ratings (users as rows, movies as columns)
ratings = {
    'user1': {'Matrix': 5, 'Inception': 4, 'Titanic': 1},
    'user2': {'Matrix': 4, 'Inception': 5, 'Interstellar': 4},
    'user3': {'Titanic': 5, 'Interstellar': 2, 'Inception': 2},
}

# Transpose to get movies as rows
movie_ratings = transpose(ratings)

# Compute similarity matrix
similarity_matrix = dot(movie_ratings, movie_ratings)

# Get recommendations for a user who likes "The Matrix"
recommendations = similarity_matrix.get('Matrix', {})

# Normalize to get ranked scores
ranked_recommendations = normalize(recommendations)
```