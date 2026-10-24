# Hypothesis: A New Approach to Property-Based Testing

| Field | Value |
|:---|:---|
| **Citation** | David R. MacIver, Zac Hatfield-Dodds. *Hypothesis: A new approach to property-based testing*. Journal of Open Source Software (JOSS), 4(43), 1891, 2019. |
| **DOI** | [10.21105/joss.01891](https://doi.org/10.21105/joss.01891) |
| **Direct PDF** | [https://joss.theoj.org/papers/10.21105/joss.01891.pdf](https://joss.theoj.org/papers/10.21105/joss.01891.pdf) |
| **Local PDF Mirror** | [`maciver_2019_hypothesis.pdf`](./maciver_2019_hypothesis.pdf) (128 KB) |
| **Keywords** | Property-Based Testing, Test Case Reduction, Shrinking, Hypothesis, Python |

---

## Abstract & Summary

`Hypothesis` is a modern property-based testing library for Python. Rather than requiring developers to manually hand-craft unit test inputs, developers specify parameterized assertions (properties) and strategies for generating data. Hypothesis automatically searches for inputs that falsify the assertions, and when a failure is detected, executes **automated test-case reduction (shrinking)** to produce a minimal reproducing counterexample.

---

## Key Technical Innovations

### 1. Representation-Driven Shrinking
In classical QuickCheck (Haskell), shrinking functions are tied directly to data types (e.g., `shrink :: a -> [a]`), requiring custom reduction logic for every new structure. 

In contrast, Hypothesis separates generation from shrinking:
- **Byte-Stream Representation:** Generators draw random data from a structured, finite stream of bytes (`ConjectureData`).
- **Universal Reducer:** Shrinking is executed by minimizing the underlying byte stream (using delta-debugging, deletion, and integer minimization).
- **Generator Preservation:** The generator runs against the reduced byte stream, ensuring all intermediate shrunk states are valid, well-formed instances of the user's data structures.

### 2. Compositional Strategy Algebra
Hypothesis provides combinators (`st.builds`, `st.one_of`, `st.mapped`, `st.flatmap`) allowing developers to define complex combinatorial and mathematical objects (e.g., sparse matrices, directed acyclic graphs, semiring elements) cleanly.

---

## Direct Application to AlgebraX Verification Suite

In **AlgebraX** (`EP-0180` and `tests/verifications/test_axiomatic_properties.py`), Hypothesis forms the backbone of **Methodology 3 (Property-Based Axiomatic Verification)**:

1. **Axiomatic Parametrization:** Testing all semirings against formal algebraic laws:
   $$\forall a, b, c \in S: \quad a \otimes (b \oplus c) = (a \otimes b) \oplus (a \otimes c)$$
2. **Singularity Probing:** Hypothesis's internal search biases automatically inject algebraic boundary points:
   - Zero element $\bar{0}$
   - One element $\bar{1}$
   - Signed infinities (`float('inf')`, `float('-inf')`)
   - Empty sparse mappings `{}`
3. **Exact Rational Domain Separation:**
   - Float strategies test approximate equalities: `math.isclose(lhs, rhs, rel_tol=1e-9)`
   - Exact strategies over `fractions.Fraction` test mathematical logic without IEEE 754 non-associativity contamination.
