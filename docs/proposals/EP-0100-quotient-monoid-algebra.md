---
title: "EP-0100: Quotient Monoid Algebra Semirings & Canonical Reductions"
description: "Extending MonoidAlgebraSemiring with quotient reduction functions for Clifford, Galois, and Skein algebras."
icon: lucide/binary
status: final
---

# EP-0100: Quotient Monoid Algebra Semirings & Canonical Reductions

| Field       | Value                                                    |
|:------------|:---------------------------------------------------------|
| **EP**      | 0100                                                     |
| **Title**   | Quotient Monoid Algebra Semirings & Canonical Reductions |
| **Author**  | Eran Rivlis & Antigravity                                |
| **Status**  | Final                                                    |
| **Type**    | Standards Track                                          |
| **Created** | 2026-08-01                                               |
| **Updated** | 2026-08-01                                               |

## Abstract

This proposal specifies an enhancement to `algebrax.semiring`: introducing `QuotientMonoidAlgebraSemiring`. It
generalizes `MonoidAlgebraSemiring` by accepting a quotient reduction function
`quotient_fn(key, coeff) -> list[tuple[key, coeff]]`. This foundational primitive allows modulo reductions over
polynomial exponents (for Galois fields $\text{GF} (p^m)$), sign-flip blade canonicalizations (for Clifford Geometric
Algebras $Cl (p,q,r)$), and term reductions (for Skein modules).

---

## Motivation

Currently, `MonoidAlgebraSemiring` computes multiplication over free monoid structures:

$$(m_1 \cdot m_2)(k) = \sum_{k_1 \cdot k_2 = k} a (k_1) \otimes b (k_2)$$

However, many advanced mathematical algebras are **quotient rings** $R[M] / I$, where key multiplication $k_1 \cdot k_2$
produces a term that must be simplified or split according to reduction rules:

1. **Clifford Algebra $Cl (p,q,r)$**: $\mathbf{e}_2 \mathbf{e}_1 = -\mathbf{e}_1 \mathbf{e}_2$ (sign flip)
   and $\mathbf{e}_i^2 = \pm 1, 0$.
2. **Galois Field $\text{GF} (p^m)$**: $x^k \bmod P (x)$ where $P (x)$ is an irreducible polynomial.
3. **Polynomial Rings**: $x^a \cdot x^b = x^{a+b}$.

Without a general `QuotientMonoidAlgebraSemiring` primitive, each specialized domain would be forced to re-implement
custom multiplication loops, violating **Shannon's Efficiency** and **Russell's Consistency**.

---

## Rationale (The Council Framework)

* **Symmetry (Noether)**: Preserves the exact same `SparseVector` mapping format `{key: coeff}` while delegating
  reduction laws to a pure canonicalization function.
* **Efficiency (Shannon)**: Single engine powers Clifford algebra, finite fields, knot skein modules, and
  univariate/multivariate polynomial rings.
* **Safety (The Golem)**: Pure functional reduction without mutating underlying key storage.

---

## Specification

### `QuotientMonoidAlgebraSemiring`

```python
class QuotientMonoidAlgebraSemiring(MonoidAlgebraSemiring[K, T], Generic[K, T]):
    """
    Monoid Algebra Semiring R[M] / I with a quotient reduction function.
    
    Args:
        coeff_semiring: The coefficient semiring R.
        key_op: Key multiplication operation k1 * k2.
        zero_key: Key identity (multiplicative one key).
        quotient_fn: Canonical reduction function mapping (key, coeff) -> list of (reduced_key, reduced_coeff).
    """

    def __init__(
            self,
            coeff_semiring: Semiring[T],
            key_op: Callable[[K, K], K],
            zero_key: K,
            quotient_fn: Callable[[K, T], Iterable[tuple[K, T]]] | None = None,
    ):
        super().__init__(coeff_semiring, key_op, zero_key)
        self.quotient_fn = quotient_fn or (lambda k, c: [(k, c)])

    def mul(self, a: SparseVector[K, T], b: SparseVector[K, T]) -> SparseVector[K, T]:
        if not a or not b:
            return {}

        result: dict[K, T] = {}
        key_op = self.key_op
        coeff_mul = self.coeff_semiring.mul
        coeff_add = self.coeff_semiring.add
        zero = self.coeff_semiring.zero
        quotient_fn = self.quotient_fn

        for e1, c1 in a.items():
            for e2, c2 in b.items():
                raw_key = key_op(e1, e2)
                raw_coeff = coeff_mul(c1, c2)

                # Apply quotient canonical reduction
                for red_key, red_coeff in quotient_fn(raw_key, raw_coeff):
                    current_coeff = result.get(red_key, zero)
                    sum_coeff = coeff_add(current_coeff, red_coeff)

                    if sum_coeff == zero:
                        result.pop(red_key, None)
                    else:
                        result[red_key] = sum_coeff

        return result
```

---

## Backwards Compatibility

`MonoidAlgebraSemiring` remains fully backwards compatible. When `quotient_fn` is `None` (default), it behaves
identically to the existing free monoid algebra implementation.

---

## Deliverables

1. **Core Implementation**: Added `QuotientMonoidAlgebraSemiring` to `src/algebrax/semiring.py`.
2. **Unit Tests**: Added test suite `tests/algebrax/test_quotient_semiring.py` (verifying polynomial modulo reduction
   and sign-flip blade multiplication).

---

## Change Log

| Date       | Author                    | Description                      |
|:-----------|:--------------------------|:---------------------------------|
| 2026-08-01 | Eran Rivlis & Antigravity | Initial Foundational EP created. |
