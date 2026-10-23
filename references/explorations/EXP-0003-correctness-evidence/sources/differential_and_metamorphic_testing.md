# Differential and Metamorphic Testing Methodologies

## Overview

Differential testing and metamorphic testing provide dual layers of correctness evidence by leveraging external reference standard libraries and intrinsic mathematical invariants.

---

## 1. Differential Testing Against Reference Python Math Libraries

Differential testing compares the output of `algebrax` sparse dictionary primitives against widely trusted, canonical mathematical software engines. When both `algebrax` and a reference library produce identical outputs across thousands of randomly generated inputs, high correctness confidence is established.

### Target Reference Libraries & Mappings Across AlgebraX Domains

| AlgebraX Domain | Reference External Library | Equivalence Mapping & Conversion |
|:----------------|:---------------------------|:---------------------------------|
| `algebrax.matrix` | **NumPy** (`numpy.ndarray`), **SciPy Sparse** (`scipy.sparse.csr_matrix`) | Dense / CSR matrix dot product, transpose, trace, power, determinant. |
| `algebrax.transforms` | **NumPy FFT** (`numpy.fft`), **SciPy Signal** | Discrete Fourier Transform (DFT/IDFT), Walsh-Hadamard, Convolution, Hilbert transform. |
| `algebrax.analysis` | **NetworkX** (`networkx.Graph`), **SciPy Graph** | Graph Laplacian, Forman-Ricci curvature, Fiedler vector, Eigen-centrality, Shortest Paths. |
| `algebrax.homology` | **GUDHI**, **Dionysus 2**, **SciPy Spatial** | Simplicial complexes, Betti numbers $b_k$, boundary operators $\partial_k$. |
| `algebrax.clifford` | **clifford** (PyDy), **galgebra** (SymPy) | Geometric product, rotor rotations, multivector reverse/grade projection. |
| `algebrax.galois` | **galois** (Python package), **SageMath** | Finite field matrix multiplication over GF($p^m$). |
| `algebrax.probability` | **SciPy Stats**, **scikit-learn** | Shannon entropy, KL-divergence, Mutual information, Wasserstein distance. |
| `algebrax.tensor` | **PyTorch** (`torch.einsum`), **NumPy** (`np.einsum`) | Sparse tensor einsum contraction, outer product, tensordot. |

---

## 2. Metamorphic Testing Methodologies

In many complex mathematical domains, an external oracle or canonical reference library may not exist (e.g., custom semiring matrix multiplication like `ProvenanceSemiring` or `KnotSemiring`). **Metamorphic Testing (MT)** solves the "oracle problem" by verifying **Metamorphic Relations (MRs)**—mathematical necessary conditions that link inputs and outputs under transformation.

### Canonical Metamorphic Relations for AlgebraX

1. **Transpose Dual Relation**:
   $$\text{dot}(A, B)^T = \text{dot}(B^T, A^T) \quad \text{(for commutative semirings)}$$

2. **Linearity / Homogeneity under Scalar Multiplication**:
   $$\text{dot}(\alpha \otimes A, B) = \alpha \otimes \text{dot}(A, B)$$

3. **Permutation Conjugacy (Graph Automorphisms)**:
   For any permutation matrix $P$:
   $$L(P A P^T) = P L(A) P^T \quad \text{where } L(A) \text{ is the Graph Laplacian}$$

4. **DFT Shift Theorem**:
   A cyclic shift in time domain manifests as a linear phase shift in frequency domain:
   $$\mathcal{F}(\text{shift}_k(x)) = \mathcal{F}(x) \cdot e^{-i 2\pi k / N}$$

5. **Simplicial Boundary Nilpotency**:
   The boundary of a boundary is always zero:
   $$\partial_k \circ \partial_{k+1} = 0$$

6. **Legendre-Fenchel Involution**:
   For convex functions, the double conjugate yields the original function:
   $$f^{**} = f$$

---

## 3. Comparative Verification Workflow

```
                        Random Mathematical Input X
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
     Transform Input: T(X)                       Standard Input: X
               │                                         │
               ▼                                         ▼
      AlgebraX Algorithm                        AlgebraX Algorithm
      Y_transformed = f(T(X))                     Y_standard = f(X)
               │                                         │
               └────────────────────┬────────────────────┘
                                    ▼
                         Metamorphic Relation Check
                         Verify: Y_transformed == g(Y_standard)
```
