---
title: "EP-0002: Mathematical Docstring Standards & Algebraic Signatures (AMDS)"
description: "Establishes the AlgebraX Mathematical Docstring Standard (AMDS) as the single source of truth for LaTeX signatures, KaTeX rendering, IDE tooltips, and automated documentation introspection."
icon: lucide/file-code-2
status: draft
---

# EP-0002: Mathematical Docstring Standards & Algebraic Signatures (AMDS)

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0002                                                                              |
| **Title**         | Mathematical Docstring Standards & Algebraic Signatures (AMDS)                    |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | The Grand Council                                                                 |
| **Delegate**      | 💡 Richard Feynman (Clarity) & 🧩 Bertrand Russell (Consistency)                  |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-11-12                                                                        |
| **Updated**       | 2026-11-12                                                                        |
| **Replaces**      | [EP-0150](EP-0150-standardized-mathematical-docstrings.md)                        |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the permanent **AlgebraX Mathematical Docstring Standard (AMDS)** across all algebraic structures, protocols, and operators in the library. As mandated by [EP-0001](EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md), code must be self-explanatory and demystified.

By defining a machine-parseable `Algebraic Signature: $...$` block and structured sections (`Carrier`, `Operations`, `Properties`, `Applications`) in every mathematical class docstring, the docstring serves as the **Single Source of Truth** for:
1. Human engineers and students reading source code in editors.
2. Rich interactive IDE tooltips (VS Code, PyCharm, Neovim) and Jupyter `?` inspection.
3. Automated reflection utilities (`algebrax.display.extract_algebraic_signature`, `get_algebraic_metadata`).
4. Publication-grade KaTeX/MathJax rendering in documentation cards and interactive notebooks.

This proposal formally supersedes and canonizes [EP-0150](EP-0150-standardized-mathematical-docstrings.md) into the single-digit foundational canon.

---

## Motivation

In computational mathematics, a code object is meaningless without its mathematical definition. When a developer inspects `TropicalSemiring()`, `CliffordAlgebra(3, 0)`, `OctonionAlgebra()`, or `CellularSheaf()`, they face immediate cognitive barriers if the formal algebraic definition is missing or buried in unstructured narrative prose:

1. **Information Asymmetry in Tooltips**: Hovering over a class in an IDE should immediately reveal its formal signature (e.g., $\langle \mathbb{R} \cup \{+\infty\}, \min, +, +\infty, 0 \rangle$), not just a vague sentence.
2. **Split-Brain Drift**: Maintaining mathematical formulas in external documentation or web pages inevitably leads to drift when code evolves. The docstring must be the authoritative anchor.
3. **Automated Verification of Documentation Completeness**: Without a formal syntactic standard, the test suite cannot verify whether new algebraic additions are properly documented with rigorous mathematical signatures.

---

## Rationale & Council Alignment

- **💡 Richard Feynman (The Freshman Test & Clarity)**:
  Every mathematical object must display its formal definition and intuitive operation directly before the reader's eyes. Mathematical rigor and clarity are not enemies; a clean algebraic signature $\langle V, +, \cdot \rangle$ provides instant clarity.
- **🧩 Bertrand Russell (Consistency & Deductive Order)**:
  Uniformity of form across all mathematical domains. Whether a semiring, a Lie algebra, a cellular sheaf, or a quantum group, the docstring follows an identical section hierarchy.
- **🔬 Karl Popper (Falsifiability & Documentation Coverage)**:
  The AMDS standard is enforced by automated test oracles (`tests/algebrax/test_docstrings.py`), ensuring that 100% of exported algebraic classes in `algebrax` contain valid, parseable LaTeX signatures.
- **⚡ Claude Shannon (Zero Overhead)**:
  Signature extraction uses pure Python standard library regex and `inspect` module utilities; zero third-party parsing dependencies (no Jinja, no external AST walkers) are required at runtime.

---

## Specification

### 1. The Anatomy of an AMDS Docstring

Every exported algebraic structure (Layer 2 protocol, concrete Layer 3 algebra, and topological complex) must conform to Google Python Style with the standardized AMDS mathematical blocks:

```python
class MyAlgebraicStructure:
    r"""One-line concise summary of the mathematical structure.

    Algebraic Signature:
        $\langle \text{Carrier}, \text{Operations...}, \text{Identities...} \rangle$

    Carrier:
        Formal set or type definition (e.g., `dict[int, float]`, `float`, `tuple[int, ...]`).

    Operations:
        - Primary Operation ($a \cdot b$): Explicit definition.
        - Auxiliary / Derived Operation: Formula.

    Properties:
        Equational axioms satisfied (e.g., Commutative, Associative, Unital, Alternative).

    Applications:
        Canonical physics, engineering, or computational use cases.
    """
```

*Note: Raw string literals (`r"""..."""`) are mandatory whenever LaTeX backslashes (e.g. `\mathbb{R}`, `\otimes`, `\langle`) are present.*

---

### 2. Domain-Specific AMDS Templates

#### 2.1 Semirings (`algebrax.semiring`)
```python
class TropicalSemiring(Semiring[float]):
    r"""The Min-Plus semiring for shortest path and dynamic programming problems.

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

    Applications:
        Shortest path routing (Dijkstra, Bellman-Ford), tropical geometry, Viterbi decoding.
    """
```

#### 2.2 Quantum & Non-Associative Algebras (`algebrax.algebra`)
```python
class SymmetricMatrixJordanAlgebra(JordanAlgebra[float, SparseMatrix[Any, float]]):
    r"""Special Jordan algebra of sparse real matrices under the anticommutator product.

    Algebraic Signature:
        $\langle \mathbb{R}, \mathrm{Mat}_n(\mathbb{R}), \cdot_s, \mathbf{0}, +, -, \circ \rangle$

    Carrier:
        `SparseMatrix[Any, float]` (real symmetric sparse matrices).

    Operations:
        - Jordan Product ($A \circ B$): $\frac{1}{2}(AB + BA)$
        - Scalar Multiplication ($r \cdot A$): Standard matrix scalar scaling.

    Properties:
        Commutative ($A \circ B = B \circ A$), Power-associative, satisfies Jordan identity
        $(A \circ B) \circ A^2 = A \circ (B \circ A^2)$.

    Applications:
        Quantum mechanical observables, density matrix evolution, self-adjoint operator dynamics.
    """
```

#### 2.3 Clifford & Geometric Algebras (`algebrax.clifford`)
```python
class CliffordAlgebra:
    r"""Universal Clifford (Geometric) Algebra over real quadratic spaces.

    Algebraic Signature:
        $C\ell_{p,q,r}(\mathbb{R}) = T(V) / \langle v \otimes v - Q(v)\mathbf{1} \rangle$

    Operations:
        - Geometric Product ($A B$): Fundamental associative Clifford product.
        - Wedge Product ($A \wedge B$): Exterior anti-symmetric product.
        - Inner Product ($A \cdot B$): Left contraction metric product.

    Properties:
        $\mathbb{Z}_2$-graded associative algebra of dimension $2^{p+q+r}$.
    """
```

#### 2.4 Functorial Sheaves & Fiber Bundles (`algebrax.topology`)
```python
class CellularSheaf:
    r"""Cellular sheaf over a cell poset category assigning vector spaces to cells and linear restriction maps to face relations.

    Algebraic Signature:
        $\mathcal{F}: \mathbf{CellPoset}(K)^\mathrm{op} \longrightarrow \mathbf{Vect}_\mathbb{R}$

    Coboundary Operator:
        $d^k: C^k(K; \mathcal{F}) \longrightarrow C^{k+1}(K; \mathcal{F})$ where $(d^k x)_{\sigma \trianglelefteq \tau} = [\sigma : \tau] \mathcal{F}_{\sigma \trianglelefteq \tau}(x_\sigma)$

    Properties:
        Coboundary nilpotency $d^{k+1} \circ d^k = \mathbf{0}$, Sheaf Laplacian $\Delta_\mathcal{F} = d^* d + d d^* \ge 0$.
    """
```

---

### 3. The Reflection & Introspection Engine (`algebrax.display`)

The library exposes standard reflection utilities in [`src/algebrax/display.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/display.py):

```python
from algebrax.display import extract_algebraic_signature, get_algebraic_metadata

# 1. Direct Signature Extraction
sig = extract_algebraic_signature(TropicalSemiring)
assert sig == r"\langle \mathbb{R} \cup \{+\infty\}, \min, +, +\infty, 0 \rangle"

# 2. Rich Metadata Card for Jupyter & Documentation
meta = get_algebraic_metadata(TropicalSemiring)
assert meta.name == "TropicalSemiring"
assert meta.signature is not None
```

---

## Backwards Compatibility

1. **Non-Breaking Extension**: This proposal imposes no breaking changes on numerical or algebraic computation.
2. **Replaces EP-0150**: All specifications previously set forth in `EP-0150` are preserved and elevated to foundational canon status in `EP-0002`.

---

## How to Teach This / Documentation Plan

1. **Developer Guides**:
   - `docs/guide/` pages include rich LaTeX cards generated directly from the docstrings.
   - New contributors and AI agents must follow AMDS when introducing new algebraic structures.
2. **Test Enforcement**:
   - The test suite verifies that every class exported in `algebrax.semiring`, `algebrax.algebra`, `algebrax.clifford`, `algebrax.lie`, and `algebrax.topology` contains an `Algebraic Signature: $...$` block.

---

## Reference Implementation

- **Docstring Parser & Metadata**: [`src/algebrax/display.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/display.py).
- **Test Suite**: `tests/algebrax/test_docstrings.py`.
- **Precedent Proposal**: [`docs/proposals/EP-0150-standardized-mathematical-docstrings.md`](EP-0150-standardized-mathematical-docstrings.md).

---

## Rejected Ideas

1. **Standalone External YAML/JSON Metadata Files**:
   *Rejected*: Storing mathematical signatures in external configuration files inevitably leads to docstring drift. Keeping the signature directly inside the Python docstring guarantees unity of documentation and code.
2. **Unstructured Prose Docstrings**:
   *Rejected*: Freeform text prevents automated parsing, inhibits rich display card generation, and makes test-based documentation coverage auditing impossible.

---

## Open Questions

None. The AMDS standard has been implemented, validated, and stress-tested across all 34 semirings and domain modules.

---

## Change Log

- **2026-09-05**: Authored initial draft as EP-0150.
- **2026-11-12**: Elevated and codified into the single-digit foundational canon as EP-0002.
