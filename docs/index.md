---
title: Introduction
description: Explore the algebrax library, providing algebraic primitives for sparse data structures in Python.
icon: lucide/info
---

# Introduction

![AlgebraX Banner](assets/images/banner.png){ align=center }

**Algebraic Primitives for Sparse Data Structures in Python**

`algebrax` treats Python's native `dict` (and `Mapping`) as a first-class sparse algebraic object, unifying linear algebra,
abstract algebra, graph algorithms, discrete geometry & topology, signal transforms, and information metrics under a
single pure-Python polymorphic framework.

---

## Quickstart

Install `algebrax` using your favorite package manager:

```shell
# Using uv (recommended)
uv add algebrax

# Using pip
pip install algebrax
```

---

## Core Philosophy

* ⚡ **Zero Heavy Dependencies**: Pure-Python core requiring no C++ compilation (`mappingtools` is the sole core runtime
  dependency), with optional bridges to NumPy, SciPy, and PIL.
* 🧱 **Deductive Algebraic Hierarchy (`algebrax.algebra`)**: Lean 4 / Mathlib-aligned `@runtime_checkable` protocols
  composed from **22 orthogonal atomic mixins** (`Has*`) — spanning `Magma`, `Monoid`, `Group`, `Lattice` &
  `BooleanAlgebra`, `Semiring` / `StarSemiring` / `KleeneAlgebra`, `Ring` / `Field`, `Ideal` / `QuotientRing`,
  `Module` / `Algebra`, and dual `Coalgebra` / `Bialgebra` / `HopfAlgebra`.
* 🔄 **Polymorphic Semiring Computing (`algebrax.semiring`)**: 33 built-in semirings and algebras. Swap $(\oplus, \otimes)$
  in `matrix.dot`, `tensor.einsum`, or `AlgebraicTrie` to compute linear algebra, tropical shortest paths, Viterbi
  probabilities, statistical moments, or symbolic rule provenance with identical code.
* 🎯 **Exact Drift-Free Linear Solvers (`algebrax.matrix`)**: Gaussian elimination, LU, QR, SVD, Cholesky, determinants,
  and matrix inversion parameterized over any `Field[V]` — including exact rationals (`StandardField(Fraction)`) and
  finite prime fields (`ModularField(p)`).
* 🌌 **Geometry, Symmetry & Algebraic Topology**: Multivector Clifford algebras $Cl(p,q,r)$ (`clifford`), classical &
  exceptional Lie algebras (`lie`), finite fields $\operatorname{GF}(p^m)$ (`galois`), and unified algebraic topology
  (`topology`: homology, cohomology cup products, persistent barcodes, DEC, and cellular sheaves).
* 🧪 **Axiomatic Law Verification (`algebrax.verification`)**: Automated axiom suites and multi-layered verification
  cross-checked against NumPy, SciPy, Hypothesis, Schwartz–Zippel PIT, and `z3-solver` SMT proofs.

---

## Overview

### 1. Polymorphic Semiring Matrix Multiplication

By changing the `semiring` parameter in `matrix.dot`, the exact same sparse algorithm switches seamlessly between
**Standard Linear Algebra**, **Tropical Shortest Paths**, and **Symbolic Provenance Tracking**:

```python
import algebrax as ax

# 1. Define a Sparse Graph Adjacency / Distance Matrix
graph = {
    0: {1: 2.0, 2: 10.0},
    1: {2: 3.0},
}

# Standard Linear Matrix Multiplication (+, *)
linear_mult = ax.matrix.dot(graph, graph, semiring=ax.semiring.StandardSemiring())
print('Linear Multiplication (0->2):', linear_mult[0][2])
# Output: 6.0 (2.0 * 3.0)

# Tropical Shortest Path (min, +)
shortest_path = ax.matrix.dot(graph, graph, semiring=ax.semiring.TropicalSemiring())
print('Shortest Path Cost (0->1->2):', shortest_path[0][2])
# Output: 5.0 (min(2.0 + 3.0, 10.0 + inf))

# Symbolic Provenance Rule Tracking
provenance_graph = {
    0: {1: {('rule_A',): 1}, 2: {('rule_C',): 1}},
    1: {2: {('rule_B',): 1}},
}
provenance_mult = ax.matrix.dot(provenance_graph, provenance_graph, semiring=ax.semiring.ProvenanceSemiring())
print('Symbolic Derivation Polynomial:', provenance_mult[0][2])
# Output: {('rule_A', 'rule_B'): 1}
```

### 2. Exact Drift-Free Solvers over Rational & Finite Fields

Parameterize sparse linear solvers over any `Field[V]` to eliminate IEEE-754 floating-point cancellation:

```python
from fractions import Fraction
from algebrax.algebra import ModularField, StandardField
from algebrax.matrix import det, solve

# Exact rational Hilbert matrix determinant over Q
h2 = {0: {0: Fraction(1, 1), 1: Fraction(1, 2)}, 1: {0: Fraction(1, 2), 1: Fraction(1, 3)}}
print(det(h2, field=StandardField(Fraction)))
# Output: Fraction(1, 12)

# Exact sparse linear system over prime field F_11
a = {'eq1': {'x': 3, 'y': 2}, 'eq2': {'x': 4, 'y': 9}}
b = {'eq1': 5, 'eq2': 1}
print(solve(a, b, field=ModularField(11)))
# Output: {'x': 4, 'y': 2}
```

---

## Architecture & Module Map

| Pillar | Submodules | Highlights |
|:-------|:-----------|:-----------|
| **Algebraic Foundations** | `algebra`, `semiring`, `group`, `lattice` | 22 orthogonal mixins, `Semiring`/`StarSemiring`/`KleeneAlgebra`, `Ring`/`Field`, `HopfAlgebra`, `ActionAlgebra`, `Ideal` & `QuotientRing` |
| **Linear & Tensor Computing** | `matrix`, `tensor`, `trie` | Sparse `dot`/`power`/`closure`, LU/QR/SVD/Cholesky, exact `Field` solvers, `einsum`, `AlgebraicTrie` |
| **Geometry, Symmetry & Topology** | `clifford`, `lie`, `galois`, `topology` | Clifford $Cl(p,q,r)$ rotors, Lie algebras ($\mathfrak{so}(3)$, $\mathfrak{e}_8$, BCH), $\operatorname{GF}(p^m)$, homology, cohomology, persistence, DEC & sheaves |
| **Dynamics, Categories & Tools** | `category`, `automata`, `transforms`, `analysis`, `probability`, `metrics`, `converters`, `display`, `verification` | Kleisli composition, DFA/NFA, DFT/Walsh–Hadamard/Z-transform, Fiedler/curvature, entropy, NumPy/SciPy bridges, Jupyter HTML/LaTeX cards, axiom verifiers |

---

## Next Steps

Explore the documentation sections:

* 💡 [**Core Concepts & Periodic Table of Mixins**](concepts.md): Learn the mathematical foundations of Atomic Mixins, Magmas, Monoids, Groups, Lattices, Semirings, Rings, Fields, Modules, Algebras, and Hopf Duality.
* ⚖️ [**Library Comparison**](comparison.md): Feature matrix and trade-off analysis comparing AlgebraX vs SciPy, NumPy, Pandas, NetworkX, and SymPy.
* 🛡️ [**Mathematical Verification & Stamp of Trust**](verification.md): Traceability matrix across differential NumPy/SciPy oracles, Hypothesis axioms, Schwartz–Zippel PIT, and `Z3` formal proofs.
* 📖 [**7-Tier User Guide**](guide/index.md): Deductive tour from single-operation Magmas and Monoids to Semirings, Rings, Exact Field Solvers, Clifford & Lie Algebras, Coalgebras & Hopf Algebras, Categories, and Topological Sheaves.
* 🍳 [**38 Use Cases, Recipes & GUI Lab**](recipes.md): Executable real-world scripts, synced Jupyter notebooks, and the interactive 12-module DearPyGui laboratory.
* 📜 [**Enhancement Proposals**](eps.md): Architectural design records and project roadmap.
