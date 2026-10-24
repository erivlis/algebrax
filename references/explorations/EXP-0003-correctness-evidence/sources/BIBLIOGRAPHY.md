# EXP-0003: Scientific Bibliography & Source Repository

This document serves as the permanent bibliographic record and source repository index for **EXP-0003 (Correctness
Evidence & Verification Methodologies)**. All papers, technical reports, and monographs cited herein are archived
locally in `references/explorations/EXP-0003-correctness-evidence/sources/papers/`.

---

## Index of Primary Source Papers

| Identifier          | Title                                                                     | Authors & Year                                    | Venue / Identifier                                                              | Local File / Archive                                                                                                                                                                                                                                                       | Methodology Mapping                                           |
|:--------------------|:--------------------------------------------------------------------------|:--------------------------------------------------|:--------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------|
| **[CHEN-1998]**     | *Metamorphic Testing: A New Approach for Generating Next Test Cases*      | T. Y. Chen, S. C. Cheung, S. M. Yiu (1998 / 2020) | arXiv:2002.12543 [cs.SE]                                                        | [`papers/chen_1998_metamorphic_testing.pdf`](./papers/chen_1998_metamorphic_testing.pdf)<br>[`papers/chen_1998_metamorphic_testing.md`](./papers/chen_1998_metamorphic_testing.md)                                                                                         | **Methodology 2:** Metamorphic Invariants & Dualities         |
| **[MACIVER-2019]**  | *Hypothesis: A new approach to property-based testing*                    | David R. MacIver, Zac Hatfield-Dodds (2019)       | *Journal of Open Source Software (JOSS)*, 4(43): 1891, DOI: 10.21105/joss.01891 | [`papers/maciver_2019_hypothesis.pdf`](./papers/maciver_2019_hypothesis.pdf)<br>[`papers/maciver_2019_hypothesis.md`](./papers/maciver_2019_hypothesis.md)                                                                                                                 | **Methodology 3:** Property-Based Axiomatic Invariant Testing |
| **[MATHLIB-2019]**  | *The Lean mathematical library*                                           | The mathlib Community (2019 / 2020)               | CPP 2020 / arXiv:1910.09336 [cs.LO]                                             | [`papers/mathlib_2019_lean_mathematical_library.pdf`](./papers/mathlib_2019_lean_mathematical_library.pdf)<br>[`papers/mathlib_2019_lean_mathematical_library.md`](./papers/mathlib_2019_lean_mathematical_library.md)                                                     | **Methodology 8:** Lean 4 Dual-Specification Verification     |
| **[SAXENA-2014]**   | *Progress on Polynomial Identity Testing – II*                            | Nitin Saxena (2014)                               | Perspectives in Computational Complexity, arXiv:1401.0976 [cs.CC]               | [`papers/saxena_2014_progress_on_polynomial_identity_testing.pdf`](./papers/saxena_2014_progress_on_polynomial_identity_testing.pdf)<br>[`papers/saxena_2014_progress_on_polynomial_identity_testing.md`](./papers/saxena_2014_progress_on_polynomial_identity_testing.md) | **Methodology 4:** Schwartz–Zippel Randomized PIT             |
| **[SALARI-2000]**   | *Code Verification by the Method of Manufactured Solutions*               | Kambiz Salari, Patrick Knupp (2000)               | Sandia National Laboratories Report SAND2000-1444, DOI: 10.2172/759450          | [`papers/salari_knupp_2000_method_manufactured_solutions.md`](./papers/salari_knupp_2000_method_manufactured_solutions.md)                                                                                                                                                 | **Methodology 5:** Method of Manufactured Solutions (MMS)     |
| **[MCKEEMAN-1998]** | *Differential Testing for Software*                                       | William M. McKeeman (1998)                        | *Digital Technical Journal*, 10(1): 100–107                                     | [`papers/mckeeman_1998_differential_testing.md`](./papers/mckeeman_1998_differential_testing.md)                                                                                                                                                                           | **Methodology 1:** Cross-Library Differential Testing         |
| **[SCHWARTZ-1980]** | *Fast Probabilistic Algorithms for Verification of Polynomial Identities* | Jacob T. Schwartz (1980)                          | *Journal of the ACM*, 27(4): 701–717, DOI: 10.1145/322217.322225                | Cited & analyzed in [`papers/saxena_2014_progress_on_polynomial_identity_testing.md`](./papers/saxena_2014_progress_on_polynomial_identity_testing.md)                                                                                                                     | **Methodology 4:** Schwartz–Zippel Lemma Formulation          |

---

## Detailed Paper Annotations & Technical Syntheses

### 1. [CHEN-1998] Metamorphic Testing: A New Approach for Generating Next Test Cases

* **Authors:** T. Y. Chen, S. C. Cheung, S. M. Yiu
* **Original Publication:** Technical Report HKUST-CS98-01, Hong Kong University of Science and Technology (1998);
  formally archived on arXiv: [arXiv:2002.12543](https://arxiv.org/abs/2002.12543).
* **Direct PDF URL:** [https://arxiv.org/pdf/2002.12543.pdf](https://arxiv.org/pdf/2002.12543.pdf)
* **Local Mirror:** `papers/chen_1998_metamorphic_testing.pdf` (581 KB)
* **Significance for AlgebraX:**
  The foundational paper that introduced Metamorphic Testing (MT) to solve the **Test Oracle Problem**. Chen et al.
  recognized that even when the expected numerical or symbolic output $f (x)$ cannot be verified by a reference oracle,
  testing can evaluate whether multiple executions satisfy essential mathematical relations (Metamorphic Relations,
  MRs).
* **Applied Invariants in AlgebraX:**
    - Commutative matrix dot transpose: $(A \otimes B)^T = B^T \otimes A^T$.
    - Linear scaling homogeneity: $\alpha \otimes (A \otimes B) = (\alpha \otimes A) \otimes B$.
    - Discrete Fourier Transform
      shift: $\mathcal{F} (\operatorname{shift}_k (x)) = \mathcal{F} (x) \odot e^{-i 2\pi k \mathbf{n}/N}$.
    - Boundary operator nilpotency: $\partial_k \circ \partial_{k+1} = \mathbf{0}$.

---

### 2. [MACIVER-2019] Hypothesis: A new approach to property-based testing

* **Authors:** David R. MacIver, Zac Hatfield-Dodds
* **Publication:** *Journal of Open Source Software (JOSS)*, 4 (43), 1891 (2019).
* **DOI:** [10.21105/joss.01891](https://doi.org/10.21105/joss.01891)
* **Direct PDF
  URL:** [https://joss.theoj.org/papers/10.21105/joss.01891.pdf](https://joss.theoj.org/papers/10.21105/joss.01891.pdf)
* **Local Mirror:** `papers/maciver_2019_hypothesis.pdf` (128 KB)
* **Significance for AlgebraX:**
  Documents the architecture of Python's premier property-based testing engine. Unlike Haskell's QuickCheck (which
  couples shrinking directly to generator types), Hypothesis introduces **generator-driven shrinking** over a flat
  byte-stream intermediate representation. This allows complex algebraic generators (e.g., sparse matrices, finite field
  elements, simplicial complexes) to shrink automatically to minimal counterexamples upon axiom failure.
* **Applied Axioms in AlgebraX:**
    - Semiring associativity, commutativity, left/right distributivity, additive/multiplicative identity, and zero
      annihilation across all 35+ semirings.
    - Lie algebra Jacobi identity and antisymmetry.
    - Lattice absorption and idempotency.

---

### 3. [MATHLIB-2019] The Lean mathematical library

* **Authors:** The mathlib Community
* **Publication:** *Proceedings of the 9th ACM SIGPLAN International Conference on Certified Programs and Proofs (CPP
  2020)*, pp. 367–381.
* **arXiv:** [arXiv:1910.09336](https://arxiv.org/abs/1910.09336)
* **Direct PDF URL:** [https://arxiv.org/pdf/1910.09336.pdf](https://arxiv.org/pdf/1910.09336.pdf)
* **Local Mirror:** `papers/mathlib_2019_lean_mathematical_library.pdf` (913 KB)
* **Significance for AlgebraX:**
  Details the unified architecture of Mathlib, the mathematical foundation of the Lean interactive theorem prover.
  Demonstrates how abstract algebraic hierarchies (Semigroup $\to$ Monoid $\to$ CommMonoid $\to$ Semiring $\to$
  CommSemiring $\to$ Ring) are encoded as typeclasses in Dependent Type Theory.
* **Applied Formal Models in AlgebraX:**
    - Establishes the formal Lean 4 specification model (`algebrax_lean`) defining matrix multiplication over arbitrary
      abstract semirings.
    - Provides machine-checked proofs that semiring matrix multiplication is associative without assuming underlying
      numerical field properties.

---

### 4. [SAXENA-2014] Progress on Polynomial Identity Testing – II

* **Author:** Nitin Saxena
* **Publication:** *Perspectives in Computational Complexity: The Somenath Biswas Anniversary Volume*, pp. 131–146
  (2014).
* **arXiv:** [arXiv:1401.0976](https://arxiv.org/abs/1401.0976)
* **Direct PDF URL:** [https://arxiv.org/pdf/1401.0976.pdf](https://arxiv.org/pdf/1401.0976.pdf)
* **Local Mirror:** `papers/saxena_2014_progress_on_polynomial_identity_testing.pdf` (241 KB)
* **Significance for AlgebraX:**
  A comprehensive survey on the state-of-the-art in Polynomial Identity Testing (PIT). Surveys the foundational
  **Schwartz–Zippel Lemma** (Schwartz 1980, Zippel 1979) and its modern derandomization techniques (hitting-set
  generators, Jacobian criteria, and circuit complexity lower bounds).
* **Applied Algorithm in AlgebraX:**
    - Evaluates symbolic equivalence $P (x_1, \dots, x_n) \equiv 0$ by treating expressions as unexpanded evaluation
      pipelines and evaluating them at random points sampled uniformly from $S = [1, 10^6]$ over $k = 3$ trials.
    - Binds false-positive error to $\le (d/|S|)^k \le 10^{-15}$, eliminating the combinatorial monomial explosion
      ($\binom{n+d}{d}$) that stalls traditional Computer Algebra Systems.

---

### 5. [SALARI-2000] Code Verification by the Method of Manufactured Solutions

* **Authors:** Kambiz Salari, Patrick Knupp
* **Publication:** Sandia National Laboratories Technical Report SAND2000-1444 (June 2000).
* **DOI / OSTI:** [10.2172/759450](https://doi.org/10.2172/759450) / OSTI ID: 759450
* **Direct Document Record:** [https://www.osti.gov/biblio/759450](https://www.osti.gov/biblio/759450)
* **Archival Record:** UNT Digital Library (Item metadc715560)
* **Local Digest:** `papers/salari_knupp_2000_method_manufactured_solutions.md`
* **Significance for AlgebraX:**
  Standardizes the **Method of Manufactured Solutions (MMS)** for code verification (formalized under ASME V&V 20).
  Distinguishes code verification (*"solving the equations right"*) from solution verification (*numerical error
  estimation*) and validation (*"solving the right equations"*).
* **Applied Verification in AlgebraX:**
    - Verifies Discrete Exterior Calculus (`EP-0160`), Hodge Laplacians (`EP-0152`), and Cellular Sheaf Laplacians
      (`EP-0161`) by manufacturing continuous analytical harmonic potentials $\phi (x, y) = \sin (2\pi x)\cos (2\pi y)$,
      projecting them onto simplicial triangulation hierarchies, and asserting that the discrete $L_2$ error norm decays
      at the theoretical second-order asymptotic rate ($O (h^2)$).

---

### 6. [MCKEEMAN-1998] Differential Testing for Software

* **Author:** William M. McKeeman
* **Publication:** *Digital Technical Journal*, Vol. 10, No. 1, 1998, pp. 100–107.
* **Semantic Scholar
  ID:** [Corpus ID 14018070](https://www.semanticscholar.org/paper/Differential-Testing-for-Software-McKeeman/fc881e8d0432ea8e4dd5fda4979243cac5e4b9e3)
* **Direct Mirror:** [Wang Zhijie DTJ Archive](https://wangzhijie.me/papers/1998/dtj/vol10num1art9.pdf)
* **Local Digest:** `papers/mckeeman_1998_differential_testing.md`
* **Significance for AlgebraX:**
  The landmark paper introducing **Differential Testing**. Addresses the test oracle problem by running randomly
  generated test inputs across two or more independent implementations of the same specification (e.g., DEC C vs GNU C)
  and flagging behavioral or numeric discrepancies.
* **Applied Verification in AlgebraX:**
    - Compares AlgebraX sparse dictionary linear algebra, FFT transforms, and graph metrics directly against canonical
      reference libraries: **NumPy**, **SciPy Sparse**, **NetworkX**, and **GUDHI**.
