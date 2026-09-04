---
title: Logic & Language Semirings
description: Boolean, Digital, Łukasiewicz Fuzzy, String, and K-Collapsed semirings in AlgebraX.
---

# Logic & Language Semirings (`algebrax.semiring.logic` & `structures`)

Logic semirings model reachability, non-commutative formal languages, digital filters, and multi-valued fuzzy logic:

---

# Boolean Semiring (Reachability)

The **Boolean Semiring** uses $(\lor, \land)$. It answers "Is there a path?" without counting them.
Matrix multiplication yields the **Transitive Closure** (Reachability).

* **Add**: $\lor$ (OR)
* **Mul**: $\land$ (AND)

<!-- name: test_boolean_semiring -->

```python linenums="1"
import algebrax as ax

# Graph Connectivity
# 0 -> 1
# 1 -> 2
# 3 -> 4 (Disconnected component)
graph = {
    0: {1: True},
    1: {2: True},
    3: {4: True}
}

semiring = ax.semiring.BooleanSemiring()

# Reachability in exactly 2 steps
step2 = ax.matrix.dot(graph, graph, semiring=semiring)
print(f"0 -> 2 reachable in 2 steps? {step2.get(0, {}).get(2, False)}")
# output: True

# Full Transitive Closure (Reachability)
# For a graph with N nodes, closure is (I + A)^N
# Or just sum of powers.
# Let's check if 0 can reach 2 eventually.
# We use ax.matrix.power() which does binary exponentiation.
# For N=5, ax.matrix.power 5 covers all paths <= 5 length.

# Add self-loops (Identity) to allow "staying" at a node
# This makes A^k include all paths of length <= k
n_nodes = 5
for i in range(n_nodes):
    if i not in graph: graph[i] = {}
    graph[i][i] = True

closure = ax.matrix.power(graph, n_nodes, semiring=semiring)

print(f"0 -> 2 reachable? {closure.get(0, {}).get(2, False)}")
print(f"0 -> 4 reachable? {closure.get(0, {}).get(4, False)}")
# output: True
# output: False
```

---

# Digital Semiring (Post-Quantum Cryptography)

The **Digital Semiring** uses the sum of decimal digits to determine order.
It is used in cryptographic protocols (Huang et al., 2024).

* **Add:** Larger digit sum wins.
* **Mul:** Smaller digit sum wins.

<!-- name: test_digital_semiring -->

```python linenums="1"
import algebrax as ax

S = ax.semiring.DigitalSemiring()

# (123) = 6, (45) = 9
# Add: 9 > 6 -> 45
print(S.add(123, 45))
# output: 45

# Mul: 6 < 9 -> 123
print(S.mul(123, 45))
# output: 123
```

---

# Discrete Logic, Fuzzy & Formal Language Semirings

While classical Boolean algebra models crisp binary reachability $\{0, 1\}$, many computational domains demand
continuous multi-valued reasoning, formal string derivations, or saturated resource bounds.

**AlgebraX** provides three specialized logic and formal language semirings in `algebrax.semiring`:

1. **`LukasiewiczSemiring`**: Continuous fuzzy logic on $[0, 1]$ using Łukasiewicz t-norms for continuous truth-value
   propagation.
2. **`StringSemiring`**: Formal language powerset $\mathcal{P} (\Sigma^*)$ for string concatenation, grammar
   derivations, and regular expressions.
3. **`KCollapsedSemiring`**: Saturated resource counting modulo threshold $k$ for bounded concurrency and semaphore
   capacity.

---

## 1. LukasiewiczSemiring: Continuous Multi-Valued Fuzzy Logic

In multi-valued fuzzy logic (Jan Łukasiewicz, 1920), propositions have truth values in the continuous interval $[0, 1]$:

$$\begin{aligned} a \oplus b &= \max (a, b) \quad \text{ (Disjunction / Union)} \\ a \otimes b &= \max (0, a + b - 1) \quad \text{ (Łukasiewicz t-norm Conjunction)} \\ \mathbf{0} &= 0.0 \quad \text{ (False)} \\ \mathbf{1} &= 1.0 \quad \text{ (True)} \end{aligned}$$

### Algebraic Properties

* **Associative & Commutative**: Both $\oplus$ and $\otimes$ are associative and commutative.
* **Distributivity**: Multiplication distributes over
  addition: $a \otimes (b \oplus c) = (a \otimes b) \oplus (a \otimes c)$.
* **Residuation / Implication**: The residuum corresponding to the t-norm is $a \to b = \min (1, 1 - a + b)$.

```python
import algebrax as ax

luk = ax.semiring.LukasiewiczSemiring()

# Two fuzzy propositions: P(A) = 0.8, P(B) = 0.7
# Conjunction P(A ∧ B) = max(0, 0.8 + 0.7 - 1) = 0.5
conj = luk.mul(0.8, 0.7)
print("Fuzzy Conjunction:", conj)  # 0.5

# Disjunction P(A ∨ B) = max(0.8, 0.7) = 0.8
disj = luk.add(0.8, 0.7)
print("Fuzzy Disjunction:", disj)  # 0.8
```

---

## 2. StringSemiring: Formal Language Powerset $\mathcal{P} (\Sigma^*)$

The **StringSemiring** forms a Kleene algebra over sets of strings from an alphabet $\Sigma$:

$$\begin{aligned} A \oplus B &= A \cup B \quad \text{ (Union of languages)} \\ A \otimes B &= \{u \cdot v \mid u \in A, v \in B\} \quad \text{ (Pairwise string concatenation)} \\ \mathbf{0} &= \emptyset \quad \text{ (Empty language)} \\ \mathbf{1} &= \{\epsilon\} \quad \text{ (Empty string singleton)} \end{aligned}$$

### Applications: Automata Path Yields

Multiplying adjacency matrices over `StringSemiring` computes all generated words along transition paths:

```python
import algebrax as ax

str_sem = ax.semiring.StringSemiring()

# Transition from Node 0 to Node 1 on {"cat", "dog"}
# Transition from Node 1 to Node 2 on {"s", "es"}
trans1 = {"cat", "dog"}
trans2 = {"s", "es"}

# Concatenation of languages
result = str_sem.mul(trans1, trans2)
print("Generated Words:", sorted(result))
# ["cats", "cates", "dogs", "doges"]
```

---

## 3. KCollapsedSemiring: Saturated Threshold Counters

In network buffer allocation, operating system semaphores, and database join size bounds, counts beyond a threshold $k$
saturate to $k$:

$$\begin{aligned} a \oplus b &= \min (k, a + b) \\ a \otimes b &= \min (k, a \cdot b) \\ \mathbf{0} &= 0 \\ \mathbf{1} &= 1 \end{aligned}$$

```python
import algebrax as ax

# Capped resource threshold at k = 10
k_sem = ax.semiring.KCollapsedSemiring(k=10)

# Saturated Addition
print("5 + 7 mod k=10:", k_sem.add(5, 7))  # 10

# Saturated Multiplication
print("3 * 4 mod k=10:", k_sem.mul(3, 4))  # 10
```

---

## Related Recipes & Applications

* [Post-Quantum Cryptography](../../recipes.md) — Non-commutative matrix key exchange over `DigitalSemiring`.
* [Natural Language Parsing](../../recipes.md) — CYK parse trees and transitive closure over `BooleanSemiring`.
* [Distributed Vector Clocks](../../recipes.md) — Causal message reachability over `BooleanSemiring`.
