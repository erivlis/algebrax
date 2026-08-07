---
title: Galois Finite Field Semiring
description: Tutorial on GaloisFieldSemiring GF(p^m) for cryptographic matrix arithmetic and MixColumns.
---

# Galois Finite Field Semiring GF(p^m)

The **`GaloisFieldSemiring`** in `algebrax.galois` enables matrix linear algebra over finite fields $\text{GF}(p^m)$ by representing field elements as sparse polynomial vectors `{exponent: coeff}` modulo an irreducible polynomial $P(x)$.

---

## Field Arithmetic

- **Addition**: Polynomial addition modulo prime characteristic $p$.
- **Multiplication**: Polynomial multiplication in $\mathbb{F}_p[x]$ reduced by long division modulo $P(x)$ (e.g. $x^8 + x^4 + x^3 + x + 1$ for AES $\text{GF}(2^8)$).

---

## Python Example: AES GF(2^8) MixColumns Matrix Multiplication

```python
import algebrax as ax

# Instantiate AES GF(2^8) ax.semiring.Semiring
gf = ax.galois.GaloisFieldSemiring(p=2, irreduc_poly=(1, 1, 0, 1, 1, 0, 0, 0, 1))

# Element multiplication: x^4 * x^4 = x^8 mod P(x) = x^4 + x^3 + x + 1
res_poly = gf.mul({4: 1}, {4: 1})
print("x^4 * x^4 mod P(x) in GF(2^8):", res_poly)
# Output: {0: 1, 1: 1, 3: 1, 4: 1}

# Sparse Matrix Multiplication over GF(2^8)
mix_col = {
    0: {0: {1: 1}, 1: {0: 1}},
    1: {0: {0: 1}, 1: {1: 1}},
}
state = {
    0: {0: {4: 1}},
    1: {0: {2: 1}},
}

out_state = ax.galois.gf_matrix_mul(mix_col, state, p=2)
print("Transformed AES State:", out_state)
```
