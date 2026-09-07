# Style Guide

This document outlines the coding, testing, and documentation style guidelines for the project. These guidelines are
meant to complement established standards like PEP 8.

## Linting and Formatting

To maintain a consistent codebase, we use the following tools for linting and formatting:

* **`commitzen`**: For enforcing commit message conventions. This helps maintain a clean and understandable Git history.
* **`ruff`**: For linting and formatting Python code. The configuration is defined in `pyproject.toml`. It's recommended
  to integrate `ruff` into your IDE to get real-time feedback.
* **`mdformat`**: For formatting Markdown files, including documentation. This ensures a consistent style across all our
  documentation.

## Code Style

* **Line Length**: Maximum 120 characters.
* **Quotes** - use the following rules unless there's a good reason not to:
    * Use single quotes for strings.
    * Use double quotes for docstrings.
    * Use double quotes for f-strings.
* **Type Hinting**: All function and method signatures should include type hints.
* **Docstrings**: All public modules, functions, classes, and methods should have a docstring. We follow
  the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for
  docstring format.
    * **Mathematical Classes (AMDS)**: All algebraic, topological, and categorical classes (semirings, algebras, finite
      fields, simplicial complexes, and categorical morphisms) must follow the **AlgebraX Mathematical Docstring
      Standard (AMDS)**. Every mathematical structure class must include:
        1. A raw docstring (`r"""..."""`) to safely support LaTeX math escape sequences.
        2. An `Algebraic Signature:` section containing the formal LaTeX signature enclosed in `$ ... $`.
        3. Canonical sections for `Carrier:` (or `Parameters:`), `Operations:`, `Properties:` (or `Axioms:`), and
           `Applications:`. Example:
      ```python
      class TropicalSemiring(Semiring[float]):
          r"""The Min-Plus semiring for shortest path problems.
  
          Algebraic Signature:
              $\langle \mathbb{R} \cup \{+\infty\}, \min, +, +\infty, 0 \rangle$
  
          Carrier:
              `float` (real numbers with `float('inf')` as additive identity).
  
          Operations:
              - Addition ($\oplus$): $\min(a, b)$
              - Multiplication ($\otimes$): $a + b$
              - Zero Element ($\mathbb{0}$): $+\infty$
              - One Element ($\mathbb{1}$): $0.0$
  
          Properties:
              Idempotent, Commutative, Dioid, Path Semiring.
          """
      ```
* **Complexity**: Aim to keep the cyclomatic complexity of functions as configured for `ruff` in `pyproject.toml` or
  `ruff.toml`.
* **Float Equality**: When comparing computed floating-point values for equivalence or convergence, use `math.isclose`.
  For exact denominator singularity checks that guard against `ZeroDivisionError`, use `x == 0.0  # NOSONAR` to avoid
  truncating legitimate tiny probabilities or introducing arbitrary epsilon thresholds.
* **Regular Expressions (Deterministic & Safe Matching)**:
    * **Simplicity First**: Prefer Python's built-in string methods (`startswith`, `endswith`, `in`, `partition`,
      `split`)
      over regex when matching fixed tokens or simple prefixes/suffixes.
    * **Raw Strings**: Always use raw strings (`r"..."`) to prevent Python string escape sequences (e.g. `\b`) from
      being misinterpreted.
    * **Module Precompilation**: Compile patterns at module level into SCREAMING_SNAKE_CASE constants (e.g.,
      `_SIG_RE = re.compile(...)`) to avoid re-compilation in hot paths.
    * **Linear-Time Delimiters ($O (N)$)**: When extracting bounded content between delimiters, always use negated
      character classes (e.g., `\$([^$]+)\$`) instead of reluctant wildcards (`\$(.*?)\$`) to eliminate catastrophic
      backtracking (ReDoS / Sonar S5852).
    * **Disjoint Tokens**: Avoid overlapping quantifier sequences (e.g. avoid `\s*\n\s*` because `\s` includes `\n`;
      collapse to `\s*` or enforce horizontal spacing: `[ \t]*\n[ \t]*`). Never use nested repetitions like `(a+)+`.
    * **Readability**: For complex patterns, use `re.VERBOSE` (`re.X`) with multi-line layout and inline comments, and
      use named capture groups (`(?P<name>...)`) instead of brittle numeric indices (`group(1)`).
* **Cognitive Complexity Baseline**: The repository follows the `AlgebraX way` Quality Profile with a Cognitive
  Complexity threshold of **30** (calibrated for advanced mathematical and algebraic algorithms).
    * **Accidental Complexity**: If a function exceeds 30 due to multiple responsibilities (e.g. multi-branch
      formatting, checking independent axioms, or handling multiple normalizations), refactor into single-responsibility
      helper functions.
    * **Irreducible Numerical Kernels**: If an algorithm is an irreducible numerical or combinatorial routine from the
      literature (e.g. Jacobi rotations, Rayleigh quotient iteration, Einstein tensor contractions), retain the
      contiguous algorithm and document with `# NOSONAR - <domain rationale>`.
* **Mathematical Comments vs. Dead Code (`python:S125`)**: Never write mathematical derivation notes using raw Python
  assignment syntax (e.g. avoid `# a = b * c`). Always use descriptive prose or mathematical annotations (e.g.
  `# Transition step: a = b @ c`) so static analysis scanners do not mistake them for commented-out dead code.
* **Closure Scoping & Late-Binding (`python:S1515`)**: In Python, callables (lambdas, nested functions) capture
  variables from enclosing scopes by reference, not by value. Inside loops or comprehensions, avoid referencing
  loop-mutated variables inside deferred callables:
    * **Direct Pipeline over Closures**: Prefer single-pass transformations directly over item pairs/tuples (e.g.
      operating on `collection.items()` or using `enumerate`) rather than looking up loop variables inside closures.
    * **Early Parameter Binding**: If a loop-scoped variable must be referenced by a callable, bind it immediately at
      definition time via default arguments (`lambda item, bound_var=var: ...`) to guarantee safe evaluation.
* **Scientific & Algebraic Naming Alignment**: Function and variable names should align with canonical scientific
  computing conventions (NumPy, SciPy, LAPACK) and mathematical literature while respecting PEP 8:
    * **Invariance & Property Suffixes**: Adopt recognized domain conventions to indicate algebraic invariants (e.g.,
      suffixing `_eigh` for Hermitian/real-symmetric decompositions where the Spectral Theorem guarantees real
      eigenvalues and orthonormal eigenvectors; `_spd` for symmetric positive-definite operators).
    * **Mathematical Symbols in PEP 8**: When translating mathematical symbols to code, maintain snake_case while
      preserving indexing clarity (e.g., use `x_k` or `v_dense` instead of uppercase `X_k`, avoiding the need for linter
      suppressions).

## Test Style

Tests are written using the `pytest` framework.

* **Location**: All tests reside in the `tests/` directory.
* **Naming**: Test files must be named `test_*.py`, and test functions must be prefixed with `test_`.
* **Structure**: Tests should follow the "Arrange, Act, Assert" pattern to ensure clarity and separation of concerns.
* **Fixtures**: Use `pytest` fixtures for setup and teardown logic. Place common fixtures in `tests/conftest.py`.
* **Mocks**: Use the `pytest-mock` library for mocking dependencies.
* **Floating Tests**: For tests that involve floating-point comparisons, use `pytest.approx` to handle precision issues.
* **Warning Block Isolation (`python:S9088`)**: When testing expected warnings with `pytest.warns()` (or exceptions with
  `pytest.raises()`), enclose **only** the single function call expected to emit the signal. Place assertion comparisons
  outside the context manager to prevent test assertions from masking or conflating with the targeted emission:
    ```python
    # Correct
    with pytest.warns(PerformanceWarning):
        res = determinant(m)
    assert res == pytest.approx(-2)

    # Avoid (triggers Sonar S9088)
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == pytest.approx(-2)
    ```

## Documentation Style & Architecture

### Tooling and Build Engine

Project documentation is statically generated using **`zensical`** (configured in [`zensical.toml`](./zensical.toml)),
with MathJax 3 support for mathematical notation and `mkdocstrings` for docstring inspection.

* **Build Command**: Documentation builds are executed via:
  ```bash
  zensical build
  # Or via uvx:
  uvx --with mkdocstrings --with mkdocstrings-python zensical build
  ```
* **Format & Linter**: All documentation is written in standard Markdown and must build with zero errors.

### Information Architecture & Guiding Principles

To ensure our documentation remains organized, scalable, and easy to navigate, we strictly enforce a clear **Separation
of Concerns** between library fundamentals and applied use cases:

1. **Start & Core Concepts (`docs/`)**:
    * Covers the library introduction (`index.md`), high-level conceptual foundations (`concepts.md`), and
      benchmarks/comparisons (`comparison.md`).

2. **The User Guide (`docs/guide/`) — Built-in Library Reference**:
    * **Scope**: Focuses exclusively on the **built-in capabilities** and core modules of `algebrax` (`semiring`,
      `matrix`,
      `tensor`, `trie`, `homology`, `transforms`, `probability`, `analysis`, `automata`, `category`, `lattice`, `group`,
      `verification`).
    * **Rule**: Do **not** invent or inline ad-hoc custom carrier types or one-off application scenarios inside the
      guide.
    * **Cross-Linking**: Guide overviews (such as the *Semiring Taxonomy*) and individual domain guides should explain
      the formal mathematics and built-in APIs, and then link directly to the relevant applied **Recipes** that
      demonstrate them in action.

3. **Recipes & Applied Applications (`recipes/` & `docs/recipes.md`) — Applied Problem Solving**:
    * **Scope**: All applied, multi-disciplinary use cases (e.g. quantum physics, cosmology, algorithmic finance,
      robotics, network resilience, cryptography, and custom carrier classes like `np.ndarray` or intervals) live in
      `recipes/`.
    * **Standard**: Every recipe must provide:
        * A standalone runnable script (`recipes/<name>.py`) with inline PEP 723 metadata (`# /// script ... ///`)
          runnable via `uv run`.
        * A synchronized Jupyter Notebook (`recipes/<name>.ipynb`).
        * Pure, exportable computational functions with **zero import-time side-effects** (demo runs must be
          encapsulated in `run_demo()` under `if __name__ == '__main__':`).
        * Graphical visualization integration in [`recipes/lab.py`](./recipes/lab.py).
        * A documented entry in [`docs/recipes.md`](./docs/recipes.md).

4. **Enhancement Proposals (`docs/proposals/` & `docs/eps.md`)**:
    * Formal design proposals (EP-xxxx) documenting mathematical rationale, API design, and Council reviews.

### Formatting & Syntax Standards

* **Mathematical Expressions**: Use LaTeX syntax rendered with MathJax:
    * Inline math: `$x \in S$`
    * Display equations:
      ```markdown
      $$a \oplus (b \otimes c) = (a \oplus b) \otimes (a \oplus c)$$
      ```
* **Admonitions**: Use standard admonition blocks to highlight critical details, notes, or tips:
  ```markdown
  !!! note "Background Context"
      Explanatory notes or historical context.

  !!! tip "Performance"
      Optimization guidelines and algorithmic trade-offs.

  !!! warning "Boundary Condition"
      Edge cases or numerical stability considerations.
  ```
* **Code Blocks**: Fenced code blocks must always include language identifiers (`python`, `bash`, `mermaid`, `toml`,
  `text`).
* **Tables**: Use standard Markdown tables for tabular comparison and mathematical signatures.
* **Internal Linking**: Always use relative paths (e.g. `[Semiring Taxonomy](../guide/semirings/index.md)`) when
  referencing internal pages.

## Git and Commit Style

To maintain a clean and understandable version history, we follow these Git practices:

* **Commit Messages**: We adhere to the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
  specification. This helps in automating changelog generation and makes the commit history more readable. Each commit
  message should have a type (e.g., `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`) and a
  concise description.

  Example:
  ```
  feat: add user authentication service
  ```

  This is enacted by the `commitizen` tool, which will follow this format when making commits. See [cz.toml](./cz.toml)
  for the configuration.

* **Branching**: Create new branches for each feature or bug fix. Name branches descriptively, like `feat/add-auth` or
  `fix/login-bug`.

* **Clean History**: Aim for a clean, linear history. Before merging a feature branch, rebase it on top of the main
  branch and squash related commits into logical units. Avoid merge commits for small features.
