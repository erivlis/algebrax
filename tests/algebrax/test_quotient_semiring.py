"""
Tests for QuotientMonoidAlgebraSemiring (EP-0100).
"""

from algebrax.semiring import QuotientMonoidAlgebraSemiring, StandardSemiring


def test_polynomial_modulo_reduction():
    """
    Test QuotientMonoidAlgebraSemiring with polynomial modulo reduction.
    Multiply (1 + x) * (1 + x) = 1 + 2x + x^2 modulo (x^2 + 1 = 0 => x^2 = -1).
    Result: (1 - 1) + 2x = 2x.
    """

    def poly_mul_keys(k1: int, k2: int) -> int:
        return k1 + k2

    def mod_x2_plus_1(key: int, coeff: float) -> list[tuple[int, float]]:
        # Reduce x^k mod (x^2 + 1)
        # x^2 = -1
        q, r = divmod(key, 2)
        sign = -1.0 if q % 2 == 1 else 1.0
        return [(r, coeff * sign)]

    semiring = QuotientMonoidAlgebraSemiring[int, float](
        coeff_semiring=StandardSemiring[float](),
        key_op=poly_mul_keys,
        zero_key=0,
        quotient_fn=mod_x2_plus_1,
    )

    # p1 = 1 + x => {0: 1.0, 1: 1.0}
    # p2 = 1 + x => {0: 1.0, 1: 1.0}
    p1 = {0: 1.0, 1: 1.0}
    p2 = {0: 1.0, 1: 1.0}

    res = semiring.mul(p1, p2)
    # Expected: 2x => {1: 2.0} (since 1 + x^2 = 1 - 1 = 0)
    assert res == {1: 2.0}


def test_blade_sign_flip_reduction():
    """
    Test QuotientMonoidAlgebraSemiring with blade swap sign-flip canonicalization.
    e1 * e2 = e12, e2 * e1 = -e12.
    (e1 + e2) * (e1 + e2) = e1^2 + e1 e2 + e2 e1 + e2^2 = 1 + e12 - e12 + 1 = 2.
    """

    def blade_mul_keys(k1: tuple[int, ...], k2: tuple[int, ...]) -> tuple[tuple[int, ...], float]:
        # Concatenate blade tuples and count inversions for sign
        combined = k1 + k2
        # Simple insertion sort inversion count
        arr = list(combined)
        n = len(arr)
        sign = 1.0
        for i in range(n):
            for j in range(i + 1, n):
                if arr[i] > arr[j]:
                    arr[i], arr[j] = arr[j], arr[i]
                    sign = -sign
                elif arr[i] == arr[j]:
                    # e_i^2 = 1 (remove pair)
                    pass
        # Count frequencies
        freq = {}
        for x in combined:
            freq[x] = freq.get(x, 0) + 1
        canonical = []
        for x in sorted(freq.keys()):
            if freq[x] % 2 == 1:
                canonical.append(x)
        return tuple(canonical), sign

    def blade_quotient(key_sign: tuple[tuple[int, ...], float], coeff: float) -> list[tuple[tuple[int, ...], float]]:
        key, sign = key_sign
        return [(key, coeff * sign)]

    semiring = QuotientMonoidAlgebraSemiring[tuple[int, ...], float](
        coeff_semiring=StandardSemiring[float](),
        key_op=lambda k1, k2: blade_mul_keys(k1, k2),  # type: ignore[arg-type]
        zero_key=(),
        quotient_fn=lambda ks, c: blade_quotient(ks, c),  # type: ignore[arg-type]
    )

    # v1 = e1 + e2 => {(1,): 1.0, (2,): 1.0}
    v1 = {(1,): 1.0, (2,): 1.0}
    res = semiring.mul(v1, v1)
    # Expected: e1^2 + e2^2 = 2.0 => {(): 2.0}
    assert res == {(): 2.0}
