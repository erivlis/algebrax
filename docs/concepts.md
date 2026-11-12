---
title: Concepts
description: Theoretical overview of the algebraic structures used in `algebrax`, including monoids, groups, semirings, and their applications in graph analysis, logic, and probability.
icon: lucide/lightbulb
---

# Concepts

This document provides a theoretical overview of the algebraic structures used in `algebrax`. Understanding these
concepts helps clarify why certain operations are grouped together and how they generalize across different domains
(graphs, logic, probability).

> [!TIP]
> **Semiring Mental Model**
> Think of a Semiring as an arithmetic engine where you swap out standard Addition (+) and
> Multiplication (×) for any custom rules — like $(\min, +)$ for shortest paths, or $(\max, \times)$
> for link reliability. The exact same sparse matrix multiplication algorithm (`dot`) then solves completely
> different problems just by switching the semiring!

---

## The Periodic Table of Algebraic Mixins (`algebrax.algebra`)

Every algebraic protocol in `algebrax.algebra` is assembled from **19 purely orthogonal atomic operational mixins**. Each mixin inherits directly from `typing.Protocol` and defines a single operational cluster, guaranteeing a diamond-free inheritance graph and a **1-to-1 left-to-right correspondence** between Python class bases and formal mathematical signatures:

$$\text{External Action } (\cdot_s) \longrightarrow \text{Additive Cluster } (\mathbf{0}, \operatorname{is\_zero}, +, -) \longrightarrow \text{Multiplicative Cluster } (\mathbf{1}, \cdot, {}^{-1}) \longrightarrow \text{Closure / Bounds / Quotients } ({}^*, \vee, \wedge, \bot, \top, \neg, \in, \bmod I)$$

| Cluster               | Atomic Mixin                 | Required Member(s)       | Default Helper(s)    | Mathematical Symbol                             |
|:----------------------|:-----------------------------|:-------------------------|:---------------------|:------------------------------------------------|
| **External Action**   | `HasScale[R, M]`             | `smul(r, m) -> M`        | —                    | $\cdot_s: R \times M \to M$                     |
| **Additive**          | `HasZero[V]`                 | `zero -> V`              | —                    | $\mathbf{0} \in V$                              |
|                       | `HasZeroPred[V]`             | —                        | `is_zero(a) -> bool` | $\operatorname{is\_zero}: V \to \{\top, \bot\}$ |
|                       | `HasAdd[V]`                  | `add(a, b) -> V`         | —                    | $+: V \times V \to V$                           |
|                       | `HasNeg[V]`                  | `neg(a) -> V`            | `sub(a, b) -> V`     | $-: V \to V$                                    |
| **Multiplicative**    | `HasOne[V]`                  | `one -> V`               | —                    | $\mathbf{1} \in V$                              |
|                       | `HasMul[V]`                  | `mul(a, b) -> V`         | —                    | $\cdot: V \times V \to V$                       |
|                       | `HasInv[V]`                  | `inv(a) -> V`            | `div(a, b) -> V`     | ${}^{-1}: V \setminus \{\mathbf{0}\} \to V$     |
| **Closure**           | `HasStar[V]`                 | `star(a) -> V`           | —                    | ${}^*: V \to V$                                 |
| **Order / Lattice**   | `HasJoin[V]`                 | `join(a, b) -> V`        | —                    | $\vee: V \times V \to V$                        |
|                       | `HasMeet[V]`                 | `meet(a, b) -> V`        | —                    | $\wedge: V \times V \to V$                      |
|                       | `HasBounds[V]`               | `bot -> V`, `top -> V`   | —                    | $\bot, \top \in V$                              |
|                       | `HasComplement[V]`           | `complement(a) -> V`     | —                    | $\neg: V \to V$                                 |
| **Domain-Agnostic**   | `HasIdentity[V]`             | `identity -> V`          | —                    | $e \in V$                                       |
|                       | `HasOp[V]`                   | `op(a, b) -> V`          | —                    | $\circ: V \times V \to V$                       |
| **Non-Associative**   | `HasBracket[V]`              | `bracket(a, b) -> V`     | —                    | $[\cdot, \cdot]: V \times V \to V$              |
| **Ideals & Quotients**| `HasContains[V]`             | `contains(x) -> bool`    | —                    | $\in: V \to \{\top, \bot\}$                     |
|                       | `HasReduce[V]`               | `reduce(x) -> V`         | —                    | $x \mapsto [x] \in R / I$                       |
|                       | `HasGenerator[V]`            | `generator -> V`         | —                    | $a \in R \text{ where } I = (a)$                |

> [!NOTE]
> **Subclassing vs. Structural Duck-Typing (The Golem Safety Contract)**
> When subclassing `HasZeroPred`, `HasNeg`, or `HasInv`, Python inherits their default helper implementations (`is_zero`, `sub`, `div`). However, when using purely structural duck-typing without inheriting from the mixins, Python's `@runtime_checkable` `isinstance(obj, Protocol)` requires that **all** protocol attributes be present on the instance or class.

### Equational Law Witness Mixins (Pillar 2)

Alongside operational mixins (`Has*`), `algebrax.algebra` defines lightweight **Law Witness Mixins** that advertise equational axioms satisfied by a structure:

| Law Witness | Property / Witness Method | Axiom / Equational Law | Canonical Examples |
|:------------|:--------------------------|:-----------------------|:-------------------|
| `LawAssociative` | `is_associative -> True` | $(a \cdot b) \cdot c = a \cdot (b \cdot c)$ | Monoids, Groups, Semirings, Associative Algebras |
| `LawCommutative` | `is_commutative -> True` | $a \cdot b = b \cdot a$ | Abelian groups, Commutative rings, Fields |
| `LawIdempotent` | `is_idempotent -> True` | $a \oplus a = a$ | Tropical semiring $(\min, +)$, Boolean $(\lor, \land)$, Lattices |
| `LawDistributive` | `is_distributive -> True` | $a \cdot (b + c) = (a \cdot b) + (a \cdot c)$ | Semirings, Rings, Fields |
| `LawUnital` | `is_unital -> True` | $a \cdot \mathbf{1} = \mathbf{1} \cdot a = a$ | Unital rings, Monoids |
| `LawLieAdmissible` | `is_lie_admissible -> True` | Jacobi identity $[[x, y], z] + [[y, z], x] + [[z, x], y] = 0$ | Lie algebras $\mathfrak{g}$, Poisson brackets |
| `LawJordanAdmissible`| `is_jordan_admissible -> True`| $(x \circ y) \circ x^2 = x \circ (y \circ x^2)$ | Jordan algebras, Quantum observables |
| `LawAlternative` | `is_alternative -> True` | $x(xy) = x^2 y$ and $(yx)x = y x^2$ | Octonions $\mathbb{O}$, Cayley-Dickson algebras |
| `LawFlexible` | `is_flexible -> True` | $(xy)x = x(yx)$ | Non-associative division algebras |

---

## Algebraic Structures

Hierarchy of Structures (Ordered by Complexity — see the [Deductive User Guide](guide/index.md) for interactive tutorials)

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

* **Permutations** (`algebrax.group`): The set of bijective mappings forms a group under composition.
    * Operation: `compose(f, g)`
    * Inverse: `invert(f)`
    * Identity: `{k: k}`

### 3. Abelian Group

A Group where the operation is also **Commutative**:

* $a \cdot b = b \cdot a$.

**Example**: Integers under addition $(\mathbb{Z}, +)$.

### 4. Groupoid $\mathcal{G}$

A **Groupoid** generalizes a Group to multi-state systems. It can be defined as a small Category in which **every morphism is an isomorphism (invertible)**, or as a set equipped with a *partial* binary composition $\circ$ satisfying:

* **Partial Composition**: $g \circ f$ is defined only when the codomain (target) of $f$ equals the domain (source) of $g$.
* **Associativity**: $(h \circ g) \circ f = h \circ (g \circ f)$ whenever composable.
* **Identities**: For every state/object $A$, there exists an identity morphism $\text{id}_A$.
* **Inverses**: For every morphism $f: A \to B$, there exists an inverse morphism $f^{-1}: B \to A$ such that:
  $$f \circ f^{-1} = \text{id}_B \quad \text{and} \quad f^{-1} \circ f = \text{id}_A$$

**Examples & Applications**:

* **Group vs Groupoid**: A Group is a Groupoid with *only one object* (all elements are everywhere composable).
* **Patch Theory (Darcs VCS)**: Repository states are objects; diff patches $P: \text{State}_1 \to \text{State}_2$ are groupoid morphisms. Every patch has a formal inverse $P^{-1}$, and patches compose along valid execution paths.
* **Topological Fundamental Groupoid $\Pi_1(X)$**: Continuous path transformations in point clouds and simplicial complexes (`algebrax.topology`).
* **Permutations** (`algebrax.group`): Full permutations form a single-object groupoid (a Group), while partial bijection transformations form a multi-object groupoid.

### 5. Semiring $(S, \oplus, \otimes)$

A set $S$ with two operations, Addition ($\oplus$) and Multiplication ($\otimes$), satisfying:

* $(S, \oplus)$ is a Commutative Monoid (Identity $\mathbf{0}$).
* $(S, \otimes)$ is a Monoid (Identity $\mathbf{1}$).
* **Distributivity**: Multiplication distributes over Addition.
* **Annihilation**: $a \otimes \mathbf{0} = \mathbf{0}$.

**Crucially**: Semirings do **not** require additive inverses (subtraction) or multiplicative inverses (division). In `algebrax.algebra`, the semiring family forms a precise three-tiered protocol hierarchy ([EP-0197](proposals/EP-0197-decoupled-semiring-foundations-star-semirings-and-kleene-algebras.md)):

* **`Semiring` (Pure Rig)** $\langle S, \mathbf{0}, \oplus, \mathbf{1}, \otimes \rangle$: Pure two-operation system (`HasZero`, `HasAdd`, `HasOne`, `HasMul`). Because Kleene star is decoupled, **every Ring is structurally a Semiring** ($\text{Semiring} \subset \text{Ring} \subset \text{Field}$).
* **`StarSemiring` (Closed / Conway Semiring)** $\langle S, \mathbf{0}, \oplus, \mathbf{1}, \otimes, {}^* \rangle$: Equips a semiring with unary Kleene star closure $a^* = \mathbf{1} \oplus a \otimes a^* = \mathbf{1} \oplus a^* \otimes a$ (`HasStar`). Exemplified by `DualNumberAlgebra` (Taylor series) and infinite reachability matrices.
* **`KleeneAlgebra`**: An idempotent star semiring where addition is idempotent ($a \oplus a = a$), witnessing [`LawIdempotent`](#equational-law-witness-mixins-pillar-2). Exemplified by `TropicalSemiring` (shortest paths) and `BooleanSemiring` (transitive reachability).

**Examples in Library** (`algebrax.semiring`):

Semirings are organized into categorical sub-modules under `algebrax.semiring`:

* **`arithmetic`**: `StandardSemiring` over real numbers $(\mathbb{R}, +, \times)$ or complex amplitudes $(\mathbb{C}, +, \times)$ (quantum path integrals, discrete wave interference).
* **`optimization`**: `TropicalSemiring` $(\mathbb{R} \cup \{\infty\}, \min, +)$, `ArcticSemiring`, `ViterbiSemiring`, `ReliabilitySemiring`, `BottleneckSemiring`, `MinTimesSemiring`. Shortest path and capacity algorithms (Kleene algebras).
* **`logic`**: `BooleanSemiring` $(\{T, F\}, \lor, \land)$, `LukasiewiczSemiring`, `DigitalSemiring`. Reachability, fuzzy logic, and post-quantum digital operations (Kleene algebras).
* **`statistical`**: `LogSemiring`, `ExpectationSemiring`, `VarianceSemiring`, `SkewnessSemiring`, `KurtosisSemiring`, `StatisticalMomentSemiring`, `BivariateVarianceSemiring`, `MultivariateMomentSemiring`. Probabilistic inference, higher-order statistical moments, multivariate covariance matrices.
* **`structures`**: `StringSemiring`, `KCollapsedSemiring`. Formal path languages, bounded counting.
* **`algebraic`**: `DualNumberAlgebra` (Star semiring), `BinomialConvolutionSemiring`, `MultivariateBinomialConvolutionSemiring`, `MonoidAlgebraSemiring`, `PolynomialAlgebra`, `KnotSemiring`, `ProvenanceSemiring`, `QuotientMonoidAlgebraSemiring`, `CliffordAlgebra` ($Cl(p,q,r)$ geometric algebras and Spacetime Dirac spinors), `GeneralizedCliffordAlgebra`, `QuantumCliffordAlgebra`, `GaloisFieldSemiring`. Free & quotient monoid algebras, divided power polynomial rings, skein modules, Clifford multivectors, finite fields.

### 6. Ring $(R, +, \cdot)$

A Semiring that **has additive inverses**.

* $(R, +)$ is an Abelian Group (Subtraction is defined).

**Example**: Integers $\mathbb{Z}$, Square Matrices $M_n (\mathbb{R})$.

> [!NOTE]
> **Why the Graph Laplacian Requires a Ring/Field**
> While reachability ($\lor, \land$) and shortest paths ($\min, +$) operate over **Semirings** without additive inverses,
> the **Graph Laplacian** $L = D - W$ and discrete exterior calculus inherently require **subtraction** (additive inverse).
> The Laplacian measures the difference between a node's self-degree and its incident neighbors. Consequently, spectral
> graph theory and discrete Laplace-Beltrami diffusion operators are housed in linear rings and fields over $\mathbb{R}$.

### 7. Field $(F, +, \cdot)$

A Ring where **multiplication has inverses** (for non-zero elements).

* $(F \setminus \{0\}, \cdot)$ is an Abelian Group (Division is defined).

**Example**: Real Numbers $\mathbb{R}$, Complex Numbers $\mathbb{C}$.

### 8. Algebra (over a Field)

A Vector Space equipped with a bilinear product.

* Elements can be added and scaled (Vector Space).
* Elements can be multiplied (Ring-like).

**Example**: The set of $N \times N$ matrices forms an Algebra.

### 9. Homomorphisms, Ideals & Canonical Quotients (`algebrax.algebra`)

An **Ideal** $I \triangleleft R$ is an additive subgroup of a ring $R$ that *absorbs* multiplication ($\forall x \in I, r \in R \implies r \cdot x \in I \text{ and } x \cdot r \in I$). Ideals arise universally as the **kernels** of structure-preserving **homomorphisms** $\phi: R \to S$:

$$\ker \phi = \{x \in R \mid \phi(x) = \mathbf{0}_S\}, \qquad R / \ker \phi \cong \operatorname{im} \phi \quad (\text{First Isomorphism Theorem})$$

* **Homomorphism Protocols**: `Homomorphism[Dom, Cod]`, `RingHom[Dom, Cod]`, `GroupHom[Dom, Cod]`, `LinearMap[R, Dom, Cod]`, `LieAlgebraHom[Dom, Cod]`, and `CallableHomomorphism`.
* **Ideal Protocols & Implementations**: `Ideal[V]`, `LeftIdeal[V]`, `RightIdeal[V]`, `PrincipalIdeal[V]`, `LieIdeal[V]`, `IntegerModuloIdeal(n)`, `PolynomialTruncationIdeal(n)`, `NilpotentIdeal(k)`, `KernelIdeal(hom, cod_ring, reducer)`, and `SubspaceLieIdeal(keys)`.
* **Canonical Unboxed Quotients**: `QuotientSemiring(semiring, ideal)`, `QuotientRing(ring, ideal)`, and `QuotientAlgebra(algebra, ideal)` evaluate operations on unboxed coset representatives via `ideal.reduce(x)` with zero heap-wrapper overhead, while `MonoidAlgebraSemiring` $\to$ `MonoidAlgebra` and `QuotientMonoidAlgebraSemiring` $\to$ `QuotientMonoidAlgebra` provide free and in-loop basis-rewriting monoid semirings and algebras.

### 10. Clifford Algebra (Geometric & Quantum Generalizations)

An associative algebra equipped with a quadratic form or root-of-unity commutation rule, unifying scalars, vectors, and higher-order blades (bivectors, trivectors).

* **Standard Clifford / Geometric Algebra $Cl(p, q, r)$**: $\mathbf{e}_i \mathbf{e}_j = -\mathbf{e}_j \mathbf{e}_i$ ($i \ne j$), $\mathbf{e}_i^2 \in \{+1, -1, 0\}$, with geometric product $ab = a \cdot b + a \wedge b$. Generalizes complex numbers, quaternions, and Dirac spinors.
* **Generalized Clifford Algebra (GCA) $C_n^{(m)}$**: Clock-and-shift commutation $\mathbf{e}_j \mathbf{e}_k = \omega \mathbf{e}_k \mathbf{e}_j$ ($j < k$) where $\omega = \exp(2\pi i / n)$ is a primitive $n$-th root of unity and $\mathbf{e}_j^n = \alpha_j \mathbf{1}$.
* **$q$-Deformed Quantum Clifford Algebra $Cl_q(m)$**: Braided quantum deformation $\mathbf{e}_j \mathbf{e}_k = -q \mathbf{e}_k \mathbf{e}_j$ ($j < k$).

---

## Discrete Exterior Calculus (DEC) & Simplicial Homology

The `algebrax.analysis` and `algebrax.topology` modules implement concepts from DEC and Topological Homology on graphs
and $k$-dimensional simplicial complexes.

| Concept                       | Mathematical Object                        | Library Type / Function     | Example / Application                        |
|:------------------------------|:-------------------------------------------|:----------------------------|:---------------------------------------------|
| **0-form**                    | Scalar Field (on nodes)                    | `SparseVector`              | Temperature at each city                     |
| **1-form**                    | Vector Field (on edges)                    | `SparseMatrix`              | Traffic flow between cities                  |
| **Gradient ($d_0$)**          | $d_0: \Omega^0 \to \Omega^1$               | `gradient()`                | Difference in temp between cities            |
| **Divergence ($d_0^*$)**      | $d_0^*: \Omega^1 \to \Omega^0$             | `divergence()`              | Net traffic flow out of a city               |
| **Laplacian ($\Delta$)**      | $\Delta = d^* d$                           | `laplacian()`               | Heat diffusion rate                          |
| **$k$-Simplex**               | $k$-dim face $(v_0, \dots, v_k)$           | `SimplicialComplex`         | Triangles, tetrahedra, cliques               |
| **Boundary ($D_k$)**          | $D_k: C_k \to C_{k-1}$                     | `sc.boundary_matrix(k)`     | Face boundary alternating sums               |
| **Nilpotency**                | $D_{k-1} \circ D_k = \mathbf{0}$           | `sc.verify_nilpotency(k)`   | Fundamental homology boundary law            |
| **Hodge-Laplacian**           | $\Delta_k = D_{k+1} D_{k+1}^T + D_k^T D_k$ | `hodge_laplacian(sc, k)`    | $k$-form diffusion & harmonic forms          |
| **Betti Numbers ($\beta_k$)** | $\dim(\ker D_k) - \text{rank}(D_{k+1})$    | `sc.betti_numbers(max_k)`   | Hole count ($\beta_0$ comp, $\beta_1$ loops) |

---

## Clifford Geometric Algebra ($Cl (p, q, r)$)

The `algebrax.clifford` module implements **Clifford Geometric Algebra** over `QuotientMonoidAlgebra`.
Multivectors unify scalars, vectors, bivectors, and pseudoscalars into a single sparse mapping `{blade_tuple: coeff}`.

* **Geometric Product**: $A B = A \cdot B + A \wedge B$ (computed via `cl.mul(A, B)` on `CliffordAlgebra`).
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

## Category Theory, $\mathbf{Mat}(\mathcal{S})$ & Lawvere Metric Spaces

The `algebrax.category` module formalizes Lean 4 Mathlib-aligned category theory, functorial duality, and enriched matrix mechanics (`EP-0200`):

* **Category & Functor Protocols**: `Category[Obj, Mor]`, `Functor[Obj, Mor, Obj_co, Mor_co]`, and `OppositeCategory[Obj, Mor]` ($\mathcal{C}^{\mathrm{op}}$), verified via `verify_category_laws()` and `verify_functor_laws()`.
* **The Matrix Category $\mathbf{Mat}(\mathcal{S})$ (`MatrixCategory`)**: Finite index sets are objects and unboxed sparse matrices `dict[K, dict[K, V]]` are morphisms, with `TransposeFunctor` realizing the duality isomorphism $\mathbf{Mat}(\mathcal{S})^{\mathrm{op}} \xrightarrow{\sim} \mathbf{Mat}(\mathcal{S})$ and `SemiringChangeOfBaseFunctor` mapping matrices across semiring homomorphisms.
* **Lawvere Metric Spaces (`LawvereMetricCategory`)**: Realizes Lawvere's theorem that a generalized directed metric space $(X, d)$ is a category enriched over `TropicalSemiring` $\langle [0, \infty], \min, +, \infty, 0 \rangle$, where composition is the triangle inequality $d(x, y) + d(y, z) \ge d(x, z)$ and `metric_closure()` computes all-pairs shortest paths via Kleene star.
* **Kleisli Monadic Composition & Kan Extensions**: `kleisli_compose()` and `kan_extension_left()` over monadic transition matrices.

---

## Functional Taxonomy

The following table categorizes the functions in the `algebrax` module by their **Domain** (Meaning) and **Operation
Type**.

### Legend

* **Structural**: Transforms the shape or content of the data (returns a `Mapping`).
* **Metric**: Reduces the data to a single number (returns `float`/`int`).
* **Predicate**: Checks a property (returns `bool`).
* **Generator**: Creates a new structure from scratch.

### 1. Linear Algebra (Matrix & Vector)

*Input: Sparse Vectors/Matrices (representing physical systems or geometric transformations)*

| Function             | Type       | Meaning                                          |
|:---------------------|:-----------|:-------------------------------------------------|
| `add`                | Structural | Element-wise addition ($A + B$).                 |
| `dot`                | Structural | Matrix Multiplication ($A \cdot B$).             |
| `mat_vec`, `vec_mat` | Structural | Matrix-Vector multiplication (Transformation).   |
| `transpose`          | Structural | Flips rows and columns ($A^T$).                  |
| `inv`                | Structural | Matrix inverse $A^{-1}$ (`algebrax.matrix.inv`). |
| `power`              | Structural | Matrix exponentiation ($A^k$).                   |
| `adjoint`            | Structural | Transpose of cofactor matrix.                    |
| `cofactor`           | Structural | Matrix of cofactors.                             |
| `inner`              | Metric     | Dot product of two vectors (Similarity).         |
| `det`                | Metric     | Matrix determinant (`algebrax.matrix.det`).      |
| `trace`              | Metric     | Sum of diagonal elements (Invariant).            |
| `kronecker_delta`    | Generator  | Creates an Identity Matrix ($I$).                |

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
