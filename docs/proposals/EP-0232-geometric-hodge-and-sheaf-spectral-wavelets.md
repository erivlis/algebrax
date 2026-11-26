---
title: "EP-0232: Geometric, Simplicial Hodge & Cellular Sheaf Spectral Wavelets"
description: "Introduce Graph, Simplicial Hodge, and Cellular Sheaf Fourier transforms alongside matrix-free Chebyshev polynomial spectral wavelets in algebrax.transforms and algebrax.topology."
icon: lucide/activity
status: draft
---

# EP-0232: Geometric, Simplicial Hodge & Cellular Sheaf Spectral Wavelets

| Field             | Value                                                                                          |
|:------------------|:-----------------------------------------------------------------------------------------------|
| **EP**            | 0232                                                                                           |
| **Title**         | Geometric, Simplicial Hodge & Cellular Sheaf Spectral Wavelets                                 |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                    |
| **Sponsor**       | Core Maintainers                                                                               |
| **Delegate**      | ⚡ Shannon (Matrix-Free Chebyshev Recurrence), ⚖️ Noether (Hodge Spectral Bands) & 🔬 Popper    |
| **Status**        | Draft                                                                                          |
| **Type**          | Standards Track                                                                                |
| **Created**       | 2026-11-14                                                                                     |
| **Updated**       | 2026-11-26                                                                                     |
| **Replaces**      | —                                                                                              |
| **Superseded-By** | —                                                                                              |

---

## Abstract

This proposal bridges [`algebrax.transforms`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/transforms.py) with the topological Laplacians of Phase 4 ([`EP-0152`](EP-0152-spectral-graph-theory-laplacian.md), [`EP-0160`](EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md), [`EP-0161`](EP-0161-cellular-sheaves-and-network-laplacians.md)), introducing **Geometric, Simplicial Hodge, and Cellular Sheaf Harmonic Analysis**:

1. **Matrix-Free Chebyshev Polynomial Spectral Filtering (`chebyshev_spectral_filter`)**:
   Evaluates any spectral filter $g(\mathcal{L})f \approx \frac{1}{2}c_0 f + \sum_{k=1}^K c_k T_k(\tilde{\mathcal{L}})f$ on any positive semidefinite sparse Laplacian $\mathcal{L}$ (Graph $L_0$, Hodge $L_k$, or Sheaf $L_{\mathcal{F}}$) via the 3-term Chebyshev recurrence $T_k(\tilde{\mathcal{L}})f = 2\tilde{\mathcal{L}}T_{k-1}(\tilde{\mathcal{L}})f - T_{k-2}(\tilde{\mathcal{L}})f$ using **only $K$ sparse matrix-vector multiplications** (zero $O(N^3)$ eigendecomposition required).
2. **Hammond–Vandergheynst–Gribonval Spectral Graph & Sheaf Wavelets (`spectral_wavelet_transform`)**:
   Constructs multiscale wavelet frames $\{T_g^{t_s} \delta_v\}$ localized at vertices, edges, or sheaf stalks across scales $t_1, \dots, t_S$.
3. **Simplicial Hodge Fourier Transform (`hodge_fourier_transform`, `hodge_spectral_filter`)**:
   Decomposes $k$-cochain signals (such as edge flows on networks and simplicial meshes) into three orthogonal spectral bands governed by $L_k = L_k^{\text{down}} + L_k^{\text{up}} = \partial_k^* \partial_k + \partial_{k+1}\partial_{k+1}^*$:
   - **Harmonic Zero-Modes ($\lambda = 0$, $\ker L_k$)**: Topological holes counted by Betti number $b_k$.
   - **Irrotational / Gradient Frequencies ($\operatorname{im} \partial_k^*$)**: Modes excited solely by $L_k^{\text{down}}$.
   - **Solenoidal / Curl Frequencies ($\operatorname{im} \partial_{k+1}$)**: Modes excited solely by $L_k^{\text{up}}$.

---

## Motivation

In Phase 4, AlgebraX introduced the Graph Laplacian (`laplacian_matrix`), the $k$-th Hodge Laplacian (`hodge_laplacian` in [`EP-0160`](EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md)), and the Sheaf Coboundary Laplacian (`sheaf_laplacian` in [`EP-0161`](EP-0161-cellular-sheaves-and-network-laplacians.md)). However:

1. **No Spectral Transform or Wavelet Layer**: Users can compute the Laplacian matrix $\mathcal{L}$, but there is no API to transform signals into the Laplacian frequency domain, design low-pass / band-pass / heat-diffusion spectral filters $g(\mathcal{L})f$, or compute localized graph/simplicial wavelets.
2. **Avoiding $O(N^3)$ Full Eigendecomposition on Sparse Complexes**: Diagonalizing a Laplacian of size $N$ costs $O(N^3)$ time and $O(N^2)$ dense memory. By contrast, Hammond, Vandergheynst & Gribonval ([HAMMOND-2009]) showed that Chebyshev polynomial approximation $T_k(\tilde{\mathcal{L}})f$ requires **only sparse dictionary matrix-vector products**, running **60x faster** (`0.24 ms` vs. `14.42 ms` with `1.80e-09` relative accuracy in [`EXP-0010`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/README.md) Experiment 4).
3. **Joint curl/divergence Filtering on Edge Flows**: Standard graph signal processing only filters node signals ($L_0$). On edge flows ($1$-cochains), a filter $g_{\text{grad}}(L_1^{\text{down}}) + g_{\text{curl}}(L_1^{\text{up}}) + g_{\text{harm}}(P_{\ker L_1})$ can independently smooth gradient noise while preserving solenoidal vortices and harmonic cycles.

---

## Rationale

Validated in [**EXP-0010**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/README.md) (Experiment 4) and aligned with the Grand Council and **Phase 8.5 (`EP-0251`–`EP-0254`)**:

- **⚡ Claude Shannon (Matrix-Free Sparse Clenshaw/Chebyshev Recurrence & $O(\text{nnz})$ Hot Paths)**:
  Operates directly on AlgebraX's unboxed `SparseMatrix[K, float]` and `SparseVector[K, float]` via `algebrax.matrix.mat_vec`, directly benefiting from [`EP-0251`](EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md)'s $O(N^2) \to O(\text{nnz})$ `mat_vec`/`inner` optimization, single-rebuild `SimplicialComplex`, `CellularSheaf` `tol` forwarding, and corrected sparse-zero semantics in `gradient`/`laplacian`.
- **⚖️ Emmy Noether (Hodge Orthogonality $L_k^{\text{down}} L_k^{\text{up}} = \mathbf{0}$ & Semiring Propagation)**:
  Because $\partial_k \circ \partial_{k+1} = 0$, the lower and upper Hodge Laplacians commute and annihilate each other ($L_k^{\text{down}} L_k^{\text{up}} = 0$), allowing independent polynomial filtering of gradient and curl frequency spectra. Builds on [`EP-0251`](EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md)'s `RectSparseMatrix` rectangular incidence operators and [`EP-0252`](EP-0252-universal-semiring-propagation-and-domain-unification.md)'s semiring-propagating `SparseChainComplex.hodge_laplacian`.
- **🔬 Karl Popper (Parseval Energy & Chebyshev Convergence Oracles)**:
  Verifies that Chebyshev polynomial filters converge exponentially to exact spectral functions $g(\mathcal{L})f$ and that the Graph/Hodge Fourier Transform is an orthogonal isometry preserving inner products $\langle f, h \rangle = \langle \hat{f}, \hat{h} \rangle$, adhering to `EP-0253` non-vacuous sample contracts and `NaN != NaN` equality guards.
- **🛡️ The Golem (Explicit Laplacian Semantics & State Safety)**:
  Respects `EP-0254`'s explicit `is_laplacian` parameter on `laplacian_smoothing` (eliminating signed-weight guesswork) and `EP-0252`'s defensive copies on `SparseChainComplex`.
- **💡 Richard Feynman (The Freshman Test)**:
  *"How do you build a wavelet on an irregular network where you can't just 'stretch' $x \to x/s$? You let a drop of heat diffuse across the edges using the Laplacian $e^{-tL}$, and take the difference between two time scales—and with Chebyshev polynomials, you just hop from neighbor to neighbor $K$ times without ever finding a single eigenvalue!"*

---

## Specification

### 1. Fast Chebyshev Polynomial Spectral Filter & Wavelets (`src/algebrax/harmonic/spectral.py`)

```python
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from algebrax.typing import SparseMatrix, SparseVector

K = TypeVar("K")


def chebyshev_coefficients(
    kernel_fn: Callable[[float], float],
    lambda_max: float,
    order: int = 12,
) -> tuple[float, ...]:
    r"""Compute Gauss–Chebyshev quadrature coefficients $(c_0, c_1, \dots, c_K)$ of $g(\lambda)$ on $[0, \lambda_{\max}]$."""
    ...


def chebyshev_spectral_filter(
    laplacian: SparseMatrix[K, float],
    signal: SparseVector[K, float],
    kernel_fn: Callable[[float], float],
    *,
    lambda_max: float | None = None,
    order: int = 12,
) -> dict[K, float]:
    r"""Apply spectral filter $g(\mathcal{L})\,f \approx \frac{1}{2}c_0 f + \sum_{k=1}^K c_k T_k(\tilde{\mathcal{L}})f$ using sparse matrix-vector products.

    Works polymorphically on Graph Laplacians ($L_0$), Simplicial Hodge Laplacians ($L_k$),
    and Cellular Sheaf Laplacians ($L_{\mathcal{F}}$) without eigendecomposition.
    """
    ...


def spectral_wavelet_transform(
    laplacian: SparseMatrix[K, float],
    signal: SparseVector[K, float],
    scales: Sequence[float],
    *,
    wavelet_kernel: Callable[[float], float] | None = None,
    scaling_kernel: Callable[[float], float] | None = None,
    lambda_max: float | None = None,
    order: int = 12,
) -> dict[int | str, dict[K, float]]:
    r"""Compute the Hammond–Vandergheynst–Gribonval multiscale spectral wavelet transform $\{T_g^{t_s} f\}$."""
    ...
```

### 2. Graph & Simplicial Hodge Spectral Transforms (`src/algebrax/harmonic/hodge_ft.py`)

```python
def hodge_spectral_filter(
    lower_laplacian: SparseMatrix[K, float],
    upper_laplacian: SparseMatrix[K, float],
    cochain: SparseVector[K, float],
    *,
    grad_kernel: Callable[[float], float],
    curl_kernel: Callable[[float], float],
    harmonic_gain: float = 1.0,
    lambda_max: float | None = None,
    order: int = 12,
) -> dict[K, float]:
    r"""Filter a $k$-cochain independently across gradient ($\operatorname{im}\partial_k^*$), curl ($\operatorname{im}\partial_{k+1}$), and harmonic ($\ker L_k$) bands."""
    ...
```

### 3. Verification Oracles (`src/algebrax/verification/`)

Exported publicly via `algebrax.verification` (complying with Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts):

- `verify_chebyshev_spectral_filter(laplacian, signal, kernel_fn)`:
  1. Verifies that for any polynomial kernel $p(\lambda)$ of degree $d \le K$, `chebyshev_spectral_filter(L, f, p, order=K)` matches exact matrix polynomial evaluation $p(L)f$ to machine precision (`< 1e-12`).
  2. Verifies Hodge band annihilation: applying `hodge_spectral_filter` with `grad_kernel=0, harmonic_gain=0` produces a purely solenoidal cochain in $\ker \partial_k$.

---

## Backwards Compatibility

Strictly additive. Introduces `chebyshev_spectral_filter`, `spectral_wavelet_transform`, and `hodge_spectral_filter` and re-exports them through `algebrax.transforms` and `algebrax.topology`.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add a spectral wavelets & Hodge filtering guide in `docs/guide/topology/spectral_wavelets.md` and cross-link from `docs/guide/transforms/spectral.md`.
- **Recipe**: Add `recipes/simplicial_hodge_wavelet_denoising.py` (and synced `.ipynb`) demonstrating vortex-preserving edge-flow denoising on a 2D mesh with holes.

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0010-generalized-harmonic-analysis/sources/prototype_harmonic_analysis.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/sources/prototype_harmonic_analysis.py) (Experiment 4).

---

## Rejected Ideas

1. **Requiring `scipy.sparse.linalg.eigsh` for All Graph/Hodge Filtering**:
   - *Rejected*: Violates the zero-heavy-dependency pure-Python mandate and is unnecessary when Chebyshev polynomial recurrence evaluates $g(\mathcal{L})f$ directly via sparse `dict` matrix-vector products.

---

## Open Questions

- [ ] Adding Gershgorin circle theorem bounds (`estimate_lambda_max(laplacian)`) as the default `lambda_max` estimator when `lambda_max=None`.

---

## Change Log

* **2026-11-14:**
  * Initial Draft authored for Phase 10 from `EXP-0010`.
* **2026-11-26:**
  * Aligned with Phase 8.5 (`EP-0251`–`EP-0254`): fixed broken symbols (`graph_laplacian` → `laplacian_matrix`, `algebrax.matrix.multiply` → `algebrax.matrix.mat_vec`), documented $O(\text{nnz})$ `mat_vec` & semiring `hodge_laplacian`/`RectSparseMatrix` integration, updated verification path to `src/algebrax/verification/`, and fixed user guide path to `docs/guide/transforms/spectral.md`.
