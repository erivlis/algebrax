---
title: "EP-0193: Documentation Architecture Realignment with Pure Algebraic Hierarchy"
description: "Restructure AlgebraX user documentation around the Lean 4-aligned pure algebraic hierarchy, establishing a deductive architectural narrative from magmas to geometric algebras and topological sheaves."
icon: lucide/book-open
status: draft
---

# EP-0193: Documentation Architecture Realignment with Pure Algebraic Hierarchy

| Field             | Value                                                                 |
|:------------------|:----------------------------------------------------------------------|
| **EP**            | 0193                                                                  |
| **Title**         | Documentation Architecture Realignment with Pure Algebraic Hierarchy  |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                           |
| **Sponsor**       | Core Maintainers                                                      |
| **Delegate**      | 💡 Feynman (Clarity & Pedagogy) & 🧩 Russell (Taxonomy & Consistency) |
| **Status**        | Draft                                                                 |
| **Type**          | Standards Track                                                       |
| **Created**       | 2026-10-27                                                            |
| **Updated**       | 2026-10-27                                                            |
| **Replaces**      | —                                                                     |
| **Superseded-By** | —                                                                     |

---

## Abstract

This proposal establishes a structural overhaul of the AlgebraX documentation architecture, realigning all guides,
catalogs, and conceptual documentation around the **Lean 4 Mathlib-aligned Pure Algebraic Hierarchy** introduced in
**EP-0190**, **EP-0191**, and **EP-0192**. The current documentation reflects a legacy "semiring-first" taxonomy where
seven dedicated modules cover semirings, while higher-order structures (Rings, Fields, Modules, Vector Spaces,
Associative and Non-Associative Algebras) and domain entities (Lie Algebras, Clifford Geometric Algebras, DEC Cochains,
Cellular Sheaves) are fragmented across ad-hoc buckets like `Discrete, Automata & Category` or `Transforms & Analysis`.

Following unanimous Grand Council review (Noether, Popper, Shannon, The Golem, Feynman, Russell, The Explorer), EP-0193
adopts the **Inverted 4-Beat Chapter Arc** (Hook $\to$ Snippet $\to$ Protocol Contract $\to$ Falsifiability), integrates
a **Jargon Decoder** and **Domain Elevators**, fully accounts for all existing pages (tensors, probability, benchmarks)
to eliminate orphan dead weight, and mandates automated snippet execution via `markdown-pytest` in CI.

---

## Motivation

AlgebraX originated as a lightweight engine for generalized matrix multiplication over semirings. Through successive
expansion phases, the framework evolved into a comprehensive pure mathematical and computational substrate featuring:

- **Phase 4**: Discrete Exterior Calculus (EP-0160), Cellular Sheaves (EP-0161), Persistent Homology (EP-0162), and Lie
  Algebras / Root Systems (EP-0163, EP-0164).
- **Phase 5**: Multi-layered axiomatic property-based testing, comparative oracles, and SMT solver verification
  (EP-0180–EP-0186).
- **Phase 6**: Granular sub-semirings (Magmas, Semigroups, Monoids, Groups, Lattices in EP-0190), super-semirings
  (Rings, Fields, Modules, Algebras in EP-0191), and domain object unification (EP-0192).

Despite this structural maturity, the documentation structure remained anchored to its early design:

1. **The "Semiring-Centric Silo"**:
   The *User Guide* devotes seven top-level chapters exclusively to semiring catalogs, yet relegates Rings, Fields,
   Groups, Modules, and Lie Algebras to isolated, nested sub-sections.
2. **Artificial Taxonomic Fragmentation**:
    - `CliffordSemiring` is listed under `guide/semirings/algebraic.md`, obscuring its identity as a full Clifford
      Geometric Algebra over multivector spaces.
    - `LieAlgebra` is placed under `guide/discrete/lie_algebras.md`, divorced from its algebraic parentage as a
      non-associative algebra.
    - `Cochain` and discrete forms are separated from the Module/Vector Space foundations that give them their linear
      structure.
    - Arbitrary umbrella categories like `Discrete, Automata & Category` lump together unrelated concepts (automata,
      category theory, Lie algebras, ring protocols).
3. **The Obscured Axiom Staircase**:
   New users and mathematicians are not presented with the natural deductive progression:
   $$\text{Magma} \longrightarrow \text{Monoid} \longrightarrow \text{Semiring} \longrightarrow \text{Ring} \longrightarrow \text{Field} \longrightarrow \text{Module} \longrightarrow \text{Algebra}$$
   Consequently, users struggle to discern *which* algebraic level unlocks *which* computational capability (e.g.,
   shortest paths vs. PageRank vs. exact nullspaces vs. spatial rotations).

EP-0193 resolves this debt by reorganizing the entire user guide, navigation tree, and conceptual documentation along
the pure algebraic hierarchy.

---

## Rationale & Council Alignment

### 💡 Feynman (Clarity, Pedagogy & The Freshman Test)

Avoids the "Bourbaki Trap" of front-loading dry abstract axioms. Introduces the **Inverted 4-Beat Chapter Flow**
(Problem $\to$ 30-Second Executable Snippet $\to$ Formal Contract $\to$ Falsifiable Verification), provides a "Hacker's
Translation Box" (Jargon Decoder), and builds "Fast-Track Elevators" so practitioners can jump directly to their target
domain.

### 🧩 Russell (Taxonomy, Ontological Integrity & Deductive Order)

Eliminates taxonomic overlap and collision. Directly mirrors the protocol taxonomy established in
`src/algebrax/algebra/` and the domain bindings from `EP-0192`. Single-sorted structures $\langle V \rangle$ are cleanly
segregated from two-sorted modules and algebras $\langle R, M \rangle$. Fully reconciles legacy paths like
`guide/discrete/algebra.md`.

### ⚖️ Noether (Structural Symmetry, Conservation & Duality)

Unifies geometric algebras (Clifford) and non-associative algebras (Lie) under the common conceptual roof of linear
algebras over modules. In Tier 5, highlights the core dualities of discrete topology: chain-cochain adjointness
($\langle \delta \omega, c \rangle = \langle \omega, \partial c \rangle$), boundary nilpotency
($\partial^2 = 0 \iff \delta^2 = 0$), and Hodge star duality ($*$).

### 🔬 Popper (Falsifiability & Executable Documentation)

Mandates that all documentation code blocks are executed during CI via `markdown-pytest`
(`pytest --markdown-docs docs/guide/`). Every chapter pairs positive law verification (`verify_*_laws`) with negative
counterexamples demonstrating where specific axioms break (e.g., zero divisors in $\mathbb{Z}/4\mathbb{Z}$ breaking
field invertibility; non-associativity in $\mathfrak{so} (3)$ brackets).

### ⚡ Shannon (Zero Bloat, Navigational Ergonomics & Zero Orphan Pages)

Integrates previously omitted sections (tensors, probability, benchmarks) into the 7-tier navigation tree, ensuring zero
orphan dead weight. Maintains flat, scannable sidebar navigation using `navigation.expand` to minimize click-depth
latency.

### 🛡️ The Golem (Type Safety, Strict Contracts & Build Integrity)

Enforces `zensical build --strict` in CI to prevent broken anchors or dead cross-references. Mandates that chapters
document error preconditions (such as `ZeroDivisionError` on non-invertible elements).

### 🧭 The Explorer (Curiosity & Frontier Synthesis)

Adds a mandatory **Frontier Horizons & Cross-Domain Bridges** section to each chapter, connecting discrete structures
with spacetime algebra, Conformal Geometric Algebra ($C\ell (4, 1)$), Jordan algebras, and Differential Graded Algebras
(DGAs).

---

## Specification

### 1. New Documentation Architecture (`zensical.toml`)

The User Guide navigation tree is restructured into seven coherent, deductively ordered sections, fully accounting for
all codebase assets:

```toml
nav = [
    { Home = "index.md" },
    { "Concepts & Architecture" = "concepts.md" },
    { Principles = "principles.md" },
    { "User Guide" = [
        { "Getting Started" = "guide/index.md" },
        { "Core Matrix Engine" = "guide/matrix/core.md" },
        { "1. Single-Operation Structures" = [
            "guide/algebra/magmas_and_monoids.md",
            "guide/algebra/groups_and_symmetries.md",
        ] },
        { "2. Two-Operation Systems" = [
            "guide/algebra/lattices_and_order.md",
            "guide/algebra/semirings_overview.md",
            "guide/semirings/arithmetic.md",
            "guide/semirings/optimization.md",
            "guide/semirings/statistical.md",
            "guide/semirings/logic.md",
            "guide/semirings/structures.md",
            "guide/semirings/verification.md",
        ] },
        { "3. Additive Inverses (Rings & Fields)" = [
            "guide/algebra/rings_and_fields.md",
            "guide/algebra/polynomials_and_quotients.md",
            "guide/algebra/exact_matrix_solvers.md",
        ] },
        { "4. Two-Sorted Systems (Modules, Algebras & Tensors)" = [
            "guide/algebra/modules_and_vector_spaces.md",
            "guide/algebra/clifford_geometric_algebra.md",
            "guide/algebra/lie_algebras.md",
            "guide/tensor/trie.md",
            "guide/tensor/einsum.md",
        ] },
        { "5. Discrete Geometry & Topology" = [
            "guide/topology/homology.md",
            "guide/topology/cohomology.md",
            "guide/topology/persistence.md",
            "guide/topology/dec.md",
            "guide/topology/sheaf.md",
        ] },
        { "6. Categories, Automata & Dynamics" = [
            "guide/discrete/category.md",
            "guide/discrete/automata.md",
            "guide/probability/information.md",
            "guide/transforms/spectral.md",
            "guide/analysis/discrete_calculus.md",
        ] },
        { "7. Ecosystem Bridges & Decompositions" = [
            "guide/matrix/decompositions.md",
            "guide/matrix/benchmarks.md",
            "guide/matrix/academic.md",
        ] },
    ] },
    { Recipes = [
        "recipes.md",
    ] },
    { Proposals = [
        "eps.md",
    ] },
]
```

---

### 2. Migration & Content Realignment Matrix

| Current Path                          | New Planned Path                                                                    | Primary Focus & Algebraic Role                                                           |
|:--------------------------------------|:------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------|
| `guide/algebra/hierarchy.md`          | `guide/algebra/magmas_and_monoids.md` & `groups_and_symmetries.md`                  | Granular sub-semiring protocols (Magma, Monoid, Group, Additive/Multiplicative variants) |
| `guide/algebra/rings_and_fields.md`   | `guide/algebra/rings_and_fields.md` (expanded)                                      | Rings, Commutative Rings, Division Rings, Fields, Galois Fields                          |
| `guide/semirings/algebraic.md`        | `guide/algebra/polynomials_and_quotients.md` & `clifford_geometric_algebra.md`      | Split: Polynomial/Dual Numbers to Rings; Clifford to Associative Algebra                 |
| `guide/discrete/lie_algebras.md`      | `guide/algebra/lie_algebras.md`                                                     | Relocated: Non-associative algebra, Jacobi identity, root systems, BCH solver            |
| `guide/discrete/algebra.md`           | Redirect stub $\to$ `guide/algebra/magmas_and_monoids.md` & `lattices_and_order.md` | Legacy page cleanly split into Groups and Lattices                                       |
| `guide/topology/homology.md`          | `guide/topology/homology.md` (retained)                                             | Simplicial chain complexes, boundary nilpotency $\partial^2 = 0$, Betti numbers          |
| `guide/topology/cohomology.md`        | `guide/topology/cohomology.md` (retained)                                           | Simplicial cochains, Alexander-Whitney cup product $\smile$, cohomology ring             |
| `guide/topology/persistence.md`       | `guide/topology/persistence.md` (retained)                                          | Persistent homology, boundary matrix reduction over $\mathbb{Z}_2$, topological barcodes |
| `guide/topology/dec.md`               | `guide/topology/dec.md` (retained)                                                  | Discrete Exterior Calculus, differential forms as cochains, Hodge star $*$, Stokes       |
| `guide/topology/sheaf.md`             | `guide/topology/sheaf.md` (retained)                                                | Cellular sheaves over complexes, restriction maps, sheaf Laplacians                      |
| `guide/transforms/spectral.md`        | `guide/transforms/spectral.md` (retained)                                           | Graph Laplacians, spectral embedding, random walk with restart                           |
| `guide/analysis/discrete_calculus.md` | `guide/analysis/discrete_calculus.md` (retained)                                    | Discrete calculus, graph divergence, gradient, and Dirichlet energy                      |
| `guide/discrete/category.md`          | `guide/discrete/category.md` (retained)                                             | Categorical morphisms, Kleisli composition, Kan extensions                               |
| `guide/discrete/automata.md`          | `guide/discrete/automata.md` (retained)                                             | Semiring-weighted automata, regular expressions, shortest path transducers               |
| `guide/tensor/trie.md`                | `guide/tensor/trie.md` (retained)                                                   | Sparse tensor representation, Algebraic Trie contraction                                 |
| `guide/tensor/einsum.md`              | `guide/tensor/einsum.md` (retained)                                                 | Multi-index einsum contractions over semirings and rings                                 |
| `guide/probability/information.md`    | `guide/probability/information.md` (retained)                                       | Information entropy, divergence, and probabilistic belief semirings                      |
| `guide/matrix/benchmarks.md`          | `guide/matrix/benchmarks.md` (retained)                                             | Sparse matrix micro-benchmarks and CodSpeed scaling profiles                             |
| `guide/matrix/academic.md`            | `guide/matrix/academic.md` (retained)                                               | Academic exact reference implementations (Gram-Schmidt, adjugate)                        |
| `guide/semirings/verification.md`     | `guide/semirings/verification.md` (retained)                                        | Axiomatic law verification and property-based tests for semirings                        |
| *New*                                 | `guide/algebra/modules_and_vector_spaces.md`                                        | `Semimodule`, `Module`, `VectorSpace`, two-sorted action $R \times M \to M$              |
| *New*                                 | `guide/algebra/exact_matrix_solvers.md`                                             | Exact field operations: RREF, determinant, nullspace, matrix inversion                   |

---

### 3. The Hacker's Translation Box (Jargon Decoder)

To demystify abstract mathematical vocabulary, the landing guide (`guide/index.md`) will feature the following
translation key:

| Mathematical Term | What It Actually Means                                                              | Concrete Analogy                                                          | Computational Superpower                                                      |
|:------------------|:------------------------------------------------------------------------------------|:--------------------------------------------------------------------------|:------------------------------------------------------------------------------|
| **Magma**         | Any binary function taking two $T$'s and returning a $T$.                           | Mixing paints: `mix(red, blue) -> purple`.                                | Basic closure: combining elements without crashing.                           |
| **Semigroup**     | A Magma where grouping doesn't matter: $(a \circ b) \circ c = a \circ (b \circ c)$. | String concatenation: `("a"+"b")+"c" == "a"+("b"+"c")`.                   | **Parallel computing!** Splitting and reducing across CPU cores.              |
| **Monoid**        | A Semigroup with an "identity" (do-nothing element).                                | Adding $0$, multiplying by $1$, empty string `""`.                        | Safe reduction over empty lists without `if len == 0:` guards.                |
| **Semiring**      | You can Add and Multiply, but **cannot subtract**.                                  | Shortest paths: $\oplus$ is $\min$, $\otimes$ is $+$.                     | **Dynamic programming & graph solvers** (Bellman-Ford, PageRank).             |
| **Ring**          | You can Add, Multiply, and **Subtract** ($a - a = 0$).                              | Integers $\mathbb{Z}$, Polynomials $\mathbb{R}[x]$.                       | Cancellation! Terms balance out, enabling cryptography and error codes.       |
| **Field**         | You can Add, Subtract, Multiply, and **Divide** ($a \cdot a^{-1} = 1$).             | Rationals $\mathbb{Q}$, Reals $\mathbb{R}$, Finite fields $\mathbb{F}_p$. | **Exact Linear Algebra!** Gaussian elimination, LU, nullspaces without drift. |
| **Module**        | Vectors scaled by a Ring instead of a Field.                                        | Grids of integers or polynomials scaled by scalars.                       | Discrete differential forms, integer lattices, error-correcting codes.        |
| **Algebra**       | A vector space where vectors can also be **multiplied together**.                   | 3D rotations (quaternions), cross products, Lie brackets.                 | Physics simulations, rigid-body rotations, angular momentum, spacetime.       |

---

### 4. Fast-Track Elevators by Discipline (`guide/index.md`)

Direct entry cards for engineers and researchers seeking immediate solutions:

- 🚀 **The Graph & Network Engineer**: Jump straight to [Semirings & Optimization](guide/semirings/optimization.md) for
  shortest paths, all-pairs routing, and transitive closures.
- 🎯 **The Exact Math & Crypto Solver**: Jump straight
  to [Rings, Fields & Exact Solvers](guide/algebra/exact_matrix_solvers.md) for exact rational RREF, nullspaces, and
  Galois field arithmetic.
- 🛰️ **The Robotics, 3D & Physics Engineer**: Jump straight
  to [Clifford Geometric Algebra](guide/algebra/clifford_geometric_algebra.md)
  and [Lie Algebras](guide/algebra/lie_algebras.md) for rotor rotations and BCH dynamics.
- 🌐 **The Data & Shape Explorer**: Jump straight to [Simplicial Homology](guide/topology/homology.md)
  and [DEC](guide/topology/dec.md) for persistent barcodes, Hodge star operators, and discrete differential forms.

---

### 5. Standard Chapter Pedagogical Template (The Inverted 4-Beat Arc)

Every algebraic guide chapter adheres strictly to the **Feynman 4-Beat Arc**:

1. **Beat 1: The Hook & Practical Problem ("What Breaks Without This?")**:
   A tangible computing or mathematical dilemma illustrating why the structure is required (e.g., why pivot division in
   Gaussian elimination fails without a Field).
2. **Beat 2: The 30-Second Executable Snippet**:
   A self-contained, copy-pasteable 5-line Python snippet providing immediate runnable demonstration.
3. **Beat 3: The Protocol & Contract**:
    - The formal mathematical contract ($\LaTeX$ axioms).
    - The Python typing signature (`Protocol[V]` or `Protocol[R, M]`) in `algebrax.algebra`.
    - The canonical raw dictionary carrier model (zero boxing).
    - Demystification of domain `.mul()` semantics (Lie bracket, geometric product, cup product).
4. **Beat 4: Falsifiability, Law Verification & Counterexamples**:
    - Executable verification test with `verify_*_laws`.
    - A negative counterexample explicitly showing what axiom fails when an unsuitable structure is used (e.g.,
      attempting division on $\mathbb{Z}/4\mathbb{Z}$ zero divisors).
5. **Beat 5: Frontier Horizons & Cross-Domain Bridges**:
   2–3 forward-looking connections to higher geometry, physics, or algorithmic applications (e.g., connecting Clifford
   algebras to Spacetime Algebra and Conformal Geometric Algebra).

---

## Backwards Compatibility & Verification

1. **URL Redirects / Aliases**:
    - Historical guide paths (e.g., `guide/discrete/lie_algebras/`, `guide/semirings/algebraic/`) will maintain
      client-side redirect meta tags to prevent broken links.
2. **Strict CI Build & Snippet Testing**:
    - CI will execute `zensical build --strict` to verify all internal links and anchors.
    - CI will execute `pytest --markdown-docs docs/guide/` to guarantee that 100% of documentation code snippets remain
      syntax-valid and pass all assertions.
3. **Zero Code Impact**:
    - This EP modifies zero files in `src/algebrax/`.

---

## How to Teach This / Documentation Plan

- Landing page (`docs/index.md`) will feature a visual, interactive **Axiom Staircase** flowchart linking directly to
  each tier.
- Every docstring in `src/algebrax/algebra/` will cross-reference its corresponding user guide chapter.

---

## Reference Implementation

- Staged navigation matrix in `zensical.toml`.
- Reorganization into `docs/guide/algebra/`, `docs/guide/topology/`, and `docs/guide/interop/`.
- Validation via `zensical build --strict` and `pytest --markdown-docs`.

---

## Rejected Ideas

1. **Bourbaki Axiom-First Template**:
    - *Rejected*: Presenting LaTeX axioms before concrete motivation alienates students and software engineers. Replaced
      with the Inverted 4-Beat Arc.
2. **Dropping Legacy Pages (Tensors, Information, Benchmarks)**:
    - *Rejected*: Identified by Council Member Shannon as dead-weight regression. Fully reintegrated into Tiers 4, 6,
      and 7.
3. **Single Monolithic Cheat Sheet**:
    - *Rejected*: Violates Shannon ergonomics. Navigating a 5,000-line document hinders deep exploration.

---

## Open Questions

- [x] **Interactive Lab Synchrony**: How should `recipes/lab.py` be re-indexed? (**Resolved: Add view tabs mapped
  directly to Tiers 1–6**).
- [x] **Legacy URL Preservation**: How to handle legacy links? (**Resolved: Provide HTML `<meta http-equiv="refresh">`
  redirect stubs**).

---

## Change Log

* **2026-10-27:**
    * Initial Draft authored following Council consensus on EP-0192.
    * Council Review Amendments: Inverted 4-Beat Chapter Flow, Jargon Decoder, Domain Elevators, reintegration of
      tensor/probability/benchmark pages, counterexample falsifiability requirements, and `markdown-pytest` CI mandate.
