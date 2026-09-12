"""
Classical infinite families and low-dimensional matrix Lie algebras.

Summary:
    Generalized families: so_n, su_n, u_n, sp_n, sl_n, se_n, and clifford_lie_algebra.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence

from algebrax.lie.core import LieAlgebra, StructureConstants
from algebrax.semiring.algebraic import CliffordSemiring
from algebrax.typing import SparseMatrix


def u_n(n: int, names: Sequence[str] | None = None) -> LieAlgebra:
    r"""The unitary Lie algebra u(n) of n x n skew-Hermitian matrices.

    Algebraic Signature:
        $\langle \mathfrak{u}(n), [\cdot, \cdot], B \rangle$
        $X^\dagger = -X, \quad \dim = n^2, \quad \mathrm{rank} = n$

    Cartan Classification:
        - Family: Reductive Lie algebra $\mathfrak{u}(n) \cong \mathfrak{su}(n) \oplus \mathfrak{u}(1)$.
        - Dimension: $n^2$.
        - Rank: $n$ (maximal abelian torus $\mathfrak{t}^n$).
        - Center: 1-dimensional center $\mathfrak{u}(1) \cdot I_n$.

    Carrier & Invariants:
        - Field: Complex matrices over real carrier $\mathbb{R}$.
        - Semisimplicity: Reductive, non-semisimple due to abelian center.
    """
    if n < 1:
        raise ValueError('u(n) is only defined for n >= 1.')
    gens: list[SparseMatrix[int, float | complex]] = []
    default_names: list[str] = []
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: 0.5}, k: {j: -0.5}})
            default_names.append(f'A_{{{j}{k}}}')
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: -0.5j}, k: {j: -0.5j}})
            default_names.append(f'S_{{{j}{k}}}')
    for k in range(n):
        gens.append({k: {k: -0.5j}})
        default_names.append(f'D_{k}')
    return LieAlgebra.from_matrix_basis(gens, names=names if names is not None else default_names)


def su_n(n: int, names: Sequence[str] | None = None) -> LieAlgebra:
    r"""The special unitary Lie algebra su(n) of n x n traceless skew-Hermitian matrices.

    Algebraic Signature:
        $\langle \mathfrak{su}(n), [\cdot, \cdot], B \rangle$
        $X^\dagger = -X, \quad \mathrm{Tr}(X) = 0, \quad \dim = n^2 - 1$

    Cartan Classification:
        - Family: Simple Lie algebra of type $A_{n-1}$ (compact real form).
        - Dimension: $n^2 - 1$.
        - Rank: $n - 1$ (Cartan subalgebra of diagonal traceless matrices).
        - Root System: $\Phi$ consists of $n(n-1)$ roots.

    Carrier & Invariants:
        - Field: Complex matrices over real carrier $\mathbb{R}$.
        - Killing Form: Non-degenerate, negative-definite (semisimple).
        - Center: $\mathfrak{z}(\mathfrak{g}) = \{0\}$.
    """
    if n < 2:
        raise ValueError('su(n) is only defined for n >= 2.')
    gens: list[SparseMatrix[int, float | complex]] = []
    default_names: list[str] = []
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: 0.5}, k: {j: -0.5}})
            default_names.append(f'A_{{{j}{k}}}')
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: -0.5j}, k: {j: -0.5j}})
            default_names.append(f'S_{{{j}{k}}}')
    for k in range(1, n):
        diag: dict[int, dict[int, float | complex]] = {}
        for m in range(k):
            diag[m] = {m: -0.5j}
        diag[k] = {k: 0.5j * k}
        gens.append(diag)
        default_names.append(f'D_{k}')
    return LieAlgebra.from_matrix_basis(gens, names=names if names is not None else default_names)


def so_n(n: int, names: Sequence[str] | None = None) -> LieAlgebra:
    r"""The special orthogonal Lie algebra so(n) of n x n skew-symmetric matrices.

    Algebraic Signature:
        $\langle \mathfrak{so}(n), [\cdot, \cdot], B \rangle \quad X^T = -X, \quad \dim = \frac{n(n-1)}{2}$

    Cartan Classification:
        - Family: Simple Lie algebra of type $B_k$ (for $n = 2k+1$) or $D_k$ (for $n = 2k$).
        - Dimension: $\frac{n(n-1)}{2}$.
        - Rank: $\lfloor n/2 \rfloor$.
        - Generators: $L_{ij} = E_{ij} - E_{ji}$ for $0 \le i < j < n$.

    Carrier & Invariants:
        - Field: Real numbers $\mathbb{R}$.
        - Semisimplicity: Semisimple for $n \ge 3$, abelian for $n = 2$.
    """
    if n < 2:
        raise ValueError('so(n) is only defined for n >= 2.')
    generators: list[SparseMatrix[int, float | complex]] = []
    default_names: list[str] = []
    for i in range(n):
        for j in range(i + 1, n):
            mat: SparseMatrix[int, float | complex] = {i: {j: 1.0}, j: {i: -1.0}}
            generators.append(mat)
            default_names.append(f'L_{{{i}{j}}}')
    return LieAlgebra.from_matrix_basis(generators, names=names if names is not None else default_names)


def sp_n(n: int, names: Sequence[str] | None = None) -> LieAlgebra:
    r"""The real symplectic Lie algebra sp(2n, R) preserving the standard symplectic form.

    Algebraic Signature:
        $\langle \mathfrak{sp}(2n, \mathbb{R}), [\cdot, \cdot], B \rangle$
        $X^T \Omega + \Omega X = 0, \quad \Omega = \begin{pmatrix} 0 & I_n \\ -I_n & 0 \end{pmatrix}$

    Cartan Classification:
        - Family: Simple Lie algebra of type $C_n$.
        - Dimension: $n(2n+1)$.
        - Rank: $n$.
        - Block Structure: Matrices $\begin{pmatrix} A & B \\ C & -A^T \end{pmatrix}$ with symmetric $B, C$.

    Carrier & Invariants:
        - Field: Real numbers $\mathbb{R}$.
        - Killing Form: Non-degenerate, split signature (semisimple).
    """
    if n < 1:
        raise ValueError('sp(2n) is only defined for n >= 1.')
    gens: list[SparseMatrix[int, float | complex]] = []
    default_names: list[str] = []
    for i in range(n):
        for j in range(n):
            gens.append({i: {j: 1.0}, n + j: {n + i: -1.0}})
            default_names.append(f'A_{{{i}{j}}}')
    for i in range(n):
        for j in range(i, n):
            if i == j:
                gens.append({i: {n + i: 1.0}})
                default_names.append(f'B_{{{i}{i}}}')
            else:
                gens.append({i: {n + j: 1.0}, j: {n + i: 1.0}})
                default_names.append(f'B_{{{i}{j}}}')
    for i in range(n):
        for j in range(i, n):
            if i == j:
                gens.append({n + i: {i: 1.0}})
                default_names.append(f'C_{{{i}{i}}}')
            else:
                gens.append({n + i: {j: 1.0}, n + j: {i: 1.0}})
                default_names.append(f'C_{{{i}{j}}}')
    return LieAlgebra.from_matrix_basis(gens, names=names if names is not None else default_names)


def sl_n(n: int, names: Sequence[str] | None = None) -> LieAlgebra:
    r"""The special linear Lie algebra sl(n, R) of n x n real traceless matrices.

    Algebraic Signature:
        $\langle \mathfrak{sl}(n, \mathbb{R}), [\cdot, \cdot], B \rangle \quad \mathrm{Tr}(X) = 0, \quad \dim = n^2 - 1$

    Cartan Classification:
        - Family: Simple Lie algebra of type $A_{n-1}$ (split real form).
        - Dimension: $n^2 - 1$.
        - Rank: $n - 1$.
    """
    if n < 2:
        raise ValueError('sl(n) is only defined for n >= 2.')
    gens: list[SparseMatrix[int, float | complex]] = []
    default_names: list[str] = []
    # 1. Off-diagonal generators: E_jk for j != k
    for j in range(n):
        for k in range(n):
            if j != k:
                gens.append({j: {k: 1.0}})
                default_names.append(f'E_{{{j}{k}}}')
    # 2. Diagonal traceless generators: E_kk - E_{k+1, k+1}
    for k in range(n - 1):
        gens.append({k: {k: 1.0}, k + 1: {k + 1: -1.0}})
        default_names.append(f'H_{k}')
    return LieAlgebra.from_matrix_basis(gens, names=names if names is not None else default_names)


def se_n(n: int, names: Sequence[str] | None = None) -> LieAlgebra:
    r"""The special Euclidean Lie algebra se(n) of n-dimensional rigid body motions.

    Algebraic Signature:
        $\langle \mathfrak{se}(n), [\cdot, \cdot] \rangle$
        $\mathfrak{se}(n) \cong \mathfrak{so}(n) \ltimes \mathbb{R}^n, \quad \dim = \frac{n(n+1)}{2}$

    Structure:
        - Rotational Subalgebra: $\mathfrak{so}(n)$ in top-left $n \times n$ block ($\binom{n}{2}$ generators).
        - Translational Ideal: Abelian $\mathbb{R}^n$ in $(n+1)$-th column ($n$ generators).
        - Semisimplicity: Non-semisimple ($\det K = 0$).
    """
    if n < 2:
        raise ValueError('se(n) is only defined for n >= 2.')
    gens: list[SparseMatrix[int, float | complex]] = []
    default_names: list[str] = []
    # 1. Rotations: E_jk - E_kj in top-left n x n
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: 1.0}, k: {j: -1.0}})
            default_names.append(f'J_{{{j}{k}}}')
    # 2. Translations: E_k, n in (n+1) x (n+1)
    for k in range(n):
        gens.append({k: {n: 1.0}})
        default_names.append(f'P_{k}')
    return LieAlgebra.from_matrix_basis(gens, names=names if names is not None else default_names)


def clifford_lie_algebra(
    clifford_or_p: CliffordSemiring | int,
    q: int = 0,
    r: int = 0,
) -> LieAlgebra:
    r"""Construct the Lie algebra formed by the bivector subspace of a Clifford algebra Cl(p, q, r).

    Algebraic Signature:
        $\langle \bigwedge^2 V, [\cdot, \cdot] \rangle$
        $[B_1, B_2] = \frac{1}{2} (B_1 B_2 - B_2 B_1), \quad \dim = \binom{n}{2}$
    """
    if isinstance(clifford_or_p, CliffordSemiring):
        cs = clifford_or_p
        total_dim = cs.p + cs.q + cs.r
    else:
        cs = CliffordSemiring(p=clifford_or_p, q=q, r=r)
        total_dim = clifford_or_p + q + r

    bivectors = list(itertools.combinations(range(total_dim), 2))
    dim = len(bivectors)
    bivector_to_idx = {b: i for i, b in enumerate(bivectors)}
    names = [f'e_{b[0]}{b[1]}' for b in bivectors]

    f_tensor: dict[tuple[int, int, int], float | complex] = {}

    for a in range(dim):
        for b in range(dim):
            ba_mv = {bivectors[a]: 1.0}
            bb_mv = {bivectors[b]: 1.0}
            prod_ab = cs.mul(ba_mv, bb_mv)
            prod_ba = cs.mul(bb_mv, ba_mv)
            all_blades = set(prod_ab.keys()) | set(prod_ba.keys())
            for blade in all_blades:
                val = 0.5 * (prod_ab.get(blade, 0.0) - prod_ba.get(blade, 0.0))
                if abs(val) > 1e-12 and blade in bivector_to_idx:
                    c = bivector_to_idx[blade]
                    f_tensor[(a, b, c)] = val

    sc = StructureConstants(dim=dim, tensor=f_tensor)
    return LieAlgebra(dim=dim, structure_constants=sc, basis_names=names)


__all__ = [
    'clifford_lie_algebra',
    'se_n',
    'sl_n',
    'so_n',
    'sp_n',
    'su_n',
    'u_n',
]
