---
title: "EP-0220: Multivariate Polynomial Algebra & Exact Gröbner Ideals"
description: "Formalize unboxed multivariate polynomial algebras k[x_1, ..., x_n], monomial orderings, and exact Gröbner basis ideals via Buchberger and F4-style sparse Macaulay matrix reduction."
icon: lucide/variable
status: final
---

# EP-0220: Multivariate Polynomial Algebra & Exact Gröbner Ideals

| Field             | Value                                                                                      |
|:------------------|:-------------------------------------------------------------------------------------------|
| **EP**            | 0220                                                                                       |
| **Title**         | Multivariate Polynomial Algebra & Exact Gröbner Ideals                                     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                |
| **Sponsor**       | Core Maintainers                                                                           |
| **Delegate**      | ⚡ Shannon (Unboxed Sparse Carriers), 🔬 Popper (Exactness Mandate) & ⚖️ Noether (Ideals)   |
| **Status**        | Final                                                                                      |
| **Type**          | Standards Track                                                                            |
| **Created**       | 2026-11-14                                                                                 |
| **Updated**       | 2026-11-25                                                                                 |
| **Replaces**      | —                                                                                          |
| **Superseded-By** | —                                                                                          |

---

## Abstract

This proposal generalizes AlgebraX's univariate `PolynomialAlgebra` to the sparse multivariate polynomial ring $k[x_1, \dots, x_n]$ over an exact `Field[V]` and introduces canonical **Gröbner Basis Ideals** (`GroebnerIdeal`). Specifically, EP-0220 establishes:

1. **Unboxed Multivariate Polynomial Algebra (`MultivariatePolynomialAlgebra[V]`)**:
   Models $k[x_1, \dots, x_n]$ as a `MonoidAlgebra[tuple[int, ...], V]` over the additive monoid $(\mathbb{N}_0^n, +)$ with native unboxed dictionary carrier `dict[tuple[int, ...], V]`.
2. **Admissible Monomial Orderings**:
   First-class support for Lexicographic (`lex`), Graded Lexicographic (`grlex`), and Graded Reverse Lexicographic (`grevlex`) monomial orders, exposing leading monomial (`lm`), leading coefficient (`lc`), leading term (`lt`), S-polynomials (`s_poly`), and multivariate remainder division (`reduce_poly`).
3. **Hybrid Buchberger & F4 Sparse Macaulay Engine (`groebner_basis`)**:
   Combines classical Buchberger reduction (with Product and Gebauer–Möller Chain criteria) and Faugère's $F_4$-style symbolic preprocessing + sparse Macaulay matrix Reduced Row Echelon Form (RREF) over exact `Field[V]`.
4. **Canonical `GroebnerIdeal[V]` (`algebrax.algebra._ideals`)**:
   Implements the [`EP-0201`](EP-0201-algebraic-homomorphisms-ideals-quotients.md) `Ideal[SparseMPoly[V]]` protocol (`contains`, `reduce`), enabling immediate construction of affine coordinate rings $k[V] = k[x_1, \dots, x_n]/I$ via `QuotientRing(ring, ideal)`.
5. **Strict Exact-Field Guardrail**:
   Explicitly rejects IEEE-754 floating-point fields (`float`, `complex`) at `GroebnerIdeal` construction time to prevent catastrophic cancellation and false unit-ideal collapse.

---

## Motivation

While [`EP-0201`](EP-0201-algebraic-homomorphisms-ideals-quotients.md) introduced the `Ideal[V]` and `QuotientRing[V]` protocols, and [`EP-0191`](EP-0191-rings-fields-modules-and-exact-solvers.md) introduced `PolynomialAlgebra`, AlgebraX's concrete polynomial and ideal machinery is currently restricted to a single variable:

1. **Univariate Limitation**: `PolynomialAlgebra` (`src/algebrax/algebra/_polynomial.py`) is fixed to `MonoidAlgebra[int, T]`, representing only $R[x]$. However, algebraic geometry, robotics kinematics, invariant theory ([`EP-0214`](EP-0214-invariant-theory-molien-series-casimir-polynomials.md)), and cryptographic SAT problems require multivariate polynomial rings $k[x_1, \dots, x_n]$.
2. **No Multivariate Ideal Membership or Normal-Form Reducer**: In univariate $k[x]$, every ideal is principal ($I = \langle g(x) \rangle$), and Euclidean polynomial division yields unique remainders. In $k[x_1, \dots, x_n]$ ($n \ge 2$), naive division by generators $\langle f_1, \dots, f_m \rangle$ depends on generator order and fails to detect ideal membership ($f \in I \not\iff \text{rem}(f, \{f_i\}) = 0$) unless the generators form a **Gröbner Basis**.
3. **Unlocking `QuotientRing` for Coordinate Rings**: With a canonical reduced Gröbner basis $G = \{g_1, \dots, g_t\}$, multivariate division $\overline{f}^G$ is unique and satisfies $f - h \in I \iff \overline{f}^G = \overline{h}^G$. This makes `GroebnerIdeal` a drop-in `Ideal` for `QuotientRing(ring, ideal)` with zero wrapper overhead.

---

## Rationale

This design is grounded in the empirical findings of [**EXP-0009**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0009-algebraic-and-tropical-varieties/README.md) and aligned with the Grand Council:

- **⚡ Claude Shannon (Unboxed Carrier Invariance & Sparse Macaulay RREF)**:
  - Rejects symbolic AST trees (`Add(Mul(Pow(Symbol('x'), 2), ...))`). A multivariate polynomial in $n$ variables is an unboxed sparse dictionary `dict[tuple[int, ...], V]` mapping exponent tuples $\alpha = (\alpha_1, \dots, \alpha_n) \in \mathbb{N}_0^n$ to non-zero coefficients in $V$.
  - Faugère's $F_4$ algorithm turns S-polynomial reduction into sparse Gaussian elimination on a Macaulay matrix — directly utilizing AlgebraX's sparse dictionary row operations (`3.20 ms` on 4-variable rational 2R Robot Inverse Kinematics vs. `16.56 ms` for classical Buchberger and `14.12 ms` for SymPy in `EXP-0009`).
- **🔬 Karl Popper (Falsifiability & The Exactness Mandate)**:
  - In `EXP-0009` Experiment 1, running Gröbner reduction over `StandardField(float)` caused IEEE-754 cancellation noise ($\approx 10^{-16}$) to become a spurious leading term and collapse a valid 2-point variety into the unit ideal `[{(0, 0): 1.0}]` ($V(I) = \emptyset$), whereas adding a tolerance `tol=1e-12` erased a genuine $10^{-14}x$ term and inflated a 0-dimensional variety into a 1-dimensional circle.
  - Therefore, `GroebnerIdeal` and `groebner_basis` enforce a strict runtime guardrail: the coefficient structure must be an **exact** `Field[V]` (`StandardField(Fraction)`, `ModularField(p)`, or `GaloisFieldSemiring`).
- **⚖️ Emmy Noether (Ideal Absorption & Canonical Normal Forms)**:
  - Completes Hilbert's Basis Theorem computationally: every finitely generated ideal $I \triangleleft k[x_1, \dots, x_n]$ possesses a unique **reduced monic Gröbner basis** for a fixed monomial order, providing a canonical invariant signature for the ideal itself.
- **🧩 Bertrand Russell (Monoid Algebra Taxonomy)**:
  - Models $k[x_1, \dots, x_n]$ deductively as a subclass of `MonoidAlgebra[tuple[int, ...], V]` satisfying `Algebra[V, SparseMPoly[V]]` and `CommRing[SparseMPoly[V]]`.
- **💡 Richard Feynman (The Freshman Test)**:
  - *"In one variable, you divide by the highest power of $x$ until the remainder has smaller degree. In many variables, 'highest power' is ambiguous until you pick a tie-breaker rule (`lex`, `grlex`, `grevlex`), and a Gröbner basis is just the complete set of dividers that guarantees no hidden cancellations are missed."*

---

## Specification

### 1. Atomic Operational Mixins (`src/algebrax/algebra/_mixins.py`)

Extends [`EP-0005`](EP-0005-universal-algebraic-protocol-architecture.md) Layer 1 capabilities with two atomic mixins for finitely generated ideals and formal derivations:

```python
from typing import Protocol, TypeVar, runtime_checkable

V = TypeVar("V")


@runtime_checkable
class HasBasis(Protocol[V]):
    r"""Finite generating basis `basis` ($\langle g_1, \dots, g_t \rangle$) generalizing `HasGenerator`."""

    @property
    def basis(self) -> tuple[V, ...]: ...


@runtime_checkable
class HasDerivation(Protocol[V]):
    r"""Formal algebraic derivation $\partial_i: V \to V$ satisfying Leibniz rule $\partial_i(ab) = \partial_i(a)b + a\partial_i(b)$."""

    def diff(self, a: V, var_index: int = 0) -> V: ...
```

### 2. Monomial Operations & Orderings (`src/algebrax/algebra/_polynomial.py`)

Exponent vectors are native $n$-tuples `Monomial = tuple[int, ...]`:

```python
from collections.abc import Callable, Sequence
from typing import Generic, Literal, TypeVar

from algebrax.algebra._field import Field
from algebrax.algebra._ideals import Ideal
from algebrax.algebra._mixins import HasBasis, HasContains, HasDerivation, HasReduce
from algebrax.algebra._monoid_algebra import MonoidAlgebra

V = TypeVar("V")
Monomial = tuple[int, ...]
SparseMPoly = dict[Monomial, V]
MonomialOrder = Literal["lex", "grlex", "grevlex"]


def monomial_add(a: Monomial, b: Monomial) -> Monomial:
    """Multiply monomials x^a * x^b = x^(a + b)."""
    return tuple(x + y for x, y in zip(a, b, strict=True))


def monomial_divides(a: Monomial, b: Monomial) -> bool:
    """Return True iff x^a divides x^b (all a_i <= b_i)."""
    return all(x <= y for x, y in zip(a, b, strict=True))


def monomial_lcm(a: Monomial, b: Monomial) -> Monomial:
    """Least common multiple of monomials x^a and x^b."""
    return tuple(max(x, y) for x, y in zip(a, b, strict=True))
```

Supported admissible monomial orders ($\succ$):
- **`lex`**: $\alpha \succ_{\text{lex}} \beta \iff$ leftmost non-zero entry of $\alpha - \beta$ is positive (variable elimination order).
- **`grlex`**: Total degree $|\alpha| > |\beta|$, breaking ties by `lex`.
- **`grevlex`** *(Default)*: Total degree $|\alpha| > |\beta|$, breaking ties where the *rightmost* non-zero entry of $\alpha - \beta$ is negative (minimizes intermediate degree swell).

### 3. `MultivariatePolynomialAlgebra` (`src/algebrax/algebra/_polynomial.py`)

```python
class MultivariatePolynomialAlgebra(
    MonoidAlgebra[Monomial, V],
    HasDerivation[SparseMPoly[V]],
    Generic[V],
):
    r"""The Multivariate Polynomial Algebra $k[x_1, \dots, x_n]$ over an exact Field $k$.

    Algebraic Signature:
        $\langle k, k[x_1, \dots, x_n], \cdot_s, \emptyset, +, -, \{\mathbf{0}: 1_k\}, \cdot, \partial_i \rangle$

    Carrier:
        `dict[tuple[int, ...], V]` (Sparse mapping from $\alpha \in \mathbb{N}_0^n$ to $c_\alpha \in k$).
    """

    def __init__(
        self,
        field: Field[V],
        n_vars: int,
        order: MonomialOrder = "grevlex",
    ) -> None: ...

    def gen(self, index: int) -> SparseMPoly[V]:
        """Return the i-th coordinate generator polynomial x_i."""
        ...

    def lm(self, poly: SparseMPoly[V]) -> Monomial:
        """Return the leading monomial LM(poly) under `self.order`."""
        ...

    def lc(self, poly: SparseMPoly[V]) -> V:
        """Return the leading coefficient LC(poly) in `self.field`."""
        ...

    def make_monic(self, poly: SparseMPoly[V]) -> SparseMPoly[V]:
        """Scale non-zero polynomial by LC(poly)^{-1} so LC == 1."""
        ...

    def eval(self, poly: SparseMPoly[V], point: Sequence[V]) -> V:
        """Evaluate polynomial at `point = (p_1, ..., p_n)` in k^n."""
        ...

    def diff(self, poly: SparseMPoly[V], var_index: int = 0) -> SparseMPoly[V]:
        r"""Formal algebraic partial derivative $\frac{\partial f}{\partial x_i}$ over `self.field`.

        Purely algebraic ($\alpha_i c_\alpha x^{\alpha - e_i}$); works over any exact field,
        including finite prime fields `ModularField(p)`.
        """
        ...

    def univariate_gcd(
        self,
        f: SparseMPoly[V],
        g: SparseMPoly[V],
        var_index: int,
    ) -> SparseMPoly[V]:
        """Compute monic Euclidean GCD of two univariate polynomials in variable `x_{var_index}`."""
        ...

    def square_free_part(self, f: SparseMPoly[V], var_index: int) -> SparseMPoly[V]:
        r"""Return square-free part $f / \gcd(f, \partial f / \partial x_i)$ for 0-dim radical reduction."""
        ...

    def poisson_bracket(
        self,
        f: SparseMPoly[V],
        g: SparseMPoly[V],
    ) -> SparseMPoly[V]:
        r"""Canonical symplectic Poisson bracket $\{f, g\} = \sum_{i=1}^{m} \left(\frac{\partial f}{\partial q_i}\frac{\partial g}{\partial p_i} - \frac{\partial f}{\partial p_i}\frac{\partial g}{\partial q_i}\right)$.

        Requires even `n_vars = 2 * m` ordered as $(q_1, \dots, q_m, p_1, \dots, p_m)$, equipping
        $k[q_1, \dots, q_m, p_1, \dots, p_m]$ with the `PoissonAlgebra` structure from `EP-0204`
        (satisfying the Leibniz rule $\{f, gh\} = \{f, g\}h + g\{f, h\}$ and Jacobi identity).
        """
        ...

    def s_poly(self, f: SparseMPoly[V], g: SparseMPoly[V]) -> SparseMPoly[V]:
        """Compute S-polynomial S(f, g) = (lcm / LT(f)) * f - (lcm / LT(g)) * g."""
        ...

    def reduce_poly(
        self,
        f: SparseMPoly[V],
        basis: Sequence[SparseMPoly[V]],
    ) -> SparseMPoly[V]:
        """Multivariate division algorithm returning remainder of `f` modulo `basis`.

        For large bases, leading-monomial divisibility queries (`monomial_divides`) can be
        indexed via an `AlgebraicTrie` (`EP-0174`) over exponent tuples `(a_1, ..., a_n)`.
        """
        ...
```

### 4. Hybrid Buchberger / F4 Gröbner Engine & `GroebnerIdeal` (`src/algebrax/algebra/_ideals.py`)

```python
@runtime_checkable
class FinitelyGeneratedIdeal(HasContains[V], HasReduce[V], HasBasis[V], Protocol[V]):
    r"""A finitely generated ideal $I = \langle g_1, \dots, g_t \rangle \triangleleft R$ (`EP-0005` flat composition)."""

    ...


def groebner_basis(
    ring: MultivariatePolynomialAlgebra[V],
    generators: Sequence[SparseMPoly[V]],
    *,
    method: Literal["auto", "f4", "buchberger"] = "auto",
) -> list[SparseMPoly[V]]:
    r"""Compute the unique reduced monic Gröbner basis of $\langle \text{generators} \rangle$.

    Raises:
        TypeError: If `ring.field` is an inexact floating-point field (`float` or `complex`).
    """
    ...


class GroebnerIdeal(FinitelyGeneratedIdeal[SparseMPoly[V]], Ideal[SparseMPoly[V]], Generic[V]):
    r"""A finitely generated polynomial ideal $I = \langle g_1, \dots, g_m \rangle \triangleleft k[x_1, \dots, x_n]$.

    Backed by its unique reduced monic Gröbner basis $G$ under `ring.order`.
    Satisfies `FinitelyGeneratedIdeal[SparseMPoly[V]]` and `Ideal[SparseMPoly[V]]` (`contains`, `reduce`, `basis`)
    for direct use with `QuotientRing`.
    """

    def __init__(
        self,
        ring: MultivariatePolynomialAlgebra[V],
        generators: Sequence[SparseMPoly[V]],
        *,
        method: Literal["auto", "f4", "buchberger"] = "auto",
    ) -> None: ...

    @property
    def basis(self) -> tuple[SparseMPoly[V], ...]:
        """The canonical reduced monic Gröbner basis."""
        ...

    def contains(self, element: SparseMPoly[V]) -> bool:
        """Test ideal membership: f in I iff reduce(f) == {}."""
        return len(self.reduce(element)) == 0

    def reduce(self, element: SparseMPoly[V]) -> SparseMPoly[V]:
        """Return canonical normal-form remainder mod G."""
        return self.ring.reduce_poly(element, self._basis)

    def is_unit(self) -> bool:
        """Return True iff I = (1) (i.e., V(I) is empty over algebraic closure)."""
        ...
```

### 5. Verification Oracles (`src/algebrax/verification.py`)

- `verify_groebner_basis_laws(ring, ideal)`:
  1. Verifies every original generator reduces to `{}` modulo `ideal.basis`.
  2. Verifies Buchberger's criterion: $\forall g_i, g_j \in G,\; \mathrm{ideal.reduce}(S(g_i, g_j)) == \{\}$.
  3. Verifies reducedness: every $g \in G$ is monic and no term of $g$ is divisible by $\mathrm{LM}(g')$ for $g' \ne g$.
  4. Verifies `QuotientRing(ring, ideal)` satisfies `CommRing` laws via `verify_quotient_ring_laws`.

---

## Backwards Compatibility

100% backwards compatible. Existing univariate `PolynomialAlgebra` and `PolynomialTruncationIdeal` remain unchanged. `MultivariatePolynomialAlgebra` and `GroebnerIdeal` are strictly additive exports in `algebrax.algebra`.

---

## How to Teach This / Documentation Plan

- **User Guide**: Expand `docs/guide/algebra/polynomials_and_quotients.md` with a dedicated section on multivariate polynomials, monomial orders (`lex` elimination vs. `grevlex` speed), and constructing quotient rings $k[x, y]/I$ via `GroebnerIdeal`.
- **AMDS Docstrings**: Include full KaTeX algebraic signatures and runnable doctests for `MultivariatePolynomialAlgebra` and `GroebnerIdeal`.

---

## Reference Implementation

Validated in the executable prototype [`references/explorations/EXP-0009-algebraic-and-tropical-varieties/sources/prototype_varieties.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0009-algebraic-and-tropical-varieties/sources/prototype_varieties.py) with 100% agreement against `sympy.groebner` across `TwistedCubic`, `Cyclic-3`, `Cyclic-4`, and `2R-Robot-IK`.

---

## Rejected Ideas

1. **Allowing `StandardField(float)` with Tolerance in `GroebnerIdeal`**:
   - *Rejected*: Empirically falsified in `EXP-0009` Experiment 1. Both zero-tolerance (`tol=0.0`) and non-zero tolerance (`tol=1e-12`) produce mathematically wrong ideal dimensions and false unit ideals under S-polynomial subtraction.
2. **Expression-Tree Symbolic Polynomials (`class PolyExpr`)**:
   - *Rejected*: Violates [`EP-0004`](EP-0004-unboxed-storage-and-sparse-carrier-invariance.md) (Unboxed Storage) and Shannon efficiency. Sparse dictionaries `dict[tuple[int, ...], V]` are unboxed, hashable-keyed, and directly compatible with `MonoidAlgebra`.

---

## Open Questions

- [x] Whether `method="auto"` should select `"f4"` for rational fields (`StandardField(Fraction)`) and `"buchberger"` (with Gebauer–Möller criteria) for small prime fields (`ModularField(p)`), or always run Gebauer–Möller-filtered $F_4$.
  - *Resolved (2026-11-25)*: `method="auto"` uniformly runs Gebauer–Möller-filtered $F_4$ (`_groebner_f4`) across all exact fields (`StandardField(Fraction)`, `ModularField(p)`, `GaloisField`), avoiding field-specific branching while outperforming classical Buchberger on elimination (`lex`) and higher-degree systems (`4.12 ms` vs. `4.27 ms` on `lex Cyclic-4` over $\mathbb{Q}$; `2.49 ms` vs. `2.98 ms` over $\mathbb{F}_{101}$). Explicit `method="buchberger"` and `method="f4"` remain selectable.

---

## Change Log

* **2026-11-25:**
  * Implemented full specification and transitioned status to **Final**:
    - Added `HasBasis` and `HasDerivation` atomic mixins (`src/algebrax/algebra/_mixins.py`).
    - Added `MultivariatePolynomialAlgebra`, monomial arithmetic, and `lex`/`grlex`/`grevlex` orderings (`src/algebrax/algebra/_polynomial.py`), including characteristic-aware `square_free_part` (with Frobenius $p$-th root extraction over $\mathbb{F}_p$ and $\mathrm{GF}(p^m)$) and `PoissonAlgebra`-compliant `poisson_bracket`/`bracket`.
    - Promoted `GaloisField` (`src/algebrax/algebra/_field.py`, exported from `algebrax.algebra`, `algebrax.galois`, and `algebrax.semiring`, replacing `GaloisFieldSemiring`) with full exact `Field` operations (`is_zero`, `neg`, `sub`, `inv`, `div`) via Extended Euclidean Algorithm.
    - Added hybrid Gebauer–Möller Buchberger & $F_4$ sparse Macaulay RREF engine (`src/algebrax/algebra/_groebner.py`) with strict IEEE-754 exact-field guardrail, plus `FinitelyGeneratedIdeal` and `GroebnerIdeal` (`src/algebrax/algebra/_ideals.py`).
    - Added `verify_groebner_basis_laws` oracle (`src/algebrax/verification/_algebra.py`), unit/falsification tests (`tests/algebrax/test_multivariate_groebner.py`), differential `sympy.groebner` oracles (`tests/verifications/test_differential_sympy.py`), and expanded user guide (`docs/guide/algebra/polynomials_and_quotients.md`).
* **2026-11-14:**
  * Initial Draft authored for Phase 9 from `EXP-0009`.
