# Annotated Bibliography — EXP-0011: Differential & Ore Algebras

## Primary Archived Papers (`papers/`)

1. **[SATTELBERGER-2019]** Anna-Laura Sattelberger and Bernd Sturmfels, *"D-Modules and Holonomic Functions"*, arXiv:1910.01395v2, 2019.
   - **Local Archive:** [`papers/Sattelberger_Sturmfels_2019_DModules_Holonomic.pdf`](../papers/Sattelberger_Sturmfels_2019_DModules_Holonomic.pdf)
   - **Relevance to AlgebraX:** Introduces left ideals and Gröbner bases in the Weyl algebra $D_n = k\langle x_1, \dots, x_n, \partial_1, \dots, \partial_n \rangle$, holonomic rank, characteristic varieties, and D-module integration algorithms directly generalizing commutative `GroebnerIdeal` (`EP-0220`).

2. **[KAUERS-2013]** Manuel Kauers, Maximilian Jaroschek, and Fredrik Johansson, *"Ore Polynomials in Sage"*, arXiv:1306.4263, 2013.
   - **Local Archive:** [`papers/Kauers_Jaroschek_Johansson_2013_Ore_Polynomials.pdf`](../papers/Kauers_Jaroschek_Johansson_2013_Ore_Polynomials.pdf)
   - **Relevance to AlgebraX:** Canonical design blueprint for skew-polynomial Ore algebras $R[\partial; \sigma, \delta]$ unifying differential operators ($\sigma=\mathrm{id}, \delta=d/dx$), shift/recurrence operators ($\sigma(n)=n+1, \delta=0$), and $q$-difference operators, including `gcrd`, `lclm`, and D-finite closure operations (addition & multiplication of holonomic functions).

3. **[KOUTSCHAN-2013]** Christoph Koutschan, *"Creative Telescoping for Holonomic Functions"*, arXiv:1307.4554, 2013.
   - **Local Archive:** [`papers/Koutschan_2013_Creative_Telescoping_Holonomic.pdf`](../papers/Koutschan_2013_Creative_Telescoping_Holonomic.pdf)
   - **Relevance to AlgebraX:** Explains Ore Gröbner elimination and Chyzak's creative telescoping algorithm for certifying definite sums and integrals of special functions automatically.

4. **[BOSTAN-2018]** Alin Bostan, Frédéric Chyzak, Pierre Lairez, and Bruno Salvy, *"Generalized Hermite Reduction, Creative Telescoping and Definite Integration of D-Finite Functions"*, *ISSAC 2018*, arXiv:1805.03445.
   - **Local Archive:** [`papers/Bostan_Chyzak_Lairez_Salvy_2018_Generalized_Hermite.pdf`](../papers/Bostan_Chyzak_Lairez_Salvy_2018_Generalized_Hermite.pdf)
   - **Relevance to AlgebraX:** Establishes exact algebraic Hermite reduction over rational and D-finite functions using purely Euclidean GCD and extended Bezout identities (`Field` arithmetic, zero factorization over $\mathbb{C}$).

---

## Foundational Textbooks & Monographs

5. **[BRONSTEIN-2005]** Manuel Bronstein, *Symbolic Integration I: Transcendental Functions*, 2nd ed., Springer, 2005.
   - **Relevance:** Definitive reference on differential fields $(K, \delta)$, Hermite reduction, Rothstein–Trager logarithmic residue integration, and algebraic differential towers.

6. **[SST-2000]** Mutsumi Saito, Bernd Sturmfels, and Nobuki Takayama, *Gröbner Deformations of Hypergeometric Differential Equations*, Springer, 2000.
   - **Relevance:** Standard reference on Weyl algebra Gröbner bases, indicial polynomials, and series solutions of holonomic differential equations.
