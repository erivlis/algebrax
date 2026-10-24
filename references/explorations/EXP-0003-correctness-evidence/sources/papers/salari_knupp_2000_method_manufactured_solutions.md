# Code Verification by the Method of Manufactured Solutions

| Field | Value |
|:---|:---|
| **Citation** | Kambiz Salari, Patrick Knupp. *Code Verification by the Method of Manufactured Solutions*. Sandia National Laboratories Technical Report SAND2000-1444, Albuquerque, NM, June 2000. |
| **DOI / OSTI** | [10.2172/759450](https://doi.org/10.2172/759450) / OSTI ID: 759450 |
| **Direct Document Record** | [https://www.osti.gov/biblio/759450](https://www.osti.gov/biblio/759450) |
| **Archival Repository** | UNT Digital Library (metadc715560) |
| **Standardization** | Basis for ASME V&V 10 & ASME V&V 20 Standards |
| **Keywords** | Code Verification, Method of Manufactured Solutions (MMS), Order of Accuracy, Grid Refinement, Discretization Error |

---

## Abstract & Summary

Verification and Validation (V&V) distinguishes two fundamental concepts:
* **Validation:** Ensuring that the computational model accurately represents the physical reality (*"solving the right equations"*).
* **Code Verification:** Ensuring that the computer code accurately solves the mathematical equations without coding bugs or algorithmic implementation errors (*"solving the equations right"*).

This Sandia report establishes a rigorous procedure for code verification using the **Method of Manufactured Solutions (MMS)**. Because exact analytical solutions to physical boundary value problems exist only for simplified, degenerate geometries and constant coefficients, they often fail to exercise all terms in the governing equations. MMS overcomes this limitation by inventing an arbitrary, smooth mathematical function, substituting it into the differential operator to analytically derive a forcing/source term, and verifying that the numerical code recovers its theoretical asymptotic order of convergence under systematic grid refinement.

---

## Core Mathematical Procedure

1. **Governing Operator:** Consider partial differential equation $\mathcal{L}(u) = 0$.
2. **Manufacture a Solution:** Choose a smooth, non-trivial analytical field $\phi(\mathbf{x}, t)$ that exercises all derivative terms (e.g., trigonometric products $\phi(x, y) = \sin(2\pi x)\cos(2\pi y)$).
3. **Analytic Source Term Generation:** Substitute $\phi$ into $\mathcal{L}$:
   $$S(\mathbf{x}, t) = \mathcal{L}(\phi)$$
4. **Modified Problem Formulation:** The code is configured to solve:
   $$\mathcal{L}(u) = S$$
   with Dirichlet boundary conditions $u_{\partial \Omega} = \phi_{\partial \Omega}$.
5. **Systematic Mesh Refinement:** Solve the discrete system $\mathcal{L}_h(u_h) = S_h$ on a sequence of systematically refined grids with spacings $h_1 > h_2 > h_3$.
6. **Convergence Rate Verification:** Evaluate discrete error $E(h) = \|u_h - \Pi_h(\phi)\|_{L_2}$. Calculate observed order of accuracy:
   $$p = \frac{\ln(E(h_1) / E(h_2))}{\ln(h_1 / h_2)}$$
   The code is formally verified if the observed order $p$ asymptotically approaches the theoretical discretization order (e.g., $p \to 2$ for second-order central differences or discrete Hodge Laplacians).

---

## Direct Application to AlgebraX Verification Suite

In **AlgebraX** (`EP-0180` and `tests/verifications/test_mms_discrete_calculus.py`), MMS implements **Methodology 5**:

1. **Discrete Exterior Calculus (`EP-0160`):**
   - Manufacturing smooth scalar potentials $\phi$ on 2D simplicial surfaces.
   - Testing discrete exterior derivative $d_0$, Hodge star $\star_1$, and codifferential $\delta_1 = \star_0^{-1} d_0^T \star_1$.
   - Verifying that discrete Laplacian $\Delta_h \phi_h$ converges to continuous $\Delta \phi = \nabla^2 \phi$ at rate $O(h^2)$.
2. **Spectral Graph Theory & Graph Laplacians (`EP-0152`):**
   - Testing unnormalized and normalized graph Laplacians on regular lattice discretizations of continuous domains.
3. **Cellular Sheaf Consensus Dynamics (`EP-0161`):**
   - Verifying that multi-dimensional stalk Laplacians preserve harmonic extensions with bounded discretization residuals.
