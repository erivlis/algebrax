"""
Tests for Galois Finite Fields GF(p^m).
"""

from algebrax.galois import GaloisFieldSemiring, gf_matrix_mul


def test_galois_field_gf28_multiplication():
    """
    Test GF(2^8) AES field multiplication modulo P(x) = x^8 + x^4 + x^3 + x + 1.
    Multiply x^4 * x^4 = x^8 mod P(x) = x^4 + x^3 + x + 1.
    """
    gf = GaloisFieldSemiring(p=2, irreduc_poly=(1, 1, 0, 1, 1, 0, 0, 0, 1))

    # x^4 = {4: 1}
    a = {4: 1}
    b = {4: 1}

    res = gf.mul(a, b)
    # Expected: x^4 + x^3 + x + 1 => {0: 1, 1: 1, 3: 1, 4: 1}
    assert res == {0: 1, 1: 1, 3: 1, 4: 1}


def test_galois_field_matrix_multiplication():
    """
    Test matrix multiplication over GF(2^8).
    """
    m1 = {0: {0: {1: 1}, 1: {0: 1}}}
    m2 = {0: {0: {2: 1}}, 1: {0: {3: 1}}}

    # M1 * M2
    res = gf_matrix_mul(m1, m2, p=2)
    # Row 0, Col 0: (x * x^2) + (1 * x^3) = x^3 + x^3 = 0 in GF(2)
    assert res == {}
