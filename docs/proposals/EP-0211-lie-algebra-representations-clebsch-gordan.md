---
title: "EP-0211: Lie Algebra Representations, Weights & Clebsch–Gordan Tensors"
description: "Formalize Lie algebra representations, highest-weight modules, weight space decompositions, quadratic Casimir operators, and sparse Clebsch–Gordan 3-tensors."
icon: lucide/orbit
status: final
---

# EP-0211: Lie Algebra Representations, Weights & Clebsch–Gordan Tensors

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0211                                                                              |
| **Title**         | Lie Algebra Representations, Weights & Clebsch–Gordan Tensors                     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | ⚖️ Noether (Continuous Symmetries) & ⚡ Shannon (Sparse Coupling Tensors)          |
| **Status**        | Final                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-11-22                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational framework for **Lie Algebra Representations** in AlgebraX, formalizing infinitesimal symmetries and quantum angular momentum coupling over sparse matrix carriers while building cleanly atop [`algebrax.lie`](EP-0163-lie-algebras-and-bch-dynamics.md) and [`algebrax.rep`](EP-0210-group-representations-character-tables-schurs-lemma.md). EP-0211 introduces:

1. **Lie Algebra Representation Protocol (`algebrax.rep.lie`)**:
   $$\rho : \mathfrak{g} \longrightarrow \mathfrak{gl}(V)$$
   refining `algebra.LieAlgebraHom` and mapping Lie generators $X \in \mathfrak{g}$ to sparse matrices satisfying the bracket homomorphism:
   $$\rho([X, Y]) = [\rho(X), \rho(Y)] = \rho(X)\rho(Y) - \rho(Y)\rho(X)$$
   Explicitly delegates `adjoint_representation(g)` and `defining_representation(g)` to existing `LieAlgebra.adjoint_matrix` and `LieAlgebra.element_to_matrix` mechanics without duplication, and bridges to group representations via $\exp(\rho(X))$.
2. **Weight Spaces & Highest Weight Modules**:
   Decomposition of $V$ into simultaneous eigenspaces of the Cartan subalgebra $\mathfrak{h}$:
   $$V = \bigoplus_{\mu} V_\mu, \quad V_\mu = \{v \in V \mid \rho(H_i) v = \mu(H_i) v\}$$
   classified by highest weight vectors $v_\Lambda$ annihilated by all positive raising operators ($E_\alpha v_\Lambda = 0$).
3. **The Quadratic Casimir Operator (`algebrax.rep.lie`)**:
   Constructing the central invariant operator $C = \sum_{i,j} g^{ij} \rho(X_i)\rho(X_j)$ in the universal enveloping algebra $U(\mathfrak{g})$:
   $$[C, \rho(X)] = \mathbf{0}, \quad C|_{V_\Lambda} = \langle \Lambda, \Lambda + 2\delta \rangle \mathbf{I}$$
   providing an automated, certified check for irreducibility.
4. **Sparse Clebsch–Gordan Coupling 3-Tensors (`algebrax.tensor.coupling`)**:
   Exact representation of tensor product decompositions $V_{\lambda_1} \otimes V_{\lambda_2} \cong \bigoplus_\mu V_\mu$ as sparse 3-tensors $C_{m_1 m_2}^{j m}$ in `algebrax.tensor` (re-exported in `algebrax.rep.lie`).
5. **Property-Based Verification (`algebrax.verification`)**:
   Automated verification of Lie bracket preservation (`verify_lie_representation_homomorphism`), Casimir commutativity (`verify_casimir_commutativity`), and Wigner–Eckart tensor transformation laws in `src/algebrax/verification.py`.

All operators build directly on AlgebraX's unboxed sparse matrices (`algebrax.matrix`), [`LieAlgebra`](EP-0163-lie-algebras-and-bch-dynamics.md), and root system engine ([`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md)).

---

## Motivation

Lie algebras govern continuous symmetries throughout physics and geometry—from 3D spatial rotations ($\mathfrak{so}(3)$) and Lorentz boosts ($\mathfrak{so}(3, 1)$) to gauge theories ($\mathfrak{su}(2), \mathfrak{su}(3)$).

1. **Beyond Structure Constants**: [`EP-0163`](EP-0163-lie-algebras-and-bch-dynamics.md) and [`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md) established Lie algebra brackets (`LieAlgebra.adjoint_matrix`, `LieAlgebra.element_to_matrix`) and root systems. Physics and geometric machine learning require unifying these into representation objects with tensor products ($\rho_1 \otimes I + I \otimes \rho_2$), contragredient duals ($-\rho(X)^T$), intertwiners, and Casimir invariants.
2. **Coupling Quantum Systems (Angular Momentum Addition)**: When two particles of spin $j_1$ and $j_2$ interact, their combined state space is the tensor product $V_{j_1} \otimes V_{j_2}$. The Clebsch–Gordan coefficients decouple this into irreducible spin states $|j, m\rangle$. Currently, AlgebraX lacks sparse coupling tensor mechanics.
3. **Casimir Invariant Eigenvalues**: In spectral analysis and graph quantum mechanics, the Casimir eigenvalue $\lambda_C = j(j+1)$ classifies energy levels and invariant laplacians on symmetric spaces.

---

## Rationale & Council Alignment

- **⚖️ Noether (Continuous Symmetries & Invariant Charges)**:
  Lie algebra representations represent the differential generators of Noether charges. The Casimir operator provides the central conserved quantity (total angular momentum $J^2$, color Casimir $C_2$).
- **⚡ Shannon (Zero Bloat & Zero Duplication)**:
  Clebsch–Gordan coefficients are notoriously sparse: selection rules force $m = m_1 + m_2$ and $|j_1 - j_2| \le j \le j_1 + j_2$. Storing them as unboxed sparse dictionary 3-tensors `{(j, m1, m2): val}` eliminates dense $O(d_1^2 d_2^2)$ allocation, while housing Lie representation abstractions in `algebrax.rep.lie` shares sparse direct-sum, tensor-product, and intertwiner machinery with finite-group representations and delegates directly to `LieAlgebra`.
- **🔬 Popper (Falsifiable Invariants)**:
  Every representation must satisfy:
  - $\rho([X, Y]) - (\rho(X)\rho(Y) - \rho(Y)\rho(X)) = \mathbf{0}$.
  - $[C, \rho(X)] = \mathbf{0}$ for all generators $X$.
  - Casimir scalar eigenvalue matches Freudenthal's formula: $\lambda_C = \langle \Lambda, \Lambda + 2\delta \rangle$.
- **🧩 Russell (Taxonomy & Functorial Action)**:
  Positions `LieRepresentation` as a `LieAlgebraHom` $\mathfrak{g} \to \mathfrak{gl}(V)$, dual to `GroupRepresentation` $\rho: G \to \mathrm{GL}(V)$ (`GroupHom`) via the exponential map $\exp: \mathfrak{g} \to G$.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"Angular momentum addition is just matrix multiplication! Clebsch-Gordan coefficients are the change-of-basis matrix between the separate-spin world and the total-spin world."*

---

## Specification

### 1. Lie Algebra Representation Protocol & Standard Constructions (`src/algebrax/rep/lie.py`)

```python
"""Lie algebra representation protocols, spin-j modules, Casimir operators, and exp bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, Sequence, TypeVar, runtime_checkable

from algebrax.algebra._homomorphisms import LieAlgebraHom
from algebrax.lie import LieAlgebra
from algebrax.typing import SparseMatrix

K = TypeVar("K")


@runtime_checkable
class LieRepresentation(LieAlgebraHom[int, SparseMatrix[int, K]], Protocol[K]):
    """Protocol for a linear representation of a Lie algebra g on K^d."""

    @property
    def dimension(self) -> int:
        """Dimension of representation space V."""
        ...

    def __call__(self, generator_idx: int) -> SparseMatrix[int, K]:
        """Evaluate representation matrix rho(X_i)."""
        ...


@dataclass(frozen=True)
class ExplicitLieRep(Generic[K]):
    """Lie representation backed by sparse generator matrices (direct sum, tensor product, dual)."""

    algebra: LieAlgebra
    generator_matrices: Sequence[SparseMatrix[int, K]]
    dimension: int

    def __call__(self, idx: int) -> SparseMatrix[int, K]:
        return self.generator_matrices[idx]


def spin_representation(
    j_halves: int,
    *,
    form: Literal["su2", "sl2"] = "su2",
) -> ExplicitLieRep[complex]:
    """Construct irreducible representation of su(2) or sl(2) of spin j = j_halves / 2."""
    ...


def adjoint_representation(algebra: LieAlgebra) -> ExplicitLieRep[float | complex]:
    """Construct adjoint representation ad_X(Y) = [X, Y] delegating to algebra.adjoint_matrix."""
    ...


def defining_representation(
    algebra: LieAlgebra,
    dimension: int | None = None,
) -> ExplicitLieRep[float | complex]:
    """Wrap algebra.matrix_basis as an ExplicitLieRep."""
    ...


def weight_space_decomposition(
    rep: LieRepresentation[K],
    cartan_indices: Sequence[int],
    tol: float = 1e-9,
) -> dict[tuple[float | complex, ...], list[dict[int, float]]]:
    """Decompose V into simultaneous Cartan weight spaces V_mu."""
    ...


def highest_weight_vectors(
    rep: LieRepresentation[K],
    cartan_indices: Sequence[int],
    raising_indices: Sequence[int],
    tol: float = 1e-9,
) -> list[tuple[tuple[float | complex, ...], dict[int, float | complex]]]:
    """Find a basis of highest-weight vectors annihilated by all raising operators."""
    ...


def quadratic_casimir(
    rep: LieRepresentation[K],
    algebra: LieAlgebra | None = None,
    killing_metric_inv: SparseMatrix[int, float | complex] | None = None,
    tol: float = 1e-12,
) -> SparseMatrix[int, Any]:
    """Compute quadratic Casimir operator C = sum_{i,j} g^{ij} rho(X_i) @ rho(X_j)."""
    ...


def freudenthal_casimir_eigenvalue(
    root_system: RootSystem,
    highest_weight_dynkin: Sequence[int | float],
) -> float:
    """Compute Freudenthal's Killing-normalized Casimir eigenvalue <Lambda, Lambda + 2*delta>_K."""
    ...
```

(Ergonomically re-exported in `algebrax.lie` via PEP 562 lazy `__getattr__` for `adjoint_representation`, `defining_representation`, `spin_representation`, and `quadratic_casimir`.)

### 2. Sparse Clebsch–Gordan Coupling 3-Tensors (`src/algebrax/tensor/coupling.py`)

```python
"""Clebsch–Gordan coefficients, sparse 3-tensors, and orthogonal coupling matrices."""

from algebrax.typing import SparseMatrix


def clebsch_gordan_coefficient(
    j1_halves: int,
    m1_halves: int,
    j2_halves: int,
    m2_halves: int,
    j_halves: int,
    m_halves: int,
) -> float:
    """Compute a single Condon–Shortley coefficient <j1 m1; j2 m2 | j m> via exact rational Racah sum."""
    ...


def clebsch_gordan_tensor(
    j1_halves: int,
    j2_halves: int,
    tol: float = 1e-14,
) -> dict[tuple[tuple[int, int], int, int], float]:
    """Compute sparse 3-tensor C_{m1, m2}^{(j, m)} coupling spins j1 and j2.

    Sparse keys are integer half-spin tuples: ((j_halves, m_halves), m1_halves, m2_halves).
    """
    ...


def clebsch_gordan_matrix(
    j1_halves: int,
    j2_halves: int,
    tol: float = 1e-14,
) -> tuple[SparseMatrix[int, float], list[tuple[int, int]]]:
    """Build orthogonal change-of-basis matrix U intertwining V_{j1} (x) V_{j2} with direct sum of V_j."""
    ...
```

### 3. Verification Suite (`src/algebrax/verification.py`)

```python
"""Property-based verification for Lie algebra representations and Clebsch–Gordan coupling."""

def verify_lie_representation_homomorphism(
    rep: Any,
    algebra: Any = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify rho([X_i, X_j]) == [rho(X_i), rho(X_j)], antisymmetry, and Jacobi identity."""
    ...

def verify_casimir_commutativity(
    rep: Any,
    algebra: Any = None,
    killing_metric_inv: Any = None,
    expected_eigenvalue: float | complex | None = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify [C, rho(X_k)] == 0 for all generators and optional Schur/Freudenthal eigenvalue match."""
    ...

def verify_clebsch_gordan_coupling(
    j1_halves: int,
    j2_halves: int,
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify U^T U = U U^T = I, selection rules, and su(2) intertwiner equivariance."""
    ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. Builds directly upon `algebrax.lie` ([`EP-0163`](EP-0163-lie-algebras-and-bch-dynamics.md), [`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md)), `algebrax.rep`, and `algebrax.tensor` (promoted from a single module to a package while preserving all existing exports).

---

## How to Teach This / Documentation Plan

- **Guide**: `docs/guide/algebra/lie_representations.md` (registered in `zensical.toml` and cross-linked from `lie_algebras.md` and `representations.md`):
  - Spin-$1/2$, Spin-$1$, and Spin-$3/2$ quantum representations and the $SU(2) \to SO(3)$ double cover via `exp_map`.
  - Weight-space decompositions and highest-weight vectors for $\mathfrak{sl}(2)$ tensor products and $\mathfrak{sl}(3)$.
  - Quadratic Casimir operators, Freudenthal's eigenvalue formula (including $\mathfrak{g}_2$), and physics $J^2 = j(j+1)\mathbf{I}$.
  - Adding angular momenta with sparse Clebsch–Gordan tensors and orthogonal coupling matrices.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for commutation relations and tensor selection rules.

---

## Reference Implementation

- **Lie Representations, Weights, Casimir & Exp Bridge**: `src/algebrax/rep/lie.py` (re-exported from `src/algebrax/rep/__init__.py` and lazily from `src/algebrax/lie/__init__.py`).
- **Sparse Clebsch–Gordan Coupling Tensors**: `src/algebrax/tensor/coupling.py` (re-exported from `src/algebrax/tensor/__init__.py` and `src/algebrax/rep/lie.py`).
- **Verification Predicates**: `src/algebrax/verification.py` (`verify_lie_representation_homomorphism`, `verify_casimir_commutativity`, `verify_clebsch_gordan_coupling`).
- **Unit, Falsification & Differential Tests**: `tests/algebrax/test_rep_lie.py` and `tests/verifications/test_differential_sympy.py::test_differential_clebsch_gordan_and_lie_expm_vs_sympy_scipy`.
- **User Guide & Traceability**: `docs/guide/algebra/lie_representations.md` and `docs/verification.md`.

---

## Rejected Ideas

1. **Dense NumPy 3D Arrays for Clebsch-Gordan**:
   - *Rejected*: Dense arrays scale as $O((2j_1+1)(2j_2+1)(2(j_1+j_2)+1))$, wasting $>90\%$ of entries due to angular momentum selection rules ($m = m_1 + m_2$). Sparse dictionaries are vastly more efficient.
2. **Hardcoding $\mathfrak{su}(2)$ only**:
   - *Rejected*: Design must remain general for all semisimple Lie algebras ($\mathfrak{sl}_n, \mathfrak{so}_n, \mathfrak{sp}_n, \mathfrak{g}_2$) via root system weights and Killing forms.
3. **Separate Representation Plumbing Inside `algebrax/lie/`**:
   - *Rejected*: Creating `lie/rep.py`, `lie/spin.py`, `lie/casimir.py` as an isolated island would duplicate `direct_sum`, `tensor_product`, `dual`, and intertwiner logic already maintained in `algebrax.rep`, as well as duplicate `LieAlgebra.adjoint_matrix`.

---

## Open Questions

- [ ] Support for Kac-Moody affine Lie algebra highest weight modules in future extensions.
- [ ] Integration with Kostant's weight multiplicity formula using the Weyl character formula.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
* **2026-11-15:**
  * Aligned specification with unified `algebrax.rep.lie` + `algebrax.lie` re-exports, `LieAlgebraHom` refinement, delegation to existing `LieAlgebra.adjoint_matrix` / `element_to_matrix`, and `src/algebrax/verification.py`.
* **2026-11-22:**
  * Implemented `src/algebrax/rep/lie.py`, `src/algebrax/tensor/coupling.py`, `src/algebrax/verification.py` predicates, unit/falsification tests (`tests/algebrax/test_rep_lie.py`), SymPy/SciPy differential verification (`tests/verifications/test_differential_sympy.py`), and user guide (`docs/guide/algebra/lie_representations.md`). Transitioned status to Final.
