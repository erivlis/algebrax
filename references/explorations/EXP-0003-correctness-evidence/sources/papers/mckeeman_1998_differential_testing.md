# Differential Testing for Software

| Field | Value |
|:---|:---|
| **Citation** | William M. McKeeman. *Differential Testing for Software*. Digital Technical Journal, Vol. 10, No. 1, pp. 100–107, December 1998. |
| **Publisher** | Digital Equipment Corporation (DEC) / Compaq |
| **Semantic Scholar ID** | [Corpus ID 14018070](https://www.semanticscholar.org/paper/Differential-Testing-for-Software-McKeeman/fc881e8d0432ea8e4dd5fda4979243cac5e4b9e3) |
| **Archival Mirror** | [Wang Zhijie DTJ Archive](https://wangzhijie.me/papers/1998/dtj/vol10num1art9.pdf) |
| **Keywords** | Differential Testing, Test Oracle Problem, Automated Fuzzing, Dual-System Testing, Test-Case Reduction |

---

## Abstract & Summary

Differential testing is an automated testing methodology designed to resolve the **test oracle problem** when testing complex systems such as compilers, run-time interpreters, and mathematical engines. Rather than constructing a golden reference output for every randomly generated input, differential testing feeds the exact same input to two or more comparable, independent systems. Any behavioral discrepancy or divergent output flags a potential defect in one or more implementations.

---

## Core Methodological Principles

### 1. Dual Independent Implementations as Mutual Oracles
Let $S_1$ and $S_2$ be two independent implementations of the same specification $Spec$. For a generated input $x$:
$$y_1 = S_1(x), \quad y_2 = S_2(x)$$
If $y_1 \ne y_2$ (or if one crashes while the other terminates), an inconsistency is flagged without knowing a priori whether $y_1$ or $y_2$ was the mathematically correct value.

### 2. High-Volume Random Input Generation
Inputs are synthesized using grammar-based random generation, exercising obscure syntax branches, corner cases, and operator combinations rarely encountered in human-written test suites.

### 3. Automated Test-Case Reduction
Because randomly generated inputs can be large and unwieldy, automated reduction algorithms iteratively strip elements until the minimal discrepancy-triggering input is isolated.

---

## Direct Application to AlgebraX Verification Suite

In **AlgebraX** (`EP-0180` and `tests/verifications/test_differential_*.py`), Differential Testing implements **Methodology 1**:

1. **Sparse Matrix Linear Algebra vs NumPy & SciPy:**
   - Evaluating matrix products `dot(A, B)`, matrix powers `power(A, k)`, trace, and determinant.
   - Mapping `algebrax` sparse dictionary matrices to dense NumPy `ndarray` and SciPy `csr_matrix`.
   - Asserting equivalence within condition-scaled numerical tolerance ($10^{-12}$).
2. **Discrete Signal Transforms vs NumPy FFT:**
   - Comparing `dft`, `idft`, and circular convolution against `numpy.fft.fft`.
3. **Graph Laplacians & Spectral Metrics vs NetworkX:**
   - Comparing unnormalized/normalized graph Laplacians, Fiedler vectors, and PageRank iterations against `networkx`.
4. **Simplicial Homology vs GUDHI & Dionysus:**
   - Validating boundary matrix ranks and Betti numbers against GUDHI simplicial streams.
