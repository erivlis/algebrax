---
title: "EP-0004: Unboxed Storage & Sparse Carrier Invariance"
description: "Codifies the Shannon Carrier Invariant: native unboxed dictionaries, sparse matrix and vector primitives, coordinate tuple keys, and the strict ban on heap-allocated element wrappers."
icon: lucide/box
status: draft
---

# EP-0004: Unboxed Storage & Sparse Carrier Invariance

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0004                                                                              |
| **Title**         | Unboxed Storage & Sparse Carrier Invariance                                       |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | The Grand Council                                                                 |
| **Delegate**      | ⚡ Claude Shannon (Efficiency) & 🛡️ The Golem (Safety & Immutability)              |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-11-12                                                                        |
| **Updated**       | 2026-11-12                                                                        |
| **Replaces**      | [EP-0153](EP-0153-semiring-matrix-symmetry-and-vector-primitives.md) (Carrier Spec)|
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal codifies the primary data-representation standard of `algebrax`: **The Shannon Carrier Invariant**. As mandated by [EP-0001](EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md), mathematical abstractions must never penalize computational performance through unnecessary heap allocations or object-oriented wrapping.

Specifically, this proposal establishes:
1. **The Native Unboxed Carrier Rule**: All mathematical carriers are pure Python native primitives:
   - Scalars are native numbers (`float`, `int`, `complex`).
   - Vectors are native sparse mappings: `SparseVector[K, V] = Mapping[K, V]`.
   - Matrices are native nested sparse mappings: `SparseMatrix[K, V] = Mapping[K, Mapping[K, V]]`.
   - Simplicial and tensor coordinates are native tuples: `tuple[K, ...]`.
2. **The Absolute Ban on Element Boxing**: Prohibiting wrapper classes (such as `class Element`, `class Vector`, `class Octonion`, or `class MatrixEntry`) that box values into heap instances.
3. **Canonical Sparse Vector & Matrix Micro-Kernels**: High-performance, semiring-parameterized primitives (`vec_add`, `vec_scale`, `vec_axpy`, `vec_norm`, `vec_clean`, `matrix.add`, `matrix.dot`, `matrix.trace`) operating directly on unboxed dictionary entries.

---

## Motivation

In scientific and algebraic computing, object-oriented designs frequently fall into the **Wrapper Trap**: wrapping every vector entry or matrix cell in a specialized class instance.

While this allows syntactic sugar like `v1 + v2`, it incurs catastrophic computational penalties in Python:
1. **Memory Bloat**: A 64-bit float is 24 bytes in Python. Wrapping it in a custom class instance inflates it to $> 150$ bytes—a $6\times$ to $10\times$ memory blowup that destroys CPU L1/L2/L3 cache locality.
2. **Allocation Overhead**: Allocating and garbage-collecting millions of wrapper objects inside tight matrix multiplication or Hodge Laplacian relaxation loops destroys throughput.
3. **Impedance Mismatch with Scientific Ecosystems**: Heavy custom wrapper objects cannot be losslessly and instantaneously converted to or from NumPy arrays, SciPy CSR matrices, or JSON/database records.

By keeping carriers **unboxed** (plain dictionaries, tuples, and numbers) and placing all algebraic logic into **stateless algebraic structures and protocols** (the separation of Data Carrier $M$ from Algebraic Structure $A$), AlgebraX achieves maximal throughput, minimal memory footprint, and instantaneous cross-library interoperability.

---

## Rationale & Council Alignment

- **⚡ Claude Shannon (The Carrier Invariant & Minimal Entropy)**:
  A sparse vector $\{0: 1.5, 5: -2.0\}$ contains exactly the information needed to represent the state, and nothing more. Zero wrapper noise, zero auxiliary pointers.
- **🛡️ The Golem (Immutability & Safety by Default)**:
  Unboxed carrier operations return *new* sparse dictionaries rather than mutating in place. This guarantees that mathematical operations are pure functions without hidden side effects.
- **🧩 Bertrand Russell (Separation of Data from Theory)**:
  In Principia Mathematica, an element of a set does not contain the definition of the set within itself. A sparse matrix does not contain the definition of a Ring; the `Ring` or `Algebra` is an external algebraic operator that acts upon the carrier data.
- **💡 Richard Feynman (The Freshman Test & Transparency)**:
  When a student inspects an octonion or a sparse matrix in a debugger, they see plain readable Python dicts: `{1: 1.0, 2: -0.5}` or `{0: {1: 5.0}}`. No layers of private wrapper classes or opaque pointer indirection.

---

## Specification

### 1. The Canonical Carrier Types ([`src/algebrax/typing.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/typing.py))

```python
from collections.abc import Mapping, Sequence
from typing import TypeAlias, TypeVar

K = TypeVar('K')  # Hashable key type (int, str, tuple[int, ...])
V = TypeVar('V')  # Element value type (float, int, complex)

# 1. Unboxed Sparse Vector
SparseVector: TypeAlias = Mapping[K, V]
# Example: {0: 1.5, 3: -2.0}

# 2. Unboxed Sparse Matrix (Nested Dictionary)
SparseMatrix: TypeAlias = Mapping[K, Mapping[K, V]]
# Example: {0: {1: 2.5, 2: -1.0}, 1: {0: 3.0}}

# 3. Unboxed Simplex / Coordinate Multi-Index
Simplex: TypeAlias = tuple[K, ...]
# Example: (0, 1, 2) represents an oriented 2-simplex triangle.

# 4. Dense Views (Sequences)
DenseVector: TypeAlias = Sequence[V]
DenseMatrix: TypeAlias = Sequence[Sequence[V]]
```

---

### 2. The Strict Ban on Element Boxing

Under **EP-0004**, the following patterns are **permanently prohibited** in AlgebraX:

```python
# ❌ PERMANENTLY PROHIBITED (The Wrapper Trap):
class MatrixElement:
    def __init__(self, row: int, col: int, val: float): ...

class Octonion:
    def __init__(self, e0: float, e1: float, ...): ...

class SimplicialCochain:
    def __init__(self, data: dict):
        self._internal_wrapper = data
```

Instead, all algorithms and protocols operate directly on unboxed carriers:
```python
# ✅ THE ALGEBRAX STANDARD (Unboxed Carrier + Stateless Algebra):
octo_algebra = OctonionAlgebra()
x: dict[int, float] = {1: 1.0, 4: -2.0}
y: dict[int, float] = {2: 1.5}
z = octo_algebra.mul(x, y)  # Returns unboxed dict[int, float]!
```

---

### 3. Canonical Vector & Matrix Micro-Kernels

The standard operations on unboxed carriers are provided by stateless functional micro-kernels:

#### 3.1 Sparse Vector Operations (`algebrax.matrix`)
- `vec_add(u, v, semiring=...) -> dict[K, V]`
- `vec_scale(c, v, semiring=...) -> dict[K, V]`
- `vec_axpy(a, x, y, semiring=...) -> dict[K, V]` ($\mathbf{y} \leftarrow a\mathbf{x} \oplus \mathbf{y}$)
- `vec_norm(v, p=2) -> float`
- `vec_clean(v, tol=1e-15) -> dict[K, V]` (prunes near-zero entries)

#### 3.2 Sparse Matrix Operations (`algebrax.matrix.core`)
- `matrix.add(A, B, semiring=...) -> SparseMatrix[K, V]`
- `matrix.dot(A, B, semiring=...) -> SparseMatrix[K, V]`
- `matrix.mat_vec(A, v, semiring=...) -> SparseVector[K, V]`
- `matrix.vec_mat(v, A, semiring=...) -> SparseVector[K, V]`
- `matrix.trace(A, semiring=...) -> V`
- `matrix.transpose(A) -> SparseMatrix[K, V]`

All operations respect the given `Semiring`'s additive identity $\mathbb{0}$ for annihilation and sparsity pruning.

---

## Backwards Compatibility

1. **Preserves Existing Code**: All existing code in `src/algebrax` already uses unboxed dictionary carriers.
2. **Elevates EP-0153**: The carrier specifications from `EP-0153` are canonized and elevated to foundational status in `EP-0004`.

---

## How to Teach This / Documentation Plan

- **User Guide**: `docs/guide/matrix/sparse_storage.md` details why unboxed sparse dictionaries outperform heavy classes and demonstrates zero-copy conversions to/from NumPy arrays.
- **Architectural Rules**: AI agents and contributors must ensure that any new algebra (e.g. quantum groups, Clifford bivectors) represents elements using native sparse dictionaries or tuples, never wrapper classes.

---

## Reference Implementation

- **Carrier Definitions**: [`src/algebrax/typing.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/typing.py).
- **Matrix Kernels**: [`src/algebrax/matrix/core.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/matrix/core.py).
- **Vector Kernels**: [`src/algebrax/matrix/__init__.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/matrix/__init__.py).

---

## Rejected Ideas

1. **Boxing Multivectors and Octonions into `class Octonion`**:
   *Rejected*: Storing basis elements in sparse `dict[int, float]` allows arbitrary sparse linear combinations with zero allocation overhead.
2. **In-Place Mutation (`u.add_in_place(v)`)**:
   *Rejected*: Violates the Golem's mandate of immutability and pure functional safety. In-place mutation creates race conditions in parallel algorithms and ruins mathematical referential transparency.

---

## Open Questions

None. The unboxed sparse dictionary architecture has been the performance bedrock of AlgebraX across all releases.

---

## Change Log

- **2026-10-16**: Vector primitives and carrier symmetries specified in EP-0153.
- **2026-11-12**: Codified as the permanent Shannon Carrier Invariant in EP-0004.
