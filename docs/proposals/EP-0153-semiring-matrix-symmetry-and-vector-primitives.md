---
title: "EP-0153: Semiring Matrix Symmetry, Sparse Vector Primitives & Cochain Carrier"
description: "Restores Noetherian semiring symmetry to matrix addition and trace, consolidates sparse vector space micro-kernels, introduces the orientation-aware Cochain carrier, and aligns analysis module docstrings with AMDS."
icon: lucide/scale
status: final
---

# EP-0153: Semiring Matrix Symmetry, Sparse Vector Primitives & Cochain Carrier

| Field        | Value                                                                                                                        |
|:-------------|:-----------------------------------------------------------------------------------------------------------------------------|
| **EP**       | 0153                                                                                                                         |
| **Title**    | Semiring Matrix Symmetry, Sparse Vector Primitives & Cochain Carrier                                                         |
| **Author**   | Eran Rivlis & Antigravity                                                                                                    |
| **Sponsor**  | The Council                                                                                                                  |
| **Delegate** | ⚖️ Emmy Noether (Symmetry), ⚡ Claude Shannon (Efficiency), 🧩 Bertrand Russell (Consistency) & 💡 Richard Feynman (Clarity) |
| **Status**   | Final                                                                                                                        |
| **Type**     | Standards Track                                                                                                              |
| **Created**  | 2026-10-16                                                                                                                   |
| **Updated**  | 2026-10-16                                                                                                                   |
| **Replaces** | None                                                                                                                         |

---

## Abstract

This proposal resolves four foundational architectural asymmetries across `algebrax.matrix`, `algebrax.lie`, `algebrax.analysis`, and `algebrax.homology` identified during the Phase 3.5/4 Council architectural audit:

1. **Semiring-Aware Matrix Addition, Trace & Normalization (`algebrax.matrix.core`):** Generalizes `matrix.add` and `matrix.trace` to accept an optional `semiring` parameter (defaulting to `StandardSemiring`) and standardizes `Semiring.normalize(semiring)` across all semiring-parameterized matrix operations (`dot`, `add`, `trace`, `inner`, `mat_vec`, `vec_mat`, `power`, `frobenius_inner`).
2. **Canonical Sparse Vector Space Primitives (`algebrax.matrix`):** Consolidates duplicated private vector helpers (`_vec_add`, `_vec_scale`, `_vec_norm`, `_vec_clean` in `algebrax.lie.core` and inline comprehensions in `algebrax.analysis`) into public, tested primitives (`vec_add`, `vec_scale`, `vec_axpy`, `vec_norm`, `vec_clean`).
3. **First-Class `Cochain[K, V]` Carrier (`algebrax.homology` & `algebrax.analysis`):** Introduces an immutable `Mapping[tuple[K, ...], V]` carrier class `Cochain` that enforces alternating orientation antisymmetry ($\omega(\pi(\sigma)) = \operatorname{sgn}(\pi)\,\omega(\sigma)$), degenerate simplex annihilation, and lossless projection between nested `SparseMatrix[K, float]` edge flows (`Cochain.from_flow` / `to_flow`) and 0-form node signals (`Cochain.from_nodes` / `to_nodes`).
4. **Module Docstring & AMDS Alignment (`algebrax.analysis`):** Restores the top-level module docstring in `src/algebrax/analysis.py` and upgrades discrete calculus operators (`gradient`, `divergence`, `laplacian`, `forman_ricci_curvature`, `gaussian_kernel`) to full compliance with the **AlgebraX Mathematical Docstring Standard (AMDS)**.

---

## Motivation

As AlgebraX has expanded from core semiring matrix multiplication into Lie algebras (`EP-0163`, `EP-0164`), spectral graph theory (`EP-0152`), and discrete exterior calculus (`EP-0160`), four subtle seams of friction have emerged between foundational modules and higher-level domain tracks:

### 1. Asymmetry Between `matrix.dot` and `matrix.add` / `matrix.trace`

In `algebrax.matrix.core`, multiplicative operations (`dot`, `mat_vec`, `vec_mat`, `inner`, `power`) are polymorphic over `Semiring[V]`. However, additive operations on the exact same `SparseMatrix[K, V]` carrier remain hardcoded to Python's standard numeric ring:

- `element_wise_binary_op(m1, m2, op)` hardcodes `row1.get(c, 0)` and prunes via `if val != 0:`.
- Calling `ax.matrix.add(m1, m2)` on two matrices over `TropicalSemiring` ($\mathbb{0} = +\infty, \oplus = \min$) silently substitutes `0` for missing edges—corrupting shortest-path unions—and uses arithmetic `+` instead of $\min$.
- Calling `ax.matrix.add(m1, m2)` on matrices over `MonoidAlgebraSemiring`, `ProvenanceSemiring`, or `CliffordSemiring` (where $\mathbb{0} = \{\}$) raises `TypeError: unsupported operand type(s) for +: 'dict' and 'int'`.
- Similarly, `ax.matrix.trace(m)` hardcodes `sum(row.get(r, 0) ...)`, preventing semiring trace evaluation $\mathrm{Tr}_{\mathcal{S}}(A) = \bigoplus_r A_{rr}$ (such as minimum cycle self-cost in tropical algebra or reflexive reachability in Boolean algebra).
- Furthermore, while `algebrax.homology` and `algebrax.analysis.pagerank` normalize semiring arguments via `Semiring.normalize(semiring)` (accepting instances, class types like `TropicalSemiring`, or catalog strings like `'tropical'`), `algebrax.matrix.core` still checks `if semiring is None: semiring = StandardSemiring()`, rejecting class types and catalog strings.

### 2. Proliferation of Private Sparse Vector Kernels

Because `algebrax.matrix` lacked first-class linear combination primitives on `SparseVector[K, V]`:

- `src/algebrax/lie/core.py` defines private functions `_vec_add`, `_vec_scale`, `_vec_norm`, and `_vec_clean` with hardcoded tolerances (`1e-14`, `1e-12`).
- `src/algebrax/analysis.py` re-implements vector scaling, L1/L2 norms, and AXPY updates ($\mathbf{u} \leftarrow \mathbf{u} - \tau \mathbf{d}$) inline inside `eigen_centrality`, `laplacian_smoothing`, and `fiedler_vector`.
- Upcoming iterative solvers in `EP-0160` (Conjugate Gradient over Hodge Laplacians $\Delta_k$) and `EP-0161` (Sheaf Laplacian consensus) would otherwise duplicate these exact kernels a third and fourth time.

### 3. Orientation Leak & Dual Representation of Cochains / 1-Forms

Mathematically, a $k$-cochain $\omega \in C^k(K; R)$ is an **alternating** linear functional on $(k+1)$-tuples of vertices:
$$\omega(v_{\pi(0)}, \dots, v_{\pi(k)}) = \operatorname{sgn}(\pi)\, \omega(v_0, \dots, v_k)$$
Representing a cochain as a raw `dict` introduces two structural hazards:
1. **Lost Orientation Antisymmetry:** If `omega = {(0, 1): 5.0}`, evaluating `omega[(1, 0)]` raises `KeyError` (or `omega.get((1, 0), 0.0)` returns `0.0`) instead of `-5.0`.
2. **Disconnect Between Graph Flows and Simplicial Cochains:** `analysis.gradient(field, graph)` and `analysis.divergence(flow)` represent 1-forms as nested `SparseMatrix[K, float]` (`flow[u][v]`), whereas `homology.SimplicialComplex` and `EP-0160` represent $k$-forms as flat mappings keyed by oriented $(k+1)$-tuples `(u, v)`.

Introducing a first-class, immutable `Cochain[K, V](Mapping[tuple[K, ...], V])` resolves both problems while remaining 100% compatible with `SparseVector` (`Mapping`) consumers.

### 4. Module Docstring Drift in `src/algebrax/analysis.py`

The module header of `src/algebrax/analysis.py` (lines 1–23) currently contains an orphaned copy of `forman_ricci_curvature`'s function docstring (`Analyze edge curvature via discrete combinatorics... Args: graph (SparseMatrix)...`) instead of a module-level summary and taxonomy of `algebrax.analysis`. Additionally, while `pagerank`, `eigen_centrality`, `laplacian_smoothing`, and `fiedler_vector` follow AMDS, older functions (`gradient`, `divergence`, `laplacian`, `forman_ricci_curvature`, `gaussian_kernel`) predate `EP-0150` and lack `Algebraic Signature:` blocks.

---

## Rationale

This proposal is governed by the 8 Pillars of The Council Framework (`PRINCIPLES.md`):

### 1. Symmetry (Emmy Noether)

- **Additive–Multiplicative Duality in $\mathcal{M}_n(\mathcal{S})$:** The set of $n \times n$ matrices over any semiring $\mathcal{S} = \langle S, \oplus, \otimes, \mathbb{0}, \mathbb{1} \rangle$ itself forms a semiring $\mathcal{M}_n(\mathcal{S})$ with matrix addition $(A \oplus B)_{ij} = A_{ij} \oplus B_{ij}$ and matrix multiplication $(A \otimes B)_{ij} = \bigoplus_k (A_{ik} \otimes B_{kj})$. Supporting `semiring` in `dot` while omitting it in `add` and `trace` broke the closure of $\mathcal{M}_n(\mathcal{S})$.
- **Alternating Permutation Symmetry:** `Cochain` enforces $\omega(\pi(\sigma)) = \operatorname{sgn}(\pi)\,\omega(\sigma)$ on both construction and lookup, and provides exact round-trip projections between skew-symmetric edge flows and 1-cochains:
  $$\mathrm{Cochain.from\_flow}(F).\mathrm{to\_flow}() = \frac{1}{2}(F - F^T)$$

### 2. Efficiency (Claude Shannon)

- **Zero-Overhead Default Path:** When `semiring is None`, `matrix.add` and `matrix.trace` use fast local bindings, preserving existing micro-benchmark performance on numeric matrices.
- **Canonical Basis Storage:** `Cochain` stores only strictly increasing vertex tuples $v_0 < v_1 < \dots < v_k$ with non-zero coefficients, cutting memory in half compared to storing both $(u, v)$ and $(v, u)$ in a skew-symmetric matrix.
- **Single-Pass `vec_axpy`:** Computing $\mathbf{z} = a \mathbf{x} + \mathbf{y}$ in one pass avoids allocating an intermediate scaled dictionary $a \mathbf{x}$.

### 3. Consistency (Bertrand Russell)

- **Universal Semiring Normalization:** Every function in `algebrax.matrix` that accepts a `semiring` argument normalizes it via `Semiring.normalize(semiring)`, matching `algebrax.homology` and `algebrax.analysis`.
- **`Mapping` Protocol Inheritance:** Just as `AlgebraicTrie` implements `MutableMapping[tuple[K, ...], V]`, `Cochain` implements `Mapping[tuple[K, ...], V]`, so every `Cochain` is a valid `SparseVector[tuple[K, ...], V]` without requiring adapter wrappers in `mat_vec`, `inner`, or `vec_add`.

### 4. Safety (The Golem)

- **Immutability by Default:** `Cochain` is an immutable `Mapping`—algebraic operations (`+`, `-`, `*`) return new `Cochain` instances without mutating state.
- **Characteristic-2 / Unoriented Safety:** An optional `oriented: bool = True` flag on `Cochain` allows unoriented $\mathbb{Z}_2$ cochains (where $-1 \equiv +1$ or negation is undefined on the carrier) to canonicalize vertex order without applying sign inversion.
- **Identity Containment:** Missing entries in `element_wise_binary_op` and `add` are resolved against the explicit additive identity `zero` (`semiring.zero`) rather than assuming `0`.

### 5. Clarity (Richard Feynman)

- **Restored Module Map & AMDS:** Repairing `src/algebrax/analysis.py`'s module docstring and adding formal `Algebraic Signature:` sections to `gradient`, `divergence`, `laplacian`, `forman_ricci_curvature`, and `gaussian_kernel` ensures `mkdocstrings` renders clear, uniform mathematical documentation.

### 6. Falsifiability (Karl Popper)

- Matrix semiring laws ($\mathcal{M}_n(\mathcal{S})$ associativity of `add`, commutativity of `add`, distributivity of `dot` over `add`, and $\mathrm{Tr}_{\mathcal{S}}(A \oplus B) = \mathrm{Tr}_{\mathcal{S}}(A) \oplus \mathrm{Tr}_{\mathcal{S}}(B)$) and cochain antisymmetry laws ($\omega(v, u) = -\omega(u, v)$, $\omega(u, u) = 0$) become directly falsifiable via property-based tests.

---

## Specification

### 1. Semiring-Aware Matrix Addition, Trace & Normalization (`algebrax.matrix.core`)

#### 1.1 `element_wise_binary_op` and `add`

```python
def element_wise_binary_op(
    m1: SparseMatrix[K, V],
    m2: SparseMatrix[K, V],
    op: Callable[[V, V], V],
    zero: V = 0,  # type: ignore[assignment]
) -> SparseMatrix[K, V]:
    """Perform element-wise binary operation on two sparse matrices.

    Missing entries are treated as `zero`, and output entries equal to `zero`
    are omitted to preserve structural sparsity.
    """
    keys = set(m1.keys()) | set(m2.keys())
    result: dict[K, dict[K, V]] = {}
    for r in keys:
        row1 = m1.get(r, {})
        row2 = m2.get(r, {})
        col_keys = set(row1.keys()) | set(row2.keys())
        new_row: dict[K, V] = {}
        for c in col_keys:
            val = op(row1.get(c, zero), row2.get(c, zero))
            if val != zero:
                new_row[c] = val
        if new_row:
            result[r] = new_row
    return result


def add(
    m1: SparseMatrix[K, V],
    m2: SparseMatrix[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> SparseMatrix[K, V]:
    r"""Perform element-wise addition of two sparse matrices over a semiring.

    Algebraic Signature:
        $(A \oplus B)_{rc} = A_{rc} \oplus B_{rc}$
    """
    if semiring is None:
        return element_wise_binary_op(m1, m2, operator.add, zero=0)  # type: ignore[arg-type]
    sr = Semiring.normalize(semiring)
    return element_wise_binary_op(m1, m2, sr.add, zero=sr.zero)
```

#### 1.2 Semiring-Aware `trace`

```python
def trace(
    matrix: SparseMatrix[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> V:
    r"""Calculate the trace of a sparse matrix (sum of diagonal elements) over a semiring.

    Algebraic Signature:
        $\mathrm{Tr}_{\mathcal{S}}(A) = \bigoplus_{r} A_{rr}$
    """
    if semiring is None:
        return sum(row.get(r, 0) for r, row in matrix.items())  # type: ignore[return-value, misc]
    sr = Semiring.normalize(semiring)
    acc = sr.zero
    sr_add = sr.add
    for r, row in matrix.items():
        if r in row:
            acc = sr_add(acc, row[r])
    return acc
```

#### 1.3 `Semiring.normalize` Standardization

Update `dot`, `inner`, `mat_vec`, `vec_mat`, `power`, and `frobenius_inner` in `src/algebrax/matrix/core.py` to accept `Semiring[V] | type[Semiring[V]] | str | None = None` and resolve via `Semiring.normalize(semiring)` when a non-`None` semiring is provided.

---

### 2. Canonical Sparse Vector Space Primitives (`algebrax.matrix.core`)

Export the following functions in `algebrax.matrix.core` and re-export in `algebrax.matrix`:

```python
def vec_add(
    u: SparseVector[K, V],
    v: SparseVector[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
    tol: float = 0.0,
) -> dict[K, V]:
    r"""Compute sparse vector addition $(u \oplus v)_k = u_k \oplus v_k$."""


def vec_scale(
    u: SparseVector[K, V],
    scalar: V,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
    tol: float = 1e-14,
) -> dict[K, V]:
    r"""Compute left scalar multiplication $(s \otimes u)_k = s \otimes u_k$ with sparsity pruning."""


def vec_axpy(
    a: float | complex,
    x: SparseVector[K, float | complex],
    y: SparseVector[K, float | complex],
    tol: float = 1e-14,
) -> dict[K, float | complex]:
    r"""Compute fused sparse linear combination $\mathbf{z} = a \mathbf{x} + \mathbf{y}$."""


def vec_norm(
    u: SparseVector[K, float | complex],
    p: float = 2.0,
) -> float:
    r"""Compute the $L_p$ norm $\|\mathbf{u}\|_p = \left(\sum_k |u_k|^p\right)^{1/p}$ (supports $p=1, 2, \infty$)."""


def vec_clean(
    u: SparseVector[K, float | complex],
    tol: float = 1e-12,
) -> dict[K, float | complex]:
    r"""Prune numerical noise $|u_k| \le \text{tol}$ and strip negligible imaginary components."""
```

`src/algebrax/lie/core.py` will import `vec_add`, `vec_scale`, `vec_norm`, and `vec_clean` from `algebrax.matrix`, removing its redundant private helpers.

---

### 3. First-Class `Cochain[K, V]` Carrier (`algebrax.homology` & `algebrax.analysis`)

#### 3.1 Type Alias in `algebrax.typing`

```python
Simplex: TypeAlias = tuple[K, ...]
"""An oriented k-simplex represented as a (k+1)-tuple of vertices (v_0, ..., v_k)."""
```

#### 3.2 `Cochain` Class Specification in `algebrax.homology`

```python
class Cochain(Mapping[tuple[K, ...], V], Generic[K, V]):
    r"""Alternating discrete differential k-form / cochain over oriented simplices.

    Algebraic Signature:
        $\omega \in C^k(K; R), \quad \omega(v_{\pi(0)}, \dots, v_{\pi(k)}) = \operatorname{sgn}(\pi)\,\omega(v_0, \dots, v_k)$

    Carrier:
        `Mapping[tuple[K, ...], V]` (Immutable sparse mapping over canonical simplices $v_0 < v_1 < \dots < v_k$).

    Operations:
        - Orientation Lookup (`__getitem__`, `get`): Evaluates $\omega(\sigma)$ for any vertex permutation $\sigma$,
          returning $\operatorname{sgn}(\pi)\,\omega(\sigma_{\text{sorted}})$ and $0$ on degenerate simplices.
        - Vector Space Arithmetic (`+`, `-`, `*`, unary `-`): Linear combinations in $C^k(K; R)$.
        - Chain Pairing (`eval`): Bilinear Kronecker pairing $\langle \omega, c \rangle = \sum_{\sigma} \omega(\sigma) c(\sigma)$.
        - Flow & Node Bridges (`from_flow`, `to_flow`, `from_nodes`, `to_nodes`): Lossless conversion between
          graph adjacency edge flows (`SparseMatrix`), node scalar fields (`SparseVector`), and cochains.

    Properties:
        Alternating antisymmetry, degenerate simplex annihilation ($\omega(\dots, u, \dots, u, \dots) = 0$),
        full compatibility with `SparseVector` (`Mapping[tuple[K, ...], V]`).

    Applications:
        Discrete Exterior Calculus (DEC), Helmholtz-Hodge flow decomposition, simplicial cohomology,
        conservative vs. rotational network flow analysis.
    """

    def __init__(
        self,
        data: Mapping[tuple[K, ...], V] | Iterable[tuple[tuple[K, ...], V]] | None = None,
        *,
        degree: int | None = None,
        oriented: bool = True,
        tol: float = 1e-14,
    ) -> None: ...

    @property
    def degree(self) -> int | None:
        """Simplicial degree k of the cochain (where simplices are (k+1)-tuples), or None if empty/mixed."""

    @property
    def oriented(self) -> bool:
        """Whether simplex permutation parity flips the sign of coefficients."""

    def __getitem__(self, simplex: tuple[K, ...]) -> V: ...
    def __iter__(self) -> Iterator[tuple[K, ...]]: ...
    def __len__(self) -> int: ...

    def eval(self, chain: Mapping[tuple[K, ...], V]) -> V:
        r"""Evaluate the bilinear Kronecker pairing $\langle \omega, c \rangle = \sum_\sigma \omega(\sigma) c_\sigma$."""

    @classmethod
    def from_nodes(
        cls,
        field: SparseVector[K, V],
        *,
        tol: float = 1e-14,
    ) -> Cochain[K, V]:
        """Lift a 0-form vertex signal `{u: val}` to a 0-cochain `{(u,): val}`."""

    def to_nodes(self) -> dict[K, V]:
        """Project a 0-cochain `{(u,): val}` to a vertex dictionary `{u: val}`."""

    @classmethod
    def from_flow(
        cls,
        flow: SparseMatrix[K, float],
        *,
        mode: Literal['auto', 'net', 'half_skew'] = 'auto',
        tol: float = 1e-14,
    ) -> Cochain[K, float]:
        r"""Project a nested adjacency edge-flow matrix onto a canonically oriented 1-cochain.

        Modes for bidirectional edges where both (u, v) and (v, u) exist (u < v):
            - `'auto'` (default): If $F_{vu} = -F_{uv}$ (already skew-symmetric, e.g. from `analysis.gradient`),
              preserves $\omega((u, v)) = F_{uv}$; otherwise computes net flux $\omega((u, v)) = F_{uv} - F_{vu}$.
            - `'net'`: Always computes net directed flux $\omega((u, v)) = F_{uv} - F_{vu}$.
            - `'half_skew'`: Computes the skew-symmetric projection $\omega((u, v)) = \frac{1}{2}(F_{uv} - F_{vu})$.
        """

    def to_flow(
        self,
        *,
        skew_symmetric: bool = True,
        tol: float = 1e-14,
    ) -> dict[K, dict[K, float]]:
        r"""Lift a 1-cochain $\omega \in C^1(K; \mathbb{R})$ to a nested adjacency flow matrix.

        When `skew_symmetric=True`, populates both $F_{uv} = \omega((u, v))$ and $F_{vu} = -\omega((u, v))$.
        When `skew_symmetric=False`, populates only the positive-flux direction ($F_{uv} = \omega((u, v))$ if $> 0$,
        else $F_{vu} = -\omega((u, v))$).
        """
```

Functional aliases `flow_to_cochain` and `cochain_to_flow` are also exported in `algebrax.analysis` and `algebrax.homology` delegating to `Cochain.from_flow` and `Cochain.to_flow`.

---

### 4. Module Docstring & AMDS Alignment in `src/algebrax/analysis.py`

1. Replace lines 1–23 of `src/algebrax/analysis.py` with a proper module docstring summarizing:
   - Discrete Exterior Calculus & Differential Operators (`gradient`, `divergence`, `laplacian`, `Cochain`, `flow_to_cochain`, `cochain_to_flow`)
   - Spectral Graph Theory & Diffusion (`laplacian_matrix`, `fiedler_vector`, `algebraic_connectivity`, `spectral_bipartition`, `laplacian_smoothing`, `laplacian_spectrum`)
   - Network Centrality & Curvature (`pagerank`, `eigen_centrality`, `forman_ricci_curvature`, `gaussian_kernel`)
2. Upgrade `gradient`, `divergence`, `laplacian`, `forman_ricci_curvature`, and `gaussian_kernel` docstrings to include `Algebraic Signature:`, `Carrier:`, `Operations:`, `Properties:`, and `Applications:`.

---

## Backwards Compatibility

- **100% Backwards Compatible:**
  - `matrix.add(m1, m2)` and `matrix.trace(m)` default to `semiring=None`, preserving exact existing behavior and return types for numeric matrices.
  - `element_wise_binary_op(m1, m2, op)` defaults to `zero=0`, preserving existing positional and keyword call sites.
  - Because `Cochain` implements `collections.abc.Mapping[tuple[K, ...], V]`, it is a drop-in `SparseVector` for all existing functions (`mat_vec`, `inner`, `vec_add`, `dict(cochain)`), and existing functions returning `dict` remain unchanged.

---

## How to Teach This / Documentation Plan

1. **User Guide (`docs/guide/matrix/core.md`):** Document semiring-polymorphic `matrix.add` and `matrix.trace` alongside `matrix.dot`, plus the new sparse vector space primitives (`vec_add`, `vec_scale`, `vec_axpy`, `vec_norm`, `vec_clean`).
2. **User Guide (`docs/guide/homology/chain_complex.md` & `docs/guide/analysis/discrete_calculus.md`):** Introduce `Cochain`, orientation antisymmetry $\omega(v, u) = -\omega(u, v)$, and how `Cochain.from_flow` / `to_flow` connect graph-based `gradient`/`divergence` with simplicial cochains.
3. **API Reference:** Automatic rendering of `Cochain` and the newly AMDS-compliant `algebrax.analysis` functions via `mkdocstrings`.

---

## Reference Implementation

```python
import algebrax as ax
from algebrax.homology import Cochain, SimplicialComplex, coboundary

# 1. Orientation-aware Cochain lookup & antisymmetry
omega = Cochain({(1, 0): 4.0, (1, 2): -2.5, (0, 0): 99.0})
assert omega[(0, 1)] == -4.0  # Canonicalized from (1, 0) with sign flip
assert omega[(1, 0)] == 4.0  # Reverse lookup flips sign automatically
assert (0, 0) not in omega  # Degenerate simplex annihilated

# 2. Bridging graph gradient with simplicial coboundary d^0
sc = SimplicialComplex([(0, 1, 2)])
graph = {0: {1: 1.0, 2: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {0: 1.0, 1: 1.0}}
potentials = {0: 1.0, 1: 4.0, 2: 2.0}

grad_cochain = Cochain.from_flow(ax.analysis.gradient(potentials, graph))
d0 = coboundary(sc, 0)
d0_cochain = Cochain(ax.matrix.mat_vec(d0, Cochain.from_nodes(potentials)))
assert grad_cochain == d0_cochain
```

---

## Rejected Ideas

1. **Making `Cochain` Do Not Inherit from `Mapping` (Opaque Wrapper Class):**
   - *Reason for Rejection:* Violates **Steward Harmony** and **Russell Consistency**. If `Cochain` were an opaque object rather than a `Mapping[tuple[K, ...], V]`, users could not pass it directly to `ax.matrix.mat_vec`, `ax.matrix.inner`, or `ax.matrix.vec_axpy`, creating an artificial type wall in a dict-native library.
2. **Creating a Separate `algebrax.vector` Top-Level Submodule:**
   - *Reason for Rejection:* Violates **Shannon Efficiency (Zero Bloat)**. Vectors (`SparseVector`) and matrices (`SparseMatrix`) already share `algebrax.matrix` (which houses `inner`, `mat_vec`, `vec_mat`).
3. **Changing `analysis.gradient` to Return `Cochain` Instead of `SparseMatrix`:**
   - *Reason for Rejection:* Breaks backwards compatibility for existing recipes and tests that index `grad[u][v]`. Providing `Cochain.from_flow(gradient(f, g))` preserves 100% compatibility while unlocking simplicial calculus.

---

## Open Questions

- None — all design trade-offs resolved during Council review.

---

## Change Log

* **2026-10-16:**
    * Initial Draft created under Phase 3.5 Council Refinement Track.
    * Upgraded Pillar 3 from standalone conversion helpers to the first-class `Cochain[K, V]` `Mapping` carrier with orientation antisymmetry.
