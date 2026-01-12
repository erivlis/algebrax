# Algebraic Structures

This document provides a theoretical overview of the algebraic structures used in `mappingtools.algebra`. Understanding
these concepts helps clarify why certain operations are grouped together and how they generalize across different
domains (graphs, logic, probability).

## Hierarchy of Structures (Ordered by Complexity)

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

**Examples in Library** (`algebra.semiring`):

* **Standard**: $(\mathbb{R}, +, \times)$. Standard Matrix Multiplication.
* **Tropical**: $(\mathbb{R} \cup \{\infty\}, \min, +)$. Shortest Path algorithms.
* **Boolean**: $(\{T, F\}, \lor, \land)$. Reachability / Transitive Closure.
* **Viterbi**: $([0, 1], \max, \times)$. Most likely path in HMMs.

### 5. Ring $(R, +, \cdot)$

A Semiring that **has additive inverses**.

* $(R, +)$ is an Abelian Group (Subtraction is defined).

**Example**: Integers $\mathbb{Z}$, Square Matrices $M_n(\mathbb{R})$.

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

## Discrete Exterior Calculus (DEC)

The `algebra.analysis` module implements concepts from DEC on graphs.

| Concept                  | Mathematical Object          | Library Type   | Example                           |
|:-------------------------|:-----------------------------|:---------------|:----------------------------------|
| **0-form**               | Scalar Field (on nodes)      | `SparseVector` | Temperature at each city          |
| **1-form**               | Vector Field (on edges)      | `SparseMatrix` | Traffic flow between cities       |
| **Gradient ($d_0$)**     | $d: \Omega^0 \to \Omega^1$   | `gradient()`   | Difference in temp between cities |
| **Divergence ($d_0^*$)** | $d^*: \Omega^1 \to \Omega^0$ | `divergence()` | Net traffic flow out of a city    |
| **Laplacian ($\Delta$)** | $\Delta = d^* d$             | `laplacian()`  | Heat diffusion rate               |

**Note on Curl**:
The Curl operator ($d_1$) maps 1-forms (edges) to 2-forms (faces). Since `mappingtools` operates on Graphs (nodes and
edges only), there are no 2-forms (triangles/faces), so **Curl is undefined** (or trivially zero). To support Curl, the
library would need to support Simplicial Complexes.

---

## The Algebraic Trie (Sparse Tensor)

The `AlgebraicTrie` (`algebra.trie`) is a generalization of the classic Trie (Prefix Tree) data structure.

Mathematically, a Trie is isomorphic to a **Sparse Tensor** of arbitrary rank.

* **Indices**: The sequence of keys (e.g., characters in a string) corresponds to the indices of the
  tensor $(i_1, i_2, \dots, i_k)$.
* **Values**: The value stored at a node corresponds to the tensor value $T_{i_1, i_2, \dots, i_k}$.

By equipping the Trie with a **Semiring**, we can perform algebraic operations:

* **Insertion (`add`)**: Corresponds to Tensor Addition ($T \oplus V$).
    * If Semiring is `Standard` (+), values accumulate (Count).
    * If Semiring is `Tropical` (min), values update to the minimum (Shortest Path).
* **Contraction (`contract`)**: Corresponds to Tensor Contraction (Marginalization).
    * Summing up all values in a subtree is equivalent to summing over the remaining dimensions of the tensor.

This abstraction allows the same `AlgebraicTrie` class to serve as:

1. **Word Counter**: `StandardSemiring` (Sum counts).
2. **Probabilistic Suffix Tree**: `ProbabilitySemiring` (Sum probabilities).
3. **Fuzzy Search Index**: `TropicalSemiring` (Minimize edit distance).

---

## Why Semirings?

`mappingtools` focuses heavily on **Semirings** because many discrete structures (graphs, automata, logic) do not
support subtraction or division.

* **Shortest Path**: You cannot "un-take" a minimum. $a \oplus b = \min(a, b)$. If $a=5, b=3$, result is 3. You cannot
  recover 5 from 3.
* **Reachability**: $T \lor F = T$. You cannot subtract $F$ to get $T$.

By abstracting matrix multiplication to use Semiring operations, we allow the same `matrix.dot` and `matrix.power`
functions to solve:

1. **Physics**: Quantum Mechanics (Standard Algebra).
2. **Optimization**: Shortest Path (Tropical Algebra).
3. **Logic**: Connectivity (Boolean Algebra).
4. **Inference**: Viterbi Decoding (Max-Product Algebra).
5. **Linguistics**: Regular Expressions (String Algebra).

## Why Not Clifford Algebra?

While Clifford Algebra is powerful for geometry (rotations, physics), it is **not implemented** in `mappingtools`
because:

1. **Density**: Geometric products often mix all components (e.g., rotating a vector usually makes it dense). This
   conflicts with the library's sparse-first philosophy.
2. **Complexity**: Implementing a full multivector system requires significant machinery (grade tracking, metric
   tensors) that is out of scope for a general-purpose mapping library.
3. **Alternatives**: Specialized libraries like `clifford` or `sympy.diffgeom` handle this domain better.

---

## Functional Taxonomy

The following table categorizes the functions in the `algebra` module by their **Domain** (Meaning) and **Operation Type
**.

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

| Function                   | Type       | Meaning                                        |
|:---------------------------|:-----------|:-----------------------------------------------|
| `laplacian`                | Structural | Graph Laplacian ($D - A$). Diffusion operator. |
| `gradient`                 | Structural | Edge-based difference operator.                |
| `divergence`               | Structural | Node-based flow operator.                      |
| `eigen_centrality`         | Structural | Node importance ranking.                       |
| `ollivier_ricci_curvature` | Metric     | Local curvature of the graph (Geometry).       |

### 5. Signal Processing

*Input: Mappings as Time Series or Signals*

| Function                 | Type       | Meaning                                                   |
|:-------------------------|:-----------|:----------------------------------------------------------|
| `convolve`               | Structural | Signal convolution ($f * g$).                             |
| `dft` / `idft`           | Structural | Discrete Fourier Transform (Time $\leftrightarrow$ Freq). |
| `z_transform`            | Structural | Z-Transform (Discrete Laplace).                           |
| `hilbert`                | Structural | Hilbert Transform (Analytic Signal).                      |
| `lorentz_boost`          | Structural | Relativistic coordinate transformation.                   |
| `box_counting_dimension` | Metric     | Fractal dimension of the signal.                          |

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

*Input: Semirings and Tries*

| Function/Class  | Type      | Meaning                                                    |
|:----------------|:----------|:-----------------------------------------------------------|
| `AlgebraicTrie` | Structure | Sparse Tensor / Prefix Tree over a Semiring.               |
| `Semiring`      | Protocol  | Defines $(+, \times)$ operations for algebraic structures. |
