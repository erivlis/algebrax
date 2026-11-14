"""
Core Lie algebra abstractions, structure constants, and BCH dynamics.

Summary:
    Unified carrier class LieAlgebra, sparse rank-3 StructureConstants,
    adjoint representations, Killing forms, and Baker-Campbell-Hausdorff series.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias

from algebrax.algebra import NonAssocAlgebra
from algebrax.matrix import (
    commutator,
    frobenius_inner,
    inverse,
    mat_vec,
    vec_add,
    vec_axpy,
    vec_clean,
    vec_norm,
    vec_scale,
)
from algebrax.tensor import einsum
from algebrax.typing import SparseMatrix, SparseVector

LieElement: TypeAlias = SparseVector[int, float | complex]


class ConvergenceWarning(UserWarning):
    """Warning raised when BCH series inputs exceed the radius of convergence."""


def _verify_closure(
    basis_matrices: Sequence[SparseMatrix[int, float | complex]],
    comm: SparseMatrix[int, float | complex],
    f_ab: dict[int, float | complex],
    a: int,
    b: int,
    tol: float,
) -> None:
    recon: dict[int, dict[int, float | complex]] = {}
    for c, coeff in f_ab.items():
        if abs(coeff) > tol:
            for r, row in basis_matrices[c].items():
                if r not in recon:
                    recon[r] = {}
                for col, v in row.items():
                    recon[r][col] = recon[r].get(col, 0.0) + coeff * v

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
        res_norm = math.sqrt(abs(frobenius_inner(diff, diff)))
        if res_norm > tol:
            raise ValueError(
                f'Matrix basis is not closed under commutator bracket at indices ({a}, {b}); '
                f'residual norm: {res_norm:.4e}'
            )


def _matrix_gram_inverse(
    basis_matrices: Sequence[SparseMatrix[int, float | complex]],
    tol: float,
) -> SparseMatrix[int, float | complex]:
    """Compute the inverse of the Frobenius Gram matrix G_ij = <T_i, T_j>."""
    dim = len(basis_matrices)
    g: SparseMatrix[int, float | complex] = {}
    for i in range(dim):
        for j in range(dim):
            val = frobenius_inner(basis_matrices[i], basis_matrices[j])
            if abs(val) > tol:
                if i not in g:
                    g[i] = {}
                g[i][j] = val
    return inverse(g, tol=tol)


def _project_commutators(
    basis_matrices: Sequence[SparseMatrix[int, float | complex]],
    g_inv: SparseMatrix[int, float | complex],
    tol: float,
) -> dict[tuple[int, int, int], float | complex]:
    """Project all pairwise commutators [T_a, T_b] onto the basis using G^{-1}."""
    dim = len(basis_matrices)
    f_tensor: dict[tuple[int, int, int], float | complex] = {}
    for a in range(dim):
        for b in range(dim):
            comm = commutator(basis_matrices[a], basis_matrices[b])
            b_vec: dict[int, float | complex] = {}
            for k in range(dim):
                v_k = frobenius_inner(basis_matrices[k], comm)
                if abs(v_k) > tol:
                    b_vec[k] = v_k
            f_ab = mat_vec(g_inv, b_vec)
            _verify_closure(basis_matrices, comm, f_ab, a, b, tol)

            for c, coeff in f_ab.items():
                clean_c = coeff.real if abs(getattr(coeff, 'imag', 0.0)) < tol else coeff
                if abs(clean_c) > tol:
                    f_tensor[(a, b, c)] = clean_c
    return f_tensor


def _build_adjoint_blocks(
    dim: int,
    tensor: dict[tuple[int, int, int], float | complex],
) -> list[dict[int, dict[int, float | complex]]]:
    """Build per-generator adjoint index maps adj[a][c][d] = f_{ad}^c."""
    adj: list[dict[int, dict[int, float | complex]]] = [{} for _ in range(dim)]
    for (a, d, c), val in tensor.items():
        if c not in adj[a]:
            adj[a][c] = {}
        adj[a][c][d] = val
    return adj


def _killing_trace(
    mat_a: dict[int, dict[int, float | complex]],
    mat_b: dict[int, dict[int, float | complex]],
) -> float | complex:
    """Compute Tr(ad_{T_a} o ad_{T_b}) = sum_{c, d} f_{ad}^c f_{bc}^d."""
    tr: complex = 0.0 + 0.0j
    for c, row_c in mat_a.items():
        for d, val_acd in row_c.items():
            if d in mat_b and c in mat_b[d]:
                tr += val_acd * mat_b[d][c]
    return tr.real if abs(tr.imag) < 1e-12 else tr


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


class LieAlgebra(NonAssocAlgebra[float | complex, LieElement]):
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
        self._gram_inv: SparseMatrix[int, float | complex] | None = None
        if self.matrix_basis is not None:
            self._gram_inv = _matrix_gram_inverse(self.matrix_basis, tol=1e-12)

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

        try:
            g_inv = _matrix_gram_inverse(basis_matrices, tol=tol)
        except ValueError as e:
            raise ValueError(f'Matrix basis is singular or linearly dependent: {e}') from e

        f_tensor = _project_commutators(basis_matrices, g_inv, tol=tol)
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

    @property
    def zero(self) -> LieElement:
        """The additive zero vector (empty sparse dictionary)."""
        return {}

    def add(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
        b: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Vector addition: a + b."""
        return vec_clean(vec_add(self._normalize_element(a), self._normalize_element(b)))

    def neg(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Additive inverse (negation): -a."""
        return vec_clean(vec_scale(self._normalize_element(a), -1.0))

    def sub(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
        b: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Vector difference: a - b (single-pass axpy, avoiding double normalization)."""
        norm_a = self._normalize_element(a)
        norm_b = self._normalize_element(b)
        return vec_clean(vec_axpy(-1.0, norm_b, norm_a))

    def smul(
        self,
        r: float | complex,
        m: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Scalar multiplication: r * m."""
        return vec_clean(vec_scale(self._normalize_element(m), r))

    def mul(
        self,
        a: Sequence[float | complex] | dict[int | str, float | complex],
        b: Sequence[float | complex] | dict[int | str, float | complex],
    ) -> LieElement:
        """Non-associative bilinear product [a, b]. Alias for self.bracket(a, b)."""
        return self.bracket(a, b)

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
        return vec_clean(res)

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
        adj = _build_adjoint_blocks(dim, self.structure_constants.tensor)
        k_mat: dict[int, dict[int, float | complex]] = {}
        for a in range(dim):
            for b in range(a, dim):
                tr_val = _killing_trace(adj[a], adj[b])
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
        """Check Cartan's criterion for semisimplicity: Killing form matrix is non-degenerate."""
        k_mat = self.killing_matrix()
        if len(k_mat) < self.dim or any(i not in k_mat for i in range(self.dim)):
            return False
        try:
            inverse(k_mat, tol=tol)
        except ValueError:
            return False
        else:
            return True

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

        norm_x = vec_norm(x_norm)
        norm_y = vec_norm(y_norm)
        if norm_x + norm_y >= math.log(2.0):
            warnings.warn(
                f'BCH input norms ({norm_x + norm_y:.4f}) exceed convergence radius ln(2) ~= 0.69315',
                ConvergenceWarning,
                stacklevel=2,
            )

        # Order 1: X + Y
        res = vec_add(x_norm, y_norm)
        if order == 1:
            return vec_clean(res)

        # Order 2: + 1/2 [X, Y]
        xy = self.bracket(x_norm, y_norm)
        res = vec_axpy(0.5, xy, res)
        if order == 2:
            return vec_clean(res)

        # Order 3: + 1/12 [X, [X, Y]] - 1/12 [Y, [X, Y]]
        x_xy = self.bracket(x_norm, xy)
        y_xy = self.bracket(y_norm, xy)
        res = vec_axpy(1.0 / 12.0, x_xy, res)
        res = vec_axpy(-1.0 / 12.0, y_xy, res)
        if order == 3:
            return vec_clean(res)

        # Order 4: - 1/24 [Y, [X, [X, Y]]]
        y_x_xy = self.bracket(y_norm, x_xy)
        res = vec_axpy(-1.0 / 24.0, y_x_xy, res)

        return vec_clean(res)

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
        b_vec: dict[int, float | complex] = {}
        for k in range(dim):
            v_k = frobenius_inner(self.matrix_basis[k], mat)
            if abs(v_k) > 1e-12:
                b_vec[k] = v_k
        coords = mat_vec(self._gram_inv, b_vec)
        return {k: (v.real if abs(getattr(v, 'imag', 0.0)) < 1e-12 else v) for k, v in coords.items() if abs(v) > 1e-12}

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
            f'<strong>LieAlgebra</strong> (&dim; = {self.dim})<br>'
            f'Generators: {", ".join(self.basis_names)}<br>'
            f'Semisimple: <code>{self.is_semisimple()}</code>'
            f'</div>'
        )

    def __repr__(self) -> str:
        return f'LieAlgebra(dim={self.dim}, generators={self.basis_names})'


__all__ = [
    'ConvergenceWarning',
    'LieAlgebra',
    'LieElement',
    'StructureConstants',
]
