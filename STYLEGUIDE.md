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
* **Logging**: Use the `loguru` library for all logging.
* **Complexity**: Aim to keep the cyclomatic complexity of functions at or below 15, as configured in `ruff`.
* **Float Equality**: When comparing values to float values use `math.isclose`.

## Test Style

Tests are written using the `pytest` framework.

* **Location**: All tests reside in the `tests/` directory.
* **Naming**: Test files must be named `test_*.py`, and test functions must be prefixed with `test_`.
* **Structure**: Tests should follow the "Arrange, Act, Assert" pattern to ensure clarity and separation of concerns.
* **Fixtures**: Use `pytest` fixtures for setup and teardown logic. Place common fixtures in `tests/conftest.py`.
* **Mocks**: Use the `pytest-mock` library for mocking dependencies.
* **Floating Tests**: For tests that involve floating-point comparisons, use `pytest.approx` to handle precision issues.

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

To ensure our documentation remains organized, scalable, and easy to navigate, we strictly enforce a clear **Separation of
Concerns** between library fundamentals and applied use cases:

1. **Start & Core Concepts (`docs/`)**:
   * Covers the library introduction (`index.md`), high-level conceptual foundations (`concepts.md`), and benchmarks/comparisons (`comparison.md`).

2. **The User Guide (`docs/guide/`) — Built-in Library Reference**:
   * **Scope**: Focuses exclusively on the **built-in capabilities** and core modules of `algebrax` (`semiring`, `matrix`,
     `tensor`, `trie`, `homology`, `transforms`, `probability`, `analysis`, `automata`, `category`, `lattice`, `group`, `verification`).
   * **Rule**: Do **not** invent or inline ad-hoc custom carrier types or one-off application scenarios inside the guide.
   * **Cross-Linking**: Guide overviews (such as the *Semiring Taxonomy*) and individual domain guides should explain the
     formal mathematics and built-in APIs, and then link directly to the relevant applied **Recipes** that demonstrate them in action.

3. **Recipes & Applied Applications (`recipes/` & `docs/recipes.md`) — Applied Problem Solving**:
   * **Scope**: All applied, multi-disciplinary use cases (e.g. quantum physics, cosmology, algorithmic finance, robotics,
     network resilience, cryptography, and custom carrier classes like `np.ndarray` or intervals) live in `recipes/`.
   * **Standard**: Every recipe must provide:
     * A standalone runnable script (`recipes/<name>.py`) with inline PEP 723 metadata (`# /// script ... ///`) runnable via `uv run`.
     * A synchronized Jupyter Notebook (`recipes/<name>.ipynb`).
     * Pure, exportable computational functions with **zero import-time side-effects** (demo runs must be encapsulated in `run_demo()` under `if __name__ == '__main__':`).
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
* **Code Blocks**: Fenced code blocks must always include language identifiers (`python`, `bash`, `mermaid`, `toml`, `text`).
* **Tables**: Use standard Markdown tables for tabular comparison and mathematical signatures.
* **Internal Linking**: Always use relative paths (e.g. `[Semiring Taxonomy](../guide/semirings/index.md)`) when referencing internal pages.

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

  This is enacted by the `commitzen` tool, which will follow this format when making commits.
  See [cz.toml](./cz.toml) for the configuration.

* **Branching**: Create new branches for each feature or bug fix. Name branches descriptively, like `feat/add-auth` or
  `fix/login-bug`.

* **Clean History**: Aim for a clean, linear history. Before merging a feature branch, rebase it on top of the main
  branch and squash related commits into logical units. Avoid merge commits for small features.
