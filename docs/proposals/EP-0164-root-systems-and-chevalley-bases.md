---
title: "EP-0164: Root Systems, Weyl Groups & Chevalley-Serre Construction for Simple Lie Algebras"
description: "Establishes root systems, Weyl reflections, Dynkin classification, and the Chevalley-Serre construction to universally generate all classical and exceptional simple Lie algebras (including F4, E6, E7, E8)."
icon: lucide/network
status: final
---

# EP-0164: Root Systems, Weyl Groups & Chevalley-Serre Construction for Simple Lie Algebras

| Field        | Value                                                                                          |
|:-------------|:-----------------------------------------------------------------------------------------------|
| **EP**       | 0164                                                                                           |
| **Title**    | Root Systems, Weyl Groups & Chevalley-Serre Construction for Simple Lie Algebras               |
| **Author**   | Eran Rivlis & Antigravity (The Explorer)                                                       |
| **Sponsor**  | The Council                                                                                    |
| **Delegate** | ⚖️ Emmy Noether (Symmetry), ⚡ Claude Shannon (Efficiency) & 🧩 Bertrand Russell (Consistency) |
| **Status**   | Final                                                                                          |
| **Type**     | Standards Track                                                                                |
| **Created**  | 2026-09-10                                                                                     |
| **Updated**  | 2026-09-12                                                                                     |
| **Replaces** | None                                                                                           |

---

## Abstract

This proposal establishes a universal **Root System and Chevalley-Serre Engine** in AlgebraX. Extending the matrix Lie
algebra foundation established in `EP-0163` (`algebrax.lie`), this engine algorithmically generates the structure
constants and basis representations of **all simple Lie algebras** directly from their integer Cartan matrix
$A \in \mathbb{Z}^{r \times r}$.

By implementing Weyl reflections, root lattice generation, and the Carter–Tits canonical sign algorithm, this engine
seamlessly constructs the entire Cartan–Killing classification: the infinite classical families ($A_n, B_n, C_n, D_n$)
and the complete exceptional family:
$$\mathfrak{g}_2 \; (\dim = 14), \quad \mathfrak{f}_4 \; (\dim = 52), \quad \mathfrak{e}_6 \; (\dim = 78), \quad \mathfrak{e}_7 \; (\dim = 133), \quad \mathfrak{e}_8 \; (\dim = 248)$$
without requiring millions of hardcoded matrix entries or external computer algebra dependencies.

---

## Motivation

In `EP-0163`, AlgebraX introduced the unified `LieAlgebra` abstraction alongside concrete matrix generators for
$\mathfrak{so} (n)$, $\mathfrak{su} (n)$, $\mathfrak{sp} (2n)$, $\mathfrak{sl} (2)$, $\mathfrak{se} (3)$, and the
exceptional
algebra $\mathfrak{g}_2$ ($\dim = 14$, realized as $7 \times 7$ derivation matrices of the octonions).

However, completing the exceptional Lie algebra family
($\mathfrak{f}_4, \mathfrak{e}_6, \mathfrak{e}_7, \mathfrak{e}_8$)
via explicit coordinate matrices encounters three severe mathematical barriers:

1. **Representation Explosion:**
    - $\mathfrak{f}_4$ ($\dim = 52$): Minimal faithful representation is $26 \times 26$.
    - $\mathfrak{e}_6$ ($\dim = 78$): Minimal representation is $27 \times 27$ (collineations of the Cayley projective
      plane).
    - $\mathfrak{e}_7$ ($\dim = 133$): Minimal representation is $56 \times 56$ (Freudenthal triple systems).
    - $\mathfrak{e}_8$ ($\dim = 248$): **Has no non-trivial representation smaller than its
      adjoint ($248 \times 248$)!**
2. **Combinatorial Bloat:**
   $\mathfrak{e}_8$ has 240 roots and **17,184 non-zero structure constant tensor entries**
   ($[e_\alpha, e_\beta] = N_{\alpha, \beta} e_{\alpha+\beta}$). Hardcoding these entries in source files would add
   megabytes of static data, violating **Shannon Efficiency (Zero Bloat)**.
3. **The Cocycle Sign Ambiguity:**
   In the Chevalley basis, the structure constants satisfy $N_{\alpha, \beta} = \pm (p + 1)$. The signs cannot be
   chosen arbitrarily; they must satisfy a non-trivial bilinear 2-cocycle condition:
   $$\epsilon (\alpha, \beta) \epsilon (\alpha + \beta, \gamma) = \epsilon (\beta, \gamma) \epsilon (\alpha, \beta + \gamma)$$
   A single sign error among 17,184 entries breaks the Jacobi identity ($[X, [Y, Z]] + \dots \ne 0$).

A universal root-system engine solves all three challenges simultaneously by deriving every root, coroot, and bracket
sign from first principles in single-digit milliseconds.

---

## Rationale

The design is governed by the 8 Pillars of The Council Framework (`PRINCIPLES.md`):

### 1. Symmetry (Emmy Noether)

Root systems are the geometric crystallization of continuous symmetry. The Weyl group $W$ acts as an isometry on the
Euclidean root space via reflections:
$$s_i (\alpha) = \alpha - \langle \alpha, \alpha_i^\vee \rangle \alpha_i$$
All invariants—the Killing form, the Casimir operator, and the Weyl dimension formula—derive symmetrically from $W$.

### 2. Efficiency (Claude Shannon)

Rather than storing tens of thousands of static coefficients, the algorithm derives $\Phi$ and $f_{ab}^c$ on-the-fly
from an $r \times r$ Cartan matrix in $O (|\Phi|^2)$ time (under 50 milliseconds for $\mathfrak{e}_8$). Memory
consumption
is minimal, and coordinate sparsity is preserved.

### 3. Consistency (Bertrand Russell)

Classical and exceptional algebras share the identical `LieAlgebra` and `StructureConstants` interfaces. A user invokes
`f4()`, `e8()`, or `so_n(10)` identically, with uniform support for brackets, Killing forms, adjoint matrices, and
BCH series.

### 4. Falsifiability (Karl Popper)

Every generated exceptional algebra is subjected to automated property-based tests verifying:

- Jacobi identity: $\sum_k (f_{ab}^k f_{kc}^d + \dots) = 0$ via `ax.tensor.einsum`
- Antisymmetry: $f_{ab}^c = -f_{ba}^c$
- Cartan semisimplicity: $\det (K) \ne 0$
- Dimension agreement with theoretical formulas: $\dim \mathfrak{g} = r + |\Phi|$.

---

## Specification

### 1. Data Models & Type Contracts in `algebrax.lie`

```python
from dataclasses import dataclass
from typing import Literal

DynkinType = Literal["A", "B", "C", "D", "G", "F", "E"]


@dataclass(frozen=True)
class RootSystem:
    """Crystallographic root system generated by simple roots and Weyl reflections."""
    cartan_matrix: list[list[int]]
    rank: int
    roots: list[tuple[int, ...]]
    positive_roots: list[tuple[int, ...]]
    coroots: list[tuple[float, ...]]

    @classmethod
    def from_cartan_matrix(cls, cartan: list[list[int]]) -> "RootSystem":
        """Generate complete root system by iterative simple Weyl reflections."""
        ...

    @classmethod
    def from_dynkin(cls, family: DynkinType, rank: int) -> "RootSystem":
        """Construct standard Cartan matrix and generate root system."""
        ...

    def weyl_reflect(self, root: tuple[int, ...], simple_idx: int) -> tuple[int, ...]:
        """Apply simple reflection s_i(alpha) = alpha - <alpha, alpha_i^v> alpha_i."""
        ...
```

### 2. The Chevalley–Serre Generator

```python
def chevalley_lie_algebra(
        cartan_or_root_system: RootSystem | list[list[int]],
        names: list[str] | None = None,
) -> LieAlgebra:
    r"""Construct a finite-dimensional simple Lie algebra in the Chevalley basis.
    
    Basis elements:
    - h_1, ..., h_r: Cartan generators (indices 0 .. r-1)
    - e_alpha for alpha in Phi^+: Positive root vectors
    - f_alpha for alpha in Phi^+: Negative root vectors (f_alpha = e_{-alpha})
    
    Total dimension: r + |Phi|.
    
    Commutation relations:
    1. [h_i, h_j] = 0
    2. [h_i, e_alpha] = <alpha, alpha_i^v> e_alpha
    3. [e_alpha, e_{-alpha}] = h_alpha = sum_i c_i h_i
    4. [e_alpha, e_beta] = N_{alpha, beta} e_{alpha+beta} if alpha + beta in Phi
    """
    ...
```

### 3. The AlgebraX Mathematical Docstring Standard (AMDS) for Lie Algebras

In accordance with `EP-0150` (AMDS), all Lie algebra structures and root systems must include a structured mathematical docstring following Google Python Style with machine-parseable metadata:

#### A. Lie Algebra Classes and Factory Functions

```python
def so3() -> LieAlgebra:
    r"""The 3D spatial rotation algebra so(3) spanned by {J_x, J_y, J_z}.

    Algebraic Signature:
        $\langle \mathfrak{so}(3), [\cdot, \cdot], B \rangle \quad [X, Y] = -[Y, X], \quad [X, [Y, Z]] + [Y, [Z, X]] + [Z, [X, Y]] = 0$

    Cartan Classification:
        - Family: Simple Lie algebra $B_1 \cong A_1$ (compact real form).
        - Dimension: $3$ ($\dim = \frac{n(n-1)}{2}$).
        - Rank: $1$ (Cartan subalgebra dimension).
        - Root System: $\Phi = \{\pm \alpha\}$ ($2$ roots).

    Carrier & Invariants:
        - Field: Real numbers $\mathbb{R}$ (or $\mathbb{C}$).
        - Killing Form: $B(X, Y) = -2 \langle X, Y \rangle$ (negative-definite, semisimple).
        - Center: $\mathfrak{z}(\mathfrak{g}) = \{0\}$.

    Commutation Relations:
        $[J_x, J_y] = J_z, \quad [J_y, J_z] = J_x, \quad [J_z, J_x] = J_y$
        Equivalently: $[u, v] = u \times v$ for $u, v \in \mathbb{R}^3$.

    Applications:
        Spatial attitude kinematics, computer vision, robotics, rigid body dynamics,
        quantum angular momentum.
    """
```

#### B. Root Systems (`RootSystem`)

```python
class RootSystem:
    r"""Crystallographic root system generated by simple roots and Weyl reflections.

    Algebraic Signature:
        $\Phi \subset \mathbb{E}^r, \quad s_i(\alpha) = \alpha - \langle \alpha, \alpha_i^\vee \rangle \alpha_i, \quad \frac{2 \langle \alpha, \beta \rangle}{\langle \beta, \beta \rangle} \in \mathbb{Z}$

    Dynkin Classification:
        - Dynkin Type: Family symbol ($A_n, B_n, C_n, D_n, G_2, F_4, E_6, E_7, E_8$).
        - Rank ($r$): Dimension of ambient Cartan subspace $\mathfrak{h}^*$.
        - Roots ($|\Phi|$): Total cardinality of root set ($2 \times |\Phi^+|$).

    Operations:
        - Simple Reflection ($s_i(\alpha)$): Fundamental Weyl reflection across hyperplane orthogonal to $\alpha_i$.
        - Euclidean Projection ($\mathbf{x}(\alpha)$): Isomorphic embedding into orthonormal Cartesian space $\mathbb{R}^N$.
        - Dynkin Diagram Rendering: Multi-format (ASCII, Mermaid flowchart, and responsive SVG vector graphic) with Jupyter rich display hook (`_repr_svg_`).

    Properties:
        Reduced, Crystallographic, Finite Reflection Group $W$.

    Applications:
        Classification of simple Lie groups, grand unified theories in particle physics,
        singularity theory, Coxeter arrangements.
    """
```

### 4. Canonical Exceptional Constructors

```python
def g2() -> LieAlgebra:
    """The 14-dimensional exceptional Lie algebra G_2 (rank 2)."""
    ...


def f4() -> LieAlgebra:
    """The 52-dimensional exceptional Lie algebra F_4 (rank 4, 48 roots)."""
    ...


def e6() -> LieAlgebra:
    """The 78-dimensional exceptional Lie algebra E_6 (rank 6, 72 roots)."""
    ...


def e7() -> LieAlgebra:
    """The 133-dimensional exceptional Lie algebra E_7 (rank 7, 126 roots)."""
    ...


def e8() -> LieAlgebra:
    """The 248-dimensional exceptional Lie algebra E_8 (rank 8, 240 roots)."""
    ...
```

---

## Backwards Compatibility

This proposal is 100% backwards-compatible:

- Extends `algebrax.lie` without modifying existing functions or class contracts.
- Existing matrix-based constructors (`so3`, `sl2`, `se3`, `su2`, `so_n`, `sp_n`) retain their current matrix basis.
- The `g2()` factory will retain its $7 \times 7$ derivation matrix basis while gaining root-system introspection.

---

## How to Teach This / Documentation Plan

1. **User Guide Expansion:**
   Update `docs/guide/discrete/lie_algebras.md` with:
    - The Cartan-Killing classification ($A_n, B_n, C_n, D_n, G_2, F_4, E_6, E_7, E_8$).
    - Roots, coroots, and the geometric action of the Weyl group.
    - Examples constructing $E_8$ and inspecting its root vectors and Killing form.
2. **Interactive Jupyter Recipe:**
   Author `recipes/exceptional_lie_algebras.py` illustrating $E_8$ root projection and BCH dynamics.

---

## Reference Implementation

```python
def generate_roots(cartan: list[list[int]]) -> list[tuple[int, ...]]:
    """Generate all roots of a finite Cartan matrix in simple root coordinates."""
    r = len(cartan)
    simple = [tuple(1 if k == i else 0 for k in range(r)) for i in range(r)]
    roots = set(simple)
    frontier = list(simple)

    while frontier:
        alpha = frontier.pop()
        for i in range(r):
            # s_i(alpha)_k = alpha_k - sum_j alpha_j * cartan[j][i] * delta_ik
            val = sum(alpha[j] * cartan[j][i] for j in range(r))
            beta = list(alpha)
            beta[i] -= val
            beta_t = tuple(beta)
            if (all(x >= 0 for x in beta_t) or all(x <= 0 for x in beta_t)) and any(x != 0 for x in beta_t):
                if beta_t not in roots:
                    roots.add(beta_t)
                    frontier.append(beta_t)

    # Include negative roots
    all_roots = set(roots)
    for a in roots:
        all_roots.add(tuple(-x for x in a))
    return sorted(all_roots)
```

---

## Rejected Ideas

1. **Hardcoding Structure Constants as Static JSON/Python Dictionaries:**
    - *Considered:* Storing precomputed `tensor` dictionaries for $F_4$ (1,152 entries) and $E_8$ (17,184 entries).
    - *Rejected:* Violates Shannon Efficiency and code hygiene. Algorithmic generation executes in milliseconds and
      guarantees mathematical transparency.
2. **Dense $248 \times 248$ Adjoint Matrices:**
    - *Considered:* Pre-assembling 248 full dense matrices for $E_8$.
    - *Rejected:* A $248 \times 248 \times 248$ dense tensor requires $>120$ MB of memory. Coordinate-sparse
      `StructureConstants` require $< 2$ MB.
3. **External Dependencies (SymPy, SageMath, GAP):**
    - *Rejected:* AlgebraX strictly maintains its zero-heavy-dependency standard. All algorithms are implemented in pure
      Python.

---

## Open Questions
 
- [X] **Multi-Format Dynkin Diagram Renderer (ASCII, Mermaid, SVG):** Accepted and implemented. `RootSystem.dynkin_diagram(format='ascii' | 'mermaid' | 'svg')`, `dynkin_ascii()`, `dynkin_mermaid()`, `dynkin_svg()`, and `_repr_svg_()` provide clean ASCII text, Mermaid flowchart markdown, and responsive SVG vector graphics with interactive Jupyter rendering for all classical and exceptional families.
- [X] **Euclidean Coordinate Projection:** Accepted and implemented. `RootSystem.to_euclidean(root)` maps roots expressed in $\mathbb{Z}^r$ simple root coordinates into standard orthonormal Cartesian space $\mathbb{R}^N$.

---

## Change Log

* **2026-09-12:**
    * Transitioned proposal status to **Final** following full implementation and verification of root systems, Weyl reflections, and Chevalley-Serre simple Lie algebra generation.
    * Expanded Coxeter-Dynkin diagram rendering to multi-format: added Mermaid flowchart and standalone responsive SVG vector graphics with Jupyter interactive cell display (`_repr_svg_()`).
    * Added dedicated convenience methods `dynkin_ascii()`, `dynkin_mermaid()`, and `dynkin_svg()` to `RootSystem`.
    * Implemented comprehensive micro-benchmarks across 7 functional groups in `benchmarks/test_lie_benchmarks.py`.
    * Added full test coverage for all classical and exceptional families in `tests/algebrax/test_lie.py`.
    * Fully resolved and marked Open Questions 1 and 2 as accepted and implemented.
* **2026-09-10:**
    * Resolved Open Questions 1 and 2: accepted automated ASCII Dynkin diagrams and Euclidean root coordinate projections.
    * Added Section 3: AlgebraX Mathematical Docstring Standard (AMDS) specification for Lie algebras and root systems.
    * Initial Draft authored following the completion and stabilization of `EP-0163`.
