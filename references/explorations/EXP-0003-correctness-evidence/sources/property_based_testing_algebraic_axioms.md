# Property-Based Axiomatic Testing for Algebraic Structures

## Overview

In computer algebra and pure mathematics software, traditional unit tests with fixed example inputs (e.g., $2 + 2 = 4$) only exercise isolated execution paths. **Property-Based Testing (PBT)** generates thousands of randomized, edge-case-heavy mathematical inputs to rigorously verify that fundamental algebraic laws hold universally across the entire carrier set of a mathematical structure.

For **AlgebraX**, where operations are parameterized by abstract algebraic structures (Semirings, Groups, Monoids, Lattices, Clifford Algebras, Galois Fields, Sheaves), property-based testing serves as an automated, continuous axiomatic proof engine within Pytest using **Hypothesis**.

---

## 1. Algebraic Axioms & Property Specifications

Every algebraic primitive in `algebrax` must satisfy formal algebraic axioms. Below is the mapping from mathematical laws to programmatically testable properties:

### 1.1 Semiring Axioms $(S, \oplus, \otimes, \bar{0}, \bar{1})$

1. **Additive Associativity**:
   $$\forall a, b, c \in S: (a \oplus b) \oplus c = a \oplus (b \oplus c)$$
2. **Additive Commutativity**:
   $$\forall a, b \in S: a \oplus b = b \oplus a$$
3. **Additive Identity ($\bar{0}$)**:
   $$\forall a \in S: a \oplus \bar{0} = a = \bar{0} \oplus a$$
4. **Multiplicative Associativity**:
   $$\forall a, b, c \in S: (a \otimes b) \otimes c = a \otimes (b \otimes c)$$
5. **Multiplicative Identity ($\bar{1}$)**:
   $$\forall a \in S: a \otimes \bar{1} = a = \bar{1} \otimes a$$
6. **Left and Right Distributivity**:
   $$\forall a, b, c \in S: a \otimes (b \oplus c) = (a \otimes b) \oplus (a \otimes c)$$
   $$\forall a, b, c \in S: (a \oplus b) \otimes c = (a \otimes c) \oplus (b \otimes c)$$
7. **Annihilation by Zero ($\bar{0}$)**:
   $$\forall a \in S: a \otimes \bar{0} = \bar{0} = \bar{0} \otimes a$$

---

### 1.2 Bounded Lattice Axioms $(L, \wedge, \vee, \bot, \top)$

1. **Associativity**: $(a \wedge b) \wedge c = a \wedge (b \wedge c)$ and $(a \vee b) \vee c = a \vee (b \vee c)$
2. **Commutativity**: $a \wedge b = b \wedge a$ and $a \vee b = b \vee a$
3. **Idempotence**: $a \wedge a = a$ and $a \vee a = a$
4. **Absorption Laws**: $a \wedge (a \vee b) = a$ and $a \vee (a \wedge b) = a$
5. **Bounds**: $a \wedge \bot = \bot$, $a \vee \top = \top$

---

### 1.3 Matrix & Tensor Algebraic Laws

1. **Matrix Multiplication Associativity**:
   $$(A \otimes_{sr} B) \otimes_{sr} C = A \otimes_{sr} (B \otimes_{sr} C)$$
2. **Distributivity over Sparse Addition**:
   $$A \otimes_{sr} (B \oplus_{sr} C) = (A \otimes_{sr} B) \oplus_{sr} (A \otimes_{sr} C)$$
3. **Transpose Anti-Automorphism**:
   $$(A \otimes_{sr} B)^T = B^T \otimes_{sr^{op}} A^T$$

---

## 2. Hypothesis Strategies for Sparse Dictionary Structures

Testing sparse nested dictionary structures (`Dict[K, Dict[K, V]]`) requires custom Hypothesis data generators (strategies) that produce valid, edge-case sparse matrices, trees, and algebraic elements:

```python
from hypothesis import strategies as st

# Custom strategy for generating arbitrary sparse dictionary matrices
@st.composite
def sparse_matrices(draw, max_size=5, val_strategy=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)):
    rows = draw(st.integers(min_value=1, max_value=max_size))
    cols = draw(st.integers(min_value=1, max_value=max_size))

    matrix = {}
    for r in range(rows):
        row_dict = {}
        for c in range(cols):
            if draw(st.booleans()): # Random sparsity pattern
                row_dict[c] = draw(val_strategy)
        if row_dict:
            matrix[r] = row_dict
    return matrix
```

---

## 3. Automated Axiom Verification Fixtures

Using pytest parameterization, a single property test runner can automatically verify all 35+ semirings registered in `algebrax.semiring`:

```python
import pytest
from hypothesis import given, settings

@pytest.mark.parametrize("semiring", ALL_ALGEBRAX_SEMIRINGS)
@given(a=sparse_elements(), b=sparse_elements(), c=sparse_elements())
def test_semiring_distributivity(semiring, a, b, c):
    # Left Distributivity: a * (b + c) == (a * b) + (a * c)
    lhs = semiring.mul(a, semiring.add(b, c))
    rhs = semiring.add(semiring.mul(a, b), semiring.mul(a, c))
    assert lhs == rhs
```

---

## 4. Handling Floating-Point Numerical Precision in Axiom Verification

When carrier sets use floating-point numbers ($\mathbb{R}$), strict equality `==` fails due to non-associativity of IEEE 754 floating-point addition. The property runner uses:
1. **ULP / Relative Tolerance Distance**:
   $$\text{abs}(x - y) \le \text{rel\_tol} \times \max(\text{abs}(x), \text{abs}(y)) + \text{abs\_tol}$$
2. **Exact Symbolic / Rational Carrier Types**: Testing semirings using Python `Fraction` or `SymPy` symbols to verify exact mathematical validity independent of floating-point noise.
