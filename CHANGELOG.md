## v0.4.0 (2026-07-31)

### Feat

- Adds tensor algebra module with einsum, outer product, and tensordot.

### Refactor

- Refactors DearPyGui lab with helpers and clearer recipe logic.
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
