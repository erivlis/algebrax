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
