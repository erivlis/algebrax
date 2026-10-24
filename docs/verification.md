---
title: Mathematical Verification & Stamp of Trust
description: Complete traceability matrix mapping AlgebraX mathematical functions to their verification tests, methodologies, and external industry reference oracles (NumPy, SciPy, Hypothesis, PIT).
icon: lucide/shield-check
---

# Mathematical Verification & Stamp of Trust

Because `algebrax` implements foundational linear algebra, semirings, discrete exterior calculus, spectral transforms, and Lie algebras in **100% pure Python with zero required runtime dependencies**, mathematical correctness cannot be left to conventional unit tests alone.

To earn a verifiable **Stamp of Trust**, `algebrax` employs a **Multi-Layered Verification Suite** housed under `tests/verifications/` (alongside the built-in law verifier in `tests/algebrax/test_verification.py`). Every mathematical claim is continuously cross-checked against external industry-standard reference engines (**NumPy**, **SciPy**, **LAPACK**, **PocketFFT**) and rigorous mathematical invariants.

---

## 1. Verification Methodologies & Categories

Each test in `tests/verifications/` is categorized by its formal verification methodology and pytest marker:

| Category / Marker    | Verification Methodology                                                         | How It Establishes Mathematical Truth                                                                                                                                                                                                                             |
|:---------------------|:---------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **`differential`**   | **Comparative / Differential Oracle Testing** *(McKeeman, 1998)*                 | Pits `algebrax` sparse dictionary algorithms directly against battle-tested C/Fortran reference libraries (`numpy.linalg`, `scipy.linalg`, `scipy.sparse.linalg`, `numpy.fft`, `scipy.signal`) across deterministic and Hypothesis-generated inputs.              |
| **`axiomatic`**      | **Property-Based Algebraic Law Testing** *(MacIver et al., 2019)*                | Uses **Hypothesis** to generate adversarial random inputs (including $\pm\infty$, boundary probabilities, and exact rationals) and verifies universal algebraic axioms (associativity, commutativity, distributivity, identity, annihilation).                    |
| **`Exact Rational`** | **Infinite-Precision $\mathbb{Q}$ Verification**                                 | Evaluates semirings and matrix operations over Python's exact `fractions.Fraction` field, eliminating IEEE 754 floating-point rounding tolerances ($\epsilon = 0$).                                                                                               |
| **`metamorphic`**    | **Metamorphic Invariant Relations** *(Chen et al., 1998)*                        | Verifies necessary structural conservation laws across input transformations when no external oracle exists (e.g., $(A \otimes B)^T = B^T \otimes A^T$, boundary nilpotency $\partial^2 = 0$, graph vertex permutation conjugacy $L(P A P^T) = P L(A) P^T$).      |
| **`pit`**            | **Schwartz–Zippel Polynomial Identity Testing** *(Schwartz, 1980; Saxena, 2014)* | Defeats exponential symbolic monomial blowup by evaluating high-degree identities (such as the Jacobi identity on 14-dimensional $\mathfrak{g}_2$) at random integer coordinates in $S \subset \mathbb{Z}$, bounding false-positive error probability to $\le (d/ |S|)^k \le 10^{-16}$. |
| **`certificates`**   | **Proof-Carrying Solver (PCS) Witnesses**                                        | Verifies the output of expensive $O(N^3)$ numerical solvers (e.g., Helmholtz–Hodge decomposition, LU, QR, SVD) via fast, independent $O(\text{nnz})$ algebraic witness checks (orthogonality, curl/divergence annihilation, exact reconstruction).                |

---

## 2. Traceability Matrix: Functionality $\to$ Verification Test

The tables below map each `algebrax` module and function to the exact verification test function, verification category, external oracle or mathematical law verified, and numerical precision.

### 2.1. Sparse Linear Algebra & Solvers (`algebrax.matrix`)

| AlgebraX Function | Verification Category | Reference Oracle / Mathematical Law | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `ax.matrix.dot(A, B)` | **Comparative (`differential`)** | `numpy.matmul(A, B)` | `test_differential_numpy.py::test_differential_matrix_multiplication_and_addition` | $10^{-10}$ |
| `ax.matrix.dot(A, B)` | **Comparative + Property (`differential`)** | `numpy.matmul(A, B)` over Hypothesis $4 \times 4$ matrices | `test_differential_numpy.py::test_hypothesis_differential_matmul_and_lu` | $10^{-9}$ |
| `ax.matrix.dot(A, B, semiring)` | **Metamorphic (`metamorphic`)** | Transpose duality $(A \otimes B)^T = B^T \otimes A^T$ & scalar homogeneity $c(AB) = (cA)B$ | `test_metamorphic_invariants.py::test_metamorphic_matrix_transpose_duality`, `test_metamorphic_scalar_homogeneity` | $10^{-10}$ |
| `ax.matrix.add(A, B)` / `subtract(A, B)` | **Comparative (`differential`)** | `numpy.add(A, B)` / `numpy.subtract(A, B)` | `test_differential_numpy.py::test_differential_matrix_multiplication_and_addition` | $10^{-12}$ |
| `ax.matrix.transpose(A)` | **Comparative (`differential`)** | `numpy.transpose(A)` | `test_differential_numpy.py::test_differential_transpose_trace_and_frobenius` | $10^{-12}$ |
| `ax.matrix.trace(A)` | **Comparative (`differential`)** | `numpy.trace(A)` | `test_differential_numpy.py::test_differential_transpose_trace_and_frobenius` | $10^{-12}$ |
| `ax.matrix.frobenius_inner(A, B)` | **Comparative (`differential`)** | `numpy.sum(A * B)` ($\operatorname{Tr}(A^T B)$) | `test_differential_numpy.py::test_differential_transpose_trace_and_frobenius` | $10^{-11}$ |
| `ax.matrix.power(A, k)` | **Comparative (`differential`)** | `numpy.linalg.matrix_power(A, k)` for $k \in \{0, 1, 2, 5\}$ | `test_differential_numpy.py::test_differential_matrix_power` | $10^{-10}$ |
| `ax.matrix.mat_vec`, `vec_mat`, `inner`, `vec_norm`, `vec_axpy` | **Comparative (`differential`)** | `A @ x`, `x @ A`, `np.dot(x, y)`, `np.linalg.norm(x)`, $\alpha x + y$ | `test_differential_numpy.py::test_differential_mat_vec_and_vec_ops` | $10^{-11}$ |
| `ax.matrix.block_diag([A, B])` | **Comparative (`differential`)** | `scipy.linalg.block_diag(A, B)` | `test_differential_numpy.py::test_differential_block_diag_vs_scipy_block_diag` | $10^{-12}$ |
| `ax.matrix.inverse(A)` | **Comparative (`differential`)** | `numpy.linalg.inv(A)` | `test_differential_numpy.py::test_differential_inverse_and_determinant` | $10^{-9}$ |
| `ax.matrix.academic.determinant(A)` | **Comparative (`differential`)** | `numpy.linalg.det(A)` & `scipy.linalg.det(A)` | `test_differential_numpy.py::test_differential_inverse_and_determinant` | $10^{-9}$ |
| `ax.matrix.cg_solve(A, b)` | **Comparative (`differential`)** | `scipy.sparse.linalg.cg(A, b)` & `numpy.linalg.solve(A, b)` | `test_differential_numpy.py::test_differential_cg_solve_vs_scipy_cg` | $10^{-7}$ |
| `ax.matrix.laplacian_matrix(A)` | **Metamorphic (`metamorphic`)** | Vertex permutation conjugacy $L(P A P^T) = P L(A) P^T$ | `test_metamorphic_invariants.py::test_metamorphic_graph_laplacian_permutation_conjugacy` | $10^{-10}$ |

---

### 2.2. Matrix Decompositions (`algebrax.matrix.decompose`)

| AlgebraX Function | Verification Category | Reference Oracle / Certificate Checked | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `ax.matrix.cholesky(A)` & `recompose_cholesky` | **Comparative + Certificate (`differential`)** | `numpy.linalg.cholesky(A)` entrywise match & $L L^T = A$ | `test_differential_numpy.py::test_differential_cholesky_vs_numpy` | $10^{-9}$ |
| `ax.matrix.lu(A)` & `recompose_lu` | **Comparative + Certificate (`differential`)** | `scipy.linalg.lu(A)` entrywise match, $P A = L U$, unit lower $L$, upper $U$ | `test_differential_numpy.py::test_differential_lu_vs_scipy_lu`, `test_hypothesis_differential_matmul_and_lu` | $10^{-9}$ |
| `ax.matrix.qr(A)` & `recompose_qr` | **Comparative + Certificate (`differential`)** | `numpy.linalg.qr(A)` (positive $R$-diagonal gauge), $Q^T Q = I$, $Q R = A$ | `test_differential_numpy.py::test_differential_qr_vs_numpy_qr` | $10^{-8}$ |
| `ax.matrix.svd(A)` & `recompose_svd` | **Comparative + Certificate (`differential`)** | `numpy.linalg.svd(A)` singular values $\sigma_i$, $U^T U = I$, $V^T V = I$, $U \Sigma V^T = A$ | `test_differential_numpy.py::test_differential_svd_vs_numpy_svd` | $10^{-7}$ |

---

### 2.3. Multidimensional Tensors & Ecosystem Bridges (`algebrax.tensor`, `algebrax.converters`)

| AlgebraX Function | Verification Category | Reference Oracle / Mathematical Law | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `ax.tensor.einsum(subscripts, *T)` | **Comparative (`differential`)** | `numpy.einsum` across `'ijk,jkl->il'`, `'bij,bjk->bik'`, `'ii->'` | `test_differential_numpy.py::test_differential_tensor_einsum_vs_numpy` | $10^{-10}$ |
| `ax.tensor.permute_tensor` & `unpermute_tensor` | **Comparative + Involution (`differential`)** | `numpy.transpose(T, axes=(2, 0, 1))` & exact inverse restoration | `test_differential_numpy.py::test_differential_tensor_permute_vs_numpy` | $10^{-12}$ |
| `ax.converters.to_numpy` / `from_numpy` | **Comparative (`differential`)** | Lossless 2D `numpy.ndarray` isomorphism | `test_differential_numpy.py::test_differential_numpy_and_scipy_converters` | $10^{-12}$ |
| `ax.converters.to_scipy` / `from_scipy` | **Comparative (`differential`)** | Lossless `scipy.sparse` (`csr`, `csc`, `coo`) isomorphism | `test_differential_numpy.py::test_differential_numpy_and_scipy_converters` | $10^{-12}$ |

---

### 2.4. Spectral & Signal Transforms (`algebrax.transforms`)

| AlgebraX Function | Verification Category | Reference Oracle / Mathematical Law | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `ax.transforms.dft(x)` & `idft(X)` | **Comparative + Property (`differential`)** | `numpy.fft.fft(x)` & `numpy.fft.ifft(X)` (deterministic & Hypothesis) | `test_differential_numpy.py::test_differential_dft_idft_and_hilbert`, `test_hypothesis_differential_dft_and_wht` | $10^{-8}$ – $10^{-10}$ |
| `ax.transforms.dft(x)` | **Metamorphic (`metamorphic`)** | Circular time-shift magnitude invariance $\|\mathcal{F}(\text{shift}(x))\| = \|\mathcal{F}(x)\|$ | `test_metamorphic_invariants.py::test_metamorphic_dft_circular_shift_invariance` | $10^{-10}$ |
| `ax.transforms.hilbert(x)` | **Comparative (`differential`)** | `scipy.signal.hilbert(x)` analytic signal | `test_differential_numpy.py::test_differential_dft_idft_and_hilbert` | $10^{-10}$ |
| `ax.transforms.convolve` & `deconvolve` | **Comparative + Inversion (`differential`)** | `numpy.convolve(f, g)` & spectral circular deconvolution recovery | `test_differential_numpy.py::test_differential_convolve_and_deconvolve` | $10^{-9}$ – $10^{-12}$ |
| `ax.transforms.walsh_hadamard` & `iwalsh_hadamard` | **Comparative + Property (`differential`)** | `scipy.linalg.hadamard(8) @ x` & inverse round-trip (deterministic & Hypothesis) | `test_differential_numpy.py::test_differential_walsh_hadamard_vs_scipy_hadamard`, `test_hypothesis_differential_dft_and_wht` | $10^{-8}$ – $10^{-11}$ |
| `ax.transforms.z_transform` & `iz_transform` | **Comparative + Homomorphism (`differential`)** | `numpy.polyval(f, 1/z)`, $\mathcal{Z}\{f * g\} = \mathcal{Z}\{f\}\mathcal{Z}\{g\}$, & contour recovery | `test_differential_numpy.py::test_differential_z_transform_and_convolution_theorem` | $10^{-9}$ – $10^{-12}$ |
| `ax.transforms.lorentz_boost(v, beta)` | **Metamorphic / Analytical (`differential`)** | Minkowski metric invariance $t^2 - x^2 - y^2 - z^2 = \text{const}$ & $-\beta$ inversion | `test_differential_numpy.py::test_differential_lorentz_boost_minkowski_invariance` | $10^{-11}$ |

---

### 2.5. Graph Calculus, Spectral Theory & Path Semirings (`algebrax.analysis`, `algebrax.semiring`)

| AlgebraX Function / Path Semiring | Verification Category | Reference Oracle / Mathematical Law | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `matrix.power(I + W, n-1, TropicalSemiring)` | **Comparative + Property (`differential`)** | `scipy.sparse.csgraph.floyd_warshall` & `networkx.floyd_warshall_numpy` (all-pairs shortest paths) | `test_differential_graphs.py::test_differential_tropical_shortest_paths_vs_csgraph_and_networkx`, `test_hypothesis_differential_tropical_apsp_and_laplacian` | $10^{-11}$ – $10^{-12}$ |
| `matrix.power(I + A, n-1, BooleanSemiring)` | **Comparative (`differential`)** | `networkx.transitive_closure(G, reflexive=True)` & `csgraph.floyd_warshall(unweighted=True)` | `test_differential_graphs.py::test_differential_boolean_transitive_closure_vs_networkx_and_csgraph` | **Exact (`==`)** |
| `matrix.power(I + W, n-1, ArcticSemiring)` | **Comparative (`differential`)** | `networkx.dag_longest_path_length` & negated-weight `csgraph.floyd_warshall` on DAGs | `test_differential_graphs.py::test_differential_arctic_longest_path_on_dag_vs_networkx` | $10^{-12}$ |
| `matrix.power(I + C, n-1, BottleneckSemiring)` | **Comparative (`differential`)** | `networkx.maximum_spanning_tree` unique path bottleneck capacity | `test_differential_graphs.py::test_differential_bottleneck_widest_path_vs_maximum_spanning_tree` | $10^{-12}$ |
| `ViterbiSemiring` & `ReliabilitySemiring` closure | **Comparative (`differential`)** | Log-domain isomorphism $\exp(-\text{csgraph.floyd\_warshall}(-\ln P))$ | `test_differential_graphs.py::test_differential_viterbi_and_reliability_vs_log_csgraph` | $10^{-11}$ |
| `LogSemiring` DAG partition function | **Comparative (`differential`)** | Resolvent $\ln((I - P)^{-1})$ via `scipy.linalg.inv` | `test_differential_graphs.py::test_differential_log_semiring_dag_partition_function_vs_scipy_inv` | $10^{-11}$ |
| `matrix.laplacian_matrix(W, normalized=None \| 'sym' \| 'rw')` | **Comparative + Property (`differential`)** | `networkx.laplacian_matrix`, `nx.normalized_laplacian_matrix`, `csgraph.laplacian`, & $I - D^{-1}W$ | `test_differential_graphs.py::test_differential_laplacian_matrices_vs_networkx_and_csgraph`, `test_hypothesis_differential_tropical_apsp_and_laplacian` | $10^{-11}$ – $10^{-12}$ |
| `analysis.laplacian_spectrum(W)` | **Comparative + Certificate (`differential`)** | `scipy.linalg.eigh(L)` eigenvalues, $V^T V = I$, & residual $\|L v_i - \lambda_i v_i\|_2$ | `test_differential_graphs.py::test_differential_laplacian_spectrum_vs_scipy_eigh` | $10^{-6}$ |
| `analysis.fiedler_vector` & `algebraic_connectivity` | **Comparative (`differential`)** | `networkx.algebraic_connectivity` & `networkx.fiedler_vector` (up to $\pm 1$ sign) | `test_differential_graphs.py::test_differential_fiedler_vector_and_algebraic_connectivity_vs_networkx` | $10^{-4}$ – $10^{-5}$ |
| `analysis.spectral_bipartition(W)` | **Comparative (`differential`)** | `networkx.cut_size`, `nx.conductance`, `nx.normalized_cut_size` | `test_differential_graphs.py::test_differential_spectral_bipartition_metrics_vs_networkx_cuts` | $10^{-12}$ |
| `analysis.pagerank(W, damping, personalization, dangling)` | **Comparative (`differential`)** | `networkx.pagerank` (standard, dangling sinks, & personalized random walks) | `test_differential_graphs.py::test_differential_pagerank_vs_networkx` | $10^{-6}$ |
| `analysis.eigen_centrality(W)` | **Comparative (`differential`)** | `networkx.eigenvector_centrality_numpy` | `test_differential_graphs.py::test_differential_eigen_centrality_vs_networkx` | $10^{-5}$ |
| `analysis.gradient`, `divergence`, `laplacian` | **Comparative + Adjoint (`differential`)** | `nx.laplacian_matrix(G) @ f`, $\operatorname{div}(\operatorname{grad} f) = -2Lf$, & Green's identity $\langle \nabla f, F \rangle_E = -\langle f, \operatorname{div} F \rangle_V$ | `test_differential_graphs.py::test_differential_gradient_divergence_laplacian_and_greens_identity` | $10^{-11}$ |
| `analysis.laplacian_smoothing` & `gaussian_kernel` | **Comparative (`differential`)** | `np.linalg.matrix_power(I - tau * L, steps) @ f` & $\exp(-D^2 / 2\sigma^2)$ | `test_differential_graphs.py::test_differential_laplacian_smoothing_and_gaussian_kernel_vs_numpy` | $10^{-11}$ – $10^{-12}$ |
| `analysis.forman_ricci_curvature(W)` | **Comparative (`differential`)** | Exact combinatorial curvature on $C_n$ ($\mathcal{F}=0$) and $K_n$ ($\mathcal{F}=6-2n$ unaugmented, $n$ augmented) | `test_differential_graphs.py::test_differential_forman_ricci_curvature_vs_combinatorial_invariants` | $10^{-12}$ |

---

### 2.6. Exact Symbolic Algebra, Lie, Galois, Clifford & Group Theory (`algebrax.lie`, `algebrax.galois`, `algebrax.clifford`, `algebrax.group`)

| AlgebraX Function / Structure | Verification Category | Reference Oracle / Mathematical Law | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `matrix.academic.determinant`, `cofactor`, `adjoint`, `inverse` over `Fraction` | **Comparative + Property (`differential`)** | `sympy.Matrix` (`.det()`, `.cofactor_matrix()`, `.adjugate()`, `.inv()`) over $\mathbb{Q}$ & $A A^{-1} = I$ | `test_differential_sympy.py::test_differential_exact_fraction_matrix_determinant_adjoint_and_inverse_vs_sympy`, `test_hypothesis_exact_fraction_determinant_and_inverse_vs_sympy` | **Exact (`==`, $\epsilon = 0$)** |
| `lie.RootSystem.from_dynkin` ($A_n, B_n, C_n, D_n, G_2, F_4, E_6, E_7, E_8$) | **Comparative (`differential`)** | `sympy.liealgebras.RootSystem` Cartan matrix, $\det C$, $|\Phi^+|$, and symmetrizing factors $d_i A_{ij} = d_j A_{ji}$ | `test_differential_sympy.py::test_differential_root_systems_and_cartan_matrices_vs_sympy` | **Exact (`==`, $\epsilon = 0$)** |
| `lie.LieAlgebra.bch(x, y, order=1..4)` | **Comparative (`differential`)** | `scipy.linalg.expm(X) @ scipy.linalg.expm(Y)` vs. `scipy.linalg.expm(BCH(X, Y))` on $\mathfrak{so}_3, \mathfrak{sl}_2, \mathfrak{su}_2, \mathfrak{se}_3$ | `test_differential_sympy.py::test_differential_lie_bch_series_vs_scipy_expm` | $10^{-6}$ |
| `lie.LieAlgebra.adjoint_matrix`, `killing_form`, `is_semisimple` | **Comparative (`differential`)** | $[\operatorname{ad}_X, \operatorname{ad}_Y] = \operatorname{ad}_{[X, Y]}$, $B(X,Y) = \operatorname{Tr}(\operatorname{ad}_X \operatorname{ad}_Y)$, ad-invariance $B([X,Y],Z) + B(Y,[X,Z]) = 0$, Cartan criterion | `test_differential_sympy.py::test_differential_lie_adjoint_homomorphism_and_killing_form` | $10^{-10}$ – $10^{-11}$ |
| `galois.GaloisFieldSemiring` ($GF(2^8), GF(3^3)$) & `gf_matrix_mul` | **Comparative (`differential`)** | `sympy.Poly` over `sympy.GF(p)` mod $P(x)$, Fermat's Little Theorem $a^{p^m-1} = 1$, Frobenius $(a+b)^p = a^p + b^p$ | `test_differential_sympy.py::test_differential_galois_field_arithmetic_and_fermat_little_theorem_vs_sympy`, `test_differential_gf_matrix_mul_vs_sympy` | **Exact (`==`, $\epsilon = 0$)** |
| `clifford.rotor_rotation(v, bivector, angle)` | **Comparative (`differential`)** | `scipy.spatial.transform.Rotation.from_rotvec` across 3D coordinate planes | `test_differential_sympy.py::test_differential_clifford_rotor_rotation_vs_scipy_rotation` | $10^{-11}$ |
| `CliffordSemiring`, `GeneralizedCliffordSemiring`, `QuantumCliffordSemiring`, `clifford_lie_algebra` | **Comparative (`differential`)** | Spacetime $\mathcal{C}\ell(1,3,0)$ anticommutation, $\mathfrak{spin}(3) \cong \mathfrak{so}(3)$, $\omega$-braiding, & $q$-deformed braiding | `test_differential_sympy.py::test_differential_clifford_algebras_and_bivector_lie_isomorphism` | $10^{-12}$ / **Exact (`==`)** |
| `group.compose`, `invert`, `signature` | **Comparative + Property (`differential`)** | `sympy.combinatorics.Permutation` composition, inverse, & parity homomorphism $\operatorname{sgn}(pq) = \operatorname{sgn}(p)\operatorname{sgn}(q)$ | `test_differential_sympy.py::test_hypothesis_differential_permutation_group_vs_sympy` | **Exact (`==`, $\epsilon = 0$)** |
| `PolynomialSemiring(StandardSemiring(Fraction))` | **Comparative (`differential`)** | `sympy.Poly(..., domain='QQ')` addition, Cauchy product, and powers | `test_differential_sympy.py::test_differential_polynomial_semiring_over_fraction_vs_sympy_poly` | **Exact (`==`, $\epsilon = 0$)** |
| `DualNumberSemiring`, `BinomialConvolutionSemiring`, `MultivariateBinomialConvolutionSemiring` | **Comparative (`differential`)** | `sympy.diff(f, x, k)` (up to 4th derivative) & `sympy.diff(g, (x, a1), (y, a2))` 2D partial derivatives | `test_differential_sympy.py::test_differential_autodiff_semirings_vs_sympy_derivatives` | $10^{-11}$ |

---

### 2.7. Semiring Catalog (`algebrax.semiring`, `algebrax.verification`)

| AlgebraX Semiring / Function | Verification Category | Reference Oracle / Axioms Verified | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `StandardSemiring(Fraction)` | **Axiomatic + Exact $\mathbb{Q}$ (`axiomatic`)** | All 9 ring axioms over infinite-precision `fractions.Fraction` via Hypothesis | `test_axiomatic_properties.py::test_standard_semiring_exact_rational_axioms` | **Exact (`==`, $\epsilon = 0$)** |
| `TropicalSemiring` $(\min, +, \infty, 0)$ | **Axiomatic (`axiomatic`)** | Commutativity, associativity, identity, $+\infty$ annihilation, distributivity via Hypothesis | `test_axiomatic_properties.py::test_tropical_semiring_axiomatic_properties` | $10^{-9}$ |
| `ArcticSemiring` $(\max, +, -\infty, 0)$ | **Axiomatic (`axiomatic`)** | Commutativity, associativity, identity, $-\infty$ annihilation, distributivity via Hypothesis | `test_axiomatic_properties.py::test_arctic_semiring_axiomatic_properties` | $10^{-9}$ |
| `BooleanSemiring` $(\lor, \land, \text{False}, \text{True})$ | **Axiomatic (`axiomatic`)** | Exhaustive Boolean algebra / distributive lattice laws via Hypothesis | `test_axiomatic_properties.py::test_boolean_semiring_axiomatic_properties` | **Exact (`==`)** |
| `ViterbiSemiring` $(\max, \times, 0, 1)$ | **Axiomatic (`axiomatic`)** | Probabilistic path monoid axioms over $[0, 1]$ via Hypothesis | `test_axiomatic_properties.py::test_viterbi_semiring_axiomatic_properties` | $10^{-6}$ |
| All 34 Catalog Semirings (`Semiring.catalog()`) | **Catalog Law Audit** | 9 semiring axioms verified across all 34 registered semirings | `tests/algebrax/test_verification.py::test_all_catalog_semirings_satisfy_laws` | $10^{-7}$ |

---

### 2.8. Topology, Exterior Calculus & Lie Algebras (`algebrax.homology`, `algebrax.lie`)

| AlgebraX Structure / Function | Verification Category | Reference Oracle / Mathematical Theorem Verified | Test File & Function | Precision / Tolerance |
|:---|:---|:---|:---|:---|
| `SimplicialComplex` & `SparseChainComplex` | **Metamorphic (`metamorphic`)** | Fundamental topological chain nilpotency $\partial_{k-1} \circ \partial_k = \mathbf{0}$ | `test_metamorphic_invariants.py::test_metamorphic_simplicial_boundary_nilpotency` | $10^{-12}$ |
| `Cochain` discrete $k$-forms | **Metamorphic (`metamorphic`)** | Alternating orientation antisymmetry $\omega(\pi(\sigma)) = \operatorname{sgn}(\pi)\omega(\sigma)$ & degenerate simplex annihilation $\omega(u, u) = 0$ | `test_metamorphic_invariants.py::test_metamorphic_cochain_orientation_antisymmetry` | **Exact (`==`)** |
| `helmholtz_hodge_decomposition` | **Proof-Carrying Certificate (`certificates`)** | $O(|E|)$ witness check: $\omega = \omega_{\text{exact}} + \omega_{\text{coexact}} + \omega_{\text{harmonic}}$, mutual $L^2$ orthogonality $\langle \cdot, \cdot \rangle = 0$, $d_1 \omega_{\text{exact}} = 0$, $\partial_1 \omega_{\text{coexact}} = 0$ | `test_certificates.py::test_helmholtz_hodge_decomposition_certificate` | $10^{-6}$ |
| `LieAlgebra` ($\mathfrak{so}_3, \mathfrak{sl}_2, \mathfrak{so}_4, \mathfrak{g}_2$) | **Schwartz–Zippel PIT (`pit`)** | Jacobi identity $[x, [y, z]] + [y, [z, x]] + [z, [x, y]] = 0$ & antisymmetry $[x, y] + [y, x] = 0$ over random integer coordinates ($|S| = 2 \times 10^4, k=4$) | `test_pit_symbolic.py::test_pit_lie_algebra_jacobi_identity`, `test_pit_lie_bracket_antisymmetry` | False-positive prob $\le 10^{-16}$ |

---

## 3. Running the Verification Suite

You can run the entire verification suite or filter by verification methodology using `pytest` markers:

```bash
# Run all verification tests (44 tests across all layers)
uv run pytest tests/verifications/ tests/algebrax/test_verification.py -v

# Run only comparative / differential tests against NumPy & SciPy
uv run pytest tests/verifications/ -m differential -v

# Run only Hypothesis axiomatic property-based tests
uv run pytest tests/verifications/ -m axiomatic -v

# Run only metamorphic invariant tests
uv run pytest tests/verifications/ -m metamorphic -v

# Run only Schwartz-Zippel randomized polynomial identity tests (PIT)
uv run pytest tests/verifications/ -m pit -v

# Run only proof-carrying solver certificate checks
uv run pytest tests/verifications/ -m certificates -v
```
