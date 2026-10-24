# Metamorphic Testing: A New Approach for Generating Next Test Cases

| Field | Value |
|:---|:---|
| **Citation** | T. Y. Chen, S. C. Cheung, S. M. Yiu. *Metamorphic Testing: A New Approach for Generating Next Test Cases*. Technical Report HKUST-CS98-01, Department of Computer Science, Hong Kong University of Science and Technology, 1998. |
| **Archived Identifier** | arXiv:2002.12543 [cs.SE] |
| **Direct PDF** | [https://arxiv.org/pdf/2002.12543.pdf](https://arxiv.org/pdf/2002.12543.pdf) |
| **Local PDF Mirror** | [`chen_1998_metamorphic_testing.pdf`](./chen_1998_metamorphic_testing.pdf) (581 KB) |
| **Keywords** | Metamorphic Testing, Test Oracle Problem, Metamorphic Relations, Software Verification |

---

## Abstract & Summary

Testing programs where an analytical test oracle is unavailable or computationally prohibitive is known as the **test oracle problem**. This seminal 1998 paper proposes **Metamorphic Testing (MT)** as an innovative paradigm to address the oracle problem. 

Instead of verifying whether an individual program output $f(x)$ matches a known expected output $y$, metamorphic testing verifies whether multiple program executions satisfy fundamental mathematical relationships termed **Metamorphic Relations (MRs)**:

$$x_1 \xrightarrow{T} x_2 \implies f(x_1) \mathrel{R} f(x_2)$$

If the relation $R$ fails between outputs $f(x_1)$ and $f(x_2)$, a defect in the implementation is definitively detected, even when neither $f(x_1)$ nor $f(x_2)$ was known in advance.

---

## Core Theoretical Formulations

### 1. Metamorphic Relations (MRs)
Let $P$ be an implementation of a target mathematical function $f$. An input transformation $T$ maps input $x$ to transformed input $x' = T(x)$. A metamorphic relation $R$ is a necessary condition:

$$\forall x, \quad f(T(x)) = g(f(x), x)$$

If $P(T(x)) \neq g(P(x), x)$ (up to numerical tolerance), the implementation $P$ is guaranteed to contain a defect.

### 2. Applications in Algebra and Geometry
The paper provides examples from numerical analysis and discrete algorithms:
- **Trigonometric Symmetries:** $\sin(\pi - x) = \sin(x)$
- **Shortest Path Monotonicity:** Increasing edge weights on edges outside the shortest path cannot decrease the total distance.
- **Matrix Invariants:** Transpose duality, scalar homogeneity, and determinant multilinearity.

---

## Direct Application to AlgebraX Verification Suite

In **AlgebraX** (`EP-0180` and `tests/verifications/test_metamorphic_invariants.py`), metamorphic testing provides automated verification for complex semirings and discrete operators where canonical reference engines do not exist:

1. **Transpose Dual Invariant:**
   $$\text{dot}(A, B)^T \equiv \text{dot}(B^T, A^T) \quad (\forall \text{ commutative semirings})$$
2. **Scalar Homogeneity:**
   $$c \otimes \text{dot}(A, B) \equiv \text{dot}(c \otimes A, B)$$
3. **Graph Automorphism Conjugacy:**
   $$L(P A P^T) \equiv P L(A) P^T \quad (\forall \text{ permutation matrices } P)$$
4. **Hodge Star Involution:**
   $$\star \star \omega \equiv (-1)^{k(n-k)} s \omega$$
5. **Chain Nilpotency:**
   $$\partial_k(\partial_{k+1}(c)) \equiv \mathbf{0} \quad \text{and} \quad d_{k+1}(d_k(\omega)) \equiv \mathbf{0}$$
