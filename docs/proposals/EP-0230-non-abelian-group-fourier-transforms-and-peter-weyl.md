---
title: "EP-0230: Non-Abelian Group Fourier Transforms, Peter–Weyl Duality & Equivariant Convolutions"
description: "Generalize harmonic analysis from 1D scalar characters to matrix-valued non-Abelian Group Fourier Transforms, Peter-Weyl inversion, Plancherel isometry, and group-equivariant convolutions."
icon: lucide/waves
status: draft
---

# EP-0230: Non-Abelian Group Fourier Transforms, Peter–Weyl Duality & Equivariant Convolutions

| Field             | Value                                                                                          |
|:------------------|:-----------------------------------------------------------------------------------------------|
| **EP**            | 0230                                                                                           |
| **Title**         | Non-Abelian Group Fourier Transforms, Peter–Weyl Duality & Equivariant Convolutions            |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                    |
| **Sponsor**       | Core Maintainers                                                                               |
| **Delegate**      | ⚖️ Noether (Peter–Weyl Duality), 🔬 Popper (Plancherel Oracles) & ⚡ Shannon (Block Spectra)    |
| **Status**        | Draft                                                                                          |
| **Type**          | Standards Track                                                                                |
| **Created**       | 2026-11-14                                                                                     |
| **Updated**       | 2026-11-14                                                                                     |
| **Replaces**      | —                                                                                              |
| **Superseded-By** | —                                                                                              |

---

## Abstract

This proposal generalizes [`algebrax.transforms.gelfand_transform`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/transforms.py) from 1-dimensional scalar characters to full **Matrix-Valued Non-Abelian Group Fourier Transforms** over the irreducible matrix representations introduced in [`EP-0210`](EP-0210-group-representations-character-tables-schurs-lemma.md). Specifically, EP-0230 introduces:

1. **Non-Abelian Group Fourier Transform (`group_fourier_transform`)**:
   Evaluates a sparse group signal $f \in \mathbb{C}[G]$ (`dict[G, complex]`) at a complete family of unitary irreducible matrix representations $\widehat{G} = \{\rho_\lambda: G \to \operatorname{GL}_{d_\lambda}(\mathbb{C})\}$:
   $$\hat{f}(\rho_\lambda) = \sum_{g \in G} f(g)\, \rho_\lambda(g) \in M_{d_\lambda}(\mathbb{C})$$
2. **Peter–Weyl Inversion (`inverse_group_fourier_transform`)**:
   Reconstructs $f: G \to \mathbb{C}$ from its block-matrix spectrum $\{\hat{f}(\rho_\lambda)\}_{\lambda \in \widehat{G}}$ via normalized matrix traces:
   $$f(g) = \frac{1}{|G|} \sum_{\lambda \in \widehat{G}} d_\lambda \operatorname{Tr}\!\left(\hat{f}(\rho_\lambda)\, \rho_\lambda(g^{-1})\right)$$
3. **Spectral Group Convolution & Plancherel Isometry (`group_spectral_convolve`, `plancherel_inner_product`)**:
   Realizes the **Peter–Weyl Algebra Isomorphism** $\mathbb{C}[G] \cong \bigoplus_{\lambda \in \widehat{G}} M_{d_\lambda}(\mathbb{C})$, converting non-commutative group convolution $(f * h)(g) = \sum_{u \in G} f(u)h(u^{-1}g)$ into independent block-matrix multiplications $\hat{f}(\rho_\lambda) \cdot \hat{h}(\rho_\lambda)$.
4. **Diaconis Markov Mixing & Bispectral Invariants (`diaconis_upper_bound_lemma`, `group_bispectrum`)**:
   Computes $k$-step random-walk distributions $P^{*k}$ on finite groups (such as card-shuffling walks on $S_n$) via matrix powers $\hat{P}(\rho_\lambda)^k$, along with translation-invariant skew/bispectral invariants.

---

## Motivation

In [`src/algebrax/transforms.py`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/transforms.py), `gelfand_transform(signal, characters)` evaluates a sparse signal against scalar functions $\chi: G \to \mathbb{C}$. While this suffices for **Abelian** groups (where every irreducible representation is 1-dimensional, e.g., $\mathbb{Z}/N\mathbb{Z}$ for `dft` and $(\mathbb{Z}/2\mathbb{Z})^n$ for `walsh_hadamard`), it fails fundamentally on **Non-Abelian** groups ($S_n, D_n, A_n, \operatorname{SL}_2(\mathbb{F}_p)$):

1. **Empirical Falsification of Scalar Characters on $S_3$ ([`EXP-0010`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/README.md) Experiment 1)**:
   Irreducible characters $\chi_\lambda(g) = \operatorname{Tr}(\rho_\lambda(g))$ are class functions ($\chi_\lambda(hgh^{-1}) = \chi_\lambda(g)$). Consequently, two distinct signals $f_1 \ne f_2 \in \mathbb{C}[S_3]$ supported on different transpositions $(12)$ vs. $(23)$ produce **100% identical scalar Gelfand spectra** `{'triv': 2.5, 'sign': -1.5, 'std': 2.5}`, losing $d_\lambda^2 - 1 = 3$ degrees of freedom on the 2D standard representation and making signal inversion impossible.
2. **Unlocking Phase 8 Representation Theory for Signal Processing & Machine Learning**:
   [`EP-0210`](EP-0210-group-representations-character-tables-schurs-lemma.md) and [`EP-0213`](EP-0213-induced-representations-and-frobenius-reciprocity.md) provide `GroupRepresentation[G, V]`. Pairing `GroupRepresentation` with `algebrax.transforms` immediately unlocks **Diaconis's spectral analysis of permutations/rankings** and **Group-Equivariant Neural Convolutions (`G-CNN`s)** (Kondor & Trivedi 2018).

---

## Rationale

Validated in [**EXP-0010**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/README.md) (Experiment 1) and aligned with the Grand Council:

- **⚖️ Emmy Noether (The Peter–Weyl Isomorphism & Plancherel Conservation)**:
  Restores the exact duality between a group algebra $\mathbb{C}[G]$ (`MonoidAlgebra`) and its dual representation category $\widehat{G}$:
  $$\sum_{g \in G} |f(g)|^2 = \frac{1}{|G|} \sum_{\lambda \in \widehat{G}} d_\lambda \|\hat{f}(\rho_\lambda)\|_F^2$$
- **⚡ Claude Shannon (Block-Diagonal Spectral Compression)**:
  Convolving two signals on a group $G$ of order $|G|$ costs $O(|G|^2)$ directly, whereas in the Peter–Weyl basis it decomposes into independent $d_\lambda \times d_\lambda$ matrix multiplications of total cost $\sum_\lambda d_\lambda^3 \ll |G|^2$, and $k$-step Markov chain convolution $P^{*k}$ reduces to $O(\log k)$ binary matrix exponentiation $\hat{P}(\rho_\lambda)^k$.
- **🔬 Karl Popper (Falsifiable Inversion, Convolution & Parseval Oracles)**:
  Every non-Abelian Fourier transform is verified against three exact laws (`0.00e+00` residual on $S_3$ in `EXP-0010`): inversion identity, non-commutative convolution homomorphism, and Plancherel energy equality.
- **💡 Richard Feynman (The Freshman Test)**:
  *"On a circle, shifting a wave only changes its phase, so frequencies are single complex numbers $e^{i\omega t}$. On a non-commutative group like triangle symmetries $S_3$, flipping and rotating don't commute—so each 'frequency' $\rho_\lambda$ is a tiny matrix, and multiplying Fourier coefficients is just matrix multiplication!"*

---

## Specification

### 1. Non-Abelian Group Fourier Transform & Peter–Weyl Inversion (`src/algebrax/transforms.py` / `src/algebrax/harmonic/group_ft.py`)

```python
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeVar

from algebrax.representation import GroupRepresentation
from algebrax.typing import SparseMatrix, SparseVector

G = TypeVar("G")
IrrepId = TypeVar("IrrepId")


def group_fourier_transform(
    signal: SparseVector[G, complex],
    irreps: Mapping[IrrepId, GroupRepresentation[G, complex]],
) -> dict[IrrepId, SparseMatrix[int, complex]]:
    r"""Compute the Non-Abelian Group Fourier Transform $\hat{f}(\rho_\lambda) = \sum_{g \in G} f(g)\,\rho_\lambda(g)$.

    Algebraic Signature:
        $\mathcal{F}_G: \mathbb{C}[G] \xrightarrow{\sim} \bigoplus_{\lambda \in \widehat{G}} M_{d_\lambda}(\mathbb{C})$
    """
    ...


def inverse_group_fourier_transform(
    spectrum: Mapping[IrrepId, SparseMatrix[int, complex]],
    group_elements: Sequence[G],
    irreps: Mapping[IrrepId, GroupRepresentation[G, complex]],
) -> dict[G, complex]:
    r"""Reconstruct $f(g) = \frac{1}{|G|} \sum_{\lambda \in \widehat{G}} d_\lambda \operatorname{Tr}\!\left(\hat{f}(\rho_\lambda)\,\rho_\lambda(g^{-1})\right)$."""
    ...


def group_spectral_convolve(
    f: SparseVector[G, complex],
    h: SparseVector[G, complex],
    group_elements: Sequence[G],
    irreps: Mapping[IrrepId, GroupRepresentation[G, complex]],
) -> dict[G, complex]:
    r"""Compute non-commutative group convolution $f * h \in \mathbb{C}[G]$ via Peter–Weyl block-matrix multiplication."""
    ...


def plancherel_energy(
    spectrum: Mapping[IrrepId, SparseMatrix[int, complex]],
    group_order: int,
    irrep_dims: Mapping[IrrepId, int],
) -> float:
    r"""Compute spectral Plancherel energy $\frac{1}{|G|} \sum_{\lambda \in \widehat{G}} d_\lambda \|\hat{f}(\rho_\lambda)\|_F^2$."""
    ...
```

### 2. Diaconis Spectral Random-Walk Mixing & Equivariant Correlation (`src/algebrax/harmonic/group_ft.py`)

```python
def spectral_markov_walk(
    step_distribution: SparseVector[G, float],
    steps: int,
    group_elements: Sequence[G],
    irreps: Mapping[IrrepId, GroupRepresentation[G, complex]],
) -> dict[G, float]:
    r"""Compute the $k$-step Markov distribution $P^{*k}$ on $G$ via spectral matrix powers $\hat{P}(\rho_\lambda)^k$."""
    ...


def diaconis_upper_bound(
    step_distribution: SparseVector[G, float],
    steps: int,
    group_order: int,
    non_trivial_irreps: Mapping[IrrepId, GroupRepresentation[G, complex]],
) -> float:
    r"""Evaluate the Diaconis–Shahshahani Upper Bound Lemma on Total Variation distance to uniformity:

    $$\|P^{*k} - U\|_{\mathrm{TV}}^2 \le \frac{1}{4} \sum_{\lambda \ne \mathrm{triv}} d_\lambda \operatorname{Tr}\!\left(\hat{P}(\rho_\lambda)^k \left(\hat{P}(\rho_\lambda)^k\right)^*\right)$$
    """
    ...
```

### 3. Verification Oracles (`src/algebrax/verification.py`)

- `verify_peter_weyl_laws(signal_a, signal_b, group, irreps)`:
  1. Verifies Burnside dimension sum $\sum_{\lambda \in \widehat{G}} d_\lambda^2 == |G|$.
  2. Verifies exact inversion `inverse_group_fourier_transform(group_fourier_transform(f, irreps)) == f`.
  3. Verifies non-Abelian convolution homomorphism `group_spectral_convolve(a, b) == group_algebra.mul(a, b)`.
  4. Verifies Plancherel energy conservation $\sum_{g \in G} |f(g)|^2 == \mathrm{plancherel\_energy}(\hat{f})$.

---

## Backwards Compatibility

100% backwards compatible. Existing `gelfand_transform` in `algebrax.transforms` remains unchanged for 1D character evaluations, while `group_fourier_transform` and `inverse_group_fourier_transform` extend `algebrax.transforms` to arbitrary matrix representations.

---

## How to Teach This / Documentation Plan

- **User Guide**: Expand `docs/guide/transforms.md` with a section on Non-Abelian Group Fourier Transforms ($S_3, D_4$) and why 1D characters collide on non-central signals.
- **Recipe**: Add `recipes/diaconis_card_shuffling_fourier.py` (and synced `.ipynb`) analyzing random transposition / riffle shuffles on $S_n$ via Peter–Weyl spectral decay.

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0010-generalized-harmonic-analysis/sources/prototype_harmonic_analysis.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/sources/prototype_harmonic_analysis.py) (Experiment 1).

---

## Rejected Ideas

1. **Overloading `gelfand_transform` to Return Mixed Scalar/Matrix Dicts**:
   - *Rejected*: Violates Golem type safety (`dict[C, complex]` vs. `dict[IrrepId, SparseMatrix[int, complex]]`). Keeping `gelfand_transform` typed for 1D characters and `group_fourier_transform` typed for matrix representations preserves static type clarity.

---

## Open Questions

- [ ] Adding Clausen's subgroup-chain FFT ($S_n \supset S_{n-1} \supset \dots \supset S_1$) using Young's Orthogonal Form from [`EP-0210`](EP-0210-group-representations-character-tables-schurs-lemma.md) for $n \ge 5$.

---

## Change Log

* **2026-11-14:**
  * Initial Draft authored for Phase 10 from `EXP-0010`.
