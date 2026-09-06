---
title: "EP-0150: Standardized Mathematical Docstrings & Algebraic Signature Registry"
description: "Establishes a unified mathematical docstring standard across semirings, algebras, and topological complexes with automated introspection, rich MathJax cards, and registry testing."
icon: lucide/file-code-2
status: draft
---

# EP-0150: Standardized Mathematical Docstrings & Algebraic Signature Registry

| Field        | Value                                                               |
|:-------------|:--------------------------------------------------------------------|
| **EP**       | 0150                                                                |
| **Title**    | Standardized Mathematical Docstrings & Algebraic Signature Registry |
| **Author**   | Eran Rivlis <eran@rivlis.info>                                      |
| **Sponsor**  | The Council                                                         |
| **Delegate** | Richard Feynman & Bertrand Russell                                  |
| **Status**   | Draft                                                               |
| **Type**     | Standards Track                                                     |
| **Created**  | 2026-09-05                                                          |
| **Updated**  | 2026-09-05                                                          |

---

## Abstract

This proposal establishes the **AlgebraX Mathematical Docstring Standard (AMDS)** across all algebraic structures in the
library (Semirings, Clifford Algebras, Galois Fields, Simplicial Complexes, and Categorical Morphisms).

By adopting a structured docstring template featuring a machine-parseable `Algebraic Signature: $...$` block, we
maintain the **Docstring as the Single Source of Truth** for human developers, IDE tooltips, and interactive Jupyter
help. A lightweight introspection utility dynamically extracts these signatures to feed a central `AlgebraicRegistry`,
auto-typesets MathJax LaTeX formulas inside `semiring_card`, provides native `_repr_latex_()`, and enforces 100%
documentation completeness through a single automated Council test (Popper).

---

## Motivation

AlgebraX is a computational laboratory where abstract mathematical theory meets high-performance sparse computing.
However, our documentation and metadata currently exhibit three points of friction:

1. **Information Asymmetry in IDEs:** When a user hovers over `TropicalSemiring()` in VS Code or executes
   `?TropicalSemiring` in Jupyter, they see arbitrary unstructured text. The formal mathematical
   signature $\langle \mathbb{R} \cup \{+\infty\}, \min, +, +\infty, 0 \rangle$ is either missing, written in ASCII
   approximations, or buried in prose.
2. **Split-Brain Maintenance Risk:** If we maintain a separate static registry file for mathematical formulas, it will
   inevitably drift out of sync with class implementations over time.
3. **Rich Display Gaps:** The interactive Jupyter notebook inspector `semiring_card` displays carrier identities and
   docstrings, but lacks the primary theoretical anchor: the publication-grade LaTeX algebraic signature.

---

## Rationale (Council Alignment)

* **Clarity (Feynman):** The "Freshman Test". When reading code, every mathematical structure must display its rigorous
  formal definition right in front of the developer's eyes—no hunting through external files.
* **Consistency (Russell):** Every mathematical class follows a uniform, predictable section hierarchy conforming to
  Google Python Style and MathJax LaTeX standards.
* **Falsifiability (Popper):** A single test suite validates that 100% of exported algebraic classes adhere to the
  docstring schema and contain valid, parseable LaTeX signatures.
* **Efficiency (Shannon):** Zero external dependencies (no Jinja2, no regex compile overhead at import, pure stdlib
  string extraction).
* **Harmony (The Steward):** Unifies docstrings, CLI catalogs, interactive Jupyter cards, and Zensical documentation
  pages from one canonical source.

---

## The AlgebraX Mathematical Docstring Standard (AMDS)

The standard defines a common anatomy tailored for each mathematical domain:

### 1. Semirings (`algebrax.semiring`)

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

    Applications:
        Shortest path routing (Dijkstra, Bellman-Ford, Floyd-Warshall),
        tropical geometry, dynamic programming.
    """
```

### 2. Clifford & Geometric Algebras (`algebrax.clifford`)

```python
class CliffordAlgebra:
    r"""Universal Clifford (Geometric) Algebra over real quadratic spaces.

    Algebraic Signature:
        $C\ell_{p,q,r}(\mathbb{R}) = T(V) / \langle v \otimes v - Q(v)\mathbf{1} \rangle$

    Metric Signature:
        $(p, q, r)$ representing positive, negative, and degenerate basis squares.

    Operations:
        - Geometric Product ($A B$): Fundamental associative Clifford product.
        - Wedge Product ($A \wedge B$): Exterior anti-symmetric product.
        - Inner Product ($A \cdot B$): Left contraction metric product.
        - Grade Reversion ($A^\dagger$): Anti-automorphism reversing blade order.

    Properties:
        $\mathbb{Z}_2$-graded associative algebra, dimension $2^{p+q+r}$.

    Applications:
        Relativistic physics (Dirac spinors), computer vision (quaternions/rotors),
        rigid body kinematics (dual quaternions PGA).
    """
```

### 3. Galois Finite Fields (`algebrax.galois`)

```python
class GaloisField:
    r"""Galois Finite Field GF(p^k) constructed via irreducible quotient polynomials.

    Algebraic Signature:
        $\mathrm{GF}(p^k) \cong \mathbb{F}_p[x] / \langle P(x) \rangle$

    Parameters:
        - Prime Characteristic ($p$): Base field $\mathbb{F}_p$.
        - Degree ($k$): Field extension dimension ($|\mathbb{F}| = p^k$).
        - Modulus ($P(x)$): Monic irreducible polynomial of degree $k$.

    Operations:
        - Addition ($a \oplus b$): Polynomial addition modulo $p$.
        - Multiplication ($a \otimes b$): Polynomial multiplication modulo $P(x)$ in $\mathbb{F}_p$.
        - Multiplicative Inverse ($a^{-1}$): Extended Euclidean algorithm in $\mathbb{F}_p[x]$.

    Properties:
        Finite field, cyclic multiplicative group $\mathrm{GF}(p^k)^\times \cong C_{p^k - 1}$.

    Applications:
        Reed-Solomon error correction, AES Rijndael cryptography, post-quantum lattices.
    """
```

### 4. Simplicial Complexes & Homology (`algebrax.homology`)

```python
class SimplicialComplex:
    r"""Abstract simplicial complex with sparse boundary operators and homology.

    Algebraic Signature:
        $\cdots \xrightarrow{\partial_{k+1}} C_k(K; \mathbb{R}) \xrightarrow{\partial_k} C_{k-1}(K; \mathbb{R}) \xrightarrow{\partial_{k-1}} \cdots$

    Boundary Nilpotency:
        $\partial_k \circ \partial_{k+1} = 0 \iff \mathrm{im}(\partial_{k+1}) \subseteq \ker(\partial_k)$

    Derived Invariants:
        - Homology Groups: $H_k(K) = \ker(\partial_k) / \mathrm{im}(\partial_{k+1})$
        - Betti Numbers ($\beta_k$): $\dim(H_k) = \mathrm{nullity}(\partial_k) - \mathrm{rank}(\partial_{k+1})$
        - Euler Characteristic ($\chi$): $\sum_{k} (-1)^k \beta_k = \sum_{k} (-1)^k |S_k|$

    Applications:
        Topological Data Analysis (TDA), persistent homology, sensor coverage consensus.
    """
```

### 5. Categorical Morphisms (`algebrax.category`)

```python
class KleisliMorphism:
    r"""Morphism in the Kleisli Category of a Monad (T, η, μ).

    Algebraic Signature:
        $f: A \to T(B) \quad \text{in} \quad \mathbf{Kl}(T)$

    Composition Law (Kleisli Fish Operator):
        $(g \circ_K f)(x) = \mu_C(T(g)(f(x)))$

    Monad Laws:
        - Left Identity: $\eta_B \circ_K f = f$
        - Right Identity: $f \circ_K \eta_A = f$
        - Associativity: $(h \circ_K g) \circ_K f = h \circ_K (g \circ_K f)$

    Applications:
        Probabilistic graph transitions, algebraic side-effects, monadic pipelines.
    """
```

### 6. Algebraic Data Structures (`algebrax.trie`)

```python
class AlgebraicTrie:
    r"""Prefix tree accumulator indexed over monoid sequences with semiring node values.

    Algebraic Signature:
        $\mathcal{T}: \Sigma^* \to (S, \oplus, \otimes)$

    Operations:
        - Insert / Merge: Value aggregation via semiring addition $\oplus$.
        - Contraction / Dot: Path convolution via semiring multiplication $\otimes$.
        - Pruning: Annihilation of zero-identity nodes ($\mathbb{0}$).

    Applications:
        Compressed n-gram language models, sparse provenance tracking, routing tables.
    """
```

---

## Technical Specification

### 1. The Introspection Engine (`algebrax.display` / `algebrax.structures`)

A lightweight parsing utility in `src/algebrax/display.py`:

```python
import inspect
import re
from typing import Any, NamedTuple

_SIG_RE = re.compile(r"Algebraic Signature:\s*\$([^$]+)\$")


class AlgebraicMeta(NamedTuple):
    name: str
    target_class: type
    signature: str
    summary: str
    docstring: str


def extract_algebraic_signature(cls_or_inst: Any) -> str | None:
    """Extract raw LaTeX algebraic signature from an object's docstring."""
    doc = inspect.getdoc(cls_or_inst) or ""
    match = _SIG_RE.search(doc)
    return match.group(1).strip() if match else None


def get_algebraic_metadata(cls_or_inst: Any) -> AlgebraicMeta:
    """Return structured metadata extracted directly from class docstring."""
    cls = cls_or_inst if isinstance(cls_or_inst, type) else type(cls_or_inst)
    doc = inspect.getdoc(cls) or ""
    sig = extract_algebraic_signature(cls) or r"\text{N/A}"
    summary = doc.split("\n")[0].strip() if doc else cls.__name__
    return AlgebraicMeta(
        name=cls.__name__,
        target_class=cls,
        signature=sig,
        summary=summary,
        docstring=doc,
    )
```

### 2. Auto-Typesetting in `semiring_card`

Update `semiring_card` to feature a centered MathJax equation block:

```python
def semiring_card(semiring: Any) -> str:
    meta = get_algebraic_metadata(semiring)
    zero_val = getattr(semiring, 'zero', 'N/A')
    one_val = getattr(semiring, 'one', 'N/A')

    math_block = ""
    if meta.signature != r"\text{N/A}":
        math_block = (
            f"<div style='margin: 8px 0 12px 0; padding: 6px 12px; background: #e2e8f0; "
            f"border-radius: 6px; font-size: 15px; text-align: center; color: #0f172a; "
            f"box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);'>"
            f"$${meta.signature}$$"
            f"</div>"
        )

    return (
        f"<div style='border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; "
        f"font-family: system-ui, -apple-system, sans-serif; max-width: 520px; "
        f"background-color: #f8fafc; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>"
        f"<div style='font-size: 16px; font-weight: bold; color: #0f172a;'>{meta.name}</div>"
        f"<div style='font-size: 13px; color: #475569; margin-top: 2px;'>{meta.summary}</div>"
        f"{math_block}"
        f"<table style='width: 100%; border-collapse: collapse; font-family: monospace; font-size: 13px;'>"
        f"<tr><td style='color: #64748b; padding: 3px 0;'>Identity &oplus; (zero):</td>"
        f"<td style='font-weight: bold; color: #0369a1;'><code>{zero_val}</code></td></tr>"
        f"<tr><td style='color: #64748b; padding: 3px 0;'>Identity &otimes; (one):</td>"
        f"<td style='font-weight: bold; color: #15803d;'><code>{one_val}</code></td></tr>"
        f"</table>"
        f"</div>"
    )
```

### 3. Free Jupyter Native LaTeX Representation (`_repr_latex_`)

Add `_repr_latex_` to `Semiring`:

```python
def _repr_latex_(self) -> str:
    sig = extract_algebraic_signature(self)
    return f"$${sig}$$" if sig else ""
```

Evaluating any semiring instance in a Jupyter cell now natively renders the mathematical formula.

---

## Testing & Verification (Popper Protocol)

A new test module `tests/algebrax/test_docstrings.py` will guarantee zero regressions:

```python
import inspect
import pytest
from algebrax.semiring import Semiring
from algebrax.display import extract_algebraic_signature


def test_all_catalog_semirings_follow_docstring_standard():
    """Verify that 100% of built-in semirings define an Algebraic Signature."""
    catalog = Semiring.catalog()
    missing = []

    for name, cls in catalog.items():
        doc = inspect.getdoc(cls)
        if not doc:
            missing.append(f"{name} (missing docstring)")
            continue
        sig = extract_algebraic_signature(cls)
        if not sig:
            missing.append(f"{name} (missing or invalid 'Algebraic Signature: $...$')")

    assert not missing, f"Semirings failing docstring standard: {missing}"


def test_specialized_structures_follow_docstring_standard():
    """Verify Clifford, Galois, and Homology classes follow the docstring standard."""
    from algebrax.clifford import CliffordAlgebra
    from algebrax.galois import GaloisField
    from algebrax.homology import SimplicialComplex

    for cls in [CliffordAlgebra, GaloisField, SimplicialComplex]:
        sig = extract_algebraic_signature(cls)
        assert sig is not None, f"{cls.__name__} missing 'Algebraic Signature: $...$'"
```

---

## How to Teach This / Documentation Plan

To ensure this standard is adopted seamlessly by current contributors, future maintainers, and AI pair-programming
agents:

1. **Integration into `STYLEGUIDE.md`**:
   The **Docstrings** section of `STYLEGUIDE.md` is updated to explicitly mandate the **AlgebraX Mathematical Docstring
   Standard (AMDS)** for all algebraic, topological, and categorical classes. It specifies the mandatory section layout:
    - `Algebraic Signature:` with MathJax LaTeX `$...$`
    - `Carrier:` / `Parameters:`
    - `Operations:`
    - `Properties:` / `Axioms:`
    - `Applications:`
2. **AI Agent Bootloader Integration**:
   Because AI agents assimilate `STYLEGUIDE.md` as part of the core bootloader protocol (`AGENTS.md`), documenting AMDS
   in the style guide guarantees that all future code generated by AI assistants will automatically conform to the
   standard.
3. **Actionable Test Diagnostics (Popper Protocol)**:
   The automated test suite in `tests/algebrax/test_docstrings.py` emits clear, instructional error messages referencing
   the style guide whenever a new class is missing its mathematical signature block.
4. **Interactive Notebook Discovery**:
   Interactive tutorial recipes and Jupyter notebooks demonstrate `_repr_latex_()` and `semiring_card`, showing
   developers how their in-code docstrings directly power the rich notebook visualization.

---

## Backwards Compatibility

This proposal is 100% backwards-compatible:

* **No Breaking Behavioral Changes:** Existing operations (`add`, `mul`, `zero`, `one`) and method contracts are
  unchanged.
* **Docstrings Only:** Only module and class docstrings are standardized and enriched.
* **Graceful Degradation:** The parser falls back cleanly to `\text{N/A}` if an external third-party semiring does not
  define an `Algebraic Signature: $...$` block.

---

## Reference Implementation

* Parser & metadata extractor: `extract_algebraic_signature(cls)` in `src/algebrax/display.py`.
* HTML card MathJax renderer: `semiring_card(semiring)` in `src/algebrax/display.py`.
* Standardized base class: `Semiring` in `src/algebrax/semiring/_base.py`.
* Verification test suite: `tests/algebrax/test_docstrings.py`.

---

## Rejected Ideas

1. **Jinja2 Template Engine for Semiring Cards:**
    * *Proposal:* Use Jinja2 HTML templates for rendering semiring cards.
    * *Rejection Rationale:* Definite overkill per Dennis Point (Noether & Shannon). AlgebraX maintains a minimal
      dependency footprint (`mappingtools` is currently the only runtime dependency). Adding Jinja2 and MarkupSafe
      brings tens of thousands of lines of template parsing and bytecode caching for ~15 lines of HTML. Standard Python
      f-strings in stdlib execute in single-digit microseconds with zero bloat.
2. **Arbitrary Dunder Attributes (`__math_def__`):**
    * *Proposal:* Add a custom magic method `__math_def__` to all semirings.
    * *Rejection Rationale:* PEP 8 explicitly reserves double-underscore names for the core Python language
      specification. Inventing custom dunders risks collisions with future Python versions and triggers static scanner
      warnings.
3. **Separate Static Registry File Without Docstrings:**
    * *Proposal:* Store all LaTeX signatures in an external dictionary file.
    * *Rejection Rationale:* Violates Locality of Reference (Feynman). When a developer or student opens `tropical.py`
      or inspects `?TropicalSemiring` in Jupyter, the mathematical signature should be right in front of them.
      Maintaining a disconnected registry causes split-brain maintenance and inevitable documentation drift.

---

## Open Questions

- [ ] Should `_repr_latex_()` on `Semiring` render solely the `Algebraic Signature`, or also include explicit rows for
  additive and multiplicative identities?
- [ ] Should the CLI command `python -m algebrax catalog` render raw LaTeX or an ASCII-art fallback when terminal
  unicode support is limited?

---

## Change Log

* **2026-09-05:**
    * Initial Draft of EP-0150.
    * Added Section: "How to Teach This (Education & Style Guide Integration)".
    * Updated `STYLEGUIDE.md` to formally document AMDS.
    * Registered EP-0150 in `EP-0099-expansion-roadmap.md` and `docs/eps.md`.
