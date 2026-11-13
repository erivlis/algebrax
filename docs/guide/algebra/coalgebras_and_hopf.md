---
title: Coalgebras, Bialgebras & Hopf Algebras
description: Categorical arrow-reversal duality, comultiplication, counits, quantum antipodes, divided power moments, and Alexander-Whitney simplicial coalgebras.
---

# Coalgebras, Bialgebras & Hopf Algebras (`algebrax.algebra`, `algebrax.topology`)

## 1. The Practical Problem: Decomposing Elements & Quantum Symmetries

Classical algebra focuses on *combining* elements: two vectors or numbers multiply into one via $\mu: A \otimes A \to A$. However, many physical and mathematical domains fundamentally operate by *splitting* or *decomposing* states:
- **Moment & Dispersion Analysis**: A total polynomial or statistical moment splits binomially across partitions: $\Delta(x^{[n]}) = \sum x^{[k]} \otimes x^{[n-k]}$.
- **Topological Cohomology**: The Alexander-Whitney diagonal approximation $\Delta(\sigma) = \sum \sigma[:i] \otimes \sigma[i-1:]$ on simplicial chains $C_*(K)$ is the fundamental engine whose linear dual generates the cohomology cup product $\smile$.
- **Quantum Groups & Symmetries**: Symmetries acting on composite tensor product states $V \otimes W$ require an algebraic comultiplication $\Delta(g) = g \otimes g$ and a "quantum inverse" or **antipode** $S: H \to H$ satisfying:
$$\mu \circ (S \otimes \mathrm{id}) \circ \Delta = \eta \circ \epsilon = \mu \circ (\mathrm{id} \otimes S) \circ \Delta$$

In AlgebraX, this arrow-reversal duality is formalized by the **`Coalgebra`**, **`Bialgebra`**, and **`HopfAlgebra`** protocols.

---

## 2. The 30-Second Executable Snippet

```python
from algebrax.algebra import GroupHopfAlgebra, HopfAlgebra, Group
from algebrax.topology import SimplicialChainCoalgebra, cup_product

# 1. Create a Group Hopf Algebra on cyclic group Z/4Z
class Z4(Group[int]):
    @property
    def zero(self) -> int: return 0
    @property
    def one(self) -> int: return 0
    def mul(self, a: int, b: int) -> int: return (a + b) % 4
    def inv(self, a: int) -> int: return (-a) % 4
    def div(self, a: int, b: int) -> int: return (a - b) % 4

gh = GroupHopfAlgebra(Z4())
assert isinstance(gh, HopfAlgebra)

# 2. Quantum operations: Coproduct, Counit, Antipode
elem = {1: 2.0, 3: 5.0}
assert gh.coproduct(elem) == {(1, 1): 2.0, (3, 3): 5.0}  # Group-like coproduct Delta(g) = g (x) g
assert gh.counit(elem) == 7.0                            # Counit epsilon(sum c_g g) = sum c_g
assert gh.antipode(elem) == {3: 2.0, 1: 5.0}             # Quantum inverse S(g) = g^(-1)

# 3. Alexander-Whitney simplicial coproduct & cohomology cup product duality
scc = SimplicialChainCoalgebra()
sigma = (0, 1, 2)  # 2-simplex
delta_sigma = scc.coproduct({sigma: 1.0})

alpha, beta = {(0, 1): 3.0}, {(1, 2): 4.0}
eval_cup = cup_product(alpha, beta).get(sigma, 0.0)
eval_dual = sum(c * alpha.get(f, 0.0) * beta.get(b, 0.0) for (f, b), c in delta_sigma.items())
assert eval_cup == eval_dual == 12.0
```

---

## 3. Protocol Architecture & Mixin Composition

Following the **Law of Flat Protocol Composition** (EP-0194 / EP-0005), coalgebras and Hopf algebras are assembled with zero diamond inheritance from atomic operational mixins:

| Protocol | Mathematical Signature | Composed Atomic Mixins | Key Axioms |
|:---|:---|:---|:---|
| **`Coalgebra[R, C]`** | $\langle R, C, \cdot_s, \mathbf{0}, +, -, \Delta, \epsilon \rangle$ | `HasScale`, `HasZero`, `HasAdd`, `HasNeg`, `HasCoproduct`, `HasCounit` | Coassociativity $(\Delta \otimes \mathrm{id})\Delta = (\mathrm{id} \otimes \Delta)\Delta$, Counitality $(\epsilon \otimes \mathrm{id})\Delta = \mathrm{id}$ |
| **`Bialgebra[R, C]`** | $\langle R, C, \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot, \Delta, \epsilon \rangle$ | `HasScale`, `HasZero`, `HasAdd`, `HasNeg`, `HasOne`, `HasMul`, `HasCoproduct`, `HasCounit` | Algebra + Coalgebra, compatibility: $\Delta(ab) = \Delta(a)\Delta(b)$, $\epsilon(ab) = \epsilon(a)\epsilon(b)$ |
| **`HopfAlgebra[R, C]`** | $\langle R, C, \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot, \Delta, \epsilon, S \rangle$ | All Bialgebra mixins + `HasAntipode` | Antipode axiom: $\mu \circ (S \otimes \mathrm{id}) \circ \Delta = \eta \circ \epsilon$ |

### Unboxed Sparse Carrier Invariant
All tensor products $C \otimes C$ are represented using AlgebraX's native unboxed sparse tuple keys `dict[tuple[K, K], float]`, ensuring zero wrapper overhead and maximum computational efficiency.

---

## 4. Built-in Coalgebraic Models

### Group Hopf Algebra (`GroupHopfAlgebra`)
Constructed from any group $G$, $K[G]$ formalizes group linear combinations:
- **Multiplication**: Group convolution $\sum_{u \cdot v = w} a_u b_v$.
- **Coproduct**: $\Delta(g) = g \otimes g$ (every group element is group-like).
- **Counit**: $\epsilon(\sum c_g g) = \sum c_g$.
- **Antipode**: $S(g) = g^{-1}$.

### Divided Power Coalgebra (`DividedPowerCoalgebra`)
Governs the polynomial sequence $x^{[n]}$ where $\Delta(x^{[n]}) = \sum_{k=0}^n x^{[k]} \otimes x^{[n-k]}$ and $\epsilon(x^{[n]}) = \delta_{n, 0}$, fundamental in characteristic-$p$ algebraic geometry, formal groups, and binomial moment convolutions.

### Alexander-Whitney Coalgebra (`SimplicialChainCoalgebra`)
Acts on oriented simplicial chains $C_*(K)$. The Alexander-Whitney diagonal approximation:
$$\Delta([v_0, \dots, v_n]) = \sum_{i=1}^{n+1} [v_0, \dots, v_{i-1}] \otimes [v_{i-1}, \dots, v_n]$$
satisfies coassociativity and counitality, providing the foundation for the simplicial cohomology ring structure $H^*(K; R)$.

---

## 5. Automated Verification

AlgebraX provides executable axiom verifiers in `algebrax.verification`:
```python
from algebrax.verification import (
    verify_coassociativity,
    verify_counitality,
    verify_antipode_axiom,
    verify_coalgebra_laws,
    verify_bialgebra_laws,
    verify_hopf_algebra_laws,
)
```
Each verifier evaluates arbitrary sample subsets and returns a dictionary of boolean law satisfaction results, verifying strict adherence to coassociativity, counitality, and the Hopf antipode identity.
