---
title: "EP-0252: Universal Semiring Propagation, Parameterized Tries & Domain Unification"
description: "Fix silent semiring/ring drops across AlgebraicTrie, tensor.einsum, Hodge Laplacians, CochainAlgebra, GroupHopfAlgebra, and automata, and unify topological K-theory on GrothendieckRing."
icon: lucide/network
status: accepted
---

# EP-0252: Universal Semiring Propagation, Parameterized Tries & Domain Unification

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0252                                                                       |
| **Title**         | Universal Semiring Propagation, Parameterized Tries & Domain Unification   |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | 🧭 Explorer (Vision) & ⚖️ Noether (Symmetry)                               |
| **Status**        | Accepted                                                                   |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-27                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal restores end-to-end algebraic parameterization across AlgebraX's higher-level domains. It introduces a shared zero-predicate helper (`make_zero_predicate` / `is_algebraic_zero`) honoring `HasZeroPred` without per-iteration `isinstance` checks, upgrades `AlgebraicTrie` and `tensor.einsum`/`outer_product`/`dot` to preserve live parameterized `Semiring` instances with hash-join contractions, fixes ignored coefficient structures in `SparseChainComplex.hodge_laplacian`, `Cochain`/`CochainAlgebra`, `GroupHopfAlgebra`, `pagerank`, and `automata`, and unifies `TopologicalKTheoryRing` onto `algebra.CommGrothendieckRing`.

---

## Motivation

AlgebraX's signature architectural strength is **universal parameterization**: swapping `StandardSemiring` for `TropicalSemiring`, `ModularField(7)`, `GaloisField`, `Fraction`, or `PolynomialAlgebra` should work seamlessly across matrices, tensors, topology, Hopf algebras, and automata. The Second Grand Council Audit revealed multiple islands where this contract breaks silently:

1. **Parameterized Semiring Destruction in `trie.py` & `tensor/core.py`**:
   - `AlgebraicTrie.__init__` only accepts a class (`type[Semiring[V]]`) and invokes zero-argument `semiring()`; `__getstate__` drops live instance state via `type(self.semiring)`.
   - `tensor.einsum` and `tensor.outer_product` create outputs via `AlgebraicTrie(semiring=type(semiring))`, either crashing with `TypeError` (`ModularField(7)`, `PAdicField(5)`, `PolynomialAlgebra(...)`) or silently resetting parameters (`ModularSemiring(7)` $\to$ `ModularSemiring(2)`, `GaloisField(3, ...)` $\to$ `GF(2^8)`), and never call `Semiring.normalize(semiring)`.
   - `tensor.einsum` uses unindexed recursive Cartesian loops ($O(\prod_t \text{nnz}_t)$), and `tensor.dot` crashes with `IndexError` on empty tensors.
2. **Silently Ignored Coefficient Rings/Semirings & Hardcoded Float Operators**:
   - `SparseChainComplex.hodge_laplacian` passes `semiring=s_inst` to `dot()` for `l_down` and `l_up`, then calls `add(l_down, l_up)` **without** `semiring=s_inst` (and `__init__` aliases caller `boundary_matrices`).
   - `CochainAlgebra(complex, coefficient_ring)` stores `self._ring` and uses it only in `.one`, while `add`, `neg`, `sub`, `smul`, and `mul` (`cup_product`) ignore `self._ring` (and `self._complex`). Worse, `Cochain` itself hardcodes Python unary `-` (breaking `ModularField`/`GaloisField` orientation signs) and `cup_product`/`cap_product` filter via `_is_non_zero(v, tol)` (silently deleting valid `TropicalSemiring.one == 0.0` entries!).
   - `GroupHopfAlgebra(group, coeff_semiring=...)` hardcodes `float` generics, `float(...)`, `sum(...)`, and `1e-15` in `coproduct`, `counit`, and `antipode`.
   - `analysis.calculus.pagerank` passes `semiring` to `vec_mat` but hardcodes Python `*` and `+` in damping/teleportation.
3. **Isolated Domain Islands**:
   - `automata.py` (`nfa_step`, `simulate_nfa`) hardcodes `defaultdict(float)` and `*`, ignoring `Semiring` (`BooleanSemiring`, `TropicalSemiring`, `ViterbiSemiring`, `StringSemiring`) and Kleene closure via `matrix.closure.matrix_star`, and returns aliased `start_states` on 0-step runs.
   - `TopologicalKTheoryRing` (`topology/k_theory.py`) re-implements `(pos, neg)` formal-difference ring arithmetic from scratch instead of composing `algebra.CommGrothendieckRing`.

---

## Rationale

- **🧭 The Explorer (Cross-Domain Synergy)**: Connecting `AlgebraicTrie`, `tensor`, `topology`, `automata`, and `k_theory` through normalized `Semiring`/`Ring`/`CommGrothendieckRing` primitives unlocks algebraic tensor networks over finite/polynomial fields, weighted finite automata over Kleene algebras, and exact modular/rational cohomology rings with minimal code.
- **⚡ Claude Shannon (Efficiency)**: Hash-join subscript indexing accumulating into a flat `dict` inside `tensor.einsum` turns three-way diagonal contraction from $O(N^3)$ to $O(N)$; hoisting `getattr(sr, 'is_zero', None)` once outside loops avoids per-element `@runtime_checkable` overhead; maintaining an $O(1)$ `_size` counter in `AlgebraicTrie.__len__` removes full-tree DFS scans.
- **⚖️ Emmy Noether (Symmetry)**: Every API accepting a `semiring` or `coefficient_ring` honors it identically across every operation while respecting genuine mathematical boundaries (`CochainAlgebra` and `GroupHopfAlgebra` require a `Ring` for negation; `nfa_closure` requires a `StarSemiring`; `pagerank` requires real/probability-compatible numeric carriers).

---

## Specification

### 0. Shared Zero-Predicate Helper (`src/algebrax/converters.py`)
Neither `Semiring` nor `Ring` guarantees an `.is_zero()` method (`HasZeroPred` is required only on `DivisionRing`/`Field`). Add a shared Layer-1/2 utility consumed across `EP-0252` and `EP-0254`:

```python
def make_zero_predicate(structure: Any, tol: float = 0.0) -> Callable[[Any], bool]:
    """Return a hoisted zero-check callable: uses structure.is_zero if present, else == structure.zero."""

def is_algebraic_zero(structure: Any, value: Any) -> bool:
    """Single-value zero check delegating to structure.is_zero when available, else value == structure.zero."""
```

Callers in inner loops **must** hoist `is_zero = make_zero_predicate(sr)` once outside the loop (never calling `@runtime_checkable isinstance(sr, HasZeroPred)` per entry).

### 1. Instance-Aware `AlgebraicTrie` & Hash-Join `tensor.core`
- **`src/algebrax/trie.py` & `src/algebrax/clifford.py`**:
  - Update `AlgebraicTrie.__init__(self, semiring: Semiring[V] | type[Semiring[V]] | str = StandardSemiring)` to normalize via `Semiring.normalize(semiring)`, preserving live parameterized instances and serializing the live `semiring` instance cleanly in `__getstate__`/`__setstate__`.
  - Convert local closures `key_op`/`quotient_fn` inside `CliffordAlgebra.__init__` (`clifford.py:104-109`) to picklable bound methods/callables so `AlgebraicTrie(CliffordAlgebra(...))` pickles cleanly.
  - Maintain an exact $O(1)$ `_size` counter across `__setitem__` (insert vs. overwrite), `__delitem__`, and zero-pruning in `add()` (using `make_zero_predicate(self.semiring)` and pruning emptied intermediate trie branches so dead subtrees do not accumulate).
- **`src/algebrax/tensor/core.py`**:
  - Add `Semiring.normalize(semiring)` and accept `Semiring[V] | type[Semiring[V]] | str | None` in `einsum`, `outer_product`, and `dot`.
  - Pass the normalized live `semiring` instance directly to `AlgebraicTrie(semiring=semiring)` in `einsum`, `outer_product`, and `dot`.
  - In `einsum`: contract left-to-right with hash-join indexing on shared already-bound subscripts, accumulating results in a flat `dict[tuple[Any, ...], V]` (pruning zeros via hoisted `is_zero`) before loading the final `AlgebraicTrie` once.
  - In `dot(tensor_a, tensor_b, ...)`: return an empty `AlgebraicTrie(semiring=semiring)` early whenever either operand has zero non-zero entries.

### 2. End-to-End Coefficient Propagation
- **`src/algebrax/topology/homology.py` & `dec.py`**:
  - Forward `semiring=s_inst` in `SparseChainComplex.hodge_laplacian`: `return add(l_down, l_up, semiring=s_inst)`.
  - Copy caller `boundary_matrices` (`{k: {r: dict(row) for r, row in m.items()} for k, m in boundary_matrices.items()}`) in `SparseChainComplex.__init__` so external mutation cannot corrupt the complex.
  - Add `| str` to `semiring` type annotations on `SparseChainComplex.verify_nilpotency`, `SparseChainComplex.hodge_laplacian`, and `dec.hodge_laplacian`.
- **`src/algebrax/topology/cohomology.py`**:
  - Upgrade `Cochain` to support an optional `ring: Ring[V] | None = None` (or `neg_fn` + `zero` + `tol=0.0` for exact rings) so orientation sign flips in `__init__`, `__getitem__`, and `get` use `ring.neg(val)` instead of Python unary `-val` (making `ModularField(p)` and `GaloisField` work end-to-end).
  - Fix `cup_product` and `cap_product` to prune zeros strictly via `make_zero_predicate(s_inst)` (applying `abs(v) <= tol` **only** when `s_inst.zero == 0` and `isinstance(v, (int, float, complex))`) so `TropicalSemiring.one == 0.0` is never deleted.
  - Route `CochainAlgebra.add`, `neg`, `sub`, `smul`, and `mul` completely through `self._ring` and `self._complex` (passing `complex=self._complex, semiring=self._ring` to `cup_product`).
- **`src/algebrax/algebra/_hopf.py`**:
  - Generalize `GroupHopfAlgebra` class generics to `Generic[T]` (`MonoidAlgebra[Any, T], HopfAlgebra[T, SparseVector[Any, T]]`), validating that `coeff_semiring` satisfies `Ring` when ring operations (`neg`/`sub`) are required, and route `coproduct`, `counit`, and `antipode` through `self.coeff_semiring` (`zero`, `add`, `mul`, and hoisted `make_zero_predicate`) instead of hardcoded `float`/`sum`/`1e-15`.
- **`src/algebrax/analysis/calculus.py`**:
  - In `pagerank`, accept `str` in the `semiring` annotation, propagate `sem.add`/`sem.mul`/`sem.zero` consistently across the damping and teleportation blend, and validate real/probability-compatible numeric carriers (raising `TypeError` upfront for non-numeric carriers like `StringSemiring` instead of mid-loop crashes).

### 3. Semiring-Parameterized Weighted Automata (`src/algebrax/automata.py`)
- Add optional `semiring: Semiring[V] | type[Semiring[V]] | str | None = None` to `nfa_step` and `simulate_nfa` (retaining a fast native path when `semiring is None` / `StandardSemiring(float)`). Return a fresh shallow copy `dict(start_states)` on 0-step `simulate_nfa` calls.
- Add Kleene reachability bridge:
  ```python
  def nfa_closure(
      transitions: Mapping[S, Mapping[A, Mapping[S, V]]],
      *,
      symbol: A | None = None,
      semiring: StarSemiring[V] | type[StarSemiring[V]] | str = BooleanSemiring,
  ) -> SparseMatrix[S, V]:
      """Compute all-path (symbol=None) or single-symbol/epsilon Kleene closure via matrix_star."""
  ```
  - When `symbol is None`, project the 3-level transition tensor into a 2-level matrix $M_{s, t} = \bigoplus_{a \in \Sigma} \delta(s, a, t)$; when `symbol` is given, extract $M_{s, t} = \delta(s, \text{symbol}, t)$.
  - Require `isinstance(sr, HasStar)` (rejecting non-star semirings such as `StringSemiring` cleanly per `EP-0250`) before delegating to `matrix.closure.matrix_star`.

### 4. Unified `GrothendieckRing` K-Theory Bridge (`src/algebrax/topology/k_theory.py`)
- Define `VectorBundleSemiring` witnessing `CommSemiring[DiscreteOrthogonalConnection | None]` (with `.zero = None`, direct sum $\oplus$, tensor product $\otimes$, and trivial line bundle as `.one`).
- Compose `TopologicalKTheoryRing` directly on `algebra.CommGrothendieckRing` (from `EP-0250`) over `VectorBundleSemiring`, eliminating duplicated `(pos, neg)` formal-difference arithmetic.

---

## Acceptance Criteria

1. `AlgebraicTrie(ModularField(7))`, `AlgebraicTrie(GaloisField(3, [1, 0, 2]))`, and `AlgebraicTrie(CliffordAlgebra(2, 0, 0))` preserve live instances across `einsum`, `outer_product`, `dot`, and `pickle.loads(pickle.dumps(trie))`; `len(trie)` runs in $O(1)$ and matches `sum(1 for _ in trie)` after inserts, overwrites, deletions, and zero-cancelling `add()`.
2. `tensor.dot` on empty tensors returns an empty `AlgebraicTrie` without `IndexError`; `tensor.einsum('ii,ii,ii->i', t, t, t)` scales linearly $O(N)$ rather than $O(N^3)$.
3. `SparseChainComplex.hodge_laplacian(k, semiring=ModularSemiring(5))` equals `add(l_down, l_up, semiring=ModularSemiring(5))`, and mutating caller `boundary_matrices` after construction does not affect the complex.
4. `CochainAlgebra(complex, ModularField(5))` and `CochainAlgebra(complex, GaloisField(2, [1, 1, 1]))` pass `verify_ring_laws`; `cup_product(..., semiring=TropicalSemiring())` preserves `0.0` (`TropicalSemiring.one`) entries.
5. `GroupHopfAlgebra(S3, coeff_semiring=ModularField(5))` and `GroupHopfAlgebra(S3, coeff_semiring=StandardField(Fraction))` pass `verify_hopf_algebra_laws` with exact arithmetic.
6. `pagerank` propagates `StandardSemiring`, `ViterbiSemiring`, and `BottleneckSemiring` consistently and raises `TypeError` on `StringSemiring`.
7. `simulate_nfa` works over `BooleanSemiring`, `TropicalSemiring`, `ViterbiSemiring`, and `StringSemiring`, returns a non-aliased copy on `symbols=[]`, and `nfa_closure` computes Kleene reachability over `BooleanSemiring`/`TropicalSemiring` while raising `TypeError` on `StringSemiring`.
8. `TopologicalKTheoryRing` delegates formal-difference arithmetic to `algebra.CommGrothendieckRing` and passes `verify_comm_ring_laws`; `VectorBundleSemiring` complies with `EP-0002` (AMDS) and `tests/algebrax/test_docstrings.py`.

---

## Backwards Compatibility

- Existing callers passing semiring classes (`AlgebraicTrie(TropicalSemiring)`) or omitting `semiring` in `automata` continue working identically.
- `pagerank` now raises `TypeError` upfront for non-numeric semirings (previously crashed mid-iteration).
- `TopologicalKTheoryRing` retains its public API while delegating internals to `CommGrothendieckRing`.

---

## How to Teach This / Documentation Plan

- Ensure `VectorBundleSemiring` and updated classes conform to `EP-0002` (AMDS) and `tests/algebrax/test_docstrings.py`.
- Update [`docs/guide/tensor/trie.md`](../guide/tensor/trie.md) and [`docs/guide/tensor/einsum.md`](../guide/tensor/einsum.md) with parameterized semiring examples (`ModularField(7)`, `GaloisField`, `TropicalSemiring`).
- Update [`docs/guide/discrete/automata.md`](../guide/discrete/automata.md) with weighted NFA examples and `nfa_closure`.
- Update [`docs/guide/topology/cohomology.md`](../guide/topology/cohomology.md), [`docs/guide/topology/k_theory.md`](../guide/topology/k_theory.md), [`docs/guide/algebra/coalgebras_and_hopf.md`](../guide/algebra/coalgebras_and_hopf.md), and [`docs/guide/analysis/discrete_calculus.md`](../guide/analysis/discrete_calculus.md).

---

## Reference Implementation

Target files verified in the Second Grand Council Audit & Review:
- `src/algebrax/converters.py`, `src/algebrax/trie.py`, `src/algebrax/clifford.py`, `src/algebrax/tensor/core.py`
- `src/algebrax/topology/{homology.py,cohomology.py,dec.py,k_theory.py}`
- `src/algebrax/algebra/_hopf.py`, `src/algebrax/automata.py`, `src/algebrax/analysis/calculus.py`

---

## Rejected Ideas

1. **Keeping `AlgebraicTrie` Restricted to Zero-Arg Semiring Classes and Adding `ParameterizedTrie`**:
   - *Rejected*: Violates Shannon's minimalism; `Semiring.normalize()` handles instances, classes, and strings uniformly.
2. **Inventing a `VarietySemiring` Carrier in `variety/k_theory.py`**:
   - *Rejected*: `AffineVariety` requires `n_vars >= 1` (cannot represent $\mathbb{A}^0 = \mathbf{1}$), disjoint unions do not live in a single $\mathbb{A}^n$, and `motivic_point_count_homomorphism` is a crisp 7-line subtraction. Adding a synthetic semiring wrapper fails the Freshman Test.
3. **Greedy Contraction-Order Optimization in `tensor.einsum` in Phase 8.5**:
   - *Rejected*: Left-to-right hash-join indexing into a flat `dict` already resolves the $O(\prod \text{nnz})$ blowup cleanly without adding hypergraph-planning complexity.
4. **Parameterizing `topology/persistence.py` Over `ModularField(p)` in `EP-0252`**:
   - *Rejected*: Persistent homology over $\mathbb{F}_p$ involves boundary-matrix column reduction and belongs in a dedicated topology EP rather than semiring propagation.

---

## Open Questions

None. All Council review items (`is_algebraic_zero`, `Cochain`/`cup_product`, `pagerank`, `nfa_closure`, `VarietySemiring` drop, `einsum` order, and `persistence.py` deferral) are resolved.

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Explorer, Noether, Shannon, Russell).
* **2026-11-27:**
  * Incorporated Grand Council Pre-Implementation Review revisions: added shared `make_zero_predicate`/`is_algebraic_zero` in `converters.py`, moved `typing.N`/`RectSparseMatrix` to `EP-0251`, fixed `Cochain` orientation negation & `cup_product` tropical `0.0` bug, generalized `GroupHopfAlgebra` generics and Ring contract, resolved `pagerank` and `nfa_closure` specs (aligning with `EP-0250` on `StringSemiring`), ensured `CliffordAlgebra` picklability and flat-dict `einsum` accumulation, absorbed `automata`/`homology` defensive copies from `EP-0254`, dropped speculative `VarietySemiring`, added Acceptance Criteria and AMDS/guide checklist, and promoted status to `Accepted`.
