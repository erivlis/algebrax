---
title: "EP-0181: Comparative Verification — Linear Algebra, Tensors & Signal Processing (NumPy & SciPy Oracles)"
description: "Establishes differential and comparative verification tests pitting AlgebraX sparse matrix factorizations, linear solvers, multidimensional einsum contractions, and signal transforms head-to-head against NumPy and SciPy reference implementations."
icon: lucide/check-check
status: final
---

# EP-0181: Comparative Verification — Linear Algebra, Tensors & Signal Processing (`NumPy` & `SciPy` Oracles)

| Field             | Value                                                                                                             |
|:------------------|:------------------------------------------------------------------------------------------------------------------|
| **EP**            | 0181                                                                                                              |
| **Title**         | Comparative Verification — Linear Algebra, Tensors & Signal Processing (`NumPy` & `SciPy` Oracles)                |
| **Author**        | Eran Rivlis & Antigravity (Council Agent)                                                                         |
| **Sponsor**       | The Council                                                                                                       |
| **Delegate**      | 🔬 Karl Popper (Falsifiability), 🧩 Bertrand Russell (Consistency), ⚡ Claude Shannon (Efficiency) & 🛡️ The Golem |
| **Status**        | Final                                                                                                             |
| **Type**          | Standards Track                                                                                                   |
| **Created**       | 2026-10-24                                                                                                        |
| **Updated**       | 2026-10-24                                                                                                        |
| **Replaces**      | None                                                                                                              |
| **Superseded-By** | None                                                                                                              |

---

## Abstract

This proposal specifies **Wave 1A** of the Phase 5 Mathematical Verification Track
([EP-0180](EP-0180-multi-layered-verification-suite.md)): a comprehensive **Comparative (Differential) Verification
Suite** that pits `algebrax` linear algebra, matrix decompositions, sparse tensor contractions, and discrete signal
transforms directly against industry-standard **NumPy** (`numpy.linalg`, `numpy.fft`, `numpy.einsum`) and **SciPy**
(`scipy.linalg`, `scipy.sparse`, `scipy.signal`) reference engines. By verifying that pure-Python sparse dictionary
representations in `algebrax` produce results numerically indistinguishable from LAPACK, BLAS, and PocketFFT backends
across randomized Hypothesis test cases, this proposal establishes a verifiable industry "Stamp of Trust" for the
numerical core of `algebrax`.

---

## Motivation

While internal algebraic identities (such as $(A B)^T = B^T A^T$) verify self-consistency, scientific and enterprise
adopters require external ground-truth validation:

1. **The "Stamp of Trust" Imperative:** `algebrax` implements pure-Python algorithms for LU, QR, SVD, and Cholesky
   factorizations (`algebrax.matrix.decompose`), linear system solvers (`solve`, `cg_solve`, `inverse`, `determinant`),
   arbitrary-rank Einstein summation (`algebrax.tensor.einsum`), and spectral signal transforms (`algebrax.transforms`).
   Proving that these routines agree to $10^{-10}$ relative tolerance with `numpy` and `scipy` across thousands of
   randomized inputs eliminates skepticism regarding homegrown numerical routines.
2. **Subtle Edge Cases in Sparse Dict Representations:** Sparse nested dictionaries omit structural zeroes. During
   Gaussian elimination (`lu`, `solve`), Gram–Schmidt orthogonalization (`qr`), or Jacobi/bidiagonal sweeps (`svd`),
   implicit zero handling, pivot selection, and sign conventions can diverge from dense array semantics if not
   continuously cross-checked against LAPACK oracles.
3. **Multidimensional Contraction Fidelity:** `algebrax.tensor.einsum` supports complex subscript strings (e.g.,
   `'ijk,jkl->il'`, `'i,j->ij'`, `'ii->i'`, ellipsis broadcasting). Differential testing against `numpy.einsum`
   guarantees 100% index-semantics parity.
4. **Converter Round-Trip Losslessness:** `algebrax.converters` (`to_numpy`, `from_numpy`, `to_scipy`, `from_scipy`)
   forms the bridge between `algebrax` and the PyData ecosystem; differential tests simultaneously validate both the
   converters and the mathematical operators.

---

## Rationale

This proposal aligns with **The Council Framework** (*PRINCIPLES.md*):

- **🔬 Falsifiability (Popper):** Every numerical function in `matrix`, `tensor`, and `transforms` is paired with an
  external LAPACK/FFT oracle and subjected to Hypothesis-generated matrices (well-conditioned, sparse, diagonal,
  triangular, symmetric positive-definite, and rectangular).
- **🧩 Consistency (Russell):** Establishes a commute-diagram isomorphism between `SparseMatrix` / `SparseTensor`
  operations and `numpy.ndarray` / `scipy.sparse.csr_matrix` operations:
  $$\operatorname{to\_numpy} (f_{\text{algebrax}} (A, B)) \approx f_{\text{numpy}} (\operatorname{to\_numpy} (A), \operatorname{to\_numpy} (B))$$
- **⚡ Efficiency (Shannon):** Matrix dimensions in CI are bounded to $N \in [2, 16]$ with `@settings(max_examples=30)`,
  achieving exhaustive structural coverage in $< 2\text{s}$ total runtime.
- **🛡️ Safety (The Golem):** Handles gauge degrees of freedom in matrix factorizations (such as sign ambiguity in QR and
  SVD singular vectors) by verifying both canonicalized factor equivalence and reconstruction certificates.

---

## Specification

### 1. Target Modules & Comparative Verification Matrix

All tests reside under `tests/verifications/test_differential_numpy.py` and
`tests/verifications/test_differential_scipy.py`:

| AlgebraX Module & Function                         | Industry Reference Oracle                           | Mathematical Equivalence / Certificate Checked                                                                    | Tolerance  |
|:---------------------------------------------------|:----------------------------------------------------|:------------------------------------------------------------------------------------------------------------------|:-----------|
| `matrix.dot(A, B)`                                 | `np.matmul(A, B)` / `scipy.sparse`                  | $\|(A B)_{\text{ax}} - (A B)_{\text{np}}\|_\infty \le \epsilon$                                                   | $10^{-11}$ |
| `matrix.add`, `sub`, `scale`, `transpose`, `trace` | `np.add`, `np.subtract`, `np.transpose`, `np.trace` | Exact entrywise equivalence                                                                                       | $10^{-12}$ |
| `matrix.power(A, k)`                               | `np.linalg.matrix_power(A, k)`                      | Binary exponentiation parity for $k \in \{0, 1, 2, 5, 8\}$                                                        | $10^{-10}$ |
| `matrix.determinant(A)`                            | `np.linalg.det(A)` & `scipy.linalg.det(A)`          | $\|\det_{\text{ax}}(A) - \det_{\text{np}}(A)\| \le \epsilon \cdot \|A\|^N$                                        | $10^{-9}$  |
| `matrix.inverse(A)`                                | `np.linalg.inv(A)`                                  | $\|A_{\text{ax}}^{-1} - A_{\text{np}}^{-1}\|_\infty \le \epsilon$ and $\|A A_{\text{ax}}^{-1} - I\| \le \epsilon$ | $10^{-9}$  |
| `matrix.solve(A, b)`                               | `np.linalg.solve(A, b)`                             | $\|x_{\text{ax}} - x_{\text{np}}\|_\infty \le \epsilon$ on non-singular systems                                   | $10^{-9}$  |
| `matrix.cg_solve(A, b)`                            | `scipy.sparse.linalg.cg(A, b)`                      | Conjugate gradient solution parity on SPD systems                                                                 | $10^{-7}$  |
| `matrix.decompose.lu(A)`                           | `scipy.linalg.lu(A)`                                | $P A = L U$, $L$ unit lower-triangular, $U$ upper-triangular                                                      | $10^{-9}$  |
| `matrix.decompose.qr(A)`                           | `np.linalg.qr(A)`                                   | $A = Q R$, $Q^T Q = I$, $R$ upper-triangular (up to diagonal phase)                                               | $10^{-9}$  |
| `matrix.decompose.cholesky(A)`                     | `np.linalg.cholesky(A)`                             | Exact entrywise match $L_{\text{ax}} \approx L_{\text{np}}$ on SPD matrices ($A = M M^T + \alpha I$)              | $10^{-9}$  |
| `matrix.decompose.svd(A)`                          | `np.linalg.svd(A)`                                  | Singular values $\sigma_i(\text{ax}) \approx \sigma_i(\text{np})$, $A = U \Sigma V^T$, $U^T U = V^T V = I$        | $10^{-7}$  |
| `tensor.einsum(subscripts, *operands)`             | `np.einsum(subscripts, *operands)`                  | Trace `'ii->'`, diagonal `'ii->i'`, batch matmul `'bij,bjk->bik'`, outer `'i,j->ij'`, 3-tensor contraction        | $10^{-10}$ |
| `tensor.permute_tensor(T, axes)`                   | `np.transpose(T, axes)`                             | Exact coordinate mapping under arbitrary axis permutations                                                        | $10^{-12}$ |
| `transforms.dft(x)` / `idft(X)`                    | `np.fft.fft(x)` / `np.fft.ifft(X)`                  | Complex spectrum parity & round-trip inversion $\operatorname{IDFT}(\operatorname{DFT}(x)) = x$                   | $10^{-10}$ |
| `transforms.convolve(x, h)`                        | `np.convolve(x, h)` / `scipy.signal.convolve`       | Discrete linear and circular convolution equivalence                                                              | $10^{-10}$ |
| `transforms.walsh_hadamard(x)`                     | `scipy.linalg.hadamard(2^k) @ x`                    | Fast Walsh–Hadamard transform vs explicit Hadamard matrix product                                                 | $10^{-10}$ |
| `converters.to_numpy` / `from_numpy`               | `scipy.sparse.csr_matrix`                           | Isomorphic round-trip conversion preservation                                                                     | Exact      |

### 2. Handling Gauge Ambiguities in Factorizations

Certain matrix decompositions are unique only up to a diagonal sign or orthogonal subspace gauge:

- **Cholesky**: Unique for symmetric positive-definite (SPD) matrices with positive diagonal entries; verified by direct
  entrywise comparison against `np.linalg.cholesky`.
- **QR**: Unique up to column signs of $Q$ (and corresponding row signs of $R$) when $\operatorname{diag} (R) > 0$. The
  differential test normalizes both `algebrax` and `numpy` outputs so $\operatorname{diag} (R) > 0$ before asserting
  entrywise equality $Q_{\text{ax}} \approx Q_{\text{np}}$ and $R_{\text{ax}} \approx R_{\text{np}}$.
- **SVD**: Singular values $\Sigma$ are uniquely ordered ($\sigma_1 \ge \sigma_2 \ge \dots \ge 0$) and compared directly
  against `np.linalg.svd(A, compute_uv=False)`, while $U$ and $V^T$ are verified via reconstruction $U \Sigma V^T = A$
  and orthonormality $U^T U = I, V^T V = I$.

---

## Backwards Compatibility

This proposal adds comparative verification tests exclusively under `tests/verifications/`. It introduces zero changes
to runtime code in `src/algebrax` and maintains full backwards compatibility.

---

## How to Teach This / Documentation Plan

1. Publish a **Comparative Verification Matrix** table in the documentation showing every `matrix`, `tensor`, and
   `transforms` function alongside its verified NumPy/SciPy counterpart.
2. Document how contributors can run the NumPy/SciPy comparative suite via
   `uv run pytest tests/verifications/ -m differential`.

---

## Reference Implementation

- `tests/verifications/test_differential_numpy.py`
- `tests/verifications/test_differential_scipy.py`

---

## Rejected Ideas

1. **Direct Entrywise Comparison of Unnormalized SVD Vectors $U, V$:** Rejected because singular vectors corresponding
   to singular values (especially repeated or zero singular values) have sign and rotation gauge freedoms across
   different SVD algorithms (Golub–Kahan vs. Jacobi). Comparing sorted singular values $\sigma_i$ against
   `np.linalg.svd` plus verifying $U \Sigma V^T = A$ and orthogonality is mathematically sound.
2. **Testing Ill-Conditioned Random Matrices Without Conditioning Control:** Rejected for `solve` and `inverse`
   differential tests because matrices with condition number $\kappa (A) > 10^{12}$ amplify IEEE 754 rounding noise.
   Hypothesis strategies construct diagonally dominant or bounded-condition matrices ($\kappa (A) < 10^5$) for solver
   parity tests.

---

## Open Questions

None.

---

## Change Log

- **2026-10-24**: Initial draft created as part of the Phase 5 Comparative Verification ("Stamp of Trust") series.
