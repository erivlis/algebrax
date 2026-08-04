"""
The `algebrax` namespace provides a comprehensive suite of mathematical operations
optimized for sparse, dictionary-based data structures.

It treats Python's native `dict` (and `Mapping`) as a first-class mathematical object,
enabling Linear Algebra, Set Theory, Graph Theory, and Probability operations directly on
sparse data without conversion to dense arrays.

Comparison with Other Libraries
-------------------------------

1. **`scipy.sparse`**:
   - **Domain**: Numerical Linear Algebra.
   - **Pros**: Industry standard, extremely fast (C/Fortran backend).
   - **Cons**: Keys must be integers; requires conversion from dicts; heavy dependency.
   - **Use Case**: Large-scale numerical simulations (e.g., Finite Element Method).

2. **`numpy`**:
   - **Domain**: Dense Numerical Arrays.
   - **Pros**: Universal standard for dense data.
   - **Cons**: Inefficient for sparse data (O(N^2) memory); integer indices only.
   - **Use Case**: Image processing, dense tensors.

3. **`pandas`**:
   - **Domain**: Tabular Data Analysis.
   - **Pros**: Excellent for time-series and labeled data.
   - **Cons**: Not optimized for general mathematical algebrax (e.g., matrix multiplication).
   - **Use Case**: Data cleaning, ETL, statistical analysis.

4. **`algebrax` (This Library)**:
   - **Domain**: Symbolic/Sparse Algebra on Mappings.
   - **Pros**:
     - **Symbolic Keys**: Works with `str`, `tuple`, or any hashable object (e.g., graphs with string nodes).
     - **Zero-Dependency**: Pure Python.
     - **Functional**: Composable API (`combine`, `compose`).
   - **Cons**: Slower than C-based libraries for massive numerical computations.
   - **Use Case**: NLP (word vectors), Knowledge Graphs, Item-Item similarity, small-to-medium sparse matrices.

Definitions & Criteria
----------------------

*   **Sparse**: Data where the number of non-zero elements ($k$) is significantly smaller than the total capacity ($N$).
    *   *Criterion*: Density ($k/N$) < 0.05 (5%).
*   **Dense**: Data where most elements are non-zero.
    *   *Criterion*: Density > 0.5 (50%).
*   **Lightweight**: Minimal memory overhead and startup time.
    *   *Criterion*: Import time < 10ms; Memory overhead < 1KB per object (beyond data).
*   **Symbolic**: Keys represent semantic entities (e.g., "User_123", "Product_X") rather than contiguous memory
    offsets (0, 1, 2).

Modules
-------

*   **`matrix`**: Linear Algebra (Core & Academic).
*   **`lattice`**: Set/Fuzzy Logic (Union, Intersection).
*   **`analysis`**: Vector Calculus on Graphs (Gradient, Laplacian).
*   **`probability`**: Bayesian/Markov Inference.
*   **`transforms`**: Signal Processing (DFT, Convolution).
*   **`automata`**: Finite State Machines.
*   **`group`**: Permutations.
*   **`metrics`**: Metrics and checks.
*   **`semiring`**: Generalized algebrax (Tropical, Boolean, String).
*   **`trie`**: Algebraic Tries (Sparse Tensors).
*   **`typing`**: Type aliases for sparse/dense structures.
*   **`homology`**: Simplicial Complexes & Betti Numbers.
*   **`clifford`**: Clifford Geometric Algebra & Rotor Rotations.
*   **`galois`**: Galois Finite Field Arithmetic.
*   **`category`**: Categorical Morphisms & Kleisli Composition.
*   **`verification`**: Algebraic Law Verification Engine.
*   **`decompose`**: Matrix Decompositions (LU, QR, SVD, Cholesky).
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
    verification,
)
from algebrax.analysis import (
    divergence,
    forman_ricci_curvature,
    gaussian_kernel,
    gradient,
    laplacian,
)
from algebrax.automata import (
    dfa_step,
    nfa_step,
    simulate_dfa,
    simulate_nfa,
)
from algebrax.category import kan_extension_left, kleisli_compose
from algebrax.clifford import geometric_product, rotor_rotation
from algebrax.converters import (
    dense_to_sparse_matrix,
    dense_to_sparse_tensor,
    dense_to_sparse_vector,
    flat_to_nested,
    from_numpy,
    from_scipy,
    get_matrix_keys,
    grid_to_sparse,
    nested_to_flat,
    prune_sparse,
    sample,
    sample_tensor,
    sparse_to_dense_matrix,
    sparse_to_dense_tensor,
    sparse_to_dense_vector,
    sparse_to_grid,
    to_numpy,
    to_scipy,
)
from algebrax.galois import gf_matrix_mul
from algebrax.group import compose, invert, signature
from algebrax.homology import SimplicialComplex, SparseChainComplex, coboundary, cohomology_rank
from algebrax.lattice import (
    average,
    combine,
    difference,
    exclude,
    exclusive,
    geometric_mean,
    harmonic_mean,
    join,
    mask,
    meet,
    product,
    ratio,
    symmetric_difference,
)
from algebrax.matrix import (
    add,
    adjoint,
    cholesky,
    cofactor,
    determinant,
    dot,
    eigen_centrality,
    inner,
    inverse,
    kronecker_delta,
    lu,
    mat_vec,
    power,
    qr,
    recompose_cholesky,
    recompose_lu,
    recompose_qr,
    recompose_svd,
    svd,
    trace,
    transpose,
    vec_mat,
)
from algebrax.metrics import (
    box_counting_dimension,
    count_elements,
    deepness,
    density,
    is_sparse,
    sparsity,
    uniformness,
    wideness,
)
from algebrax.probability import (
    bayes_update,
    cross_entropy,
    entropy,
    expected_value,
    kl_divergence,
    kurtosis,
    marginalize,
    markov_steady_state,
    markov_step,
    mode,
    mutual_information,
    normalize,
    skewness,
    variance,
)
from algebrax.semiring import (
    ArcticSemiring,
    BooleanSemiring,
    BottleneckSemiring,
    DigitalSemiring,
    DualNumberSemiring,
    ExpectationSemiring,
    KCollapsedSemiring,
    KnotSemiring,
    LogSemiring,
    LukasiewiczSemiring,
    MinTimesSemiring,
    ModularSemiring,
    MonoidAlgebraSemiring,
    PolynomialSemiring,
    ProvenanceSemiring,
    QuotientMonoidAlgebraSemiring,
    ReliabilitySemiring,
    Semiring,
    StandardSemiring,
    StringSemiring,
    TropicalSemiring,
    VarianceSemiring,
    ViterbiSemiring,
)
from algebrax.tensor import (
    einsum,
    flatten_tensor,
    outer_product,
    permute_tensor,
    tensordot,
    unflatten_tensor,
    unpermute_tensor,
)
from algebrax.transforms import (
    convolve,
    deconvolve,
    dft,
    gelfand_transform,
    hilbert,
    idft,
    iwalsh_hadamard,
    iz_transform,
    legendre_fenchel,
    lorentz_boost,
    walsh_hadamard,
    z_transform,
)
from algebrax.trie import AlgebraicTrie
from algebrax.typing import (
    DenseMatrix,
    DenseVector,
    SparseMatrix,
    SparseTensor,
    SparseVector,
)
from algebrax.verification import (
    get_semiring_samples,
    semiring_elements_equal,
    verify_semiring_laws,
)

__all__ = [
    'AlgebraicTrie',
    'ArcticSemiring',
    'BooleanSemiring',
    'BottleneckSemiring',
    'CliffordSemiring',
    'DenseMatrix',
    'DenseVector',
    'DigitalSemiring',
    'DualNumberSemiring',
    'ExpectationSemiring',
    'GaloisFieldSemiring',
    'KCollapsedSemiring',
    'KnotSemiring',
    'LogSemiring',
    'LukasiewiczSemiring',
    'MinTimesSemiring',
    'ModularSemiring',
    'MonoidAlgebraSemiring',
    'PolynomialSemiring',
    'ProvenanceSemiring',
    'QuotientMonoidAlgebraSemiring',
    'ReliabilitySemiring',
    'Semiring',
    'SimplicialComplex',
    'SparseChainComplex',
    'SparseMatrix',
    'SparseTensor',
    'SparseVector',
    'StandardSemiring',
    'StringSemiring',
    'TropicalSemiring',
    'VarianceSemiring',
    'ViterbiSemiring',
    'add',
    'adjoint',
    'analysis',
    'automata',
    'average',
    'bayes_update',
    'box_counting_dimension',
    'category',
    'cholesky',
    'clifford',
    'coboundary',
    'cofactor',
    'cohomology_rank',
    'combine',
    'compose',
    'converters',
    'convolve',
    'count_elements',
    'cross_entropy',
    'deconvolve',
    'deepness',
    'dense_to_sparse_matrix',
    'dense_to_sparse_tensor',
    'dense_to_sparse_vector',
    'density',
    'determinant',
    'dfa_step',
    'dft',
    'difference',
    'display',
    'divergence',
    'dot',
    'eigen_centrality',
    'einsum',
    'entropy',
    'exclude',
    'exclusive',
    'expected_value',
    'flat_to_nested',
    'forman_ricci_curvature',
    'from_numpy',
    'from_scipy',
    'galois',
    'gaussian_kernel',
    'gelfand_transform',
    'geometric_mean',
    'geometric_product',
    'get_matrix_keys',
    'get_semiring_samples',
    'gf_matrix_mul',
    'gradient',
    'grid_to_sparse',
    'group',
    'harmonic_mean',
    'hilbert',
    'homology',
    'idft',
    'inner',
    'inverse',
    'invert',
    'is_sparse',
    'iwalsh_hadamard',
    'iz_transform',
    'join',
    'kan_extension_left',
    'kl_divergence',
    'kleisli_compose',
    'kronecker_delta',
    'kurtosis',
    'laplacian',
    'lattice',
    'legendre_fenchel',
    'lorentz_boost',
    'lu',
    'marginalize',
    'markov_steady_state',
    'markov_step',
    'mask',
    'mat_vec',
    'matrix',
    'meet',
    'metrics',
    'mode',
    'mutual_information',
    'nested_to_flat',
    'nfa_step',
    'normalize',
    'outer_product',
    'permute_tensor',
    'power',
    'probability',
    'product',
    'prune_sparse',
    'qr',
    'ratio',
    'recompose_cholesky',
    'recompose_lu',
    'recompose_qr',
    'recompose_svd',
    'rotor_rotation',
    'sample',
    'sample_tensor',
    'semiring',
    'semiring_elements_equal',
    'signature',
    'simulate_dfa',
    'simulate_nfa',
    'skewness',
    'sparse_to_dense_matrix',
    'sparse_to_dense_tensor',
    'sparse_to_dense_vector',
    'sparse_to_grid',
    'sparsity',
    'svd',
    'symmetric_difference',
    'tensor',
    'tensordot',
    'to_numpy',
    'to_scipy',
    'trace',
    'transforms',
    'transpose',
    'trie',
    'unflatten_tensor',
    'uniformness',
    'unpermute_tensor',
    'variance',
    'vec_mat',
    'verification',
    'verify_semiring_laws',
    'walsh_hadamard',
    'wideness',
    'z_transform',
]
