---
title: "EP-0165: Unified Topology Namespace, Cochain Ring Products & Persistent Cohomology"
description: "Refactors monolithic homology.py into a modular algebrax.topology package and introduces the Alexander-Whitney cup/cap products, dual persistent cohomology, and first sheaf cohomology H^1."
icon: lucide/layers
status: final
---

# EP-0165: Unified Topology Namespace, Cochain Ring Products & Persistent Cohomology

| Field        | Value                                                                                                                                       |
|:-------------|:--------------------------------------------------------------------------------------------------------------------------------------------|
| **EP**       | 0165                                                                                                                                        |
| **Title**    | Unified Topology Namespace, Cochain Ring Products & Persistent Cohomology                                                                   |
| **Author**   | Eran Rivlis & Antigravity (The Council)                                                                                                     |
| **Sponsor**  | The Council                                                                                                                                 |
| **Delegate** | 🧩 Bertrand Russell (Taxonomy), ⚖️ Emmy Noether (Duality), ⚡ Claude Shannon (Efficiency), 🤝 The Steward (Ergonomics) & 💡 Richard Feynman |
| **Status**   | Final                                                                                                                                       |
| **Type**     | Standards Track                                                                                                                             |
| **Created**  | 2026-10-25                                                                                                                                  |
| **Updated**  | 2026-10-25                                                                                                                                  |
| **Replaces** | None                                                                                                                                        |

---

## Abstract

This proposal introduces a first-class **`algebrax.topology`** package that decomposes the 2,020-line monolithic
`src/algebrax/homology.py` module into five cohesive submodules (`homology`, `cohomology`, `persistence`, `dec`, and
`sheaf`) sharing a private `_core` kernel while preserving `algebrax.homology` as a 100% backwards-compatible facade.
Simultaneously, it completes the algebraic duality between homology and cohomology by introducing:

1. **The Alexander–Whitney Cup Product (`cup_product`)**: Turns the graded cochain space $C^*(K; \mathcal{S})$ and
   cohomology $H^*(K; \mathcal{S})$ into a graded ring over any `Semiring[V]`, satisfying the graded Leibniz rule
   $d (\alpha \smile \beta) = (d\alpha) \smile \beta + (-1)^p \, \alpha \smile (d\beta)$.
2. **The Cap Product (`cap_product`)**: Implements the Poincaré duality contraction
   $\frown: C_n (K; \mathcal{S}) \times C^p (K; \mathcal{S}) \to C_{n-p} (K; \mathcal{S})$.
3. **Dual Persistent Cohomology (`persistent_cohomology`)**: Reduces the transposed coboundary matrix in reverse
   filtration order over $\mathbb{Z}_2$, matching `persistent_homology` barcodes while extracting representative
   cocycles.
4. **First Sheaf Cohomology (`CellularSheaf.first_cohomology_dimension`)**: Computes the obstruction group dimension
   $\dim H^1 (G; \mathcal{F}) = \dim \operatorname{coker} \delta_{\mathcal{F}}$, completing the sheaf Euler–Poincaré
   identity $\chi (G; \mathcal{F}) = \dim H^0 (G; \mathcal{F}) - \dim H^1 (G; \mathcal{F})$.

---

## Motivation

### 1. Structural Growth Beyond `homology.py`

Across Phases 2 and 4 (`EP-0101`, `EP-0110`, `EP-0160`, `EP-0161`, and `EP-0162`), `src/algebrax/homology.py` grew to
over **2,020 lines** spanning five distinct mathematical subdomains:

- Simplicial & chain homology (`SparseChainComplex`, `SimplicialComplex`)
- Simplicial cohomology (`Cochain`, `coboundary`, `cohomology_rank`)
- Discrete Exterior Calculus & Hodge theory (`exterior_derivative`, `codifferential`, `hodge_star`,
  `helmholtz_hodge_decomposition`)
- Cellular sheaves (`CellularSheaf`, `sheaf_laplacian`, `sheaf_diffusion`, `sheaf_harmonic_extension`)
- Persistent homology (`FilteredSimplicialComplex`, `persistent_homology`, `bottleneck_distance`)

Following the precedent established by `algebrax.semiring/` ([EP-0134](EP-0134-semiring-namespace-refactoring.md)) and
`algebrax.lie/` ([EP-0163](EP-0163-lie-algebras-and-bch-dynamics.md)), organizing these into `src/algebrax/topology/`
restores structural clarity and keeps each module focused (~300–450 lines).

### 2. Why Cohomology Needs Its Ring Structure

As vector spaces over a field, homology $H_k (K; \mathbb{F})$ and cohomology $H^k (K; \mathbb{F})$ have identical Betti
numbers $\beta_k = \dim H_k = \dim H^k$. However, **cohomology is strictly stronger than homology** because cochains
possess a natural multiplication—the **Alexander–Whitney cup product** ($\smile$):

- **Distinguishing Spaces with Identical Betti Numbers**: The 2-torus $T^2$ and the wedge sum $S^2 \vee S^1 \vee S^1$
  have identical Betti numbers ($\beta_0 = 1, \beta_1 = 2, \beta_2 = 1$). Homology cannot tell them apart. In
  cohomology, the cup product of the two 1-cocycle generators $[\alpha], [\beta] \in H^1 (T^2)$ evaluates to the
  non-zero fundamental class $[\alpha \smile \beta] \ne 0 \in H^2 (T^2)$, whereas on $S^2 \vee S^1 \vee S^1$ the cup
  product vanishes identically.
- **Natural Semiring Polymorphism**: On a $(p+q)$-simplex $[v_0, v_1, \dots, v_{p+q}]$, the Alexander–Whitney formula
  $$\bigl (\alpha \smile \beta\bigr)([v_0, \dots, v_{p+q}]) =
  \alpha ([v_0, \dots, v_p]) \otimes_{\mathcal{S}} \beta ([v_p, \dots, v_{p+q}])$$
  uses only semiring addition $\oplus_{\mathcal{S}}$ and multiplication $\otimes_{\mathcal{S}}$ (no subtraction!). Thus
  `cup_product` generalizes naturally to **every `Semiring` in `algebrax`**.

---

## Rationale

The design aligns with the Council Framework (`PRINCIPLES.md`):

### 1. Structural Taxonomy (Russell)

- **Clean Domain Decomposition**: `algebrax.topology` groups `homology`, `cohomology`, `persistence`, `dec`, and
  `sheaf` under a single umbrella while isolating shared low-level kernels (`_canonicalize_simplex`,
  `_count_inversions_and_sort`, `_matrix_rank`) in `algebrax.topology._core`.

### 2. Symmetry & Duality (Noether)

- **Chain–Cochain Poincaré Duality**: Every homology operation now has its exact cohomological dual:
    - Boundary $\partial_k: C_k \to C_{k-1}$ $\longleftrightarrow$ Coboundary $d^k = \partial_{k+1}^T: C^k \to C^{k+1}$
    - Cup product $\smile: C^p \times C^q \to C^{p+q}$ $\longleftrightarrow$ Cap product
      $\frown: C_n \times C^p \to C_{n-p}$
      obeying $\langle \psi, c \frown \phi \rangle = \langle \phi \smile \psi, c \rangle$
    - Persistent Homology $H_*(K_\bullet)$ $\longleftrightarrow$ Persistent Cohomology $H^*(K_\bullet)$ (identical
      barcodes by Universal Coefficient Duality)
    - Sheaf Global Sections $H^0 (G; \mathcal{F}) = \ker \delta_{\mathcal{F}}$ $\longleftrightarrow$ Sheaf Obstructions
      $H^1 (G; \mathcal{F}) = \operatorname{coker} \delta_{\mathcal{F}}$ obeying
      $\dim H^0 - \dim H^1 = \sum_{v} d_v - \sum_{e} d_e$.

### 3. Efficiency (Shannon)

- **Sparse Support-Driven Cup Product**: Given sparse cochains $\alpha \in C^p$ and $\beta \in C^q$, `cup_product`
  indexes $\beta$ by its leading vertex $v_p = \tau[0]$ so only compatible front-face / back-face pairs
  $([v_0, \dots, v_p], [v_p, \dots, v_{p+q}])$ with $v_0 < \dots < v_p < \dots < v_{p+q}$ are multiplied, running in
  $O (|\operatorname{supp} (\alpha)| \cdot \text{deg}_{\text{out}} (v_p))$ instead of enumerating all $(p+q)$-simplices.

### 4. Developer Ergonomics & Compatibility (Steward)

- **Zero Breaking Changes**: `algebrax.homology` and `algebrax.analysis` continue to export every existing class and
  function without deprecation warnings.

---

## Specification

### 1. Package Layout (`src/algebrax/topology/`)

```text
src/algebrax/topology/
├── __init__.py          # Exports unified topology namespace + submodules
├── _core.py             # _canonicalize_simplex, _count_inversions_and_sort, _matrix_rank, _is_non_zero
├── homology.py          # SparseChainComplex, SimplicialComplex
├── cohomology.py        # Cochain, DiscreteForm, coboundary, cohomology_rank, cup_product, cap_product,
│                        # canonicalize_form, flow_to_cochain, cochain_to_flow
├── persistence.py       # PersistenceInterval, FilteredSimplicialComplex, persistent_homology,
│                        # persistent_cohomology, betti_curve, persistence_entropy, bottleneck_distance
├── dec.py               # HodgeDecomposition, exterior_derivative, codifferential, hodge_star,
│                        # hodge_laplacian, helmholtz_hodge_decomposition
└── sheaf.py             # CellularSheaf, StalkCoord, EdgeStalkCoord, RestrictionMap,
                         # sheaf_laplacian, sheaf_diffusion, sheaf_harmonic_extension
```

`src/algebrax/homology.py` becomes a re-export facade importing `__all__` from `algebrax.topology`.

### 2. Cochain Ring & Dual Operations (`algebrax.topology.cohomology`)

```python
def cup_product(
    alpha: Cochain[K, V] | Mapping[tuple[K, ...], V],
    beta: Cochain[K, V] | Mapping[tuple[K, ...], V],
    *,
    complex: SimplicialComplex | None = None,
    semiring: Semiring[V] | type[Semiring[V]] | None = None,
    tol: float = 1e-14,
) -> Cochain[K, V]:
    r"""Compute the Alexander-Whitney cup product $\alpha \smile \beta \in C^{p+q}(K; \mathcal{S})$.

    For a canonical $(p+q)$-simplex $\sigma = (v_0, \dots, v_p, \dots, v_{p+q})$:
        $(\alpha \smile \beta)(\sigma) = \alpha(v_0, \dots, v_p) \otimes_{\mathcal{S}} \beta(v_p, \dots, v_{p+q})$

    If `complex` is provided, restricts the output cochain to $(p+q)$-simplices present in `complex`.
    """


def cap_product(
    chain: Mapping[tuple[K, ...], V],
    cochain: Cochain[K, V] | Mapping[tuple[K, ...], V],
    *,
    semiring: Semiring[V] | type[Semiring[V]] | None = None,
    tol: float = 1e-14,
) -> dict[tuple[K, ...], V]:
    r"""Compute the Alexander-Whitney cap product $c \frown \phi \in C_{n-p}(K; \mathcal{S})$.

    For an $n$-simplex $\sigma = (v_0, \dots, v_p, \dots, v_n)$ and a $p$-cochain $\phi$:
        $\sigma \frown \phi = \phi(v_0, \dots, v_p) \otimes_{\mathcal{S}} (v_p, \dots, v_n)$
    satisfying the Kronecker duality identity $\langle \psi, c \frown \phi \rangle = \langle \phi \smile \psi, c \rangle$.
    """
```

### 3. Dual Persistent Cohomology (`algebrax.topology.persistence`)

```python
def persistent_cohomology(
    filtration: FilteredSimplicialComplex,
    max_k: int = 2,
    include_zero_persistence: bool = False,
) -> tuple[list[PersistenceInterval], dict[PersistenceInterval, set[tuple[int, ...]]]]:
    r"""Compute persistent cohomology over $\mathbb{Z}_2$ via reverse-filtration coboundary reduction.

    Returns:
        Tuple `(intervals, cocycles)` where `intervals` matches `persistent_homology` and
        `cocycles` maps each `PersistenceInterval` to its representative $\mathbb{Z}_2$ cocycle support.
    """
```

### 4. First Sheaf Cohomology (`algebrax.topology.sheaf`)

```python
class CellularSheaf(Generic[K]):
    ...

    def first_cohomology_dimension(self, tol: float = 1e-9) -> int:
        r"""Compute the 1st sheaf cohomology dimension $\dim H^1(G; \mathcal{F}) = \dim \operatorname{coker} \delta_{\mathcal{F}}$."""

    def euler_characteristic(self) -> int:
        r"""Compute the sheaf Euler characteristic $\chi(G; \mathcal{F}) = \sum_{v \in V} d_v - \sum_{e \in E} d_e$."""
```

---

## Backwards Compatibility

100% backwards-compatible:

- `import algebrax.homology` and `from algebrax.homology import ...` remain fully supported and export all existing and
  new symbols.
- `algebrax.analysis` continues to re-export DEC and sheaf symbols.
- `algebrax.topology` is added to `algebrax.__all__`.

---

## How to Teach This / Documentation Plan

1. **User Guide**: Update `docs/guide/homology/simplicial.md` to showcase `algebrax.topology`, the Alexander–Whitney
   `cup_product` distinguishing $T^2$ from $S^2 \vee S^1 \vee S^1$, `cap_product` duality, and `persistent_cohomology`.
2. **Verification Matrix**: Register `cup_product` (graded Leibniz rule & associativity), `cap_product` (Kronecker
   duality $\langle \psi, c \frown \phi \rangle = \langle \phi \smile \psi, c \rangle$), `persistent_cohomology`
   (barcode parity with `persistent_homology` and cocycle condition $d\alpha = 0$), and sheaf Euler–Poincaré
   conservation in `docs/verification.md`.

---

## Reference Implementation

```python
def cup_product(
    alpha: Cochain[K, V] | Mapping[tuple[K, ...], V],
    beta: Cochain[K, V] | Mapping[tuple[K, ...], V],
    *,
    complex: SimplicialComplex | None = None,
    semiring: Semiring[V] | type[Semiring[V]] | None = None,
    tol: float = 1e-14,
) -> Cochain[K, V]:
    s_inst = Semiring.normalize(semiring)
    c_a = alpha if isinstance(alpha, Cochain) else Cochain(alpha, tol=tol)
    c_b = beta if isinstance(beta, Cochain) else Cochain(beta, tol=tol)
    if c_a.degree is None or c_b.degree is None:
        return Cochain(tol=tol)

    p, q = c_a.degree, c_b.degree
    allowed = complex._simplices.get(p + q) if complex is not None else None

    beta_by_head: dict[K, list[tuple[tuple[K, ...], V]]] = {}
    for s_b, val_b in c_b.items():
        beta_by_head.setdefault(s_b[0], []).append((s_b, val_b))

    out: dict[tuple[K, ...], V] = {}
    for s_a, val_a in c_a.items():
        pivot_v = s_a[-1]
        for s_b, val_b in beta_by_head.get(pivot_v, ()):
            # Because s_a = (v_0 < ... < v_p) and s_b = (v_p < ... < v_{p+q}),
            # merged = (v_0 < ... < v_{p+q}) is strictly increasing with sign +1.
            merged = s_a + s_b[1:]
            if allowed is not None and merged not in allowed:
                continue
            prod = s_inst.mul(val_a, val_b)
            if not s_inst.is_zero(prod):
                out[merged] = s_inst.add(out[merged], prod) if merged in out else prod

    return Cochain(out, degree=p + q, oriented=c_a.oriented and c_b.oriented, tol=tol)
```

---

## Rejected Ideas

1. **Removing `algebrax.homology` in Favor of `algebrax.topology`**:
    - *Considered*: Deleting `src/algebrax/homology.py` and requiring all callers to migrate to `algebrax.topology`.
    - *Rejected*: Violates the Steward's backwards-compatibility guarantee; keeping `homology.py` as a thin re-export
      module costs ~40 lines of code and preserves 100% compatibility across all existing scripts, notebooks, and tests.
2. **Simplicial Cup-1 ($\smile_1$) Steenrod Higher Homotopy Operations in Initial Scope**:
    - *Considered*: Implementing the full hierarchy of Steenrod $\smile_i$ operations to witness homotopy commutativity
      at the cochain level.
    - *Rejected for initial scope*: The primary Alexander–Whitney cup ($\smile_0$) and cap ($\frown$) products already
      induce
      the graded-commutative cohomology ring $H^*(K; \mathcal{S})$ and satisfy the exact Leibniz rule.

---

## Open Questions

- [x] Should `Cochain` also overload the `@` or `^` operator as syntactic sugar for `cup_product(a, b)`? *(Resolved:
  Implemented both `Cochain.cup(other, ...)` and `Cochain.__xor__` (`alpha ^ beta`) as syntactic sugar for
  `cup_product`.)*

---

## Change Log

* **2026-10-25:** Initial Draft authored by Eran Rivlis & Antigravity, reviewed by the Council, and implemented across
  `src/algebrax/topology/` (`_core`, `homology`, `cohomology`, `persistence`, `dec`, `sheaf`) and `src/algebrax/homology.py`.
  Transitioned status to `Final`.

