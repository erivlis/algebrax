---
title: "EP-0163: Lie Algebras, Root Systems, and Baker–Campbell–Hausdorff Dynamics"
description: "Establishes Lie algebras, commutator brackets, structure constant tensors, the Killing form, and Baker–Campbell–Hausdorff (BCH) dynamics in AlgebraX."
icon: lucide/orbit
status: draft
---

# EP-0163: Lie Algebras, Root Systems, and Baker–Campbell–Hausdorff Dynamics

| Field        | Value                                                                              |
|:-------------|:-----------------------------------------------------------------------------------|
| **EP**       | 0163                                                                               |
| **Title**    | Lie Algebras, Root Systems, and Baker–Campbell–Hausdorff Dynamics                  |
| **Author**   | Eran Rivlis & Antigravity (The Explorer)                                           |
| **Sponsor**  | The Council                                                                        |
| **Delegate** | ⚖️ Emmy Noether (Symmetry), ⚡ Claude Shannon (Efficiency) & 🛡️ The Golem (Safety) |
| **Status**   | Draft                                                                              |
| **Type**     | Standards Track                                                                    |
| **Created**  | 2026-09-08                                                                         |
| **Updated**  | 2026-09-09                                                                         |
| **Replaces** | None                                                                               |

---

## Abstract

This proposal establishes first-class support for continuous symmetry generators and **Lie Algebras** ($\mathfrak{g}$)
in AlgebraX. It provides:

1. Base abstractions for Lie algebras (`LieAlgebra`) and matrix Lie algebras (`MatrixLieAlgebra`), equipped with an
   alternating bilinear bracket $[\cdot, \cdot]: \mathfrak{g} \times \mathfrak{g} \to \mathfrak{g}$ satisfying the
   Jacobi identity.
2. Structure constants representation via coordinate-sparse rank-3 tensors ($f_{ab}^c$), with automated Jacobi identity
   validation via tensor contraction over [`algebrax.tensor.einsum`](../../src/algebrax/tensor/einsum.py).
3. The adjoint representation $\mathrm{ad}_X (Y) = [X, Y]$ and the symmetric bilinear **Killing
   Form** $B (X, Y) = \mathrm{Tr} (\mathrm{ad}_X \circ \mathrm{ad}_Y)$, providing Cartan's criterion for semisimplicity.
4. Concrete classical Lie algebras:
    - $\mathfrak{so} (3)$: 3D rotation generators (isomorphic to Euclidean cross products).
    - $\mathfrak{sl} (2, \mathbb{R})$: Special linear algebra of traceless $2 \times 2$ matrices.
    - $\mathfrak{se} (3)$: Special Euclidean kinematics algebra for robotics and screw theory.
    - $\mathfrak{so} (3, 1)$: Lorentz algebra via bivector commutators in [
      `algebrax.clifford.CliffordAlgebra`](../../src/algebrax/clifford.py).
5. The **Baker–Campbell–Hausdorff (BCH) Formula**: Truncated series expansion for non-commutative group logarithms:
   $$Z = \log (\exp (X)\exp (Y)) = X + Y + \frac{1}{2}[X, Y] + \frac{1}{12}[X, [X, Y]] - \frac{1}{12}[Y, [X, Y]] + \dots$$
   enabling geometric numerical integration on Lie groups without leave-manifold drift.

---

## Motivation

Continuous symmetries play a central role across modern physics, robotics, quantum mechanics, and machine learning:

- **Missing Infinitesimal Generators**: While [`algebrax.clifford`](../../src/algebrax/clifford.py) computes finite
  rotations and Lorentz boosts via rotor sandwiches ($R x \tilde{R}$) and [
  `algebrax.matrix`](../../src/algebrax/matrix/core.py) multiplies linear transformations, AlgebraX currently lacks the
  **infinitesimal generators** spanning the tangent space at the group identity ($T_e G \cong \mathfrak{g}$).
- **The Non-Commutative Product Problem**: When multiplying group exponentials $\exp (X) \exp (Y)$, the exponent is not
  simply $X + Y$ due to non-commutativity. The Baker–Campbell–Hausdorff (BCH) formula allows compounding small Lie
  algebra steps purely within $\mathfrak{g}$, which is critical for:
    - **Lie Group Integrators**: Symplectic mechanics on manifolds, attitude control in aerospace, and rigid body
      dynamics ($SE (3)$).
    - **Quantum Spin Dynamics**: Composing non-commuting Hamiltonian evolutions in quantum optics and NMR.
- **Unifying Existing Subsystems**:
    - *Tensors*: Structure constants $f_{ab}^c$ are natural rank-3 tensors where Jacobi verification is an exact
      `einsum` contraction.
    - *Geometric Algebra*: Degree-2 bivectors in Clifford algebra $\mathcal{C}\ell (p, q)$ form closed Lie algebras
      under the commutator bracket $[B_1, B_2] = \frac{1}{2} (B_1 B_2 - B_2 B_1)$.
    - *Semirings*: The Universal Enveloping
      Algebra $\mathcal{U} (\mathfrak{g}) = T (\mathfrak{g}) / \langle xy - yx - [x, y]\rangle$ is isomorphic to [
      `QuotientMonoidAlgebraSemiring`](../../src/algebrax/semiring/algebraic.py).

By creating `algebrax.lie`, AlgebraX provides a unified, zero-dependency engine for continuous symmetry algebras.

---

## Rationale & The Council Alignment

The design is governed by the 8 Pillars of The Council Framework (`PRINCIPLES.md`):

### 1. Symmetry (Noether)

- **Noether's Theorem Realized**: Lie algebras are the mathematical substrate of continuous symmetries. Every
  1-parameter Lie subgroup generates an infinitesimal symmetry of a Hamiltonian system, corresponding to a conserved
  Noether charge.
- **Antisymmetry & Jacobi Identity**:
  $$[X, Y] = -[Y, X], \quad [X, [Y, Z]] + [Y, [Z, X]] + [Z, [X, Y]] = 0$$
- **Invariance of the Killing Form**: The Killing metric satisfies the associative invariance property:
  $$B ([X, Y], Z) = B (X, [Y, Z])$$
  demonstrating profound geometric and algebraic balance.

### 2. Efficiency (Shannon)

- **Sparse Structure Constants**: In almost all classical Lie algebras, the structure constants tensor $f_{ab}^c$ is
  extremely sparse (e.g. for $\mathfrak{so} (3)$, only 6 out of 27 entries are
  non-zero: $f_{12}^3 = 1$, $f_{23}^1 = 1$, $f_{31}^2 = 1$, and their alternating permutations).
- **Coordinate-Sparse Bracket & Einsum Interoperability**: Structure constants are stored as coordinate 3-tuples
  `dict[tuple[int, int, int], float]` (or `AlgebraicTrie`), enabling seamless contraction via [
  `algebrax.tensor.einsum`](../../src/algebrax/tensor.py). Evaluating $[X, Y]^c = \sum_{a,b} f_{ab}^c X^a Y^b$ skips all
  zero entries, executing in $O (s)$ where $s$ is the number of non-zero structure constants.

### 3. Safety (The Golem)

- **BCH Radius of Convergence**: The BCH series $\log (\exp (X)\exp (Y))$ converges absolutely only within the
  disk $\|X\|_2 + \|Y\|_2 < \ln 2 \approx 0.69315$. The BCH solver evaluates input vector 2-norms and issues an explicit
  `ConvergenceWarning` if inputs exceed this radius.
- **Immutability & Bounds**: Lie algebra basis elements and structure tensors are immutable instances. BCH orders are
  validated against the supported range ($1 \le \text{order} \le 4$) to prevent unverified higher-order truncation
  errors.
- **Semisimplicity Check**: Singular or degenerate Killing forms ($\det B = 0$) are safely detected before calculating
  Casimir invariants.

### 4. Clarity (Feynman)

- **The Freshman Test**: Lie brackets represent the "failure of infinitesimal displacements to form a closed rectangle":
    - Walking 1 meter North then 1 meter East on a sphere does not land on the same spot as 1 meter East then 1 meter
      North.
    - The bracket $[X, Y]$ measures the net gap.
    - The BCH formula tells you exactly what direction to steer to compensate for that gap.

### 5. Falsifiability (Popper)

- The implementation will be verified against standard algebraic identities:
    1. **Cross-Product Isomorphism**: For $\mathfrak{so} (3)$, $[X, Y] = X \times Y$ for all basis vectors.
    2. **Pauli Matrix Commutators**:
       For $\mathfrak{su} (2)$, $[\sigma_j, \sigma_k] = 2i \sum_l \epsilon_{jkl} \sigma_l$.
    3. **Killing Signature**: Verify that $\mathfrak{so} (3)$ has a negative-definite Killing
       form $B (X, Y) = -2 \langle X, Y \rangle$.
    4. **Adjoint Invariance**: $B (\mathrm{ad}_X (Y), Z) + B (Y, \mathrm{ad}_X (Z)) = 0$.

### 6. Consistency (Russell)

- **Mode vs. Type Heuristic**: Rather than maintaining a separate class hierarchy (`MatrixLieAlgebra` vs `LieAlgebra`),
  AlgebraX adheres to the Mode vs Type heuristic (`PRINCIPLES.md`): `LieAlgebra` is the unified carrier class, and
  matrix generators are supported via the specialized factory method `LieAlgebra.from_matrix_basis(...)`.
- **Tensor Architecture Symmetry**: Structure constants are native rank-3 tensors conforming directly to the
  tuple-indexed representation required by `algebrax.tensor.einsum`, eliminating conversion overhead.
- Clear delineation between:
    - **Lie Group** ($G$): The global non-linear manifold (e.g., $SO (3)$ rotation matrices or rotors).
    - **Lie Algebra** ($\mathfrak{g}$): The linear vector space of tangent generators at identity with $[\cdot, \cdot]$.
    - **Exponential Map** ($\exp: \mathfrak{g} \to G$): The canonical bridge between them.

---

## Specification

### 1. Data Models & Type Contracts

```python
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias
from algebrax.typing import SparseMatrix, SparseVector

LieElement: TypeAlias = SparseVector[int, float]


@dataclass(frozen=True)
class StructureConstants:
    """Sparse rank-3 tensor representing f_{ab}^c for a Lie algebra.
    
    Stored as coordinate 3-tuples (a, b, c) -> value, representing [T_a, T_b] = sum_c f_{ab}^c T_c.
    """
    dim: int
    tensor: dict[tuple[int, int, int], float]

    def verify_jacobi(self, tol: float = 1e-12) -> bool:
        r"""Verify the Jacobi identity via einsum contraction over all basis triples:
        sum_k (f_{ab}^k f_{kc}^d + f_{bc}^k f_{ka}^d + f_{ca}^k f_{kb}^d) == 0
        """
        ...
```

### 2. Base Class & Factory in `algebrax.lie`

```python
class LieAlgebra:
    """Finite-dimensional Lie algebra defined by structure constants or matrix generators."""
    dim: int
    basis_names: list[str]
    structure_constants: StructureConstants
    matrix_basis: list[SparseMatrix[int, float]] | None

    def __init__(
            self,
            dim: int,
            structure_constants: StructureConstants,
            basis_names: Sequence[str] | None = None,
            matrix_basis: Sequence[SparseMatrix[int, float]] | None = None,
    ):
        ...

    @classmethod
    def from_matrix_basis(
            cls,
            basis_matrices: Sequence[SparseMatrix[int, float]],
            names: Sequence[str] | None = None,
    ) -> "LieAlgebra":
        """Construct a LieAlgebra by projecting matrix commutators [A, B] = AB - BA onto the basis."""
        ...

    def bracket(self, x: LieElement, y: LieElement) -> LieElement:
        """Compute the Lie bracket [X, Y]^c = sum_{a,b} f_{ab}^c X^a Y^b."""
        ...

    def adjoint_matrix(self, x: LieElement) -> SparseMatrix[int, float]:
        """Return the adjoint representation matrix ad_X where (ad_X)_b^c = sum_a f_{ab}^c X^a."""
        ...

    def killing_matrix(self) -> SparseMatrix[int, float]:
        """Return the Killing form matrix K_{ab} = Tr(ad_{T_a} @ ad_{T_b})."""
        ...

    def killing_form(self, x: LieElement, y: LieElement) -> float:
        """Compute the Killing form B(X, Y) = Tr(ad_X @ ad_Y)."""
        ...

    def is_semisimple(self) -> bool:
        """Check Cartan's criterion: det(Killing Matrix) != 0."""
        ...

    def bch(self, x: LieElement, y: LieElement, order: int = 4) -> LieElement:
        r"""Compute the Baker-Campbell-Hausdorff series up to specified order (1 <= order <= 4).
        
        Order 1: X + Y
        Order 2: + 1/2 [X, Y]
        Order 3: + 1/12 [X, [X, Y]] - 1/12 [Y, [X, Y]]
        Order 4: - 1/24 [Y, [X, [X, Y]]]
        
        Issues ConvergenceWarning if ||X||_2 + ||Y||_2 >= ln(2).
        """
        ...
```

### 3. Factory Constructors for Canonical Algebras

- `so3()`: The rotation algebra $\mathfrak{so} (3)$, dimension 3, basis $\{J_x, J_y, J_z\}$.
- `sl2()`: The special linear algebra $\mathfrak{sl} (2, \mathbb{R})$, dimension 3, basis $\{e, f, h\}$.
- `se3()`: The rigid kinematics algebra $\mathfrak{se} (3)$, dimension 6, basis 3 rotations + 3 translations.
- `clifford_lie_algebra(clifford_instance)`: Constructs the Lie algebra formed by the bivector subspace under commutator
  multiplication.

---

## Backwards Compatibility

This proposal is purely additive:

- Introduces new subpackage `algebrax.lie`.
- Cross-exports `commutator` in `algebrax.matrix` (which computes $[A, B] = AB - BA$).
- No existing APIs or serialization contracts are impacted.

---

## How to Teach This / Documentation Plan

1. **User Guide**: Add `docs/guide/discrete/lie_algebras.md` detailing:
    - What are Lie algebras and infinitesimal generators?
    - Structure constants and the Jacobi identity.
    - The Killing form and classification of semisimplicity.
    - The Baker-Campbell-Hausdorff series and Lie group time-steppers.
2. **Interactive Recipe**: Add a robotics recipe in `docs/recipes.md`:
    - *Rigid Body Attitude Tracking with BCH*: Integrating angular velocity
      vectors $\boldsymbol{\omega} (t) \in \mathfrak{so} (3)$ using 4th-order BCH integration without drift
      off $SO (3)$.

---

## Reference Implementation

```python
import math
import warnings
from algebrax.matrix import commutator, dot, trace, add, subtract
from algebrax.tensor import einsum
from algebrax.typing import SparseMatrix, SparseVector


class ConvergenceWarning(UserWarning):
    """Warning raised when BCH series inputs exceed the radius of convergence."""
    pass


class LieAlgebra:
    """Unified finite-dimensional Lie algebra."""

    def __init__(self, dim, structure_constants, basis_names=None, matrix_basis=None):
        self.dim = dim
        self.structure_constants = structure_constants
        self.basis_names = list(basis_names) if basis_names else [f"T_{i}" for i in range(dim)]
        self.matrix_basis = list(matrix_basis) if matrix_basis else None

    @classmethod
    def from_matrix_basis(cls, basis_matrices, names=None):
        dim = len(basis_matrices)
        f_tensor = {}
        # Project [T_a, T_b] onto basis via trace inner product Tr(T_c^T @ [T_a, T_b])
        # Assuming orthonormal basis under trace: Tr(T_i^T @ T_j) = delta_ij
        for a in range(dim):
            for b in range(dim):
                comm = commutator(basis_matrices[a], basis_matrices[b])
                for c in range(dim):
                    val = trace(dot(basis_matrices[c], comm))
                    if abs(val) > 1e-12:
                        f_tensor[(a, b, c)] = val

        sc = StructureConstants(dim=dim, tensor=f_tensor)
        return cls(dim=dim, structure_constants=sc, basis_names=names, matrix_basis=basis_matrices)

    def bracket(self, x: SparseVector, y: SparseVector) -> dict:
        """Compute [X, Y]^c = sum_{a,b} f_{ab}^c X^a Y^b."""
        res = {}
        for (a, b, c), fabc in self.structure_constants.tensor.items():
            xa = x.get(a, 0.0)
            yb = y.get(b, 0.0)
            if xa and yb:
                res[c] = res.get(c, 0.0) + fabc * xa * yb
        return {c: v for c, v in res.items() if abs(v) > 1e-12}

    def bch(self, x: SparseVector, y: SparseVector, order: int = 4) -> dict:
        norm_x = math.sqrt(sum(v * v for v in x.values()))
        norm_y = math.sqrt(sum(v * v for v in y.values()))
        if norm_x + norm_y >= math.log(2.0):
            warnings.warn(
                f"BCH input norms ({norm_x + norm_y:.4f}) exceed convergence radius ln(2) ~= 0.69315",
                ConvergenceWarning,
                stacklevel=2,
            )

        # Order 1: X + Y
        res = {k: x.get(k, 0.0) + y.get(k, 0.0) for k in set(x.keys()) | set(y.keys())}
        if order < 2:
            return res

        # Order 2: + 1/2 [X, Y]
        xy = self.bracket(x, y)
        for k, v in xy.items():
            res[k] = res.get(k, 0.0) + 0.5 * v
        if order < 3:
            return res

        # Order 3: + 1/12 [X, [X, Y]] - 1/12 [Y, [X, Y]]
        x_xy = self.bracket(x, xy)
        y_xy = self.bracket(y, xy)
        for k, v in x_xy.items():
            res[k] = res.get(k, 0.0) + (1.0 / 12.0) * v
        for k, v in y_xy.items():
            res[k] = res.get(k, 0.0) - (1.0 / 12.0) * v
        if order < 4:
            return res

        # Order 4: - 1/24 [Y, [X, [X, Y]]]
        y_x_xy = self.bracket(y, x_xy)
        for k, v in y_x_xy.items():
            res[k] = res.get(k, 0.0) - (1.0 / 24.0) * v

        return {k: v for k, v in res.items() if abs(v) > 1e-12}
```

---

## Rejected Ideas

1. **Infinite-Dimensional Virasoro / Kac-Moody Algebras**:
    - *Considered*: Supporting formal polynomial-graded infinite-dimensional Lie algebras.
    - *Rejected*: Violates minimal representation and practical utility. AlgebraX focuses on finite-dimensional Lie
      algebras and computational symmetry groups.
2. **Automated Symbolic Root System Dynkin Diagram Renderer**:
    - *Considered*: Building a full ASCII/SVG Dynkin diagram classifier ($A_n, B_n, C_n, D_n, E_{6,7,8}, F_4, G_2$).
    - *Rejected*: Deferred to a future informational exploration. Cartan classification and root spaces will start with
      matrix root vectors rather than full graphical Dynkin parsing.

---

## Open Questions

- [ ] Should the BCH expansion beyond order 4 be supported via Dynkin's explicit summation formula over free Lie trees,
  or is order 4 sufficient for 99% of numerical integration use cases?
- [ ] Should `algebrax.clifford` provide a direct conversion method `.as_lie_algebra()` for its bivector graded
  component?

---

## Change Log

* **2026-09-09:**
    * Council Review amendments incorporating The Dennis Point:
        - Unified `LieAlgebra` and `MatrixLieAlgebra` into a single class with `from_matrix_basis` factory method,
          adhering to the *Mode vs Type* heuristic.
        - Updated `StructureConstants` to use coordinate 3-tuples `(a, b, c) -> float`, enabling direct tensor
          contractions with `algebrax.tensor.einsum`.
        - Added `ConvergenceWarning` check for BCH series based on 2-norm threshold $\|X\|_2 + \|Y\|_2 < \ln 2$.
* **2026-09-08:**
    * Initial Draft authored by Eran Rivlis and Antigravity (The Explorer).
