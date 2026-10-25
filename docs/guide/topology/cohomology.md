---
title: Cohomology & Ring Products
description: Alternating cochains, coboundary operators, cohomology ranks, and Alexander-Whitney cup and cap products.
---

# Cohomology & Ring Products (`algebrax.topology.cohomology`)

While homology groups $H_k(K; R)$ are purely additive modules, dualizing chains into **cochains** $C^k(K; \mathcal{S}) = \operatorname{Hom}(C_k(K), \mathcal{S})$ equips topology with a **graded associative ring structure** via the Alexander–Whitney **cup product** ($\smile$). This graded ring $H^*(K; \mathcal{S})$ distinguishes topological spaces that share identical Betti numbers (such as the torus $T^2$ vs. the wedge sum $S^2 \vee S^1 \vee S^1$).

---

## Alternating Cochains & Discrete Forms (`Cochain`)

The **`Cochain[K, V]`** carrier in `algebrax.topology.cohomology` (aliased as `DiscreteForm`) represents an alternating discrete differential $k$-form $\omega \in C^k(K; \mathcal{S})$ satisfying permutation parity antisymmetry:

$$\omega(v_{\pi(0)}, \dots, v_{\pi(k)}) = \operatorname{sgn}(\pi)\,\omega(v_0, \dots, v_k)$$

`Cochain` implements `Mapping[tuple[K, ...], V]`, making it directly compatible with `SparseVector` operators (`mat_vec`, `inner`, `vec_axpy`) while automatically canonicalizing simplex orientations ($v_0 < v_1 < \dots < v_k$) and annihilating degenerate simplices with repeated vertices:

```python
from algebrax.matrix import mat_vec
from algebrax.topology import Cochain, SimplicialComplex, coboundary, cohomology_rank

# 1-cochain initialized with arbitrary edge orientation
omega = Cochain({(1, 0): 5.0, (1, 2): -3.0})
print(omega[(0, 1)])  # -> -5.0 (canonical orientation)
print(omega[(1, 0)])  # -> +5.0 (reversed orientation flips sign)
print(omega.get((0, 0)))  # -> 0.0 (degenerate simplex vanishes)

# Coboundary operator d^0 = D_1^T : C^0 -> C^1
sc = SimplicialComplex([(0, 1, 2)])
f0 = Cochain.from_nodes({0: 1.0, 1: 4.0, 2: -2.0})
df = Cochain(mat_vec(coboundary(sc, 0), f0), degree=1)
print(df[(0, 1)], df[(1, 2)])  # -> 3.0, -6.0
print('dim H^1:', cohomology_rank(sc, 1))  # -> 0
```

---

## Alexander–Whitney Cup Product (`cup_product` & `^`)

Given a $p$-cochain $\alpha \in C^p(K; \mathcal{S})$ and a $q$-cochain $\beta \in C^q(K; \mathcal{S})$, the **Alexander–Whitney cup product** $\alpha \smile \beta \in C^{p+q}(K; \mathcal{S})$ evaluates on a canonically ordered $(p+q)$-simplex $(v_0 < v_1 < \dots < v_{p+q})$ by joining front $p$-faces and back $q$-faces at the shared pivot vertex $v_p$:

$$(\alpha \smile \beta)(v_0, \dots, v_{p+q}) = \alpha(v_0, \dots, v_p) \otimes_{\mathcal{S}} \beta(v_p, \dots, v_{p+q})$$

### Algebraic Laws

1. **Associativity**:
   $$(\alpha \smile \beta) \smile \gamma = \alpha \smile (\beta \smile \gamma)$$
2. **Graded Leibniz Rule (Differential Graded Algebra)**:
   $$d^{p+q}(\alpha \smile \beta) = (d^p \alpha) \smile \beta + (-1)^p \, \alpha \smile (d^q \beta)$$
3. **Semiring Polymorphism**: Because canonical simplices $(v_0 < \dots < v_p)$ and $(v_p < \dots < v_{p+q})$ concatenate directly into a strictly increasing $(p+q)$-simplex $(v_0 < \dots < v_{p+q})$ with parity $+1$, `cup_product` requires only semiring addition $\oplus_{\mathcal{S}}$ and multiplication $\otimes_{\mathcal{S}}$ — working seamlessly over `StandardSemiring`, exact `Fraction`, `TropicalSemiring`, or `BooleanSemiring`.

```python
import algebrax as ax

tet = ax.topology.SimplicialComplex([(0, 1, 2, 3)])
alpha = ax.topology.Cochain({(0, 1): 2.0, (1, 2): 3.0})
beta = ax.topology.Cochain({(1, 2): 4.0, (2, 3): -1.0})

# Compute cup product via ^ operator, .cup(), or cup_product()
two_form = alpha ^ beta
print(two_form)
# Cochain({(0, 1, 2): 8.0, (1, 2, 3): -3.0}, degree=2)

# Restrict support to simplices present in a SimplicialComplex or use a custom Semiring
tropical_cup = ax.topology.cup_product(
    alpha,
    beta,
    complex=tet,
    semiring=ax.semiring.TropicalSemiring(),
)
print(tropical_cup)
# Cochain({(0, 1, 2): 6.0, (1, 2, 3): 2.0}, degree=2)
```

---

## Alexander–Whitney Cap Product (`cap_product`)

The **cap product** $\frown: C_n(K; \mathcal{S}) \times C^p(K; \mathcal{S}) \to C_{n-p}(K; \mathcal{S})$ contracts an $n$-chain with a $p$-cochain ($n \ge p$) by evaluating the cochain on the front $p$-face $(v_0, \dots, v_p)$ and weighting the back $(n-p)$-face $(v_p, \dots, v_n)$:

$$\sigma \frown \phi = \phi(v_0, \dots, v_p) \otimes_{\mathcal{S}} [v_p, \dots, v_n]$$

It satisfies **Kronecker cup-cap duality** for all $\phi \in C^p$, $\psi \in C^q$, and $c \in C_{p+q}$:

$$\langle \psi, c \frown \phi \rangle = \langle \phi \smile \psi, c \rangle$$

```python
from algebrax.topology import Cochain, cap_product

alpha = Cochain({(0, 1): 2.0, (1, 2): 3.0})
chain_2 = {(0, 1, 2): 5.0}

# Contract 2-chain with 1-cochain -> 1-chain
chain_1 = cap_product(chain_2, alpha)
print(chain_1)
# {(1, 2): 10.0}
```

---

## Related Sections

* [Homology & Chain Complexes](homology.md) — Boundary operators $\partial_k$ and static Betti numbers.
* [Persistent Homology & Barcodes](persistence.md) — Dual persistent cohomology (`persistent_cohomology`) and representative cocycle extraction.
* [Discrete Exterior Calculus & Hodge Theory](dec.md) — Metric Hodge star $\star$, codifferential $\delta$, and Helmholtz–Hodge decomposition.
