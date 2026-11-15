# EXP-0011: Differential & Ore Algebras — Weyl D-Modules, Skew Polynomials, Hermite Integration & Taylor Jets

| Field           | Value                                                                                                                                                                                                                                   |
|:----------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0011                                                                                                                                                                                                                                    |
| **Title**       | Differential & Ore Algebras — Weyl D-Modules, Skew Polynomials, Hermite Integration & Taylor Jets                                                                                                                                       |
| **Author**      | Eran Rivlis & Antigravity (Principal Architect & Grand Council)                                                                                                                                                                         |
| **Status**      | Concluded                                                                                                                                                                                                                               |
| **Type**        | Architectural & Research Exploration                                                                                                                                                                                                    |
| **Created**     | 2026-11-14                                                                                                                                                                                                                              |
| **Updated**     | 2026-11-14                                                                                                                                                                                                                              |
| **Related EPs** | [EP-0001](../../../docs/proposals/EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md), [EP-0003](../../../docs/proposals/EP-0003-axiomatic-verification-and-property-based-testing.md), [EP-0004](../../../docs/proposals/EP-0004-unboxed-storage-and-sparse-carrier-invariance.md), [EP-0005](../../../docs/proposals/EP-0005-equational-theories-and-typeclass-axioms.md), [EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md), [EP-0204](../../../docs/proposals/EP-0204-non-associative-quantum-algebras-jordan-octonions-poisson.md), [EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md), [EP-0231](../../../docs/proposals/EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md) |

---

## 1. Abstract & Context

### 1.1 Context in AlgebraX
Through Phases 1–10, AlgebraX has built the complete **commutative**, **discrete**, **categorical**, and **spectral** algebraic machinery, yet remains silent on **algebraic analysis** (calculus done purely via algebraic derivations, recurrences, and operator ideals without floating-point limits):

1. **Derivation Mixin Ready**: [EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md) introduced `HasDerivation[V]` (`diff`) in `src/algebrax/algebra/_mixins.py` alongside `MultivariatePolynomialAlgebra` and the canonical symplectic `poisson_bracket` ([EP-0204](../../../docs/proposals/EP-0204-non-associative-quantum-algebras-jordan-octonions-poisson.md)).
2. **Polynomial & Quotient Substrate Already Exists**: [`PolynomialAlgebra`](../../../src/algebrax/algebra/_polynomial.py), [`PolynomialTruncationIdeal`](../../../src/algebrax/algebra/_ideals.py), [`QuotientRing`](../../../src/algebrax/algebra/_quotient.py), and exact fields ([`StandardField(Fraction)`](../../../src/algebrax/algebra/_field.py), [`ModularField(p)`](../../../src/algebrax/algebra/_field.py)) already execute exact sparse polynomial and truncated quotient arithmetic with zero AST boxing.
3. **Shift & Difference Bridge from Phase 10**: [EP-0231](../../../docs/proposals/EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md) models linear shift-invariant operators via polynomial quotients; the dual operator perspective replaces fixed finite cyclic shifts with general **Ore skew-polynomials** $R[\partial; \sigma, \delta]$ governing arbitrary linear ODEs, difference recurrences, and $q$-difference equations simultaneously.

Missing is the continent of **Differential & Ore Algebra**: non-commutative Weyl algebras $A_n(k)$ (canonical quantization $[\partial_i, x_j] = \delta_{ij}$), unified Ore skew-polynomial rings $R[\partial; \sigma, \delta]$ for $D$-finite holonomic closure (`gcrd`, `lclm`), exact algebraic rational integration via Hermite reduction & creative telescoping, exact algebraic ODE solving in Taylor Jet algebras $k[x]/\langle x^{r+1} \rangle$, and **Differential Galois Theory** (Picard–Vessiot extensions, symmetric powers $\operatorname{Sym}^k(L)$, Kovacic factorization, and $\operatorname{SL}_2$ non-Liouvillian obstruction proofs).

### 1.2 The Core Question
> *Can AlgebraX formalize Differential Rings, non-commutative Weyl $D$-modules, unified Ore skew-polynomial algebras, exact symbolic integration (Hermite reduction & creative telescoping), arbitrary-order Taylor Jet ODE solvers, and bounded-order Differential Galois Theory using unboxed sparse dictionary carriers and exact `Field` arithmetic—without turning into a slow symbolic expression-tree CAS (`SymPy`) or sacrificing numerical stability?*

---

## 2. Exploration & Options Analysis

### 2.1 Literature & Ecosystem Survey
We surveyed primary computational paradigms (archived in [`papers/`](./papers/) and indexed in [`sources/BIBLIOGRAPHY.md`](./sources/BIBLIOGRAPHY.md)):

1. **Weyl Algebras & Holonomic $D$-Modules ([SATTELBERGER-2019], [SST-2000])**:
   The $n$-th Weyl algebra $A_n(k) = k\langle x_1, \dots, x_n, \partial_1, \dots, \partial_n \rangle / \langle [\partial_i, x_j] - \delta_{ij}, [x_i, x_j], [\partial_i, \partial_j] \rangle$ represents polynomial-coefficient partial differential operators in canonical normal-ordered form $\sum_{\alpha, \beta} c_{\alpha, \beta} x^\alpha \partial^\beta$. Non-commutative multiplication obeys the explicit Leibniz rule:
   $$(x^\alpha \partial^\beta)(x^u \partial^v) = \sum_{\mathbf{0} \le \kappa \le \min(\beta, u)} \binom{\beta}{\kappa}\binom{u}{\kappa} \kappa!\; x^{\alpha + u - \kappa} \partial^{\beta + v - \kappa}$$
   Left ideals $I \subseteq A_n(k)$ annihilating special functions $f$ admit non-commutative left Gröbner bases under Bernstein weight $(1, 1)$ (generalizing `GroebnerIdeal` from [EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md)), turning differential identity proving into left-ideal remainder testing ($\overline{L}^G = 0$).

2. **Unified Ore Skew-Polynomial Algebras $R[\partial; \sigma, \delta]$ ([KAUERS-2013])**:
   Given any commutative base ring/field $R$, an injective ring endomorphism $\sigma: R \to R$, and a $\sigma$-derivation $\delta: R \to R$ satisfying the twisted Leibniz rule $\delta(ab) = \sigma(a)\delta(b) + \delta(a)b$, the **Ore polynomial ring** $R[\partial; \sigma, \delta]$ is governed by the single skew commutation law:
   $$\partial \cdot r = \sigma(r)\,\partial + \delta(r)$$
   This single algebraic abstraction unifies three seemingly disjoint worlds:
   - **Differential Operators ($\mathbb{Q}[x][\partial_x]$)**: $\sigma = \mathrm{id},\; \delta = \frac{d}{dx} \implies \partial_x x = x \partial_x + 1$.
   - **Shift / Recurrence Operators ($\mathbb{Q}[n][S_n]$)**: $\sigma(p(n)) = p(n+1),\; \delta = 0 \implies S_n n = (n + 1) S_n$.
   - **$q$-Difference Operators ($\mathbb{Q}[x][D_q]$)**: $\sigma(p(x)) = p(qx),\; \delta = 0 \implies D_q x = q x D_q$.
   Non-commutative right Euclidean division gives `gcrd` (Greatest Common Right Divisor) and `lclm` (Least Common Left Multiple), implementing **effective $D$-finite closure**: if $L_1(f) = 0$ and $L_2(g) = 0$, then $\operatorname{lclm}(L_1, L_2)$ automatically annihilates $f + g$.

3. **Exact Symbolic Integration via Hermite Reduction & Creative Telescoping ([BOSTAN-2018], [KOUTSCHAN-2013], [BRONSTEIN-2005])**:
   Classical calculus textbooks integrate rational functions $\frac{A(x)}{D(x)} \in \mathbb{Q}(x)$ by factoring $D(x)$ over $\mathbb{C}$ into linear roots—computationally catastrophic in exact arithmetic. **Hermite reduction** uses Yun's square-free decomposition $D = \prod_{k=1}^m Q_k^k$ and extended Euclidean Bézout inverses modulo $Q_k$ to decompose any rational integrand **without any polynomial factorization over $\overline{\mathbb{Q}}$**:
   $$\int \frac{A(x)}{D(x)}\,dx = P(x) + \frac{G_{\text{num}}(x)}{G_{\text{den}}(x)} + \int \frac{H(x)}{S(x)}\,dx$$
   where $S(x)$ is guaranteed **strictly square-free** ($\deg \gcd(S, S') = 0$). **Generalized Hermite Reduction** ([BOSTAN-2018]) and **Creative Telescoping** ([KOUTSCHAN-2013]) extend this exact operator-reduction paradigm to $D$-finite definite integrals and hypergeometric sums.

4. **Algebraic Taylor Jet Algebras $k[x_1, \dots, x_n]/\mathfrak{m}^{r+1}$ & Kähler Differentials $\Omega^1_{k[V]/k}$**:
   Truncated polynomial quotients (unifying [`DualNumberAlgebra`](../../../src/algebrax/algebra/_dual.py) $\mathbb{R}[\varepsilon]/(\varepsilon^2)$ as the $n=1, r=1$ case!) convert higher-order partial derivatives, Hessians, Lie derivatives, and nonlinear ODEs (e.g., Riccati $y' = 1 + y^2$) into exact `QuotientRing` arithmetic. On affine varieties $V(I)$, the quotient module of **Kähler differentials** $\Omega^1_{k[V]/k} = \bigoplus_i k[V]\,dx_i / \langle df \mid f \in I \rangle$ gives the intrinsic algebraic exterior derivative bridging Phase 4 DEC (`EP-0160`) and Phase 9 coordinate rings (`EP-0221`).

5. **Discrete Difference Ore ($\Delta = S - 1$), Gosper's Algorithm & Frobenius Indicial Equations**:
   Forward differences $\Delta = S - 1$ obey the twisted Leibniz law $\Delta(ab) = S(a)\Delta(b) + \Delta(a)b$ and yield **Gosper's algorithm**—the exact discrete counterpart to Hermite reduction—producing rational certificates $r(n)$ or proving non-summability for hypergeometric series. Likewise, rewriting differential Ore operators in the Euler variable $\theta = x\partial_x$ extracts **indicial polynomials** $I(\rho) \in k[\rho]$ at regular singular points (Frobenius series) and constructs **Differential Companion Matrices** $C_L \in M_m(k(x))$ ($\partial Y = C_L Y$).

6. **Picard–Vessiot Differential Galois Theory, Symmetric Powers & Kovacic Factorization**:
   Just as classical Galois theory classifies polynomial solvability by radicals via finite permutation groups, **Picard–Vessiot theory** associates to any linear differential operator $L \in k(x)[\partial_x]$ a differential splitting field $E/k(x)$ and an affine algebraic Galois group $\operatorname{Gal}_\partial(E/k(x)) \subseteq \operatorname{GL}_m(k)$—whose coordinate ring is a `CoordinateHopfAlgebra` (`EP-0206`) / `AffineVariety` (`EP-0221`) torsor. The **Abel–Liouville Wronskian identity** ($W' = -\operatorname{Tr}(C_L)W$) reduces the problem to $\operatorname{SL}_m$, while **symmetric powers** $\operatorname{Sym}^k(L)$ detect invariant subspaces corresponding to reducible (Borel), dihedral ($D_\infty$), or finite primitive ($A_4, S_4, A_5$, `EP-0210`/`EP-0214`) subgroups. For order-2 ODEs $y'' = r(x)y$, **Kovacic’s algorithm** reuses Yun's square-free pole decomposition to extract exact Riccati right-factors $(\partial - \omega_2)(\partial - \omega_1)$ or produce falsifiable **$\operatorname{SL}_2$ non-Liouvillian obstruction certificates** (e.g., Airy's $y'' - xy = 0$).

### 2.2 Comparative Trade-Offs of Implementation Options

| Option | Core Mechanism | Strengths | Weaknesses / Traps | Council Fit |
|:-------|:---------------|:----------|:-------------------|:------------|
| **Option 1: Numerical Finite Differences & Floating ODE Steppers** | `float` step sizes $\Delta x$, RK4 / Euler arrays | Simple for numerical trajectories | Not algebraic; accumulates truncation and IEEE-754 drift; cannot prove operator identities or compute exact LCLMs | **Rejected** (Belongs in `SciPy`, violates Popper & Noether) |
| **Option 2: Expression-Tree Symbolic Calculus (`Expr` AST)** | Wrap SymPy-style `Add`/`Mul`/`Derivative` AST nodes | Familiar user syntax for elementary closed forms | Slow tree traversals (`111.35 ms` on simple rational integrals); mixes parsing with algebra | **Rejected** (Violates Shannon & `EP-0004`) |
| **Option 3: Unboxed Weyl, Ore, Hermite/Gosper & Multivariate Jet Algebras** | `dict[tuple[Monomial, Monomial], V]` for $A_n(k)$; `dict[int, R]` for $R[\partial; \sigma, \delta]$; Yun/Bézout Hermite & Gosper; `QuotientRing` Multivariate Jets | Zero AST overhead; unifies ODEs, shifts, $\Delta$, and $q$-differences; **37.7x faster** exact rational Hermite reduction than `sympy.integrate`; exact `Field` mandate prevents cancellation noise | Non-commutative Gröbner (`A_n`) scales exponentially in $n$; full transcendental Risch integration requires recursive field towers (deferred to `SymPy`) | **Accepted** |

### 2.3 Empirical Findings (`sources/prototype_differential_algebra.py`)
We authored and executed [`sources/prototype_differential_algebra.py`](./sources/prototype_differential_algebra.py) (full output archived in [`raw/prototype_benchmark_output.txt`](./raw/prototype_benchmark_output.txt)) on Python 3.14.7 with differential verification against `SymPy` as an external oracle:

#### Experiment 1: Non-Commutative Weyl Algebra $A_2(\mathbb{Q})$ & Heisenberg Commutation
* **Carrier**: `dict[tuple[Monomial, Monomial], Fraction]` mapping $(x^\alpha, \partial^\beta) \mapsto c_{\alpha,\beta}$ using closed-form normal-ordered Leibniz convolution.
* **Verified Algebraic Laws**:
  * Canonical CCR: $[\partial_0, x_0] == 1$ (`True`) and $[\partial_0, x_1] == 0$ (`True`).
  * Quantum harmonic oscillator ladder operators: $[(\partial_0 + x_0), (x_0 - \partial_0)] == 2$ (`True`).
  * Degree-3 non-commutative associativity $(L_1 L_2) L_3 == L_1 (L_2 L_3)$ (`True`).
  * Left $D$-module representation homomorphism $(L_1 L_2)(f) == L_1(L_2(f))$ on $f(x_0, x_1) = 3x_0^2 x_1 + x_1^2$ (`True`).

#### Experiment 2: Unified Ore Skew-Polynomial Algebra (`OreAlgebra`)
* **Differential Ore ($\mathbb{Q}[x][\partial_x]$)**:
  * Computed $\operatorname{lclm}(\partial_x - 1,\; \partial_x^2 + 1)$ of order $3$, verified exact right-divisibility by both factors (`True`) and exact annihilation of the Taylor series of $\exp(x) + \cos(x)$ through $x^8$ (`True`).
* **Shift / Recurrence Ore ($\mathbb{Q}[n][S_n]$)**:
  * Computed $\operatorname{lclm}(S_n^2 - S_n - 1,\; n S_n - (n+1))$ of order $3$, verified right-divisibility by both factors (`True`) and exact annihilation of the non-constant-coefficient sequence $a_n = F_n + n$ with **`max residual = 0`**.
* **$q$-Difference Ore ($\mathbb{Q}[x][D_q],\; q=2$)**:
  * Verified exact $q$-skew commutation $D_q \cdot x == 2x \cdot D_q$ (`True`) under the same generic `OreAlgebra` engine.

#### Experiment 3: Exact Rational Integration via Hermite Reduction vs. `SymPy` Oracle
* Target integrand with repeated linear and irreducible quadratic factors and improper numerator degree:
  $$\frac{x^7 - 2x^4 + 3x^2 + 5x - 1}{(x - 1)^3 (x^2 + 1)^2}$$
* **Results**:
  * **Pure-Python Hermite Reduction runtime**: **`2.95 ms`** vs. **`SymPy.integrate` runtime: `111.35 ms`** (**37.7x speedup**).
  * **Square-free guarantee**: $\deg\gcd(S, S') == 0$ (`True`).
  * **Exact Derivative Verification**: $\frac{d}{dx}(P + G_{\text{num}}/G_{\text{den}}) + H/S - \text{Num}/\text{Den} == 0$ (`True`) and differential agreement with `sympy.integrate` (`True`).

#### Experiment 4: Exact Taylor Jet Algebra $k[x]/\langle x^{13} \rangle$ & Nonlinear Riccati ODE Solver
* Instantiated directly using existing AlgebraX primitives: `QuotientRing(PolynomialAlgebra(StandardField(Fraction)), PolynomialTruncationIdeal(13, field.zero))` (catching the real parameter-order ergonomics nuance of `PolynomialTruncationIdeal(max_degree, zero_coeff)`).
* Solved nonlinear Riccati ODE $y'(x) = 1 + y(x)^2,\; y(0) = 0$ ($y(x) = \tan x$) to exact degree 12:
  * Matched `sympy.series(sp.tan(x), x, 0, 13)` **bit-for-bit identically (`True`)**: `x^1=1, x^3=1/3, x^5=2/15, x^7=17/315, x^9=62/2835`.
  * Exact ODE residual $(y' - (1 + y^2)) \bmod x^{12} == 0$ (`True`).

#### Experiment 5: Non-Commutative Weyl Left Ideal Reduction
* Using graded-lex Bernstein weight $(1,1)$ left reduction (`weyl_reduce_left`) in $A_1(\mathbb{Q})$:
  * Given the first-order Gaussian annihilator $L_1 = \partial_x - 2x$ of $e^{x^2}$, non-commutative left reduction certified $\overline{\partial_x^2 - 4x^2 - 2}^{\{L_1\}} == \emptyset$ (`True`), matching the exact Leibniz factorization $(\partial_x + 2x)(\partial_x - 2x) = \partial_x^2 - 4x^2 - 2$.

#### Experiment 6: Difference Ore Algebra ($\Delta = S - 1$), Gosper Summation & Euler Indicial Roots
* **Difference Skew Commutation**: Verified $\Delta \cdot p == S(p)\Delta + \Delta(p)$ on $p(n) = n^2 + 3n$ (`True`).
* **Gosper Indefinite Hypergeometric Summation (`gosper_rational_sum`)**:
  * **Factorial test ($\sum n \cdot n!$)**: Automatically extracted dispersion $h=1$ via resultant $R(h)$ and certified $r(n) = \frac{1}{n}$ (`True`, giving $S(n) = n!$).
  * **Rational telescoping with dispersion $h = 1$ ($\sum \frac{2n+1}{n^2(n+1)^2}$)**: Extracted $r(n) = -\frac{(n+1)^2}{2n+1}$, yielding $r(n) t_n = -\frac{1}{n^2}$ in exact agreement with `sympy.concrete.gosper.gosper_sum` (`True`).
  * **Harmonic non-summability proof ($\sum \frac{1}{n}$)**: Returned `None` (`True`), proving no hypergeometric closed form exists.
* **Euler Operator $\theta = x\partial_x$ & Frobenius Indicial Equation**:
  * Verified Bessel's identity $x^2 \partial_x^2 + x\partial_x + (x^2 - \frac{1}{4}) == \theta^2 - \frac{1}{4} + x^2$ inside $A_1(\mathbb{Q})$ (`True`) and extracted the exact indicial polynomial $I(\rho) = \rho^2 - \frac{1}{4}$ with roots $\rho = \pm \frac{1}{2}$ (`True`).

#### Experiment 7: Multivariate Taylor Jets $k[x,y]/\mathfrak{m}^4$, Characteristic Varieties & Kähler 1-Forms
* **Multivariate Taylor Jet AD ($k[x, y]/\langle x, y \rangle^4$)**: Evaluated $f(x, y) = \exp(xy) + x^2 y$ via pure truncated dictionary arithmetic and extracted all partial derivatives through order 3 matching `SymPy` identically (`True`: $\frac{\partial^2 f}{\partial x \partial y}(0,0) = 1$, $\frac{\partial^3 f}{\partial x^2 \partial y}(0,0) = 2$).
* **Weyl Characteristic Variety $\operatorname{Char}(I)$**: Extracted order-filtration principal symbols $\operatorname{gr}(I) = \langle \xi_0, \xi_1 \rangle \triangleleft \mathbb{Q}[x_0, x_1, \xi_0, \xi_1]$ for the 2D Gaussian ideal, certifying $\dim \operatorname{Char}(I) = 2 = n_{\text{vars}}$ (holonomic, `True`).
* **Kähler Differential Pairing on $V(x^2 + y^2 - 1)$**: Verified $\langle d(x^2 + y^2 - 1),\; -y \frac{\partial}{\partial x} + x \frac{\partial}{\partial y} \rangle == 0$ identically over $\mathbb{Q}[x, y]$ (`True`).

#### Experiment 8: Differential Galois Theory — Symmetric Powers, Kovacic Factorization & $\operatorname{SL}_2$ Obstructions
* **Symmetric Powers $\operatorname{Sym}^k(L)$ over $\mathbb{Q}(x)$**:
  * Harmonic oscillator $L = \partial_x^2 + 1$: computed exact $\operatorname{Sym}^2(L) = \partial_x^3 + 4\partial_x$ (`True`) and $\operatorname{Sym}^3(L) = \partial_x^4 + 10\partial_x^2 + 9$ (`True`).
  * Non-constant-coefficient Airy ODE $L = \partial_x^2 - x$: computed $\operatorname{Sym}^2(L) = \partial_x^3 - 4x\partial_x - 2$ (`True`) and verified zero differential residual on `sympy.airyai(x) * sympy.airybi(x)` (`True`).
* **Abel–Liouville Wronskian Identity**: Verified $W(y_1, y_2) = \frac{1}{x}$ for $y'' + \frac{1}{x}y' + (1 - \frac{1}{4x^2})y = 0$ satisfies $W' + \frac{1}{x}W == 0$ (`True`).
* **Kovacic Non-Liouvillian Obstruction Certificate (Airy $y'' - xy = 0$)**: Using `square_free_factors` pole decomposition, certified `val_inf = -1`, `case1_admissible = False`, `case2_admissible = False`, `case3_admissible = False` $\implies \operatorname{Gal}_\partial = \operatorname{SL}_2$ (`liouvillian_possible = False`).
* **Kovacic Case 1 Apparent-Singularity Factorization ($y'' - (x^2 + 3)y = 0$)**: Extracted exact rational log-derivative $\omega_1(x) = \frac{x^2 + 1}{x}$ ($P(x) = x$), certifying $(\partial_x + \omega_1)(\partial_x - \omega_1) == \partial_x^2 - (x^2 + 3)$ (`True`) and passing `sympy.checkodesol` (`(True, 0)`) on both Riccati and order-2 ODEs—even where `sympy.dsolve` fell back to `O(x**6)` series and `sympy.solvers.ode.riccati.solve_riccati` returned `[]`. Also verified Cauchy–Euler $y'' - \frac{2}{x^2}y = 0$ ($\omega_1 = \frac{2}{x}$) against `solve_riccati`.

#### Experiment 9: Differential Polynomial Rings, Rota–Baxter Identities, Newton Polygons & $D$-Finite Guessing
* **Differential Polynomial Ring $\mathbb{Q}\{u\}$ & Euler–Lagrange Variational Complex**:
  * Verified **Null-Lagrangian Exactness ($\frac{\delta}{\delta u} \circ D \equiv 0$)** on $F = u^2 u'' + (u')^3$ (`euler_lagrange(total_diff(F)) == {}` -> `True`), harmonic oscillator $\frac{1}{2}(u')^2 - \frac{1}{2}u^2 \mapsto -u'' - u$ (`True`), and 2nd-order jet Lagrangian $\frac{1}{2}(u'')^2 + u(u')^2 \mapsto u^{(4)} - (u')^2 - 2uu''$ (`True`).
* **Rota–Baxter Algebraic Duality**: Verified $R(a)R(b) == R(R(a)b + aR(b) + \lambda ab)$ for weight $\lambda = 0$ (polynomial integration by parts, `True`) and weight $\lambda = +1$ (strict partial summation by parts, `True`).
* **Differential Newton Polygons & Katz Slopes**: Extracted lower convex hull of $(k, \operatorname{val}_0(c_k) - k)$: Bessel ($x=0$) gave horizontal slope `[0]` (`Fuchsian=True`); mixed irregular $x^3\partial^2 + x\partial - 1$ gave slopes `[0, 1]`; Airy at $\infty$ ($z^5\partial_z^2 + 2z^4\partial_z - 1$) recovered the exact WKB Katz slope **`3/2`** (`True`).
* **$D$-Finite Padé / Recurrence Guessing (`guess_diff_ore`, `guess_shift_ore`)**:
  * Recovered $\partial_x^3 - \partial_x^2 + \partial_x - 1$ (`LCLM` from Experiment 2) purely from 10 Taylor coefficients of $\exp(x) + \cos(x)$ (`True`).
  * Recovered Catalan ODE $(x^2 - \frac{1}{4}x)\partial_x^2 + (\frac{5}{2}x - \frac{1}{2})\partial_x + \frac{1}{2}$ from Catalan Taylor coefficients (annihilating through $x^9$ with `0` residual, `True`) and Catalan recurrence $(n + 2)S_n - (4n + 2)$ from 8 sequence terms, exactly predicting $C_8 = 1430$ and $C_9 = 4862$ (`True`).

#### Experiment 10: Algebraic Hamiltonian Mechanics (Poisson Derivations, Legendre Duality, Weyl Ehrenfest & Symplectic Jets)
* **`CanonicalPoissonAlgebra` (`EP-0204` / `EP-0220` Concrete Realization)**:
  * Over 2-DOF phase space $\mathbb{Q}[q_0, q_1, p_0, p_1]$, verified Jacobi identity (`== 0`), Leibniz rule (`== 0`), Hamiltonian derivation Lie homomorphism $[X_F, X_G] == -X_{\{F, G\}}$ (`True`), and exact Noether conservation of angular momentum $\{q_0 p_1 - q_1 p_0,\; \frac{1}{2}(p_0^2 + p_1^2 + q_0^2 + q_1^2)\} == 0$ (`True`).
* **Algebraic Legendre Transform ($\mathcal{L}(q, \dot{q}) \leftrightarrow H(q, p)$)**:
  * Transformed coupled 2-DOF Lagrangian with non-diagonal mass matrix $M = \begin{pmatrix} 1 & 1 \\ 1 & 3 \end{pmatrix}$ to exact $H(q, p)$ ($\frac{3}{4}p_0^2 - \frac{1}{2}p_0 p_1 + \frac{1}{4}p_1^2 + \frac{1}{2}(q_0^2 + q_1^2)$) and verified exact round-trip involution $\mathcal{L} \mapsto H \mapsto \mathcal{L}$ (`True`), while rejecting singular Chern–Simons-like $\mathcal{L} = q_0\dot{q}_1 - q_1\dot{q}_0$ ($\det M = 0 \implies$ `ValueError`, `True`).
  * Verified 1-DOF anharmonic Lagrangian $\frac{1}{2}(u')^2 - \frac{1}{2}u^2 - \frac{1}{4}u^4$ produces `DifferentialPolynomialRing.euler_lagrange` $== -(u'' + u + u^3)$, identically matching Hamilton's equation $\dot{p} = \{p, H\} = -q - q^3$ (`True`).
* **Weyl $\leftrightarrow$ Poisson Ehrenfest Correspondence**:
  * In `WeylAlgebra` $A_2(\mathbb{Q})$, verified quantum conservation $[\widehat{L}_z, \widehat{H}] == 0$ (`True`) and exact Bernstein principal-symbol correspondence $\sigma_{\text{top}}([\widehat{A}, \widehat{B}]) == -\{\sigma_{\text{top}}(\widehat{A}), \sigma_{\text{top}}(\widehat{B})\}_{q,p}$ on mixed degree-3 operators (`True`).
* **Exact Hamiltonian Energy & Symplectic Jacobian Conservation in Taylor Jets**:
  * Integrated the nonlinear anharmonic Hamiltonian flow $\dot{q} = p,\; \dot{p} = -q - q^3$ from $(q_0, p_0) = (1, 0)$ in $\mathbb{Q}[t]/\langle t^{11} \rangle$: verified exact energy conservation $H(q(t), p(t)) \equiv \frac{3}{4} \pmod{t^{11}}$ (`True`), exact symplectic variational Jacobian $M(t)^T J M(t) == J$ ($\det D\Phi_t \equiv 1 \pmod{t^{11}}$, `True`), and zero `SymPy` ODE series residual through $t^9$ (`True`).

#### Experiment 11: Algebraic de Rham Complex, Graded Exterior Derivative $d_k$ & Cartan Calculus
* **Graded Differential Algebra $\Omega^\bullet = \mathbb{Q}[x_0, \dots, x_{n-1}] \otimes \bigwedge^\bullet(dx_i)$ (`AlgebraicDeRhamComplex`)**:
  * In 3D $(x, y, z)$ with unboxed `dict[tuple[Monomial, tuple[int, ...]], Fraction]` carriers (reusing Grassmann blades from [`CliffordAlgebra`](../../../src/algebrax/clifford.py) over exact fields), verified graded commutativity ($\alpha \wedge \beta = -\beta \wedge \alpha$), graded Leibniz rule $d(\alpha \wedge \beta) = d\alpha \wedge \beta - \alpha \wedge d\beta$, and exact cochain nilpotency $d(d(\alpha_1)) == 0$ (`True`).
* **Exact Algebraic Poincaré Chain Homotopy ($h_k : \Omega^k \to \Omega^{k-1}$)**:
  * Verified Cartan homotopy identity $(d \circ h + h \circ d)(\omega_2) == \omega_2$ on non-closed 2-forms (`True`), and constructively recovered exact scalar potentials $\phi = h(d\phi)$ and divergence-free vector potentials $B = d(h(B))$ (`True`).
* **Symplectic Cartan–Liouville Bridge & Kähler 2-Forms**:
  * On 4D Hénon–Heiles phase space with canonical symplectic 2-form $\omega = dq_0 \wedge dp_0 + dq_1 \wedge dp_1$, verified closedness $d\omega == 0$, Cartan's coordinate-free Hamilton equation $\iota_{X_H}(\omega) == dH$, $\iota_X^2 == 0$, and **Liouville's Theorem** $\mathcal{L}_{X_H}(\omega) = (d\iota_{X_H} + \iota_{X_H}d)(\omega) == 0$ (`True`), plus the Kähler quotient relation $d(x^2+y^2-1) \wedge (-y\,dx + x\,dy) \equiv 2\,dx \wedge dy \pmod{x^2+y^2-1}$ on the circle (`True`).

---

## 3. Architectural Synthesis & Constraint Alignment

1. **Noether (Quantization as Non-Commutative Deformation of Poisson Geometry & Picard–Vessiot Torsors)**:
   Differential algebra forms the non-commutative quantum counterpart of AlgebraX's commutative & symplectic hierarchy:
   - `PolynomialAlgebra` / `MultivariatePolynomialAlgebra` ([EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md)) provides commutative phase space $k[q, p]$ and `CanonicalPoissonAlgebra` (`EP-0204`) realizes `{f, g}`, Hamiltonian vector fields $X_H(f) = \{f, H\}$, and conserved integrals $\{I, H\} = 0$, linking quadratic Hamiltonians directly to $\mathfrak{sp}(2n)$ (`EP-0163`).
   - **Differential Polynomial Ring $k\{u\}$ & Variational / Legendre Duality**: Unbounded jet-variable polynomials $k[u, u', u'', \dots]$ realize an exact algebraic cochain complex $0 \to k \to k\{u\} \xrightarrow{D} k\{u\} \xrightarrow{\delta/\delta u} k\{u\}$ ($\frac{\delta}{\delta u} \circ D \equiv 0$, mirroring `EP-0101` & `EP-0160`), while regular `legendre_transform` maps quadratic $\mathcal{L}(q, \dot{q}) \leftrightarrow H(q, p)$ over exact `Field[V]`.
   - **Weyl Algebra $A_n(k)$** replaces $p_i$ with $\partial_i$ satisfying canonical commutation $[\partial_i, x_j] = \delta_{ij}$, realizing a concrete unital associative **Non-Commutative `Algebra` & Left `Module`** over $k[x_1, \dots, x_n]$ whose principal-symbol commutator reproduces the canonical Poisson bracket (Ehrenfest correspondence).
   - **Characteristic Varieties (`EP-0221` Bridge)**: Passing to order-filtration principal symbols maps a left Weyl ideal $I \subseteq A_n(k)$ to a commutative Phase 9 `AffineVariety` $\operatorname{Char}(I) \subset k^{2n}$ ($\dim \operatorname{Char}(I) = n \iff$ holonomic!).
   - **Algebraic de Rham & Kähler Differentials ($\Omega^\bullet_{k[V]/k}$, `EP-0160` + `EP-0111` + `EP-0221` Bridge)**: Extends `KahlerDifferentialModule` from $\Omega^1$ to the full graded exterior algebra $\Omega^\bullet_{k[V]/k}$ with wedge product $\wedge$, exterior derivative $d_k$ ($d^2 = 0$), interior product $\iota_X$, Cartan Lie derivative $\mathcal{L}_X = d\iota_X + \iota_X d$, and algebraic Poincaré homotopy $h_k$—dualizing `HasTangentLocus` Jacobians, symplectic Liouville geometry ($\iota_{X_H}\omega = dH$, $\mathcal{L}_{X_H}\omega = 0$), Grassmann blades ([`CliffordAlgebra`](../../../src/algebrax/clifford.py)), and Phase 4 DEC cochains ([`exterior_derivative`](../../../src/algebrax/topology/dec.py)).
   - **Ore Skew-Polynomial Ring $R[\partial; \sigma, \delta]$** generalizes derivations and ring endomorphisms (`RingHom` from [EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md)) into a single operator algebra unifying differential, shift, forward-difference ($\Delta$), and $q$-difference calculus, with a **Differential Companion Matrix** $C_L \in M_m(k(x))$ bridging scalar ODEs to `algebrax.matrix` and `EP-0163` Magnus/BCH flows, and **Differential Newton Polygons** bridging `EP-0222` tropical hulls to Katz irregular singularity slopes.
   - **Picard–Vessiot Torsors & Representation Bridge (`EP-0206` + `EP-0210`/`EP-0214`)**: A differential Galois group $\operatorname{Gal}_\partial(E/k(x)) \subseteq \operatorname{GL}_m(k)$ is an affine algebraic group whose coordinate ring is a `CoordinateHopfAlgebra` (`EP-0206`) / `AffineVariety` (`EP-0221`) torsor, while order-2 Kovacic subgroup classification ($\operatorname{Borel}, D_\infty, A_4, S_4, A_5, \operatorname{SL}_2$) directly connects Ore symmetric powers $\operatorname{Sym}^k(L)$ to Phase 8 representation & invariant theory.

2. **Russell & `EP-0005` (Atomic Mixins & Protocol Taxonomy)**:
   - Extend [`src/algebrax/algebra/_mixins.py`](../../../src/algebrax/algebra/_mixins.py) cleanly with `HasSkewDerivation[R]` (generalizing `HasDerivation[V]` with endomorphism $\sigma$ and $\sigma$-derivation $\delta$: $\delta(ab) = \sigma(a)\delta(b) + \delta(a)b$), `HasIntegrate[V]`, `LawLeibniz`, and `LawRotaBaxter` ($R(a)R(b) = R(R(a)b + aR(b) + \lambda ab)$ unifying integration by parts $\lambda=0$ and summation by parts $\lambda=\pm 1$).
   - **Weyl Algebra vs. Commutative Ring Separation**: `WeylAlgebra[V]` and `OreAlgebra[R]` satisfy associative `Ring[Op]` / `Algebra[k, Op]` protocols **without** inheriting `CommRing` or `LawCommutative`, preserving `EP-0005` diamond-free typeclass soundness. `CanonicalPoissonAlgebra` cleanly binds `MultivariatePolynomialAlgebra` (`EP-0220`) to `PoissonAlgebra` (`EP-0204`) and `HasDerivation` (`hamiltonian_derivation`), while `AlgebraicDeRhamComplex` implements graded-associative `Algebra[k, DiffForm]` without falsely claiming `LawCommutative`.

3. **Popper (Falsifiable Differential & Operator Oracles — `EP-0003`)**:
   - **Exact Field Mandate**: Mirroring `GroebnerIdeal` ([EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md)), non-commutative Weyl Gröbner reduction, Ore `gcrd`/`lclm`, Gosper dispersion, Kovacic Galois classification, regular Legendre mass-matrix inversion, and Kähler coordinate-ring reduction MUST reject IEEE-754 floating-point fields (`float`, `complex`) because $[\partial, x] = 1$ cancellation residuals create false unit ideals $\langle 1 \rangle$.
   - **Universal Falsifiable Laws**:
     1. **Skew Leibniz & Rota–Baxter Laws**: $\partial(r \cdot a) = \sigma(r)(\partial a) + \delta(r)a$ and $R(a)R(b) = R(R(a)b + aR(b) + \lambda ab)$.
     2. **Variational, Hamiltonian, Exterior-Derivative & LCLM Laws**: $\frac{\delta}{\delta u}(D(F)) \equiv 0$; Legendre involution $\mathcal{L} \leftrightarrow H$; Ehrenfest $\sigma_{\text{top}}([\widehat{A}, \widehat{B}]) == -\{\sigma_{\text{top}}(\widehat{A}), \sigma_{\text{top}}(\widehat{B})\}$; Taylor-Jet Hamiltonian energy $H(q(t), p(t)) \equiv H(q_0, p_0)$ and symplectic Jacobian $D\Phi_t^T J D\Phi_t \equiv J \pmod{t^{r+1}}$; de Rham $d^2 \equiv 0$, graded Leibniz $d(\alpha \wedge \beta) = d\alpha \wedge \beta + (-1)^p\alpha \wedge d\beta$, Cartan $\iota_{X_H}\omega = dH$, Liouville $\mathcal{L}_{X_H}\omega = 0$, Poincaré $dh + hd = \mathrm{id}$; and $\operatorname{lclm}(A, B)$ right-divisibility/annihilation.
     3. **Hermite & Gosper Fundamental Theorems**: $\frac{d}{dx}(P + G_{\text{num}}/G_{\text{den}}) + H/S \equiv A/D$ ($\deg\gcd(S, S') = 0$), and $r(n+1)\frac{f(n)}{g(n)} - r(n) \equiv 1$.
     4. **Differential Galois & SymPy Oracles**: Exact operator factorization $(\partial - \omega_2)(\partial - \omega_1) == L$, `Sym^k(L)` annihilation residuals, falsifiable $\operatorname{SL}_2$ non-Liouvillian obstruction certificates, and exact coefficient agreement with `sympy.series`, `sympy.integrate`, `sympy.concrete.gosper.gosper_sum`, and `sympy.checkodesol`.

4. **Shannon (Unboxed Sparse Carriers & Algorithmic Escape Hatches — `EP-0004`)**:
   - **Zero-Allocation Carriers**:
     - `WeylAlgebra`: `dict[tuple[Monomial, Monomial], V]` (reusing `Monomial = tuple[int, ...]`).
     - `AlgebraicDeRhamComplex`: `dict[tuple[Monomial, tuple[int, ...]], V]` (reusing `Monomial` and sorted Grassmann `Blade` tuples).
     - `DifferentialPolynomialRing`: `dict[tuple[int, ...], V]` mapping canonical trailing-trimmed jet exponent tuples to exact field scalars.
     - `OreAlgebra`: `dict[int, R]` (sparse operator degrees mapped to unboxed coefficient elements $r \in R$).
     - `TaylorJetAlgebra` (1D & Multivariate): unboxed `dict[int, V]` and `dict[Monomial, V]` directly generalizing [`DualNumberAlgebra`](../../../src/algebrax/algebra/_dual.py) ($n=1, r=1$) via `QuotientRing`.
   - **Escape Hatch Pattern & Deliberate Deferrals (Dennis Point)**:
     - **Pure-Python Core (Zero New Dependencies)**: Weyl multiplication, `DifferentialPolynomialRing` Euler–Lagrange, `CanonicalPoissonAlgebra` & regular quadratic Legendre transforms, `AlgebraicDeRhamComplex` ($d_k$, $\iota_X$, $\mathcal{L}_X$, Poincaré $h_k$), Rota–Baxter laws, Ore arithmetic/`gcrd`/`lclm`/`guess_ore_operator`, Hermite & Gosper algorithms, Frobenius/Newton-polygon slope analysis, multivariate Taylor Jet AD/Hamiltonian/ODEs, Kähler differentials, $A_n(k)$ left Gröbner bases, $\operatorname{Sym}^k(L)$ / Kovacic Case 1 factorization, and $\operatorname{SL}_2$ obstruction analysis run 100% in pure Python over exact `Field` / `PolynomialAlgebra`.
     - **Deliberate Deferrals**: Full **transcendental Risch integration towers**, **Ritt–Wu nonlinear differential characteristic sets**, **arbitrary-order ($n \ge 3$) general Picard–Vessiot Galois group reconstruction (Hrushovski / van der Put–Singer)**, **infinite-dimensional bi-Hamiltonian PDE / Gelfand–Dickey pseudodifferential $\partial^{-1}$ hierarchies**, **constrained Dirac brackets** ($\det M = 0$), **infinite-jet variational bicomplexes $\Omega^{p,q}(J^\infty)$**, **smooth Riemannian metric Hodge stars**, **rational/punctured de Rham cohomology**, and **numerical symplectic ODE integrators** (Verlet / Gauss–Legendre RK) are deliberately deferred.
     - **Escape Hatches**: Multi-modular CRT rational reconstruction (`ModularField(p)`) for coefficient swell, and optional `SciPy`/`NumPy` analytic continuation of certified Frobenius/Taylor Jet expansions.

5. **Feynman (The Freshman Test)**:
   - *"Calculus without floating-point limits! A derivative $\partial$, a shift $S$, a finite difference $\Delta$, a Hamiltonian flow $X_H = \{\cdot, H\}$, and the exterior derivative $d$ ($d^2 = 0$, $\operatorname{curl}\nabla = 0$, $\operatorname{div}\operatorname{curl} = 0$) all obey exact algebraic rules. Once you know how operators commute and wedge past monomials, recovering exact scalar/vector potentials via Poincaré's homotopy, proving Liouville's phase-volume conservation in one line, solving nonlinear Hamiltonian trajectories in Taylor jets with zero energy drift, dualizing Lagrangians via Legendre transforms, summing factorials with Gosper, splitting rational integrals with Hermite, guessing recurrence laws, and proving non-solvability obstructions all reduce to exact polynomial algebra."*

6. **Steward & Explorer (Ergonomics & Ecosystem Bridges)**:
   - **Ergonomics Note (Dennis Point)**: Keep algebraic analysis clearly separated from numerical analysis (`algebrax.analysis` Laplacians vs. `algebrax.differential` / `algebrax.ore`), and pair `PolynomialTruncationIdeal(max_degree, zero_coeff)` with a clean `TaylorJetAlgebra(field, n_vars=1, order=...)` factory unifying [`DualNumberAlgebra`](../../../src/algebrax/algebra/_dual.py).
   - **Cross-Continent Unification**: Connects directly to `EP-0111` (Grassmann blade keys $\bigwedge^\bullet$), `EP-0149` (divided powers / falling factorials), `EP-0160` (`exterior_derivative` DEC cochains $\leftrightarrow$ algebraic de Rham / Kähler $\Omega^\bullet_{k[V]/k}$ & Euler–Lagrange complex), `EP-0163` (Lie brackets, $\mathfrak{sp}(2n)$ linear Hamiltonians & BCH via Weyl commutators and companion ODE systems), `EP-0204` (`CanonicalPoissonAlgebra`, Cartan symplectic geometry, Legendre duality & Weyl–Ehrenfest quantization), `EP-0206`/`EP-0210`/`EP-0214` (Picard–Vessiot Hopf torsors & finite $\operatorname{SL}_2$ subgroups), `EP-0220`/`EP-0221`/`EP-0222` (commutative Gröbner ideals $\leftrightarrow$ Weyl $D$-modules, `CharacteristicVariety` & differential Newton polygons), and `EP-0231` (polynomial shift models $\to$ Ore recurrence operators).

---

## 4. The Verdict / Actionable Design

**Verdict: Approved as Phase 11 ("Algebraic Analysis, Differential Rings, Ore Algebras & Differential Galois Theory", `EP-0240`–`EP-0243`).**

To maintain high cohesion under the Dennis Point, the Council recommends a clean 4-EP Standards-Track architecture starting at **`EP-0240`**:

1. **`EP-0240`: Differential Rings, Weyl Algebras $A_n(k)$, Characteristic Varieties & Kähler–de Rham Forms**:
   - Extend `algebra._mixins` with `HasSkewDerivation[R]`, `HasIntegrate[V]`, `LawLeibniz`, and `LawRotaBaxter`.
   - Introduce `algebrax.differential` with `DifferentialPolynomialRing` ($k\{u\}$ total derivative `total_diff` & exact variational `euler_lagrange` complex $\frac{\delta}{\delta u}\circ D \equiv 0$), `CanonicalPoissonAlgebra` (`hamiltonian_derivation` $X_H = \{\cdot, H\}$, conserved integrals `{I, H} == 0`, algebraic `legendre_transform` $\mathcal{L}(q, \dot{q}) \leftrightarrow H(q, p)$), and `WeylAlgebra[V]` over unboxed `dict[tuple[Monomial, Monomial], V]` carriers with left $D$-module action and Weyl–Poisson Ehrenfest principal-symbol correspondence (`EP-0204` bridge).
   - Non-commutative Weyl left Gröbner reduction (`weyl_reduce_left` with Bernstein $(1,1)$ ordering), `CharacteristicVariety` / holonomic rank certification bridging Phase 9 `AffineVariety` (`EP-0221`), and full graded `AlgebraicDeRhamComplex` / `KahlerDifferentialModule` $\Omega^\bullet_{k[V]/k}$ (`wedge`, `exterior_derivative` $d_k$ with $d^2=0$, `interior_product` $\iota_X$, Cartan `lie_derivative`, and algebraic `poincare_homotopy` $h_k$) bridging `EP-0111`/`EP-0160`/`EP-0221`.
2. **`EP-0241`: Unified Ore Skew-Polynomial Algebras $R[\partial; \sigma, \delta]$, $D$-Finite Closure & Frobenius Solvers**:
   - Generic `OreAlgebra[R]` parameterized by exact base ring/field `R`, ring endomorphism `sigma`, and skew derivation `delta`, with preset constructors: `differential_ore`, `shift_ore`, `difference_ore` ($\Delta = S - 1$), and `q_difference_ore`.
   - Pseudo-right and rational Euclidean division (`right_divmod`), `gcrd`, `lclm`, `symmetric_product`, and exact $D$-finite Padé guessing (`guess_ore_operator` synthesizing minimal differential/shift operators from exact series/sequences).
   - Euler operator $\theta = x\partial_x$ conversion, regular-singular `indicial_polynomial`, `differential_newton_polygon` (Katz irregularity slopes bridging `EP-0222`), and `differential_companion_matrix` $C_L \in M_m(k(x))$ (`algebrax.matrix` / `EP-0163` bridge), alongside [EP-0231](../../../docs/proposals/EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md) shift models.
3. **`EP-0242`: Exact Symbolic Integration, Hermite & Gosper Reduction, Creative Telescoping & Multivariate Taylor Jet Solvers**:
   - Yun square-free decomposition (`square_free_decomposition`), exact Bronstein **Hermite reduction** (`hermite_reduce`), and Rothstein–Trager logarithmic resultant extraction over exact fields (`StandardField(Fraction)`).
   - Exact **Gosper indefinite hypergeometric summation** (`gosper_sum`) and Zeilberger / Chyzak **Creative Telescoping** (`creative_telescope`) for certifying definite hypergeometric/holonomic sums and integrals.
   - Univariate & **Multivariate `TaylorJetAlgebra[V]`** ($k[x_1, \dots, x_n]/\mathfrak{m}^{r+1}$) unifying [`DualNumberAlgebra`](../../../src/algebrax/algebra/_dual.py) ($n=1, r=1$), providing exact higher-order AD (gradients, Hessians, Lie derivatives), formal integration (`jet_integrate`), Lagrange reversion, algebraic Newton–Picard nonlinear ODE & symplectic-preserving Hamiltonian jet solving (`solve_ode_jet`, `solve_hamiltonian_jet`), and direct series feeding into `guess_ore_operator` (`EP-0241`).
4. **`EP-0243`: Picard–Vessiot Differential Galois Theory, Symmetric Powers & Kovacic Factorization**:
   - **Wronskian & Abel–Liouville Determinant Operator** (`wronskian_operator`) linking `differential_companion_matrix` (`EP-0241`) to $\operatorname{SL}_m$ Galois reductions.
   - **Symmetric & Exterior Powers** (`symmetric_power`, `exterior_power`) over exact differential rational fields $\mathbb{Q}(x)$ for algebraic invariant detection.
   - **Order-2 Kovacic Classifier & Riccati Factorization** (`kovacic_classify`, `kovacic_factorize`) reusing `square_free_decomposition` (`EP-0242`) to extract exact $(\partial - \omega_2)(\partial - \omega_1)$ factorizations (Case 1, plus Case 2 $\operatorname{Sym}^2$ & Case 3 finite-group degree checks) and falsifiable **$\operatorname{SL}_2$ non-Liouvillian obstruction certificates** (Airy $y'' - xy = 0$).
   - **Picard–Vessiot Torsor Interface** bridging solution-space Galois groups to `CoordinateHopfAlgebra` (`EP-0206`) and `AffineVariety` (`EP-0221`), with $n \ge 3$ general Picard–Vessiot reconstruction explicitly deferred under the Dennis Point.

---

## 5. Related Enhancement Proposals & Artifacts

### Connected EPs
* **Prerequisites**: [EP-0005](../../../docs/proposals/EP-0005-equational-theories-and-typeclass-axioms.md) (Equational Theories & Mixins), [EP-0149](../../../docs/proposals/EP-0149-binomial-convolution-moment-semiring.md) (Binomial Divided Powers), [EP-0160](../../../docs/proposals/EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md) (DEC Exterior Derivative), [EP-0163](../../../docs/proposals/EP-0163-lie-algebras-and-bch-dynamics.md) (Lie & BCH Dynamics), [EP-0201](../../../docs/proposals/EP-0201-algebraic-homomorphisms-ideals-quotients.md) (`QuotientRing`, `RingHom`, `PolynomialTruncationIdeal`), [EP-0204](../../../docs/proposals/EP-0204-non-associative-quantum-algebras-jordan-octonions-poisson.md) (Poisson Algebras), [EP-0206](../../../docs/proposals/EP-0206-coalgebras-bialgebras-and-hopf-algebras.md) (`CoordinateHopfAlgebra`), [EP-0210](../../../docs/proposals/EP-0210-group-representations-character-tables-schurs-lemma.md) (Group Representations), [EP-0214](../../../docs/proposals/EP-0214-invariant-theory-molien-series-casimir-polynomials.md) (Invariant Theory), [EP-0220](../../../docs/proposals/EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md) (`HasDerivation`, `MultivariatePolynomialAlgebra`, `GroebnerIdeal`), [EP-0221](../../../docs/proposals/EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) (`AffineVariety`, `HasTangentLocus`), [EP-0222](../../../docs/proposals/EP-0222-tropical-varieties-and-polyhedral-duals.md) (`NewtonPolytope`), [EP-0231](../../../docs/proposals/EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md) (Polynomial Shift Models).
* **Candidate Phase 11 EPs**: `EP-0240` (Differential Rings, Weyl Algebras, Characteristic Varieties & Kähler Differentials), `EP-0241` (Unified Ore Skew-Polynomials, $D$-Finite Closure & Frobenius Solvers), `EP-0242` (Hermite & Gosper Reduction, Creative Telescoping & Multivariate Taylor Jet Solvers), `EP-0243` (Picard–Vessiot Differential Galois Theory, Symmetric Powers & Kovacic Factorization).

### Bundled Compendium Artifacts
* [`sources/prototype_differential_algebra.py`](./sources/prototype_differential_algebra.py) — Executable pure-Python prototype & benchmark suite covering all 11 differential, variational, Hamiltonian/Legendre, de Rham/Kähler exterior-derivative, Rota–Baxter, Ore, Newton-polygon, $D$-finite guessing, Gosper, Frobenius, Jet, and Differential Galois experiments with `SymPy` differential verification.
* [`raw/prototype_benchmark_output.txt`](./raw/prototype_benchmark_output.txt) — Exact captured stdout from executing the prototype on Python 3.14.7.
* [`sources/BIBLIOGRAPHY.md`](./sources/BIBLIOGRAPHY.md) — Annotated bibliography of primary papers and monographs.
* [`papers/`](./papers/) — Archived open-access arXiv PDFs ([SATTELBERGER-2019], [KAUERS-2013], [KOUTSCHAN-2013], [BOSTAN-2018]).
