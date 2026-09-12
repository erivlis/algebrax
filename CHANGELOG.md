## v0.9.0 (2026-09-13)

### Feat

- **lie**: Adds Mermaid and SVG rendering for Dynkin diagrams.
- **matrix.core**: Adds Frobenius inner product and matrix inverse.
- **EP-0163**: add Lie algebra module with structure constants and operations
- add element-wise binary operations and commutator function for sparse matrices

### Fix

- **tensor**: remove keys from output trie when value is zero
- **algebraic**: improve error handling for generator index exceeding dimensions
- **docs/proposals**: simplify `_SIG_RE` regex for algebraic signature parsing
- **display**: simplify `_SIG_RE` regex for signature parsing

### Refactor

- **lie**: Splits into core, classical, exceptional, and roots modules.
- **styleguide**: enhance clarity and structure of mathematical classes documentation
- **display**: limit displayed items to a maximum of 50 and skip paths exceeding max depth
- **academic, probability**: enhance comments for cofactor and determinant functions, clarify transition update step
- **academic, probability**: enhance comments for cofactor and determinant functions, clarify transition update step
- **probability**: clarify transition update step comment for better understanding
- **converters**: simplify maximum column calculation with default parameter
- **transforms**: standardize variable naming in sample processing loop for consistency
- **eigenvalue**: replace manual Jacobi eigenvalue computation with modular function for improved readability
- **decompose**: modularize SVD and Jacobi eigenvalue decomposition logic for clarity
- **statistical**: simplify calculations by removing commented-out code
- **transforms**: modularize Legendre-Fenchel transform logic for clarity and reuse
- **core**: modularize Laplacian construction into specialized functions
- **verification**: modularize semiring law checks for clarity and reuse
- **core**: expose `__version__` attribute and enhance version resolution logic
- **recipes**: Modularize `spectral_graph_clustering` with reusable functions
- **analysis**: Move `eigen_centrality` from `matrix.academic` to `analysis`

### Perf

- **lie**: Adds benchmarks for Lie algebra and root systems.

## v0.8.0 (2026-09-06)

### Feat

- **analysis**: Add Laplacian matrix, spectral theory, and Fiedler vector utilities
- **analysis**: Add algebraic PageRank implementation over semirings
- **cli**: Introduce AlgebraX CLI for semiring inspection, verification, and matrix operations
- **display**: Add `semiring_card` for Jupyter rich HTML rendering

### Refactor

- **semiring**: Replace `_normalize_semiring` with `Semiring.normalize` and add canonical `default` method
- **recipes**: Replace custom PageRank logic with `ax.analysis.pagerank`
- **recipes**: Add semiring card previews and Jupyter compatibility checks

## v0.7.0 (2026-09-04)

### Feat

- **semiring**: Add new algebraic and statistical semirings with expanded catalog support
- **verification**: Add support for complex number comparison and expand semiring catalog

### Fix

- Exposes core type aliases directly from the `algebrax` package.
- Exposes core type aliases directly from the `algebrax` package.

### Refactor

- **recipes**: Modularize and enhance examples for cryptography, homology, and topology
- **recipes/lab.py**: Add `BivariateVarianceSemiring` and refine variance handling
- **financial_risk_portfolio**: Simplify variance computation using `VarianceSemiring` methods
- **semiring**: Implements EP-0149 Optimize performance with dimension caching and replace `SecondMoment`

## v0.6.1 (2026-08-07)

### Refactor

- **matrix**: Refines dot product logic for improved sparsity.
- **api**: Standardizes module access via `ax` alias and renames `tensordot` to `dot`.
- **EP-0146**: Completes EP-0146 ergonomics
- **EP-0145**: Completes type safety and contract hardening.

## v0.6.0 (2026-08-05)

### Feat

- **EP-0140**: Adds inverse transforms and decomposition recomposition.
- **EP-0132**: Implements sparse matrix LU, QR, SVD, Cholesky decompositions.
- **EP-0131**: Adds ModularSemiring and algebraic law verification engine.

### Refactor

- **EP-0141**: Completes taxonomy cleanup and module relocations.
- Refines SparseMatrix type hints in Kleisli composition.
- **EP-0134**: Refactors monolithic semiring module into categorized namespace.

### Perf

- **EP-0142**: Completes performance and efficiency optimizations.

## v0.5.0 (2026-08-02)

### Feat

- **EP-0113**: Adds Kleisli monadic composition for categorical morphisms.
- **EP-0112**: Adds Galois finite fields for cryptographic arithmetic.
- **EP-0111**: Adds Clifford Geometric Algebra and rotor rotations.
- **EP-0110**: Adds Simplicial Homology and Betti number computation.
- **EP-0101**: Adds SparseChainComplex for algebraic topology.
- **EP-0100**: Adds Quotient Monoid Algebra Semiring.

### Refactor

- Renames `reciepes` directory to `recipes`.
- Refactors lab recipes for algebrax API updates and UI enhancements.
- Refactors DearPyGui lab with helpers and clearer recipe logic.

## v0.4.0 (2026-07-31)

### Feat

- Adds tensor algebra module with einsum, outer product, and tensordot.

### Refactor

- Refactors DearPyGui lab with helpers and clearer recipe logic.

## v0.3.1 (2026-07-27)

### Refactor

- Corrects float comparison for weighted graph detection.

## v0.3.0 (2026-07-26)

### Feat

- Introduces MonoidAlgebraSemiring and generalizes StandardSemiring.

### Refactor

- Exposes MonoidAlgebraSemiring and other semirings for convolve.
- Refactors `convolve` to use `MonoidAlgebraSemiring`.
- Standardizes code style, simplifies Z-transform types, adds re-export test.

## v0.2.1 (2026-07-25)

### Refactor

- Update import paths for density and fenchel_legendre_transform; improve consistency in module naming
- Rename test files for consistency and clarity; remove unused tests
- Renames sparsity.py to metrics.py and updates related references; improves documentation and consistency in algebrax terminology.

## v0.2.0 (2026-06-20)

### Feat

- Enhance Fenchel-Legendre transform to support multiple semirings
- Replaces Ollivier-Ricci with Forman-Ricci graph curvature.

### Fix

- Uses math.isclose for robust float comparison in graph weight check.

### Refactor

- **test_anlysis**: Improves analysis test precision using pytest.approx assertions.

## v0.1.1 (2026-04-09)

### Refactor

- update Semiring protocol to use TypeVar for improved type flexibility
- update semiring classes to use instance methods instead of static methods
