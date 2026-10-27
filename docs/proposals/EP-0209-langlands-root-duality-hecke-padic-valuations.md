---
title: "EP-0209: Langlands Root Duality, Hecke Algebras & p-Adic Valuations"
description: "Formalize the computational pillars of the Langlands program: Langlands dual root systems and Cartan transposition, Hecke convolution operators, Ramanujan expander bounds, and p-adic numbers with tropical valuations."
icon: lucide/globe
status: draft
---

# EP-0209: Langlands Root Duality, Hecke Algebras & p-Adic Valuations

| Field             | Value                                                                |
|:------------------|:---------------------------------------------------------------------|
| **EP**            | 0209                                                                 |
| **Title**         | Langlands Root Duality, Hecke Algebras & p-Adic Valuations           |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                          |
| **Sponsor**       | Core Maintainers                                                     |
| **Delegate**      | ⚖️ Noether (Dual Symmetries) & 🔬 Popper (Ramanujan Spectral Bounds) |
| **Status**        | Draft                                                                |
| **Type**          | Standards Track                                                      |
| **Created**       | 2026-10-28                                                           |
| **Updated**       | 2026-10-28                                                           |
| **Replaces**      | —                                                                    |
| **Superseded-By** | —                                                                    |

---

## Abstract

This proposal establishes the discrete, computational foundations of the **Langlands Program** within AlgebraX,
connecting Lie representation theory, spectral graph theory, and non-archimedean arithmetic. EP-0209 introduces:

1. **Langlands Root Duality (`algebrax.lie`)**: Algorithmic construction of the Langlands dual root system $\Phi^\vee$
   via coroot inversion $\alpha^\vee = \frac{2\alpha}{\langle \alpha, \alpha \rangle}$ and Cartan matrix
   transposition $A \mapsto A^T$, formalizing the fundamental duality:
   $$\mathfrak{so} (2n+1) \longleftrightarrow \mathfrak{sp} (2n) \quad (B_n \longleftrightarrow C_n)$$
   while verifying the self-duality of $A_n, D_n, G_2, F_4, E_8$.
2. **Ramanujan Graph Verifier (`algebrax.analysis.spectral`)**: Verifying the **Ramanujan bound** (proved by Deligne via
   the Weil/Langlands conjectures) for $d$-regular network graphs:
   $$\max_{|\lambda_i| < d} |\lambda_i| \le 2\sqrt{d - 1}$$
   providing certified detection of optimal expander networks.
3. **Discrete Hecke Algebras on Graphs**: Double-coset convolution matrices and walk polynomials acting as discrete
   Hecke operators.
4. **$p$-Adic Numbers ($\mathbb{Q}_p$) & Non-Archimedean Valuations**: Implementing exact $p$-adic field arithmetic and
   the ultrametric $p$-adic valuation $v_p (x)$, establishing the canonical mathematical isomorphism between
   non-archimedean valuations and AlgebraX's **Tropical Min-Plus Semiring**:
   $$v_p (x \cdot y) = v_p (x) + v_p (y), \quad v_p (x + y) \ge \min (v_p (x), v_p (y))$$
5. **Property-Based Verification**: Executable testing in `algebrax.verification`: `verify_cartan_duality`,
   `verify_ramanujan_spectral_gap`, and `verify_padic_ultrametric_inequality`.

All representations preserve unboxed sparse matrix carriers and exact integer coordinate representations.

---

## Motivation

The Langlands Program is widely regarded as the pinnacle of 20th-century mathematical unification, connecting Galois
representations with automorphic forms and quantum gauge theories.

In computational discrete mathematics:

1. **Root Duality**: In [`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md), AlgebraX introduced simple Lie
   algebras and Dynkin diagrams. However, without Langlands root duality, we cannot model the relation between
   orthogonal and symplectic groups, or electric-magnetic S-duality ($G \leftrightarrow G^\vee$).
2. **Expander Graphs & Ramanujan Bounds**: In distributed algorithms and network theory, the optimal communication
   networks are **Ramanujan expander graphs** (Lubotzky, Phillips, Sarnak 1988), whose spectrum is governed by the
   Ramanujan-Petersson conjecture. AlgebraX's spectral graph theory package currently lacks this verification
   capability.
3. **The Tropical-$p$-Adic Bridge**: The tropical min-plus semiring is fundamentally the non-archimedean valuation ring
   of $p$-adic numbers. Formalizing $\mathbb{Q}_p$ and $v_p$ unifies exact number theory with tropical optimization.

---

## Rationale & Council Alignment

- **⚖️ Noether (Dual Symmetries & Coroot Invariance)**:
  Root duality $A \mapsto A^T$ represents one of the deepest dualities in representation theory. The dual group's
  Casimirs mirror the center of the original algebra.
- **🔬 Popper (Falsifiability & Strict Spectral Bounds)**:
  The Ramanujan inequality $|\lambda_i| \le 2\sqrt{d - 1}$ is an exact, falsifiable spectral threshold. The ultrametric
  inequality $|x + y|_p \le \max (|x|_p, |y|_p)$ is numerically verifiable.
- **⚡ Shannon (Zero Bloat & Sparse Cartan Transposition)**:
  Langlands duality on root systems requires zero new data structures: it is literally the matrix transpose of
  the $(r \times r)$ sparse Cartan matrix.
- **🧩 Russell (Taxonomy & Deductive Order)**:
  Correctly positions $p$-adic fields alongside Galois fields $\mathbb{F}_q$ and Reals $\mathbb{R}$ in
  `algebrax.algebra`.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"Langlands duality sounds intimidating until you look at the matrix: you take the Cartan matrix of an odd-dimensional
  sphere rotation, flip rows and columns, and out comes the matrix of symplectic rotations of phase space!"*

---

## Specification

### 1. Langlands Dual Root System (`src/algebrax/lie/langlands.py`)

```python
from algebrax.lie.root_system import RootSystem
from algebrax.linalg.sparse import transpose


def langlands_dual_root_system(rs: RootSystem) -> RootSystem:
    r"""Construct the Langlands dual root system $\Phi^\vee$.

    Coroots: $\alpha^\vee = \frac{2\alpha}{\langle \alpha, \alpha \rangle}$.
    Cartan matrix: $A^\vee = A^T$.
    """
    dual_cartan = transpose(rs.cartan_matrix)
    # Reconstruct root system from transposed Cartan matrix
    ...
    return RootSystem(cartan_matrix=dual_cartan)
```

### 2. Ramanujan Expander Graph Verifier (`src/algebrax/analysis/ramanujan.py`)

```python
import math
from typing import Any
from algebrax.analysis.spectral import adjacency_spectrum


def is_ramanujan_graph(
        adjacency: dict[Any, set[Any]],
        degree: int,
        tol: float = 1e-7,
) -> tuple[bool, float, float]:
    r"""Verify if a d-regular graph satisfies the Ramanujan bound:
    $$\max_{|\lambda_i| < d} |\lambda_i| \le 2\sqrt{d - 1}$$

    Returns:
        (is_ramanujan, max_nontrivial_eigenvalue, ramanujan_threshold)
    """
    threshold = 2.0 * math.sqrt(degree - 1)
    eigenvalues = adjacency_spectrum(adjacency)

    # Filter out trivial eigenvalues lambda == d and lambda == -d (bipartite)
    nontrivial = [abs(lam) for lam in eigenvalues if abs(abs(lam) - degree) > tol]
    max_lam = max(nontrivial, default=0.0)

    is_ram = max_lam <= threshold + tol
    return (is_ram, max_lam, threshold)
```

### 3. $p$-Adic Numbers & Tropical Valuation (`src/algebrax/algebra/padic.py`)

```python
class PAdicNumber:
    r"""A p-adic number in $\mathbb{Q}_p$ with expansion $x = p^v \sum_{i=0}^{N} a_i p^i$."""

    def __init__(self, p: int, valuation: int, digits: list[int]) -> None:
        self.p = p
        self.valuation = valuation  # v_p(x)
        self.digits = digits

    def p_adic_norm(self) -> float:
        r"""Compute p-adic absolute value $|x|_p = p^{-v_p(x)}$."""
        return self.p ** (-self.valuation)

    def tropical_valuation(self) -> float:
        r"""Compute tropical min-plus valuation $v_p(x)$."""
        return float(self.valuation)
```

### 4. Verification Suite (`src/algebrax/verification/langlands.py`)

```python
def verify_cartan_duality(rs: RootSystem) -> None:
    """Verify that dual of dual is isomorphic to original root system."""
    dual = langlands_dual_root_system(rs)
    dual_dual = langlands_dual_root_system(dual)
    assert dual_dual.cartan_matrix == rs.cartan_matrix


def verify_padic_ultrametric(x: PAdicNumber, y: PAdicNumber) -> None:
    r"""Verify the strong triangle inequality: $|x + y|_p \le \max(|x|_p, |y|_p)$."""
    sum_norm = (x + y).p_adic_norm()
    max_norm = max(x.p_adic_norm(), y.p_adic_norm())
    assert sum_norm <= max_norm + 1e-12
```

---

## Backwards Compatibility

Strictly additive. Extends `algebrax.lie`, `algebrax.analysis.spectral`, and `algebrax.algebra`.

---

## How to Teach This / Documentation Plan

1. **Applied Guide (`docs/guides/langlands-and-ramanujan.md`)**:
    - Visualizing Langlands root duality: why $B_n$ flips to $C_n$.
    - Certifying Ramanujan expander graphs for high-throughput network design.
    - The $p$-adic tree and the tropical semiring connection.

---

## Reference Implementation

A prototype of Cartan transposition and Ramanujan bound verification was validated in
`references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md`.

---

## Rejected Ideas

1. **Continuous Automorphic Representations of $GL_n (\mathbb{A})$**:
   *Rejected*: Infinite-dimensional representation theory over adele rings belongs in symbolic number theory software.
   AlgebraX models the finite, discrete combinatorial and spectral invariants.

---

## Open Questions

1. **Iwahori–Hecke Quadratic Relations**:
   Should we include a polynomial Hecke algebra generator $(T_i - q)(T_i + 1) = 0$? *Recommendation*: Yes, as an
   extension of Weyl group algebras.

---

## Change Log

- **2026-10-28**: Initial draft authored following Council consensus.
