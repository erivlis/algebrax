---
title: "EP-0205: Normed, Banach & Hilbert Spaces — Inner Products, RKHS & Contractions"
description: "Equip VectorSpace with metric geometry: vector and matrix p-norms, inner product spaces (finite-dimensional Hilbert spaces), Reproducing Kernel Hilbert Spaces (RKHS), and certified Banach contraction solvers."
icon: lucide/maximize-2
status: draft
---

# EP-0205: Normed, Banach & Hilbert Spaces — Inner Products, RKHS & Contractions

| Field             | Value                                                                 |
|:------------------|:----------------------------------------------------------------------|
| **EP**            | 0205                                                                  |
| **Title**         | Normed, Banach & Hilbert Spaces — Inner Products, RKHS & Contractions |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                           |
| **Sponsor**       | Core Maintainers                                                      |
| **Delegate**      | ⚡ Shannon (Sparse Norms) & 🔬 Popper (Cauchy-Schwarz Invariants)     |
| **Status**        | Draft                                                                 |
| **Type**          | Standards Track                                                       |
| **Created**       | 2026-10-28                                                            |
| **Updated**       | 2026-10-28                                                            |
| **Replaces**      | —                                                                     |
| **Superseded-By** | —                                                                     |

---

## Abstract

This proposal equips AlgebraX's `VectorSpace` protocol hierarchy (`algebrax.algebra._module`) with metric, geometric,
and functional analysis structures. EP-0205 establishes:

1. **Normed Spaces (`NormedSpace[K, V]`)**: Vector spaces equipped with absolutely scalable, subadditive
   norms $\|v\| \ge 0$, implementing standard sparse vector $p$-norms ($L_1, L_2, L_\infty$) and matrix
   operator/Frobenius norms.
2. **Inner Product Spaces (`InnerProductSpace[K, V]`)**: Equipping vector spaces with positive-definite sesquilinear
   forms $\langle u, v \rangle$, realizing finite-dimensional **Hilbert Spaces** with induced Euclidean
   norms $\|u\| = \sqrt{\langle u, u \rangle}$, angles, and Gram–Schmidt orthogonalization.
3. **Reproducing Kernel Hilbert Spaces (RKHS)**: Positive-definite Mercer kernel functions $k (x, y)$ that implicitly
   define feature inner products, generating sparse Gram matrices for kernel PCA, kernel ridge regression, and spectral
   embeddings.
4. **Certified Banach Contraction Solvers**: Formalizing contractive operators $\|T (x) - T (y)\| \le \gamma \|x - y\|$
   ($\gamma < 1$), providing certified geometric convergence guarantees for AlgebraX's PageRank, Jacobi, and
   Bellman-Ford solvers.
5. **Executable Analytical Verification**: Multi-property tests in `algebrax.verification`: `verify_cauchy_schwarz`,
   `verify_triangle_inequality`, and `verify_contraction_constant`.

All norm and inner product operations run directly on AlgebraX's canonical unboxed dictionary carriers
(`dict[K, float]`), with zero heap overhead.

---

## Motivation

In Phase 6 ([EP-0191](EP-0191-rings-fields-modules-and-exact-solvers.md)), AlgebraX formalized the `VectorSpace[R, M]`
protocol. However, a bare vector space possesses purely linear structure without geometry:

- It has no concept of **length**, **size**, or **distance**.
- It has no concept of **angles**, **orthogonality**, or **projections**.
- It has no concept of **analytical convergence** or **contractive stability**.

In modern computational mathematics:

1. **Geometric Data Science**: Machine learning and signal processing rely heavily on **Reproducing Kernel Hilbert
   Spaces (RKHS)**, where non-linear patterns are mapped into linear inner products via Mercer
   kernels $k (x, y) = \langle \Phi (x), \Phi (y) \rangle_{\mathcal{H}}$.
2. **Algorithm Certification**: Iterative matrix solvers (e.g., PageRank random walks in `EP-0151`, path iteration over
   tropical semirings) are fundamentally **Banach Fixed-Point Contractions**. Without formalizing the norm contraction
   constant $\gamma < 1$, convergence is treated as a runtime heuristic rather than a mathematically certified
   guarantee.
3. **Finite Completeness**: In finite dimensions, every normed space is complete (Banach), and every inner product space
   is complete (Hilbert). Formalizing these protocols grounds AlgebraX's spectral and linear algebra tools in rigorous
   functional analysis without requiring infinite-dimensional measure theory.

---

## Rationale & Council Alignment

- **⚡ Shannon (Zero Bloat & Sparse Norm Efficiency)**:
  Rejects object-oriented function wrappers. Vector $p$-norms and inner products operate directly on sparse dictionaries
  via generator expressions (`sum(v * v for v in x.values())`).
- **🔬 Popper (Falsifiability & Analytical Invariants)**:
  Demands executable verification of fundamental inequalities:
    1. **Cauchy–Schwarz**: $|\langle u, v \rangle|^2 \le \langle u, u \rangle \langle v, v \rangle$.
    2. **Triangle Inequality**: $\|u + v\| \le \|u\| + \|v\|$.
    3. **Parallelogram Law**: $\|u + v\|^2 + \|u - v\|^2 = 2 (\|u\|^2 + \|v\|^2)$.
- **🧩 Russell (Taxonomy & Deductive Order)**:
  Cleanly stratifies the metric hierarchy:
  $$\text{VectorSpace} \subset \text{NormedSpace (Banach)} \subset \text{InnerProductSpace (Hilbert)}$$
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  Explains Hilbert spaces plainly: *"A vector space is just a room where you can stretch and add arrows. An inner
  product space is when you turn on the lights and give everyone a ruler and a protractor."*

---

## Specification

### 1. Atomic Mixins & Flat Normed Space Protocol (`src/algebrax/algebra/_mixins.py` & `src/algebrax/analysis/normed.py`)

In strict compliance with [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md) (**Law of Flat Protocol Composition**), we define two Layer 1 atomic mixins in `algebrax.algebra._mixins` (`HasNorm[V]` and `HasInner[R, V]`), and compose `NormedSpace[R, V]` and `InnerProductSpace[R, V]` flatly from Layer 1 mixins and `Protocol` (never inheriting from Layer 2 `VectorSpace` or `NormedSpace` protocols):

```python
from typing import Any, Protocol, TypeVar, runtime_checkable
from algebrax.algebra._mixins import HasAdd, HasNeg, HasScale, HasZero

R = TypeVar("R")
V = TypeVar("V")


class HasNorm(Protocol[V]):
    """Atomic operational mixin for structures equipped with a norm ||v|| >= 0."""

    def norm(self, v: V) -> float:
        r"""Compute the norm $\|v\| \ge 0$."""
        ...


class HasInner(Protocol[R, V]):
    """Atomic operational mixin for structures equipped with a scalar inner product <u, v>."""

    def inner(self, u: V, v: V) -> R:
        r"""Compute inner product $\langle u, v \rangle \in R$."""
        ...


@runtime_checkable
class NormedSpace(HasZero[V], HasAdd[V], HasNeg[V], HasScale[R, V], HasNorm[V], Protocol):
    r"""A vector space $V$ over field $R$ equipped with a norm $\|\cdot\| : V \to \mathbb{R}_{\ge 0}$."""

    def sub(self, a: V, b: V) -> V:
        return self.add(a, self.neg(b))

    def distance(self, u: V, v: V) -> float:
        r"""Induced metric distance $d(u, v) = \|u - v\|_V$."""
        return self.norm(self.sub(u, v))
```

### 2. Standard Sparse $p$-Norms (`src/algebrax/analysis/normed.py`)

```python
import math
from algebrax.typing import SparseMatrix, SparseVector


def norm_p(vec: SparseVector[Any, float], p: float = 2.0) -> float:
    r"""Compute sparse vector $L_p$ norm: $\|x\|_p = \left( \sum |x_i|^p \right)^{1/p}$."""
    if p == float("inf"):
        return max((abs(v) for v in vec.values()), default=0.0)
    if p == 1.0:
        return sum(abs(v) for v in vec.values())
    if p == 2.0:
        return math.sqrt(sum(v * v for v in vec.values()))
    return math.pow(sum(abs(v) ** p for v in vec.values()), 1.0 / p)


def norm_frobenius(mat: SparseMatrix[Any, float]) -> float:
    r"""Compute matrix Frobenius norm $\|A\|_F = \sqrt{\sum A_{ij}^2}$."""
    return math.sqrt(sum(val * val for row in mat.values() for val in row.values()))
```

### 3. Flat Inner Product Space Protocol (`src/algebrax/analysis/normed.py`)

```python
@runtime_checkable
class InnerProductSpace(
    HasZero[V], HasAdd[V], HasNeg[V], HasScale[R, V], HasNorm[V], HasInner[R, V], Protocol
):
    r"""An inner product space (finite-dimensional Hilbert space) $\langle R, V, \langle \cdot, \cdot \rangle \rangle$."""

    def sub(self, a: V, b: V) -> V:
        return self.add(a, self.neg(b))

    def norm(self, v: V) -> float:
        r"""Induced Euclidean norm $\|v\| = \sqrt{\langle v, v \rangle}$."""
        return math.sqrt(float(self.inner(v, v)))  # type: ignore[arg-type]

    def distance(self, u: V, v: V) -> float:
        return self.norm(self.sub(u, v))
```

### 4. Reproducing Kernel Hilbert Spaces (RKHS) (`src/algebrax/analysis/rkhs.py`)

```python
from collections.abc import Callable


class ReproducingKernelHilbertSpace:
    r"""RKHS defined by a positive-definite Mercer kernel $k : \mathcal{X} \times \mathcal{X} \to \mathbb{R}$."""

    def __init__(self, kernel_fn: Callable[[Any, Any], float]) -> None:
        self.kernel_fn = kernel_fn

    def build_gram_matrix(self, samples: list[Any]) -> SparseMatrix[int, float]:
        r"""Assemble the sparse positive semi-definite Gram matrix $K_{ij} = k(x_i, x_j)$."""
        gram: SparseMatrix[int, float] = {}
        n = len(samples)
        for i in range(n):
            for j in range(i, n):
                val = self.kernel_fn(samples[i], samples[j])
                if abs(val) > 1e-12:
                    gram.setdefault(i, {})[j] = val
                    if i != j:
                        gram.setdefault(j, {})[i] = val
        return gram
```

### 5. Certified Banach Contraction Solvers (`src/algebrax/analysis/contraction.py`)

```python
class BanachContractionVerifier:
    r"""Certifies that operator $T : V \to V$ is a contraction with Lipschitz constant $\gamma < 1$."""

    def __init__(self, normed_space: NormedSpace[R, V], gamma: float) -> None:
        if not (0.0 <= gamma < 1.0):
            raise ValueError(f"Contraction constant must satisfy 0 <= gamma < 1, got {gamma}")
        self.space = normed_space
        self.gamma = gamma

    def verify_step(self, operator: Callable[[V], V], u: V, v: V) -> bool:
        r"""Verify $\|T(u) - T(v)\| \le \gamma \|u - v\|$."""
        dist_in = self.space.distance(u, v)
        dist_out = self.space.distance(operator(u), operator(v))
        return dist_out <= (self.gamma * dist_in + 1e-9)
```

---

## Backwards Compatibility

1. **Flat Protocol Composition (EP-0194)**:
   `NormedSpace` and `InnerProductSpace` are flat compositions of Layer 1 atomic mixins (`HasZero`, `HasAdd`, `HasNeg`, `HasScale`, `HasNorm`, `HasInner`) + `Protocol`, structurally compatible with `VectorSpace` without multi-level protocol inheritance.
2. **Seamless Solver Bridge**:
   Existing solvers (`pagerank`, `bellman_ford`) remain unchanged, with `BanachContractionVerifier` available as an opt-in formal correctness validator.

---

## How to Teach This / Documentation Plan

1. **Applied Guide (`docs/guides/norms-hilbert-and-kernels.md`)**:
    - Guide to vector and matrix norms in sparse computation.
    - Using RKHS Mercer kernels to perform non-linear classification via sparse linear solvers.
    - Certifying PageRank convergence rates using the Banach contraction principle.

---

## Reference Implementation

Prototypes of `norm_p`, `InnerProductSpace`, and `BanachContractionVerifier` were tested in Council exploration
`references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md`.

---

## Rejected Ideas

1. **Infinite-Dimensional Function Spaces ($L^2$, Sobolev $H^s$)**:
   *Rejected*: AlgebraX operates strictly on finite-dimensional discrete structures. Continuous measure theory belongs
   in symbolic engines.

---

## Open Questions

1. **Complex Inner Products**:
   Should `inner(u, v)` enforce conjugate-symmetry $\langle u, v \rangle = \overline{\langle v, u \rangle}$
   automatically for complex carriers? *Recommendation*: Yes, using `complex.conjugate()` when $K$ is complex.

---

## Change Log

- **2026-10-28**: Initial draft authored following Council consensus.
