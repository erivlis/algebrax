---
title: "EP-0001: The Mathematical Manifesto, Core Invariants & Foundational Canon"
description: "Establishes the foundational constitution of AlgebraX: the five Grand Council invariants, the four-tier architecture, and the master roadmap for the single-digit foundational canon."
icon: lucide/scroll
status: draft
---

# EP-0001: The Mathematical Manifesto, Core Invariants & Foundational Canon

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0001                                                                              |
| **Title**         | The Mathematical Manifesto, Core Invariants & Foundational Canon                  |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | The Grand Council                                                                 |
| **Delegate**      | 🧩 Russell (Taxonomy), ⚖️ Noether (Symmetry), ⚡ Shannon (Zero Overhead)            |
| **Status**        | Draft                                                                             |
| **Type**          | Process                                                                           |
| **Created**       | 2026-11-12                                                                        |
| **Updated**       | 2026-11-12                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the permanent constitutional foundation of `algebrax`. Drawing upon four decades of lessons from computer algebra systems (Axiom, GAP 4, SageMath) and modern dependently typed proof assistants (Lean 4 Mathlib, Coq Mathematical Components), this document formalizes:
1. **The Core Invariants**: The five non-negotiable architectural mandates of the Grand Council (Shannon zero-boxing efficiency, Russell deductive type theory, Popperian falsifiability, Noether symmetry, and Feynman pedagogical clarity).
2. **The Four-Tier Architecture**: A strict conceptual separation between Core Storage Primitives (Tier 1), The Foundational Canon (Tier 2), Specialized Mathematical Continents (Tier 3), and Empirical Exploration Studios (Tier 4).
3. **The Single-Digit Foundational Canon (`EP-0001`–`EP-0006`)**: Defining the complete sequence of constitutional proposals governing notations, verification oracles, unboxed carriers, algebraic protocol composition, and universal morphisms.

---

## Motivation

As `algebrax` evolved from a semiring matrix prototype into a comprehensive computational algebra framework spanning Lean 4 Mathlib-aligned algebraic hierarchies, discrete exterior calculus, Clifford geometric algebras, fiber bundles, and quantum algebras, architectural decisions risked becoming ad-hoc or fragmented. 

Without a singular constitutional manifesto:
- **Seed Domains Confounded with Foundations**: Early concrete domains (such as semirings or simplicial complexes) were at risk of being treated as foundational architecture rather than domain-specific mathematical modules.
- **Type Erasure vs. Axiom Blindness**: Structural typing (`typing.Protocol`) risked reducing mathematically rich structures to mere syntactic function signatures, conflating Lie algebras with Jordan algebras or rings with commutative rings.
- **Creeping Allocation Bloat**: The temptation to wrap mathematical objects in object-oriented class instances threatened the pure-Python zero-overhead sparse matrix engine.

`EP-0001` serves as the supreme constitutional document of AlgebraX, providing an immutable reference against which all subsequent Enhancement Proposals, code contributions, and refactorings must be measured.

---

## Rationale & Council Alignment

The manifesto is built upon the five core pillars of the Grand Council:

### 1. ⚡ Claude Shannon (Zero Overhead & Native Carrier Invariance)
- Mathematical objects must not be burdened with heap-allocated wrapper instances.
- Scalars are native Python numbers (`float`, `int`, `complex`); vectors and matrices are native sparse dictionaries (`dict[K, V]`, `dict[R, dict[C, V]]`); coordinates are native tuples (`tuple[int, ...]`).
- Abstractions must be computationally transparent: zero allocations for law witnesses, zero memory penalty for protocol conformance.

### 2. 🧩 Bertrand Russell (Deductive Soundness & The Theory of Types)
- A type system must distinguish signature ($\Sigma$) from equational theory ($E$).
- Hierarchy composition must be flat and diamond-free (**Law of Flat Protocol Composition**).
- No self-referential paradoxes or circular dependencies are permitted between algebraic layers.

### 3. 🔬 Karl Popper (Falsifiability & Empirical Testing)
- Every mathematical claim made by an algebraic structure is a testable hypothesis.
- "The happy path is a lie": implementations must be accompanied by property-based randomized falsification oracles (Hypothesis) and automated verification suites (`algebrax.verification`).

### 4. ⚖️ Emmy Noether (Symmetry, Conservation & Duality)
- Algebraic and geometric dualities must be preserved faithfully:
  - Vector vs. Dual Co-vector ($V \cong V^*$).
  - Boundary vs. Coboundary ($\partial_k^\top = d^{k-1}$).
  - Commutator symmetry vs. Anticommutator symmetry ($[x, y] = -[y, x]$ vs. $x \circ y = y \circ x$).
- Transformations must conserve structural invariants.

### 5. 💡 Richard Feynman (The Freshman Test & Demystification)
- Mathematics must not hide behind esoteric jargon.
- If a concept cannot be explained cleanly to an undergraduate and computed directly in three lines of Python, the abstraction is deficient.
- The code must invite exploration, wonder, and physical intuition.

---

## Specification

### 1. The Four-Tier Architecture of AlgebraX

To maintain absolute modular clarity, all code, proposals, and artifacts in AlgebraX belong strictly to one of four tiers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Tier 4: Empirical Application Layer & Interactive Studios              │
│   • recipes/lab.py (32 Real-Time Interactive Desktop Sandboxes)        │
│   • recipes/*.ipynb (Use-Case Notebooks & Computational Simulations)   │
│   • site/explorer/ (EP-0120 Zero-Dependency Browser Visual Studio)     │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 3: Specialized Domain Modules (Concrete Mathematics)              │
│   • algebrax.clifford, lie, topology, representation, quantum, ...     │
│   • Specific Domain EPs (EP-0100 through EP-0215)                      │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 2: The Foundational Canon (Constitutional Single-Digit EPs)       │
│   • EP-0000 through EP-0006                                            │
├────────────────────────────────────────────────────────────────────────┤
│ Tier 1: Core Storage Primitives & Pure Python Runtime                  │
│   • Native dict, tuple, SparseMatrix, SparseVector                     │
└────────────────────────────────────────────────────────────────────────┘
```

- **Tier 1 (Storage Primitives)**: Pure Python builtins representing unboxed sparse data.
- **Tier 2 (Foundational Canon)**: Universal, domain-agnostic rules governing notation, testing, typing, protocols, and morphisms.
- **Tier 3 (Domain Continents)**: Concrete mathematical structures (Lie algebras, Clifford geometric algebra, sheaf Laplacians, Galois fields, representation theory).
- **Tier 4 (Empirical Layer)**: Standalone computational notebooks, simulation recipes, and interactive GUI/Web explorers that validate theory against real-world physics and engineering.

---

### 2. The Single-Digit Foundational Canon

The single-digit block (`EP-0000` through `EP-0006`) is reserved exclusively for universal, cross-cutting constitutional specifications:

| Foundational EP | Title | Constitutional Focus |
|:---|:---|:---|
| **`EP-0000`** | **Enhancement Proposals & Council Governance** | The formal PEP-style proposal lifecycle, statuses, and Grand Council review workflows. *(Active)* |
| **`EP-0001`** | **The Mathematical Manifesto, Core Invariants & Foundational Canon** | *This Document.* The supreme constitutional charter, Council invariants, four-tier hierarchy, and canon roadmap. |
| **`EP-0002`** | **Mathematical Docstring Standards & Algebraic Signatures (AMDS)** | Universal docstring standards: KaTeX display equations, formal algebraic signature blocks ($\langle V, \cdot \rangle$), and automated documentation introspection. |
| **`EP-0003`** | **Axiomatic Verification & Property-Based Falsification** | The universal testing engine (`algebrax.verification`): randomized Hypothesis fuzzing, tolerance verification for floating-point carriers, Schwartz–Zippel polynomial identity testing, and SMT/Z3 certificates. |
| **`EP-0004`** | **Unboxed Storage & Sparse Carrier Invariance** | Technical specification of the native carrier rule: `SparseVector[K, V]`, `SparseMatrix[R, C, V]`, multi-index coordinate tuples, and zero-wrapper algorithms. |
| **`EP-0005`** | **Universal Algebraic Protocol Architecture** | The 3-pillar protocol framework: Layer 1 Operational Mixins (`Has*`), Layer 1 Law Witness Mixins (`Law*`), Layer 2 Flat Protocols, and Characteristic Derived Methods (supersedes EP-0194, incorporates EXP-0008). |
| **`EP-0006`** | **Morphisms, Homomorphisms & Structural Mappings** | Universal maps between structures: `Homomorphism`, `RingHom`, `GroupHom`, `LinearMap`, functors, natural dualities, and category-theoretic arrows. |

---

### 3. Concrete Domain Modules Belong in Dedicated Tracks

Domain-specific subjects (such as semiring catalogs, homology, differential forms, or quantum groups) must **never** occupy single-digit foundational EP numbers. They belong to their respective domain tracks:
- **`EP-0100` – `EP-0109`**: Foundational Engine Extensions (Quotient Monoids, Chain Complexes).
- **`EP-0110` – `EP-0119`**: Classical Domain Modules (Simplicial Homology, Clifford GA, Galois Fields, Kleisli Categories).
- **`EP-0120` – `EP-0129`**: Visual & Interactive Studios (Web Explorer, Desktop Lab).
- **`EP-0160` – `EP-0179`**: Continuous Symmetries & Geometric Calculus (DEC, Lie Algebras, Root Systems).
- **`EP-0180` – `EP-0189`**: Multi-Layered Correctness Evidence Suites.
- **`EP-0190` – `EP-0199`**: Granular Lean 4 Mathlib Alignment & Canonical Consolidations.
- **`EP-0200` – `EP-0219`**: Categorical DEC, Fiber Bundles, Quantum/Non-Associative Algebras, and Representations.

---

## Backwards Compatibility

This proposal is an overarching process and architectural document; it introduces no breaking code changes to the library runtime. It establishes the governing standards under which all existing and future code is organized.

---

## How to Teach This / Documentation Plan

1. **Repository Root Alignment**:
   - Update `PRINCIPLES.md` to reference `EP-0001` as the formal constitutional specification of the Council Framework.
2. **Developer Documentation (`AGENTS.md` & `CONTRIBUTING.md`)**:
   - Instruct AI agents and human contributors to verify any new proposal against the 4-tier model and the 5 Council Invariants before submitting.
3. **Public Documentation Site**:
   - Highlight the Manifesto on the documentation landing page as the guiding philosophy of AlgebraX.

---

## Reference Implementation

- **Research Compendium**: `references/explorations/EXP-0008-equational-theories-and-typeclass-axioms/README.md`.
- **Precedent Foundational Documents**:
  - `PRINCIPLES.md` (Repository Root)
  - [`docs/proposals/EP-0000-process.md`](EP-0000-process.md)
  - [`docs/proposals/EP-0099-expansion-roadmap.md`](EP-0099-expansion-roadmap.md)

---

## Rejected Ideas

1. **Assigning Concrete Domains to Single-Digit EPs (e.g., EP-0005 Semirings, EP-0006 DEC)**:
   *Rejected*: Conflates early historical implementation seeds with universal architectural foundations. As AlgebraX expanded, semirings and DEC became concrete domains alongside Clifford, Lie, and Representation theory. Single-digit EPs must remain strictly domain-agnostic.
2. **Object-Oriented Element Boxing (`class Vector`, `class Element`)**:
   *Rejected*: Violates the Shannon Carrier Invariant. Wrapping numbers or sparse entries in Python class instances degrades performance and memory density by orders of magnitude.
3. **Deep Chained Protocol Inheritance**:
   *Rejected*: Violates Russell's mandate against diamond inheritance. Handled by the Law of Flat Protocol Composition in `EP-0005`.

---

## Open Questions

1. **Migration of Existing EP-0150 and EP-0180**:
   Should `EP-0150` (Docstrings) and `EP-0180` (Verification) be formally superseded by `EP-0002` and `EP-0003`?
   *Recommendation*: Yes. `EP-0002` and `EP-0003` will synthesize and elevate them into permanent foundational canon.

---

## Change Log

- **2026-11-12**: Initial constitutional draft authored following Grand Council consensus.
