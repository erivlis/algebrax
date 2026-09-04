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
# # Galois Finite Field $\\text{GF}(2^8)$ & AES Cryptographic MixColumns
#
# ## Theoretical Foundations & Physics
# 1. **Galois Field $\\text{GF}(p^m)$**: Polynomial quotient arithmetic modulo an irreducible polynomial $P(x)$.
# 2. **AES MixColumns**: Matrix multiplication over $\\text{GF}(2^8)$ with
#    irreducible polynomial $P(x) = x^8 + x^4 + x^3 + x + 1$.

# %%
import algebrax as ax


def gf_multiply(
    a: dict[int, int],
    b: dict[int, int],
    p: int = 2,
    irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1),
) -> dict[int, int]:
    """Multiply polynomials in Galois Field GF(p^m) modulo irreducible polynomial."""
    gf = ax.galois.GaloisFieldSemiring(p=p, irreduc_poly=irreduc_poly)
    return gf.mul(a, b)


def gf_mix_columns(
    state: dict[int, dict[int, dict[int, int]]],
    mix_col_matrix: dict[int, dict[int, dict[int, int]]] | None = None,
    p: int = 2,
) -> dict[int, dict[int, dict[int, int]]]:
    """Perform AES MixColumns linear diffusion over GF(2^8)."""
    if mix_col_matrix is None:
        mix_col_matrix = {
            0: {0: {1: 1}, 1: {0: 1}},
            1: {0: {0: 1}, 1: {1: 1}},
        }
    return ax.galois.gf_matrix_mul(mix_col_matrix, state, p=p)


# %% [markdown]
# ## Step 1: Field Element Multiplication in $\\text{GF}(2^8)$
#
# ## Step 2: AES MixColumns Matrix Transformation over $\\text{GF}(2^8)$


def run_demo() -> None:
    """Run GF(2^8) arithmetic and AES MixColumns transformations."""
    a = {4: 1}
    b = {4: 1}
    print('Field Element Multiplication in GF(2^8):')
    print('  a = x^4, b = x^4')
    res_poly = gf_multiply(a, b)
    print('  a * b mod (x^8 + x^4 + x^3 + x + 1) =', res_poly)
    assert res_poly == {0: 1, 1: 1, 3: 1, 4: 1}

    state = {
        0: {0: {4: 1}},
        1: {0: {2: 1}},
    }
    out_state = gf_mix_columns(state)
    print('AES MixColumns Matrix Transformation over GF(2^8):')
    print('  Input State:', state)
    print('  Output Transformed State:', out_state)


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Galois Finite Field GF(2^8) Cryptography Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
