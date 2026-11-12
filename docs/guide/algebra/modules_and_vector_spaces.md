---
title: Modules, Vector Spaces & Algebras
description: Two-sorted algebraic structures (Semimodule, Module, VectorSpace, NonAssocAlgebra, Algebra) coupling a scalar domain R with a carrier space M.
---

# Modules, Vector Spaces & Algebras (`algebrax.algebra`)

## 1. The Practical Problem: Separating Scalars from Vectors

Single-sorted structures (`Monoid[V]`, `Ring[V]`, `Field[V]`) operate on a single type $V$. In linear algebra, differential geometry, and physics, however, **scalars** $r \in R$ and **vectors/operators** $m \in M$ are two distinct types linked by external scalar multiplication:
$$\cdot_s : R \times M \longrightarrow M$$
- When scalars $R$ form a **Semiring** and $M$ is an `AddCommMonoid`, $\langle R, M \rangle$ is a **`Semimodule[R, M]`**.
- When scalars $R$ form a **Ring** and $M$ is an `AddCommGroup`, $\langle R, M \rangle$ is a **`Module[R, M]`**.
- When scalars $R$ form a **Field**, $\langle R, M \rangle$ is a **`VectorSpace[R, M]`**.
- When $M$ also possesses a bilinear vector-vector product $M \times M \to M$, $\langle R, M \rangle$ is a **`NonAssocAlgebra[R, M]`** (e.g., Lie algebras) or an associative unital **`Algebra[R, M]`** (e.g., Clifford geometric algebras, polynomial algebras, cohomology rings).

---

## 2. The 30-Second Executable Snippet

```python
from algebrax.algebra import Algebra, Module, NonAssocAlgebra, PolynomialAlgebra
from algebrax.clifford import CliffordAlgebra
from algebrax.lie import so_n
from algebrax.semiring import StandardSemiring
from algebrax.topology import CochainAlgebra, SimplicialComplex

# 1. PolynomialAlgebra(StandardSemiring(int)) is an Algebra[int, dict[int, int]] and Module
poly = PolynomialAlgebra(StandardSemiring(int))
assert isinstance(poly, Algebra) and isinstance(poly, Module)
assert poly.smul(5, {0: 1, 2: -3}) == {0: 5, 2: -15}

# 2. CliffordAlgebra is an associative unital Algebra[float, dict[tuple[int, ...], float]]
cl3 = CliffordAlgebra(p=3, q=0)
assert isinstance(cl3, Algebra)

# 3. LieAlgebra is a NonAssocAlgebra (has bilinear bracket as mul, but no multiplicative identity 1!)
lie_so3 = so_n(3)
assert isinstance(lie_so3, NonAssocAlgebra)
assert not isinstance(lie_so3, Algebra)

# 4. CochainAlgebra is a graded associative Algebra over a SimplicialComplex
sc = SimplicialComplex([(0, 1, 2)])
ca = CochainAlgebra(sc, StandardSemiring(float))
assert isinstance(ca, Algebra)
```

---

## 3. Atomic Mixins & Protocol Contracts

All two-sorted protocols place `HasScale[R, M]` first in their base tuple alongside explicit `Protocol[R, M]` so the generic type parameter order `(R, M)` (Scalar Ring $R$ first, Carrier $M$ second) is strictly preserved:

| Named Protocol | Mixin Composition | Algebraic Signature |
|:---------------|:------------------|:--------------------|
| `Semimodule[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, + \rangle$ |
| `Module[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, - \rangle$ |
| `VectorSpace[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, - \rangle$ ($R$ is a `Field`) |
| `NonAssocAlgebra[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$ |
| `JordanAlgebra[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, -, \circ \rangle$ ($(x \circ y) \circ x^2 = x \circ (y \circ x^2)$) |
| `AlternativeAlgebra[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$ ($(x \cdot x) \cdot y = x \cdot (x \cdot y)$) |
| `MalcevAlgebra[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, -, [\cdot, \cdot] \rangle$ ($\operatorname{Im}(\mathbb{O})$) |
| `PoissonAlgebra[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], HasBracket[M], Protocol[R, M])` | $\langle R, P, \cdot_s, \mathbf{0}, +, -, \cdot, \{\cdot, \cdot\} \rangle$ |
| `Algebra[R, M]` | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasOne[M], HasMul[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ |

### Domain Unification Table

| Domain Structure | Module Path | Scalar $R$ | Carrier $M$ | `.mul(a, b)` Semantics |
|:-----------------|:------------|:-----------|:------------|:-----------------------|
| `PolynomialAlgebra[T]` | `algebrax.algebra` | `T` | `dict[int, T]` | Cauchy polynomial convolution |
| `DualNumberAlgebra` | `algebrax.algebra` | `float` | `tuple[float, float]` | Dual number product $(a+b\varepsilon)(c+d\varepsilon)$ |
| `SymmetricMatrixJordanAlgebra` | `algebrax.algebra` | `float` | `SparseMatrix[Any, float]` | Quantum anticommutator $A \circ B = \frac{1}{2}(AB + BA)$ |
| `OctonionAlgebra` | `algebrax.algebra` | `float` | `dict[int, float]` | Fano-plane Cayley–Dickson octonion product |
| `ImaginaryOctonionMalcevAlgebra` | `algebrax.algebra` | `float` | `dict[int, float]` | Malcev commutator $[x, y] = \frac{1}{2}(xy - yx)$ on $\operatorname{Im}(\mathbb{O})$ |
| `CliffordAlgebra` | `algebrax.clifford` | `float` | `dict[tuple[int, ...], float]` | Geometric product $ab = a \cdot b + a \wedge b$ |
| `LieAlgebra` | `algebrax.lie` | `float` | `dict[int, float]` | Lie commutator bracket $[X, Y]$ |
| `CochainAlgebra` | `algebrax.topology` | `float` | `dict[tuple[int, ...], float]` | Alexander–Whitney cup product $\alpha \smile \beta$ |

---

## 4. Non-Associative & Quantum Algebras (EP-0204)

Beyond Lie algebras, modern quantum mechanics, division algebra classification (Hurwitz's theorem), and Hamiltonian mechanics rely on structured non-associative algebras:

- **`SymmetricMatrixJordanAlgebra`**: Models quantum mechanical observables via the symmetric anticommutator $A \circ B = \frac{1}{2}(AB + BA)$, satisfying the Jordan identity $(x \circ y) \circ x^2 = x \circ (y \circ x^2)$.
- **`OctonionAlgebra`**: The 8-dimensional non-associative normed division algebra $\mathbb{O}$ over $\mathbb{R}$, satisfying Artin's left/right alternative identities ($x(xy) = (xx)y$, $(yx)x = y(xx)$) and Hurwitz norm multiplicativity $\|a \cdot b\|^2 = \|a\|^2 \|b\|^2$.
- **`ImaginaryOctonionMalcevAlgebra`**: The 7-dimensional commutator algebra on $\operatorname{Im}(\mathbb{O})$ satisfying the Malcev identity $J(x, y, [x, z]) = [J(x, y, z), x]$.
- **`PoissonAlgebra`**: Combines commutative multiplication `mul` with a Lie bracket `bracket` linked by the Leibniz derivation law $\{f, g \cdot h\} = \{f, g\} \cdot h + g \cdot \{f, h\}$.

```python
from algebrax.algebra import (
    ImaginaryOctonionMalcevAlgebra,
    OctonionAlgebra,
    SymmetricMatrixJordanAlgebra,
)
from algebrax.verification import (
    verify_alternative_laws,
    verify_jordan_laws,
    verify_malcev_laws,
)

# 1. Jordan Algebra of Quantum Observables
jordan = SymmetricMatrixJordanAlgebra()
m1 = {0: {0: 2.0, 1: 1.0}, 1: {0: 1.0, 1: 3.0}}
m2 = {0: {0: -1.0, 1: 4.0}, 1: {0: 4.0, 1: 2.0}}
assert all(verify_jordan_laws(jordan, [m1, m2]).values())

# 2. Octonions O and Alternative Division Laws
octo = OctonionAlgebra()
e1, e2, e4 = {1: 1.0}, {2: 1.0}, {4: 1.0}
assert octo.associator(e1, e2, e4) == {7: 2.0}  # Non-associative!
assert all(verify_alternative_laws(octo, [e1, e2, e4]).values())

# 3. Malcev Algebra on Im(O)
malcev = ImaginaryOctonionMalcevAlgebra()
assert all(verify_malcev_laws(malcev, [e1, e2, e4]).values())
```

---

## 5. Falsifiability: Law Verification & Bilinearity

Every module and algebra can be verified using `verify_module_laws`, `verify_non_assoc_algebra_laws`, and `verify_algebra_laws`:

```python
from algebrax.semiring import StandardSemiring
from algebrax.verification import verify_algebra_laws, verify_non_assoc_algebra_laws

# 1. Verify CliffordAlgebra Cl(2, 0) satisfies all associative Algebra laws
cl2 = CliffordAlgebra(p=2, q=0)
scalars = [0.0, 1.0, -2.0, 0.5]
multivectors = [{}, {(): 1.0}, {(1,): 2.0}, {(1, 2): -1.0}]
assert all(verify_algebra_laws(cl2, StandardSemiring(float), scalars, multivectors).values())

# 2. Verify LieAlgebra so(3) satisfies NonAssocAlgebra bilinearity laws
vecs = [{}, {0: 1.0}, {1: 2.0}, {0: 1.0, 2: -1.0}]
assert all(verify_non_assoc_algebra_laws(lie_so3, StandardSemiring(float), scalars, vecs).values())
```

---

## 6. Frontier Horizons & Cross-Domain Bridges

- **[Clifford Geometric Algebras](clifford_geometric_algebra.md)**: Unify inner products and exterior wedge products into an associative unital `Algebra`.
- **[Lie Algebras](lie_algebras.md)**: Model tangent spaces of continuous symmetry groups as a `NonAssocAlgebra` where `.mul()` is the alternating Lie bracket $[X, Y]$.
- **[Cohomology Rings](../topology/cohomology.md)**: Turn topological cochains into a graded `Algebra` under the Alexander–Whitney cup product $\smile$.
