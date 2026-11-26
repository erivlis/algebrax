---
title: Enhancement Proposals
description: "Index of all Enhancement Proposals (EPs) for AlgebraX."
icon: lucide/scroll-text
---

# Enhancement Proposals

Enhancement Proposals (EPs) are the primary mechanism for proposing major features, collecting input,
and documenting design decisions. See [EP-0000](proposals/EP-0000-process.md) for the full process.

---

## Process

| EP                                      | Title                        |                  Status                   |
|:----------------------------------------|:-----------------------------|:-----------------------------------------:|
| [EP-0000](proposals/EP-0000-process.md) | Enhancement Proposal Process | :material-check-circle:{ .active } Active |

---

## Single-Digit Foundational Canon

| EP                                                                                            | Title                                                         | Module                  |          Status         |
|:----------------------------------------------------------------------------------------------|:--------------------------------------------------------------|:------------------------|:-----------------------:|
| [EP-0001](proposals/EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md) | Mathematical Manifesto, Core Invariants & Foundational Canon  | Foundations             | :material-check-circle:{ .active } Active |
| [EP-0002](proposals/EP-0002-mathematical-docstring-standards-and-algebraic-signatures.md)    | Mathematical Docstring Standards & Algebraic Signatures       | Standards               | :material-check-circle:{ .active } Active |
| [EP-0003](proposals/EP-0003-axiomatic-verification-and-property-based-testing.md)            | Axiomatic Verification, Falsification & Multi-Layered Testing | `algebrax.verification` | :material-check-circle:{ .active } Active |
| [EP-0004](proposals/EP-0004-unboxed-storage-and-sparse-carrier-invariance.md)                | Unboxed Storage & Sparse Carrier Invariance                   | Architecture            | :material-check-circle:{ .active } Active |
| [EP-0005](proposals/EP-0005-universal-algebraic-protocol-architecture.md)                    | Universal Algebraic Protocol Architecture                     | `algebrax.algebra`      | :material-check-circle:{ .active } Active |
| [EP-0006](proposals/EP-0006-algebraic-morphisms-and-structural-mappings.md)                  | Morphisms, Homomorphisms & Structural Mappings                | `algebrax.algebra`      | :material-check-circle:{ .active } Active |

---

## Phase 0 — Architecture

| EP                                                | Title                                                     |                  Status                   |
|:--------------------------------------------------|:----------------------------------------------------------|:-----------------------------------------:|
| [EP-0099](proposals/EP-0099-expansion-roadmap.md) | Master Expansion Roadmap & Unified Algebraic Architecture | :material-check-circle:{ .active } Active |

---

## Phase 1 — Foundational Engine Extensions

| EP                                                      | Title                                  | Module              |           Status           |
|:--------------------------------------------------------|:---------------------------------------|:--------------------|:--------------------------:|
| [EP-0100](proposals/EP-0100-quotient-monoid-algebra.md) | Quotient Monoid Algebra Semiring       | `algebrax.semiring` | :material-check-all: Final |
| [EP-0101](proposals/EP-0101-sparse-chain-complex.md)    | Sparse Chain Complex & Hodge-Laplacian | `algebrax.analysis` | :material-check-all: Final |

---

## Phase 2 — Specialized Domain Tracks

| EP                                                         | Title                                         | Module              |           Status           |
|:-----------------------------------------------------------|:----------------------------------------------|:--------------------|:--------------------------:|
| [EP-0110](proposals/EP-0110-simplicial-homology.md)        | Simplicial Homology & Betti Numbers           | `algebrax.homology` | :material-check-all: Final |
| [EP-0111](proposals/EP-0111-clifford-geometric-algebra.md) | Clifford Geometric Algebra & Rotors           | `algebrax.clifford` | :material-check-all: Final |
| [EP-0112](proposals/EP-0112-galois-finite-fields.md)       | Galois Finite Fields & Cryptographic Matrices | `algebrax.galois`   | :material-check-all: Final |
| [EP-0113](proposals/EP-0113-categorical-kleisli.md)        | Categorical Morphisms & Kleisli Composition   | `algebrax.category` | :material-check-all: Final |

---

## Phase 3 — Explorer, Maturity & Curiosity

| EP                                                             | Title                                              | Module                      |           Status           |
|:---------------------------------------------------------------|:---------------------------------------------------|:----------------------------|:--------------------------:|
| [EP-0120](proposals/EP-0120-algebraic-web-explorer.md)         | Algebraic Web Explorer & Interactive Visual Studio | Web / Visual                |  :material-pencil: Draft   |
| [EP-0130](proposals/EP-0130-api-consistency-audit.md)          | API Consistency & Public Export Audit              | `algebrax.__init__`         | :material-check-all: Final |
| [EP-0131](proposals/EP-0131-algebraic-law-verification.md)     | Algebraic Law Verification Engine                  | `algebrax.verification`     | :material-swap-horizontal: Superseded |
| [EP-0132](proposals/EP-0132-matrix-decompositions.md)          | Matrix Decompositions — LU, QR, SVD, Cholesky      | `algebrax.matrix.decompose` | :material-check-all: Final |
| [EP-0133](proposals/EP-0133-jupyter-cli-integration.md)        | Jupyter & CLI Integration                          | `algebrax.display`          | :material-check-all: Final |
| [EP-0134](proposals/EP-0134-semiring-namespace-refactoring.md) | Semiring Namespace Refactoring                     | `algebrax.semiring/`        | :material-check-all: Final |

---

## Phase 3.5 — Council Refinement Track

Proposals derived from the [Grand Council Assessment](proposals/EP-0099-expansion-roadmap.md) —
a comprehensive architectural audit by the 8 Pillars of the Council Framework.

| EP                                                                             | Title                                                                | Council Sponsor                                 |              Status               |
|:-------------------------------------------------------------------------------|:---------------------------------------------------------------------|:------------------------------------------------|:---------------------------------:|
| [EP-0140](proposals/EP-0140-api-symmetry-restoration.md)                       | API Symmetry Restoration                                             | ⚖️ Noether                                      |    :material-check-all: Final     |
| [EP-0141](proposals/EP-0141-taxonomy-cleanup.md)                               | Structural Taxonomy Cleanup                                          | 🧩 Russell                                      |    :material-check-all: Final     |
| [EP-0142](proposals/EP-0142-performance-optimizations.md)                      | Performance & Efficiency Optimizations                               | ⚡ Shannon                                      |    :material-check-all: Final     |
| [EP-0143](proposals/EP-0143-documentation-clarity.md)                          | Documentation Clarity & Freshman Test                                | 💡 Feynman                                      |    :material-check-all: Final     |
| [EP-0144](proposals/EP-0144-testing-hardening.md)                              | Testing & Falsifiability Hardening                                   | 🔬 Popper                                       |    :material-check-all: Final     |
| [EP-0145](proposals/EP-0145-type-safety-hardening.md)                          | Type Safety & Contract Hardening                                     | 🛡️ Golem                                        |    :material-check-all: Final     |
| [EP-0146](proposals/EP-0146-developer-ergonomics.md)                           | Developer Ergonomics & Ecosystem Bridges                             | 🤝 Steward                                      |    :material-check-all: Final     |
| [EP-0147](proposals/EP-0147-optional-loop-pragmas.md)                          | Optional Loop Pragmas & Concurrency                                  | ⚡ Shannon                                      | :material-clock-outline: Deferred |
| [EP-0148](proposals/EP-0148-formalized-benchmarking.md)                        | Formalized Micro-Benchmarking & CodSpeed                             | 🔬 Popper                                       |    :material-check-all: Final     |
| [EP-0149](proposals/EP-0149-binomial-convolution-moment-semiring.md)           | Universal & Multivariate Binomial Convolution Moments                | ⚖️ Noether                                      |    :material-check-all: Final     |
| [EP-0150](proposals/EP-0150-standardized-mathematical-docstrings.md)           | Standardized Mathematical Docstrings & Algebraic Registry            | 💡 Feynman                                      | :material-swap-horizontal: Superseded |
| [EP-0151](proposals/EP-0151-algebraic-pagerank-semirings.md)                   | Algebraic PageRank & Semiring Random Walks with Restart              | ⚡ Shannon                                      |    :material-check-all: Final     |
| [EP-0152](proposals/EP-0152-spectral-graph-theory-laplacian.md)                | Spectral Graph Theory, Algebraic Connectivity & Graph Laplacians     | ⚖️ Noether & ⚡ Shannon                         |    :material-check-all: Final     |
| [EP-0153](proposals/EP-0153-semiring-matrix-symmetry-and-vector-primitives.md) | Semiring Matrix Symmetry, Sparse Vector Primitives & Cochain Carrier | ⚖️ Noether, ⚡ Shannon, 🧩 Russell & 💡 Feynman |    :material-check-all: Final     |

---

## Phase 4 — Algebraic Continents & Next Frontiers

Proposals stemming from the **Next Frontiers Exploration**
([EXP-0001](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0001-algebraic-frontiers-and-missing-domains/README.md)),
expanding AlgebraX into discrete differential geometry, continuous symmetries, and higher topology.

| EP                                                                                 | Title                                                                     | Council Sponsor                                 |           Status           |
|:-----------------------------------------------------------------------------------|:--------------------------------------------------------------------------|:------------------------------------------------|:--------------------------:|
| [EP-0160](proposals/EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md) | Discrete Exterior Calculus & Helmholtz-Hodge Flow Decomposition           | ⚖️ Noether, ⚡ Shannon & 💡 Feynman             | :material-check-all: Final |
| [EP-0161](proposals/EP-0161-cellular-sheaves-and-network-laplacians.md)            | Cellular Sheaves, Sheaf Cohomology & Network Laplacians                   | 🧩 Russell, 🤝 Steward, ⚖️ Noether & ⚡ Shannon | :material-check-all: Final |
| [EP-0162](proposals/EP-0162-persistent-homology-and-topological-barcodes.md)       | Persistent Homology, Simplicial Filtrations & Topological Barcodes        | 🔬 Popper, 🧭 Explorer, ⚡ Shannon & 💡 Feynman | :material-check-all: Final |
| [EP-0163](proposals/EP-0163-lie-algebras-and-bch-dynamics.md)                      | Lie Algebras, Root Systems, and Baker–Campbell–Hausdorff Dynamics         | ⚖️ Noether, ⚡ Shannon & 🛡️ Golem               | :material-check-all: Final |
| [EP-0164](proposals/EP-0164-root-systems-and-chevalley-bases.md)                   | Root Systems, Weyl Groups & Chevalley-Serre Simple Lie Algebras           | ⚖️ Noether, ⚡ Shannon & 🧩 Russell             | :material-check-all: Final |
| [EP-0165](proposals/EP-0165-topology-namespace-and-cohomology-ring.md)             | Unified Topology Namespace, Cochain Ring Products & Persistent Cohomology | 🧩 Russell, ⚖️ Noether, ⚡ Shannon & 🤝 Steward | :material-check-all: Final |

---

## Phase 5 — Mathematical Verification & Correctness Evidence Track

Proposals stemming from the **Correctness Evidence Exploration**
([EXP-0003](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0003-correctness-evidence/README.md)),
establishing multi-layered verification, differential testing against canonical math libraries ("Stamp of Trust"),
metamorphic invariants, Schwartz–Zippel PIT, and certified solvers.

| EP                                                                                     | Title                                                                                                | Council Sponsor                                           |           Status           |
|:---------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------|:----------------------------------------------------------|:--------------------------:|
| [EP-0180](proposals/EP-0180-multi-layered-verification-suite.md)                       | Multi-Layered Verification Test Architecture                                                         | 🔬 Popper, ⚖️ Noether, ⚡ Shannon, 🛡️ Golem & 🧭 Explorer | :material-swap-horizontal: Superseded |
| [EP-0181](proposals/EP-0181-comparative-verification-linalg-tensors-transforms.md)     | Comparative Verification — Linear Algebra, Tensors & Signal Processing (`NumPy` & `SciPy` Oracles)   | 🔬 Popper, 🧩 Russell, ⚡ Shannon & 🛡️ Golem              | :material-check-all: Final |
| [EP-0182](proposals/EP-0182-comparative-verification-graphs-spectral-semirings.md)     | Comparative Verification — Graph Calculus, Spectral Theory & Path Semirings (`NetworkX` & `csgraph`) | 🔬 Popper, ⚖️ Noether, ⚡ Shannon & 🧩 Russell            | :material-check-all: Final |
| [EP-0183](proposals/EP-0183-comparative-verification-symbolic-lie-galois-group.md)     | Comparative Verification — Exact Symbolic Algebra, Lie, Galois, Clifford & Group (`SymPy` Oracle)    | ⚖️ Noether, 🔬 Popper, 🧩 Russell & 🛡️ Golem              | :material-check-all: Final |
| [EP-0184](proposals/EP-0184-comparative-verification-topology-probability-automata.md) | Comparative Verification — Topology, Information Theory & Formal Languages (`SciPy.stats` & TDA)     | 🔬 Popper, ⚖️ Noether, 💡 Feynman & 🧭 Explorer           | :material-check-all: Final |
| [EP-0185](proposals/EP-0185-axiomatic-statistical-sheaf-mms-verification.md)           | Axiomatic Property, Streaming Moment & Manufactured Solution Verification (Semirings & Sheaves)      | 🔬 Popper, ⚖️ Noether, 🧩 Russell & ⚡ Shannon            | :material-check-all: Final |
| [EP-0186](proposals/EP-0186-certificates-pit-and-smt-formal-verification.md)           | Proof-Carrying Solver Certificates, Schwartz–Zippel PIT & SMT Formal Verification (`Z3` Oracle)      | 🛡️ Golem, ⚡ Shannon, 🔬 Popper & 🧭 Explorer             | :material-check-all: Final |

---

## Phase 6 — Pure Algebraic Hierarchy

Proposals stemming from the **Pure Algebraic Hierarchy Exploration**
([EXP-0004](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0004-pure-algebraic-hierarchy/README.md)),
establishing Lean 4 Mathlib-aligned granular structural protocols, sub-semiring abstractions (magmas, monoids, groups,
lattices), super-semiring rings & fields, and exact polymorphic matrix solvers.

| EP                                                                                 | Title                                                                         | Council Sponsor         |           Status           |
|:-----------------------------------------------------------------------------------|:------------------------------------------------------------------------------|:------------------------|:--------------------------:|
| [EP-0190](proposals/EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md) | Granular Algebraic Hierarchy — Magmas, Monoids, Groups & Lattices             | 🧩 Russell & 🔬 Popper  | :material-check-all: Final |
| [EP-0191](proposals/EP-0191-rings-fields-modules-and-exact-solvers.md)             | Rings, Fields, Modules & Exact Matrix Solvers                                 | ⚖️ Noether & ⚡ Shannon | :material-check-all: Final |
| [EP-0192](proposals/EP-0192-unifying-domain-objects-with-algebraic-hierarchy.md)   | Unifying Domain Objects with the Pure Algebraic Hierarchy                     | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |
| [EP-0193](proposals/EP-0193-documentation-architecture-realignment.md)             | Documentation Architecture Realignment with Pure Algebraic Hierarchy          | 💡 Feynman & 🧩 Russell | :material-check-all: Final |
| [EP-0194](proposals/EP-0194-atomic-algebraic-mixins-and-protocol-composition.md)   | Atomic Algebraic Mixins & Diamond-Free Protocol Composition                   | 🧩 Russell & ⚖️ Noether | :material-swap-horizontal: Superseded |
| [EP-0195](proposals/EP-0195-canonical-core-consolidation.md)                       | Canonical Core Consolidation & Deprecation Purge                              | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |
| [EP-0196](proposals/EP-0196-peripheral-ecosystem-realignment.md)                   | Peripheral Ecosystem Realignment (Benchmarks, Recipes, GUI Lab & User Guides) | 🎨 Feynman & ⏱️ Shannon  | :material-check-all: Final |
| [EP-0197](proposals/EP-0197-decoupled-semiring-foundations-star-semirings-and-kleene-algebras.md) | Decoupled Semiring Foundations — Pure Rigs, Star Semirings & Kleene Algebras | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |
| [EP-0198](proposals/EP-0198-generalized-closure-operators-kleene-plus-matrix-star-and-action-algebras.md) | Generalized Closure Operators — Kleene Plus, Matrix Star & Action Algebras | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |

---

## Phase 7 — Categorical Foundations & Morphisms

Proposals stemming from the **Categorical Foundations Exploration**
([EXP-0005](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md)),
establishing Lean 4 Mathlib-aligned category protocols, enriched matrix categories, Lawvere metric spaces, algebraic
homomorphisms, ideals, canonical quotients, and functorial cellular sheaves.

| EP                                                                                        | Title                                                           | Council Sponsor         |         Status          |
|:------------------------------------------------------------------------------------------|:----------------------------------------------------------------|:------------------------|:-----------------------:|
| [EP-0200](proposals/EP-0200-categorical-abstractions-and-enriched-matrices.md)            | Categorical Abstractions & Enriched Matrix Mechanics            | 🧩 Russell & ⚡ Shannon | :material-check-all: Final |
| [EP-0201](proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md)                  | Algebraic Homomorphisms, Ideals & Canonical Quotients           | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |
| [EP-0202](proposals/EP-0202-functorial-sheaves-and-categorical-dec.md)                    | Functorial Sheaves & Categorical DEC                            | ⚖️ Noether & 🔬 Popper  | :material-check-all: Final |
| [EP-0203](proposals/EP-0203-discrete-fiber-bundles-and-gauge-connections.md)              | Discrete Fiber Bundles & Gauge Connections                      | ⚖️ Noether & ⚡ Shannon | :material-check-all: Final |
| [EP-0204](proposals/EP-0204-non-associative-quantum-algebras-jordan-octonions-poisson.md) | Non-Associative & Quantum Algebras (Jordan, Octonions, Poisson) | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |
| [EP-0205](proposals/EP-0205-normed-banach-hilbert-spaces-and-rkhs.md)                     | Normed, Banach & Hilbert Spaces (Inner Products, RKHS)          | ⚡ Shannon & 🔬 Popper  | :material-check-all: Final |
| [EP-0206](proposals/EP-0206-coalgebras-bialgebras-and-hopf-algebras.md)                   | Coalgebras, Bialgebras & Hopf Algebras                          | ⚖️ Noether & ⚡ Shannon | :material-check-all: Final |
| [EP-0207](proposals/EP-0207-topological-k-theory-and-characteristic-classes.md)           | Topological K-Theory & Characteristic Classes                   | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |
| [EP-0208](proposals/EP-0208-categorical-type-theory-and-homotopy-groupoids.md)            | Categorical Type Theory & Homotopy Groupoids                    | 🧩 Russell & 🛡️ Golem   | :material-check-all: Final |
| [EP-0209](proposals/EP-0209-langlands-root-duality-hecke-padic-valuations.md)             | Langlands Root Duality, Hecke & p-Adic Valuations               | ⚖️ Noether & 🔬 Popper  | :material-check-all: Final |

---

## Phase 8 — Representation Theory, Invariant Theory & Quantum Groups

Proposals stemming from the **Representation Theory Exploration**
([EXP-0006](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0006-representation-theory-and-quantum-symmetries/README.md)),
establishing group representations, character tables, Schur orthogonality, Lie highest weights, Clebsch–Gordan tensors,
quiver representations, and quantum groups.

| EP                                                                                  | Title                                                 | Council Sponsor         |         Status          |
|:------------------------------------------------------------------------------------|:------------------------------------------------------|:------------------------|:-----------------------:|
| [EP-0210](proposals/EP-0210-group-representations-character-tables-schurs-lemma.md) | Group Representations, Character Tables & Schur       | ⚖️ Noether & 🧩 Russell | :material-check-all: Final |
| [EP-0211](proposals/EP-0211-lie-algebra-representations-clebsch-gordan.md)          | Lie Algebra Representations & Clebsch–Gordan Tensors  | ⚖️ Noether & ⚡ Shannon | :material-check-all: Final |
| [EP-0212](proposals/EP-0212-quiver-representations-and-gabriels-ade-theorem.md)     | Quiver Representations & Gabriel's ADE Theorem        | 🧩 Russell & 🔬 Popper  | :material-check-all: Final |
| [EP-0213](proposals/EP-0213-induced-representations-and-frobenius-reciprocity.md)   | Induced Representations & Frobenius Reciprocity       | 🧩 Russell & ⚖️ Noether | :material-check-all: Final |
| [EP-0214](proposals/EP-0214-invariant-theory-molien-series-casimir-polynomials.md)  | Invariant Theory, Molien Series & Casimir Polynomials | ⚖️ Noether & ⚡ Shannon | :material-check-all: Final |
| [EP-0215](proposals/EP-0215-quantum-groups-yang-baxter-braided-categories.md)       | Quantum Groups, Yang–Baxter Equation & R-Matrices     | ⚖️ Noether & 🛡️ Golem   | :material-check-all: Final |

---

## Phase 8.5 — Second Grand Council Refinement & Hardening Track

Proposals stemming from the **Second Grand Council Codebase Audit** across all 111 modules (36.6k LOC),
consolidating Phases 4–8 and early Phase 9 by hardening algebraic soundness, sparse linear algebra kernels,
universal semiring propagation, falsifiable verification, and codebase ergonomics/hygiene before completing Phase 9
(`EP-0222`) and launching Phases 10–11.

| EP                                                                                                | Title                                                                                   | Council Sponsor                        |         Status          |
|:--------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------|:---------------------------------------|:-----------------------:|
| [EP-0250](proposals/EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md)          | Protocol Integrity, Law Witnesses & Algebraic Soundness                                 | ⚖️ Noether & 🧩 Russell                | :material-check: Accepted |
| [EP-0251](proposals/EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md)         | Sparse Linear Algebra Kernel, Decomposition Correctness & Hot-Path Performance          | ⚡ Shannon & 🛡️ Golem                  | :material-check: Accepted |
| [EP-0252](proposals/EP-0252-universal-semiring-propagation-and-domain-unification.md)             | Universal Semiring Propagation, Parameterized Tries & Domain Unification                | 🧭 Explorer & ⚖️ Noether               | :material-check: Accepted |
| [EP-0253](proposals/EP-0253-verification-engine-hardening-and-grounded-proofs.md)                 | Verification Engine Hardening, Falsifiability & Grounded Formal Proofs                  | 🔬 Popper & 🧪 Bacon                   | :material-check: Accepted |
| [EP-0254](proposals/EP-0254-ergonomics-state-safety-ecosystem-bridges-and-hygiene.md)             | Ergonomics, State Safety, Ecosystem Bridges & Codebase Hygiene                          | 💡 Feynman, 🌿 Steward & 🛡️ Golem      | :material-check: Accepted |

---

## Phase 9 — Commutative Algebra, Algebraic Varieties & Tropical Geometry

Proposals stemming from the **Algebraic & Tropical Varieties Exploration**
([EXP-0009](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0009-algebraic-and-tropical-varieties/README.md)),
establishing unboxed multivariate polynomial algebras, exact Gröbner basis ideals (Buchberger & $F_4$ sparse Macaulay RREF),
affine algebraic varieties, coordinate rings, Stickelberger companion matrix solvers, and tropical polyhedral varieties.

| EP                                                                                      | Title                                                               | Council Sponsor                          |         Status          |
|:----------------------------------------------------------------------------------------|:--------------------------------------------------------------------|:-----------------------------------------|:-----------------------:|
| [EP-0220](proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md)     | Multivariate Polynomial Algebra & Exact Gröbner Ideals              | ⚡ Shannon, 🔬 Popper & ⚖️ Noether       | :material-check-all: Final |
| [EP-0221](proposals/EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md)    | Affine Algebraic Varieties, Coordinate Rings & Stickelberger Solvers | ⚖️ Noether, 🧩 Russell & ⚡ Shannon      | :material-check-all: Final |
| [EP-0222](proposals/EP-0222-tropical-varieties-and-polyhedral-duals.md)                 | Tropical Varieties, Newton Polytopes & Balanced Polyhedral Complexes | 🧭 Explorer, ⚖️ Noether & ⚡ Shannon     | :material-pencil: Draft |

---

## Phase 10 — Generalized Harmonic Analysis & Spectral Signal Theory

Proposals stemming from the **Generalized Harmonic Analysis Exploration**
([EXP-0010](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/README.md)),
generalizing `algebrax.transforms` into non-Abelian Peter–Weyl matrix Fourier transforms, Püschel–Moura polynomial shift models, exact finite-field NTTs, Rota poset Möbius transforms, and matrix-free Chebyshev spectral wavelets.

| EP                                                                                      | Title                                                                              | Council Sponsor                        |         Status          |
|:----------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------|:---------------------------------------|:-----------------------:|
| [EP-0230](proposals/EP-0230-non-abelian-group-fourier-transforms-and-peter-weyl.md)     | Non-Abelian Group Fourier Transforms, Peter–Weyl Duality & Equivariant Convolutions | ⚖️ Noether, 🔬 Popper & ⚡ Shannon      | :material-pencil: Draft |
| [EP-0231](proposals/EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md)   | Algebraic Signal Processing, Exact Finite-Field NTT & Poset Möbius Transforms      | 🧩 Russell, 🔬 Popper & ⚡ Shannon      | :material-pencil: Draft |
| [EP-0232](proposals/EP-0232-geometric-hodge-and-sheaf-spectral-wavelets.md)             | Geometric, Simplicial Hodge & Cellular Sheaf Spectral Wavelets                     | ⚡ Shannon, ⚖️ Noether & 🔬 Popper     | :material-pencil: Draft |

---

## Phase 11 — Algebraic Analysis, Differential Rings & Ore Algebras

Proposals stemming from the **Differential & Ore Algebras Exploration**
([EXP-0011](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/README.md)),
establishing skew-derivation mixins, unboxed non-commutative Weyl algebras $A_n(k)$, left Gröbner $D$-modules,
characteristic varieties, Kähler differentials $\Omega^1_{k[V]/k}$, unified Ore skew-polynomial rings
$R[\partial; \sigma, \delta]$, Frobenius indicial equations, exact rational Hermite reduction, Gosper summation,
creative telescoping, multivariate Taylor Jet solvers, and bounded-order Picard–Vessiot Differential Galois Theory.

| EP                                                                                                | Title                                                                                                    | Council Sponsor                      |         Status          |
|:--------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------|:-------------------------------------|:-----------------------:|
| [EP-0240](proposals/EP-0240-differential-rings-weyl-algebras-and-kahler-differentials.md)         | Differential Rings, Weyl Algebras, Characteristic Varieties & Kähler Differentials                         | ⚖️ Noether, ⚡ Shannon & 🛡️ Golem    | :material-pencil: Draft |
| [EP-0241](proposals/EP-0241-ore-skew-polynomial-algebras-dfinite-closure-and-frobenius.md)        | Unified Ore Skew-Polynomial Algebras, D-Finite Closure & Frobenius Solvers                               | ⚖️ Noether, ⚡ Shannon & 🔬 Popper   | :material-pencil: Draft |
| [EP-0242](proposals/EP-0242-hermite-gosper-reduction-creative-telescoping-and-taylor-jets.md)     | Exact Symbolic Integration, Hermite & Gosper Reduction, Creative Telescoping & Multivariate Taylor Jets  | ⚡ Shannon, 🔬 Popper & 🛡️ Golem     | :material-pencil: Draft |
| [EP-0243](proposals/EP-0243-picard-vessiot-differential-galois-and-kovacic.md)                    | Picard–Vessiot Differential Galois Theory, Symmetric Powers & Kovacic Factorization                      | ⚖️ Noether, 🔬 Popper & 🛡️ Golem     | :material-pencil: Draft |



