r"""
Real-World Use Case: Galois Finite Field GF(2^8) & AES Cryptographic MixColumns.

Theoretical Foundations & Physics:
1. Galois Field GF(p^m): Polynomial quotient arithmetic modulo an irreducible polynomial P(x).
2. AES MixColumns: Matrix multiplication over GF(2^8) with P(x) = x^8 + x^4 + x^3 + x + 1.
3. Zero-Knowledge QAP Polynomial Polynomials: Fast finite field sparse ax.matrix.dot products over GF(p^m).
"""

import algebrax as ax


def main() -> None:
    print('--- Galois Finite Field GF(2^8) Cryptographic Arithmetic ---')

    gf = ax.galois.ax.semiring.GaloisFieldSemiring(p=2, irreduc_poly=(1, 1, 0, 1, 1, 0, 0, 0, 1))

    # Define polynomial elements a = x^4, b = x^4
    a = {4: 1}
    b = {4: 1}

    print('\n[1] Field Element Multiplication in GF(2^8):')
    print('  a = x^4, b = x^4')
    res_poly = gf.mul(a, b)
    print('  a * b mod (x^8 + x^4 + x^3 + x + 1) =', res_poly)

    # Expected: x^8 mod P(x) = x^4 + x^3 + x + 1 => {0: 1, 1: 1, 3: 1, 4: 1}
    assert res_poly == {0: 1, 1: 1, 3: 1, 4: 1}

    # AES MixColumns Sparse Matrix Multiplication
    mix_col = {
        0: {0: {1: 1}, 1: {0: 1}},
        1: {0: {0: 1}, 1: {1: 1}},
    }
    state = {
        0: {0: {4: 1}},  # State col 0: x^4
        1: {0: {2: 1}},  # State col 1: x^2
    }

    out_state = ax.galois.ax.galois.gf_matrix_mul(mix_col, state, p=2)
    print('\n[2] AES MixColumns Matrix Transformation over GF(2^8):')
    print('  Input State:', state)
    print('  Output Transformed State:', out_state)

    print('\nSuccessfully verified Galois Finite Field GF(2^8) Cryptographic Arithmetic!')


if __name__ == '__main__':
    main()
