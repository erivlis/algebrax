r"""
Sparse Clebsch-Gordan Coupling 3-Tensors for $\mathfrak{su}(2)$ / $\mathfrak{sl}(2)$ Angular Momentum Addition.

Algebraic Signatures:
    Tensor Product Decomposition:  $V_{j_1} \otimes V_{j_2} \cong \bigoplus_{j = |j_1 - j_2|}^{j_1 + j_2} V_j$
    Selection Rules:               $m = m_1 + m_2, \quad |j_1 - j_2| \le j \le j_1 + j_2$
    Orthogonality:                 $\sum_{m_1, m_2} C_{m_1 m_2}^{j m} C_{m_1 m_2}^{j' m'} = \delta_{jj'}\delta_{mm'}$

All spin and magnetic quantum numbers are encoded as exact integer half-spin units
($J = 2j \in \mathbb{Z}_{\ge 0}$, $M = 2m \in \{-J, -J+2, \dots, J\}$) to avoid floating-point
dictionary key drift.
"""

from __future__ import annotations

import math
from fractions import Fraction

from algebrax.typing import SparseMatrix


def _validate_half_spin(j_halves: int, name: str) -> None:
    if not isinstance(j_halves, int) or isinstance(j_halves, bool) or j_halves < 0:
        raise ValueError(f'{name} must be a non-negative integer (2j), got {j_halves!r}.')


def _valid_selection_rules(
    j1_halves: int,
    m1_halves: int,
    j2_halves: int,
    m2_halves: int,
    j_halves: int,
    m_halves: int,
) -> bool:
    """Return True iff quantum numbers satisfy triangle, projection, and parity selection rules."""
    if m_halves != m1_halves + m2_halves:
        return False
    if j_halves < abs(j1_halves - j2_halves) or j_halves > j1_halves + j2_halves:
        return False
    if (j1_halves + j2_halves - j_halves) % 2 != 0:
        return False
    if abs(m1_halves) > j1_halves or abs(m2_halves) > j2_halves or abs(m_halves) > j_halves:
        return False
    return (
        (j1_halves - m1_halves) % 2 == 0
        and (j2_halves - m2_halves) % 2 == 0
        and (j_halves - m_halves) % 2 == 0
    )


def clebsch_gordan_coefficient(
    j1_halves: int,
    m1_halves: int,
    j2_halves: int,
    m2_halves: int,
    j_halves: int,
    m_halves: int,
) -> float:
    r"""Compute a single Condon-Shortley Clebsch-Gordan coefficient $\langle j_1 m_1; j_2 m_2 \mid j m \rangle$.

    Uses Racah's closed-form alternating sum evaluated in exact rational arithmetic (`Fraction`)
    before taking the final square root, preventing catastrophic cancellation at high spins.

    Args:
        j1_halves: First spin $2j_1 \in \mathbb{Z}_{\ge 0}$.
        m1_halves: First magnetic projection $2m_1 \in \{-2j_1, -2j_1+2, \dots, 2j_1\}$.
        j2_halves: Second spin $2j_2 \in \mathbb{Z}_{\ge 0}$.
        m2_halves: Second magnetic projection $2m_2 \in \{-2j_2, -2j_2+2, \dots, 2j_2\}$.
        j_halves: Coupled total spin $2j \in \mathbb{Z}_{\ge 0}$.
        m_halves: Coupled total projection $2m \in \{-2j, -2j+2, \dots, 2j\}$.

    Returns:
        Real-valued Clebsch-Gordan coefficient (exact `0.0` when forbidden by selection rules).
    """
    _validate_half_spin(j1_halves, 'j1_halves')
    _validate_half_spin(j2_halves, 'j2_halves')
    _validate_half_spin(j_halves, 'j_halves')

    if not _valid_selection_rules(j1_halves, m1_halves, j2_halves, m2_halves, j_halves, m_halves):
        return 0.0

    a = (j1_halves + j2_halves - j_halves) // 2
    b = (j1_halves - j2_halves + j_halves) // 2
    c = (-j1_halves + j2_halves + j_halves) // 2
    s = (j1_halves + j2_halves + j_halves) // 2 + 1

    p1 = (j1_halves + m1_halves) // 2
    q1 = (j1_halves - m1_halves) // 2
    p2 = (j2_halves + m2_halves) // 2
    q2 = (j2_halves - m2_halves) // 2
    p = (j_halves + m_halves) // 2
    q = (j_halves - m_halves) // 2

    t1 = (j_halves - j2_halves + m1_halves) // 2
    t2 = (j_halves - j1_halves - m2_halves) // 2

    k_min = max(0, -t1, -t2)
    k_max = min(a, q1, p2)

    fact = math.factorial
    racah_sum = Fraction(0)
    for k in range(k_min, k_max + 1):
        denom = (
            fact(k)
            * fact(a - k)
            * fact(q1 - k)
            * fact(p2 - k)
            * fact(k + t1)
            * fact(k + t2)
        )
        racah_sum += Fraction(-1 if k % 2 else 1, denom)

    if racah_sum == 0:
        return 0.0

    prefactor_sq = Fraction(
        (j_halves + 1) * fact(a) * fact(b) * fact(c) * fact(p1) * fact(q1) * fact(p2) * fact(q2) * fact(p) * fact(q),
        fact(s),
    )
    sign = -1.0 if racah_sum < 0 else 1.0
    total_sq = prefactor_sq * racah_sum * racah_sum
    return sign * math.sqrt(float(total_sq))


def clebsch_gordan_tensor(
    j1_halves: int,
    j2_halves: int,
    tol: float = 1e-14,
) -> dict[tuple[tuple[int, int], int, int], float]:
    r"""Compute the sparse Clebsch-Gordan coupling 3-tensor $C_{m_1, m_2}^{(j, m)}$ for spins $j_1, j_2$.

    Only non-zero entries obeying the selection rules $m = m_1 + m_2$ and $|j_1 - j_2| \le j \le j_1 + j_2$
    are stored. All quantum numbers use integer half-spin units ($2j, 2m$).

    Args:
        j1_halves: First spin $2j_1 \in \mathbb{Z}_{\ge 0}$.
        j2_halves: Second spin $2j_2 \in \mathbb{Z}_{\ge 0}$.
        tol: Pruning threshold below which coefficients are treated as zero.

    Returns:
        Sparse dictionary mapping `((j_halves, m_halves), m1_halves, m2_halves) -> float`.
    """
    _validate_half_spin(j1_halves, 'j1_halves')
    _validate_half_spin(j2_halves, 'j2_halves')

    tensor: dict[tuple[tuple[int, int], int, int], float] = {}
    j_min = abs(j1_halves - j2_halves)
    j_max = j1_halves + j2_halves

    for j_h in range(j_max, j_min - 1, -2):
        for m_h in range(j_h, -j_h - 1, -2):
            for m1_h in range(j1_halves, -j1_halves - 1, -2):
                m2_h = m_h - m1_h
                if abs(m2_h) > j2_halves:
                    continue
                coeff = clebsch_gordan_coefficient(j1_halves, m1_h, j2_halves, m2_h, j_h, m_h)
                if abs(coeff) > tol:
                    tensor[((j_h, m_h), m1_h, m2_h)] = coeff
    return tensor


def clebsch_gordan_matrix(
    j1_halves: int,
    j2_halves: int,
    tol: float = 1e-14,
) -> tuple[SparseMatrix[int, float], list[tuple[int, int]]]:
    r"""Build the orthogonal change-of-basis matrix $U$ coupling $V_{j_1} \otimes V_{j_2}$ to $\bigoplus_j V_j$.

    Rows are indexed in lexicographical uncoupled basis order $(m_1, m_2)$ with descending
    $m_1 \in \{j_1, j_1-1, \dots, -j_1\}$ and $m_2 \in \{j_2, j_2-1, \dots, -j_2\}$.
    Columns are indexed in coupled basis order $(j, m)$ with descending $j \in \{j_1+j_2, \dots, |j_1-j_2|\}$
    and descending $m \in \{j, \dots, -j\}$, satisfying:
    $$U^T (\rho_{j_1}(X) \otimes \mathbf{I} + \mathbf{I} \otimes \rho_{j_2}(X)) U = \bigoplus_j \rho_j(X)$$

    Args:
        j1_halves: First spin $2j_1 \in \mathbb{Z}_{\ge 0}$.
        j2_halves: Second spin $2j_2 \in \mathbb{Z}_{\ge 0}$.
        tol: Pruning threshold below which matrix entries are omitted.

    Returns:
        Tuple `(u_matrix, coupled_basis)` where `u_matrix` is the orthogonal sparse matrix $U$
        and `coupled_basis` lists the column quantum numbers `(j_halves, m_halves)`.
    """
    _validate_half_spin(j1_halves, 'j1_halves')
    _validate_half_spin(j2_halves, 'j2_halves')

    d2 = j2_halves + 1
    cg_tensor = clebsch_gordan_tensor(j1_halves, j2_halves, tol=tol)

    coupled_basis: list[tuple[int, int]] = []
    for j_h in range(j1_halves + j2_halves, abs(j1_halves - j2_halves) - 1, -2):
        for m_h in range(j_h, -j_h - 1, -2):
            coupled_basis.append((j_h, m_h))
    col_of = {jm: idx for idx, jm in enumerate(coupled_basis)}

    u_mat: dict[int, dict[int, float]] = {}
    for (jm, m1_h, m2_h), coeff in cg_tensor.items():
        idx1 = (j1_halves - m1_h) // 2
        idx2 = (j2_halves - m2_h) // 2
        row = idx1 * d2 + idx2
        col = col_of[jm]
        u_mat.setdefault(row, {})[col] = coeff

    return u_mat, coupled_basis


__all__ = [
    'clebsch_gordan_coefficient',
    'clebsch_gordan_matrix',
    'clebsch_gordan_tensor',
]
