---
title: Categories, Type Theory, Coeffects & Path Groupoids
description: Guide to Category, Functor, MatrixCategory Mat(S), LawvereMetricCategory, Kleisli monads, Cartesian Closed Categories (CCC), Semiring Coeffects, and Simplicial Path Groupoids.
---

# Categories, Type Theory, Coeffects & Path Groupoids (`algebrax.category`, `algebrax.topology`)

In **AlgebraX**, category theory is not an abstract layer of object-oriented wrappers—it is the **structural meta-language of sparse matrix computation, type theory, and homotopy**. Following **Stephen Dolan (2013)** (*Fun with Semirings*), **F. William Lawvere (1973)** (*Metric spaces, generalized logic, and closed categories*), and the **Curry–Howard–Lambek correspondence**, AlgebraX unifies enriched matrix categories, Cartesian Closed Categories, semiring-graded coeffects, and simplicial path groupoids.

---

## 1. The Matrix Category $\mathbf{Mat}(\mathcal{S})$

For any semiring $\mathcal{S}$, `MatrixCategory(semiring)` realizes the mathematical category $\mathbf{Mat}(\mathcal{S})$:

- **Objects**: Finite index sets (`frozenset[K]`).
- **Morphisms**: Unboxed sparse dictionary matrices `SparseMatrix[K, V]` (`dict[K, dict[K, V]]`).
- **Identity ($\mathrm{id}_A$)**: Diagonal unit matrix $\{k: \{k: \mathbf{1}_{\mathcal{S}}\} \mid k \in A\}$.
- **Composition ($\mathrm{compose}(f, g)$)**: Semiring matrix multiplication $\mathrm{dot}(f, g, \mathrm{semiring}=\mathcal{S})$.

```python
import algebrax as ax
from fractions import Fraction

# Construct Mat(Q) over exact rational numbers
cat_q = ax.category.MatrixCategory(ax.semiring.StandardSemiring(Fraction))

obj = frozenset({0, 1})
f = {0: {0: Fraction(1, 2), 1: Fraction(2)}, 1: {1: Fraction(3)}}
g = {0: {1: Fraction(4)}, 1: {0: Fraction(-1), 1: Fraction(1)}}

# Identity and categorical composition
id_01 = cat_q.id(obj)
fg = cat_q.compose(f, g)

# Verify left identity, right identity, and associativity
laws = ax.verification.verify_category_laws(cat_q, [obj], [f, g, id_01])
assert all(laws.values())
```

---

## 2. Categorical Duality (`OppositeCategory`) & `TransposeFunctor`

Every category $\mathcal{C}$ has a dual **Opposite Category** $\mathcal{C}^{\mathrm{op}}$ obtained by reversing the direction of all morphisms:

$$\mathrm{compose}_{\mathcal{C}^{\mathrm{op}}}(f, g) = \mathrm{compose}_{\mathcal{C}}(g, f)$$

For any commutative semiring $\mathcal{S}$, matrix transposition defines a canonical **Functor** `TransposeFunctor` providing an isomorphism $\mathbf{Mat}(\mathcal{S})^{\mathrm{op}} \xrightarrow{\sim} \mathbf{Mat}(\mathcal{S})$:

$$(f \cdot g)^T = g^T \cdot f^T, \qquad (\mathbf{I}_A)^T = \mathbf{I}_A$$

```python
import algebrax as ax

cat = ax.category.MatrixCategory(ax.semiring.StandardSemiring(float))
op_cat = cat.opposite()
transpose_F = ax.category.TransposeFunctor()

obj = frozenset({0, 1})
m1 = {0: {0: 1.0, 1: 2.0}, 1: {1: 3.0}}
m2 = {0: {1: -1.0}, 1: {0: 2.0, 1: 4.0}}
m3 = {0: {0: 2.0}, 1: {1: 5.0}}

assert all(ax.verification.verify_functor_laws(transpose_F, op_cat, cat, [obj], [m1, m2, m3]).values())
```

Similarly, any semiring homomorphism $\phi: \mathcal{R} \to \mathcal{S}$ induces an entrywise **Change-of-Base Functor** `SemiringChangeOfBaseFunctor` from $\mathbf{Mat}(\mathcal{R}) \to \mathbf{Mat}(\mathcal{S})$.

---

## 3. Lawvere Metric Spaces (`LawvereMetricCategory`)

In 1973, F. William Lawvere proved that a **generalized metric space** $(X, d)$ is strictly a category enriched over the **Tropical Cost Semiring** $\mathcal{V} = \langle [0, \infty], \min, +, \infty, 0 \rangle$:

| Metric Space Concept | Enriched Categorical Meaning in $\mathcal{V}$ |
| :--- | :--- |
| Point $x \in X$ | Object $x \in \mathrm{Obj}(\mathcal{C})$ |
| Directed distance $d(x, y) \in [0, \infty]$ | Enriched Hom-object $\mathcal{C}(x, y)$ |
| Zero self-distance $0 \ge d(x, x)$ | Identity morphism $\mathrm{id}_x : 0 \to \mathcal{C}(x, x)$ |
| Triangle inequality $d(x, y) + d(y, z) \ge d(x, z)$ | Enriched composition $\circ : \mathcal{C}(x, y) \otimes \mathcal{C}(y, z) \to \mathcal{C}(x, z)$ |

Computing all-pairs shortest paths via `metric_closure()` is the Kleene star closure sending any raw weighted graph to the free **Lawvere Metric Category** satisfying the triangle inequality:

```python
import algebrax as ax

# Raw directed edge costs where A -> C (10.0) violates the triangle inequality via B (2.0 + 3.0 = 5.0)
raw_edges = {
    'A': {'B': 2.0, 'C': 10.0},
    'B': {'C': 3.0},
}

space = ax.category.LawvereMetricCategory(raw_edges)
print('Raw triangle inequality satisfied?', space.satisfies_triangle_inequality())
# Output: False

# Compute the Kleene star metric closure over TropicalSemiring
closed_distances = space.metric_closure()
metric_space = ax.category.LawvereMetricCategory(closed_distances)
print('Shortest path A -> C:', metric_space.distance('A', 'C'))
# Output: 5.0
print('Closed triangle inequality satisfied?', metric_space.satisfies_triangle_inequality())
# Output: True
```

---

## 4. Kleisli Monadic Composition & Left Kan Extensions

Effectful monadic morphisms $f: A \to T(B)$ and $g: B \to T(C)$ compose via **Kleisli Composition** (`kleisli_compose`):

$$(g \circ_T f)(A, C) = \bigoplus_{B} f(A, B) \otimes g(B, C)$$

By swapping the underlying semiring, `kleisli_compose` and `kan_extension_left` compute different monadic effects:
- **`ViterbiSemiring`**: Most probable state transition chains ($f: A \to \mathrm{Prob}(B)$).
- **`TropicalSemiring`**: Lawvere minimum-cost path composition ($f: A \to \mathrm{Cost}(B)$).
- **`BooleanSemiring`**: Nondeterministic reachability ($f: A \to \mathcal{P}(B)$).

```python
import algebrax as ax

f_prob = {'A': {'B': 0.8, 'C': 0.2}}
g_prob = {'B': {'D': 0.9}, 'C': {'D': 0.5}}

# 1. Probabilistic Viterbi Monad
prob_res = ax.category.kleisli_compose(f_prob, g_prob, semiring=ax.semiring.ViterbiSemiring())
print('Probabilistic Max Path A -> D:', prob_res['A']['D'])
# Output: 0.72
```

---

## 5. Cartesian Closed Categories & Curry–Howard–Lambek (`FiniteSetCCC`)

The **Curry–Howard–Lambek correspondence** establishes that intuitionistic propositional logic, the simply typed lambda calculus, and **Cartesian Closed Categories (CCCs)** are three perspectives on the exact same structure:

| Logic | Type Theory ($\lambda$-Calculus) | Cartesian Closed Category (`CartesianClosedCategory`) |
| :--- | :--- | :--- |
| True ($\top$) | Unit type `()` | Terminal object $\mathbf{1}$ (`terminal`) |
| Conjunction ($A \land B$) | Product type $(A, B)$ | Categorical product $A \times B$ (`product`, `proj1`, `proj2`, `pair`) |
| Implication ($B \Rightarrow C$) | Function type $B \to C$ | Exponential object $C^B$ (`exponential`, `eval_mor`) |
| Deduction theorem ($A \land B \vdash C \iff A \vdash B \Rightarrow C$) | Currying $\lambda b.\, f(a, b)$ | Natural bijection $\mathrm{Hom}(A \times B, C) \cong \mathrm{Hom}(A, C^B)$ (`curry`, `uncurry`) |

`FiniteSetCCC` models $\mathbf{FinSet}$ over unboxed `frozenset` objects and `(dom, cod, mapping_dict)` total-function morphisms:

```python
import algebrax as ax

ccc = ax.category.FiniteSetCCC()
A = frozenset({'u', 'v'})
B = frozenset({0, 1})
C = frozenset({False, True})

AB = ccc.product(A, B)
f = (AB, C, {('u', 0): False, ('u', 1): True, ('v', 0): True, ('v', 1): False})

# Curry f : A x B -> C into lambda_f : A -> C^B
curried = ccc.curry(f, A, B)
print('Exponential cardinality |C^B|:', len(ccc.exponential(C, B)))
# Output: 4

# Verify product universal pairing, beta evaluation, and currying bijection
laws = ax.verification.verify_exponential_adjunction(ccc, A, B, C, [f])
assert all(laws.values())
```

---

## 6. Semiring-Graded Coeffects (`CoeffectContext` & `SemiringCoeffectTracker`)

While **monadic effects** (`kleisli_compose`) model what a computation *produces* on its output, **semiring-graded coeffects** (Orchard, Petricek, McBride) model what a computation *demands from its execution context* $\Gamma$. Typing contexts $\Gamma : \mathrm{Var} \to \mathcal{S}$ form a left $\mathcal{S}$-semimodule under `CoeffectContext(semiring)`:

- **Context Addition ($\Gamma_1 + \Gamma_2$)**: Pointwise $\oplus$ across parallel or sequential sub-expressions.
- **Modal Context Scaling ($r \cdot \Gamma$)**: Pointwise left $\otimes$ when an expression is executed under a modality of grade $r$ (e.g., inside a loop running $r$ times).

| Semiring $\mathcal{S}$ | Coeffect Meaning | $\Gamma_1 + \Gamma_2$ ($\oplus$) | $r \cdot \Gamma$ ($\otimes$) |
| :--- | :--- | :--- | :--- |
| `StandardSemiring(int)` | Exact variable usage count (Linear / Bounded Types) | Sum of usages $u_1 + u_2$ | Loop amplification $r \times u$ |
| `BooleanSemiring()` | Liveness & dead-code analysis | Used in either branch ($u_1 \lor u_2$) | Guarded reachability ($r \land u$) |
| `TropicalSemiring()` | Minimum latency / privacy sensitivity budget | Fastest path $\min(d_1, d_2)$ | Accumulated delay $r + d$ |

```python
import algebrax as ax

# Track exact variable reuse counts over (N, +, *, 0, 1)
ctx_alg = ax.category.CoeffectContext(ax.semiring.StandardSemiring(int))
body_ctx = ctx_alg.add(ctx_alg.singleton('x', 1), ctx_alg.singleton('y', 2))

# Execute body inside a 4-iteration loop: 4 * (1*x + 2*y) = 4*x + 8*y
loop_ctx = ctx_alg.scale(4, body_ctx)
print('Loop variable demands:', loop_ctx)
# Output: {'x': 4, 'y': 8}
```

---

## 7. Simplicial Homotopy Path Groupoids $\Pi_1(K)$ (`SimplicialPathGroupoid`)

In **Homotopy Type Theory (HoTT)** and algebraic topology, a space (or type) is represented by its **fundamental path groupoid** $\Pi_1(K)$:

- **Objects (Terms / Points)**: Vertices $v \in K_0$.
- **Morphisms (Identity Proofs / Paths)**: Edge walks $p = (v_0, v_1, \dots, v_n)$ in the 1-skeleton $K_1$.
- **Composition & Inversion**: Path concatenation $p_1 \cdot p_2$ and path reversal $p^{-1} = (v_n, \dots, v_0)$.
- **2-Simplex Homotopy (Higher Proofs)**: Two paths $p, q : u \to w$ are homotopic ($p \sim q$) if one can be deformed into the other by canceling backtracking spurs $(u, v, u) \sim (u,)$ and sliding across filled 2-simplices $(u, v, w) \sim (u, w)$ for $\{u, v, w\} \in K_2$.

```python
import algebrax as ax

# 1. Filled triangle Delta^2: (0, 1, 2) is homotopic to the direct edge (0, 2)
filled = ax.topology.SimplicialComplex([(0, 1, 2)])
pi1_filled = ax.topology.SimplicialPathGroupoid.from_simplicial_complex(filled)
print('Contractible across filled 2-simplex?', pi1_filled.are_homotopic((0, 1, 2), (0, 2)))
# Output: True

# 2. Hollow triangle boundary S^1 (missing 2-simplex): topological hole obstructs homotopy!
hollow = ax.topology.SimplicialComplex([(0, 1), (1, 2), (0, 2)])
pi1_hollow = ax.topology.SimplicialPathGroupoid.from_simplicial_complex(hollow)
print('Contractible across hollow 1-cycle?', pi1_hollow.are_homotopic((0, 1, 2), (0, 2)))
# Output: False
```

