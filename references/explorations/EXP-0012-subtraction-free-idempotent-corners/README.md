# EXP-0012: Subtraction-Free Idempotent Corners — Kleene–Hopf Bialgebras, Exceptional Jordan Quantales, Shattered Artin–Moufang Tiers & Drift Derivations

| Field           | Value                                                                                                                                                                                                                |
|:----------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0012                                                                                                                                                                                                                 |
| **Title**       | Subtraction-Free Idempotent Corners — Kleene–Hopf Bialgebras, Exceptional Jordan Quantales, Shattered Artin–Moufang Tiers & Drift Derivations                                                                       |
| **Author**      | Eran Rivlis, Antigravity AI, Grand Council                                                                                                                                                                           |
| **Status**      | Concluded                                                                                                                                                                                                            |
| **Type**        | Architectural & Research Exploration                                                                                                                                                                                 |
| **Created**     | 2026-11-28                                                                                                                                                                                                           |
| **Updated**     | 2026-11-28                                                                                                                                                                                                           |
| **Related EPs** | [EP-0005](../../../docs/proposals/EP-0005-universal-algebraic-protocol-architecture.md), [EP-0197](../../../docs/proposals/EP-0197-decoupled-semiring-foundations-star-semirings-and-kleene-algebras.md), [EP-0198](../../../docs/proposals/EP-0198-generalized-closure-operators-kleene-plus-matrix-star-and-action-algebras.md), [EP-0204](../../../docs/proposals/EP-0204-non-associative-quantum-algebras-jordan-octonions-poisson.md), [EP-0206](../../../docs/proposals/EP-0206-coalgebras-bialgebras-and-hopf-algebras.md), [EP-0240](../../../docs/proposals/EP-0240-differential-rings-weyl-algebras-and-kahler-differentials.md), [EP-0250](../../../docs/proposals/EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md) |

---

## 1. Abstract & Context

### 1.1 The Research Question
> *Can we systematically map genuinely uncanonized "corners" of AlgebraX's atomic mixin hypercube (`algebrax.algebra._mixins`)—intersections of operations and equational laws that classical ring-theoretic literature overlooks—and verify them empirically via SMT finite-model synthesis (Z3) and live protocol audits?*

### 1.2 The Structural Hypothesis
AlgebraX decomposes abstract algebra into orthogonal Layer-1 operational atoms (`HasZero`, `HasOne`, `HasAdd`, `HasNeg`, `HasMul`, `HasStar`, `HasResiduals`, `HasCoproduct`, `HasCounit`, `HasAntipode`, `HasDerivation`) and equational law witnesses (`LawIdempotent`, `LawCommutative`, `LawAssociative`, `LawJordan`, `LawAlternative`, `LawLie`).

In classical mathematics, **Hopf algebras**, **Jordan algebras**, **alternative algebras**, and **differential algebras** are almost universally built over rings with additive inverses (`HasNeg`). Conversely, **Kleene algebras**, **action algebras**, and **quantales** live in the subtraction-free **idempotent continent** (`LawIdempotent`: $a \oplus a = a$).

The frontier hypothesis of EXP-0012 is that **idempotence is not "broken negation"—it is an alternative conservation law**:
- It annihilates scalar denominators and integer multiplicities ($\frac{1}{2}$, $n!$, $\binom{n}{k} \mapsto 1$).
- It converts alternating inverse series (Hopf antipodes, exponential automorphisms) into monotone fixed-point closures (Kleene stars).
- It **shatters classical ring-theoretic equivalences** whose proofs rely on subtracting linearized terms (such as Artin's 1931 theorem for alternative algebras and the characterization of special Jordan algebras).

To survive falsification, every candidate corner must pass:
1. **Noether's Coupling Filter:** Cross-continent operations must interlock through a non-trivial algebraic identity.
2. **Popper's Non-Collapse Filter:** Dropping `HasNeg` must not collapse the structure to triviality (for example, an anticommutative Lie bracket with $[x, x] = \mathbf{0}$ in a zerosumfree idempotent monoid forces $0 = [x \oplus y, x \oplus y] = [x, y] \oplus [y, x] \implies [x, y] \equiv \mathbf{0}$).

---

## 2. Exploration & Empirical Findings (Z3 & Finite Models)

All finite-model lower bounds, counterexamples, and non-collapse proofs were synthesized and machine-verified using **Z3 5.4.1** in [`sources/z3_corner_hunter.py`](./sources/z3_corner_hunter.py) (archived outputs in [`sources/z3_findings.json`](./sources/z3_findings.json)).

### 2.1 Corner 1: Kleene–Hopf Bialgebras (The 2×2 Convolution Star Phase Diagram)

In a classical Hopf algebra, Takeuchi's formula expresses the antipode $S$ as an alternating convolution series $S = \sum_{n \ge 0} (-1)^n (\mathrm{id} - \eta\epsilon)^{*n}$, which cannot exist without `HasNeg`. In an **idempotent semibialgebra** $(B, \mathbf{0}, \oplus, \mathbf{1}, \mu, \Delta, \epsilon)$, the convolution algebra $(\operatorname{End}(B), \oplus, *)$ is an idempotent semiring where $\mathrm{id}$ admits a **convolution Kleene star** $\circledast$:

$$\circledast \;=\; \mathrm{id}^{*_*} \;=\; \bigoplus_{n \ge 0} \mu^{(n)} \circ \Delta^{(n)} \;=\; \bigoplus_{n \ge 0} \psi_n$$

satisfying Kozen-style convolution unfold and induction laws:

$$\eta\epsilon \oplus (\mathrm{id} * \circledast) = \circledast = \eta\epsilon \oplus (\circledast * \mathrm{id}), \qquad g \oplus (\mathrm{id} * f) \le f \implies \circledast * g \le f.$$

Operationally, $\Delta$ models **FORK**, $\mu$ models **JOIN**, $\psi_n$ is an $n$-way fork–join barrier, and $\circledast$ is **unbounded dynamic fork–join closure**. Empirical testing across all four commutativity/cocommutativity quadrants reveals a sharp **2×2 phase transition**:

| $\mu$ Commutative? | $\Delta$ Cocommutative? | $\circledast$ vs. $\mu$ | $\circledast$ vs. $\Delta$ | $\circledast^2 = \circledast$? | Canonical Model |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Yes** | **Yes** | Exact Hom | Exact Co-Hom | **Yes** | Group-like monoids (**classical Kleene algebra** as subvariety) |
| **Yes** | **No** | **Exact Hom** | **Strictly Lax** ($(\circledast\otimes\circledast)\Delta \lneq \Delta\circledast$) | **Yes** | Shuffle–Deconcatenation (parallel trace reordering; $16 < 24$ splits on `'abc'`) |
| **No** | **Yes** | **Strictly Lax** ($\circledast(x)\circledast(y) \lneq \circledast(xy)$) | **Exact Co-Hom** | **Yes** | Concatenation–Unshuffle (`['ab'] < ['ab', 'ba']`) |
| **No** | **No** | **Neither** | **Neither** | **No** | Non-commutative matrix bialgebra $\mathcal{O}_{\mathrm{nc}}(M_2)$ |

**Automata discovery in $\mathcal{O}_{\mathrm{nc}}(M_2)$:** With generators $e_{ij}$, $\Delta(e_{ij}) = \bigoplus_k e_{ik} \otimes e_{kj}$, and concatenation $\mu$, $\psi_k(e_{ij})$ equals the exact set of length-$k$ walks from $i$ to $j$, so $\circledast(e_{ij})$ is the regular language of all $i \to j$ paths. However, $\psi_2(\psi_2(e_{01})) \neq \psi_4(e_{01})$: applying $\circledast$ twice jumps from 1D paths to 2-strand braided walks. Thus **idempotence of $\circledast$ is conserved strictly on the semi-commutative L-shaped boundary** (commutative or cocommutative).

---

### 2.2 Corner 2: Jordan Quantales & The Provably Exceptional 5-Element Model $E_5$

Under `LawIdempotent`, the anticommutator $A \circ B = AB \oplus BA$ eliminates the $\frac{1}{2}$ denominator required by classical Jordan algebras ($A \circ A = A^2$), remains power-associative on matrices, and fuses associative residuals into a single **symmetric Jordan residual** $A \multimap_\circ C = (A \backslash C) \wedge (C / A)$.

Z3 finite-model search established two sharp minimal landmarks:

1. **$J_4$ — Minimal Non-Associative Jordan–Kleene Quantale** (`n=3 UNSAT`, `n=4 SAT`):
   On the chain $0 < \varepsilon < 1 < \top$ ($\oplus = \max$) with $\varepsilon \circ \varepsilon = 0$, $\varepsilon \circ \top = 1$, $\top \circ \top = \top$. Strictly non-associative since $(\varepsilon \circ \varepsilon) \circ \top = 0 \neq \varepsilon = \varepsilon \circ (\varepsilon \circ \top)$. Embeds into $2 \times 2$ Boolean matrices under $AB \cup BA$ (special).

2. **The Endomorphism-Square Specialness Criterion (Theorem):**
   Let $J$ be any idempotent Jordan semiring embedding into $Q^+$ ($a \circ b = ab \oplus ba$) for *any* associative idempotent semiring $Q$. Because $u \le v \iff u \oplus v = v$ is preserved by any homomorphism:
   $$a \circ x \le a \implies (ax \le a \text{ and } xa \le a) \implies (ax^2 \le a \text{ and } x^2 a \le a) \implies a \circ (x \circ x) \le a.$$
   Taking $x = a \multimap_\circ a$ in a Jordan quantale yields **Pratt's pure induction invariant** $(a \multimap_\circ a)^2 \le (a \multimap_\circ a)$ and $(a \multimap_\circ a)^* \le (a \multimap_\circ a)$ for **every special Jordan quantale**.

3. **$E_5$ — Minimal Provably Exceptional (Non-Special) Jordan Quantale** (`n=4 UNSAT`, `n=5 SAT` in `0.36s`):
   - **Poset:** Pentagon $N_5$ with $0 < 1 < v < \top$ and $0 < u < \top$ ($u$ incomparable to $1, v$).
   - **Product:** $u \circ u = 1$, $u \circ v = u$, $v \circ v = \top$, $x \circ \top = \top$ ($x \neq 0$).
   - **Verification:** Satisfies commutativity, distributivity, exact Jordan identity, 4th- and 5th-power associativity, exact Galois residuals, and Kozen Kleene-star induction.
   - **Non-specialness witness:** $u \circ v = u \le u$ (so $v = u \multimap_\circ u$), yet $u \circ (v \circ v) = u \circ \top = \top \not\le u$, and $(u \multimap_\circ u)^* = v^* = \top \not\le v$.
   - **Significance:** $E_5$ is a 5-element subtraction-free analogue of the 27-dimensional Albert algebra $H_3(\mathbb{O})$, proving that **Pratt's pure induction axiom acts as an exact subtraction-free specialness separator**.

4. **4th-Power Associativity Lower Bound:** Z3 proved `UNSAT` for any idempotent Jordan semiring violating $(x^2)^2 = x(x \cdot x^2)$ up to $n = 6$ (unlike characteristic-2 rings).

---

### 2.3 Corner 3: Alternative Quantales — The 3-Tier Shattering of Artin's Theorem

In classical rings with `HasNeg`, **Artin's Theorem (1931)** proves that left + right alternativity ($(xx)y = x(xy)$ and $(yx)x = y(xx)$) automatically imply flexibility $(xy)x = x(yx)$, 2-generator associativity, and all three Moufang identities.

Z3 proved that dropping `HasNeg` **shatters Artin's Theorem into three strictly distinct subtraction-free varieties**:

| Tier | Axioms Satisfied | Axioms Violated | Minimal Witness | Z3 Bounds |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Artin-Alternative Quantale** | Left/Right Alternative, Galois `ldiv`/`rdiv` | **Flexibility**, Moufang, Artin 2-gen | **$A_5$** (chain $0 < c < b < a < 1$; $(ab)a = c \neq 0 = a(ba)$) | $n=3, 4$ UNSAT; $n=5$ SAT |
| **Tier 2: Flexible-Alternative Quantale** | Left/Right Alternative + **Flexibility**, Galois `ldiv`/`rdiv` | **Moufang** | **$F_5$** (chain $0 < 2 < 4 < 1 < 3$) | $n=4$ UNSAT; $n=5$ SAT |
| **Tier 3: Moufang Quantale ("Tropical Octonion")** | Alternative + Flexible + **All 3 Moufang** + **Artin 2-gen (`True`!)**, Galois `ldiv`/`rdiv` | **Associativity** on single triple $(2, 4, 5)$: $(2 \cdot 4) \cdot 5 = 1 \neq 0 = 2 \cdot (4 \cdot 5)$ | **$M_7$** (chain $0 < 1 < 2 < 3 < 4 < 5 < 6 = \mathbf{1}$) | $n=5$ general UNSAT; $n=5, 6$ chain UNSAT; $n=7$ chain SAT (`1.88s`) |
| **Tier 4: Associative Quantale** | Full associativity | — | Classical corner (`RelationActionAlgebra`) | — |

---

### 2.4 Corner 4: Idempotent Differential–Kleene Algebras & The Unital-Drift Law

Under `LawIdempotent`, binomial coefficients $\binom{n}{k}$ collapse to $\mathbf{1}$, eliminating the $n!$ denominator of classical Lie exponentials $e^D = \sum \frac{1}{n!} D^n$. For *any* continuous positive Leibniz derivation $D(ab) = D(a)b \oplus a D(b)$:

$$D^*(ab) = D^*(a)\,D^*(b) \qquad \text{and} \qquad D^*(D^*(a)) = D^*(a).$$

Because $D(\mathbf{1}) = D(\mathbf{1}) \oplus D(\mathbf{1})$ no longer forces $D(\mathbf{1}) = \mathbf{0}$, Z3 uncovered two non-ring phenomena:
1. **$D_3$ (`n=3 SAT`):** Non-inner unital-drift derivation on idempotent dual numbers $\{0 < \varepsilon < 1\}$ ($\varepsilon^2 = 0$) with $D(1) = \varepsilon$, $D(\varepsilon) = \varepsilon \neq D(1)\cdot\varepsilon = 0$.
2. **$DK_4$ (`n=4 SAT`) — Exact Unital-Drift Star Law:** Naive commutation $D^*(a^*) = (D^*(a))^*$ fails whenever $D(\mathbf{1}) > \mathbf{0}$ (since $D^*(0^*) = D^*(\mathbf{1}) = \top \neq \mathbf{1} = (D^*(0))^*$). Because $D^*$ is a multiplicative *semi*-homomorphism (not unital), the exact conservation law is:
   $$D^*(a^*) \;=\; D^*(\mathbf{1}) \cdot \bigl(D^*(a)\bigr)^*$$
   which reduces to $D^*(a^*) = (D^*(a))^*$ precisely when $D(\mathbf{1}) = \mathbf{0}$.

---

## 3. Architectural Synthesis & AlgebraX Protocol Audit

To test how AlgebraX's live Layer-1/Layer-2 protocol architecture (`src/algebrax/algebra/`) handles these four corners, we built and executed [`playground/idempotent_corners_prototype.py`](../../../playground/idempotent_corners_prototype.py) (archived at [`sources/idempotent_corners_prototype.py`](./sources/idempotent_corners_prototype.py)).

### 3.1 Live `isinstance()` Audit Results

```text
Structure                  | Semiring | CommSemi | KleeneAl | ActionAl | JordanAl | Alternat | Bialgebr | HopfAlge
---------------------------------------------------------------------------------------------------------------------
KleeneHopf(Shuffle)        |   YES    |    .     |    .     |    .     |    .     |    .     |    .     |    .    
J_4 (JordanQuantale)       |   YES    |   YES    |   YES    |   YES    |    .     |    .     |    .     |    .    
E_5 (ExceptionalJordan)    |   YES    |   YES    |   YES    |   YES    |    .     |    .     |    .     |    .    
A_5 (Alt-NonFlex)          |   YES    |    .     |   YES    |   YES    |    .     |    .     |    .     |    .    
F_5 (Alt-NonMoufang)       |   YES    |    .     |   YES    |   YES    |    .     |    .     |    .     |    .    
M_7 (MoufangQuantale)      |   YES    |    .     |   YES    |   YES    |    .     |    .     |    .     |    .    
DK_4 (DiffKleene)          |   YES    |    .     |    .     |    .     |    .     |    .     |    .     |    .    
```

### 3.2 Three Structural Findings for AlgebraX (Grand Council Review)

1. **🔬 Popper & 🧩 Russell — False-Positive Associativity Blindness in Semiring/Kleene/Action Protocols:**
   `Semiring`, `CommSemiring`, `KleeneAlgebra`, and `ActionAlgebra` do **not** inherit [`LawAssociative`](../../../src/algebrax/algebra/_mixins.py) (unlike `Ring`, `Bialgebra`, and `HopfAlgebra`). Consequently, strictly non-associative structures ($J_4$, $E_5$, $A_5$, $F_5$, $M_7$) **falsely satisfy `isinstance(..., Semiring)`, `isinstance(..., KleeneAlgebra)`, and `isinstance(..., ActionAlgebra)`**—even though $E_5$ explicitly violates Pratt's pure induction axiom documented on `ActionAlgebra`!
2. **⚖️ Noether & 🛡️ The Golem — Over-Coupled `HasNeg` / `HasScale` on Non-Associative & Coalgebraic Protocols:**
   `JordanAlgebra`, `AlternativeAlgebra`, `Coalgebra`, `Bialgebra`, and `HopfAlgebra` hard-wire `HasNeg` and `HasScale`, locking out subtraction-free semibialgebras and quantales. Under [EP-0005](../../../docs/proposals/EP-0005-universal-algebraic-protocol-architecture.md)'s Law of Flat Protocol Composition, subtraction-free counterparts can be added cleanly as flat Layer-2 compositions with **zero** diamond inheritance.
3. **🧭 The Explorer — Missing Equational Law Witnesses in `_mixins.py`:**
   The 3-tier Artin split ($A_5 \subsetneq F_5 \subsetneq M_7$) and the 2×2 Kleene–Hopf phase diagram prove that four atomic witnesses are independent in the subtraction-free world:
   - `LawFlexible` ($(xy)x = x(yx)$)
   - `LawMoufang` (the three Moufang identities)
   - `LawCocommutative` ($\tau \circ \Delta = \Delta$)
   - `HasConvStar` (or distinguishing multiplicative `star` from convolution `conv_star` $\circledast$ on bialgebras so Kleene–Hopf structures do not collide with `HasStar`!).

---

## 4. The Verdict / Actionable Design

1. **Immediate Protocol Hygiene (Candidate follow-up to EP-0250):**
   - Evaluate whether `Semiring`, `CommSemiring`, `KleeneAlgebra`, and `ActionAlgebra` should adopt `LawAssociative` (consistent with `Ring`, `Bialgebra`, `HopfAlgebra`)—or document explicitly that un-witnessed duck-typed `Semiring` protocols defer associativity to `verify_semiring_laws` while `ActionAlgebra` requires `LawAssociative` to guarantee Pratt's pure induction soundness.
2. **Zero-Dependency Exploration Status (No Core Bloat):**
   - Keep `z3-solver` strictly in dev/verification tooling (`tests/verifications/` and `references/explorations/`); the runnable prototypes in `playground/idempotent_corners_prototype.py` require **zero external dependencies**.
3. **Future Standards-Track EP Candidates (Post-Phase 8.5 / Phase 12 Frontier):**
   - **Candidate EP-0260 (Subtraction-Free Non-Associative Quantales & Law Witnesses):** Add `LawFlexible`, `LawMoufang`, `JordanQuantale`, and `AlternativeQuantale` (plus `TropicalMatrixJordanQuantale`) to `algebrax.algebra` and register $J_4, E_5, A_5, F_5, M_7$ as canonical falsification fixtures in `algebrax.verification`.
   - **Candidate EP-0261 (Idempotent Semibialgebras & Kleene–Hopf Algebras):** Add `LawCocommutative`, `Semibialgebra`, and `KleeneHopfBialgebra` (with `ShuffleDeconcat`, `ConcatUnshuffle`, and $\mathcal{O}_{\mathrm{nc}}(M_n)$ path automata) as the subtraction-free dual of EP-0206.
   - **Candidate EP-0262 (Idempotent Differential–Kleene Algebras):** Couple Phase 11's `HasDerivation` with `KleeneAlgebra` and verify the unital-drift law $D^*(a^*) = D^*(\mathbf{1}) \cdot (D^*(a))^*$.

---

## 5. Related Enhancement Proposals & Bundled Artifacts

### Related EPs
- [EP-0005: Universal Algebraic Protocol Architecture](../../../docs/proposals/EP-0005-universal-algebraic-protocol-architecture.md)
- [EP-0197: Decoupled Semiring Foundations, Star Semirings & Kleene Algebras](../../../docs/proposals/EP-0197-decoupled-semiring-foundations-star-semirings-and-kleene-algebras.md)
- [EP-0198: Generalized Closure Operators & Action Algebras](../../../docs/proposals/EP-0198-generalized-closure-operators-kleene-plus-matrix-star-and-action-algebras.md)
- [EP-0204: Non-Associative Quantum Algebras](../../../docs/proposals/EP-0204-non-associative-quantum-algebras-jordan-octonions-poisson.md)
- [EP-0206: Coalgebras, Bialgebras & Hopf Algebras](../../../docs/proposals/EP-0206-coalgebras-bialgebras-and-hopf-algebras.md)
- [EP-0250: Protocol Integrity, Law Witnesses & Algebraic Soundness](../../../docs/proposals/EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md)

### Bundled Provenance Artifacts
- [`sources/z3_corner_hunter.py`](./sources/z3_corner_hunter.py) — Reproducible Z3 5.4.1 finite-model hunter proving all UNSAT lower bounds and synthesizing $J_4, E_5, A_5, F_5, M_7, D_3, DK_4$.
- [`sources/z3_findings.json`](./sources/z3_findings.json) — Machine-verified JSON output containing exact addition/multiplication/residual/derivation tables and solver timings.
- [`sources/idempotent_corners_prototype.py`](./sources/idempotent_corners_prototype.py) — Provenance archive of the live AlgebraX prototype and Layer-2 protocol audit (mirrored at [`playground/idempotent_corners_prototype.py`](../../../playground/idempotent_corners_prototype.py)).
