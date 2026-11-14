---
title: "EP-0221: Affine Algebraic Varieties, Coordinate Rings & Stickelberger Solvers"
description: "Introduce algebrax.variety for affine algebraic varieties V(I), coordinate rings k[V], polynomial morphisms, Stickelberger companion matrix solvers, and finite-field varieties."
icon: lucide/orbit
status: draft
---

# EP-0221: Affine Algebraic Varieties, Coordinate Rings & Stickelberger Solvers

| Field             | Value                                                                                      |
|:------------------|:-------------------------------------------------------------------------------------------|
| **EP**            | 0221                                                                                       |
| **Title**         | Affine Algebraic Varieties, Coordinate Rings & Stickelberger Solvers                       |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                |
| **Sponsor**       | Core Maintainers                                                                           |
| **Delegate**      | ⚖️ Noether (Ideal–Variety Duality), 🧩 Russell (Functorial Pullbacks) & ⚡ Shannon (Matrices) |
| **Status**        | Draft                                                                                      |
| **Type**          | Standards Track                                                                            |
| **Created**       | 2026-11-14                                                                                 |
| **Updated**       | 2026-11-14                                                                                 |
| **Replaces**      | —                                                                                          |
| **Superseded-By** | —                                                                                          |

---

## Abstract

This proposal introduces the **`algebrax.variety`** module, establishing the geometric dual to [`EP-0220`](EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md) (`GroebnerIdeal`) and [`EP-0201`](EP-0201-algebraic-homomorphisms-ideals-quotients.md) (`QuotientRing`, `RingHom`). Specifically, EP-0221 provides:

1. **Affine Algebraic Varieties (`AffineVariety[V]`)**:
   Represents the zero locus $V(I) = \{p \in k^n \mid f(p) = 0 \;\forall f \in I\}$ paired with its canonical coordinate ring $k[V] = k[x_1, \dots, x_n] / I$ realized as a zero-overhead `QuotientRing`.
2. **The Ideal–Variety Dictionary & Hilbert's Nullstellensatz Operations**:
   Algebraic-geometric operations pairing ideal operations with geometric set operations:
   - Variety intersection $V(I) \cap V(J) = V(I + J)$ (ideal sum).
   - Variety union $V(I) \cup V(J) = V(I \cap J)$ and $V(I \cdot J)$ (ideal product/intersection).
   - Variable elimination $I_k = I \cap k[x_{k+1}, \dots, x_n]$ (projection of varieties via `lex` Gröbner bases).
   - Weak Nullstellensatz consistency check ($V_{\bar{k}}(I) = \emptyset \iff 1 \in I$).
3. **Stickelberger Companion Matrix Solvers (`companion_matrix`, `solve_zero_dimensional`)**:
   For 0-dimensional varieties ($\dim_{k}(k[V]) < \infty$), constructs the exact sparse multiplication operators $M_{x_i}: k[V] \to k[V]$ on the standard monomial basis $\mathcal{B} = \{x^\alpha \notin \langle \mathrm{LT}(I) \rangle\}$, turning nonlinear polynomial root-finding into commuting linear eigenvalue problems.
4. **Finite-Field Varieties & Algebraic SAT (`enum_points`, `solve_f2_sat`)**:
   Exact point enumeration over $\mathbb{F}_p^n$ (`ModularField(p)`) for elliptic curves and algebraic codes, plus Boolean ideal reduction in $\mathbb{F}_2[x_1, \dots, x_n]/\langle x_i^2 - x_i \rangle$.
5. **Contravariant Polynomial Morphisms (`PolynomialMap`)**:
   Realizes the functorial duality between a polynomial map $\phi: V \to W$ and its coordinate-ring pullback `RingHom` $\phi^*: k[W] \to k[V]$.

---

## Motivation

Computational algebraic geometry is often perceived as purely symbolic manipulation, yet its most powerful applications reduce nonlinear geometry to **sparse linear algebra**:

1. **Completing the `EP-0201` Duality**: [`EP-0201`](EP-0201-algebraic-homomorphisms-ideals-quotients.md) formalized `Ideal`, `QuotientRing`, and `RingHom`. In algebraic geometry, these three concepts have exact geometric counterparts:
   $$\text{Ideal } I \longleftrightarrow \text{Variety } V(I), \qquad \text{Quotient } k[X]/I \longleftrightarrow \text{Coordinate Ring } k[V], \qquad \text{RingHom } \phi^* \longleftrightarrow \text{Morphism } \phi: V \to W$$
2. **Nonlinear Kinematics & Physics without Initial-Guess Fragility**: Newton–Raphson solvers on nonlinear systems (such as robotic inverse kinematics or chemical equilibria) only find a single local root and diverge near singularities. Stickelberger's Eigenvalue Theorem constructs exact sparse companion matrices $M_{x_i}$ whose eigenvalues give *all* isolated roots simultaneously.
3. **Syzygies in Invariant Theory ([`EP-0214`](EP-0214-invariant-theory-molien-series-casimir-polynomials.md))**: Given invariant polynomials $f_1, \dots, f_m \in k[V]^G$, finding the algebraic relations (syzygies) among them is an elimination ideal problem in $k[x_1, \dots, x_n, y_1, \dots, y_m]$ modulo $\langle y_j - f_j(x) \rangle$.
4. **Finite-Field Cryptography & Verification ([`EP-0112`](EP-0112-galois-finite-fields.md), [`EP-0186`](EP-0186-certificates-pit-and-smt-formal-verification.md))**: Counting rational points on curves over $\mathbb{F}_p$ (elliptic curve cryptography) and solving Boolean polynomial systems over $\mathbb{F}_2$ unify `algebrax.galois` and `algebrax.verification` under affine varieties.

---

## Rationale

Validated in [**EXP-0009**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0009-algebraic-and-tropical-varieties/README.md) (Experiment 3 & Experiment 4) and aligned with the Grand Council:

- **⚖️ Emmy Noether (Contravariant Algebra–Geometry Duality)**:
  Honors Noether's structural revolution in algebraic geometry: geometry on an affine space $V$ is completely encoded by commutative algebra on its coordinate ring $k[V]$, and geometric morphisms $\phi: V \to W$ correspond contravariantly to ring homomorphisms $\phi^*: k[W] \to k[V]$ ($f \mapsto f \circ \phi$).
- **⚡ Claude Shannon (Stickelberger Linearization & The Escape Hatch)**:
  Instead of implementing brittle univariate resultant cascades, `AffineVariety.companion_matrix(i)` produces a standard AlgebraX `SparseMatrix[int, V]` ($M_{x_i}$). Users can inspect exact rational traces, determinants, and commutators ($[M_{x_i}, M_{x_j}] = \mathbf{0}$) in pure Python, or use the optional NumPy eigensolver Escape Hatch to extract floating-point root coordinates with machine precision (`0.00e+00` residual on 4-point conic intersection and exact 2R Robot poses in `EXP-0009`).
- **🧩 Bertrand Russell (Finiteness Criterion & Dimension Classification)**:
  Cleanly distinguishes 0-dimensional varieties (where every variable $x_i$ has a pure power $x_i^{d_i} \in \langle \mathrm{LT}(I) \rangle$, yielding a finite basis $\mathcal{B}$ of size $\dim_k k[V]$) from positive-dimensional varieties (detected via Krull dimension / Hilbert polynomial of $\langle \mathrm{LT}(I) \rangle$).
- **🔬 Karl Popper (Commutativity & Residual Falsification)**:
  Every companion matrix family $\{M_{x_1}, \dots, M_{x_n}\}$ must satisfy the falsifiable invariant `commutator(M_i, M_j) == {}` over exact `Field[V]`, and every extracted root $p \in V(I)$ is verified by evaluating $f(p) = 0$ for all generators.
- **💡 Richard Feynman (The Freshman Test)**:
  *"How do you solve a system of nonlinear polynomial equations using only linear algebra? You divide out by the equations to get a finite list of leftover monomials like $\{1, x, y, y^2\}$. Multiplying that list by $x$ is just a matrix $M_x$—and the eigenvalues of $M_x$ are the exact $x$-coordinates of the solutions!"*

---

## Specification

### 1. Atomic Geometric Capability Mixins & Flat Protocols (`src/algebrax/variety/_mixins.py`)

Following [`EP-0005`](EP-0005-universal-algebraic-protocol-architecture.md) (Law of Flat Protocol Composition), `algebrax.variety._mixins` defines four single-principle Layer 1 geometric capabilities and two flat Layer 2 protocols unifying classical (`EP-0221`) and tropical (`EP-0222`) varieties:

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra import GroebnerIdeal, QuotientRing, SparseMPoly
from algebrax.typing import SparseMatrix

P = TypeVar("P")
V = TypeVar("V")


@runtime_checkable
class HasPointLocus(Protocol[P]):
    r"""Ambient point-membership capability $p \in X \subseteq A^n$.

    Algebraic Signature:
        $\langle A^n, X, \operatorname{ambient\_dimension}, \operatorname{contains\_point} \rangle$
    """

    @property
    def ambient_dimension(self) -> int: ...

    def contains_point(self, point: Sequence[P]) -> bool: ...


@runtime_checkable
class HasDimension(Protocol):
    r"""Intrinsic geometric dimension capability $\dim X$ (Krull or polyhedral dimension).

    Algebraic Signature:
        $\langle X, \operatorname{dimension} \rangle$
    """

    def dimension(self) -> int: ...


@runtime_checkable
class HasCoordinateRing(Protocol[V]):
    r"""Noetherian algebra–geometry duality capability pairing $V(I)$ with $I$ and $k[V] = k[X]/I$.

    Algebraic Signature:
        $\langle V(I), I, k[V] \rangle$
    """

    @property
    def ideal(self) -> GroebnerIdeal[V]: ...

    @property
    def coordinate_ring(self) -> QuotientRing[SparseMPoly[V]]: ...


@runtime_checkable
class HasTangentLocus(Protocol[V]):
    r"""Differential-geometric capability providing the Jacobian $J(p)$ and smoothness predicate.

    Algebraic Signature:
        $\langle X, J(p), \operatorname{is\_smooth\_at} \rangle$
    """

    def jacobian_at(self, point: Sequence[V]) -> SparseMatrix[int, V]: ...

    def is_smooth_at(self, point: Sequence[V]) -> bool: ...


# Layer 2 Flat Geometric Protocols (Zero Layer-2-to-Layer-2 Inheritance)
@runtime_checkable
class GeometricVariety(HasPointLocus[P], HasDimension, Protocol[P]):
    r"""Flat protocol satisfied by both classical `AffineVariety[V]` and `TropicalHypersurface`."""

    ...


@runtime_checkable
class SmoothableVariety(
    HasPointLocus[V],
    HasDimension,
    HasCoordinateRing[V],
    HasTangentLocus[V],
    Protocol[V],
):
    r"""Flat protocol for algebraic varieties equipped with coordinate rings and Jacobian tangent spaces."""

    ...
```

### 2. `AffineVariety` & Coordinate Rings (`src/algebrax/variety/affine.py`)

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from algebrax.algebra import (
    GroebnerIdeal,
    MultivariatePolynomialAlgebra,
    QuotientRing,
    RingHom,
    SparseMPoly,
)
from algebrax.typing import SparseMatrix
from algebrax.variety._mixins import SmoothableVariety

V = TypeVar("V")
Monomial = tuple[int, ...]


class AffineVariety(SmoothableVariety[V], Generic[V]):
    r"""An affine algebraic variety $V(I) = \{p \in k^n \mid f(p) = 0 \;\forall f \in I\}$.

    Algebraic Dual:
        Coordinate ring $k[V] = k[x_1, \dots, x_n] / I$ realized via `QuotientRing`.
    """

    def __init__(
        self,
        ring: MultivariatePolynomialAlgebra[V],
        generators: Sequence[SparseMPoly[V]],
    ) -> None:
        self.ring = ring
        self._ideal = GroebnerIdeal(ring, generators)
        self._coordinate_ring = QuotientRing(ring, self._ideal)

    @property
    def ambient_dimension(self) -> int:
        """Ambient affine space dimension n of k^n."""
        return self.ring.n_vars

    @property
    def ideal(self) -> GroebnerIdeal[V]:
        """Defining Gröbner ideal I(V)."""
        return self._ideal

    @property
    def coordinate_ring(self) -> QuotientRing[SparseMPoly[V]]:
        """Coordinate ring k[V] = k[x_1, ..., x_n] / I."""
        return self._coordinate_ring

    def contains_point(self, point: Sequence[V]) -> bool:
        """Return True iff point p in k^n satisfies f(p) == 0 for all generators."""
        return all(self.ring.field.is_zero(self.ring.eval(g, point)) for g in self.ideal.basis)

    def is_empty_over_closure(self) -> bool:
        """Weak Nullstellensatz check: True iff 1 in I (G == [{0: 1}])."""
        return self.ideal.is_unit()

    def is_zero_dimensional(self) -> bool:
        """Return True iff k[V] is a finite-dimensional k-vector space."""
        ...

    def krull_dimension(self) -> int:
        r"""Compute the affine Krull dimension $\dim V(I)$ from the initial ideal $\langle \mathrm{LT}(I) \rangle$.

        Equals the maximum cardinality of an independent subset of variables $S \subseteq \{x_1, \dots, x_n\}$
        such that $\langle \mathrm{LT}(I) \rangle \cap k[S] = \{0\}$ (returns -1 if $V(I) = \emptyset$).
        """
        ...

    def dimension(self) -> int:
        """Return intrinsic Krull dimension (`HasDimension` protocol)."""
        return self.krull_dimension()

    def hilbert_function(self, degree: int) -> int:
        r"""Compute the affine Hilbert function $\operatorname{HF}_{k[V]}(d) = \dim_k k[V]_{\le d}$.

        Counts standard monomials $x^\alpha \notin \langle \mathrm{LT}(I) \rangle$ of total degree $|\alpha| \le d$,
        providing the polynomial-ring dual to the Molien series in `EP-0214`.
        """
        ...

    def quotient_basis(self) -> list[Monomial] | None:
        """Return standard monomial basis B = {x^a not in <LT(I)>} if 0-dimensional."""
        ...

    def jacobian_poly_matrix(self) -> list[list[SparseMPoly[V]]]:
        r"""Return the formal $m \times n$ algebraic Jacobian matrix $J_{ij} = \frac{\partial g_i}{\partial x_j}$."""
        ...

    def jacobian_at(self, point: Sequence[V]) -> SparseMatrix[int, V]:
        r"""Evaluate the Jacobian matrix $J(p)$ at `point` $p \in k^n$ (tangent space $T_p V = \ker J(p)$)."""
        ...

    def is_smooth_at(self, point: Sequence[V]) -> bool:
        r"""Jacobian criterion: True iff $p \in V(I)$ and $\operatorname{rank}(J(p)) == n - \dim V(I)$."""
        ...

    def radical_zero_dim(self) -> AffineVariety[V]:
        r"""Compute the 0-dimensional radical variety $V(\sqrt{I})$ via Seidenberg's Lemma.

        Adjoins the square-free parts $f_i / \gcd(f_i, f_i')$ of univariate elimination generators
        $f_i \in I \cap k[x_i]$, guaranteeing semisimple (diagonalizable) Stickelberger companion matrices.
        """
        ...

    def intersect(self, other: AffineVariety[V]) -> AffineVariety[V]:
        """Geometric intersection V(I) cap V(J) = V(I + J)."""
        return AffineVariety(self.ring, [*self.ideal.basis, *other.ideal.basis])

    def eliminate(self, num_vars_to_eliminate: int) -> AffineVariety[V]:
        """Compute k-th elimination variety V(I cap k[x_{k+1}, ..., x_n]) using lex order."""
        ...
```

### 3. Stickelberger Companion Matrix Solver (`src/algebrax/variety/stickelberger.py`)

```python
def companion_matrix(
    variety: AffineVariety[V],
    var_index: int,
) -> SparseMatrix[int, V]:
    r"""Construct the exact sparse multiplication matrix $M_{x_i}: k[V] \to k[V]$ in basis $\mathcal{B}$.

    Raises:
        ValueError: If `variety` is not zero-dimensional.
    """
    ...


def solve_zero_dimensional(
    variety: AffineVariety[V],
    *,
    use_radical: bool = True,
) -> list[tuple[float | complex, ...]]:
    r"""Extract isolated root coordinates of a 0-dimensional variety via Stickelberger's Theorem.

    When `use_radical=True`, first reduces to $\sqrt{I}$ via Seidenberg's Lemma so repeated roots
    do not produce defective Jordan blocks, then extracts simultaneous Rayleigh quotients of
    $M_{x_1}, \dots, M_{x_n}$.
    """
    ...
```

### 4. Finite-Field Varieties & Algebraic SAT (`src/algebrax/variety/finite.py`)

```python
def enum_variety_points(
    variety: AffineVariety[int],
) -> list[tuple[int, ...]]:
    r"""Enumerate all rational points $V(I)(\mathbb{F}_p) \subseteq \mathbb{F}_p^n$ over `ModularField(p)`."""
    ...


def boolean_variety(
    n_vars: int,
    clauses_or_polys: Sequence[SparseMPoly[int]],
) -> AffineVariety[int]:
    r"""Construct a Boolean variety in $\mathbb{F}_2[x_1, \dots, x_n] / \langle x_1^2 + x_1, \dots, x_n^2 + x_n \rangle$."""
    ...
```

### 5. Contravariant Polynomial Morphisms & Representation Theory Bridges (`src/algebrax/variety/morphism.py`)

```python
class PolynomialMap(RingHom[SparseMPoly[V], SparseMPoly[V]], Generic[V]):
    r"""A polynomial morphism $\phi: V \to W$ together with its contravariant pullback $\phi^*: k[W] \to k[V]$.

    Calling `phi.eval_point(p)` maps a point $p \in V \subseteq k^n$ to $\phi(p) \in W \subseteq k^m$.
    Calling `phi(g)` (as a `RingHom`) pulls back $g \in k[W]$ to $\mathrm{reduce}_{I(V)}(g(\phi_1, \dots, \phi_m)) \in k[V]$.
    """
    ...


def syzygy_variety(
    ring: MultivariatePolynomialAlgebra[V],
    invariant_polys: Sequence[SparseMPoly[V]],
) -> AffineVariety[V]:
    r"""Compute the GIT quotient / syzygy variety $V // G \subseteq k^m$ of invariant polynomials (`EP-0214` bridge).

    Constructs the tag-variable ideal $\langle y_1 - \pi_1(x), \dots, y_m - \pi_m(x) \rangle \triangleleft k[x_1, \dots, x_n, y_1, \dots, y_m]$
    and eliminates $x_1, \dots, x_n$ via a `lex` Gröbner basis to return the algebraic variety of
    polynomial relations $I_{\text{syz}} \triangleleft k[y_1, \dots, y_m]$ satisfied by the invariants.
    """
    ...


def plucker_grassmannian_variety(
    field: Field[V],
    k_subspace: int,
    n_ambient: int,
) -> AffineVariety[V]:
    r"""Construct the Grassmannian variety $\operatorname{Gr}(k, n)$ cut out by quadratic Plücker relations (`EP-0211` bridge).

    Provides the canonical flag/Grassmannian testbed for Borel–Weil representation theory (`EP-0211`)
    and exterior algebra $k$-blades (`EP-0160`).
    """
    ...


class CoordinateHopfAlgebra(Generic[V]):
    r"""Coordinate Hopf Algebra $k[G] = k[x_{11}, \dots, x_{nn}] / I(G)$ of an affine algebraic matrix group (`EP-0206` bridge).

    Equips the coordinate ring `variety.coordinate_ring` of a matrix group variety $G \subseteq \operatorname{GL}_n(k)$
    (e.g., $\operatorname{SL}_n(k)$ cut out by $\det(X) - 1 = 0$, or $\operatorname{SO}_n(k)$ cut out by $X^\top X = I_n$)
    with the commutative `HopfAlgebra` operations from `EP-0206`:
    - Comultiplication $\Delta(x_{ij}) = \sum_{k=1}^n x_{ik} \otimes x_{kj}$ (dual to matrix multiplication $G \times G \to G$).
    - Counit $\epsilon(x_{ij}) = \delta_{ij}$ (dual to identity matrix $I_n \in G$).
    - Antipode $S(X) = X^{-1} \pmod{I(G)}$ via cofactor / adjugate inversion (dual to group inversion $g \mapsto g^{-1}$).
    """

    def __init__(self, n_dim: int, group_variety: AffineVariety[V]) -> None: ...
    def counit(self, f: SparseMPoly[V]) -> V: ...
    def antipode(self, f: SparseMPoly[V]) -> SparseMPoly[V]: ...
    def comultiply_generator(self, row: int, col: int) -> list[tuple[SparseMPoly[V], SparseMPoly[V]]]: ...
```

### 6. Algebraic K-Theory, Serre–Swan Bundles & Schubert Cohomology Rings (`src/algebrax/variety/k_theory.py`)

Bridges `algebrax.variety` directly with `algebrax.topology.k_theory` ([`EP-0207`](EP-0207-topological-k-theory-and-characteristic-classes.md)) and `GrothendieckRing` (`algebrax.algebra._grothendieck`):

```python
def is_serre_swan_projective_bundle(
    variety: AffineVariety[V],
    projector_matrix: SparseMatrix[int, SparseMPoly[V]],
) -> bool:
    r"""Verify the Serre–Swan theorem condition $P^2 \equiv P \pmod{I(V)}$ for an algebraic vector bundle.

    An idempotent matrix $P \in M_r(k[V])$ over `variety.coordinate_ring` defines a finitely generated
    projective module over $k[V]$ (and hence an algebraic vector bundle $E \to V$ in $K_0(V)$).
    """
    ...


def schubert_chern_cohomology_ring(
    field: Field[V],
    k_subspace: int,
    n_ambient: int,
) -> QuotientRing[SparseMPoly[V]]:
    r"""Construct Borel's Chern/Schubert cohomology quotient ring $H^*(\operatorname{Gr}(k, n); k)$ (`EP-0207` bridge).

    Generated by tautological Chern classes $c_1, \dots, c_k$ and quotient Chern classes
    $\tilde{c}_1, \dots, \tilde{c}_{n-k}$ modulo the Whitney sum relation
    $(1 + c_1 + \cdots + c_k)(1 + \tilde{c}_1 + \cdots + \tilde{c}_{n-k}) = 1$.
    """
    ...


def motivic_point_count_homomorphism(
    variety_pair: tuple[AffineVariety[int], AffineVariety[int]],
) -> int:
    r"""Evaluate the $\mathbb{F}_p$-point counting homomorphism $\#V(\mathbb{F}_p) - \#W(\mathbb{F}_p)$ on $K_0(\mathbf{Var}_{\mathbb{F}_p})$.

    Satisfies cut-and-paste scissor congruence $[V] = [Z] + [V \setminus Z]$ in `GrothendieckRing`.
    """
    ...
```

---

## Backwards Compatibility

Strictly additive. Introduces `src/algebrax/variety/` and exports `variety` in `algebrax.__init__`. Existing `algebrax.algebra` and `algebrax.matrix` APIs remain unchanged.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add `docs/guide/algebra/varieties_and_geometry.md` illustrating:
  1. Conic intersections, coordinate rings, and affine matrix group Hopf algebras ($k[\operatorname{SL}_2]$).
  2. Solving 2R planar robot inverse kinematics via Stickelberger companion matrices.
  3. Counting points on elliptic curves over $\mathbb{F}_p$ and verifying Hasse's bound.
- **Recipes (Tier 4 Applied Showcases)**:
  - `recipes/robot_kinematics_algebraic_variety.py` (and synced `.ipynb`) — 2R/3R inverse kinematics & singularity loci via `jacobian_at` and Stickelberger companion matrices.
  - `recipes/quantum_segre_entanglement_and_algebraic_stats.py` (and synced `.ipynb`) — Showcasing the Segre determinantal variety ($z_{00}z_{11} - z_{01}z_{10} = 0$) as an exact quantum entanglement / tensor rank-1 detector (`algebrax.tensor`), alongside Markov basis toric ideals ($p_{ij}p_{kl} - p_{il}p_{kj} = 0$) for statistical independence in `algebrax.probability`.

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0009-algebraic-and-tropical-varieties/sources/prototype_varieties.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0009-algebraic-and-tropical-varieties/sources/prototype_varieties.py) (Experiments 3 and 4).

---

## Rejected Ideas

1. **Abstract Grothendieck Schemes (`Spec(R)`, Prime Ideal Sheaves) in Core API**:
   - *Rejected*: Violates Feynman's Freshman Test and Shannon's minimal representation principle. Computing all prime ideals of a multivariate polynomial ring is prohibitively expensive and unnecessary for concrete geometric, kinematic, and finite-field varieties.
2. **Multivariate Resultant / Macaulay Sylvester Determinants as Primary Solver**:
   - *Rejected*: Sylvester/Macaulay resultant matrices grow much larger than the quotient basis dimension $\dim_k(k[V])$, whereas Stickelberger companion matrices have exact dimension $\dim_k(k[V]) \times \dim_k(k[V])$ and reuse `GroebnerIdeal.reduce`.

---

## Open Questions

- [ ] Adding pure-Python exact rational root isolation for 1D/triangular `lex` bases when `numpy` is not installed.

---

## Change Log

* **2026-11-14:**
  * Initial Draft authored for Phase 9 from `EXP-0009`.
