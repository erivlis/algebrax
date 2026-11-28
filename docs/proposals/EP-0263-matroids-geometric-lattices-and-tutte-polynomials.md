---
title: "EP-0263: Matroids, Geometric Lattices, Characteristic & Tutte Polynomials"
description: "Introduce zero-dependency bitmask FiniteMatroid, graphic and exact finite-field linear matroids, the Whitney-Rota geometric flat lattice cryptomorphism, Rota Mobius characteristic polynomials, and Tutte polynomials."
icon: lucide/shapes
status: draft
---

# EP-0263: Matroids, Geometric Lattices, Characteristic & Tutte Polynomials

| Field             | Value                                                                                          |
|:------------------|:-----------------------------------------------------------------------------------------------|
| **EP**            | 0263                                                                                           |
| **Title**         | Matroids, Geometric Lattices, Characteristic & Tutte Polynomials                               |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                    |
| **Sponsor**       | Core Maintainers                                                                               |
| **Delegate**      | ⚡ Shannon (Bitmask Flats & D/C), ⚖️ Noether (Whitney–Rota Cryptomorphism) & 🧭 Explorer       |
| **Status**        | Draft                                                                                          |
| **Type**          | Standards Track                                                                                |
| **Created**       | 2026-11-28                                                                                     |
| **Updated**       | 2026-11-28                                                                                     |
| **Replaces**      | —                                                                                              |
| **Superseded-By** | —                                                                                              |

---

## Abstract

This proposal implements **Phase 12, Wave 4** on top of [`EP-0260`](EP-0260-lattice-protocol-soundness-finite-posets-and-lattices.md) and [`EP-0251`](EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md), bringing combinatorial geometry and matroid theory into `algebrax.lattice._matroid`. It delivers a zero-dependency bitmask-backed `FiniteMatroid`, canonical constructors (`uniform_matroid`, `graphic_matroid`, exact `linear_matroid` over `ModularField`/`GaloisField`/`FractionField` via `algebrax.matrix.eliminate.rank`, `fano_matroid`, and `non_fano_matroid`), the bidirectional **Whitney–Rota cryptomorphism** between simple matroids and geometric lattices, exact **characteristic polynomials** $\chi_M(t)$ computed directly from `EP-0260`'s Rota Möbius matrix, and bivariate **Tutte polynomials** $T_M(x, y)$ stored in unboxed sparse `dict` carriers.

---

## Motivation

Matroids unify linear independence (vector spaces over fields), graphic acyclicity (spanning forests), algebraic transcendence, and tropical geometry (`EP-0222`):

1. **Missing Combinatorial Bridge Between Linear Algebra, Graphs & Lattices:** AlgebraX already computes exact ranks over $\mathbb{Q}$ and $\mathbb{F}_p$ (`EP-0251`), simplicial/graph complexes (`EP-0165`), and finite lattices (`EP-0260`), yet lacks the unifying abstraction (`FiniteMatroid`) whose flats form a **geometric lattice** (atomistic + upper semimodular).
2. **Characteristic & Tutte Polynomials Without External CAS Dependencies:** Chromatic polynomials of graphs, flow polynomials, spanning-tree counts (Cayley's formula), reliability polynomials, and Jones-polynomial specializations on alternating links (`EP-0215`) are all exact evaluations of a single universal matroid invariant—the **Tutte polynomial** $T_M(x, y)$—whose specialization $\chi_M(t) = (-1)^{r(M)} T_M(1 - t, 0)$ equals the Rota Möbius characteristic polynomial of its flat lattice.
3. **Tropical Bergman Fan Foundation:** Future tropical linear spaces and Dressians (`EP-0222`) are parameterized directly by the lattice of flats of a matroid.

---

## Rationale

Validated in [**EXP-0013**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) (Region IV prototype on graphic matroid $M(K_4)$: `15` flats, `is_geometric() == True`, exact Rota Möbius characteristic polynomial $\chi_{K_4}(t) = t^3 - 6t^2 + 11t - 6 = (t - 1)(t - 2)(t - 3)$, and Tutte specialization $T_{K_4}(1, 1) = 16 = 4^{4-2}$ spanning trees):

- **⚖️ Emmy Noether (Whitney–Rota Cryptomorphism & Matroid Duality):**
  Establishes two exact dualities as executable laws:
  1. *Cryptomorphism:* Simple matroids $M \longleftrightarrow$ geometric lattices $\mathcal{L}(M)$ via `matroid.flat_lattice()` and `matroid_from_geometric_lattice(L)`.
  2. *Matroid Duality:* $r_{M^*}(S) = |S| + r_M(E \setminus S) - r_M(E)$, satisfying the exact Tutte symmetry $T_{M^*}(x, y) = T_M(y, x)$.
- **⚡ Claude Shannon (Zero-Duplicate Linear Rank & Memoized Deletion–Contraction):**
  `linear_matroid` delegates directly to `EP-0251`'s `Field[V]`-polymorphic `algebrax.matrix.eliminate.rank`, adding zero duplicate Gaussian elimination code. Subsets are packed as Python `int` bitmasks; Tutte deletion–contraction memoizes isomorphic minor bitmask pairs `(available_mask, contracted_mask)` and stores polynomials in unboxed `dict[int, int]` and `dict[tuple[int, int], int]` carriers (`EP-0004`).
- **🔬 Karl Popper (Cross-Theorem Oracle Verification):**
  Computing $\chi_M(t)$ independently via (a) the Rota Möbius matrix on $\mathcal{L}(M)$ (`EP-0260`) and (b) the Tutte specialization $(-1)^{r(M)} T_M(1 - t, 0)$ provides an internal, zero-external-dependency cross-verification oracle.

---

## Specification

### 1. `FiniteMatroid[E]` (`src/algebrax/lattice/_matroid.py`)

```python
class FiniteMatroid(Generic[E]):
    r"""Finite matroid $M = (E, r)$ backed by bitmask rank caching and exact cryptomorphisms."""

    def __init__(
        self,
        ground: Sequence[E],
        rank_fn: Callable[[frozenset[E]], int],
        *,
        validate: bool = True,
    ) -> None: ...

    @classmethod
    def from_bases(cls, ground: Sequence[E], bases: Iterable[Iterable[E]]) -> FiniteMatroid[E]: ...

    @classmethod
    def from_circuits(cls, ground: Sequence[E], circuits: Iterable[Iterable[E]]) -> FiniteMatroid[E]: ...

    @property
    def ground(self) -> tuple[E, ...]: ...
    def rank(self, subset: Iterable[E] | None = None) -> int: ...
    def is_independent(self, subset: Iterable[E]) -> bool: ...
    def is_loop(self, element: E) -> bool: ...
    def is_coloop(self, element: E) -> bool: ...
    def closure(self, subset: Iterable[E]) -> frozenset[E]: ...
    def is_flat(self, subset: Iterable[E]) -> bool: ...
    def bases(self) -> tuple[frozenset[E], ...]: ...
    def circuits(self) -> tuple[frozenset[E], ...]: ...
    def flats(self) -> tuple[frozenset[E], ...]: ...
    def hyperplanes(self) -> tuple[frozenset[E], ...]: ...
    def flat_lattice(self) -> FiniteLattice[frozenset[E]]: ...
    def dual(self) -> FiniteMatroid[E]: ...
    def delete(self, element: E) -> FiniteMatroid[E]: ...
    def contract(self, element: E) -> FiniteMatroid[E]: ...
    def characteristic_polynomial(self) -> dict[int, int]: ...
    def tutte_polynomial(self) -> dict[tuple[int, int], int]: ...
    def evaluate_tutte(self, x: int | Fraction, y: int | Fraction) -> int | Fraction: ...
```

### 2. Canonical Constructors & Cryptomorphism Inverse (`src/algebrax/lattice/_matroid.py`)

```python
def uniform_matroid(r: int, n: int) -> FiniteMatroid[int]:
    r"""Uniform matroid $U_{r, n}$ of rank $r$ on $n$ elements."""
    ...


def graphic_matroid(edges: Sequence[tuple[Hashable, Hashable]]) -> FiniteMatroid[int]:
    r"""Cycle matroid $M(G)$ of an undirected multigraph (edges indexed $0 \dots |E|-1$)."""
    ...


def linear_matroid(
    columns: Sequence[SparseVector[int, V]],
    field: Field[V],
) -> FiniteMatroid[int]:
    r"""Vector matroid represented by sparse columns over an exact `Field[V]` (`ModularField`, `GaloisField`, `FractionField`)."""
    ...


def fano_matroid() -> FiniteMatroid[int]:
    r"""The rank-3 Fano matroid $F_7$ (representable strictly over characteristic 2)."""
    ...


def non_fano_matroid() -> FiniteMatroid[int]:
    r"""The rank-3 non-Fano matroid $F_7^-$ (representable strictly over characteristic $\neq 2$)."""
    ...


def matroid_from_geometric_lattice(lattice: FiniteLattice[T]) -> FiniteMatroid[T]:
    r"""Recover the unique simple matroid on the atoms of a finite geometric lattice (Whitney–Rota inverse)."""
    ...
```

### 3. Verification Oracles (`src/algebrax/verification/`)

- `verify_matroid_rank_axioms(matroid)`: checks $0 \le r(A) \le |A|$, monotonicity $A \subseteq B \implies r(A) \le r(B)$, and submodularity $r(A \cup B) + r(A \cap B) \le r(A) + r(B)$.
- `verify_matroid_cryptomorphism(matroid)`: verifies `matroid.flat_lattice().is_geometric() == True` and (for simple matroids) exact round-trip isomorphism via `matroid_from_geometric_lattice`.
- `verify_tutte_identities(matroid)`: checks:
  1. Exact Rota–Tutte identity $\chi_M(t) = (-1)^{r(M)} T_M(1 - t, 0)$.
  2. Duality identity $T_{M^*}(x, y) = T_M(y, x)$.
  3. Basis count $T_M(1, 1) = |\mathcal{B}(M)|$.

---

## Backwards Compatibility

Strictly additive inside `src/algebrax/lattice/` and `src/algebrax/verification/`. Zero breaking changes.

---

## How to Teach This / Documentation Plan

1. Add a **"Matroids, Geometric Lattices & Tutte Polynomials"** guide section showcasing $M(K_4)$'s chromatic polynomial via Rota Möbius inversion, Cayley's spanning-tree count $T_{K_4}(1, 1) = 16$, and the Fano ($F_7$) vs. Non-Fano ($F_7^-$) characteristic-2 representability split over `ModularField(2)` vs. `ModularField(3)`.
2. Add a Tier-4 recipe connecting `graphic_matroid`, `flat_lattice()`, and `tutte_polynomial()`.

---

## Reference Implementation

- **Research Compendium:** [`references/explorations/EXP-0013-lattice-and-order-continent/README.md`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) (Section 2.2, Region IV)
- **Zero-Dependency Prototype:** [`playground/lattice_continent_prototype.py`](https://github.com/erivlis/algebrax/blob/main/playground/lattice_continent_prototype.py) (`GraphicMatroid`, `M(K_4)` flat lattice, Rota Möbius $\chi_{K_4}(t)$, and Tutte $T_{K_4}(1, 1) = 16$)

---

## Rejected Ideas

1. **Re-Implementing Matrix Rank Inside `_matroid.py`:**
   *Rejected*: Duplicates `EP-0251`'s `algebrax.matrix.eliminate.rank` and risks diverging on finite-field or exact `Fraction` pivoting.
2. **Dense `2^|E|` Precomputation of All Subsets on `__init__`:**
   *Rejected*: Prevents creating matroids with $|E| > 16$ even when users only query `rank()`, `is_independent()`, or `closure()`. Rank caching should be lazy per bitmask, while exhaustive methods (`flats()`, `tutte_polynomial()`) guard reasonable size bounds cleanly.
3. **Boxing Polynomial Outputs in Custom `TuttePolynomial` Wrapper Classes:**
   *Rejected*: Violates `EP-0004`'s unboxed storage invariant. Returning `dict[int, int]` (univariate) and `dict[tuple[int, int], int]` (bivariate) keeps outputs directly interoperable with `PolynomialAlgebra` and `MultivariatePolynomialAlgebra` (`EP-0220`).

---

## Open Questions

- [ ] Should `graphic_matroid` also accept a `SparseMatrix` adjacency representation directly for interoperability with `algebrax.analysis` spectral graph routines?
- [ ] What default ground-set size limit should `tutte_polynomial()` enforce before requiring an explicit `allow_large=True` flag (e.g., $|E| \le 18$)?

---

## Change Log

* **2026-11-28:**
    * Initial Draft authored from `EXP-0013` as Phase 12 Wave 4.
