# EXP-0014: Uncharted Continents & Protocol Shells — Semigroups, Homological Algebra, Symmetric Functions, Coding Theory, Free Probability & Higher Categories

| Field           | Value                                                                                                                                                                                                                                   |
|:----------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0014                                                                                                                                                                                                                                    |
| **Title**       | Uncharted Continents & Protocol Shells — Semigroups, Homological Algebra, Symmetric Functions, Coding Theory, Free Probability & Higher Categories                                                                                      |
| **Author**      | Eran Rivlis, Antigravity AI (The Explorer & Grand Council)                                                                                                                                                                              |
| **Status**      | Active                                                                                                                                                                                                                                  |
| **Type**        | Architectural & Research Exploration                                                                                                                                                                                                    |
| **Created**     | 2026-11-28                                                                                                                                                                                                                              |
| **Updated**     | 2026-11-28                                                                                                                                                                                                                              |
| **Related EPs** | [EP-0005](../../../docs/proposals/EP-0005-universal-algebraic-protocol-architecture.md), [EP-0099](../../../docs/proposals/EP-0099-expansion-roadmap.md), [EP-0250](../../../docs/proposals/EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md), [EP-0260](../../../docs/proposals/EP-0260-lattice-protocol-soundness-finite-posets-and-lattices.md) |

---

## 1. Abstract & Context

### 1.1 The Cartographic Question
Following the formalization of **Phase 12** ([`EXP-0012`](../EXP-0012-subtraction-free-idempotent-corners/README.md) & [`EXP-0013`](../EXP-0013-lattice-and-order-continent/README.md), `EP-0260`–`EP-0264`), which promoted `algebrax.lattice` from a protocol-only shell and sparse-dictionary helper file into a planned 5-region order-theoretic continent, the Architect asked:

> *"What else is missing in AlgebraX in the same vein?"*

In the tradition of [`EXP-0002: Off the Map`](../EXP-0002-off-the-map-frontiers/README.md), this living atlas inventories the remaining **protocol-only shells**, **thin single-file islands**, and **uncharted adjacent continents** across `src/algebrax/`—grounded in a reproducible AST & runtime `isinstance()` audit ([`sources/codebase_surface_audit.py`](./sources/codebase_surface_audit.py) → [`sources/surface_audit_snapshot.json`](./sources/surface_audit_snapshot.json)).

### 1.2 Empirical Ground-Truth Audit (`2026-11-28`)
Running `sources/codebase_surface_audit.py` across `src/algebrax/` surfaced two objective structural facts:

1. **Four Protocol-Only Shells (Zero Concrete Classes, Zero Public Functions):**
   - [`src/algebrax/algebra/_magma.py`](../../../src/algebrax/algebra/_magma.py) (`161` LOC, 8 protocols, `0` concrete classes)
   - [`src/algebrax/algebra/_monoid.py`](../../../src/algebrax/algebra/_monoid.py) (`126` LOC, 6 protocols, `0` concrete classes)
   - [`src/algebrax/algebra/_module.py`](../../../src/algebrax/algebra/_module.py) (`143` LOC, 5 protocols, `0` concrete classes)
   - [`src/algebrax/algebra/_lattice.py`](../../../src/algebrax/algebra/_lattice.py) (`121` LOC, 6 protocols, `0` concrete classes — addressed by Phase 12 `EP-0260`)
2. **Nine Confirmed Live Protocol Isomers (`9/9` False Positives at Runtime):**
   Because these protocols omit Layer-1 law witnesses (`LawAssociative`, `LawCommutative`, `LawIdempotent`, `LawDistributive`, field-scalar witness), deliberately violating objects falsely pass `isinstance(...)`:
   - `Magma == Semigroup == Band` (non-associative, non-idempotent subtraction satisfies all three)
   - `AddMagma == AddSemigroup`, `OpMagma == OpSemigroup`
   - `Monoid == CommMonoid`, `AddMonoid == AddCommMonoid`, `OpMonoid == OpCommMonoid`
   - `Module == VectorSpace` (a $\mathbb{Z}$-module over a non-field passes `isinstance(z_mod, VectorSpace)`)
   - `Lattice == DistributiveLattice` (non-modular $N_5$ passes `isinstance(n5, DistributiveLattice)` — fixed in `EP-0260`)
3. **Thin Single-File Domain Islands:**
   - [`src/algebrax/galois.py`](../../../src/algebrax/galois.py): `49` LOC (`gf_matrix_mul` only)
   - [`src/algebrax/automata.py`](../../../src/algebrax/automata.py): `254` LOC (5 functions: `dfa_step`, `nfa_step`, `simulate_dfa`, `simulate_nfa`, `nfa_closure`)
   - [`src/algebrax/probability.py`](../../../src/algebrax/probability.py): `394` LOC (classical discrete probability only; `EXP-0002` Terra II unbuilt)
   - [`src/algebrax/category/`](../../../src/algebrax/category/__init__.py): 7 compact modules (`~120–184` LOC each) with no `NaturalTransformation`, `Adjunction`, `Monad`, limits/colimits, or monoidal string diagrams (`EXP-0002` Terra III unbuilt)

---

## 2. Exploration & Options Analysis (Seven Uncharted Continents)

```text
+---------------------------------------------------------------------------------------------------+
|                             ALGEBRAX UNCHARTED CONTINENT ATLAS                                    |
|                                                                                                   |
|  [A. EXISTING PROTOCOL SHELLS & THIN ISLANDS]                                                     |
|   Terra I   : Semigroups, Monoids, Quasigroups & Weighted Automata   (_magma, _monoid, automata)  |
|   Terra II  : Exact PID Modules (SNF/HNF) & Homological Algebra      (_module, topology/homology) |
|   Terra III : Algebraic Coding Theory, Integer Lattices & Number Fld (galois.py, _padic.py)       |
|   Terra IV  : Higher Categories, Monads, Topos & Operads             (category/, EXP-0002 T-III)  |
|                                                                                                   |
|  [B. HIGH-SYNERGY ADJACENT CONTINENTS]                                                            |
|   Terra V   : Algebraic Combinatorics & Symmetric Functions          (group/, rep/, _hopf, P12)   |
|   Terra VI  : Non-Commutative & Free Probability                     (probability, P12 NC(n))     |
|   Terra VII : Universal Algebra & Equational Term Rewriting          (P12 Con(A)/Sub(A), HSP)     |
+---------------------------------------------------------------------------------------------------+
```

### Terra I: Semigroups, Monoids, Quasigroups & Weighted Automata
* **Existing Anchor:** `_magma.py` (6 isomers), `_monoid.py` (6 isomers), `automata.py` (5 functions), `KleeneAlgebra` / `ActionAlgebra`.
* **Mathematical Machinery:**
  - **Finite Semigroups & Monoids:** Transformation monoids $T_n$, Green's relations ($\mathcal{L}, \mathcal{R}, \mathcal{H}, \mathcal{D}, \mathcal{J}$) and egg-box decompositions, regular/inverse semigroups (partial bijections via Wagner–Preston), Rees matrix semigroups $\mathcal{M}^0(G; I, \Lambda; P)$, and Krohn–Rhodes wreath-product cascades.
  - **Weighted Automata & Rational Series:** Syntactic monoids (unifying `automata` $\leftrightarrow$ finite monoids), Brzozowski/Hopcroft minimization, formal power series over arbitrary `Semiring[V]`, Kleene's theorem (Regex $\leftrightarrow$ NFA $\leftrightarrow$ `KleeneAlgebra`), and Knuth–Bendix monoid rewriting.
  - **Quasigroups & Loops:** Latin squares, isotopisms, and Moufang loops (bridging `algebrax.group/` to `OctonionAlgebra` and `EP-0264`).
* **Protocol Hardening:** Eliminate all 7 magma/monoid isomers (`LawAssociative`, `LawCommutative`, `LawIdempotent`, `LawAddAssociative`, `LawAddCommutative`).

### Terra II: Exact PID Linear Algebra (SNF/HNF) & Homological Algebra
* **Existing Anchor:** `_module.py` (`Module == VectorSpace` isomer, 0 concrete classes), `topology/homology.py` (currently $\mathbb{Q}/\mathbb{F}_p$ Betti numbers only), `algebra/_groebner.py` (`EP-0220`).
* **Mathematical Machinery:**
  - **PID Normal Forms:** Exact Hermite Normal Form (HNF) and **Smith Normal Form (SNF)** over $\mathbb{Z}$ and univariate $k[x]$ — unlocking **exact integral homology $H_k(X; \mathbb{Z})$ with torsion invariant factors** (e.g., $\mathbb{Z}/2\mathbb{Z}$ on $\mathbb{R}P^2$ and the Klein bottle!) and the structure theorem for finitely generated abelian groups.
  - **Homological Algebra:** Free resolutions of $k[x_1,\dots,x_n]$-modules via Schreyer's theorem (built on `EP-0220` Gröbner bases), syzygy modules & graded Betti tables, $\operatorname{Ext}^n_R(M, N)$ and $\operatorname{Tor}_n^R(M, N)$, Group cohomology $H^n(G, M)$, Chevalley–Eilenberg Lie cohomology, and Hochschild (co)homology.

### Terra III: Algebraic Coding Theory, Integer Lattices & Number Fields
* **Existing Anchor:** `galois.py` (49 LOC), `ModularField`/`GaloisField`, `_padic.py`, `EP-0231` (exact NTT), `EP-0263` (linear matroids).
* **Mathematical Machinery:**
  - **Algebraic Coding Theory:** Linear $[n, k, d]_q$ codes over `ModularField`/`GaloisField`, dual codes $C^\perp$, syndrome decoding, Hamming / Reed–Solomon / BCH / Golay codes, MacWilliams weight enumerator identity, and direct cryptomorphism to `EP-0263` linear matroids.
  - **Geometry of Numbers & Algebraic Number Theory:** LLL lattice basis reduction over $\mathbb{Z}^n$, rings of integers ($\mathbb{Z}[i]$, $\mathbb{Z}[\omega]$, quadratic/cyclotomic number fields $\mathbb{Q}(\sqrt{d}), \mathbb{Q}(\zeta_n)$), Dedekind ideal factorization & class groups, and elliptic curves $E(\mathbb{F}_p)$ (exact projective group law, Hasse bound, Weil pairing).

### Terra IV: Higher Categories, Monads, Elementary Topos & Operads
* **Existing Anchor:** `category/` (7 modules), `EP-0261` (`GaloisConnection`), `EP-0262` (`HeytingAlgebra` / `AlexandroffLocale`), `EP-0215` (braids), unfinished **`EXP-0002` Terra III**.
* **Mathematical Machinery:**
  - **2-Categorical Primitives:** Explicit `NaturalTransformation` (vertical/horizontal composition & interchange law), general `Adjunction` ($F \dashv G$, generalizing `GaloisConnection`), `Monad`/`Comonad` (Eilenberg–Moore & Kleisli), and finite limits/colimits (pullbacks, pushouts, equalizers).
  - **Elementary Topos & Presheaf Logic:** Subobject classifier $\Omega$ as a sheaf of `EP-0262` Heyting truth values over poset/cell sites (closing `EXP-0002` Terra III).
  - **Monoidal String Diagrams & Operads:** Symmetric monoidal categories, ZX-calculus rewrite diagrams, and algebraic operads ($\mathrm{Ass}, \mathrm{Comm}, \mathrm{Lie}, A_\infty$).

### Terra V: Algebraic Combinatorics & Symmetric Functions
* **Existing Anchor:** `group/` ($S_n$), `rep/` (character tables), `_hopf.py` (Hopf algebras), `EP-0260` (`FinitePoset`).
* **Mathematical Machinery:**
  - **Partitions & Young Tableaux:** Integer partitions, **Young's lattice** (as an `EP-0260` `FinitePoset`), Hook-Length Formula, Robinson–Schensted–Knuth (RSK) bijection, jeu de taquin.
  - **Ring of Symmetric Functions $\Lambda$:** All 5 classical bases ($m_\lambda, e_\lambda, h_\lambda, p_\lambda, s_\lambda$ Schur functions) in unboxed `dict[tuple[int, ...], V]` carriers, Jacobi–Trudi determinants, Kostka matrices, Littlewood–Richardson coefficients, and the **Murnaghan–Nakayama rule** (computing exact $S_n$ characters combinatorially as a cross-check oracle against `algebrax.rep`!).
  - **Combinatorial Hopf Algebras:** $\mathrm{Sym}, \mathrm{QSym}, \mathrm{NSym}$ implementing `EP-0206` Hopf protocols.

### Terra VI: Non-Commutative & Free Probability (`EXP-0002` Terra II Revival)
* **Existing Anchor:** `probability.py`, `EP-0149` (classical binomial moment semirings), `EP-0260` (Rota Möbius inversion).
* **Mathematical Machinery:**
  - **Non-Crossing Partition Lattice $\mathrm{NC}(n)$:** Kreweras complement and exact Rota Möbius function $\mu_{\mathrm{NC}}(0_n, 1_n) = (-1)^{n-1} C_{n-1}$ directly powered by `EP-0260`'s `FinitePoset`.
  - **Free Cumulants & Convolutions:** Moment–cumulant inversion via `poset.mobius_transform`, Voiculescu's $R$-transform (free additive convolution $\boxplus$) and $S$-transform (free multiplicative convolution $\boxtimes$), yielding exact Wigner Semicircle and Marchenko–Pastur moment sequences with zero Monte Carlo sampling.

### Terra VII: Universal Algebra & Equational Logic
* **Existing Anchor:** `EP-0260` (`FiniteLattice`), `EP-0005` (equational law witnesses), `EXP-0012` / `EP-0264` (finite algebraic models).
* **Mathematical Machinery:**
  - General finite $\Sigma$-algebras $(A, \{f_i\})$, congruence lattices $\operatorname{Con}(A)$ and subalgebra lattices $\operatorname{Sub}(A)$ returning `EP-0260` `FiniteLattice`, Birkhoff's HSP variety operators (homomorphic images, subalgebras, direct products), Maltsev condition detectors (congruence-permutable / modular / distributive), and Knuth–Bendix term-rewriting completion.

---

## 3. Architectural Synthesis & Constraint Alignment (Grand Council Review)

| Terra | Priority | Fixes Live Shells / Bugs? | Core Pillar Fit | Key Constraint / Synergy |
| :--- | :---: | :--- | :--- | :--- |
| **Terra I: Semigroups, Monoids & Automata** | **1** | **Yes** (`_magma`, `_monoid` 7 isomers + `automata.py`) | 🧩 Russell & ⚡ Shannon | Zero-dep bitmask/tuple transformation monoids; completes Tier-1 single-op foundations. |
| **Terra II: PID Modules (SNF/HNF) & Homological** | **2** | **Yes** (`_module` isomer + integral torsion in `homology.py`) | ⚖️ Noether & 🔬 Popper | Reuses `matrix/eliminate` & `EP-0220` Gröbner bases; zero external CAS deps. |
| **Terra V: Algebraic Combinatorics & $\Lambda$** | **3** | New continent | ⚖️ Noether & 🔬 Popper | Unboxed `dict[tuple[int,...], V]` basis carriers; combinatorial oracle for `rep/` $S_n$ characters. |
| **Terra VI: Free Probability & $\mathrm{NC}(n)$** | **4** | Closes `EXP-0002` Terra II | 🔬 Popper & ⚡ Shannon | Plugs directly into `EP-0260` Rota Möbius + `EP-0149` moment semirings. |
| **Terra III: Coding Theory, LLL & Number Fields** | **5** | Expands `galois.py` (49 LOC) & `_padic.py` | 🛡️ Golem & ⚡ Shannon | Reuses `ModularField`/`GaloisField`, `EP-0231` NTT, `EP-0263` linear matroids. |
| **Terra IV: Higher Categories, Topos & Operads** | **6** | Expands `category/` & closes `EXP-0002` Terra III | 🧩 Russell & 🧭 Explorer | Generalizes `EP-0261` Galois adjunctions + `EP-0262` Heyting locales. |
| **Terra VII: Universal Algebra & Rewriting** | **7** | Companion to Phase 12 & `EXP-0012` | 🧭 Explorer & 🔬 Popper | $\operatorname{Con}(A)$ and $\operatorname{Sub}(A)$ return `EP-0260` `FiniteLattice`. |

### The Dennis Point — Execution Discipline Before New EPs
At the time of this audit (`2026-11-28`), **Phases 9–12 already carry 15 `Draft` EPs** queued behind **Phase 8.5** (`EP-0253`–`EP-0255` `Accepted`):
- **Do NOT allocate EP numbers (`EP-0270+`) yet.** This document serves as a permanent, empirically grounded **radar & backlog map** (`Status: Active`), analogous to `EXP-0002`.
- **Execution Gate:** Complete Phase 8.5 (`EP-0253`–`EP-0255`), Phase 9 (`EP-0222`), and Phase 12 Wave 1 (`EP-0260`) before spinning any Terra from `EXP-0014` into a dedicated deep-dive exploration and Standards-Track EP series.
- **Immediate Quick Win (Optional):** When convenient, the 7 magma/monoid isomers (`_magma.py`, `_monoid.py`) and `Module == VectorSpace` isomer (`_module.py`) can be patched independently or folded into the first Terra I / Terra II EP.

---

## 4. The Verdict / Actionable Design

1. **Preserve as Permanent Cartography (`Status: Active`):** Keep `EXP-0014` as the master inventory of post-Phase-12 algebraic continents and remaining protocol shells, updated as individual Terras graduate into their own deep-dive explorations (`EXP-0015+`) and phases (`Phase 13+`).
2. **Recommended Promotion Order (When Ready After Phase 8.5 / 9 / 12-Wave-1):**
   1. **Terra I (Semigroups, Monoids & Weighted Automata)** — highest structural hygiene payoff (closes 7 live protocol isomers + promotes `automata.py`).
   2. **Terra II (PID Normal Forms SNF/HNF & Homological Algebra)** — closes `_module.py` shell and unlocks exact $\mathbb{Z}$-torsion homology in `topology/homology.py`.
   3. **Terra V (Symmetric Functions & Young Combinatorics)** or **Terra VI (Free Probability on $\mathrm{NC}(n)$)** — highest cross-continent synergy once `EP-0260` (`FinitePoset` / Rota Möbius) is live.
   4. **Terra III (Coding Theory, LLL & Number Fields)**, **Terra IV (Higher Categories, Topos & Operads)**, and **Terra VII (Universal Algebra)**.

---

## 5. Related Enhancement Proposals & Bundled Artifacts

### Related Explorations & EPs
- [EXP-0002: Off the Map — Quantum Groups, Free Probability, Topos Logics & Tropical Cryptosystems](../EXP-0002-off-the-map-frontiers/README.md)
- [EXP-0012: Subtraction-Free Idempotent Corners](../EXP-0012-subtraction-free-idempotent-corners/README.md)
- [EXP-0013: Expanding the Lattice & Order Continent](../EXP-0013-lattice-and-order-continent/README.md)
- [EP-0005: Universal Algebraic Protocol Architecture](../../../docs/proposals/EP-0005-universal-algebraic-protocol-architecture.md)
- [EP-0099: Master Expansion Roadmap](../../../docs/proposals/EP-0099-expansion-roadmap.md)
- [EP-0260: Lattice Protocol Soundness, Package Promotion & Finite Posets/Lattices](../../../docs/proposals/EP-0260-lattice-protocol-soundness-finite-posets-and-lattices.md)

### Bundled Provenance Artifacts
- [`sources/codebase_surface_audit.py`](./sources/codebase_surface_audit.py) — Reproducible AST & runtime `isinstance()` audit script verifying the 4 protocol-only shells, thin islands, and 9/9 live protocol isomer false positives.
- [`sources/surface_audit_snapshot.json`](./sources/surface_audit_snapshot.json) — Machine-generated snapshot of module LOC, protocol/class counts, and live isomer results as of `2026-11-28`.
