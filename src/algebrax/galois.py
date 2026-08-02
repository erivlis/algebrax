"""
Galois Finite Fields GF(p^m) & Cryptographic Arithmetic (EP-0112).

This module provides finite field polynomial quotient semirings GF(p^m) for AES GF(2^8)
mix-columns matrix arithmetic, Reed-Solomon error correction matrices, and QAP zero-knowledge proofs.
"""

from algebrax.matrix.core import dot
from algebrax.semiring.algebraic import GaloisFieldSemiring
from algebrax.typing import SparseMatrix


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
