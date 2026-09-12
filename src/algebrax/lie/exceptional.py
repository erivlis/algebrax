"""
Exceptional Lie algebras G₂, F₄, E₆, E₇, E₈.

Summary:
    Algorithmic constructions of all 5 exceptional simple Lie algebras:
    - G₂ (dim 14) via octonionic derivations in so(7).
    - E₆ (dim 78), E₇ (dim 133), E₈ (dim 248) via the Frenkel-Kac root lattice engine.
    - F₄ (dim 52) via the canonical outer automorphism folding of E₆.
"""

from __future__ import annotations

import functools
import itertools
from collections.abc import Sequence

from algebrax.lie.core import LieAlgebra, StructureConstants
from algebrax.lie.roots import RootSystem
from algebrax.typing import SparseMatrix, SparseVector


def _fano_3form_sparse_equations(so7_basis: list[tuple[int, int]]) -> dict[int, dict[int, float]]:
    fano = [
        (0, 1, 2),
        (0, 3, 4),
        (0, 6, 5),
        (1, 3, 5),
        (1, 4, 6),
        (2, 3, 6),
        (2, 5, 4),
    ]
    phi: dict[tuple[int, int, int], float] = {}
    for a, b, c in fano:
        for (i, j, k), s in [
            ((a, b, c), 1.0),
            ((b, c, a), 1.0),
            ((c, a, b), 1.0),
            ((b, a, c), -1.0),
            ((c, b, a), -1.0),
            ((a, c, b), -1.0),
        ]:
            phi[(i, j, k)] = s

    eqs: dict[int, dict[int, float]] = {}
    row_idx = 0
    for i, j, k in itertools.combinations(range(7), 3):
        row: dict[int, float] = {}
        for idx, (p, q) in enumerate(so7_basis):
            coeff = 0.0
            if q == i:
                coeff += phi.get((p, j, k), 0.0)
            if p == i:
                coeff -= phi.get((q, j, k), 0.0)
            if q == j:
                coeff += phi.get((i, p, k), 0.0)
            if p == j:
                coeff -= phi.get((i, q, k), 0.0)
            if q == k:
                coeff += phi.get((i, j, p), 0.0)
            if p == k:
                coeff -= phi.get((i, j, q), 0.0)
            if abs(coeff) > 1e-12:
                row[idx] = coeff
        if row:
            eqs[row_idx] = row
            row_idx += 1
    return eqs


def _solve_sparse_nullspace(  # noqa: C901, NOSONAR - sparse Gauss-Jordan nullspace solver with partial pivoting
    eqs: dict[int, dict[int, float]],
    num_cols: int,
    tol: float = 1e-10,
) -> list[SparseVector[int, float]]:
    """Solve the nullspace of a sparse homogeneous linear system A x = 0 using sparse row operations."""
    a_mat = {r: dict(row) for r, row in eqs.items()}
    pivots: list[int] = []
    col = 0
    num_rows = len(a_mat)
    for r in range(num_rows):
        if col >= num_cols:
            break
        pivot_r = None
        max_val = tol
        for i in range(r, num_rows):
            if col in a_mat[i]:
                val = abs(a_mat[i][col])
                if val > max_val:
                    max_val = val
                    pivot_r = i
        while pivot_r is None:
            col += 1
            if col >= num_cols:
                break
            for i in range(r, num_rows):
                if col in a_mat[i]:
                    val = abs(a_mat[i][col])
                    if val > max_val:
                        max_val = val
                        pivot_r = i
        if col >= num_cols or pivot_r is None:
            break

        if pivot_r != r:
            a_mat[r], a_mat[pivot_r] = a_mat[pivot_r], a_mat[r]

        pv = a_mat[r][col]
        a_mat[r] = {c: v / pv for c, v in a_mat[r].items()}
        pivot_row = a_mat[r]

        for i in range(num_rows):
            if i != r and col in a_mat[i]:
                factor = a_mat[i][col]
                for c, v in pivot_row.items():
                    new_val = a_mat[i].get(c, 0.0) - factor * v
                    if abs(new_val) > tol:
                        a_mat[i][c] = new_val
                    elif c in a_mat[i]:
                        del a_mat[i][c]
        pivots.append(col)
        col += 1

    free_cols = [c for c in range(num_cols) if c not in pivots]
    null_basis: list[SparseVector[int, float]] = []
    for fc in free_cols:
        vec: dict[int, float] = {fc: 1.0}
        for r, pc in enumerate(pivots):
            coeff = -a_mat[r].get(fc, 0.0)
            if abs(coeff) > tol:
                vec[pc] = coeff
        null_basis.append(vec)
    return null_basis


def _build_simply_laced_algebra(
    dynkin_or_roots: str | RootSystem,
    names: Sequence[str] | None = None,
) -> LieAlgebra:
    """Construct simply-laced Lie algebra (E6, E7, E8 or custom RootSystem) via Frenkel-Kac cocycle."""
    rs = RootSystem.from_dynkin(dynkin_or_roots) if isinstance(dynkin_or_roots, str) else dynkin_or_roots

    r = rs.rank
    all_roots = rs.roots
    root_to_idx = {root: idx for idx, root in enumerate(all_roots)}
    cartan = rs.cartan_matrix

    def ip(a: tuple[int, ...], b: tuple[int, ...]) -> int:
        return sum(a[i] * b[j] * cartan[i][j] for i in range(r) for j in range(r))

    eps_simple: dict[tuple[int, int], int] = {
        (i, j): -1 for i in range(r) for j in range(r) if i > j and cartan[i][j] == -1
    }

    def eps(a: tuple[int, ...], b: tuple[int, ...]) -> int:
        sign = 1
        for i, a_i in enumerate(a):
            if a_i:
                for j, b_j in enumerate(b):
                    if b_j and (i, j) in eps_simple and (a_i * b_j) % 2 != 0:
                        sign = -sign
        return sign

    dim = r + len(all_roots)
    f_tensor: dict[tuple[int, int, int], float | complex] = {}

    for a_idx, a in enumerate(all_roots):
        gen_a = r + a_idx
        for i in range(r):
            val = float(sum(a[j] * cartan[j][i] for j in range(r)))
            if val != 0:
                f_tensor[(i, gen_a, gen_a)] = val
                f_tensor[(gen_a, i, gen_a)] = -val

    for a_idx, a in enumerate(all_roots):
        neg_a = tuple(-x for x in a)
        neg_idx = root_to_idx[neg_a]
        gen_a = r + a_idx
        gen_neg = r + neg_idx
        sign = float(eps(a, neg_a))
        for i in range(r):
            val = sign * float(a[i])
            if val != 0:
                f_tensor[(gen_a, gen_neg, i)] = val

    for a_idx, a in enumerate(all_roots):
        for b_idx, b in enumerate(all_roots):
            if ip(a, b) == -1:
                a_plus_b = tuple(a[k] + b[k] for k in range(r))
                if a_plus_b in root_to_idx:
                    sum_idx = root_to_idx[a_plus_b]
                    f_tensor[(r + a_idx, r + b_idx, r + sum_idx)] = float(eps(a, b))

    basis_names = (
        list(names)
        if names is not None
        else [f'H_{i}' for i in range(r)] + [f'E_{i}' for i in range(len(all_roots))]
    )
    sc = StructureConstants(dim=dim, tensor=f_tensor)
    return LieAlgebra(dim=dim, structure_constants=sc, basis_names=basis_names)


@functools.lru_cache(maxsize=1)
def g2() -> LieAlgebra:
    r"""The 14-dimensional exceptional Lie algebra G₂ (rank 2).

    Algebraic Signature:
        $\langle \mathfrak{g}_2, [\cdot, \cdot], B \rangle \quad \dim = 14, \quad \mathrm{rank} = 2$

    Cartan Classification:
        - Family: Exceptional Lie algebra $G_2$.
        - Dimension: $14$.
        - Rank: $2$.
        - Root System: $\Phi$ consists of $12$ roots (6 short, 6 long).

    Carrier & Representation:
        - Realized as the derivation algebra of the octonions $\mathrm{Der}(\mathbb{O})$.
        - Minimal representation: 14 sparse $7 \times 7$ skew-symmetric matrices in $\mathfrak{so}(7)$
          preserving the octonionic associative 3-form $\phi$.
    """
    so7_basis = [(p, q) for p in range(7) for q in range(p + 1, 7)]
    eqs = _fano_3form_sparse_equations(so7_basis)
    null_basis = _solve_sparse_nullspace(eqs, num_cols=21)

    g2_matrices: list[SparseMatrix[int, float | complex]] = []
    for vec in null_basis:
        mat: SparseMatrix[int, float | complex] = {}
        for idx, coeff in vec.items():
            p, q = so7_basis[idx]
            if p not in mat:
                mat[p] = {}
            if q not in mat:
                mat[q] = {}
            mat[p][q] = coeff
            mat[q][p] = -coeff
        g2_matrices.append(mat)

    return LieAlgebra.from_matrix_basis(g2_matrices, names=[f'G_{i}' for i in range(14)])


@functools.lru_cache(maxsize=1)
def e6() -> LieAlgebra:
    r"""The 78-dimensional exceptional Lie algebra E₆ (rank 6).

    Algebraic Signature:
        $\langle \mathfrak{e}_6, [\cdot, \cdot], B \rangle \quad \dim = 78, \quad \mathrm{rank} = 6$

    Cartan Classification:
        - Family: Exceptional simply-laced Lie algebra $E_6$.
        - Dimension: $78$.
        - Rank: $6$.
        - Root System: $\Phi$ consists of $72$ roots of length $\sqrt{2}$.
    """
    return _build_simply_laced_algebra('E6')


@functools.lru_cache(maxsize=1)
def e7() -> LieAlgebra:
    r"""The 133-dimensional exceptional Lie algebra E₇ (rank 7).

    Algebraic Signature:
        $\langle \mathfrak{e}_7, [\cdot, \cdot], B \rangle \quad \dim = 133, \quad \mathrm{rank} = 7$

    Cartan Classification:
        - Family: Exceptional simply-laced Lie algebra $E_7$.
        - Dimension: $133$.
        - Rank: $7$.
        - Root System: $\Phi$ consists of $126$ roots of length $\sqrt{2}$.
    """
    return _build_simply_laced_algebra('E7')


@functools.lru_cache(maxsize=1)
def e8() -> LieAlgebra:
    r"""The 248-dimensional exceptional Lie algebra E₈ (rank 8).

    Algebraic Signature:
        $\langle \mathfrak{e}_8, [\cdot, \cdot], B \rangle \quad \dim = 248, \quad \mathrm{rank} = 8$

    Cartan Classification:
        - Family: Exceptional simply-laced Lie algebra $E_8$.
        - Dimension: $248$.
        - Rank: $8$.
        - Root System: $\Phi$ consists of $240$ roots of length $\sqrt{2}$.
        - Minimal representation: The adjoint representation itself ($248 \times 248$).
    """
    return _build_simply_laced_algebra('E8')


@functools.lru_cache(maxsize=1)
def f4() -> LieAlgebra:
    r"""The 52-dimensional exceptional Lie algebra F₄ (rank 4).

    Algebraic Signature:
        $\langle \mathfrak{f}_4, [\cdot, \cdot], B \rangle \quad \dim = 52, \quad \mathrm{rank} = 4$

    Cartan Classification:
        - Family: Exceptional non-simply-laced Lie algebra $F_4$.
        - Dimension: $52$.
        - Rank: $4$.
        - Root System: $\Phi$ consists of $48$ roots ($24$ long, $24$ short).
        - Construction: Canonical outer automorphism folding of $\mathfrak{e}_6$ under $\mathbb{Z}_2$ symmetry.
    """
    alg_e6 = e6()
    rs = RootSystem.from_dynkin('E6')
    r = rs.rank
    all_roots = rs.roots
    root_to_idx = {root: i for i, root in enumerate(all_roots)}
    cartan = rs.cartan_matrix

    def ip(a: tuple[int, ...], b: tuple[int, ...]) -> int:
        return sum(a[i] * b[j] * cartan[i][j] for i in range(r) for j in range(r))

    # Outer automorphism permutation of E6 Dynkin diagram
    tau_perm = {0: 5, 5: 0, 2: 4, 4: 2, 1: 1, 3: 3}
    m_tau: dict[int, dict[int, float]] = {i: {tau_perm[i]: 1.0} for i in range(r)}
    simple = rs.simple_roots
    for i in range(r):
        simple_root = simple[i]
        tau_root = tuple(simple_root[tau_perm[k]] for k in range(r))
        e_i = r + root_to_idx[simple_root]
        e_tau = r + root_to_idx[tau_root]
        m_tau[e_i] = {e_tau: 1.0}
        f_i = r + root_to_idx[tuple(-x for x in simple_root)]
        f_tau = r + root_to_idx[tuple(-x for x in tau_root)]
        m_tau[f_i] = {f_tau: 1.0}

    for gamma in sorted(all_roots, key=lambda a: (abs(sum(a)), abs(sum(a)) if a[0] >= 0 else -1)):
        g_idx = r + root_to_idx[gamma]
        if g_idx in m_tau:
            continue
        for i in range(r):
            alpha_i = simple[i] if sum(gamma) > 0 else tuple(-x for x in simple[i])
            beta = tuple(gamma[k] - alpha_i[k] for k in range(r))
            if beta in root_to_idx and ip(alpha_i, beta) == -1:
                a_idx = r + root_to_idx[alpha_i]
                b_idx = r + root_to_idx[beta]
                brk = alg_e6.bracket({a_idx: 1.0}, {b_idx: 1.0})
                if g_idx in brk:
                    c = brk[g_idx]
                    tau_a = m_tau[a_idx]
                    tau_b = m_tau[b_idx]
                    tau_brk = alg_e6.bracket(tau_a, tau_b)
                    m_tau[g_idx] = {k: v / c for k, v in tau_brk.items()}
                    break

    dim_e6 = alg_e6.dim
    f4_basis: list[dict[int, float]] = []
    for i in range(dim_e6):
        vec: dict[int, float] = {i: 0.5}
        for out_k, out_v in m_tau[i].items():
            vec[out_k] = vec.get(out_k, 0.0) + 0.5 * out_v
        for b in f4_basis:
            dot_b = sum(b.get(k, 0.0) * vec.get(k, 0.0) for k in set(b) & set(vec))
            norm_b = sum(v * v for v in b.values())
            fac = dot_b / norm_b
            for k, v in b.items():
                vec[k] = vec.get(k, 0.0) - fac * v
        clean = {k: v for k, v in vec.items() if abs(v) > 1e-10}
        norm = sum(v * v for v in clean.values())
        if norm > 1e-8:
            inv_n = 1.0 / (norm**0.5)
            clean_unit = {k: v * inv_n for k, v in clean.items()}
            f4_basis.append(clean_unit)

    f_f4: dict[tuple[int, int, int], float | complex] = {}
    for i in range(52):
        for j in range(i + 1, 52):
            comm = alg_e6.bracket(f4_basis[i], f4_basis[j])
            for k in range(52):
                proj = sum(f4_basis[k].get(idx, 0.0) * comm.get(idx, 0.0) for idx in set(f4_basis[k]) & set(comm))
                if abs(proj) > 1e-10:
                    f_f4[(i, j, k)] = proj
                    f_f4[(j, i, k)] = -proj

    sc_f4 = StructureConstants(dim=52, tensor=f_f4)
    names = [f'F_{i}' for i in range(52)]
    return LieAlgebra(dim=52, structure_constants=sc_f4, basis_names=names)


__all__ = [
    'e6',
    'e7',
    'e8',
    'f4',
    'g2',
]
