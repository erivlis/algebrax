---
title: "EP-0211: Lie Algebra Representations, Weights & Clebsch–Gordan Tensors"
description: "Formalize Lie algebra representations, highest-weight modules, weight space decompositions, quadratic Casimir operators, and sparse Clebsch–Gordan 3-tensors."
icon: lucide/orbit
status: draft
---

# EP-0211: Lie Algebra Representations, Weights & Clebsch–Gordan Tensors

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0211                                                                              |
| **Title**         | Lie Algebra Representations, Weights & Clebsch–Gordan Tensors                     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | ⚖️ Noether (Continuous Symmetries) & ⚡ Shannon (Sparse Coupling Tensors)          |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-10-28                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational framework for **Lie Algebra Representations** in AlgebraX, formalizing infinitesimal symmetries and quantum angular momentum coupling over sparse matrix carriers. EP-0211 introduces:

1. **Lie Algebra Representation Protocol (`algebrax.lie.rep`)**:
   $$\rho : \mathfrak{g} \longrightarrow \mathfrak{gl}(V)$$
   mapping Lie generators $X \in \mathfrak{g}$ to sparse matrices satisfying the bracket homomorphism:
   $$\rho([X, Y]) = [\rho(X), \rho(Y)] = \rho(X)\rho(Y) - \rho(Y)\rho(X)$$
2. **Weight Spaces & Highest Weight Modules**:
   Decomposition of $V$ into simultaneous eigenspaces of the Cartan subalgebra $\mathfrak{h}$:
   $$V = \bigoplus_{\mu} V_\mu, \quad V_\mu = \{v \in V \mid \rho(H_i) v = \mu(H_i) v\}$$
   classified by highest weight vectors $v_\Lambda$ annihilated by all positive raising operators ($E_\alpha v_\Lambda = 0$).
3. **The Quadratic Casimir Operator**:
   Constructing the central invariant operator $C = \sum_i X_i X^i$ in the universal enveloping algebra $U(\mathfrak{g})$:
   $$[C, \rho(X)] = \mathbf{0}, \quad C|_{V_\Lambda} = \langle \Lambda, \Lambda + 2\delta \rangle \mathbf{I}$$
   providing an automated, certified check for irreducibility.
4. **Sparse Clebsch–Gordan Coupling 3-Tensors (`algebrax.tensor.coupling`)**:
   Exact representation of tensor product decompositions $V_{\lambda_1} \otimes V_{\lambda_2} \cong \bigoplus_\mu V_\mu$ as sparse 3-tensors $C_{m_1 m_2}^{j m}$ in `algebrax.tensor`.
5. **Property-Based Verification (`algebrax.verification.lie_rep`)**:
   Automated verification of Lie bracket preservation, Casimir commutativity, and Wigner-Eckart tensor transformation laws.

All operators are built directly on AlgebraX's unboxed sparse matrices (`algebrax.matrix.sparse`) and root system engine ([`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md)).

---

## Motivation

Lie algebras govern continuous symmetries throughout physics and geometry—from 3D spatial rotations ($\mathfrak{so}(3)$) and Lorentz boosts ($\mathfrak{so}(3, 1)$) to gauge theories ($\mathfrak{su}(2), \mathfrak{su}(3)$).

1. **Beyond Structure Constants**: [`EP-0163`](EP-0163-lie-algebras-and-bch-dynamics.md) and [`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md) established Lie algebra brackets and root systems. However, physics and geometric machine learning require representations acting on states (spinors, tensors, wavefunctions, and particle multiplets).
2. **Coupling Quantum Systems (Angular Momentum Addition)**: When two particles of spin $j_1$ and $j_2$ interact, their combined state space is the tensor product $V_{j_1} \otimes V_{j_2}$. The Clebsch–Gordan coefficients decouple this into irreducible spin states $|j, m\rangle$. Currently, AlgebraX lacks sparse coupling tensor mechanics.
3. **Casimir Invariant Eigenvalues**: In spectral analysis and graph quantum mechanics, the Casimir eigenvalue $\lambda_C = j(j+1)$ classifies energy levels and invariant laplacians on symmetric spaces.

---

## Rationale & Council Alignment

- **⚖️ Noether (Continuous Symmetries & Invariant Charges)**:
  Lie algebra representations represent the differential generators of Noether charges. The Casimir operator provides the central conserved quantity (total angular momentum $J^2$, color Casimir $C_2$).
- **⚡ Shannon (Zero Bloat & Sparse 3-Tensors)**:
  Clebsch–Gordan coefficients are notoriously sparse: selection rules force $m = m_1 + m_2$ and $|j_1 - j_2| \le j \le j_1 + j_2$. Storing them as unboxed sparse dictionary 3-tensors `{(j, m1, m2): val}` eliminates the $O(d_1^2 d_2^2)$ memory explosion of dense arrays.
- **🔬 Popper (Falsifiable Invariants)**:
  Every representation must satisfy:
  - $\rho([X, Y]) - (\rho(X)\rho(Y) - \rho(Y)\rho(X)) = \mathbf{0}$.
  - $[C, \rho(X)] = \mathbf{0}$ for all generators $X$.
  - Casimir scalar eigenvalue matches Freudenthal's formula: $\lambda_C = \langle \Lambda, \Lambda + 2\delta \rangle$.
- **🧩 Russell (Taxonomy & Functorial Action)**:
  Positions Lie algebra representation as a Lie algebra homomorphism $\mathfrak{g} \to \mathfrak{gl}(V)$, dual to group representation $\rho: G \to \mathrm{GL}(V)$ via the exponential map $\exp: \mathfrak{g} \to G$.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"Angular momentum addition is just matrix multiplication! Clebsch-Gordan coefficients are the change-of-basis matrix between the separate-spin world and the total-spin world."*

---

## Specification

### 1. Lie Algebra Representation Protocol (`src/algebrax/lie/rep.py`)

```python
"""Lie algebra representation protocols and operators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, Sequence, TypeVar

from algebrax.lie.algebra import LieAlgebra
from algebrax.matrix import SparseMatrix

K = TypeVar("K")


class LieRepresentation(Protocol[K]):
    """Protocol for a linear representation of a Lie algebra g on K^d."""

    @property
    def dimension(self) -> int:
        """Dimension of representation space V."""
        ...

    def __call__(self, generator_idx: int) -> SparseMatrix[K]:
        """Evaluate representation matrix rho(X_i)."""
        ...


@dataclass(frozen=True)
class ExplicitLieRep(Generic[K]):
    """Lie representation backed by a sequence of sparse generator matrices."""

    algebra: LieAlgebra
    generator_matrices: Sequence[SparseMatrix[K]]
    dimension: int

    def __call__(self, idx: int) -> SparseMatrix[K]:
        return self.generator_matrices[idx]
```

### 2. Standard Representations for $\mathfrak{sl}_2$ and $\mathfrak{so}_3$ (`src/algebrax/lie/spin.py`)

```python
"""Standard spin-j and adjoint representations."""

def spin_representation(j_halves: int) -> ExplicitLieRep[complex]:
    """Construct irreducible representation of sl_2 / su_2 of spin j = j_halves / 2.
    
    Dimension is 2j + 1. Generators are J_z, J_+, J_-.
    """
    ...

def adjoint_representation(algebra: LieAlgebra) -> ExplicitLieRep[float]:
    """Construct adjoint representation ad_X(Y) = [X, Y] of dimension dim(g)."""
    ...
```

### 3. Casimir Operator Construction (`src/algebrax/lie/casimir.py`)

```python
"""Quadratic Casimir invariant operators."""

from algebrax.lie.algebra import LieAlgebra
from algebrax.lie.rep import LieRepresentation
from algebrax.matrix import SparseMatrix


def quadratic_casimir(
    rep: LieRepresentation[K],
    killing_metric_inv: SparseMatrix[float],
) -> SparseMatrix[K]:
    """Compute quadratic Casimir operator C = sum_{i,j} g^{ij} rho(X_i) @ rho(X_j).
    
    By Schur's lemma, on an irreducible representation C is a scalar multiple of I.
    """
    ...
```

### 4. Sparse Clebsch–Gordan Coupling 3-Tensors (`src/algebrax/tensor/coupling.py`)

```python
"""Clebsch–Gordan coefficients and sparse coupling tensors."""

from algebrax.tensor import SparseTensor


def clebsch_gordan_tensor(j1_halves: int, j2_halves: int) -> SparseTensor[float]:
    """Compute sparse 3-tensor C_{m1, m2}^{(j, m)} coupling spins j1 and j2.
    
    Sparse keys are tuples: ((j, m), m1, m2) where m = m1 + m2.
    """
    ...
```

### 5. Verification Suite (`src/algebrax/verification/lie_rep.py`)

```python
"""Property-based verification for Lie algebra representations."""

def verify_lie_homomorphism(rep: LieRepresentation[K], algebra: LieAlgebra) -> bool:
    """Verify rho([X_i, X_j]) == rho(X_i) rho(X_j) - rho(X_j) rho(X_i)."""
    ...

def verify_casimir_commutativity(rep: LieRepresentation[K], algebra: LieAlgebra) -> bool:
    """Verify [C, rho(X_k)] == 0 for all generators X_k."""
    ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. Builds directly upon `algebrax.lie` ([`EP-0163`](EP-0163-lie-algebras-and-bch-dynamics.md), [`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md)) and `algebrax.tensor`.

---

## How to Teach This / Documentation Plan

- **Guide**: `guide/algebra/lie_representations.md`:
  - Spin-1/2, Spin-1, and Spin-3/2 quantum representations.
  - Adding angular momenta with Clebsch–Gordan tensors.
  - Verifying the Casimir eigenvalue formula $j(j+1)$.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for commutation relations and tensor selections.

---

## Reference Implementation

Prototype implementations will reside in `src/algebrax/lie/rep.py` and `src/algebrax/tensor/coupling.py`.

---

## Rejected Ideas

1. **Dense NumPy 3D Arrays for Clebsch-Gordan**:
   - *Rejected*: Dense arrays scale as $O((2j_1+1)(2j_2+1)(2(j_1+j_2)+1))$, wasting $>90\%$ of entries due to angular momentum selection rules ($m = m_1 + m_2$). Sparse dictionaries are vastly more efficient.
2. **Hardcoding $\mathfrak{su}(2)$ only**:
   - *Rejected*: Design must remain general for all semisimple Lie algebras ($\mathfrak{sl}_n, \mathfrak{so}_n, \mathfrak{sp}_n$) via root system weights.

---

## Open Questions

- [ ] Support for Kac-Moody affine Lie algebra highest weight modules in future extensions.
- [ ] Integration with Kostant's weight multiplicity formula using the Weyl character formula.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
