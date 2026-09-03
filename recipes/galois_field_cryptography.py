# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Galois Finite Field $\text{GF}(2^8)$ & AES Cryptographic MixColumns
#
# ## Theoretical Foundations & Physics
# 1. **Galois Field $\text{GF}(p^m)$**: Polynomial quotient arithmetic modulo an irreducible polynomial $P(x)$.
# 2. **AES MixColumns**: Matrix multiplication over $\text{GF}(2^8)$ with
#    irreducible polynomial $P(x) = x^8 + x^4 + x^3 + x + 1$.
# 3. **Zero-Knowledge QAP Polynomials**: Fast finite field sparse matrix dot products over $\text{GF}(p^m)$.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Field Element Multiplication in $\text{GF}(2^8)$
# Multiply $a = x^4$ and $b = x^4$ modulo $P(x) = x^8 + x^4 + x^3 + x + 1$.

# %%
gf = ax.galois.GaloisFieldSemiring(p=2, irreduc_poly=(1, 1, 0, 1, 1, 0, 0, 0, 1))

a = {4: 1}
b = {4: 1}

print('Field Element Multiplication in GF(2^8):')
print('  a = x^4, b = x^4')
res_poly = gf.mul(a, b)
print('  a * b mod (x^8 + x^4 + x^3 + x + 1) =', res_poly)
assert res_poly == {0: 1, 1: 1, 3: 1, 4: 1}

# %% [markdown]
# ## Step 2: AES MixColumns Matrix Transformation over $\text{GF}(2^8)$

# %%
mix_col = {
    0: {0: {1: 1}, 1: {0: 1}},
    1: {0: {0: 1}, 1: {1: 1}},
}
state = {
    0: {0: {4: 1}},
    1: {0: {2: 1}},
}

out_state = ax.galois.gf_matrix_mul(mix_col, state, p=2)
print('AES MixColumns Matrix Transformation over GF(2^8):')
print('  Input State:', state)
print('  Output Transformed State:', out_state)


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Galois Finite Field GF(2^8) Cryptography Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
