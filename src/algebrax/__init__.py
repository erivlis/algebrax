"""
Summary: Pure-Python polymorphic semiring algebra and tensor algorithms for sparse dictionary mappings.

`algebrax` treats Python's native `dict` (and `Mapping`) as a first-class mathematical object,
unifying linear algebra, graph theory, signal processing, formal language theory, and discrete geometry.

Quickstart
----------

>>> import algebrax as ax
>>> graph = {0: {1: 2.0, 2: 10.0}, 1: {2: 3.0}}
>>> shortest_paths = ax.matrix.dot(graph, graph, semiring=ax.semiring.TropicalSemiring())
>>> shortest_paths[0][2]
5.0

Submodules & Domain Taxonomy
----------------------------

1. Core Foundations & Data Structures
   - `matrix`: Core linear algebra (`add`, `dot`, `power`, `transpose`) & academic invariants (`determinant`).
   - `matrix.decompose`: Matrix factorizations (`lu`, `qr`, `svd`, `cholesky`).
   - `semiring`: 24 polymorphic semirings (Arithmetic, Optimization, Logic, Statistical, Algebraic).
   - `tensor`: Sparse multidimensional tensor contractions (`einsum`, `permute_tensor`).
   - `trie`: `AlgebraicTrie` tensor prefix trees over semirings.

2. Discrete Geometry, Topology & Fields
   - `homology`: Simplicial complexes, boundary operators, and Betti numbers (`SimplicialComplex`, `betti_numbers`).
   - `clifford`: Clifford Geometric Algebra Cl(p,q,r) multivectors & 3D rotors (`rotor_rotation`).
   - `galois`: Finite field matrix arithmetic GF(p^m) (`GaloisFieldSemiring`, `gf_matrix_mul`).
   - `category`: Category theory & monadic Kleisli composition (`kleisli_compose`).

3. Signal Processing, Dynamics & Logic
   - `transforms`: Signal processing (`dft`, `idft`, `convolve`, `walsh_hadamard`, `z_transform`).
   - `analysis`: Vector calculus on graphs (`gradient`, `divergence`, `laplacian`, `forman_ricci_curvature`).
   - `probability`: Information theory & Markov chains (`entropy`, `kl_divergence`, `bayes_update`).
   - `automata`: Finite state machines (`simulate_dfa`, `simulate_nfa`).
   - `lattice`: Set-theoretic & fuzzy logic key/value operations (`join`, `meet`, `combine`).
   - `group`: Permutation groups & Artin braid crossings (`compose`, `signature`).

4. Tools & Ecosystem Bridges
   - `converters`: Sparse-dense array conversion & PyData bridges (`to_numpy`, `from_numpy`, `to_scipy`).
   - `display`: Rich Jupyter HTML rendering (`display_matrix`, `display_vector`, `display_trie`).
   - `verification`: Algebraic law verification engine (`verify_semiring_laws`).
   - `metrics`: Density, sparsity, and fractal dimension estimators (`box_counting_dimension`).
   - `typing`: Standard generic type aliases (`SparseMatrix[K, V]`, `SparseVector[K, V]`).
"""

from algebrax import (
    analysis,
    automata,
    category,
    clifford,
    converters,
    display,
    galois,
    group,
    homology,
    lattice,
    matrix,
    metrics,
    probability,
    semiring,
    tensor,
    transforms,
    trie,
    typing,
    verification,
)
from algebrax.typing import (
    DenseMatrix,
    DenseVector,
    SparseMatrix,
    SparseTensor,
    SparseVector,
)

__all__ = [
    'DenseMatrix',
    'DenseVector',
    'SparseMatrix',
    'SparseTensor',
    'SparseVector',
    'analysis',
    'automata',
    'category',
    'clifford',
    'converters',
    'display',
    'galois',
    'group',
    'homology',
    'lattice',
    'matrix',
    'metrics',
    'probability',
    'semiring',
    'tensor',
    'transforms',
    'trie',
    'typing',
    'verification',
]
