# EXP-0009: Scientific Bibliography & Source Repository

This document records the primary mathematical and algorithmic sources for **EXP-0009 (Algebraic & Tropical Varieties)**. Open-access arXiv papers cited below are archived locally in [`papers/`](../papers/).

---

## Index of Archived Primary Papers

| Identifier | Title | Authors & Year | Venue / Identifier | Local Archive | Relevance to EXP-0009 |
|:-----------|:------|:---------------|:-------------------|:--------------|:----------------------|
| **[ALBRECHT-2010]** | *F4/5* | Martin Albrecht, John Perry (2010) | `arXiv:1006.4933 [cs.SC]` | [`papers/Albrecht_Perry_2010_F4_5.pdf`](../papers/Albrecht_Perry_2010_F4_5.pdf) | Unifies F4 Macaulay matrix reduction with F5 syzygy criteria; guides sparse linear-algebraic Gröbner design |
| **[COX-2020]** | *Stickelberger and the Eigenvalue Theorem* | David A. Cox (2020) | `arXiv:2007.12573 [math.AC]`, *Commutative Algebra* (Springer, 2021) | [`papers/Cox_2020_Stickelberger_Eigenvalue_Theorem.pdf`](../papers/Cox_2020_Stickelberger_Eigenvalue_Theorem.pdf) | Proves and contextualizes Stickelberger's Eigenvalue Theorem linking $k[x]/I$ multiplication maps to $V(I)$ |
| **[BENDER-2021]** | *Yet another eigenvalue algorithm for solving polynomial systems* | Matías R. Bender, Simon Telen (2021) | `arXiv:2105.08472 [math.NA]` | [`papers/Bender_Telen_2021_Eigenvalue_Polynomial_Systems.pdf`](../papers/Bender_Telen_2021_Eigenvalue_Polynomial_Systems.pdf) | Symbolic–numeric stability analysis for companion/multiplication matrices and simultaneous diagonalization |
| **[RGST-2003]** | *First steps in tropical geometry* | Jürgen Richter-Gebert, Bernd Sturmfels, Thorsten Theobald (2003) | `arXiv:math/0306366 [math.AG]`, *Contemp. Math.* 377 (2005) | [`papers/RichterGebert_Sturmfels_Theobald_2003_First_Steps_Tropical_Geometry.pdf`](../papers/RichterGebert_Sturmfels_Theobald_2003_First_Steps_Tropical_Geometry.pdf) | Foundational formulation of tropical varieties over $(\mathbb{R}, \min, +)$, Newton subdivisions, and vertex balancing |

---

## Foundational Textbooks & Reference Systems

* **[FAUGERE-1999]** Jean-Charles Faugère, *"A new efficient algorithm for computing Gröbner bases ($F_4$)"*, *Journal of Pure and Applied Algebra*, 139(1–3): 61–88 (1999), DOI: `10.1016/S0022-4049(99)00005-5`.
  * Introduces simultaneous S-polynomial reduction via symbolic preprocessing and sparse Gaussian elimination on Macaulay matrices.
* **[CLO-2005]** David A. Cox, John Little, Donal O'Shea, *Using Algebraic Geometry* (2nd ed., GTM 185, Springer, 2005).
  * Canonical reference for quotient ring bases, Stickelberger companion matrices (Ch. 2, §4), and resultant/eigenvalue solvers.
* **[CLO-2015]** David A. Cox, John Little, Donal O'Shea, *Ideals, Varieties, and Algorithms* (4th ed., Springer, 2015).
  * Canonical reference for monomial orders, Buchberger's criteria, Hilbert's Nullstellensatz, and the Ideal–Variety correspondence.
* **[STURMFELS-2002]** Bernd Sturmfels, *Solving Systems of Polynomial Equations* (CBMS Regional Conference Series 97, AMS, 2002).
  * Bridges Gröbner bases, companion matrices, toric varieties, and numerical/tropical roots.
* **[MATHLIB-MV]** Lean 4 Mathlib `MvPolynomial` & `AlgebraicGeometry.AffineScheme` (`Mathlib.RingTheory.MvPolynomial`, `Mathlib.AlgebraicGeometry.AffineSpace`).
  * Reference taxonomy separating multivariate polynomial rings (`Finsupp` monoid algebra over $\mathbb{N}^n$), ideals, quotients, and affine zero loci.
