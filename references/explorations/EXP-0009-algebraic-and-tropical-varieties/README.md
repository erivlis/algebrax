# EXP-0009: Algebraic & Tropical Varieties — Exact Quotients, Companion Matrices & Polyhedral Duals

| Field           | Value                                                                                                                                                                                             |
|:----------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0009                                                                                                                                                                                              |
| **Title**       | Algebraic & Tropical Varieties — Exact Quotients, Companion Matrices & Polyhedral Duals                                                                                                           |
| **Author**      | Eran Rivlis & Antigravity (Principal Architect & Grand Council)                                                                                                                                   |
| **Status**      | Concluded                                                                                                                                                                                         |
| **Type**        | Architectural & Research Exploration                                                                                                                                                              |
| **Created**     | 2026-11-14                                                                                                                                                                                        |
| **Updated**     | 2026-11-14                                                                                                                                                                                        |
| **Related EPs** | [EP-0001](../../../docs/proposals/EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md), [EP-0003](../../../docs/proposals/EP-0003-axiomatic-verification-and-property-based-testing.md), [EP-0004](../../../docs/proposals/EP-0004-unboxed-storage-and-sparse-carrier-invariance.md), [EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md), [EP-0214](../../../docs/proposals/EP-0214-invariant-theory-molien-series-casimir-polynomials.md), [EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md), [EP-0221](../../../docs/proposals/EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md), [EP-0222](../../../docs/proposals/EP-0222-tropical-varieties-and-polyhedral-duals.md) |

---

## 1. Abstract & Context

### 1.1 Context in AlgebraX
Following the formalization of algebraic ideals, homomorphisms, and canonical quotients in [EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md) (`Ideal`, `RingHom`, `QuotientRing`) and the polynomial invariant machinery proposed in [EP-0214](../../../docs/proposals/EP-0214-invariant-theory-molien-series-casimir-polynomials.md), AlgebraX possesses half of commutative algebra's foundational bridge:

1. **Unboxed Polynomial Carriers**: [`PolynomialAlgebra`](../../../src/algebrax/algebra/_polynomial.py) models univariate $R[x]$ as `dict[int, T]` on [`MonoidAlgebra`](../../../src/algebrax/algebra/_monoid_algebra.py).
2. **Ideal & Quotient Protocols**: [`Ideal`](../../../src/algebrax/algebra/_ideals.py) (`contains`, `reduce`) and [`QuotientRing`](../../../src/algebrax/algebra/_quotient.py) provide zero-allocation normal-form arithmetic for $R/I$, yet concrete ideals are currently limited to 1D/subspace cases (`IntegerModuloIdeal`, `PolynomialTruncationIdeal`, `NilpotentIdeal`, `SubspaceLieIdeal`).
3. **Exact Field Solvers & Semirings**: [`StandardField(Fraction)`](../../../src/algebrax/algebra/_field.py), [`ModularField(p)`](../../../src/algebrax/algebra/_field.py), [`galois`](../../../src/algebrax/galois.py), and [`TropicalSemiring`](../../../src/algebrax/semiring/optimization.py) already exist as first-class primitives.

Missing is the geometric dual: **Algebraic Varieties** $V(I) = \{p \in k^n \mid f(p) = 0 \;\forall f \in I\}$, multivariate polynomial rings $k[x_1, \dots, x_n]$, Gröbner-backed coordinate rings $k[V] = k[x_1, \dots, x_n] / I$, and their semiring-deformed cousins, **Tropical Varieties**.

### 1.2 The Core Question
> *Can AlgebraX support algebraic varieties natively in pure Python without becoming a slow SymPy clone, without succumbing to IEEE-754 cancellation or Buchberger's doubly-exponential blowup, and while exploiting AlgebraX's unique sparse `dict`, exact `Field`, and `TropicalSemiring` architecture?*

---

## 2. Exploration & Options Analysis

### 2.1 Literature & Ecosystem Survey
We surveyed four primary computational paradigms (archived in [`papers/`](./papers/) and indexed in [`sources/BIBLIOGRAPHY.md`](./sources/BIBLIOGRAPHY.md)):

1. **Classical Buchberger vs. F4 Matrix Reduction ([ALBRECHT-2010], [FAUGERE-1999])**:
   Classical Buchberger performs sequential AST/polynomial S-pair reductions. Faugère's $F_4$ algorithm replaces individual polynomial divisions with **simultaneous sparse Gaussian elimination (RREF)** on a Macaulay matrix of shifted reducers. In pure Python, where tight dictionary-row elimination maps cleanly onto sparse `dict` structures, $F_4$ directly leverages AlgebraX's sparse matrix paradigm.
2. **Stickelberger's Eigenvalue Theorem ([COX-2020], [BENDER-2021], [CLO-2005])**:
   For any 0-dimensional ideal $I \triangleleft k[x_1, \dots, x_n]$, the coordinate ring $k[V] = k[x_1, \dots, x_n]/I$ is a finite-dimensional $k$-vector space with monomial basis $\mathcal{B} = \{x^\alpha \notin \langle \mathrm{LT}(I) \rangle\}$. Multiplication by $x_i$ defines a linear operator $M_{x_i}: k[V] \to k[V]$ whose joint eigenvalues are the exact affine variety points $V(I)$. This converts nonlinear polynomial system solving into linear algebra.
3. **Finite-Field Varieties & Algebraic SAT**:
   Over $\mathbb{F}_p$ (`ModularField(p)`) or Boolean rings $\mathbb{F}_2[x_1,\dots,x_n]/(x_i^2 - x_i)$, coefficient swell disappears completely, enabling exact point counting (e.g. elliptic curves), algebraic coding theory, and exact SAT solving via Gröbner reduction.
4. **Tropical Algebraic Geometry ([RGST-2003])**:
   Replacing $(+, \times)$ with $(\min, +)$ (`TropicalSemiring`) on the *exact same* sparse polynomial carrier `dict[tuple[int, ...], T]` turns a polynomial into a piecewise-linear function $f_{\text{trop}}(w) = \min_\alpha (c_\alpha + \langle \alpha, w \rangle)$. Its tropical hypersurface $\mathcal{T}(f)$ (where the minimum is attained at least twice) is a **balanced polyhedral complex** dual to the regular subdivision of its Newton polytope — a domain unsupported by standard CAS polynomial engines like SymPy.

### 2.2 Comparative Trade-Offs of Implementation Options

| Option | Core Mechanism | Strengths | Weaknesses / Traps | Council Fit |
|:-------|:---------------|:----------|:-------------------|:------------|
| **Option 1: Naive Floating-Point Gröbner** | `StandardField(float)` + Buchberger | Fast numeric operations; accepts approximate input directly | **Catastrophic failure:** rounding noise creates false unit ideals $(1)$, or `tol` erases genuine small terms | **Rejected** (Violates Popper & Russell) |
| **Option 2: General-Purpose Pure-Python CAS** | Symbolic AST `Expr` + Buchberger | Broad symbolic familiarity | 100x slower than C/Singular (`FLINT`/`FGb`) on large ideals; heap-heavy AST boxing | **Rejected** (Violates Shannon) |
| **Option 3: Unboxed Exact `Field` + F4-RREF + Stickelberger + Tropical Dual** | `dict[tuple[int, ...], V]` carrier; exact `Field[V]` mandate; F4 sparse Macaulay RREF; `QuotientRing` companion matrices; `TropicalSemiring` polyhedral dual | Zero wrapper overhead; 100% `EP-0201` compatible; fast on low/medium-dim systems; unique Tropical capability; optional NumPy eigensolver Escape Hatch | Not intended for 15+ variable cryptographic Gröbner attacks (belongs in C/Rust); `F4` needs pair filtering to beat Buchberger on sparse $\mathbb{F}_p$ cases | **Accepted** |

### 2.3 Empirical Findings (`sources/prototype_varieties.py`)
We authored and executed [`sources/prototype_varieties.py`](./sources/prototype_varieties.py) (full output archived in [`raw/prototype_benchmark_output.txt`](./raw/prototype_benchmark_output.txt)) on Python 3.14.7 with differential verification against `sympy.groebner` as an external oracle:

#### Experiment 1: Floating-Point Cancellation Suicide vs. Exact Fields
* **Case A (IEEE-754 rounding residual, `tol=0.0`)**: Intersecting $3x + 2y = 5$, $\frac{3}{7}x + \frac{2}{7}y = \frac{5}{7}$, and $x^2 + y^2 = 2$:
  * `StandardField(Fraction)`: Exact Gröbner basis yielding the 2 exact points $(1, 1)$ and $(\frac{19}{13}, \frac{4}{13})$.
  * `StandardField(float, tol=0.0)`: Floating-point cancellation residual $\approx 10^{-16}$ becomes a spurious leading term and explodes to **`[{(0, 0): 1.0}]` (unit ideal $(1) \implies V(I) = \emptyset$)**.
* **Case B (Genuine small coefficient $10^{-14}$ with `tol=1e-12`)**: System $x^2 + y^2 - 1 = 0,\; x^2 + y^2 + 10^{-14}x - 1 = 0$:
  * `StandardField(Fraction)`: Exact 0-dimensional basis $\{x, y^2 - 1\}$ (2 points $(0, \pm 1)$).
  * `StandardField(float, tol=1e-12)`: Silently deletes $10^{-14}x$ and returns **`{(2, 0): 1.0, (0, 2): 1.0, (0, 0): -1.0}`**, falsely inflating a 0-dimensional variety into a 1-dimensional circle!

#### Experiment 2: Buchberger vs. F4-Sparse-RREF vs. SymPy Oracle
| Benchmark System | Buchberger | F4 Sparse RREF | SymPy Oracle | Oracle Match (B, F4) |
|:-----------------|:----------:|:--------------:|:------------:|:--------------------:|
| **Twisted Cubic** ($\mathbb{Q}$, `lex`) | `0.38 ms` ($S=5$) | `1.04 ms` (6 rounds, 28 rows) | `33.48 ms` | `(True, True)` |
| **Cyclic-3** ($\mathbb{Q}$, `grevlex`) | `0.75 ms` ($S=2$) | `1.70 ms` (4 rounds, 32 rows) | `1.60 ms` | `(True, True)` |
| **Cyclic-3** ($\mathbb{F}_{101}$, `grevlex`) | `0.44 ms` ($S=2$) | `1.42 ms` (4 rounds, 32 rows) | `1.46 ms` | `(True, True)` |
| **Cyclic-4** ($\mathbb{F}_{101}$, `grevlex`) | `3.87 ms` ($S=11$) | `11.11 ms` (7 rounds, 169 rows) | `10.48 ms` | `(True, True)` |
| **2R Planar Robot IK** ($\mathbb{Q}$, `grevlex`) | `16.56 ms` ($S=22$) | **`3.20 ms`** (5 rounds, 49 rows) | `14.12 ms` | `(True, True)` |

**Empirical Insight:** Both engines matched SymPy's reduced Gröbner basis **100% identically** across all 5 benchmarks. Crucially, on the 4-variable rational **2R Robot Inverse Kinematics** problem, F4 sparse Macaulay RREF outperformed classical Buchberger by **5.2x** (`3.20 ms` vs. `16.56 ms`) and outperformed SymPy by **4.4x** (`3.20 ms` vs. `14.12 ms`). Conversely, on ultra-sparse $\mathbb{F}_{101}$ Cyclic-4, Buchberger with Gebauer–Möller criteria outperformed unfiltered F4 (`3.87 ms` vs. `11.11 ms`) because F4 constructed 169 redundant Macaulay rows — confirming that production F4 must pair Macaulay RREF with Gebauer–Möller pair selection (as in [ALBRECHT-2010]).

#### Experiment 3: Coordinate Rings (`QuotientRing`) & Stickelberger Companion Matrices
* `GroebnerIdeal` satisfies `isinstance(ideal, Ideal) == True` and `QuotientRing(ring, ideal)` satisfies `isinstance(coord_ring, CommRing) == True` with **zero changes to `EP-0201`**.
* For $I = \langle x^2 + y^2 - 5,\; xy - 2 \rangle$: $\dim_{\mathbb{Q}}(\mathbb{Q}[V]) = 4$, exact commutator `[M_x, M_y] == {}` verified over $\mathbb{Q}$, and Stickelberger simultaneous diagonalization extracted all 4 exact points `[(-2, -1), (-1, -2), (1, 2), (2, 1)]` with **`0.00e+00` polynomial residual**.
* For **2R Planar Robot IK** ($L_1=2, L_2=1$, target $(2, 1)$): $\dim_{\mathbb{Q}}(\mathbb{Q}[V]) = 2$, extracting both exact elbow-up/elbow-down poses `(0.6, 0.8, 0.0, -1.0)` and `(1.0, 0.0, 0.0, 1.0)` directly from polynomial eigenvalues without trigonometry or initial guesses.

#### Experiment 4: Finite-Field Varieties & $\mathbb{F}_2$ Algebraic SAT
* **Elliptic Curve over $\mathbb{F}_7$** ($y^2 = x^3 + x + 1$): Yields 4 affine points ($\#E(\mathbb{F}_7) = 5$), satisfying Hasse's bound $|5 - 8| = 3 \le 2\sqrt{7} \approx 5.29$.
* **$\mathbb{F}_2$ 3-SAT**: Polynomial encoding over `ModularField(2)` with field equations $x_i^2 + x_i = 0$ yields reduced Gröbner basis `[x0 + x2, x1 + x2 + 1, x2^2 + x2]` and $\dim_{\mathbb{F}_2} = 2$, matching brute-force satisfying assignments `[(0, 1, 0), (1, 0, 1)]`.

#### Experiment 5: Tropical Varieties over `TropicalSemiring`
* Using the **exact same** `dict[tuple[int, ...], float]` polynomial carrier with `TropicalSemiring()` (`min`, `+`), a 2D tropical conic yields 4 tropical vertices `[(-1.0, 1.0), (1.0, -1.0), (1.0, 1.0), (2.0, 2.0)]`, each attaining its tropical minimum at 3 monomials simultaneously and satisfying **exact `(0, 0)` Noether vertex balancing residuals** across all 4 vertices.

---

## 3. Architectural Synthesis & Constraint Alignment

1. **Shannon (Unboxed Native Carriers — `EP-0004`)**:
   - Multivariate polynomials $k[x_1, \dots, x_n]$ require **zero AST node classes** or wrapper objects: the canonical carrier is `dict[tuple[int, ...], V]` (`SparseVector[tuple[int, ...], V]`) over `MonoidAlgebra[tuple[int, ...], V]`.
   - Coordinate ring elements in $k[V] = k[x_1, \dots, x_n]/I$ remain unboxed reduced dictionaries `ideal.reduce(f)`.
2. **Popper & Russell (Exact Field Mandate & Falsifiability — `EP-0003` / `EP-0005`)**:
   - Floating-point carriers (`float`, `complex`) MUST be **rejected at construction time** by `GroebnerIdeal` (raising `TypeError` or `ValueError` unless the scalar `Field[V]` is exact, e.g., `StandardField(Fraction)`, `ModularField(p)`, or `GaloisField`).
   - Every reduced Gröbner basis is falsifiable via Buchberger's S-polynomial criterion ($\forall g_i, g_j \in G,\; \overline{S(g_i, g_j)}^G = 0$) and differential verification against SymPy.
3. **Noether (Ideal–Variety Duality & Tropical Conservation)**:
   - Classical correspondence: `Ideal` $\leftrightarrow$ `AffineVariety`, `QuotientRing` $\leftrightarrow$ coordinate ring $k[V]$, and `RingHom` $\phi^*: k[W] \to k[V]$ $\leftrightarrow$ polynomial morphism $\phi: V \to W$.
   - Tropical correspondence: Dual Newton polytope subdivisions satisfy exact zero-sum balancing at every tropical vertex.
4. **Feynman (The Freshman Test — No Scheme Bloat)**:
   - Defer abstract Grothendieck schemes (`Spec`, ringed topoi) from the core API. Expose the clear geometric narrative: *equations $\to$ ideal $\to$ coordinate ring remainder arithmetic $\to$ exact/eigenvalue solutions or balanced tropical polyhedra*.
5. **The "Escape Hatch" Pattern (Zero-Dependency Core $\to$ Optional Acceleration)**:
   - **Pure-Python Core (Zero New Dependencies)**: Multivariate arithmetic, `GroebnerIdeal`, `QuotientRing`, finite-field point enumeration, exact companion matrices $M_{x_i}$, and tropical valuation/vertex extraction require **only pure Python + `mappingtools`**.
   - **Escape Hatch 1 (Eigenvalue Root Extraction)**: When extracting real/complex numerical coordinates of a 0-dimensional variety via Stickelberger's theorem, optionally bridge the sparse companion matrices $M_{x_i}$ to `numpy.linalg.eig` (when `numpy` is installed) or pure-Python QR/characteristic polynomial fallback for small dimensions.
   - **Escape Hatch 2 (Exact Rational Swell)**: For large integer/rational ideals, document multi-modular computation (`ModularField(p)` + Chinese Remainder Reconstruction) as an algorithmic escape hatch against intermediate coefficient blowup.

### 3.1 Cross-Continent Mathematical Synthesis (Why Phase 9 Unifies Phases 1–8)
During Council review, we identified seven deep mathematical bridges connecting `algebrax.variety` (`EP-0220`–`EP-0222`) to earlier AlgebraX continents:

| Connected Continent | Mathematical Bridge | Canonical Realization in AlgebraX | Placement |
|:--------------------|:--------------------|:----------------------------------|:----------|
| **Representation & Invariant Theory** ([`EP-0211`](../../../docs/proposals/EP-0211-lie-algebras-root-systems-and-killing-form.md), [`EP-0214`](../../../docs/proposals/EP-0214-invariant-theory-molien-series-casimir-polynomials.md)) | **GIT Quotient Varieties & Borel–Weil Flag Varieties**: The invariant subring $k[V]^G$ is the coordinate ring of the orbit space $V // G$, whose syzygy ideal $I_{\text{syz}}$ is an elimination ideal; irreducible representations of $G$ live on Grassmannians $\operatorname{Gr}(k, n)$ cut out by quadratic Plücker relations. | `syzygy_variety`, `plucker_grassmannian_variety`, `hilbert_function` | `EP-0221` (§1, §4) |
| **Topological & Algebraic K-Theory** ([`EP-0207`](../../../docs/proposals/EP-0207-topological-k-theory-and-characteristic-classes.md), [`EP-0165`](../../../docs/proposals/EP-0165-homology-and-betti-numbers.md)) | **Serre–Swan Equivalence, Schubert Calculus & Viro Patchworking**: Algebraic vector bundles over $V$ are idempotent matrices $P^2 \equiv P \pmod{I(V)}$ over $k[V]$; $H^*(\operatorname{Gr}(k, n))$ is a `QuotientRing` of Chern classes; tropical hypersurfaces export to `SimplicialComplex` for Betti numbers. | `is_serre_swan_projective_bundle`, `schubert_chern_cohomology_ring`, `motivic_point_count_homomorphism`, `to_simplicial_complex` | `EP-0221` (§5) & `EP-0222` (§2) |
| **Hopf Algebras & Quantum Groups** ([`EP-0206`](../../../docs/proposals/EP-0206-coalgebras-bialgebras-and-hopf-algebras.md)) | **Affine Algebraic Groups**: A linear algebraic group $G \subseteq \operatorname{GL}_n(k)$ (such as $\operatorname{SL}_n$ or $\operatorname{SO}_n$) is an affine variety whose coordinate ring $k[G] = k[x_{ij}]/I(G)$ is a commutative **Hopf Algebra** ($\Delta(x_{ij}) = \sum_k x_{ik} \otimes x_{kj}$, $\epsilon(x_{ij}) = \delta_{ij}$, $S(X) = X^{-1}$). | `CoordinateHopfAlgebra` | `EP-0221` (§4) |
| **Symplectic & Poisson Geometry** ([`EP-0204`](../../../docs/proposals/EP-0204-jordan-and-poisson-algebras.md)) | **Polynomial Phase Space & Symplectic Reduction**: On $k[q_1, \dots, q_m, p_1, \dots, p_m]$, formal partial derivatives `diff` define the canonical symplectic **Poisson bracket** $\{f, g\} = \sum_i (\frac{\partial f}{\partial q_i}\frac{\partial g}{\partial p_i} - \frac{\partial f}{\partial p_i}\frac{\partial g}{\partial q_i})$. | `MultivariatePolynomialAlgebra.poisson_bracket` | `EP-0220` (§2) |
| **Tensors & Quantum Entanglement** ([`EP-0108`](../../../docs/proposals/EP-0108-n-dimensional-tensors-and-decompositions.md), [`EP-0155`](../../../docs/proposals/EP-0155-clifford-geometric-algebra.md)) | **Segre & Spinor Varieties**: Rank-1 (unentangled) quantum states in $\mathbb{P}^a \times \mathbb{P}^b$ form the **Segre Variety** cut out by $2 \times 2$ minors $z_{ij}z_{kl} - z_{il}z_{kj} = 0$; pure spinors in `CliffordAlgebra` form the quadratic **Spinor Variety**. | Applied Showcase (constructed directly via `AffineVariety`) | `EP-0221` Recipes |
| **Probability & Algebraic Statistics** ([`EP-0107`](../../../docs/proposals/EP-0107-probabilistic-and-markov-algebra.md)) | **Toric Independence Varieties & Tropical Viterbi**: Statistical independence $P(X=i, Y=j) = P(X=i)P(Y=j)$ is the toric variety of $2 \times 2$ minors; the log-limit of sum-product (`ProbabilitySemiring`) is the tropical polynomial (`TropicalSemiring`). | Applied Showcase (constructed directly via `AffineVariety` & `TropicalHypersurface`) | `EP-0221` & `EP-0222` Recipes |
| **Automata & Prefix Tries** ([`EP-0174`](../../../docs/proposals/EP-0174-automata-and-algebraic-tries.md)) | **Janet / Monomial Division Tries**: Exponent tuples $(\alpha_1, \dots, \alpha_n) \in \mathbb{N}_0^n$ are strings over the coordinate alphabet; `AlgebraicTrie` indexes leading monomials for fast divisibility queries in `reduce_poly`. | Internal indexing note on `reduce_poly` | `EP-0220` (§2) |

> **Architectural Decision (Why No `EP-0223` Grab-Bag):** Per the Dennis Point and `EP-0001` (Tier 3 Core vs. Tier 4 Recipes), true algebraic primitives (`poisson_bracket` and `CoordinateHopfAlgebra`) are folded directly into `EP-0220` and `EP-0221`, while domain applications (Segre quantum entanglement and Algebraic Statistics) are delivered as Tier 4 `recipes/` rather than fragmenting Phase 9 into a low-cohesion catch-all EP.

---

## 4. The Verdict / Actionable Design

**Verdict: Approved for Phased Standards-Track Integration (`algebrax.variety`).**

1. **Tier Placement (`EP-0001`)**:
   - `MultivariatePolynomialAlgebra` and `GroebnerIdeal` extend Tier 2/3 foundational algebra in `algebrax.algebra` (`_polynomial.py`, `_ideals.py`).
   - `AffineVariety`, `CoordinateRing` helpers, Stickelberger companion matrix solvers, finite-field variety tools, and `TropicalHypersurface` live in a dedicated Tier 3 domain module **`algebrax.variety`**.
2. **Engine Strategy**:
   - Implement **both** Buchberger (with Gebauer–Möller criteria) and **F4-style sparse Macaulay RREF** (upgraded with Gebauer–Möller pair selection) behind a unified `groebner_basis(..., method='auto' | 'f4' | 'buchberger')` interface.
   - Enforce an explicit `ExactField` check so IEEE-754 floating-point silent corruption is impossible by construction.
3. **Unifying Classical & Tropical Geometry**:
   - Keep the `dict[tuple[int, ...], V]` polynomial representation identical across `MultivariatePolynomialAlgebra` (exact `Field[V]`) and `TropicalPolynomialSemiring` (`TropicalSemiring`), showcasing AlgebraX's semiring polymorphism in algebraic geometry.

---

## 5. Related Enhancement Proposals & Artifacts

### Resulting Phase 9 Standards-Track EPs
* [**`EP-0220`**: Multivariate Polynomial Algebra & Exact Gröbner Ideals](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md) — Generalizes `algebrax.algebra._polynomial` to `MultivariatePolynomialAlgebra`, monomial orderings (`lex`, `grlex`, `grevlex`), and `GroebnerIdeal` (Buchberger + Gebauer–Möller $F_4$ sparse RREF) over exact fields.
* [**`EP-0221`**: Affine Algebraic Varieties, Coordinate Rings & Stickelberger Solvers](../../../docs/proposals/EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) — Introduces `algebrax.variety` (`AffineVariety`, coordinate ring $k[V]$ via `QuotientRing`, `RingHom` pullbacks, Stickelberger companion matrix solvers, $\mathbb{F}_p$/$\mathbb{F}_2$ variety enumeration, and syzygy links to [EP-0214](../../../docs/proposals/EP-0214-invariant-theory-molien-series-casimir-polynomials.md)).
* [**`EP-0222`**: Tropical Varieties, Newton Polytopes & Balanced Polyhedral Complexes](../../../docs/proposals/EP-0222-tropical-varieties-and-polyhedral-duals.md) — Tropical polynomials on `dict[tuple[int, ...], float]` over `TropicalSemiring`, Newton polytope subdivisions, balanced tropical hypersurfaces, and `algebrax.topology` bridges.

### Bundled Compendium Artifacts
* [`sources/prototype_varieties.py`](./sources/prototype_varieties.py) — Executable pure-Python prototype & benchmark suite covering all 5 experiments and SymPy differential verification.
* [`raw/prototype_benchmark_output.txt`](./raw/prototype_benchmark_output.txt) — Exact captured stdout from executing the prototype on Python 3.14.7.
* [`sources/BIBLIOGRAPHY.md`](./sources/BIBLIOGRAPHY.md) — Annotated bibliography of primary papers and textbooks.
* [`papers/`](./papers/) — Archived open-access arXiv PDFs ([ALBRECHT-2010], [COX-2020], [BENDER-2021], [RGST-2003]).
