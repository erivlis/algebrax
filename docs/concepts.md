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

Every algebraic and categorical protocol in `algebrax.algebra` and `algebrax.category` is assembled from **37 purely orthogonal atomic operational mixins** (28 algebraic `Has*` + 9 categorical `Has*`). Each mixin inherits directly from `typing.Protocol` and defines a single operational cluster, guaranteeing a diamond-free inheritance graph and a **1-to-1 left-to-right correspondence** between Python class bases and formal mathematical signatures:

$$\text{External Action } (\cdot_s) \longrightarrow \text{Additive Cluster } (\mathbf{0}, \operatorname{is\_zero}, +, -) \longrightarrow \text{Multiplicative Cluster } (\mathbf{1}, \cdot, {}^{-1}) \longrightarrow \text{Coalgebraic Cluster } (\Delta, \epsilon, S) \longrightarrow \text{Closure / Bounds / Quotients / Derivation } ({}^*, \vee, \wedge, \bot, \top, \neg, \in, \bmod I, \partial_i)$$

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
| **Coalgebra & Duality**| `HasCoproduct[C]`           | `coproduct(c) -> dict`   | —                    | $\Delta: C \to C \otimes C$                     |
|                       | `HasCounit[R, C]`            | `counit(c) -> R`         | —                    | $\epsilon: C \to R$                             |
|                       | `HasAntipode[H]`             | `antipode(h) -> H`       | —                    | $S: H \to H$                                    |
| **Closure & Action**  | `HasStar[V]`                 | `star(a) -> V`           | —                    | ${}^*: V \to V$                                 |
|                       | `HasPlus[V]`                 | `plus(a) -> V`           | —                    | ${}^+: V \to V$                                 |
|                       | `HasResiduals[V]`            | `lres`, `rres`           | —                    | $\backslash, /: V \times V \to V$               |
| **Norm & Inner Prod** | `HasNorm[V]`                 | `norm(v) -> float`       | —                    | $\|\cdot\|: V \to \mathbb{R}_{\ge 0}$           |
|                       | `HasInner[R, V]`             | `inner(u, v) -> R`       | —                    | $\langle \cdot, \cdot \rangle: V \times V \to R$ |
| **Order / Lattice**   | `HasJoin[V]`                 | `join(a, b) -> V`        | —                    | $\vee: V \times V \to V$                        |
|                       | `HasMeet[V]`                 | `meet(a, b) -> V`        | —                    | $\wedge: V \times V \to V$                      |
|                       | `HasBounds[V]`               | `bot -> V`, `top -> V`   | —                    | $\bot, \top \in V$                              |
|                       | `HasComplement[V]`           | `complement(a) -> V`     | —                    | $\neg: V \to V$                                 |
| **Domain-Agnostic**   | `HasIdentity[V]`             | `identity -> V`          | —                    | $e \in V$                                       |
|                       | `HasOp[V]`                   | `op(a, b) -> V`          | —                    | $\circ: V \times V \to V$                       |
| **Non-Associative**   | `HasBracket[V]`              | `bracket(a, b) -> V`     | —                    | $[\cdot, \cdot]: V \times V \to V$              |
| **Ideals, Basis & Derivation**| `HasContains[V]`     | `contains(x) -> bool`    | —                    | $\in: V \to \{\top, \bot\}$                     |
|                       | `HasReduce[V]`               | `reduce(x) -> V`         | —                    | $x \mapsto [x] \in R / I$                       |
|                       | `HasGenerator[V]`            | `generator -> V`         | —                    | $a \in R \text{ where } I = (a)$                |
|                       | `HasBasis[V]`                | `basis -> Sequence[V]`   | —                    | $\{g_1, \dots, g_m\} \subset R$                 |
|                       | `HasDerivation[V]`           | `diff(a, var_index=0) -> V` | —                 | $\partial_i: V \to V$ (Leibniz rule)            |
| **Categorical (`category`)** | `HasQuiver[Obj, Mor]` | `source(f)`, `target(f)` | —                    | $\mathrm{dom}, \mathrm{cod}: \mathrm{Hom} \to \mathrm{Obj}$ |
|                       | `HasCatId[Obj, Mor]`         | `id(x) -> Mor`           | —                    | $\mathrm{id}_x \in \mathrm{Hom}(x, x)$          |
|                       | `HasCompose[Mor]`            | `compose(f, g) -> Mor`   | —                    | $\circ: \mathrm{Hom} \times \mathrm{Hom} \to \mathrm{Hom}$ |
|                       | `HasMorInv[Mor]`             | `invert_path(f) -> Mor`  | —                    | $()^{-1}: \mathrm{Hom}(x, y) \to \mathrm{Hom}(y, x)$ |
|                       | `HasTerminal[Obj, Mor]`      | `terminal`, `to_terminal`| —                    | $\mathbf{1} \in \mathrm{Obj}, !_A: A \to \mathbf{1}$ |
|                       | `HasProducts[Obj, Mor]`      | `product`, `proj1`, `proj2`, `pair` | —         | $A \times B, \pi_1, \pi_2, \langle f, g \rangle$ |
|                       | `HasExponentials[Obj, Mor]`  | `exponential`, `eval_mor`, `curry`, `uncurry` | — | $B^A, \mathrm{eval}, \mathrm{curry}, \mathrm{uncurry}$ |
|                       | `HasMapObj[Obj, Obj_co]`     | `map_obj(x) -> Obj_co`   | —                    | $F_{\mathrm{Obj}}: \mathrm{Obj}(\mathcal{C}) \to \mathrm{Obj}(\mathcal{D})$ |
|                       | `HasMapMor[Mor, Mor_co]`     | `map_mor(f) -> Mor_co`   | —                    | $F_{\mathrm{Mor}}: \mathrm{Hom}(\mathcal{C}) \to \mathrm{Hom}(\mathcal{D})$ |

> [!NOTE]
> **Subclassing vs. Structural Duck-Typing (The Golem Safety Contract)**
> When subclassing `HasZeroPred`, `HasNeg`, or `HasInv`, Python inherits their default helper implementations (`is_zero`, `sub`, `div`). However, when using purely structural duck-typing without inheriting from the mixins, Python's `@runtime_checkable` `isinstance(obj, Protocol)` requires that **all** protocol attributes be present on the instance or class.

### Equational Law Witness Mixins (Pillar 2)

Alongside operational mixins (`Has*`), `algebrax.algebra` defines **10 lightweight Law Witness Mixins** that advertise equational axioms satisfied by a structure:

| Law Witness | Property / Witness Method | Axiom / Equational Law | Canonical Examples |
|:------------|:--------------------------|:-----------------------|:-------------------|
| `LawAssociative` | `is_associative -> True` | $(a \cdot b) \cdot c = a \cdot (b \cdot c)$ | Monoids, Groups, Semirings, Associative Algebras |
| `LawCommutative` | `is_commutative -> True` | $a \cdot b = b \cdot a$ | Abelian groups, Commutative rings, Fields |
| `LawAddAssociative` | `is_add_associative -> True` | $(a + b) + c = a + (b + c)$ | Additive semigroups, Monoids, Rings |
| `LawAddCommutative` | `is_add_commutative -> True` | $a + b = b + a$ | Additive commutative monoids, Abelian groups |
| `LawAnticommutative` | `is_anticommutative -> True` | $[a, b] = -[b, a]$ | Lie brackets, Poisson brackets, Malcev algebras |
| `LawIdempotent` | `is_idempotent -> True` | $a \oplus a = a$ | Tropical semiring $(\min, +)$, Boolean $(\lor, \land)$, Lattices |
| `LawLie` | `is_lie -> True` | Jacobi identity $[[x, y], z] + [[y, z], x] + [[z, x], y] = \mathbf{0}$ | Lie algebras $\mathfrak{g}$, Poisson brackets |
| `LawJordan` | `is_jordan -> True` | $(a \circ b) \circ a^2 = a \circ (b \circ a^2)$ | Jordan algebras, Symmetric quantum observables |
| `LawAlternative` | `is_alternative -> True` | $(a \cdot a) \cdot b = a \cdot (a \cdot b)$ and $(b \cdot a) \cdot a = b \cdot (a \cdot a)$ | Octonions $\mathbb{O}$, Cayley–Dickson algebras |
| `LawMalcev` | `is_malcev -> True` | $J(x, y, x \cdot z) = J(x, y, z) \cdot x$ | Imaginary octonions $\operatorname{Im}(\mathbb{O})$ |

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
* **Topological Fundamental Groupoid $\Pi_1(K)$**: `SimplicialPathGroupoid` in `algebrax.topology` models edge paths $(v_0, \dots, v_n)$ modulo 1-simplex backtracking $(u, v, u) \sim (u,)$ and 2-simplex face homotopies $(u, v, w) \sim (u, w)$.
* **Cartesian Closed Categories & Coeffects (`algebrax.category`)**: `CartesianClosedCategory` and `FiniteSetCCC` model products $A \times B$, exponentials $C^B$, and the Curry–Howard–Lambek currying adjunction, while `CoeffectContext` and `SemiringCoeffectTracker` grade variable-usage contexts over any semiring.
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
* **`algebraic`**: `DualNumberAlgebra` (Star semiring), `BinomialConvolutionSemiring`, `MultivariateBinomialConvolutionSemiring`, `MonoidAlgebraSemiring`, `PolynomialAlgebra`, `KnotSemiring`, `ProvenanceSemiring`, `QuotientMonoidAlgebraSemiring`, `CliffordAlgebra` ($Cl(p,q,r)$ geometric algebras and Spacetime Dirac spinors), `GeneralizedCliffordAlgebra`, `QuantumCliffordAlgebra`, `GaloisField`. Free & quotient monoid algebras, divided power polynomial rings, skein modules, Clifford multivectors, finite fields.

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

**Examples in Library** (`algebrax.algebra`): `StandardField(Fraction)` ($\mathbb{Q}$), `StandardField(float)` ($\mathbb{R}$), `StandardField(complex)` ($\mathbb{C}$), `ModularField(p)` ($\mathbb{F}_p$), `GaloisField(p, irreduc_poly)` ($\mathrm{GF}(p^m)$), and `PAdicField(p)` ($\mathbb{Q}_p$).

### 8. Algebra (over a Field)

A Vector Space equipped with a bilinear product.

* Elements can be added and scaled (Vector Space).
* Elements can be multiplied (Ring-like).

**Example**: The set of $N \times N$ matrices, `PolynomialAlgebra`, `MultivariatePolynomialAlgebra`, and `CliffordAlgebra`.

### 9. Homomorphisms, Ideals & Canonical Quotients (`algebrax.algebra`)

An **Ideal** $I \triangleleft R$ is an additive subgroup of a ring $R$ that *absorbs* multiplication ($\forall x \in I, r \in R \implies r \cdot x \in I \text{ and } x \cdot r \in I$). Ideals arise universally as the **kernels** of structure-preserving **homomorphisms** $\phi: R \to S$:

$$\ker \phi = \{x \in R \mid \phi(x) = \mathbf{0}_S\}, \qquad R / \ker \phi \cong \operatorname{im} \phi \quad (\text{First Isomorphism Theorem})$$

* **Homomorphism Protocols**: `Homomorphism[Dom, Cod]`, `RingHom[Dom, Cod]`, `GroupHom[Dom, Cod]`, `LinearMap[R, Dom, Cod]`, `LieAlgebraHom[Dom, Cod]`, and `CallableHomomorphism`.
* **Ideal Protocols & Implementations**: `Ideal[V]`, `LeftIdeal[V]`, `RightIdeal[V]`, `PrincipalIdeal[V]`, `FinitelyGeneratedIdeal[V]`, `LieIdeal[V]`, `IntegerModuloIdeal(n)`, `PolynomialTruncationIdeal(n)`, `NilpotentIdeal(k)`, `KernelIdeal(hom, cod_ring, reducer)`, `GroebnerIdeal(ring, generators)`, and `SubspaceLieIdeal(keys)`.
* **Canonical Unboxed Quotients**: `QuotientSemiring(semiring, ideal)`, `QuotientRing(ring, ideal)`, and `QuotientAlgebra(algebra, ideal)` evaluate operations on unboxed coset representatives via `ideal.reduce(x)` with zero heap-wrapper overhead, while `MonoidAlgebraSemiring` $\to$ `MonoidAlgebra` and `QuotientMonoidAlgebraSemiring` $\to$ `QuotientMonoidAlgebra` provide free and in-loop basis-rewriting monoid semirings and algebras.

### 10. Clifford Algebra (Geometric & Quantum Generalizations)

An associative algebra equipped with a quadratic form or root-of-unity commutation rule, unifying scalars, vectors, and higher-order blades (bivectors, trivectors).

* **Standard Clifford / Geometric Algebra $Cl(p, q, r)$**: $\mathbf{e}_i \mathbf{e}_j = -\mathbf{e}_j \mathbf{e}_i$ ($i \ne j$), $\mathbf{e}_i^2 \in \{+1, -1, 0\}$, with geometric product $ab = a \cdot b + a \wedge b$. Generalizes complex numbers, quaternions, and Dirac spinors.
* **Generalized Clifford Algebra (GCA) $C_n^{(m)}$**: Clock-and-shift commutation $\mathbf{e}_j \mathbf{e}_k = \omega \mathbf{e}_k \mathbf{e}_j$ ($j < k$) where $\omega = \exp(2\pi i / n)$ is a primitive $n$-th root of unity and $\mathbf{e}_j^n = \alpha_j \mathbf{1}$.
* **$q$-Deformed Quantum Clifford Algebra $Cl_q(m)$**: Braided quantum deformation $\mathbf{e}_j \mathbf{e}_k = -q \mathbf{e}_k \mathbf{e}_j$ ($j < k$).

### 11. Non-Associative & Bracket Algebras (`algebrax.algebra`, `algebrax.lie`)

Dropping multiplication associativity yields rich symmetry and physical algebras characterized by **Law Witness Mixins** (`LawLie`, `LawJordan`, `LawAlternative`, `LawMalcev`, `LawAnticommutative`):

* **Lie Algebra ($\mathfrak{g}, [\cdot, \cdot]$)**: Anticommutative bracket $[x, y] = -[y, x]$ satisfying the **Jacobi identity** $[[x, y], z] + [[y, z], x] + [[z, x], y] = \mathbf{0}$ (`LieAlgebra`). Infinitesimal generator of continuous Lie groups.
* **Poisson Algebra ($A, \cdot, \{\cdot, \cdot\}$)**: Commutative associative algebra equipped with a Lie bracket obeying the **Leibniz derivation law** $\{f, gh\} = \{f, g\}h + g\{f, h\}$ (`PoissonAlgebra`, realized by `MultivariatePolynomialAlgebra` on canonical phase-space coordinates).
* **Jordan Algebra ($J, \circ$)**: Commutative product satisfying the **Jordan identity** $(x \circ y) \circ x^2 = x \circ (y \circ x^2)$ (`JordanAlgebra`, `SymmetricMatrixJordanAlgebra` with $A \circ B = \frac{1}{2}(AB + BA)$).
* **Alternative & Malcev Algebras**: Artin alternativity $(xx)y = x(xy)$ and $(yx)x = y(xx)$ realized by the 8-dimensional **Octonions** (`OctonionAlgebra`), whose pure-imaginary commutator subspace satisfies the **Malcev identity** (`ImaginaryOctonionMalcevAlgebra`).

---

## Commutative Algebra, Multivariate Polynomials & Exact Gröbner Ideals

The `algebrax.algebra` module implements unboxed sparse multivariate polynomial rings $k[x_1, \dots, x_n]$ and canonical ideal decision procedures over any **exact `Field[V]`** (`StandardField(Fraction)`, `ModularField(p)`, `GaloisField`):

* **Sparse Multivariate Polynomials (`MultivariatePolynomialAlgebra[V]`)**: Represents elements as unboxed exponent-tuple mappings `dict[tuple[int, ...], V]` under admissible monomial orderings (`grevlex`, `grlex`, `lex`). Satisfies `CommRing`, `Algebra`, `HasDerivation` (formal algebraic partial derivatives $\partial/\partial x_i$, exact univariate GCD, and characteristic-aware `square_free_part` with Frobenius $p$-th root extraction), and `PoissonAlgebra` (canonical symplectic Poisson bracket $\{f, g\}$).
* **Exact Gröbner Bases (`groebner_basis`, `GroebnerIdeal`)**: Computes canonical reduced monic Gröbner bases via Gebauer–Möller-filtered **Buchberger** and **Faugère $F_4$** (sparse Macaulay matrix RREF), strictly rejecting IEEE-754 floating-point fields (`TypeError`) to prevent catastrophic S-polynomial cancellation. Implements `FinitelyGeneratedIdeal` (`HasBasis`, `HasContains`, `HasReduce`), composing directly with `QuotientRing(ring, ideal)` to form exact coordinate rings $k[x_1, \dots, x_n]/I$.

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

`GaloisField` (canonical in `algebrax.algebra`, re-exported in `algebrax.galois` and `algebrax.semiring`) implements the exact finite extension field $\mathrm{GF}(p^m) \cong \mathbb{F}_p[x] / \langle P(x) \rangle$ over `QuotientMonoidAlgebraSemiring`. Elements are represented as sparse polynomial vectors `{exponent: coeff}` modulo an irreducible polynomial $P(x)$.

* **Exact Field Arithmetic**: Addition, negation/subtraction, multiplication modulo $P(x)$ (e.g. $x^8 + x^4 + x^3 + x + 1$ for AES $\mathrm{GF}(2^8)$), and exact multiplicative inversion (`inv`/`div`) via the polynomial Extended Euclidean Algorithm.
* **Matrix Arithmetic & Polynomials**: `algebrax.galois.gf_matrix_mul()` computes sparse matrix multiplication for cryptographic MixColumns transformations and Reed–Solomon generator matrices, while `MultivariatePolynomialAlgebra(GaloisField(...))` supports exact polynomials and Gröbner ideals over $\mathrm{GF}(p^m)$.

---

## Category Theory, $\mathbf{Mat}(\mathcal{S})$ & Lawvere Metric Spaces

The `algebrax.category` module formalizes Lean 4 Mathlib-aligned category theory, functorial duality, and enriched matrix mechanics (`EP-0200`):

* **Category & Functor Protocols**: `Category[Obj, Mor]`, `Functor[Obj, Mor, Obj_co, Mor_co]`, and `OppositeCategory[Obj, Mor]` ($\mathcal{C}^{\mathrm{op}}$), verified via `verify_category_laws()` and `verify_functor_laws()`.
* **The Matrix Category $\mathbf{Mat}(\mathcal{S})$ (`MatrixCategory`)**: Finite index sets are objects and unboxed sparse matrices `dict[K, dict[K, V]]` are morphisms, with `TransposeFunctor` realizing the duality isomorphism $\mathbf{Mat}(\mathcal{S})^{\mathrm{op}} \xrightarrow{\sim} \mathbf{Mat}(\mathcal{S})$ and `SemiringChangeOfBaseFunctor` mapping matrices across semiring homomorphisms.
* **Lawvere Metric Spaces (`LawvereMetricCategory`)**: Realizes Lawvere's theorem that a generalized directed metric space $(X, d)$ is a category enriched over `TropicalSemiring` $\langle [0, \infty], \min, +, \infty, 0 \rangle$, where composition is the triangle inequality $d(x, y) + d(y, z) \ge d(x, z)$ and `metric_closure()` computes all-pairs shortest paths via Kleene star.
* **Kleisli Monadic Composition & Kan Extensions**: `kleisli_compose()` and `kan_extension_left()` over monadic transition matrices.

---

## Coalgebras, Bialgebras & Hopf Algebras (Quantum Symmetries & Duality)

The `algebrax.algebra` and `algebrax.topology` modules complete the arrow-reversal categorical duality of algebraic structures (`EP-0206`):

* **Coalgebra Protocol (`Coalgebra[R, C]`)**: Reverses the multiplication arrow, decomposing states via comultiplication $\Delta: C \to C \otimes C$ and counit $\epsilon: C \to R$ satisfying coassociativity $(\Delta \otimes \mathrm{id})\Delta = (\mathrm{id} \otimes \Delta)\Delta$ and counitality $(\epsilon \otimes \mathrm{id})\Delta = \mathrm{id} = (\mathrm{id} \otimes \epsilon)\Delta$.
* **Bialgebra Protocol (`Bialgebra[R, C]`)**: Unifies algebra and coalgebra structures such that $\Delta$ and $\epsilon$ are algebra homomorphisms.
* **Hopf Algebra Protocol (`HopfAlgebra[R, C]`)**: Equips a bialgebra with an antipode $S: H \to H$ (the quantum inverse) satisfying $\mu \circ (S \otimes \mathrm{id}) \circ \Delta = \eta \circ \epsilon = \mu \circ (\mathrm{id} \otimes S) \circ \Delta$.
* **Group Hopf Algebras (`GroupHopfAlgebra`)**: Group convolution ring $R[G]$ with group-like coproduct $\Delta(g) = g \otimes g$, counit $\epsilon(g) = 1$, and antipode $S(g) = g^{-1}$.
* **Alexander-Whitney Simplicial Coalgebra (`SimplicialChainCoalgebra`)**: Evaluates the diagonal approximation on simplicial chains $\Delta(\sigma) = \sum \sigma[:i] \otimes \sigma[i-1:]$, establishing exact linear duality with the simplicial cohomology cup product $\langle \alpha \smile \beta, \sigma \rangle = \langle \alpha \otimes \beta, \Delta(\sigma) \rangle$.
* **Divided Power Coalgebras (`DividedPowerCoalgebra`)**: Binomial degree-splitting $\Delta(x^{[n]}) = \sum_{k=0}^n x^{[k]} \otimes x^{[n-k]}$ governing moment sequences.

---

## Topological K-Theory, Grothendieck Groups & Characteristic Classes

The `algebrax.algebra` and `algebrax.topology` modules formalize the universal completion of commutative monoids and vector bundle semirings into abelian groups and rings of virtual bundles (`EP-0207`):

* **Universal Grothendieck Group & Ring (`GrothendieckGroup[M]`, `GrothendieckRing[M]`)**: Left adjoint functor converting any additive commutative monoid $(M, +, 0)$ into an abelian group $K_0(M)$ of formal differences $[a] - [b]$ under stabilized equivalence $a + d + k = b + c + k$, lifting any monoid homomorphism $f: M \to G$ uniquely via `lift_homomorphism`.
* **Vector Bundle Semiring & Virtual Bundle Ring (`TopologicalKTheoryRing`)**: Equips discrete orthogonal gauge connections (`DiscreteOrthogonalConnection`) with Whitney direct sums $E_1 \oplus E_2$ (`bundle_direct_sum`, block-diagonal transport) and Kronecker tensor products $E_1 \otimes E_2$ (`bundle_tensor_product`), completing them into the commutative ring $K^0(K)$ of virtual bundles $[E] - [F]$.
* **Discrete Chern Character & Quantized Topological Charge (`chern_character`, `first_chern_number`)**: Maps 2-face curvature holonomy angles into simplicial cohomology classes $(\mathrm{ch}_0, \mathrm{ch}_1, \mathrm{ch}_2)$ satisfying Whitney sum additivity $\mathrm{ch}(E_1 \oplus E_2) = \mathrm{ch}(E_1) + \mathrm{ch}(E_2)$ and exact integer quantization $\int_\Sigma c_1(E) \in \mathbb{Z}$ over closed oriented 2-surfaces.

---

## Lie Algebras, Root Systems & Continuous Symmetries (`algebrax.lie`)

Whereas finite groups capture discrete symmetries, **continuous Lie groups** $G$ (rotations $\mathrm{SO}(3)$, unitary gauge symmetries $\mathrm{SU}(N)$, rigid-body motions $\mathrm{SE}(3)$) are governed infinitesimally by their tangent space at the identity — a **Lie Algebra** $\mathfrak{g} = T_e G$ equipped with the commutator bracket $[X, Y]$:

* **Sparse Structure Constants & Invariants (`LieAlgebra`)**: Represents elements as unboxed sparse basis maps `dict[K, V]` with structure constants $[e_i, e_j] = \sum_k f_{ij}^k e_k$. Computes the **adjoint representation** $\operatorname{ad}_X(Y) = [X, Y]$ (`adjoint_matrix()`), the **Killing form** $B(X, Y) = \operatorname{Tr}(\operatorname{ad}_X \circ \operatorname{ad}_Y)$ (`killing_form()`), and **Cartan's semisimplicity criterion** (`is_semisimple()`).
* **Classical & Exceptional Families**: Built-in factories for classical algebras (`so_n`, `su_n`, `sl_n`, `sp_n`, `u_n`, `se_n`), Clifford bivector spin algebras (`clifford_lie_algebra`, witnessing $\mathfrak{spin}(3) \cong \mathfrak{so}(3)$), and **Cartan–Killing root systems** (`RootSystem.from_dynkin` + `chevalley_lie_algebra`) covering all classical ($A_n, B_n, C_n, D_n$) and exceptional ($G_2, F_4, E_6, E_7, E_8$) Dynkin diagrams.
* **The Lie Algebra $\leftrightarrow$ Lie Group Bridge (BCH & Exponential Map)**: `algebrax` connects infinitesimal generators $X, Y \in \mathfrak{g}$ to local group composition $\exp(X)\exp(Y) = \exp(Z) \in G$ via the **Baker–Campbell–Hausdorff series** (`LieAlgebra.bch(x, y, order=...)`), matrix exponentials on Lie representations (`ExplicitLieRep.exp_map()`), and spinor rotors $R = \exp(-\frac{\theta}{2}\mathbf{B})$ in `algebrax.clifford`.

---

## Representation Theory, Invariants, Quantum Groups & Quivers (`algebrax.rep`)

Representation theory linearizes abstract symmetries — turning groups, Lie algebras, and directed quivers into concrete sparse linear operators and decompositions:

* **Finite Group Characters & Schur Projectors (`algebrax.rep.group`)**: `GroupRepresentation`, `ExplicitGroupRep`, `CharacterTable` (built-in for $C_n, D_{2n}, S_3, S_4, A_4, Q_8$), Schur orthogonality (`character_inner_product`), `is_intertwiner`, `reynolds_average`, and orthogonal `isotypic_projector` decompositions into irreducible subspaces.
* **Induction & Mackey Theory (`algebrax.rep.induction`)**: `induced_representation` ($\operatorname{Ind}_H^G$), `restrict_representation` ($\operatorname{Res}_H^G$), Frobenius reciprocity adjointness, and `mackey_decomposition` / `mackey_intertwining_number`.
* **Lie Representations & Tensor Coupling (`algebrax.rep.lie`)**: `LieRepresentation`, `ExplicitLieRep` (with `exp_map()`), `spin_representation`, `weight_space_decomposition`, `highest_weight_vectors`, `quadratic_casimir` & `cubic_casimir_operator`, and exact Condon–Shortley **Clebsch–Gordan** coupling (`clebsch_gordan_coefficient`, `clebsch_gordan_matrix`, `clebsch_gordan_tensor`).
* **Invariant Theory (`algebrax.rep.invariant`)**: Exact `compute_molien_series` ($M_G(t) = \frac{1}{|G|} \sum_{g \in G} \det(I - t\rho(g))^{-1}$), `reynolds_polynomial_operator`, and `invariant_basis_at_degree` for constructing symmetry-equivariant polynomial bases.
* **Quantum Groups & Knot Invariants (`algebrax.rep.quantum`)**: $q$-deformed enveloping algebra `QuantumSL2` ($U_q(\mathfrak{sl}_2)$), `universal_r_matrix_sl2_fundamental` satisfying the Quantum Yang–Baxter Equation, `braiding_operator` / `braid_to_matrix`, `quantum_trace`, and `jones_polynomial_eval`.
* **Quiver Representations & Gabriel's ADE Theorem (`algebrax.rep.quiver`)**: `Quiver`, `QuiverRepresentation`, `PathAlgebra` ($KQ$), `tits_quadratic_form`, `classify_representation_type` (finite ADE, tame Euclidean, wild), `gabriel_positive_roots`, BGP reflection functors (`bgp_reflect_dimension`), and bidirectional sheaf bridge (`to_cellular_sheaf`, `from_cellular_sheaf`).

---

## Langlands Duality, Ramanujan Expanders & $p$-Adic Valuations

Connecting Lie theory, spectral graph theory, and non-archimedean arithmetic (`EP-0209`):

* **Langlands Root Duality & Iwahori–Hecke Algebras (`algebrax.lie`)**: `langlands_dual_root_system()` constructs $\Phi^\vee$ via Cartan transposition $A^\vee = A^T$ and coroot inversion $\alpha^\vee = \frac{2\alpha}{\langle \alpha, \alpha \rangle}$ (`coroot_in_dual()`), exchanging $B_n \leftrightarrow C_n$ while preserving simply-laced types; `IwahoriHeckeAlgebra` $q$-deforms Weyl group algebras via $(T_i - q)(T_i + 1) = 0$.
* **Ramanujan Expander Graphs & Graph Hecke Operators (`algebrax.analysis`)**: `is_ramanujan_graph()` tests the optimal Alon–Boppana spectral bound $\max_{|\lambda_i| < d} |\lambda_i| \le 2\sqrt{d - 1}$ on $d$-regular graphs, while `hecke_graph_operator()` generates the commuting ring of non-backtracking walk operators $T_k$.
* **Unboxed $p$-Adic Fields (`PAdicField` in `algebrax.algebra`)**: Implements exact $\mathbb{Q}_p$ arithmetic over unboxed sparse Laurent mappings `dict[int, int]` with Hensel-lifted inverses, non-archimedean ultrametric norm $|x + y|_p \le \max(|x|_p, |y|_p)$, and valuation $v_p(x)$ mapping multiplicatively into `TropicalSemiring`.

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
