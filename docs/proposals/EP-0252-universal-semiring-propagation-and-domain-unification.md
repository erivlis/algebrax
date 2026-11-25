---
title: "EP-0252: Universal Semiring Propagation, Parameterized Tries & Domain Unification"
description: "Fix silent semiring/ring drops across AlgebraicTrie, tensor.einsum, Hodge Laplacians, CochainAlgebra, GroupHopfAlgebra, and automata, and unify K-theory constructions on GrothendieckRing."
icon: lucide/network
status: draft
---

# EP-0252: Universal Semiring Propagation, Parameterized Tries & Domain Unification

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0252                                                                       |
| **Title**         | Universal Semiring Propagation, Parameterized Tries & Domain Unification   |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | 🧭 Explorer (Vision) & ⚖️ Noether (Symmetry)                               |
| **Status**        | Draft                                                                      |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-26                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal restores end-to-end algebraic parameterization across AlgebraX's higher-level domains. It upgrades `AlgebraicTrie` and `tensor.einsum`/`outer_product`/`dot` to preserve live parameterized `Semiring` instances (and perform hash-join contractions), fixes ignored coefficient structures in `SparseChainComplex.hodge_laplacian`, `CochainAlgebra`, `GroupHopfAlgebra`, `pagerank`, and `automata`, unifies topological and motivic K-theory directly onto `algebra.GrothendieckRing`, and generalizes core type aliases (`typing.N` and rectangular `SparseMatrix`).

---

## Motivation

AlgebraX's signature architectural strength is **universal parameterization**: swapping `StandardSemiring` for `TropicalSemiring`, `ModularField(7)`, `GaloisField`, `Fraction`, or `PolynomialAlgebra` should work seamlessly across matrices, tensors, topology, Hopf algebras, and automata. The Second Grand Council Audit revealed multiple islands where this contract breaks silently:

1. **Parameterized Semiring Destruction in `trie.py` & `tensor/core.py`**:
   - `AlgebraicTrie.__init__` only accepts a class (`type[Semiring[V]]`) and invokes zero-argument `semiring()`.
   - `tensor.einsum` and `tensor.outer_product` create outputs via `AlgebraicTrie(semiring=type(semiring))`, either crashing with `TypeError` (`ModularField(7)`, `PAdicField(5)`, `PolynomialAlgebra(...)`) or silently resetting parameters (`ModularSemiring(7)` $\to$ `ModularSemiring(2)`, `GaloisField(3, ...)` $\to$ `GF(2^8)`).
   - `tensor.einsum` uses unindexed recursive Cartesian loops ($O(\prod_t \text{nnz}_t)$), and `tensor.dot` crashes with `IndexError` on empty tensors.
2. **Silently Ignored Coefficient Rings/Semirings**:
   - `SparseChainComplex.hodge_laplacian` passes `semiring=s_inst` to `dot()` for `l_down` and `l_up`, then calls `add(l_down, l_up)` **without** `semiring=s_inst`.
   - `CochainAlgebra(complex, coefficient_ring)` stores `self._ring` and uses it only in `.one`, while `add`, `neg`, `sub`, `smul`, and `mul` (`cup_product`) ignore `self._ring` (and `self._complex`).
   - `GroupHopfAlgebra(group, coeff_semiring=...)` accepts a custom `coeff_semiring` yet hardcodes `float(...)`, `sum(...)`, and `1e-15` in `coproduct`, `counit`, and `antipode`.
   - `analysis.calculus.pagerank` passes `semiring` to `vec_mat` but hardcodes Python `*` and `+` in damping/teleportation.
3. **Isolated Domain Islands**:
   - `automata.py` (`nfa_step`, `simulate_nfa`) hardcodes `defaultdict(float)` and `*`, ignoring `Semiring` (`BooleanSemiring`, `TropicalSemiring`, `ViterbiSemiring`, `StringSemiring`) and `matrix.closure.star`.
   - `TopologicalKTheoryRing` (`topology/k_theory.py`) re-implements `(pos, neg)` formal-difference ring arithmetic from scratch instead of composing `algebra.GrothendieckRing`; `variety/k_theory.py:motivic_point_count_homomorphism` operates on raw tuples without connecting to `GrothendieckRing.lift_homomorphism`.
   - `typing.py` defines `SparseMatrix = Mapping[K, Mapping[K, V]]` (forcing identical row/col key types, mis-typing rectangular boundary/incidence maps) and omits `Fraction` from `typing.N`.

---

## Rationale

- **🧭 The Explorer (Cross-Domain Synergy)**: Connecting `AlgebraicTrie`, `tensor`, `topology`, `automata`, and `k_theory` through the same normalized `Semiring`/`Ring`/`GrothendieckRing` primitives unlocks algebraic tensor networks over finite/polynomial fields, weighted finite automata over arbitrary Kleene algebras, and exact modular/rational cohomology rings with minimal code.
- **⚡ Claude Shannon (Efficiency)**: Adding hash-join subscript indexing to `tensor.einsum` turns three-way diagonal contraction from $O(N^3)$ to $O(N)$, and maintaining an $O(1)$ entry counter in `AlgebraicTrie.__len__` removes full-tree scans.
- **⚖️ Emmy Noether (Symmetry)**: Every API accepting a `semiring` or `coefficient_ring` must honor it identically across every operation—no half-parameterized methods that silently fall back to Python `float`.

---

## Specification

### 1. Instance-Aware `AlgebraicTrie` & Hash-Join `tensor.core`
- **`src/algebrax/trie.py`**:
  - Update `AlgebraicTrie.__init__(self, semiring: Semiring[V] | type[Semiring[V]] | str = StandardSemiring)` to normalize via `Semiring.normalize(semiring)`, preserving live parameterized instances and serializing the instance cleanly in `__getstate__`/`__setstate__`.
  - Maintain an $O(1)$ `_size` counter updated in `__setitem__`/`__delitem__` (and prune zero entries on `add` using `semiring.is_zero` / `== semiring.zero`).
- **`src/algebrax/tensor/core.py`**:
  - Pass the normalized live `semiring` instance directly to `AlgebraicTrie(semiring=semiring)` in `einsum` and `outer_product`.
  - Pre-index tensor entries by their already-bound subscript labels (hash join) inside `einsum` so contractions run in output-sensitive time rather than full Cartesian products.
  - In `dot(tensor_a, tensor_b, ...)`: return an empty `AlgebraicTrie(semiring=semiring)` early whenever either operand has zero non-zero entries.

### 2. End-to-End Coefficient Propagation
- **`src/algebrax/topology/homology.py`**:
  - Forward `semiring=s_inst` in `SparseChainComplex.hodge_laplacian`: `return add(l_down, l_up, semiring=s_inst)`.
- **`src/algebrax/topology/cohomology.py`**:
  - Route `CochainAlgebra.add`, `neg`, `sub`, `smul`, and `mul` through `self._ring` (using `self._ring.add`, `self._ring.neg`, `self._ring.mul`, `self._ring.is_zero` and passing `complex=self._complex, semiring=self._ring` to `cup_product`).
- **`src/algebrax/algebra/_hopf.py`**:
  - Route `GroupHopfAlgebra.coproduct`, `counit`, and `antipode` through `self.coeff_semiring` (`zero`, `add`, `mul`, `is_zero`) instead of hardcoded `float`/`sum`/`1e-15`.
- **`src/algebrax/analysis/calculus.py`**:
  - In `pagerank`, either apply `sem.add`/`sem.mul` consistently across the damping and teleportation blend (and accept `str` in the `semiring` type annotation) or explicitly restrict/document non-numeric semiring semantics.

### 3. Semiring-Parameterized Weighted Automata (`src/algebrax/automata.py`)
- Add optional `semiring: Semiring[V] | type[Semiring[V]] | str | None = None` to `nfa_step` and `simulate_nfa` (defaulting to `StandardSemiring(float)` for full backwards compatibility).
- Add a Kleene reachability bridge `nfa_closure(transitions, semiring=BooleanSemiring)` delegating to `matrix.closure.star` / `matrix_star`.

### 4. Unified `GrothendieckRing` K-Theory Bridges
- **`src/algebrax/topology/k_theory.py`**:
  - Compose `TopologicalKTheoryRing` directly on `algebra.GrothendieckRing` over a `VectorBundleSemiring` carrier instead of duplicating `(pos, neg)` formal-difference arithmetic.
- **`src/algebrax/variety/k_theory.py`**:
  - Expose a `VarietySemiring` / `GrothendieckRing` bridge so `motivic_point_count_homomorphism` can be constructed via `GrothendieckRing.lift_homomorphism` (while retaining the existing `(V, W)` helper signature).

### 5. Core Typing Extensions (`src/algebrax/typing.py`)
- Add `Fraction` to `N = TypeVar('N', int, float, complex, Decimal, Fraction)`.
- Add `RectSparseMatrix = Mapping[R, Mapping[C, V]]` (or generalize `SparseMatrix` where rectangular row/column key domains differ, such as boundary maps and restriction maps).

---

## Backwards Compatibility

- **Fully backwards-compatible** for existing callers:
  - `AlgebraicTrie(TropicalSemiring)` (class argument) continues to work identically alongside `AlgebraicTrie(ModularSemiring(7))` (instance argument).
  - `nfa_step` and `simulate_nfa` default to `StandardSemiring(float)`.
  - `TopologicalKTheoryRing` and `motivic_point_count_homomorphism` retain their existing public methods and signatures.

---

## How to Teach This / Documentation Plan

- Update [`docs/guide/tensor/trie.md`](../guide/tensor/trie.md) and [`docs/guide/tensor/einsum.md`](../guide/tensor/einsum.md) with parameterized semiring examples (`ModularField(7)`, `GaloisField`, `TropicalSemiring`).
- Update [`docs/guide/discrete/automata.md`](../guide/discrete/automata.md) with weighted NFA examples over `TropicalSemiring` (shortest accepting path), `ViterbiSemiring` (most probable parse), and `BooleanSemiring` + Kleene closure.
- Update [`docs/guide/topology/cohomology.md`](../guide/topology/cohomology.md) and [`docs/guide/topology/k_theory.md`](../guide/topology/k_theory.md) to highlight exact $\mathbb{F}_p$/$\mathbb{Q}$ `CochainAlgebra` and `GrothendieckRing` unification.

---

## Reference Implementation

Target files verified in the Second Grand Council Audit:
- `src/algebrax/trie.py`, `src/algebrax/tensor/core.py`
- `src/algebrax/topology/{homology.py,cohomology.py,k_theory.py}`, `src/algebrax/variety/k_theory.py`
- `src/algebrax/algebra/_hopf.py`, `src/algebrax/automata.py`, `src/algebrax/analysis/calculus.py`, `src/algebrax/typing.py`

---

## Rejected Ideas

1. **Keeping `AlgebraicTrie` Restricted to Zero-Arg Semiring Classes and Adding a Separate `ParameterizedTrie`**:
   - *Rejected*: Violates Shannon's minimal representation principle and "Mode vs. Type". `Semiring.normalize()` already handles instances, classes, and strings uniformly everywhere else in `algebrax`.
2. **Changing `SparseMatrix[K, V]` to a 3-Parameter Generic `SparseMatrix[R, C, V]` Globally**:
   - *Rejected*: Would break hundreds of existing type annotations across user code and tests. Adding a dedicated `RectSparseMatrix[R, C, V]` alias preserves 100% compatibility for square `SparseMatrix[K, V]`.

---

## Open Questions

- [ ] Should `tensor.einsum` automatically optimize contraction order (greedy minimum-degree elimination) for $\ge 3$ tensors, or contract left-to-right with hash-join indexing first?
- [ ] Should `topology/persistence.py` also be parameterized over `ModularField(p)` in this EP or in a follow-up topology EP?

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Explorer, Noether, Shannon, Russell).
