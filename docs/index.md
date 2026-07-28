---
title: Introduction
description: Explore the algebrax library, providing algebraic primitives for sparse data structures in Python.
icon: lucide/info
---

# Introduction

**AlgebraX: Algebraic Primitives for Sparse Data Structures in Python**

`algebrax` treats Python's native `dict` as a first-class sparse algebraic object, unifying linear algebra, graph
algorithms, formal language theory, signal transforms, and information metrics under a single polymorphic framework.

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

* ⚡ **Zero Heavy Dependencies**: Built entirely with pure Python, requiring no heavy external libraries or C++
  compilation. Includes native conversion between sparse dict representations and dense multidimensional arrays.
* 🔄 **Polymorphic Semiring Computing**: By changing the algebraic semiring $(\oplus, \otimes)$, the exact same matrix
  algorithms compute standard linear algebra, tropical shortest path latencies, or symbolic rule provenance.
* 🌌 **Sparse Multidimensional Tensors**: Arbitrary nested mappings behave as infinite-dimensional sparse tensors, tries,
  and lattices with custom key operators.

---

## Overview

Below is a 10-line demonstration showing how swapping the semiring parameter in `matrix.dot` changes matrix
multiplication from **Standard Linear Algebra** to **Tropical Shortest Path** and **Symbolic Provenance Tracking**:

```python
from algebrax.matrix import dot
from algebrax.semiring import DigitalSemiring, ProvenanceSemiring, StandardSemiring, TropicalSemiring

# 1. Define a Sparse Graph Adjacency / Distance Matrix
graph = {
    0: {1: 2.0, 2: 10.0},
    1: {2: 3.0},
}

# Standard Linear Matrix Multiplication (+, *)
linear_mult = dot(graph, graph, semiring=StandardSemiring())
print("Linear Multiplication (0->2):", linear_mult[0][2])
# Output: 30.0 (path combination weight)

# Tropical Shortest Path (min, +)
shortest_path = dot(graph, graph, semiring=TropicalSemiring())
print("Shortest Path Cost (0->1->2):", shortest_path[0][2])
# Output: 5.0 (min(2 + 3, 10 + inf))

# Symbolic Provenance Rule Tracking
provenance_graph = {
    0: {1: {("rule_A",): 1}, 2: {("rule_C",): 1}},
    1: {2: {("rule_B",): 1}},
}
provenance_mult = dot(provenance_graph, provenance_graph, semiring=ProvenanceSemiring())
print("Symbolic Derivation Polynomial:", provenance_mult[0][2])
# Output: {('rule_A', 'rule_B'): 1}
```

---

## Next Steps

Explore the documentation sections:

* 💡 [**Core Concepts**](concepts.md): Learn the mathematical foundations of Monoids, Groups, Semirings, and Lattices.
* 📖 [**Tutorials**](tutorials/semirings/semiring_standard.md): Step-by-step guides for 11 semirings, tries, signal
  transforms, and graph algorithms.
* 🍳 [**Use Cases & Recipes**](recipes.md): Executable real-world scripts, Jupyter notebooks, and the interactive
  DearPyGui laboratory.
