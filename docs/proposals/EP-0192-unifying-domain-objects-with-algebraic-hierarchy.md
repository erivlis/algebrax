---
title: "EP-0192: Unifying Domain Objects with the Pure Algebraic Hierarchy"
description: "Bind existing domain systems (Lie algebras, cohomology cochains, Clifford algebras, polynomial rings) to the Lean 4-aligned algebraic protocol hierarchy as first-class typeclass operators."
icon: lucide/git-merge
status: draft
---

# EP-0192: Unifying Domain Objects with the Pure Algebraic Hierarchy

| Field        | Value                                                     |
|:-------------|:----------------------------------------------------------|
| **EP**       | 0192                                                      |
| **Title**    | Unifying Domain Objects with the Pure Algebraic Hierarchy |
| **Author**   | Eran Rivlis & Antigravity                                 |
| **Sponsor**  | Council Framework                                         |
| **Delegate** | ⚖️ Noether (Algebraic Invariants) & 🧩 Russell (Taxonomy) |
| **Status**   | Draft                                                     |
| **Type**     | Standards Track                                           |
| **Created**  | 2026-10-27                                                |
| **Updated**  | 2026-10-27                                                |

## Abstract

This proposal establishes a bridge between AlgebraX's domain-specific mathematical engines (Lie theory in
`algebrax.lie`, algebraic topology in `algebrax.topology`, geometric algebra in `algebrax.clifford`, and polynomials in
`algebrax.semiring`) and the pure algebraic protocol hierarchy established
in [EP-0190](EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md)
and [EP-0191](EP-0191-rings-fields-modules-and-exact-solvers.md). By equipping domain objects—specifically `LieAlgebra`,
`CliffordSemiring`, `PolynomialSemiring`, `DualNumberSemiring`, and `Cochain`—with standard protocol methods (`add`,
`sub`, `neg`, `smul`, `mul`, `zero`, `one`), these structures become first-class algebraic typeclass operators while
preserving 100% of their existing capabilities, collaborator semiring compatibility, and unboxed sparse dictionary
representations.

Following unanimous Council review (Noether, Popper, Shannon, The Golem, Feynman, Russell, The Explorer), this proposal
incorporates single-pass vector arithmetic, explicit simplicial complex anchoring for cochain unitality, dedicated
non-associative and Lie algebra law verifiers, and tolerance-consistent zero-cleaning.

## Motivation

AlgebraX has evolved across multiple developmental phases:

- **Phase 1–2**: Foundations and specialized domains (`homology`, `clifford`, `galois`, `category`).
- **Phase 4**: Continuous symmetries and higher topology (`lie`, `topology.cohomology`, `dec`).
- **Phase 6**: Pure algebraic protocols (`algebrax.algebra`—magmas, monoids, groups, rings, fields, modules, algebras).

Because domain packages were built before the Phase 6 algebraic protocols existed, a significant structural disconnect
emerged:

1. **Isolated Operator Interfaces**: `LieAlgebra` implements `bracket(x, y)` and `adjoint_matrix(x)`, but has no
   `add(a, b)`, `smul(r, m)`, or `mul(a, b)` methods. To add or scale Lie elements, users must manually locate and
   invoke external functions (`vec_add`, `vec_scale`).
2. **Artificial Demotion of True Rings and Algebras**:
    - `PolynomialSemiring` and `CliffordSemiring` mask as mere `Semiring`s because they were written before `Ring` and
      `Algebra` existed in AlgebraX. Neither exposes `.neg()` or `.sub()`, even though multivectors and polynomials
      natively admit additive inverses.
    - Dual numbers $a + b\epsilon$ ($\epsilon^2 = 0$) form a commutative ring with nilpotents for automatic differentiation,
      but are constrained to `DualNumberSemiring`.
3. **Barriers to Generic Collaborators**: Functions like `power(algebra, x, n)` (logarithmic binary exponentiation),
   `zsmul(module, r, x)`, and `verify_algebra_laws` cannot operate directly on `LieAlgebra` or `CliffordSemiring`
   because the objects do not expose the required protocol methods.
4. **Under-formalized Topological Ring Structure**: In simplicial cohomology, discrete $k$-forms (`Cochain`) form a
   graded $R$-algebra under the Alexander–Whitney **cup product** ($\smile$). Currently, `cup_product` is an external
   standalone function, preventing cochains from participating in generic ring or module pipelines.

Binding these domain structures to `algebrax.algebra` protocols resolves these discrepancies, completing the unification
of AlgebraX.

### The Mental Model (The Freshman Test)

- **The Universal Arithmetic Rule**: If an object represents mathematical entities that can be added, scaled, and
  multiplied (like Lie algebra vectors, polynomials, or Clifford multivectors), the object itself should provide
  `.add()`, `.smul()`, `.mul()`, and `.zero`.
- **Domain-Specific Multiplications**:
  - In `LieAlgebra`, `.mul(a, b)` is the **Lie bracket** $[a, b] = ab - ba$ (alternating, non-associative, Jacobi-satisfying).
  - In `CliffordAlgebra`, `.mul(a, b)` is the **geometric product** $ab = a \cdot b + a \wedge b$.
  - In `CochainAlgebra`, `.mul(a, b)` is the **Alexander–Whitney cup product** $a \smile b$.
- **Generalization Without Loss**: Upgrading `CliffordSemiring` to `CliffordAlgebra` does not remove its ability to
  act as a semiring. Because `CliffordAlgebra` and `PolynomialRing` inherit from `QuotientMonoidAlgebraSemiring` (which
  supplies `star()`), they satisfy both the `Algebra` / `Ring` protocol and the `Semiring` protocol simultaneously.
  They are immediately usable anywhere a collaborator semiring is expected (e.g. in sparse matrix multiplication
  `dot(A, B, semiring=CliffordAlgebra())`).

## Rationale & Council Alignment

- **⚖️ Noether (Algebraic Invariants & Structural Conservation)**:
    - Formally realizes Lie algebras as the canonical non-associative algebra ($\mathfrak{g}$ satisfies bilinearity,
      antisymmetry, and the Jacobi identity).
    - Ensures `PolynomialRing.neg` delegates to the underlying coefficient ring's `.neg()` method, preserving canonical
      residues in finite modular fields $\mathbb{Z}_p$.
    - Identifies that `CochainAlgebra` requires an underlying `SimplicialComplex` to define the multiplicative unit
      $\mathbf{1} \in C^0(K; R)$ evaluating to $1_R$ on all 0-simplices.
- **🔬 Popper (Falsifiability & Empirical Invariants)**:
    - Retracts the claim that `LieAlgebra` satisfies `verify_algebra_laws` (which asserts unit $\mathbf{1}$ and
      associativity, both of which Lie algebras lack).
    - Specifies dedicated verification engines: `verify_non_assoc_algebra_laws` and `verify_lie_algebra_laws`.
    - Eliminates "ghost blades" in floating-point multivector subtraction via uniform tolerance zero-cleaning (`tol=1e-14`).
- **⚡ Shannon (Zero-Cost Delegation & Single-Pass Efficiency)**:
    - Eliminates double-normalization and intermediate dictionary allocation by implementing single-pass `sub(a, b)`
      via `vec_axpy(a, b, -1.0)` in `LieAlgebra`.
    - Implements direct elementwise subtraction in `CliffordAlgebra` and `PolynomialRing` rather than chaining `add(a, neg(b))`.\
    - Preserves unboxed sparse dictionary carriers with zero heap overhead and zero-cost symbol aliases.
- **🛡️ The Golem (Type Safety & Invariant Containment)**:
    - Corrects `CochainAlgebra` to use native `Cochain` operator overloads (`+`, `-`, `*`) rather than non-existent helper functions.
    - Accurately demarcates the `Semiring.star()` boundary under static type checking (`mypy`/`pyright`).
    - Enforces parameter contravariance and exact return types across all protocol implementations.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
    - Exposes the universal arithmetic interface (`.add()`, `.smul()`, `.mul()`) while clearly documenting domain-specific
      meanings of `.mul()` (bracket, geometric product, cup product).
- **🧩 Russell (Taxonomy & Deductive Consistency)**:
    - Validates `LieAlgebra` as `NonAssocAlgebra` without introducing redundant naming collisions.
    - Elevates `PolynomialAlgebra` and `DualNumberAlgebra` to full algebras over their scalar bases with `.smul()`, while preserving single-sorted `CommRing` and `Semiring` compatibility via exact aliases (`*Ring`, `*Semiring`).
    - Subclasses `DualNumberAlgebra` from concrete `DualNumberSemiring` while declaring `CommRing` and `Algebra`.
- **🧭 The Explorer (Curiosity & Frontier Synthesis)**:
    - Prepares the protocol substrate for Conformal Geometric Algebra ($C\ell(4, 1)$), Spacetime Algebra ($C\ell(1, 3)$),
      Jordan algebras, octonions, and Differential Graded Algebras (DGAs).

## Specification

### 1. `LieAlgebra` as `NonAssocAlgebra` (`src/algebrax/lie/core.py`)

`LieAlgebra` inherits from `NonAssocAlgebra[float | complex, LieElement]`:

```python
from collections.abc import Sequence
from algebrax.algebra import NonAssocAlgebra
from algebrax.matrix import vec_add, vec_axpy, vec_clean, vec_scale

LieElement = dict[int, float | complex]


class LieAlgebra(NonAssocAlgebra[float | complex, LieElement]):
    ...

    @property
    def zero(self) -> LieElement:
        """The additive zero element (empty sparse dictionary)."""
        return {}

    def add(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
        b: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Vector addition: a + b."""
        return vec_clean(vec_add(self._normalize_element(a), self._normalize_element(b)))

    def neg(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Additive inverse (negation): -a."""
        return vec_clean(vec_scale(self._normalize_element(a), -1.0))

    def sub(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
        b: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Vector difference: a - b (single-pass axpy, avoiding double normalization)."""
        norm_a = self._normalize_element(a)
        norm_b = self._normalize_element(b)
        return vec_clean(vec_axpy(norm_a, norm_b, -1.0))

    def smul(
        self,
        r: float | complex,
        m: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Scalar multiplication: r * m."""
        return vec_clean(vec_scale(self._normalize_element(m), r))

    def mul(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
        b: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Non-associative bilinear product [a, b]. Alias for self.bracket(a, b)."""
        return self.bracket(a, b)
```

**Type Conformance Guarantees**:
- `isinstance(lie, NonAssocAlgebra)` $\to$ `True`
- `isinstance(lie, Module)` $\to$ `True`
- `isinstance(lie, NonAssocRing)` $\to$ `True`
- `isinstance(lie, Ring)` $\to$ `False` (Exact: Lie multiplication has no unit $\mathbf{1}$)
- `isinstance(lie, Algebra)` $\to$ `False` (Exact: Lie bracket is non-associative)

---

### 2. Generalizing `CliffordSemiring` to `CliffordAlgebra` (`src/algebrax/semiring/algebraic.py`)

`CliffordSemiring` is redefined as `CliffordAlgebra`, inheriting both `QuotientMonoidAlgebraSemiring` and `Algebra`:

```python
from algebrax.algebra import Algebra
from algebrax.semiring.structures import QuotientMonoidAlgebraSemiring

SparseMultivector = dict[tuple[int, ...], float]


class CliffordAlgebra(
    QuotientMonoidAlgebraSemiring[tuple[int, ...], float],
    Algebra[float, SparseMultivector],
):
    r"""The Clifford (Geometric) Algebra $C\ell(p, q, r)$ over $\mathbb{R}$."""

    def neg(self, a: SparseMultivector) -> SparseMultivector:
        """Additive inverse of a multivector with zero-cleaning."""
        return {k: -v for k, v in a.items() if abs(v) > 1e-14}

    def sub(self, a: SparseMultivector, b: SparseMultivector) -> SparseMultivector:
        """Direct elementwise difference: a - b (eliminates intermediate allocation)."""
        result = dict(a)
        for k, v in b.items():
            diff = result.get(k, 0.0) - v
            if abs(diff) > 1e-14:
                result[k] = diff
            elif k in result:
                del result[k]
        return result

    def smul(self, r: float, m: SparseMultivector) -> SparseMultivector:
        """Scalar multiplication: r * m."""
        if abs(r) <= 1e-14:
            return {}
        return {k: r * v for k, v in m.items() if abs(r * v) > 1e-14}


# Canonical backwards-compatible aliases
CliffordSemiring = CliffordAlgebra
GeneralizedCliffordAlgebra = GeneralizedCliffordSemiring
QuantumCliffordAlgebra = QuantumCliffordSemiring
```

---

### 3. Generalizing `PolynomialSemiring` to `PolynomialAlgebra` (`src/algebrax/semiring/algebraic.py`)

Equipped with coefficient-aware negation and scalar multiplication to fulfill `CommRing[SparseVector[int, T]]` and `Algebra[T, SparseVector[int, T]]`:

```python
from algebrax.algebra import Algebra, CommRing
from algebrax.semiring.structures import MonoidAlgebraSemiring


class PolynomialAlgebra(
    MonoidAlgebraSemiring[int, T],
    CommRing[SparseVector[int, T]],
    Algebra[T, SparseVector[int, T]],
    Generic[T],
):
    r"""Polynomial associative algebra and commutative ring $R[x]$ over coefficient ring $R$."""

    def neg(self, a: SparseVector[int, T]) -> SparseVector[int, T]:
        """Negate coefficients, delegating to coefficient ring if available."""
        neg_fn = getattr(self.coeff_semiring, "neg", None)
        zero = self.coeff_semiring.zero
        if neg_fn is not None:
            return {deg: neg_fn(c) for deg, c in a.items() if c != zero}
        return {deg: -c for deg, c in a.items() if c != zero}

    def sub(self, a: SparseVector[int, T], b: SparseVector[int, T]) -> SparseVector[int, T]:
        """Direct polynomial difference: a - b."""
        neg_b = self.neg(b)
        return self.add(a, neg_b)

    def smul(self, r: T, m: SparseVector[int, T]) -> SparseVector[int, T]:
        """Scale polynomial by scalar r: r * (c0 + c1*x + ...) = (r*c0) + (r*c1)*x + ..."""
        zero = self.coeff_semiring.zero
        mul_fn = self.coeff_semiring.mul
        if r == zero:
            return {}
        return {deg: mul_fn(r, c) for deg, c in m.items() if mul_fn(r, c) != zero}


# Canonical backwards-compatible aliases
PolynomialRing = PolynomialAlgebra
PolynomialSemiring = PolynomialAlgebra
```

---

### 4. Generalizing `DualNumberSemiring` to `DualNumberAlgebra` (`src/algebrax/semiring/algebraic.py`)

Subclasses concrete `DualNumberSemiring` and implements both `CommRing` and `Algebra[float, tuple[float, float]]`:

```python
from algebrax.algebra import Algebra, CommRing


class DualNumberAlgebra(
    DualNumberSemiring,
    CommRing[tuple[float, float]],
    Algebra[float, tuple[float, float]],
):
    r"""The Dual Number Algebra $\mathbb{R}[\varepsilon] / (\varepsilon^2)$ over $\mathbb{R}$."""

    def neg(self, a: tuple[float, float]) -> tuple[float, float]:
        """Additive inverse: -(u + v*eps) = -u - v*eps."""
        return (-a[0], -a[1])

    def sub(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        """Difference: (u1 - u2, v1 - v2)."""
        return (a[0] - b[0], a[1] - b[1])

    def smul(self, r: float, m: tuple[float, float]) -> tuple[float, float]:
        """Stretch dual number by real scalar r: r * (u, v) = (r*u, r*v)."""
        return (r * m[0], r * m[1])


# Canonical backwards-compatible aliases
DualNumberRing = DualNumberAlgebra
DualNumberSemiring = DualNumberAlgebra
```

> [!NOTE]
> **Dual Multi-Protocol Conformance**: `DualNumberAlgebra` simultaneously satisfies `Semiring[tuple[float, float]]`
> (preserving `star()` for sparse matrix operations), `CommRing[tuple[float, float]]` (providing additive inverses and cancellation),
> and `Algebra[float, tuple[float, float]]` (providing scalar scaling `smul` over $\mathbb{R}$). Because $\varepsilon^2 = 0$,
> dual numbers contain nilpotent zero divisors ($(0, b)^2 = (0, 0)$) and therefore form a commutative ring and algebra,
> but not a `DivisionRing` or `Field`.

---

### 5. `CochainAlgebra` over Simplicial Complexes (`src/algebrax/topology/cohomology.py`)

`CochainAlgebra` anchors to the underlying `SimplicialComplex` to construct the canonical multiplicative unit $\mathbf{1}$:

```python
from algebrax.algebra import Algebra, Ring
from algebrax.homology import SimplicialComplex
from algebrax.topology.cohomology import Cochain, cup_product


class CochainAlgebra(Algebra[R, Cochain[K, R]], Generic[K, R]):
    r"""Differential graded algebra over simplicial cochains with the Alexander-Whitney cup product $\smile$."""

    def __init__(self, complex: SimplicialComplex, coefficient_ring: Ring[R]):
        self._complex = complex
        self._ring = coefficient_ring

    @property
    def zero(self) -> Cochain[K, R]:
        return Cochain({})

    @property
    def one(self) -> Cochain[K, R]:
        """Canonical 0-cochain assigning 1_R to every vertex in K_0."""
        return Cochain({(v,): self._ring.one for v in self._complex.vertices})

    def add(self, a: Cochain[K, R], b: Cochain[K, R]) -> Cochain[K, R]:
        return a + b

    def neg(self, a: Cochain[K, R]) -> Cochain[K, R]:
        return -a

    def sub(self, a: Cochain[K, R], b: Cochain[K, R]) -> Cochain[K, R]:
        return a - b

    def smul(self, r: R, m: Cochain[K, R]) -> Cochain[K, R]:
        return m * r

    def mul(self, a: Cochain[K, R], b: Cochain[K, R]) -> Cochain[K, R]:
        """Alexander-Whitney cup product: a \smile b."""
        return cup_product(a, b)
```

---

### 6. Verification Engine Additions (`src/algebrax/verification.py`)

Add dedicated verification functions tailored to non-unital and non-associative structures:

```python
def verify_non_assoc_algebra_laws(
    algebra: NonAssocAlgebra[R, M],
    ring: Ring[R],
    r_samples: Iterable[R],
    m_samples: Iterable[M],
    tol: float = 1e-7,
) -> dict[str, bool]:
    """Test Non-Associative Algebra laws:
    - Module laws over ring R
    - NonAssocRing laws on M (abelian group + two-sided distributivity)
    - Scalar bilinearity: r * (a * b) == (r * a) * b == a * (r * b)
    """
    ...


def verify_lie_algebra_laws(
    lie: NonAssocAlgebra[R, LieElement],
    ring: Ring[R],
    r_samples: Iterable[R],
    m_samples: Iterable[LieElement],
    tol: float = 1e-7,
) -> dict[str, bool]:
    """Test Lie Algebra axioms:
    - NonAssocAlgebra laws (Module + distributivity + bilinearity)
    - Skew-symmetry: [x, x] == 0 and [x, y] == -[y, x]
    - Jacobi Identity: [x, [y, z]] + [y, [z, x]] + [z, [x, y]] == 0
    """
    ...
```

---

## Backwards Compatibility

1. **100% Symbol Preservation**:
    - `CliffordSemiring`, `PolynomialSemiring`, and `DualNumberSemiring` remain available as exact aliases to
      `CliffordAlgebra`, `PolynomialAlgebra`, and `DualNumberAlgebra`.
    - `PolynomialRing` and `DualNumberRing` are also provided as canonical aliases.
    - All existing methods (`bracket`, `adjoint_matrix`, `killing_form`, `bch`, `power`, `star`) remain unmodified.
2. **Collaborator Semiring Interoperability**:
    - `CliffordAlgebra`, `PolynomialAlgebra`, and `DualNumberAlgebra` inherit from their respective base semirings, which implement `star()`.
    - They pass all type checks for `Semiring` and function seamlessly in `matrix.dot(..., semiring=...)`.

## How to Teach This / Documentation Plan

1. **User Guide Integration**:
    - Add unified arithmetic examples across domain guides (`guide/algebra/clifford_geometric_algebra.md`,
      `guide/algebra/lie_algebras.md`, `guide/algebra/polynomials_and_quotients.md`).
    - Explain domain `.mul()` semantics (Lie bracket, geometric product, cup product) using Feynman's 4-Beat Arc.
2. **The "Every Algebra is a Ring" Principle**:
    - Teach how upgrading from Semiring to Algebra unlocks additive cancellation and vector scaling without breaking
      sparse matrix multiplication pipelines.

## Reference Implementation

A prototype verification test on `LieAlgebra` confirmed:

```python
so3 = so_n(3)
assert isinstance(so3, NonAssocAlgebra)
assert isinstance(so3, Module)
assert isinstance(so3, NonAssocRing)
assert not isinstance(so3, Ring)
assert not isinstance(so3, Algebra)
```

## Rejected Ideas

1. **Asserting `LieAlgebra` satisfies `verify_algebra_laws`**:
    - *Rejected*: `verify_algebra_laws` asserts a multiplicative identity $\mathbf{1}$ and associativity, both of which
      Lie algebras lack. Corrected to `verify_non_assoc_algebra_laws` and `verify_lie_algebra_laws`.
2. **Instantiating `CochainAlgebra` without a `SimplicialComplex`**:
    - *Rejected*: Without the vertex set $K_0$, the multiplicative identity $\mathbf{1}$ under the cup product cannot
      be constructed, violating the `Algebra` protocol.
3. **Chaining `add(a, neg(b))` for vector subtraction**:
    - *Rejected*: Generates intermediate dictionary allocations and double normalization passes. Replaced with single-pass
      `vec_axpy`.

## Open Questions

- [x] Should `GeneralizedCliffordSemiring` and `QuantumCliffordSemiring` also be aliased to `*Algebra`? (**Resolved: Yes**).
- [x] Should `LieAlgebra` expose `.bracket` as primary with `mul = bracket`? (**Resolved: Yes**).

## Change Log

* **2026-10-27:**
    * Initial Draft authored by Eran Rivlis & Antigravity following Grand Council review of EP-0191.
    * Council Review Amendments: Single-pass `sub(a, b)` using `vec_axpy`, explicit `SimplicialComplex` anchoring for `CochainAlgebra`, dedicated `verify_lie_algebra_laws`, coefficient-aware `PolynomialAlgebra.neg`, and multi-protocol `Algebra` & `CommRing` elevation for `DualNumberAlgebra` and `PolynomialAlgebra` (with `*Ring` and `*Semiring` aliases).
