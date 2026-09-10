"""
Lie Algebras, Root Systems, and Baker-Campbell-Hausdorff Dynamics.

Summary:
    Continuous symmetry generators, structure constants tensors, commutator brackets,
    adjoint representations, Killing forms, and BCH geometric integration.

This module provides first-class support for finite-dimensional Lie algebras (g)
equipped with an alternating bilinear bracket [X, Y] satisfying the Jacobi identity.
Supports both real and complex matrix generators (e.g. so(3), sl(2), se(3), su(2), u(1)).
"""

from __future__ import annotations

import itertools
import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias

from algebrax.matrix.core import commutator
from algebrax.semiring.algebraic import CliffordSemiring
from algebrax.tensor import einsum
from algebrax.typing import SparseMatrix, SparseVector

LieElement: TypeAlias = SparseVector[int, float | complex]


class ConvergenceWarning(UserWarning):
    """Warning raised when BCH series inputs exceed the radius of convergence."""


def _frobenius_inner(
        a: SparseMatrix[int, float | complex],
        b: SparseMatrix[int, float | complex],
) -> float | complex:
    """Compute Frobenius inner product <A, B> = Tr(A^H @ B) = sum_{r,c} conj(A_{rc}) B_{rc}."""
    val: complex = 0.0 + 0.0j
    for r, row in a.items():
        if r in b:
            b_row = b[r]
            for c, v in row.items():
                if c in b_row:
                    v_conj = v.conjugate() if isinstance(v, complex) else v
                    val += v_conj * b_row[c]
    return val.real if abs(val.imag) < 1e-14 else val


def _invert_dense_matrix(
        mat: list[list[float | complex]],
        tol: float = 1e-12,
) -> list[list[float | complex]]:
    """Invert a dense n x n matrix using Gauss-Jordan elimination with partial pivoting."""
    n = len(mat)
    aug: list[list[complex]] = [
        [complex(x) for x in row] + [1.0 + 0.0j if i == j else 0.0 + 0.0j for j in range(n)]
        for i, row in enumerate(mat)
    ]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < tol:
            raise ValueError('Matrix is singular or linearly dependent.')
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        pv = aug[col][col]
        for c in range(col, 2 * n):
            aug[col][c] /= pv
        for r in range(n):
            if r != col:
                factor = aug[r][col]
                for c in range(col, 2 * n):
                    aug[r][c] -= factor * aug[col][c]
    return [[c.real if abs(c.imag) < tol else c for c in row[n:]] for row in aug]


def _matrix_det_dense(mat: list[list[float | complex]], tol: float = 1e-14) -> float | complex:
    """Compute determinant of a dense n x n matrix via Gaussian elimination with partial pivoting."""
    n = len(mat)
    a: list[list[complex]] = [[complex(x) for x in row] for row in mat]
    det: complex = 1.0 + 0.0j
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < tol:
            return 0.0
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            det = -det
        pv = a[col][col]
        det *= pv
        for r in range(col + 1, n):
            factor = a[r][col] / pv
            for c in range(col + 1, n):
                a[r][c] -= factor * a[col][c]
    return det.real if abs(det.imag) < tol else det


def _vec_add(u: LieElement, v: LieElement) -> LieElement:
    res = dict(u)
    for k, val in v.items():
        res[k] = res.get(k, 0.0) + val
    return res


def _vec_scale(u: LieElement, s: float | complex) -> LieElement:
    return {k: s * val for k, val in u.items() if abs(s * val) > 1e-14}


def _vec_norm(u: LieElement) -> float:
    """Compute Euclidean 2-norm ||X||_2 = sqrt(sum |x_i|^2) safe for complex vectors."""
    return math.sqrt(sum(abs(v) ** 2 for v in u.values()))


def _vec_clean(u: LieElement, tol: float = 1e-12) -> LieElement:
    res: dict[int, float | complex] = {}
    for k, v in u.items():
        if abs(v) > tol:
            res[k] = v.real if abs(v.imag) < tol else v
    return res


@dataclass(frozen=True)
class StructureConstants:
    r"""Sparse rank-3 tensor representing structure constants $f_{ab}^c$ for a Lie algebra.

    Algebraic Signature:
        $[T_a, T_b] = \sum_c f_{ab}^c T_c, \quad f_{ab}^c = -f_{ba}^c$

    Stored as coordinate 3-tuples `(a, b, c) -> value`.
    """

    dim: int
    tensor: dict[tuple[int, int, int], float | complex]

    def verify_antisymmetry(self, tol: float = 1e-12) -> bool:
        """Verify antisymmetry f_{ab}^c = -f_{ba}^c and f_{aa}^c = 0."""
        for (a, b, c), val in self.tensor.items():
            if a == b and abs(val) > tol:
                return False
            rev = self.tensor.get((b, a, c), 0.0)
            if abs(val + rev) > tol:
                return False
        return True

    def verify_jacobi(self, tol: float = 1e-12) -> bool:
        r"""Verify the Jacobi identity via einsum contraction over all basis triples:

        $\sum_k (f_{ab}^k f_{kc}^d + f_{bc}^k f_{ka}^d + f_{ca}^k f_{kb}^d) = 0$
        """
        if not self.tensor:
            return True

        t1 = einsum('abk,kcd->abcd', self.tensor, self.tensor)
        t2 = einsum('bck,kad->abcd', self.tensor, self.tensor)
        t3 = einsum('cak,kbd->abcd', self.tensor, self.tensor)

        jacobi_sum: dict[tuple[int, ...], float | complex] = {}
        for k, v in t1.items():
            jacobi_sum[k] = jacobi_sum.get(k, 0.0) + v
        for k, v in t2.items():
            jacobi_sum[k] = jacobi_sum.get(k, 0.0) + v
        for k, v in t3.items():
            jacobi_sum[k] = jacobi_sum.get(k, 0.0) + v

        return all(abs(val) <= tol for val in jacobi_sum.values())


class LieAlgebra:
    r"""Finite-dimensional Lie algebra equipped with an alternating bilinear bracket.

    Algebraic Signature:
        $\langle \mathfrak{g}, [\cdot, \cdot], B \rangle$
        $[X, Y] = -[Y, X], \quad [X, [Y, Z]] + [Y, [Z, X]] + [Z, [X, Y]] = 0$

    Represents a Lie algebra either through explicit structure constants $f_{ab}^c$
    or through a set of sparse matrix generators $T_a \in \mathfrak{gl}(n, \mathbb{C})$.
    """

    def __init__(
            self,
            dim: int,
            structure_constants: StructureConstants,
            basis_names: Sequence[str] | None = None,
            matrix_basis: Sequence[SparseMatrix[int, float | complex]] | None = None,
    ) -> None:
        self.dim = dim
        self.structure_constants = structure_constants
        self.basis_names = list(basis_names) if basis_names is not None else [f'T_{i}' for i in range(dim)]
        self._name_to_idx: dict[str, int] = {name: i for i, name in enumerate(self.basis_names)}
        self.matrix_basis = list(matrix_basis) if matrix_basis is not None else None
        self._gram_inv: list[list[float | complex]] | None = None
        if self.matrix_basis is not None:
            g = [[_frobenius_inner(self.matrix_basis[i], self.matrix_basis[j]) for j in range(dim)] for i in range(dim)]
            self._gram_inv = _invert_dense_matrix(g)

    @classmethod
    def from_matrix_basis(
            cls,
            basis_matrices: Sequence[SparseMatrix[int, float | complex]],
            names: Sequence[str] | None = None,
            tol: float = 1e-10,
    ) -> LieAlgebra:
        """Construct a LieAlgebra by projecting matrix commutators [A, B] = AB - BA onto the basis.

        Args:
            basis_matrices: Linearly independent sparse matrices spanning the Lie algebra.
            names: Optional human-readable basis generator names.
            tol: Tolerance for checking closure and linear independence.

        Returns:
            A LieAlgebra instance equipped with structure constants and matrix basis.

        Raises:
            ValueError: If the basis matrices are linearly dependent or not closed under commutator.
        """
        dim = len(basis_matrices)
        if dim == 0:
            raise ValueError('Cannot construct LieAlgebra from an empty basis.')

        g = [[_frobenius_inner(basis_matrices[i], basis_matrices[j]) for j in range(dim)] for i in range(dim)]
        g_inv = _invert_dense_matrix(g, tol=tol)

        f_tensor: dict[tuple[int, int, int], float | complex] = {}

        for a in range(dim):
            for b in range(dim):
                comm = commutator(basis_matrices[a], basis_matrices[b])
                b_vec = [_frobenius_inner(basis_matrices[k], comm) for k in range(dim)]
                f_ab = [sum(g_inv[k][j] * b_vec[j] for j in range(dim)) for k in range(dim)]

                # Verify closure: comm == sum_c f_ab^c basis_matrices[c]
                recon: dict[int, dict[int, float | complex]] = {}
                for c, coeff in enumerate(f_ab):
                    if abs(coeff) > tol:
                        for r, row in basis_matrices[c].items():
                            if r not in recon:
                                recon[r] = {}
                            for col, v in row.items():
                                recon[r][col] = recon[r].get(col, 0.0) + coeff * v

                # Residual difference comm - recon
                diff: dict[int, dict[int, float | complex]] = {}
                all_rows = set(comm.keys()) | set(recon.keys())
                for r in all_rows:
                    c_row = comm.get(r, {})
                    r_row = recon.get(r, {})
                    all_cols = set(c_row.keys()) | set(r_row.keys())
                    for col in all_cols:
                        delta = c_row.get(col, 0.0) - r_row.get(col, 0.0)
                        if abs(delta) > tol:
                            if r not in diff:
                                diff[r] = {}
                            diff[r][col] = delta

                if diff:
                    res_norm = math.sqrt(abs(_frobenius_inner(diff, diff)))
                    if res_norm > tol:
                        raise ValueError(
                            f'Matrix basis is not closed under commutator bracket at indices ({a}, {b}); '
                            f'residual norm: {res_norm:.4e}'
                        )

                for c, coeff in enumerate(f_ab):
                    if abs(coeff.imag) < tol:
                        coeff = coeff.real
                    if abs(coeff) > tol:
                        f_tensor[(a, b, c)] = coeff

        sc = StructureConstants(dim=dim, tensor=f_tensor)
        return cls(dim=dim, structure_constants=sc, basis_names=names, matrix_basis=basis_matrices)

    def _normalize_element(
            self,
            x: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Convert Sequence, int-keyed dict, or str-keyed dict into canonical SparseVector[int, float | complex]."""
        if isinstance(x, (list, tuple)):
            res_seq: dict[int, float | complex] = {}
            for i, v in enumerate(x):
                val = complex(v) if isinstance(v, complex) else float(v)
                if abs(val.imag) < 1e-14:
                    val = val.real
                if abs(val) > 1e-14:
                    res_seq[i] = val
            return res_seq
        res: dict[int, float | complex] = {}
        for k, v in x.items():
            if isinstance(k, str):
                if k not in self._name_to_idx:
                    raise KeyError(f"Unknown basis generator name '{k}'. Known: {self.basis_names}")
                idx = self._name_to_idx[k]
            else:
                idx = int(k)
            val = complex(v) if isinstance(v, complex) else float(v)
            if abs(val.imag) < 1e-14:
                val = val.real
            if abs(val) > 1e-14:
                res[idx] = res.get(idx, 0.0) + val
        return res

    def bracket(
            self,
            x: Sequence[float | complex] | dict[int | str, float | complex],
            y: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        r"""Compute the Lie bracket $[X, Y]^c = \sum_{a, b} f_{ab}^c X^a Y^b$.

        Args:
            x: First Lie algebra vector.
            y: Second Lie algebra vector.

        Returns:
            The bracket vector [X, Y] as a sparse coordinate mapping.
        """
        x_norm = self._normalize_element(x)
        y_norm = self._normalize_element(y)
        res: dict[int, float | complex] = {}
        for (a, b, c), fabc in self.structure_constants.tensor.items():
            xa = x_norm.get(a, 0.0)
            yb = y_norm.get(b, 0.0)
            if xa and yb:
                res[c] = res.get(c, 0.0) + fabc * xa * yb
        return _vec_clean(res)

    def adjoint_matrix(
            self,
            x: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> SparseMatrix[int, float | complex]:
        r"""Return the adjoint representation matrix $\mathrm{ad}_X$ where $(\mathrm{ad}_X)_c^b = \sum_a f_{ab}^c X^a$.

        Satisfies $(\mathrm{ad}_X Y)^c = [X, Y]^c$.
        """
        x_norm = self._normalize_element(x)
        mat: dict[int, dict[int, float | complex]] = {}
        for (a, b, c), fabc in self.structure_constants.tensor.items():
            xa = x_norm.get(a, 0.0)
            if xa:
                if c not in mat:
                    mat[c] = {}
                mat[c][b] = mat[c].get(b, 0.0) + fabc * xa
        return {c: {b: v for b, v in row.items() if abs(v) > 1e-12} for c, row in mat.items() if row}

    def killing_matrix(self) -> SparseMatrix[int, float | complex]:
        r"""Return the symmetric Killing form matrix $K_{ab} = \mathrm{Tr}(\mathrm{ad}_{T_a} \circ \mathrm{ad}_{T_b})$.

        Formula: $K_{ab} = \sum_{c, d} f_{ad}^c f_{bc}^d$.
        """
        dim = self.dim
        adj: list[dict[int, dict[int, float | complex]]] = [{} for _ in range(dim)]
        for (a, d, c), val in self.structure_constants.tensor.items():
            if c not in adj[a]:
                adj[a][c] = {}
            adj[a][c][d] = val

        k_mat: dict[int, dict[int, float | complex]] = {}
        for a in range(dim):
            for b in range(a, dim):
                tr: complex = 0.0 + 0.0j
                mat_a = adj[a]
                mat_b = adj[b]
                for c, row_c in mat_a.items():
                    for d, val_acd in row_c.items():
                        if d in mat_b and c in mat_b[d]:
                            tr += val_acd * mat_b[d][c]
                tr_val = tr.real if abs(tr.imag) < 1e-12 else tr
                if abs(tr_val) > 1e-12:
                    if a not in k_mat:
                        k_mat[a] = {}
                    k_mat[a][b] = tr_val
                    if b != a:
                        if b not in k_mat:
                            k_mat[b] = {}
                        k_mat[b][a] = tr_val
        return k_mat

    def killing_form(
            self,
            x: Sequence[float | complex] | dict[int | str, float | complex],
            y: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> float | complex:
        r"""Compute the Killing form bilinear product $B(X, Y) = \mathrm{Tr}(\mathrm{ad}_X \circ \mathrm{ad}_Y)$."""
        x_norm = self._normalize_element(x)
        y_norm = self._normalize_element(y)
        k_mat = self.killing_matrix()
        total: complex = 0.0 + 0.0j
        for a, xa in x_norm.items():
            if a in k_mat:
                row_a = k_mat[a]
                for b, yb in y_norm.items():
                    if b in row_a:
                        total += xa * yb * row_a[b]
        return total.real if abs(total.imag) < 1e-12 else total

    def is_semisimple(self, tol: float = 1e-10) -> bool:
        """Check Cartan's criterion for semisimplicity: det(Killing Matrix) != 0."""
        k_mat = self.killing_matrix()
        grid = [[k_mat.get(i, {}).get(j, 0.0) for j in range(self.dim)] for i in range(self.dim)]
        det = _matrix_det_dense(grid)
        return abs(det) > tol

    def bch(
            self,
            x: Sequence[float | complex] | dict[int | str, float | complex],
            y: Sequence[float | complex] | dict[int | str, float | complex],
            order: int = 4,
    ) -> LieElement:
        r"""Compute the Baker-Campbell-Hausdorff series $Z = \log(\exp(X)\exp(Y))$ up to specified order.

        Supported orders: $1 \le \text{order} \le 4$.
        - Order 1: $X + Y$
        - Order 2: $+ \frac{1}{2} [X, Y]$
        - Order 3: $+ \frac{1}{12} [X, [X, Y]] - \frac{1}{12} [Y, [X, Y]]$
        - Order 4: $- \frac{1}{24} [Y, [X, [X, Y]]]$

        Issues a `ConvergenceWarning` if $\|X\|_2 + \|Y\|_2 \ge \ln(2) \approx 0.69315$.
        """
        if order < 1 or order > 4:
            raise ValueError(f'BCH order must be between 1 and 4, got {order}.')

        x_norm = self._normalize_element(x)
        y_norm = self._normalize_element(y)

        norm_x = _vec_norm(x_norm)
        norm_y = _vec_norm(y_norm)
        if norm_x + norm_y >= math.log(2.0):
            warnings.warn(
                f'BCH input norms ({norm_x + norm_y:.4f}) exceed convergence radius ln(2) ~= 0.69315',
                ConvergenceWarning,
                stacklevel=2,
            )

        # Order 1: X + Y
        res = _vec_add(x_norm, y_norm)
        if order == 1:
            return _vec_clean(res)

        # Order 2: + 1/2 [X, Y]
        xy = self.bracket(x_norm, y_norm)
        res = _vec_add(res, _vec_scale(xy, 0.5))
        if order == 2:
            return _vec_clean(res)

        # Order 3: + 1/12 [X, [X, Y]] - 1/12 [Y, [X, Y]]
        x_xy = self.bracket(x_norm, xy)
        y_xy = self.bracket(y_norm, xy)
        res = _vec_add(res, _vec_scale(x_xy, 1.0 / 12.0))
        res = _vec_add(res, _vec_scale(y_xy, -1.0 / 12.0))
        if order == 3:
            return _vec_clean(res)

        # Order 4: - 1/24 [Y, [X, [X, Y]]]
        y_x_xy = self.bracket(y_norm, x_xy)
        res = _vec_add(res, _vec_scale(y_x_xy, -1.0 / 24.0))

        return _vec_clean(res)

    def element_to_matrix(
            self,
            x: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> SparseMatrix[int, float | complex]:
        """Convert a Lie algebra coordinate vector to its sparse matrix representation sum_a X^a T_a."""
        if self.matrix_basis is None:
            raise ValueError('Lie algebra was not initialized with a matrix basis.')
        x_norm = self._normalize_element(x)
        res: dict[int, dict[int, float | complex]] = {}
        for a, coeff in x_norm.items():
            if abs(coeff) < 1e-14 or a >= len(self.matrix_basis):
                continue
            mat = self.matrix_basis[a]
            for r, row in mat.items():
                if r not in res:
                    res[r] = {}
                for c, val in row.items():
                    res[r][c] = res[r].get(c, 0.0) + coeff * val
        return {r: {c: v for c, v in row.items() if abs(v) > 1e-12} for r, row in res.items() if row}

    def matrix_to_element(self, mat: SparseMatrix[int, float | complex]) -> LieElement:
        """Project a matrix representation back to Lie algebra coordinates."""
        if self.matrix_basis is None or self._gram_inv is None:
            raise ValueError('Lie algebra was not initialized with a matrix basis.')
        dim = self.dim
        b_vec = [_frobenius_inner(self.matrix_basis[k], mat) for k in range(dim)]
        coords = [sum(self._gram_inv[k][j] * b_vec[j] for j in range(dim)) for k in range(dim)]
        return {k: (v.real if abs(v.imag) < 1e-12 else v) for k, v in enumerate(coords) if abs(v) > 1e-12}

    def to_named(
            self,
            x: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> dict[str, float | complex]:
        """Convert a coordinate vector to human-readable generator name mappings."""
        x_norm = self._normalize_element(x)
        return {self.basis_names[k]: v for k, v in x_norm.items() if k < len(self.basis_names)}

    def _repr_latex_(self) -> str:
        names_str = ', '.join(self.basis_names[:6])
        if len(self.basis_names) > 6:
            names_str += ', \\dots'
        return f'$$\\mathfrak{{g}}: \\dim = {self.dim}, \\; \\text{{basis}} = \\{{{names_str}\\}}$$'

    def _repr_html_(self) -> str:
        return (
            f"<div style='border: 1px solid #8b5cf6; padding: 8px; border-radius: 4px;'>"
            f"<strong>LieAlgebra</strong> (&dim; = {self.dim})<br>"
            f"Generators: {', '.join(self.basis_names)}<br>"
            f'Semisimple: <code>{self.is_semisimple()}</code>'
            f'</div>'
        )

    def __repr__(self) -> str:
        return f'LieAlgebra(dim={self.dim}, generators={self.basis_names})'


def u_n(n: int) -> LieAlgebra:
    """The n^2-dimensional unitary Lie algebra u(n) of n x n skew-Hermitian matrices.

    Spanned by:
    - Skew-symmetric rotations: 0.5 * (E_jk - E_kj)
    - Symmetric imaginary matrices: -0.5i * (E_jk + E_kj)
    - Diagonal imaginary matrices: -0.5i * E_kk
    """
    if n < 1:
        raise ValueError('u(n) is only defined for n >= 1.')
    gens: list[SparseMatrix[int, float | complex]] = []
    names: list[str] = []
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: 0.5}, k: {j: -0.5}})
            names.append(f'A_{{{j}{k}}}')
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: -0.5j}, k: {j: -0.5j}})
            names.append(f'S_{{{j}{k}}}')
    for k in range(n):
        gens.append({k: {k: -0.5j}})
        names.append(f'D_{k}')
    return LieAlgebra.from_matrix_basis(gens, names=names)


def su_n(n: int) -> LieAlgebra:
    """The (n^2 - 1)-dimensional special unitary Lie algebra su(n) of n x n traceless skew-Hermitian matrices.

    Spanned by:
    - Skew-symmetric rotations: 0.5 * (E_jk - E_kj)
    - Symmetric imaginary matrices: -0.5i * (E_jk + E_kj)
    - Diagonal traceless imaginary matrices: -0.5i * (sum_{m < k} E_mm - k E_kk)
    """
    if n < 2:
        raise ValueError('su(n) is only defined for n >= 2.')
    gens: list[SparseMatrix[int, float | complex]] = []
    names: list[str] = []
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: 0.5}, k: {j: -0.5}})
            names.append(f'A_{{{j}{k}}}')
    for j in range(n):
        for k in range(j + 1, n):
            gens.append({j: {k: -0.5j}, k: {j: -0.5j}})
            names.append(f'S_{{{j}{k}}}')
    for k in range(1, n):
        diag: dict[int, dict[int, float | complex]] = {}
        for m in range(k):
            diag[m] = {m: -0.5j}
        diag[k] = {k: 0.5j * k}
        gens.append(diag)
        names.append(f'D_{k}')
    return LieAlgebra.from_matrix_basis(gens, names=names)


def sp_n(n: int) -> LieAlgebra:
    """The n(2n+1)-dimensional symplectic Lie algebra sp(2n, R) preserving the standard symplectic form.

    Represented as 2n x 2n matrices with block structure [[A, B], [C, -A^T]] where B and C are symmetric.
    """
    if n < 1:
        raise ValueError('sp(2n) is only defined for n >= 1.')
    gens: list[SparseMatrix[int, float | complex]] = []
    names: list[str] = []
    # Block A: E_ij in top-left, -E_ji in bottom-right
    for i in range(n):
        for j in range(n):
            gens.append({i: {j: 1.0}, n + j: {n + i: -1.0}})
            names.append(f'A_{{{i}{j}}}')
    # Block B (symmetric): top-right
    for i in range(n):
        for j in range(i, n):
            if i == j:
                gens.append({i: {n + i: 1.0}})
                names.append(f'B_{{{i}{i}}}')
            else:
                gens.append({i: {n + j: 1.0}, j: {n + i: 1.0}})
                names.append(f'B_{{{i}{j}}}')
    # Block C (symmetric): bottom-left
    for i in range(n):
        for j in range(i, n):
            if i == j:
                gens.append({n + i: {i: 1.0}})
                names.append(f'C_{{{i}{i}}}')
            else:
                gens.append({n + i: {j: 1.0}, n + j: {i: 1.0}})
                names.append(f'C_{{{i}{j}}}')
    return LieAlgebra.from_matrix_basis(gens, names=names)


def so_n(n: int) -> LieAlgebra:
    """The n(n-1)/2-dimensional special orthogonal algebra so(n) of n x n skew-symmetric matrices.

    Generators L_{ij} = E_{ij} - E_{ji}.
    """
    if n < 2:
        raise ValueError('so(n) is only defined for n >= 2.')
    generators: list[SparseMatrix[int, float | complex]] = []
    names: list[str] = []
    for i in range(n):
        for j in range(i + 1, n):
            mat: SparseMatrix[int, float | complex] = {i: {j: 1.0}, j: {i: -1.0}}
            generators.append(mat)
            names.append(f'L_{{{i}{j}}}')
    return LieAlgebra.from_matrix_basis(generators, names=names)


def su2() -> LieAlgebra:
    r"""The special unitary algebra su(2) of 2x2 skew-Hermitian traceless matrices.

    Generators J_k = -i/2 * sigma_k satisfying [J_x, J_y] = J_z, [J_y, J_z] = J_x, [J_z, J_x] = J_y.
    Isomorphic to so(3) as a real Lie algebra with real structure constants.
    """
    jx: SparseMatrix[int, complex] = {0: {1: -0.5j}, 1: {0: -0.5j}}
    jy: SparseMatrix[int, complex] = {0: {1: -0.5}, 1: {0: 0.5}}
    jz: SparseMatrix[int, complex] = {0: {0: -0.5j}, 1: {1: 0.5j}}
    return LieAlgebra.from_matrix_basis([jx, jy, jz], names=['J_x', 'J_y', 'J_z'])


def u1() -> LieAlgebra:
    """The 1-dimensional abelian unitary algebra u(1)."""
    t: SparseMatrix[int, complex] = {0: {0: 1.0j}}
    return LieAlgebra.from_matrix_basis([t], names=['T'])


def so3() -> LieAlgebra:
    """The 3D spatial rotation algebra so(3) spanned by {J_x, J_y, J_z}.

    Isomorphic to R^3 equipped with standard vector cross products [u, v] = u x v.
    """
    jx: SparseMatrix[int, float] = {1: {2: -1.0}, 2: {1: 1.0}}
    jy: SparseMatrix[int, float] = {0: {2: 1.0}, 2: {0: -1.0}}
    jz: SparseMatrix[int, float] = {0: {1: -1.0}, 1: {0: 1.0}}
    return LieAlgebra.from_matrix_basis([jx, jy, jz], names=['J_x', 'J_y', 'J_z'])


def sl2() -> LieAlgebra:
    """The special linear algebra sl(2, R) of traceless 2x2 matrices spanned by {e, f, h}.

    Commutators: [e, f] = h, [h, e] = 2e, [h, f] = -2f.
    """
    e: SparseMatrix[int, float] = {0: {1: 1.0}}
    f: SparseMatrix[int, float] = {1: {0: 1.0}}
    h: SparseMatrix[int, float] = {0: {0: 1.0}, 1: {1: -1.0}}
    return LieAlgebra.from_matrix_basis([e, f, h], names=['e', 'f', 'h'])


def se3() -> LieAlgebra:
    """The special Euclidean kinematics algebra se(3) of rigid body motions in 3D.

    Dimension 6: 3 rotational generators {J_x, J_y, J_z} and 3 translation generators {P_x, P_y, P_z}.
    """
    jx: SparseMatrix[int, float] = {1: {2: -1.0}, 2: {1: 1.0}}
    jy: SparseMatrix[int, float] = {0: {2: 1.0}, 2: {0: -1.0}}
    jz: SparseMatrix[int, float] = {0: {1: -1.0}, 1: {0: 1.0}}
    px: SparseMatrix[int, float] = {0: {3: 1.0}}
    py: SparseMatrix[int, float] = {1: {3: 1.0}}
    pz: SparseMatrix[int, float] = {2: {3: 1.0}}
    return LieAlgebra.from_matrix_basis([jx, jy, jz, px, py, pz], names=['J_x', 'J_y', 'J_z', 'P_x', 'P_y', 'P_z'])


def clifford_lie_algebra(
        clifford_or_p: CliffordSemiring | int,
        q: int = 0,
        r: int = 0,
) -> LieAlgebra:
    """Construct the Lie algebra formed by the bivector subspace of a Clifford algebra Cl(p, q, r).

    Commutator bracket: [B_1, B_2] = 1/2 (B_1 B_2 - B_2 B_1).
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


def _fano_3form_equations(so7_basis: list[tuple[int, int]]) -> list[list[float]]:
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

    eqs: list[list[float]] = []
    for i, j, k in itertools.combinations(range(7), 3):
        row: list[float] = []
        for p, q in so7_basis:
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
            row.append(coeff)
        if any(abs(c) > 1e-12 for c in row):
            eqs.append(row)
    return eqs


def _solve_nullspace(matrix: list[list[float]], num_cols: int, tol: float = 1e-10) -> list[list[float]]:
    a_mat = [row[:] for row in matrix]
    pivots: list[int] = []
    col = 0
    for r in range(len(a_mat)):
        if col >= num_cols:
            break
        pivot_r = max(range(r, len(a_mat)), key=lambda idx: abs(a_mat[idx][col]))
        while abs(a_mat[pivot_r][col]) < tol:
            col += 1
            if col >= num_cols:
                break
            pivot_r = max(range(r, len(a_mat)), key=lambda idx: abs(a_mat[idx][col]))
        if col >= num_cols:
            break
        a_mat[r], a_mat[pivot_r] = a_mat[pivot_r], a_mat[r]
        pv = a_mat[r][col]
        for c in range(col, num_cols):
            a_mat[r][c] /= pv
        for idx in range(len(a_mat)):
            if idx != r:
                factor = a_mat[idx][col]
                for c in range(col, num_cols):
                    a_mat[idx][c] -= factor * a_mat[r][c]
        pivots.append(col)
        col += 1

    free_cols = [c for c in range(num_cols) if c not in pivots]
    null_basis: list[list[float]] = []
    for fc in free_cols:
        vec = [0.0] * num_cols
        vec[fc] = 1.0
        for r, pc in enumerate(pivots):
            vec[pc] = -a_mat[r][fc]
        null_basis.append(vec)
    return null_basis


def g2() -> LieAlgebra:
    """The 14-dimensional exceptional Lie algebra G₂.

    Realized as the derivation algebra of the octonions Der(O), represented by
    14 sparse 7x7 skew-symmetric matrices preserving the associative 3-form.
    """
    so7_basis = [(p, q) for p in range(7) for q in range(p + 1, 7)]
    eqs = _fano_3form_equations(so7_basis)
    null_basis = _solve_nullspace(eqs, num_cols=21)

    g2_matrices: list[SparseMatrix[int, float | complex]] = []
    for vec in null_basis:
        mat: SparseMatrix[int, float | complex] = {}
        for idx, (p, q) in enumerate(so7_basis):
            coeff = vec[idx]
            if abs(coeff) > 1e-12:
                if p not in mat:
                    mat[p] = {}
                if q not in mat:
                    mat[q] = {}
                mat[p][q] = mat[p].get(q, 0.0) + coeff
                mat[q][p] = mat[q].get(p, 0.0) - coeff
        g2_matrices.append(mat)

    return LieAlgebra.from_matrix_basis(g2_matrices, names=[f'G_{i}' for i in range(14)])


def f4() -> LieAlgebra:
    """The exceptional Lie algebra F₄ of dimension 52."""
    raise NotImplementedError(
        'F₄ (dimension 52) exceptional algebra is planned for Phase 4 via root-system Chevalley generators.'
    )

def e6() -> LieAlgebra:
    """The exceptional Lie algebra E₆ of dimension 78."""
    raise NotImplementedError(
        'E₆ (dimension 78) exceptional algebra is planned for Phase 4 via root-system Chevalley generators.'
    )

def e7() -> LieAlgebra:
    """The exceptional Lie algebra E₇ of dimension 133."""
    raise NotImplementedError(
        'E₇ (dimension 133) exceptional algebra is planned for Phase 4 via root-system Chevalley generators.'
    )

def e8() -> LieAlgebra:
    """The exceptional Lie algebra E₈ of dimension 248."""
    raise NotImplementedError(
        'E₈ (dimension 248) exceptional algebra is planned for Phase 4 via the E₈ root lattice.'
    )


__all__ = [
    'ConvergenceWarning',
    'LieAlgebra',
    'LieElement',
    'StructureConstants',
    'clifford_lie_algebra',
    'e8',
    'f4',
    'g2',
    'se3',
    'sl2',
    'so3',
    'so_n',
    'sp_n',
    'su2',
    'su_n',
    'u1',
    'u_n',
]
