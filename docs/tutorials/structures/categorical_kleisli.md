---
title: Categorical Morphisms & Kleisli Composition
description: Tutorial on kleisli_compose for monadic composition over semirings.
---

# Categorical Morphisms & Kleisli Composition

The `algebrax.category` module models categories where hom-sets $\text{Hom}(A, B)$ are represented as sparse matrix mappings $M[A][B]$.

Effectful monadic morphisms $f: A \to T(B)$ and $g: B \to T(C)$ compose via **Kleisli Composition**:

$$(g \circ_T f)(A, C) = \bigoplus_{B} f(A, B) \otimes g(B, C)$$

---

## Semiring Monad Enrichment

By swapping the underlying semiring, the exact same `kleisli_compose()` function computes different monadic effects:
- **ViterbiSemiring**: Probabilistic transition chains ($f: A \to \text{Prob}(B)$).
- **TropicalSemiring**: Lawvere metric space minimum cost path composition ($f: A \to \text{Cost}(B)$).
- **BooleanSemiring**: Poset graph reachability ($f: A \to \text{Bool}(B)$).

---

## Python Example: Kleisli Monadic Composition

```python
from algebrax.category import kleisli_compose
from algebrax.semiring import BooleanSemiring, TropicalSemiring, ViterbiSemiring

# Define Morphisms A -> B and B -> C
f_prob = {'A': {'B': 0.8, 'C': 0.2}}
g_prob = {'B': {'D': 0.9}, 'C': {'D': 0.5}}

# 1. Probabilistic Viterbi Monad
prob_res = kleisli_compose(f_prob, g_prob, semiring=ViterbiSemiring())
print("Probabilistic Max Path A -> D:", prob_res['A']['D'])
# Output: 0.72

# 2. Lawvere Metric Cost Monad
cost_res = kleisli_compose({'A': {'B': 3.0}}, {'B': {'D': 2.0}}, semiring=TropicalSemiring())
print("Min Shortest Path Cost A -> D:", cost_res['A']['D'])
# Output: 5.0

# 3. Boolean Reachability Monad
bool_res = kleisli_compose({'A': {'B': True}}, {'B': {'D': True}}, semiring=BooleanSemiring())
print("Boolean Reachability A -> D:", bool_res['A']['D'])
# Output: True
```
