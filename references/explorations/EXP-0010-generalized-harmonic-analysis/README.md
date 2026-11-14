# EXP-0010: Generalized Harmonic Analysis — Non-Abelian Peter–Weyl, Algebraic Signal Models, Spectral Wavelets & Exact NTT

| Field           | Value                                                                                                                                                                                             |
|:----------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0010                                                                                                                                                                                              |
| **Title**       | Generalized Harmonic Analysis — Non-Abelian Peter–Weyl, Algebraic Signal Models, Spectral Wavelets & Exact NTT                                                                                    |
| **Author**      | Eran Rivlis & Antigravity (Principal Architect & Grand Council)                                                                                                                                   |
| **Status**      | Concluded                                                                                                                                                                                         |
| **Type**        | Architectural & Research Exploration                                                                                                                                                              |
| **Created**     | 2026-11-14                                                                                                                                                                                        |
| **Updated**     | 2026-11-14                                                                                                                                                                                        |
| **Related EPs** | [EP-0001](../../../docs/proposals/EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md), [EP-0003](../../../docs/proposals/EP-0003-axiomatic-verification-and-property-based-testing.md), [EP-0004](../../../docs/proposals/EP-0004-unboxed-storage-and-sparse-carrier-invariance.md), [EP-0160](../../../docs/proposals/EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md), [EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md), [EP-0210](../../../docs/proposals/EP-0210-group-representations-character-tables-schurs-lemma.md), [EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md), [EP-0221](../../../docs/proposals/EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) |

---

## 1. Abstract & Context

### 1.1 Context in AlgebraX
[`src/algebrax/transforms.py`](../../../src/algebrax/transforms.py) was designed in AlgebraX's initial phase and currently supports only **1D Abelian scalar transforms**:
1. **`dft` / `idft`**: Fourier transform on the cyclic group $\mathbb{Z}/N\mathbb{Z}$.
2. **`walsh_hadamard` / `iwalsh_hadamard`**: Fourier transform on the Boolean hypercube $(\mathbb{Z}/2\mathbb{Z})^n$.
3. **`gelfand_transform`**: Evaluates a sparse signal `dict[K, V]` against scalar characters $\chi: G \to \mathbb{C}$.
4. **`z_transform` & `legendre_fenchel`**: Unilateral power series evaluation and convex tropical conjugation.

Meanwhile, Phases 4–9 introduced the mathematical foundations required for a far deeper theory:
- **Phase 4 (`topology`, `analysis`)**: Graph Laplacians $L_0$, Simplicial Hodge Laplacians $L_k = \partial_{k+1}\partial_{k+1}^* + \partial_k^*\partial_k$ ([EP-0160](../../../docs/proposals/EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md)), and Cellular Sheaf Laplacians $L_{\mathcal{F}}$ ([EP-0161](../../../docs/proposals/EP-0161-cellular-sheaves-and-network-laplacians.md)).
- **Phase 6 (`algebra`, `galois`, `lattice`)**: `ModularField(p)`, `GaloisFieldSemiring`, `MonoidAlgebra`, and finite lattices/posets (`BoundedLattice`, `DistributiveLattice`).
- **Phase 7 (`algebra._quotient`, `_padic`)**: `QuotientRing(R, I)` ([EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md)) and $p$-adic / Hecke algebras ([EP-0209](../../../docs/proposals/EP-0209-langlands-root-duality-hecke-padic-valuations.md)).
- **Phase 8 (`representation`)**: Irreducible matrix representations $\rho_\lambda: G \to \operatorname{GL}(V_\lambda)$ ([EP-0210](../../../docs/proposals/EP-0210-group-representations-character-tables-schurs-lemma.md)).
- **Phase 9 (`variety`)**: Polynomial ideals (`GroebnerIdeal`) and Stickelberger shift companion matrices $M_{x_i}$ ([EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md), [EP-0221](../../../docs/proposals/EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md)).

### 1.2 The Core Question
> *Can we unify Non-Abelian Group Harmonic Analysis (Peter–Weyl), Algebraic Signal Processing (Püschel–Moura polynomial quotient shift models), Graph/Hodge/Sheaf Spectral Wavelets, Exact Finite-Field Number-Theoretic Transforms (NTT), and Poset Möbius Harmonic Analysis into a cohesive mathematical architecture that bridges Phases 4, 6, 7, 8, and 9?*

---

## 2. Exploration & Options Analysis

### 2.1 Literature & Ecosystem Survey
We surveyed five foundational frameworks (archived in [`papers/`](./papers/) and indexed in [`sources/BIBLIOGRAPHY.md`](./sources/BIBLIOGRAPHY.md)):

1. **Non-Abelian Group Fourier Transform & Peter–Weyl Duality ([KONDOR-2007], [KONDOR-2018], [DIACONIS-1988])**:
   For a non-Abelian group $G$ (e.g., $S_n$, $D_n$, $A_n$, $\operatorname{SL}_2(\mathbb{F}_p)$), 1D characters $\chi_\lambda(g) = \operatorname{Tr}(\rho_\lambda(g))$ are class functions ($\chi(hgh^{-1}) = \chi(g)$) and **cannot invert general signals on $G$**. The true Fourier transform evaluates $f \in \mathbb{C}[G]$ at each complete unitary irreducible matrix representation $\rho_\lambda: G \to \operatorname{GL}_{d_\lambda}(\mathbb{C})$:
   $$\hat{f}(\rho_\lambda) = \sum_{g \in G} f(g)\, \rho_\lambda(g) \in M_{d_\lambda}(\mathbb{C}), \qquad f(g) = \frac{1}{|G|} \sum_{\lambda \in \widehat{G}} d_\lambda \operatorname{Tr}\!\left(\hat{f}(\rho_\lambda)\, \rho_\lambda(g^{-1})\right)$$
   This establishes the **Peter–Weyl algebra isomorphism** $\mathbb{C}[G] \cong \bigoplus_{\lambda \in \widehat{G}} M_{d_\lambda}(\mathbb{C})$, turning non-commutative group convolution $f * h$ into block-diagonal matrix multiplication $\hat{f}(\rho_\lambda) \cdot \hat{h}(\rho_\lambda)$.

2. **Püschel–Moura Algebraic Signal Processing Theory ([PUSCHEL-2006])**:
   Every linear shift-invariant signal model is a triple $(\mathcal{A}, \mathcal{M}, \Phi)$ where the filter algebra $\mathcal{A} = k[x_1, \dots, x_n]/I$ is a **polynomial quotient ring** (`QuotientRing` from `EP-0201` / `EP-0220`), the generalized shift operator is the **Stickelberger companion matrix $M_{x_i}$** (`EP-0221`), and the generalized Fourier transform is the eigenbasis diagonalizing $M_{x_i}$ over the variety $V(I)$:
   - $I = \langle x^N - 1 \rangle \implies$ Circular Shift $\implies$ **DFT** (variety = $N$-th roots of unity).
   - $I = \langle T_N(x) \rangle$ (Chebyshev polynomial) $\implies$ Symmetric Boundary Shift $\implies$ **DCT / DST** (variety = Chebyshev nodes $\cos\frac{(2k+1)\pi}{2N}$).
   - Multivariate $I \triangleleft k[x_1, \dots, x_n] \implies$ **Algebraic Variety Fourier Transform** diagonalizing commuting Stickelberger operators $M_{x_1}, \dots, M_{x_n}$.

3. **Exact Finite-Field Number-Theoretic Transforms (NTT)**:
   Replacing $\mathbb{C}$ with `ModularField(p)` where $N \mid (p - 1)$ and $e^{-2\pi i/N}$ with a primitive $N$-th root of unity $\omega \in \mathbb{F}_p^\times$ yields an exact ring isomorphism $\mathbb{F}_p[x]/\langle x^N - 1 \rangle \cong \mathbb{F}_p^N$ with **zero IEEE-754 rounding drift**.

4. **Graph, Hodge & Sheaf Spectral Wavelets via Fast Chebyshev Recurrence ([HAMMOND-2009])**:
   Given any positive semidefinite geometric Laplacian $\mathcal{L}$ (Graph $L_0$, Hodge $L_k$, or Sheaf $L_{\mathcal{F}}$) with spectrum in $[0, \lambda_{\max}]$, rescaling $\tilde{\mathcal{L}} = \frac{2}{\lambda_{\max}}\mathcal{L} - I \in [-1, 1]$ allows evaluating any spectral filter or wavelet $g(\mathcal{L})f \approx \frac{1}{2}c_0 f + \sum_{k=1}^K c_k T_k(\tilde{\mathcal{L}})f$ via the 3-term Chebyshev recurrence $T_k(\tilde{\mathcal{L}})f = 2\tilde{\mathcal{L}}T_{k-1}(\tilde{\mathcal{L}})f - T_{k-2}(\tilde{\mathcal{L}})f$ using **only $K$ sparse matrix-vector multiplications** (avoiding $O(N^3)$ diagonalization).

5. **Poset & Lattice Harmonic Analysis ([ROTA-1964])**:
   On a finite poset/lattice $(P, \le)$, the Incidence Algebra $I(P, R)$ is governed by the Zeta transform $(Zf)(x) = \sum_{y \le x} f(y)$ and its inverse, the Möbius transform $(\mu f)(x) = \sum_{y \le x} \mu(y, x)f(y)$. On distributive/Boolean lattices, the **Fast Zeta / Möbius Transform (FZT / FMT)** diagonalizes join-convolution $(f *_P g)(x) = \sum_{y \vee z = x} f(y)g(z)$ in $O(n 2^n)$ instead of $O(4^n)$.

### 2.2 Comparative Trade-Offs of Implementation Options

| Option | Core Mechanism | Strengths | Weaknesses / Traps | Council Fit |
|:-------|:---------------|:----------|:-------------------|:------------|
| **Option 1: Keep `transforms.py` as 1D Scalar DSP Utilities** | Leave `dft`, `walsh_hadamard`, and 1D `gelfand_transform` as-is | Zero new code | Fails on non-Abelian groups (`gelfand_transform` collides); float64 `dft` corrupts large integer/modular convolutions; disconnected from Phases 4, 8, and 9 | **Rejected** (Violates Noether, Popper & Russell) |
| **Option 2: Heavy External FFT/PyG Dependency Wrapper** | Wrap `scipy.fft` and `pygsp` | Fast C routines for standard 1D grids | Cannot do exact `ModularField(p)` NTT, cannot do Peter–Weyl matrix FT on `GroupRepresentation`, cannot do Püschel–Moura `QuotientRing` transforms | **Rejected** (Violates Zero-Dependency Mandate) |
| **Option 3: Unified Algebraic, Non-Abelian & Geometric Harmonic Analysis** | Peter–Weyl Matrix FT (`GroupFourierTransform`), Püschel–Moura `AlgebraicSignalModel` on `QuotientRing`/`AffineVariety`, Exact `ntt`/`intt` on `ModularField(p)`, Chebyshev Laplacian wavelets on `L_0`/`L_k`/`L_F`, and Poset `zeta`/`mobius` transforms | 100% pure-Python exact & sparse-carrier native; unifies Phases 4, 6, 7, 8, and 9; falsifiable Parseval/Plancherel/inversion laws across every domain | Very large dense 1D arrays should still use `numpy.fft` as an Escape Hatch | **Accepted** |

### 2.3 Empirical Findings (`sources/prototype_harmonic_analysis.py`)
We authored and executed [`sources/prototype_harmonic_analysis.py`](./sources/prototype_harmonic_analysis.py) (full output archived in [`raw/prototype_benchmark_output.txt`](./raw/prototype_benchmark_output.txt)) on Python 3.14.7 across all 5 harmonic domains:

#### Experiment 1: Non-Abelian Peter–Weyl Fourier Transform vs. 1D `gelfand_transform` Collapse
* **Empirical Falsification of 1D Scalar Characters on $S_3$**:
  Two distinct signals $f_1 \ne f_2$ on $S_3$ supported on different transpositions $(12)$ vs. $(23)$ yielded **identical scalar spectra** `{'triv': 2.5, 'sign': -1.5, 'std': 2.5}` under `algebrax.transforms.gelfand_transform` because traces $\chi_\lambda(g)$ are constant on conjugacy classes.
* **Peter–Weyl Matrix Resolution**:
  Evaluating $\hat{f}(\rho_\lambda) \in M_{d_\lambda}(\mathbb{C})$ across the 3 unitary irreps of $S_3$ ($1 \oplus 1 \oplus 2$):
  * Separated $f_1$ and $f_2$ immediately on the $2 \times 2$ standard irrep.
  * **Peter–Weyl Inversion Error**: `0.00e+00`.
  * **Non-Abelian Convolution Theorem Error** ($\widehat{f_1 * f_2}(\rho_\lambda) == \hat{f}_1(\rho_\lambda)\hat{f}_2(\rho_\lambda)$ vs. `MonoidAlgebra.mul`): `0.00e+00`.
  * **Plancherel Energy Conservation**: Spatial energy `5.250000` == Spectral energy `5.250000` (`diff = 0.00e+00`).
  * **Diaconis Random Transposition Walk ($k=8$ steps)**: Spectral matrix powers $\hat{P}(\rho_\lambda)^8$ computed total variation distance to uniform `1.95e-03`.

#### Experiment 2: Püschel–Moura Algebraic Signal Processing (`QuotientRing` Shift Models)
* **Architectural Discovery**: `PolynomialTruncationIdeal` in `src/algebrax/algebra/_ideals.py` only truncates at $x^d$ (`max_degree: int`). Introducing a general `PolynomialModulusIdeal` $\langle P(x) \rangle$ (univariate case of `GroebnerIdeal`) turns `QuotientRing(PolynomialAlgebra, ideal)` into a universal Püschel–Moura signal model:
  * **Model A ($\mathbb{C}[x]/\langle x^4 - 1 \rangle \leftrightarrow \text{DFT}$)**: `QuotientRing.mul` matched `idft(dft(a) * dft(b))` to **`1.27e-15`**.
  * **Model B ($\mathbb{R}[x]/\langle T_4(x) \rangle \leftrightarrow \text{DCT}$)**: The Stickelberger companion matrix $M_x$ on $\mathbb{R}[x]/\langle x^4 - x^2 + \frac{1}{8} \rangle$ produced eigenvalues `[-0.92388, -0.382683, 0.382683, 0.92388]`, matching the exact Chebyshev DCT nodes $\cos\frac{(2k+1)\pi}{8}$ to **`9.99e-16`**.

#### Experiment 3: Exact Finite-Field NTT (`ModularField(p)`) vs. Float64 DFT Overflow
* Convolving 9-digit integer polynomials of length $N = 8$ modulo the canonical NTT prime $p = 998244353 = 119 \cdot 2^{23} + 1$ (primitive 8-th root $\omega = 372528824$):
  * **Float64 `dft`/`idft`**: Intermediate sums ($\sim 3 \times 10^{18}$) exceeded IEEE-754's 53-bit exact integer limit ($2^{53} \approx 9 \times 10^{15}$), corrupting **7 out of 7 (100%)** modular coefficients!
  * **Exact `ntt`/`intt` over `ModularField(998244353)`**: **0 out of 7 mismatches (100% bit-exact)** using pure integer modular arithmetic.

#### Experiment 4: Graph & Hodge Spectral Wavelets via Fast Chebyshev Recurrence
* **Cycle Graph $C_{64}$ Mexican-Hat Wavelet**: Order-$K=14$ Chebyshev polynomial recurrence matched full `numpy.linalg.eigh` spectral filtering to **`1.80e-09` relative error** while running **60x faster** (`0.24 ms` vs. `14.42 ms`).
* **Simplicial Hodge 1-Laplacian $L_1 = B_1^\top B_1 + B_2 B_2^\top$**: Extracted the topological harmonic 1-cochain ($\ker L_1$, $b_1 = 1$) with residual `||L_1 f_harm|| = 2.78e-16`.

#### Experiment 5: Lattice Harmonic Analysis (Rota Fast Zeta / Möbius Transform)
* On the Boolean subset lattice $2^{[9]}$ (512 elements):
  * **Rota Möbius Inversion Error** ($\|f - \operatorname{FMT}(\operatorname{FZT}(f))\|_\infty$): `0.00e+00`.
  * **Join-Convolution Error** ($\|f *_{\vee} g - \operatorname{FMT}(\operatorname{FZT}(f) \odot \operatorname{FZT}(g))\|_\infty$): `0.00e+00`.
  * **Speedup**: Fast Möbius convolution ran in **`1.38 ms`** vs. naive join convolution **`19.82 ms`** (**14.3x speedup** at $n=9$, scaling as $O(n 2^n)$ vs. $O(4^n)$).

---

## 3. Architectural Synthesis & Constraint Alignment

1. **Noether (Conservation of Energy & Convolution–Multiplication Duality)**:
   Every harmonic transform in AlgebraX is an **algebra isomorphism** from a convolution algebra to a pointwise/block-matrix multiplication algebra, accompanied by an invariant Plancherel/Parseval conservation law:

   | Domain / Carrier | Convolution Algebra | Spectral Target | Transform |
   |:-----------------|:--------------------|:----------------|:----------|
   | Cyclic Group $\mathbb{Z}/N\mathbb{Z}$ | $\mathbb{C}[\mathbb{Z}/N\mathbb{Z}]$ | $\mathbb{C}^N$ (pointwise) | `dft` / `idft` |
   | Finite Group $G$ (`EP-0210`) | $\mathbb{C}[G]$ (`MonoidAlgebra`) | $\bigoplus_\lambda M_{d_\lambda}(\mathbb{C})$ (block matrix mul) | `group_ft` / `igroup_ft` (Peter–Weyl) |
   | Polynomial Model $k[X]/I$ (`EP-0221`) | `QuotientRing(k[X], I)` | $k^{V(I)}$ (Stickelberger eigenbasis) | `algebraic_signal_transform` (DCT/DST/Variety FT) |
   | Finite Field $\mathbb{F}_p[x]/\langle x^N - 1 \rangle$ | Modular cyclic convolution | $\mathbb{F}_p^N$ (exact modular product) | `ntt` / `intt` (`ModularField(p)`) |
   | Graph / Simplicial / Sheaf Laplacian | Polynomials in $\mathcal{L}$ ($k[\mathcal{L}]$) | Eigenmodes / Chebyshev basis $T_k(\tilde{\mathcal{L}})$ | `gft`, `hodge_ft`, `chebyshev_spectral_filter` |
   | Poset / Lattice $(P, \le)$ (`lattice`) | Join/Meet Convolution $(P, \vee)$ | Pointwise Lattice Product | `poset_zeta_transform` / `poset_mobius_transform` |

2. **Popper (Falsifiable Spectral Oracles — `EP-0003`)**:
   - Every transform pair $(\mathcal{F}, \mathcal{F}^{-1})$ is governed by three universal falsifiable laws in `algebrax.verification`:
     1. **Exact Inversion**: $\mathcal{F}^{-1}(\mathcal{F}(f)) == f$.
     2. **Convolution Homomorphism**: $\mathcal{F}(f * g) == \mathcal{F}(f) \odot \mathcal{F}(g)$.
     3. **Plancherel / Parseval Isometry**: $\|f\|_2^2 == \|\mathcal{F}(f)\|_{\text{Plancherel}}^2$.
3. **Shannon (Unboxed Sparse Signals & Matrix-Free Chebyshev Filtering — `EP-0004`)**:
   - Signals remain unboxed sparse dictionaries `dict[K, V]`.
   - Chebyshev spectral wavelets operate directly via sparse matrix-vector multiplication (`algebrax.matrix.multiply`) without materializing dense $N \times N$ eigenvector matrices.
4. **Feynman (The Freshman Test)**:
   - *"What is a Fourier transform really doing? You have an operation—like shifting a signal in time, rotating a molecule by a group $G$, diffusing heat across a graph, or taking unions in a lattice—that mixes values together. The Fourier transform is simply changing coordinates to the special basis where that mixing operation becomes plain multiplication!"*

---

## 4. The Verdict / Actionable Design

**Verdict: Approved for Phase 10 Standards-Track Proposals (`EP-0230`–`EP-0232`).**

Should we proceed to author Phase 10 EPs from `EXP-0010`, the Council recommends a clean 3-EP decomposition starting at the decade boundary **`EP-0230`**:

1. **`EP-0230`: Non-Abelian Group Fourier Transforms, Peter–Weyl Duality & Equivariant Convolutions**:
   - Matrix-valued `group_fourier_transform` & `inverse_group_fourier_transform` over Phase 8 `GroupRepresentation`s (`EP-0210`).
   - Plancherel inner products, Diaconis random-walk spectral mixing bounds, and group-equivariant steerable convolutions.
2. **`EP-0231`: Algebraic Signal Processing, Polynomial Shift Models & Exact Finite-Field NTT**:
   - General `PolynomialModulusIdeal` $\langle P(x) \rangle$ in `algebrax.algebra._ideals`.
   - Püschel–Moura `AlgebraicSignalModel` bridging `QuotientRing` / `AffineVariety` Stickelberger shift matrices (`EP-0221`) with DCT/DST/polynomial transforms.
   - Exact `ntt` and `intt` (Cooley–Tukey radix-2 & arbitrary radix) over `ModularField(p)` and `GaloisFieldSemiring`, plus Fast Poset Zeta/Möbius transforms (`fast_zeta_transform`, `fast_mobius_transform`, `poset_mobius_inversion`).
3. **`EP-0232`: Geometric, Simplicial Hodge & Cellular Sheaf Spectral Wavelets**:
   - Graph Fourier Transform (`gft` / `igft`), Simplicial Hodge Fourier Transform (`hodge_ft` separating curl-free, divergence-free, and harmonic modes), and Sheaf Fourier Transform.
   - Matrix-free `chebyshev_spectral_filter` and Hammond–Vandergheynst–Gribonval `spectral_graph_wavelets` over sparse Laplacians.

---

## 5. Related Enhancement Proposals & Artifacts

### Connected EPs
* **Prerequisites**: [EP-0160](../../../docs/proposals/EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md) (Hodge Laplacians), [EP-0161](../../../docs/proposals/EP-0161-cellular-sheaves-and-network-laplacians.md) (Sheaf Laplacians), [EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md) (`QuotientRing`), [EP-0210](../../../docs/proposals/EP-0210-group-representations-character-tables-schurs-lemma.md) (`GroupRepresentation`), [EP-0221](../../../docs/proposals/EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) (`AffineVariety` & Stickelberger companion matrices).
* **Candidate Phase 10 EPs**: `EP-0230` (Non-Abelian Peter–Weyl FT), `EP-0231` (Algebraic Signal Processing, Exact NTT & Poset Möbius FT), `EP-0232` (Graph, Hodge & Sheaf Spectral Wavelets).

### Bundled Compendium Artifacts
* [`sources/prototype_harmonic_analysis.py`](./sources/prototype_harmonic_analysis.py) — Executable pure-Python prototype & benchmark suite covering all 5 harmonic experiments.
* [`raw/prototype_benchmark_output.txt`](./raw/prototype_benchmark_output.txt) — Exact captured stdout from executing the prototype on Python 3.14.7.
* [`sources/BIBLIOGRAPHY.md`](./sources/BIBLIOGRAPHY.md) — Annotated bibliography of primary papers and monographs.
* [`papers/`](./papers/) — Archived open-access arXiv PDFs ([PUSCHEL-2006], [KONDOR-2007], [KONDOR-2018], [HAMMOND-2009]).
