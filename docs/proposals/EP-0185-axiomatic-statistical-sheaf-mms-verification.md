---
title: "EP-0185: Axiomatic Property, Streaming Moment & Manufactured Solution Verification Across Semirings, Categories, Lattices & Sheaves"
description: "Extends Hypothesis property-based verification across all 34 built-in semirings, verifies streaming statistical moment semirings against SciPy batch statistics, tests Kleisli monad and lattice laws, and verifies Cellular Sheaf PDEs via the Method of Manufactured Solutions (MMS)."
icon: lucide/layers
status: draft
---

# EP-0185: Axiomatic Property, Streaming Moment & Manufactured Solution Verification Across Semirings, Categories, Lattices & Sheaves

| Field             | Value                                                                                                                      |
|:------------------|:---------------------------------------------------------------------------------------------------------------------------|
| **EP**            | 0185                                                                                                                       |
| **Title**         | Axiomatic Property, Streaming Moment & Manufactured Solution Verification Across Semirings, Categories, Lattices & Sheaves |
| **Author**        | Eran Rivlis & Antigravity (Council Agent)                                                                                  |
| **Sponsor**       | The Council                                                                                                                |
| **Delegate**      | 🔬 Karl Popper (Falsifiability), ⚖️ Emmy Noether (Symmetry), 🧩 Bertrand Russell (Consistency) & ⚡ Claude Shannon         |
| **Status**        | Draft                                                                                                                      |
| **Type**          | Standards Track                                                                                                            |
| **Created**       | 2026-10-24                                                                                                                 |
| **Updated**       | 2026-10-24                                                                                                                 |
| **Replaces**      | None                                                                                                                       |
| **Superseded-By** | None                                                                                                                       |

---

## Abstract

This proposal specifies **Wave 2A** of the Phase 5 Mathematical Verification Track
([EP-0180](EP-0180-multi-layered-verification-suite.md)), addressing the domains where `algebrax` implements novel or
higher-order mathematical structures beyond standard dense matrix libraries:

1. **The Full 34-Semiring Catalog (`algebrax.semiring`)**: Generalizing [`tests/algebrax/test_verification.py`](../../tests/algebrax/test_verification.py) with custom Hypothesis strategies
   for all 34 semirings, and differentially verifying **Streaming Statistical Moment Semirings** (`Expectation`,
   `Variance`, `Skewness`, `Kurtosis`, `BivariateCovariance`, `BinomialConvolution`, `MultivariateMoment`) against batch
   **`numpy`** and **`scipy.stats`** moment calculations (`np.mean`, `np.var`, `scipy.stats.skew`,
   `scipy.stats.kurtosis`, `np.cov`).
2. **Categories, Lattices & Tries (`algebrax.category`, `algebrax.lattice`, `algebrax.trie`)**: Property-based
   verification of Kleisli monad laws, Kan extensions, distributive lattice absorption/De Morgan laws, and
   `AlgebraicTrie` prefix-tree homomorphisms.
3. **Method of Manufactured Solutions (MMS) for Cellular Sheaves & Graph PDEs (`algebrax.homology`,
   `algebrax.analysis`)**: Applying Salari & Knupp's (2000) MMS methodology to verify `CellularSheaf`
   Laplacians $\mathcal{L}_{\mathcal{F}}$, `sheaf_diffusion`, `sheaf_harmonic_extension`, and `laplacian_smoothing`
   against exact analytical manufactured solutions.

---

## Motivation

1. **Closing the 29-Semiring Hypothesis Gap:** Currently, `tests/verifications/test_axiomatic_properties.py` tests 5
   semirings with Hypothesis, while the remaining 29 semirings in the catalog are only checked against 3–5 static values
   in `test_verification.py`. Streaming statistical semirings (`VarianceSemiring`, `SkewnessSemiring`,
   `KurtosisSemiring`, `MultivariateMomentSemiring`) use Welford/Chan parallel merge algebras and divided-power binomial
   convolutions ([EP-0149](EP-0149-binomial-convolution-moment-semiring.md)). Pitting their associative parallel fold
   `(S(A) + S(B))` directly against `scipy.stats.skew(A + B)` and `scipy.stats.kurtosis(A + B)` on partitioned random
   datasets is the ultimate "Stamp of Trust" for streaming statistics.
2. **Testing PDEs Without External Oracles via MMS:** No mainstream Python library provides general Cellular Sheaf
   harmonic extension (`sheaf_harmonic_extension`) or sheaf diffusion (`sheaf_diffusion`) out of the box. Using the
   **Method of Manufactured Solutions (MMS)**—constructing a known global section or stalk assignment $x^*$, computing
   its forcing residual $f = \mathcal{L}_{\mathcal{F}} x^*$, and verifying that the solver recovers $x^*$ on interior
   vertices—solves the test oracle problem with exact analytical rigor.
3. **Categorical, Lattice & Trie Algebraic Completeness:** `category.py`, `lattice.py`, and `trie.py` previously had 0%
   representation in `tests/verifications/`. Verifying Kleisli associativity, lattice absorption, and
   Trie-to-SparseVector isomorphism brings module coverage to 100%.

---

## Rationale

- **🔬 Falsifiability (Popper):** Hypothesis strategies generate arbitrary dataset
  partitions $D = D_1 \sqcup D_2 \sqcup D_3$ and verify that folding `StatisticalMomentSemiring.add` across partitions
  reproduces `scipy.stats` moments on $D$.
- **⚖️ Symmetry (Noether):** Validates monadic associativity $(f \circ_K g) \circ_K h = f \circ_K (g \circ_K h)$,
  lattice duality (join/meet absorption), and sheaf restriction-adjunction
  symmetry $\mathcal{L}_{\mathcal{F}} = \delta^T \delta$.
- **🧩 Consistency (Russell):** Proves that `AlgebraicTrie` operations commute with flat dictionary vector/tensor
  operations: $\operatorname{to\_dict} (T_1 \oplus T_2) = \operatorname{to\_dict} (T_1) \oplus \operatorname{to\_dict} (T_2)$.

---

## Specification

### 1. Verification Matrix

Tests reside in `tests/verifications/test_axiomatic_properties.py` (expanded),
`tests/verifications/test_differential_statistical_semirings.py`, and
`tests/verifications/test_mms_sheaves_and_categories.py`:

| Domain / Module          | Target Structure / Function                       | Verification Methodology & Oracle                                               | Mathematical Identity Checked                                                                                                                                    |
|:-------------------------|:--------------------------------------------------|:--------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `semiring.statistical`   | `Expectation`, `Variance`, `Skewness`, `Kurtosis` | Differential vs `np.mean`, `np.var`, `scipy.stats.skew`, `scipy.stats.kurtosis` | Associative parallel merge of partitioned streams $D_1 \sqcup D_2$ matches batch statistics on $D_1 \cup D_2$ ($10^{-10}$)                                       |
| `semiring.statistical`   | `BivariateCovariance`, `BivariateVariance`        | Differential vs `np.cov(X, Y, ddof=0)`                                          | Parallel merge of $(X_1, Y_1) \oplus (X_2, Y_2)$ matches full sample covariance ($10^{-10}$)                                                                     |
| `semiring.statistical`   | `BinomialConvolution`, `MultivariateMoment`       | Differential vs raw power moments $\frac{1}{N}\sum (x - \mu)^k$                 | Divided-power binomial convolution algebra matches exact shifted moments                                                                                         |
| `semiring` (All 34)      | Full `Semiring.catalog()`                         | Hypothesis property-based axiom runner + `.star(a)` dioid closure               | All 9 semiring axioms + Kleene star fixed-point law $a^* = 1 \oplus a \otimes a^*$                                                                               |
| `homology.CellularSheaf` | `sheaf_laplacian`, `sheaf_harmonic_extension`     | Method of Manufactured Solutions (MMS)                                          | Manufactured global section $s \in \ker \mathcal{L}_{\mathcal{F}}$ restricted to boundary $\partial B$ is exactly recovered on interior $V \setminus \partial B$ |
| `homology.CellularSheaf` | `sheaf_diffusion`                                 | MMS & Energy Monotonicity Certificate                                           | Dirichlet sheaf energy $E(x_t) = x_t^T \mathcal{L}_{\mathcal{F}} x_t$ is monotonically non-increasing and converges to harmonic equilibrium                      |
| `category`               | `kleisli_compose`, `kan_extension`                | Hypothesis Metamorphic Monad Laws                                               | Left identity $\eta \circ_K f = f$, Right identity $f \circ_K \eta = f$, Associativity $(f \circ_K g) \circ_K h = f \circ_K (g \circ_K h)$                       |
| `lattice`                | `join`, `meet`, `combine`                         | Hypothesis Lattice Axiom Suite                                                  | Idempotence, Commutativity, Associativity, Absorption $a \lor (a \land b) = a$ & $a \land (a \lor b) = a$                                                        |
| `trie`                   | `AlgebraicTrie`                                   | Homomorphism vs `SparseVector`                                                  | $\Phi(T_1 \oplus_{\mathcal{S}} T_2) = \Phi(T_1) \oplus_{\mathcal{S}} \Phi(T_2)$ across semirings                                                                 |

---

## Backwards Compatibility

Purely additive verification tests under `tests/verifications/`. Zero changes to `src/algebrax`.

---

## How to Teach This / Documentation Plan

1. Document the Streaming Moment Semiring vs `scipy.stats` equivalence in `docs/guide/`.
2. Showcase the Method of Manufactured Solutions (MMS) for Cellular Sheaf harmonic extension in
   `references/explorations/EXP-0003-correctness-evidence/`.

---

## Reference Implementation

- `tests/verifications/test_axiomatic_properties.py`
- `tests/verifications/test_differential_statistical_semirings.py`
- `tests/verifications/test_mms_sheaves_and_categories.py`

---

## Rejected Ideas

1. **Testing `Skewness` and `Kurtosis` Semirings on Degenerate Zero-Variance Constant Streams Without Guard:** Constant
   arrays have $\sigma^2 = 0$, where standardized skewness $m_3 / \sigma^3$ is $0/0$ (`NaN` in `scipy.stats.skew`).
   Hypothesis strategies filter or explicitly test non-degenerate variance $\sigma^2 > 10^{-8}$ when comparing
   standardized cumulants against `scipy.stats`.

---

## Open Questions

None.

---

## Change Log

- **2026-10-24**: Initial draft created as Wave 2A of the Phase 5 Mathematical Verification Track.
