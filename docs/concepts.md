---
title: Concepts
description: Theoretical overview of the algebraic structures used in `algebrax`, including monoids, groups, semirings, and their applications in graph analysis, logic, and probability.
icon: lucide/lightbulb
---

# Concepts

This document provides a theoretical overview of the algebraic structures used in `algebrax`. Understanding these
concepts helps clarify why certain operations are grouped together and how they generalize across different domains
(graphs, logic, probability).

## Algebraic Structures

Hierarchy of Structures (Ordered by Complexity)

### 1. Monoid $(M, \cdot)$

A set $M$ with a single binary operation $\cdot$ that satisfies:

* **Closure**: If $a, b \in M$, then $a \cdot b \in M$.
* **Associativity**: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.
* **Identity**: There exists $e \in M$ such that $a \cdot e = e \cdot a = a$.

**Example**:

* Natural numbers under addition $(\mathbb{N}, +)$. Identity is 0.
* Strings under concatenation. Identity is `""`.

### 2. Group $(G, \cdot)$

A Monoid where every element has an **Inverse**.

* **Inverse**: For every $a \in G$, there exists $a^{-1}$ such that $a \cdot a^{-1} = e$.

**Example in Library**:

* **Permutations** (`algebra.group`): The set of bijective mappings forms a group under composition.
    * Operation: `compose(f, g)`
    * Inverse: `invert(f)`
    * Identity: `{k: k}`

### 3. Abelian Group

A Group where the operation is also **Commutative**:

* $a \cdot b = b \cdot a$.

**Example**: Integers under addition $(\mathbb{Z}, +)$.

### 4. Semiring $(S, \oplus, \otimes)$

A set $S$ with two operations, Addition ($\oplus$) and Multiplication ($\otimes$), satisfying:

* $(S, \oplus)$ is a Commutative Monoid (Identity $\mathbf{0}$).
* $(S, \otimes)$ is a Monoid (Identity $\mathbf{1}$).
* **Distributivity**: Multiplication distributes over Addition.
* **Annihilation**: $a \otimes \mathbf{0} = \mathbf{0}$.

**Crucially**: Semirings do **not** require additive inverses (subtraction) or multiplicative inverses (division).

**Examples in Library** (`algebrax.semiring`):

Semirings are organized into categorical sub-modules under `algebrax.semiring`:
* **`arithmetic`**: `StandardSemiring` $(\mathbb{R}, +, \times)$. Standard Matrix Multiplication.
* **`optimization`**: `TropicalSemiring` $(\mathbb{R} \cup \{\infty\}, \min, +)$, `ArcticSemiring`, `ViterbiSemiring`, `ReliabilitySemiring`, `BottleneckSemiring`, `MinTimesSemiring`. Shortest path and capacity algorithms.
* **`logic`**: `BooleanSemiring` $(\{T, F\}, \lor, \land)$, `LukasiewiczSemiring`, `DigitalSemiring`. Reachability, fuzzy logic, and post-quantum digital operations.
* **`statistical`**: `LogSemiring`, `ExpectationSemiring`, `VarianceSemiring`, `DualNumberSemiring`. Probabilistic inference, moments, automatic differentiation.
* **`structures`**: `StringSemiring`, `KCollapsedSemiring`. Formal path languages, bounded counting.
* **`algebraic`**: `MonoidAlgebraSemiring`, `PolynomialSemiring`, `KnotSemiring`, `ProvenanceSemiring`, `QuotientMonoidAlgebraSemiring`, `CliffordSemiring`, `GaloisFieldSemiring`. Free & quotient monoid algebras, skein modules, Clifford multivectors, finite fields.

### 5. Ring $(R, +, \cdot)$

A Semiring that **has additive inverses**.

* $(R, +)$ is an Abelian Group (Subtraction is defined).

**Example**: Integers $\mathbb{Z}$, Square Matrices $M_n (\mathbb{R})$.

### 6. Field $(F, +, \cdot)$

A Ring where **multiplication has inverses** (for non-zero elements).

* $(F \setminus \{0\}, \cdot)$ is an Abelian Group (Division is defined).

**Example**: Real Numbers $\mathbb{R}$, Complex Numbers $\mathbb{C}$.

### 7. Algebra (over a Field)

A Vector Space equipped with a bilinear product.

* Elements can be added and scaled (Vector Space).
* Elements can be multiplied (Ring-like).

**Example**: The set of $N \times N$ matrices forms an Algebra.

### 8. Ideal

A subset $I$ of a Ring $R$ that absorbs multiplication.

* If $x \in I$ and $r \in R$, then $r \cdot x \in I$.
* Used to define Quotient Rings (e.g., Modular Arithmetic).

### 9. Clifford Algebra (Geometric Algebra)

An associative algebra equipped with a quadratic form, unifying scalars, vectors, and higher-order blades (bivectors,
trivectors).

* **Geometric Product**: $ab = a \cdot b + a \wedge b$.
* Generalizes Complex Numbers and Quaternions.
* Used for rotations and physics in any dimension.

---

## Discrete Exterior Calculus (DEC) & Simplicial Homology

The `algebrax.analysis` and `algebrax.homology` modules implement concepts from DEC and Topological Homology on graphs
and $k$-dimensional simplicial complexes.

| Concept                       | Mathematical Object                        | Library Type / Function | Example / Application                        |
|:------------------------------|:-------------------------------------------|:------------------------|:---------------------------------------------|
| **0-form**                    | Scalar Field (on nodes)                    | `SparseVector`          | Temperature at each city                     |
| **1-form**                    | Vector Field (on edges)                    | `SparseMatrix`          | Traffic flow between cities                  |
| **Gradient ($d_0$)**          | $d_0: \Omega^0 \to \Omega^1$               | `gradient()`            | Difference in temp between cities            |
| **Divergence ($d_0^*$)**      | $d_0^*: \Omega^1 \to \Omega^0$             | `divergence()`          | Net traffic flow out of a city               |
| **Laplacian ($\Delta$)**      | $\Delta = d^* d$                           | `laplacian()`           | Heat diffusion rate                          |
| **$k$-Simplex**               | $k$-dim face $(v_0, \dots, v_k)$           | `SimplicialComplex`     | Triangles, tetrahedra, cliques               |
| **Boundary ($D_k$)**          | $D_k: C_k \to C_{k-1}$                     | `boundary_matrix()`     | Face boundary alternating sums               |
| **Nilpotency**                | $D_{k-1} \circ D_k = \mathbf{0}$           | `verify_nilpotency()`   | Fundamental homology boundary law            |
| **Hodge-Laplacian**           | $\Delta_k = D_{k+1} D_{k+1}^T + D_k^T D_k$ | `hodge_laplacian()`     | $k$-form diffusion & harmonic forms          |
| **Betti Numbers ($\beta_k$)** | $\dim(\ker D_k) - \text{rank}(D_{k+1})$    | `betti_numbers()`       | Hole count ($\beta_0$ comp, $\beta_1$ loops) |

---

## Clifford Geometric Algebra ($Cl (p, q, r)$)

The `algebrax.clifford` module implements **Clifford Geometric Algebra** over `QuotientMonoidAlgebraSemiring`.
Multivectors unify scalars, vectors, bivectors, and pseudoscalars into a single sparse mapping `{blade_tuple: coeff}`.

* **Geometric Product**: $A B = A \cdot B + A \wedge B$ (computed via `geometric_product()`).
* **Canonical Blade Reduction**: $\mathbf{e}_i \mathbf{e}_j = -\mathbf{e}_j \mathbf{e}_i$ and $\mathbf{e}_i^2 = +1$
  ($i \le p$), $-1$ ($p < i \le p+q$), $0$ ($i > p+q$).
* **Rotor Sandwiching ($v' = R v R^\dagger$)**: Smooth 3D spatial rotations $R = \exp (-\theta/2 \mathbf{B})$ via
  `rotor_rotation()` without gimbal lock or matrix conversions.

---

## Galois Finite Field Arithmetic ($\text{GF} (p^m)$)

The `algebrax.galois` module provides finite field arithmetic over `QuotientMonoidAlgebraSemiring`. Elements are
represented as sparse polynomial vectors `{exponent: coeff}` modulo an irreducible polynomial $P (x)$.

* **Polynomial Modulo Reduction**: Polynomial multiplication in $\mathbb{F}_p[x]$ reduced modulo $P (x)$
  (e.g. $x^8 + x^4 + x^3 + x + 1$ for AES $\text{GF} (2^8)$).
* **Matrix Arithmetic**: `gf_matrix_mul()` computes sparse matrix multiplication for cryptographic MixColumns
  transformations and Reed-Solomon generator matrices.

---

## Category Theory & Kleisli Monadic Composition

The `algebrax.category` module formalizes category-theoretic compositions.

* **Morphisms as Matrices**: Hom-sets $\text{Hom} (A, B)$ are sparse matrices $M[A][B]$.
* **Kleisli Monadic Composition**: Effectful morphisms $f: A \to T (B)$ and $g: B \to T (C)$ compose via Kleisli matrix
  multiplication ($g \circ_T f = \text{dot} (f, g, \text{semiring})$) over probabilistic (Viterbi), cost-metric
  (Tropical), or reachability (Boolean) monad semirings.
* **Kan Extensions**: Left Kan extensions $\text{Lan}_P F$ computed over sparse category graphs.

---

## Functional Taxonomy

The following table categorizes the functions in the `algebra` module by their **Domain** (Meaning) and **Operation
Type**.

### Legend

* **Structural**: Transforms the shape or content of the data (returns a `Mapping`).
* **Metric**: Reduces the data to a single number (returns `float`/`int`).
* **Predicate**: Checks a property (returns `bool`).
* **Generator**: Creates a new structure from scratch.

### 1. Linear Algebra (Matrix & Vector)

*Input: Sparse Vectors/Matrices (representing physical systems or geometric transformations)*

| Function             | Type       | Meaning                                        |
|:---------------------|:-----------|:-----------------------------------------------|
| `add`                | Structural | Element-wise addition ($A + B$).               |
| `dot`                | Structural | Matrix Multiplication ($A \cdot B$).           |
| `mat_vec`, `vec_mat` | Structural | Matrix-Vector multiplication (Transformation). |
| `transpose`          | Structural | Flips rows and columns ($A^T$).                |
| `inverse`            | Structural | Finds $A^{-1}$ such that $A \cdot A^{-1} = I$. |
| `power`              | Structural | Matrix exponentiation ($A^k$).                 |
| `adjoint`            | Structural | Transpose of cofactor matrix.                  |
| `cofactor`           | Structural | Matrix of cofactors.                           |
| `inner`              | Metric     | Dot product of two vectors (Similarity).       |
| `determinant`        | Metric     | Volume scaling factor of the transformation.   |
| `trace`              | Metric     | Sum of diagonal elements (Invariant).          |
| `kronecker_delta`    | Generator  | Creates an Identity Matrix ($I$).              |

### 2. Lattice & Set Theory (Fuzzy Logic)

*Input: Mappings as Sets or Fuzzy Sets (Values represent membership/intensity)*

| Function                                     | Type       | Meaning                             |
|:---------------------------------------------|:-----------|:------------------------------------|
| `join`                                       | Structural | Union / Max ($A \cup B$).           |
| `meet`                                       | Structural | Intersection / Min ($A \cap B$).    |
| `difference`                                 | Structural | Set Difference ($A - B$).           |
| `symmetric_difference`                       | Structural | XOR ($A \Delta B$).                 |
| `combine`                                    | Structural | Generalized element-wise operation. |
| `mask`                                       | Structural | Keep keys in A that are also in B.  |
| `exclude`                                    | Structural | Keep keys in A that are NOT in B.   |
| `product`                                    | Structural | Element-wise product (Hadamard).    |
| `ratio`                                      | Structural | Element-wise division.              |
| `average`, `geometric_mean`, `harmonic_mean` | Structural | Element-wise means.                 |

### 3. Probability & Statistics

*Input: Mappings as Probability Distributions (Values sum to 1)*

| Function                           | Type       | Meaning                                        |
|:-----------------------------------|:-----------|:-----------------------------------------------|
| `bayes_update`                     | Structural | Posterior $\propto$ Likelihood $\times$ Prior. |
| `markov_step`                      | Structural | Advance state by $N$ steps ($v \cdot P^n$).    |
| `markov_steady_state`              | Structural | Find equilibrium distribution ($\pi = \pi P$). |
| `marginalize`                      | Structural | Sum over rows/cols (Joint $\to$ Marginal).     |
| `normalize`                        | Structural | Scale values to sum to 1.                      |
| `entropy`                          | Metric     | Uncertainty ($H(X)$).                          |
| `cross_entropy`                    | Metric     | Difference between distributions ($H(P, Q)$).  |
| `kl_divergence`                    | Metric     | Information Gain ($D_{KL}(P \| Q)$).           |
| `mutual_information`               | Metric     | Dependence between variables ($I(X; Y)$).      |
| `expected_value`                   | Metric     | Mean of the distribution ($E[X]$).             |
| `variance`, `skewness`, `kurtosis` | Metric     | Higher-order moments.                          |
| `mode`                             | Metric     | Most probable outcome.                         |

### 4. Graph Analysis (Network Science)

*Input: Mappings as Adjacency Matrices (Graphs)*

| Function                 | Type       | Meaning                                        |
|:-------------------------|:-----------|:-----------------------------------------------|
| `laplacian`              | Structural | Graph Laplacian ($D - A$). Diffusion operator. |
| `gradient`               | Structural | Edge-based difference operator.                |
| `divergence`             | Structural | Node-based flow operator.                      |
| `eigen_centrality`       | Structural | Node importance ranking.                       |
| `forman_ricci_curvature` | Metric     | Local curvature of the graph (Geometry).       |

### 5. Signal Processing

*Input: Mappings as Time Series or Signals*

| Function                 | Type       | Meaning                                                     |
|:-------------------------|:-----------|:------------------------------------------------------------|
| `convolve`               | Structural | Discrete convolution / polynomial multiplication ($f * g$). |
| `dft` / `idft`           | Structural | Discrete Fourier Transform (Time $\leftrightarrow$ Freq).   |
| `walsh_hadamard`         | Structural | Walsh-Hadamard Transform (Orthogonal Hadamard mapping).     |
| `gelfand_transform`      | Structural | Generalized character evaluation over monoid algebras.      |
| `legendre_fenchel`       | Structural | Fenchel-Legendre transform (Slope transform).               |
| `z_transform`            | Structural | Z-Transform (Discrete Laplace / Semiring power series).     |
| `hilbert`                | Structural | Hilbert Transform (Analytic Signal).                        |
| `lorentz_boost`          | Structural | Relativistic coordinate transformation.                     |
| `box_counting_dimension` | Metric     | Fractal dimension of the signal.                            |

### 6. Group Theory

*Input: Mappings as Permutations (Bijective Functions)*

| Function    | Type       | Meaning                             |
|:------------|:-----------|:------------------------------------|
| `compose`   | Structural | Function composition ($f \circ g$). |
| `invert`    | Structural | Inverse function ($f^{-1}$).        |
| `signature` | Metric     | Parity of permutation (+1 or -1).   |

### 7. Sparsity & Meta-Analysis

*Input: Any Mapping*

| Function      | Type      | Meaning                                       |
|:--------------|:----------|:----------------------------------------------|
| `sparsity`    | Metric    | Fraction of zero elements ($1 - k/N$).        |
| `density`     | Metric    | Fraction of non-zero elements ($k/N$).        |
| `deepness`    | Metric    | Maximum nesting depth.                        |
| `wideness`    | Metric    | Maximum branching factor.                     |
| `uniformness` | Metric    | Variance of value distribution (0 = uniform). |
| `is_sparse`   | Predicate | Checks if density < threshold.                |

### 8. Automata

*Input: State Machines (Transition Functions)*

| Function                       | Type       | Meaning               |
|:-------------------------------|:-----------|:----------------------|
| `dfa_step`, `nfa_step`         | Structural | Single transition.    |
| `simulate_dfa`, `simulate_nfa` | Structural | Full execution trace. |

### 9. Algebraic Structures

*Input: Tries & Higher-Order Structures*

| Function/Class  | Type      | Meaning                                      |
|:----------------|:----------|:---------------------------------------------|
| `AlgebraicTrie` | Structure | Sparse Tensor / Prefix Tree over a Semiring. |
