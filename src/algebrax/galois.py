"""
Galois Finite Fields GF(p^m) & Cryptographic Arithmetic (EP-0112).

This module provides finite field polynomial quotient semirings GF(p^m) for AES GF(2^8)
mix-columns matrix arithmetic, Reed-Solomon error correction matrices, and QAP zero-knowledge proofs.
"""

from collections.abc import Iterable

from algebrax.matrix.core import dot
from algebrax.semiring import QuotientMonoidAlgebraSemiring, StandardSemiring
from algebrax.typing import SparseMatrix, SparseVector


def _gf_poly_mod(
    exp: int, coeff: int, p: int = 2, irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1)
) -> list[tuple[int, int]]:
    """
    Reduce polynomial term coeff * x^exp modulo irreducible polynomial irreduc_poly in GF(p).
    Default irreduc_poly: x^8 + x^4 + x^3 + x + 1 (AES GF(2^8) field).
    """
    m = len(irreduc_poly) - 1  # Degree of irreducible polynomial
    c = coeff % p
    if c == 0:
        return []

    # If exponent < m, no reduction needed
    if exp < m:
        return [(exp, c)]

    # Long division polynomial reduction in GF(p)
    poly = [0] * (exp + 1)
    poly[exp] = c

    for deg in range(exp, m - 1, -1):
        if poly[deg] != 0:
            factor = poly[deg]
            for i in range(len(irreduc_poly)):
                target_deg = deg - m + i
                poly[target_deg] = (poly[target_deg] - factor * irreduc_poly[i]) % p

    result: list[tuple[int, int]] = []
    for deg in range(m):
        if poly[deg] != 0:
            result.append((deg, poly[deg]))

    return result


class GaloisFieldSemiring(QuotientMonoidAlgebraSemiring[int, int]):
    """
    Galois Finite Field GF(p^m) Semiring.
    Values are field elements represented as sparse polynomial vectors dict[int, int].
    """

    def __init__(
        self, p: int = 2, irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1)
    ):
        self.p = p
        self.irreduc_poly = irreduc_poly

        def key_op(k1: int, k2: int) -> int:
            return k1 + k2

        def quotient_fn(key: int, coeff: int) -> Iterable[tuple[int, int]]:
            return _gf_poly_mod(key, coeff, p=self.p, irreduc_poly=self.irreduc_poly)

        super().__init__(
            coeff_semiring=StandardSemiring[int](),
            key_op=key_op,
            zero_key=0,
            quotient_fn=quotient_fn,
        )

    def add(self, a: SparseVector[int, int], b: SparseVector[int, int]) -> SparseVector[int, int]:
        """
        Elementwise addition in GF(p).
        """
        result = dict(a)
        p = self.p
        for exp, coeff in b.items():
            sum_val = (result.get(exp, 0) + coeff) % p
            if sum_val == 0:
                result.pop(exp, None)
            else:
                result[exp] = sum_val
        return result


def gf_matrix_mul(
    m1: SparseMatrix,
    m2: SparseMatrix,
    p: int = 2,
    irreduc_poly: tuple[int, ...] = (1, 1, 0, 1, 1, 0, 0, 0, 1),
) -> SparseMatrix:
    """
    Compute sparse matrix multiplication over Galois Field GF(p^m).
    """
    gf = GaloisFieldSemiring(p=p, irreduc_poly=irreduc_poly)
    return dot(m1, m2, semiring=gf)
