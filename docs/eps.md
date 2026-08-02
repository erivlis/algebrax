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
| [EP-0131](proposals/EP-0131-algebraic-law-verification.md)     | Algebraic Law Verification Engine                  | `algebrax.verification`     | :material-check-all: Final |
| [EP-0132](proposals/EP-0132-matrix-decompositions.md)          | Matrix Decompositions — LU, QR, SVD, Cholesky      | `algebrax.matrix.decompose` | :material-check-all: Final |
| [EP-0133](proposals/EP-0133-jupyter-cli-integration.md)        | Jupyter & CLI Integration                          | `algebrax.display`          |  :material-pencil: Draft   |
| [EP-0134](proposals/EP-0134-semiring-namespace-refactoring.md) | Semiring Namespace Refactoring                     | `algebrax.semiring/`        | :material-check-all: Final |

---

## Phase 3.5 — Council Refinement Track

Proposals derived from the [Grand Council Assessment](proposals/EP-0099-expansion-roadmap.md) —
a comprehensive architectural audit by the 8 Pillars of the Council Framework.

| EP                                                        | Title                                    | Council Sponsor |           Status           |
|:----------------------------------------------------------|:-----------------------------------------|:----------------|:--------------------------:|
| [EP-0140](proposals/EP-0140-api-symmetry-restoration.md)  | API Symmetry Restoration                 | ⚖️ Noether      | :material-check-all: Final |
| [EP-0141](proposals/EP-0141-taxonomy-cleanup.md)          | Structural Taxonomy Cleanup              | 🧩 Russell      |  :material-pencil: Draft   |
| [EP-0142](proposals/EP-0142-performance-optimizations.md) | Performance & Efficiency Optimizations   | ⚡ Shannon      |  :material-pencil: Draft   |
| [EP-0143](proposals/EP-0143-documentation-clarity.md)     | Documentation Clarity & Freshman Test    | 💡 Feynman      |  :material-pencil: Draft   |
| [EP-0144](proposals/EP-0144-testing-hardening.md)         | Testing & Falsifiability Hardening       | 🔬 Popper       |  :material-pencil: Draft   |
| [EP-0145](proposals/EP-0145-type-safety-hardening.md)     | Type Safety & Contract Hardening         | 🛡️ Golem        |  :material-pencil: Draft   |
| [EP-0146](proposals/EP-0146-developer-ergonomics.md)      | Developer Ergonomics & Ecosystem Bridges | 🤝 Steward      |  :material-pencil: Draft   |
