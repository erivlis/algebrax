---
title: Topological K-Theory, Grothendieck Groups & Characteristic Classes
description: Universal Grothendieck group and ring completion, Whitney direct sums, tensor products of discrete vector bundles, virtual bundles in K^0(X), and discrete Chern character forms.
---

# Topological K-Theory, Grothendieck Groups & Characteristic Classes (`algebrax.topology.k_theory`)

**Topological K-Theory** bridges discrete gauge connections, commutative algebra, and simplicial cohomology by completing the commutative semiring of vector bundles $(\mathrm{Vect}(X), \oplus, \otimes)$ into a commutative ring of **virtual vector bundles** $K^0(X)$ via the universal **Grothendieck group construction** (`GrothendieckGroup`, `GrothendieckRing`).

---

## 1. Universal Grothendieck Group $K_0(M)$ & Ring $K_0(S)$ (`algebrax.algebra`)

Given any additive commutative monoid $(M, +, 0)$, its **Grothendieck group** $K_0(M)$ (`GrothendieckGroup`) is the universal abelian group (`AddCommGroup`) of formal differences $[a] - [b]$ represented by pairs $(a, b) \in M \times M$ under the stabilized equivalence relation:

$$(a, b) \sim (c, d) \iff \exists k \in M \text{ such that } a + d + k = b + c + k$$

When $S$ is a commutative semiring $(S, +, \cdot, 0, 1)$, `GrothendieckRing` equips $K_0(S)$ with formal difference multiplication (`CommRing`):

$$(a - b) \cdot (c - d) = (a c + b d) - (a d + b c)$$

### Universal Property of $K_0(M)$

Every monoid homomorphism $f: M \to G$ into an abelian group $G$ factors uniquely through the canonical embedding $\iota(a) = (a, 0_M)$ via `lift_homomorphism`:

$$\tilde{f}(a, b) = f(a) -_G f(b), \qquad \tilde{f} \circ \iota = f$$

```python
from algebrax.algebra import AddCommGroup, AddCommMonoid, GrothendieckGroup, GrothendieckRing
from algebrax.semiring import Semiring
from algebrax.verification import verify_comm_ring_laws, verify_grothendieck_universal_property


class NatSemiring(Semiring[int]):
    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, a: int, b: int) -> int:
        return a + b

    def mul(self, a: int, b: int) -> int:
        return a * b


class RealAddGroup(AddCommGroup[float]):
    @property
    def zero(self) -> float:
        return 0.0

    def add(self, a: float, b: float) -> float:
        return a + b

    def neg(self, a: float) -> float:
        return -a


# Construct K_0(N, +, *) = Z with canonical pair reduction (a - min(a,b), b - min(a,b))
k0_z = GrothendieckRing(
    NatSemiring(),
    normalize_fn=lambda p: (p[0] - min(p), p[1] - min(p)),
)

# (3 - 1) * (2 - 5) = 2 * (-3) = -6 -> canonical pair (0, 6)
assert k0_z.mul((3, 1), (2, 5)) == (0, 6)
assert all(verify_comm_ring_laws(k0_z, [(0, 0), (1, 0), (2, 0), (0, 3)]).values())

# Universal property: lift f(n) = 2.5 * n from N to (R, +)
props = verify_grothendieck_universal_property(
    k0_z,
    RealAddGroup(),
    monoid_map=lambda n: 2.5 * float(n),
    monoid_samples=[0, 1, 2, 3],
)
assert all(props.values())
```

---

## 2. Whitney Direct Sums ($E_1 \oplus E_2$) & Tensor Products ($E_1 \otimes E_2$)

Over a 1-skeleton $K_1$, discrete orthogonal vector bundles (`DiscreteOrthogonalConnection`) form a commutative semiring under:

1. **Whitney Direct Sum (`bundle_direct_sum`)**: Block-diagonal parallel transport of fiber dimension $d_1 + d_2$:
   $$\rho_{E_1 \oplus E_2}(u, v) = \begin{pmatrix} \rho_1(u, v) & \mathbf{0} \\ \mathbf{0} & \rho_2(u, v) \end{pmatrix}$$
2. **Bundle Tensor Product (`bundle_tensor_product`)**: Kronecker product parallel transport of fiber dimension $d_1 \cdot d_2$:
   $$\rho_{E_1 \otimes E_2}(u, v) = \rho_1(u, v) \otimes \rho_2(u, v)$$
3. **Trivial Flat Bundle (`trivial_bundle`)**: Flat rank-$d$ identity bundle $\underline{\mathbb{R}}^d$ with $\rho(u, v) = I_d$.

---

## 3. Discrete Chern Character ($\mathrm{ch}$) & Integer Chern Numbers

The **Chern–Weil homomorphism** maps the curvature holonomy $\Omega(f)$ of a discrete bundle on 2-faces into simplicial cohomology $H^{2k}(K; \mathbb{R})$:

- **First Chern Character 2-Form (`compute_chern_character_1`)**:
  $$\mathrm{ch}_1(E)(f) = c_1(E)(f) = \frac{1}{2\pi} \Omega(f)$$
- **Second Chern Character (`compute_chern_character_2`)**:
  Evaluates the quadratic curvature form $\frac{1}{2} c_1(E) \smile c_1(E)$ via the Alexander–Whitney cup product on 4-simplices (or facewise quadratic curvature density on 2-faces).
- **Chern Character Ring Homomorphism (`chern_character`)**:
  $$\mathrm{ch}(E_1 \oplus E_2) = \mathrm{ch}(E_1) + \mathrm{ch}(E_2)$$
- **Topological Charge Quantization (`first_chern_number`, `verify_chern_number_integrality`)**:
  Over any closed oriented 2-cycle $\Sigma$ (such as the boundary of a tetrahedron $\partial \Delta^3 \cong S^2$), the integrated first Chern number is quantized to an exact integer:
  $$\int_\Sigma c_1(E) = \sum_{f \in \Sigma} c_1(E)(f) \in \mathbb{Z}$$

```python
import math
from algebrax.topology import (
    DiscreteOrthogonalConnection,
    TopologicalKTheoryRing,
    first_chern_number,
    trivial_bundle,
)
from algebrax.verification import (
    verify_chern_character_additivity,
    verify_chern_number_integrality,
)


def rot2d(theta: float) -> dict[int, dict[int, float]]:
    c, s = math.cos(theta), math.sin(theta)
    return {0: {0: c, 1: -s}, 1: {0: s, 1: c}}


# Outward-oriented boundary 2-cycle of a tetrahedron S^2
oriented_faces = [(1, 2, 3), (0, 3, 2), (0, 1, 3), (0, 2, 1)]
edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

# Construct a discrete U(1) ~= SO(2) monopole bundle with Dirac string on face (1, 2, 3)
monopole = DiscreteOrthogonalConnection(2)
for u, v in [(0, 1), (0, 2), (0, 3)]:
    monopole.set_transport(u, v, rot2d(0.0))
monopole.set_transport(1, 2, rot2d(2.2))
monopole.set_transport(2, 3, rot2d(2.2))
monopole.set_transport(1, 3, rot2d(-2.2))

c1_int = first_chern_number(monopole, oriented_faces)
print('First Chern number on S^2:', round(c1_int))  # -> -1
assert verify_chern_number_integrality(monopole, oriented_faces)

# Verify Whitney sum additivity ch(E_1 (+) E_2) = ch(E_1) + ch(E_2)
flat_bundle = trivial_bundle(2, edges)
additivity = verify_chern_character_additivity(monopole, flat_bundle, oriented_faces)
assert all(additivity.values())

# Virtual bundle [monopole] - [trivial_2] in K^0(S^2) has virtual rank 0 but non-trivial ch_1
k_ring = TopologicalKTheoryRing(edges)
virtual_class = (monopole, flat_bundle)
assert k_ring.virtual_rank(virtual_class) == 0
v_ch1 = k_ring.virtual_chern_1(virtual_class, oriented_faces)
assert math.isclose(sum(v_ch1.values()), -1.0, abs_tol=1e-9)
```

---

## Related Guides

* [Cellular Sheaves & Discrete Fiber Bundles](sheaf.md)
* [Simplicial Cohomology & Cup Product Ring](cohomology.md)
* [Discrete Exterior Calculus (DEC) & Hodge Decomposition](dec.md)
* [Additive Inverses: Rings, Fields & Ideals](../algebra/rings_and_fields.md)
