---
title: "EP-0162: Persistent Homology, Simplicial Filtrations & Topological Barcodes"
description: "Extends simplicial homology from static complexes to multiscale filtrations, persistence reduction over Z_2, birth-death intervals, Betti curves, and bottleneck distances."
icon: lucide/bar-chart-horizontal
status: draft
---

# EP-0162: Persistent Homology, Simplicial Filtrations & Topological Barcodes

| Field        | Value                                                                                                                       |
|:-------------|:----------------------------------------------------------------------------------------------------------------------------|
| **EP**       | 0162                                                                                                                        |
| **Title**    | Persistent Homology, Simplicial Filtrations & Topological Barcodes                                                          |
| **Author**   | Eran Rivlis & Antigravity (The Explorer)                                                                                    |
| **Sponsor**  | The Council                                                                                                                 |
| **Delegate** | 🔬 Karl Popper (Falsifiability), 🧭 The Explorer (Curiosity), ⚡ Claude Shannon (Efficiency) & 💡 Richard Feynman (Clarity) |
| **Status**   | Draft                                                                                                                       |
| **Type**     | Standards Track                                                                                                             |
| **Created**  | 2026-10-16                                                                                                                  |
| **Updated**  | 2026-10-16                                                                                                                  |
| **Replaces** | None                                                                                                                        |

---

## Abstract

This proposal introduces **Persistent Homology** and **Topological Data Analysis (TDA)** in `algebrax.homology`,
extending `SimplicialComplex` ([EP-0110](EP-0110-simplicial-homology.md)) from static single-scale Betti numbers to
multiscale filtrations $\emptyset = K_0 \subseteq K_1 \subseteq \dots \subseteq K_m = K$. Specifically, this proposal
introduces:

1. **`FilteredSimplicialComplex`**: A monotone filtration carrier associating each simplex $\sigma \in K$ with a
   filtration birth value $f (\sigma) \in \mathbb{R}$ satisfying the subcomplex monotonicity
   law $\tau \subseteq \sigma \implies f (\tau) \le f (\sigma)$, along with constructors for **Vietoris–Rips** distance
   filtrations (`from_vietoris_rips`) and **lower-star** vertex scalar field filtrations (`from_lower_star`).
2. **`PersistenceInterval(NamedTuple)`**: Represents a topological feature's lifecycle
   `(dimension, birth, death, birth_simplex, death_simplex)`, where `death = math.inf` denotes an essential (immortal)
   homology class.
3. **Standard Persistence Boundary Reduction (`persistent_homology`)**: Sparse column reduction of the total filtered
   boundary matrix over $\mathbb{Z}_2$ using `low(j)` pivot elimination, with the **clearing (twist) optimization**
   (Chen & Kerber) to eliminate redundant column operations.
4. **Topological Summaries & Metrics**: `betti_curve`, `persistence_entropy`, and `bottleneck_distance` for quantitative
   comparison of persistence diagrams.

---

## Motivation

`SimplicialComplex.betti_numbers` ([EP-0110](EP-0110-simplicial-homology.md)) computes exact Betti numbers $\beta_k$ for
a fixed simplicial complex. However, when analyzing empirical data—such as weighted networks, point-cloud distance
matrices, or time-varying signals—there is rarely a single "correct" threshold $\epsilon$:

- At small thresholds $\epsilon$, a point cloud is a dust of isolated vertices ($\beta_0 = N, \, \beta_1 = 0$).
- At intermediate thresholds, true geometric loops and cavities emerge ($\beta_1 > 0$).
- At large thresholds, all vertices merge into a single contractible blob ($\beta_0 = 1, \, \beta_1 = 0$).

**Persistent Homology** tracks the exact birth threshold $\epsilon_{\text{birth}}$ and death
threshold $\epsilon_{\text{death}}$ of every $k$-dimensional topological feature across all scales simultaneously.
Long-lived intervals ($\epsilon_{\text{death}} - \epsilon_{\text{birth}} \gg 0$) correspond to genuine structural
topology, whereas short-lived intervals represent sampling noise.

---

## Rationale

The design aligns with the 8 Pillars of The Council Framework (`PRINCIPLES.md`):

### 1. Falsifiability (Popper)

- **Distinguishing Signal from Noise**: Persistent homology makes topological hypotheses quantitatively falsifiable by
  measuring feature persistence $\text{pers} (\gamma) = d - b$ and comparing diagrams via the stability-guaranteed
  `bottleneck_distance`.
- **Exact Algebraic Verification**: At any filtration threshold $t \in \mathbb{R}$, the count of active persistence
  intervals $[b_i, d_i)$ containing $t$ ($b_i \le t < d_i$) must equal the static Betti number $\beta_k (K_t)$ of the
  thresholded `SimplicialComplex` $K_t = \{\sigma \in K \mid f (\sigma) \le t\}$.

### 2. Symmetry (Noether) & Consistency (Russell)

- **Structure Theorem over $\mathbb{F}_2[t]$**: By the Zomorodian–Carlsson Structure Theorem, the persistent homology
  module $H_*(K_\bullet; \mathbb{F}_2)$ decomposes uniquely into interval modules $\bigoplus_i \mathbb{F}_2[b_i, d_i)$,
  invariant under filtration-preserving isomorphisms.
- **Monotonicity Enforcement**: `FilteredSimplicialComplex.add_simplex(simplex, filtration_value)` automatically
  enforces $f (\tau) \le f (\sigma)$ for all faces $\tau \subset \sigma$ by
  taking $f (\tau) = \min (f_{\text{existing}} (\tau), f (\sigma))$.

### 3. Efficiency (Shannon)

- **Sparse $\mathbb{Z}_2$ Column Set Reduction**: Over $\mathbb{F}_2 = \mathbb{Z}/2\mathbb{Z}$, each boundary column is
  represented as a sparse Python `set[int]` of row indices, and column addition $C_j \leftarrow C_j \oplus C_i$ is a
  single symmetric-difference operation (`C_j ^= C_i`) in C-level set arithmetic.
- **Clearing (Twist) Optimization**: By reducing dimensions from top to bottom ($k = \dim K$ down to $1$), any simplex
  index $i$ that serves as the pivot row `low(j)` of a reduced $(k+1)$-boundary column is a boundary cycle
  ($\partial_k (C_j) = 0$) and can be immediately cleared to $\emptyset$ in dimension $k$ in $O (1)$ time.

### 4. Clarity (Feynman)

- **The Freshman Test**: Imagine flooding a mountain range with water as the sea level $t$ rises:
    - In dimension $0$, every mountain valley where a new lake forms is a **birth** of a connected component ($H_0$);
      when the water rises over a pass and two lakes merge into one, the younger lake **dies** (Elder Rule).
    - In dimension $1$, when water completely surrounds an island peak, a ring-shaped moat ($H_1$ loop) is **born**;
      when the water finally submerges the peak, the hole is filled in and the loop **dies**.

---

## Specification

### 1. Data Structures & Filtration Builders in `algebrax.homology`

```python
from typing import NamedTuple
from algebrax.typing import SparseMatrix, SparseVector


class PersistenceInterval(NamedTuple):
    """A birth-death topological interval in a persistence barcode."""

    dimension: int
    birth: float
    death: float
    birth_simplex: tuple[int, ...]
    death_simplex: tuple[int, ...] | None = None

    @property
    def persistence(self) -> float:
        """Lifespan `death - birth` (`math.inf` for essential classes)."""
        return self.death - self.birth


class FilteredSimplicialComplex:
    r"""Monotone filtration of a simplicial complex $\emptyset = K_0 \subseteq K_1 \subseteq \dots \subseteq K_m$."""

    def __init__(
            self,
            simplices: Mapping[tuple[int, ...], float] | Iterable[tuple[tuple[int, ...], float]] | None = None,
    ) -> None: ...

    def add_simplex(self, simplex: tuple[int, ...], filtration: float = 0.0) -> None:
        """Insert a simplex and all its sub-faces, enforcing $f(\\tau) \\le f(\\sigma)$."""

    def to_simplicial_complex(self, threshold: float = math.inf) -> SimplicialComplex:
        """Extract the static subcomplex $K_{\\le \\text{threshold}} = \\{\\sigma \\mid f(\\sigma) \\le \\text{threshold}\\}$."""

    @classmethod
    def from_vietoris_rips(
            cls,
            distance_matrix: SparseMatrix[int, float],
            max_dim: int = 2,
            max_edge_length: float = math.inf,
    ) -> FilteredSimplicialComplex:
        r"""Construct the Vietoris-Rips filtration where $f(\sigma) = \max_{u, v \in \sigma} d(u, v)$."""

    @classmethod
    def from_lower_star(
            cls,
            complex: SimplicialComplex,
            vertex_values: SparseVector[int, float],
    ) -> FilteredSimplicialComplex:
        r"""Construct the lower-star sublevel filtration where $f(\sigma) = \max_{v \in \sigma} h(v)$."""

    def persistent_homology(
            self,
            max_k: int = 2,
            include_zero_persistence: bool = False,
    ) -> list[PersistenceInterval]:
        """Compute persistence intervals across dimensions $0 \\le k \\le \\text{max\\_k}$."""
```

### 2. Topological Summary & Metric Functions

```python
def persistent_homology(
        filtration: FilteredSimplicialComplex,
        max_k: int = 2,
        include_zero_persistence: bool = False,
) -> list[PersistenceInterval]:
    """Compute the persistence barcode of a `FilteredSimplicialComplex`."""


def betti_curve(
        intervals: Iterable[PersistenceInterval],
        thresholds: Sequence[float],
        dimension: int = 0,
) -> list[int]:
    """Evaluate the Betti number $\\beta_k(t)$ at each threshold $t \\in \\text{thresholds}$."""


def persistence_entropy(
        intervals: Iterable[PersistenceInterval],
        dimension: int | None = None,
) -> float:
    r"""Compute the Shannon entropy $H = -\sum_i p_i \ln p_i$ of finite persistence lifespans $L_i = d_i - b_i$."""


def bottleneck_distance(
        diagram_a: Iterable[PersistenceInterval],
        diagram_b: Iterable[PersistenceInterval],
        dimension: int | None = None,
) -> float:
    r"""Compute the exact $L_\infty$ bottleneck distance $d_B(D_A, D_B)$ between two persistence diagrams."""
```

---

## Backwards Compatibility

Purely additive. `SimplicialComplex` and all existing `algebrax.homology` functions remain untouched;
`FilteredSimplicialComplex.to_simplicial_complex(threshold)` bridges directly back to `SimplicialComplex`.

---

## How to Teach This / Documentation Plan

1. **User Guide**: Add a Persistent Homology & Barcodes section in `docs/guide/homology/simplicial.md` showing
   Vietoris–Rips filtration on a noisy circle point cloud and verifying that a single high-persistence $H_1$ bar
   emerges.
2. **Recipe**: Add a topological data analysis (TDA) regime-detection recipe in `docs/recipes.md`.

---

## Reference Implementation

```python
def _reduce_filtration_columns(
        ordered_simplices: list[tuple[tuple[int, ...], float]],
        max_k: int,
) -> list[PersistenceInterval]:
    idx_of = {s: i for i, (s, _) in enumerate(ordered_simplices)}
    cols: dict[int, set[int]] = {}
    for j, (s, _) in enumerate(ordered_simplices):
        if 1 <= len(s) - 1 <= max_k + 1:
            cols[j] = {idx_of[s[:i] + s[i + 1:]] for i in range(len(s))}

    low_to_col: dict[int, int] = {}
    paired_births: set[int] = set()
    intervals: list[PersistenceInterval] = []

    for j in range(len(ordered_simplices)):
        col = cols.get(j)
        if not col:
            continue
        while col and max(col) in low_to_col:
            col ^= cols[low_to_col[max(col)]]
        if col:
            piv = max(col)
            low_to_col[piv] = j
            paired_births.add(piv)
            b_simplex, b_time = ordered_simplices[piv]
            d_simplex, d_time = ordered_simplices[j]
            intervals.append(
                PersistenceInterval(
                    dimension=len(b_simplex) - 1,
                    birth=b_time,
                    death=d_time,
                    birth_simplex=b_simplex,
                    death_simplex=d_simplex,
                )
            )
    return intervals
```

---

## Rejected Ideas

1. **Arbitrary Prime Field $\mathbb{F}_p$ Persistence in v1**:
    - *Considered*: Parameterizing persistence reduction over `GaloisFieldSemiring(p)` for arbitrary primes $p$.
    - *Rejected for initial kernel*: 99% of applied TDA (Ripser, Gudhi, Dionysus) operates over $\mathbb{Z}_2$ where
      bitset/set symmetric difference `^=` gives an order-of-magnitude speedup over dictionary field
      arithmetic. $\mathbb{F}_p$ reduction can be added later as an optional parameter if needed for torsion detection
      (e.g. Klein bottle).

---

## Open Questions

- [ ] Should `bottleneck_distance` use a pure-Python Hopcroft–Karp bipartite matching bisection over candidate
  distances, or also expose the 1-Wasserstein persistence distance?

---

## Change Log

* **2026-10-16:** Initial Draft authored by Eran Rivlis & Antigravity, completing the Phase 4 roadmap from `EXP-0001`.
