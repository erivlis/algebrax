## v0.14.1 (2026-11-14)

### Refactor

- extract boundary column reduction logic into a dedicated function
- modularize LU decomposition logic by extracting field-specific handling into dedicated functions
- modularize Cartan matrix logic by extracting exceptional and classical family handling into dedicated functions
- modularize E6 to F4 projection logic by extracting cocycle sign computation and bracket population into dedicated functions
- modularize matrix operations by extracting Gram matrix inversion, commutator projection, and adjoint block construction into dedicated functions
- encapsulate scalar action law verification in a dedicated function
- extract Frobenius inner product logic into a separate function for clarity
- extract partitioning and merging logic for 2x2 sparse matrix blocks

## v0.14.0 (2026-11-13)

### Feat

- add Action Algebra and related operations for matrix closures
- **topology**: implement SimplicialChainCoalgebra with Alexander-Whitney coproduct
- **algebra**: add Coalgebra, Bialgebra, and Hopf Algebra implementations with associated mixins and verification functions
- **analysis**: implement EP-0205 normed spaces, Hilbert spaces, RKHS, and Banach contractions
- enhance algebra classes with new law mixins and type safety checks
- decouple semiring foundations into pure rigs, star semirings, and Kleene algebras with updated protocols and verification methods
- add new non-associative algebra classes and update documentation for Jordan, Alternative, Malcev, and Poisson algebras
- add non-associative algebra classes and verification functions for Jordan, Alternative, Malcev, and Poisson algebras
- add DiscreteConnection and DiscreteOrthogonalConnection classes for discrete fiber bundles
- introduce CellPosetCategory and related classes for cellular sheaf structures

### Fix

- implement __subclasshook__ for Semiring to enforce structural protocol attributes

### Refactor

- improve output formatting in run_demonstration function

## v0.13.0 (2026-11-12)

### Feat

- enhance algebra module by adding homomorphism and ideal protocols
- restructure category module and introduce core protocols for category theory

## v0.12.0 (2026-11-08)

### Feat

- **algebra**: introduce mixin protocols for algebraic operations and update existing classes
- add rings and fields guide to the zensical configuration
- update status of EP-0191 to final
- add verification laws for non-associative rings, division rings, fields, modules, and algebras
- introduce Field, Module, and Algebra protocols with implementations for standard and modular fields
- Add algebraic hierarchy protocols and helper functions for groups, lattices, and magmas
- **Homology**: Add PersistenceInterval and FilteredSimplicialComplex classes with associated methods for topological data analysis

### Refactor

- reorganize imports across multiple test files for clarity
- clean up imports in analysis.py by removing duplicates
- remove Base Semiring protocol and related imports
- update references from CliffordSemiring to CliffordAlgebra and adjust imports
- remove canonical aliases for algebraic structures to streamline imports
- **algebra**: add DualNumber and Polynomial algebra classes; update imports

## v0.11.3 (2026-10-25)

### Fix

- Update power method to return 0.0 for zero exponent
- **converters**: Adjust array initialization to handle complex numbers in matrix
- **roots**: Correct d_factors assignment for Dynkin types B, C, and F
- **analysis**: Adjust max_sweeps parameter in symmetric Jacobi eigenvalue computation for improved performance

## v0.11.1 (2026-10-24)

### Refactor

- Removes unused add method from GF(p) implementation
- Removes unused multiplication method from ProvenanceSemiring
- Simplifies power method implementations across multiple classes
- Refactors restriction normalization by extracting row logic.

## v0.11.0 (2026-10-17)

### Feat

- **EP-0161**: Implements CellularSheaf and related sheaf operators.
- **EP-0160**: Implements DEC operators, Hodge decomposition, and conjugate gradient solver.
- Implements EP-0153 Cochain carrier, semiring matrix, and vector primitives.

### Perf

- **benchmarks**: Updates determinant benchmark to use `academic.determinant`.

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
- **semiring**: Add new algebraic and statistical semirings with expanded catalog support
- **verification**: Add support for complex number comparison and expand semiring catalog

### Fix

- Exposes core type aliases directly from the `algebrax` package.
- Exposes core type aliases directly from the `algebrax` package.

### Refactor

- **semiring**: Replace `_normalize_semiring` with `Semiring.normalize` and add canonical `default` method
- **recipes**: Replace custom PageRank logic with `ax.analysis.pagerank`
- **recipes**: Add semiring card previews and Jupyter compatibility checks
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
- Adds tensor algebra module with einsum, outer product, and tensordot.

### Refactor

- Renames `reciepes` directory to `recipes`.
- Refactors lab recipes for algebrax API updates and UI enhancements.
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
