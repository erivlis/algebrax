---
title: "EP-0184: Comparative Verification — Topology, Information Theory & Formal Languages (SciPy.stats & Reference TDA Oracles)"
description: "Establishes comparative verification tests validating AlgebraX simplicial homology, discrete exterior calculus, information-theoretic probability divergences, fractal metrics, and finite-state automata against SciPy.stats, exact Smith/rank oracles, and canonical topological manifolds."
icon: lucide/shapes
status: draft
---

# EP-0184: Comparative Verification — Topology, Information Theory & Formal Languages (
`SciPy.stats` & Reference TDA Oracles)

| Field             | Value                                                                                                              |
|:------------------|:-------------------------------------------------------------------------------------------------------------------|
| **EP**            | 0184                                                                                                               |
| **Title**         | Comparative Verification — Topology, Information Theory & Formal Languages (`SciPy.stats` & Reference TDA Oracles) |
| **Author**        | Eran Rivlis & Antigravity (Council Agent)                                                                          |
| **Sponsor**       | The Council                                                                                                        |
| **Delegate**      | 🔬 Karl Popper (Falsifiability), ⚖️ Emmy Noether (Symmetry), 💡 Richard Feynman (Clarity) & 🧭 The Explorer        |
| **Status**        | Draft                                                                                                              |
| **Type**          | Standards Track                                                                                                    |
| **Created**       | 2026-10-24                                                                                                         |
| **Updated**       | 2026-10-24                                                                                                         |
| **Replaces**      | None                                                                                                               |
| **Superseded-By** | None                                                                                                               |

---

## Abstract

This proposal specifies **Wave 1D** of the Phase 5 Mathematical Verification Track
([EP-0180](EP-0180-multi-layered-verification-suite.md)): a **Comparative Verification Suite** covering
`algebrax.homology`, `algebrax.probability`, `algebrax.automata`, and `algebrax.metrics`. It pits information-theoretic
measures (`entropy`, `kl_divergence`, `js_divergence`, `mutual_information`, `bayes_update`) against **`scipy.stats`**
and **`scipy.special`**, validates simplicial homology Betti numbers and Hodge Laplacians against exact rank-nullity
oracles (`numpy.linalg.matrix_rank` / `sympy.Matrix.rank`) and canonical triangulated manifolds ($S^1, S^2, T^2$),
verifies discrete Stokes' theorem $\langle d\omega, c \rangle = \langle \omega, \partial c \rangle$, and validates
DFA/NFA formal language acceptance (`algebrax.automata`) against reference state-subset constructions.

---

## Motivation

1. **Topological Invariant Ground Truth (`algebrax.homology`):** Simplicial complexes, Betti numbers
   ($\beta_0, \beta_1, \beta_2$), Hodge Laplacians
   ($\Delta_k = \partial_{k+1}\partial_{k+1}^T + \partial_k^T \partial_k$), and discrete exterior calculus operators
   must agree with exact linear algebraic rank calculations
   ($\beta_k = \dim C_k - \operatorname{rank} (\partial_k) - \operatorname{rank} (\partial_{k+1})$) and must satisfy the
   **Euler–Poincaré Theorem** ($\chi = \sum (-1)^k |K_k| = \sum (-1)^k \beta_k$) as well as **Discrete Stokes' Theorem**
   ($\langle d\omega, c \rangle = \langle \omega, \partial c \rangle$).
2. **Information Theory Parity (`algebrax.probability`):** Probability distributions, Shannon entropy, Kullback–Leibler
   divergence, Jensen–Shannon divergence, and Bayesian updates are foundational to statistical machine learning.
   Comparing `algebrax.probability` directly against `scipy.stats.entropy` and `scipy.spatial.distance.jensenshannon`
   guarantees numerical accuracy across skewed, uniform, and sparse support distributions.
3. **Formal Language Equivalence (`algebrax.automata`):** `simulate_dfa` and `simulate_nfa` implement weighted and
   unweighted state-machine transitions via semiring matrix-vector products. Comparing NFA execution against
   deterministic Rabin–Scott powerset construction and Python's `re` engine on regular languages proves formal language
   correctness.
4. **Sparsity & Fractal Dimension Metrics (`algebrax.metrics`):** `box_counting_dimension` and sparsity estimators must
   converge to analytical Hausdorff dimensions on self-similar fractals ($\ln 2 / \ln 3$ for the Cantor
   set, $\ln 3 / \ln 2$ for the Sierpiński gasket).

---

## Rationale

- **🔬 Falsifiability (Popper):** Tests randomized probability simplex vectors via Hypothesis
  (`st.lists(st.floats(0, 1))` normalized to sum to 1) against `scipy.stats.entropy`, probing near-zero
  probabilities $p_i \to 0^+$ where $0 \log 0 = 0$ conventions are critical.
- **⚖️ Symmetry (Noether):** Validates the fundamental duality between homology chains ($\partial_k$) and cohomology
  cochains ($d_{k-1} = \partial_k^T$) via Discrete Stokes'
  Theorem $\langle d\omega, c \rangle = \langle \omega, \partial c \rangle$, and verifies Hodge Theorem
  isomorphism $\dim (\ker \Delta_k) = \beta_k$.
- **💡 Clarity (Feynman):** Uses classical geometric surfaces—the Circle $S^1$, Hollow Tetrahedron $\cong S^2$, Minimal
  Triangulated Torus $T^2$ ($\beta = (1, 2, 1)$), and Disconnected Clusters—as transparent, self-explanatory topological
  test beds.

---

## Specification

### 1. Target Modules & Comparative Verification Matrix

Tests reside in `tests/verifications/test_differential_topology_prob.py`:

| AlgebraX Module & Function                    | External Oracle / Analytical Law                                        | Mathematical Truth Verified                                                                                            | Tolerance                    |
|:----------------------------------------------|:------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|:-----------------------------|
| `homology.SimplicialComplex.betti_numbers`    | `np.linalg.matrix_rank` on dense $\partial_k$ & canonical manifolds     | $\beta_k =                                                                                                             | K_k                          | - \operatorname{rank}(\partial_k) - \operatorname{rank}(\partial_{k+1})$; matches $S^1 (1,1,0)$, $S^2 (1,0,1)$, $T^2 (1,2,1)$ | **Exact (`==`)** |
| `homology` Euler–Poincaré Characteristic      | $\chi(K) = \sum_k (-1)^k                                                | K_k                                                                                                                    | $ vs $\sum_k (-1)^k \beta_k$ | Topological Euler characteristic invariant holds for all generated complexes | **Exact (`==`)** |
| `homology` Discrete Stokes' Theorem           | `exterior_derivative` ($d\omega$) vs `boundary_matrices` ($\partial c$) | $\langle d\omega, c \rangle = \langle \omega, \partial c \rangle$ for all $(k-1)$-cochains $\omega$ and $k$-chains $c$ | $10^{-11}$                   |
| `homology.hodge_laplacian(k)`                 | `scipy.linalg.eigvalsh(Delta_k)` nullity                                | Number of zero eigenvalues of $\Delta_k$ equals Betti number $\beta_k$ (Discrete Hodge Theorem)                        | **Exact (`==`)**             |
| `probability.entropy(P)`                      | `scipy.stats.entropy(P)`                                                | Shannon entropy $H(P) = -\sum p_i \ln p_i$ parity, $0 \le H(P) \le \ln                                                 | S                            |$ | $10^{-11}$ |
| `probability.kl_divergence(P, Q)`             | `scipy.stats.entropy(P, Q)` / `scipy.special.rel_entr`                  | $D_{KL}(P \| Q)$ parity, Gibbs' inequality $D_{KL}(P \| Q) \ge 0$, $D_{KL}(P \| P) = 0$                                | $10^{-11}$                   |
| `probability.js_divergence(P, Q)`             | `scipy.spatial.distance.jensenshannon(P, Q) ** 2`                       | Symmetry $JSD(P \| Q) = JSD(Q \| P)$, boundedness $0 \le JSD \le \ln 2$                                                | $10^{-11}$                   |
| `probability.bayes_update(prior, likelihood)` | Analytical Bayes' Rule & iterated sequential conditioning               | Commutativity of independent evidence updates $B(B(P, E_1), E_2) = B(B(P, E_2), E_1)$                                  | $10^{-12}$                   |
| `automata.simulate_dfa` / `simulate_nfa`      | Rabin–Scott powerset DFA & regex oracle                                 | NFA acceptance equals determinized DFA acceptance across $\Sigma^*$ words                                              | **Exact (`==`)**             |
| `metrics.density` / `sparsity`                | Dense `np.count_nonzero(A) / A.size`                                    | Exact density + sparsity $= 1.0$ conservation                                                                          | $10^{-12}$                   |

---

## Backwards Compatibility

Purely additive verification test suite under `tests/verifications/test_differential_topology_prob.py`. Zero impact on
`src/algebrax`.

---

## How to Teach This / Documentation Plan

1. Add Discrete Stokes' Theorem and Discrete Hodge Theorem ($\dim \ker \Delta_k = \beta_k$) verification examples to
   `docs/guide/geometry/`.
2. Add Information Theory vs `scipy.stats` verification table to `docs/guide/probability/information.md`.

---

## Reference Implementation

- `tests/verifications/test_differential_topology_prob.py`

---

## Rejected Ideas

1. **Requiring `gudhi` or `ripser` C++ Bindings as Mandatory CI Dependencies:** Rejected because `gudhi` binary wheels
   often lag behind bleeding-edge Python releases (e.g., Python 3.14 on Windows). Using `numpy.linalg.matrix_rank`,
   `scipy.linalg.eigvalsh`, and exact rational Smith/Gaussian rank alongside optional `pytest.importorskip("gudhi")`
   guards guarantees 100% execution on Python 3.14 while supporting `gudhi` when installed.

---

## Open Questions

None.

---

## Change Log

- **2026-10-24**: Initial draft created as Wave 1D of the Phase 5 Comparative Verification series.
