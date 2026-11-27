r"""
Lie Algebra Representation Protocols, Highest-Weight Modules, Casimir Operators, and Exp Bridge.

Algebraic Signatures:
    Lie Representation:   $\rho : \mathfrak{g} \longrightarrow \mathfrak{gl}(V), \quad
                           \rho([X, Y]) = [\rho(X), \rho(Y)] = \rho(X)\rho(Y) - \rho(Y)\rho(X)$
    Tensor Product:       $(\rho_1 \otimes \rho_2)(X) = \rho_1(X) \otimes \mathbf{I} + \mathbf{I} \otimes \rho_2(X)$
    Contragredient Dual:  $\rho^*(X) = -\rho(X)^T$
    Quadratic Casimir:    $C = \sum_{i,j} g^{ij} \rho(X_i)\rho(X_j), \quad [C, \rho(X)] = \mathbf{0}$
    Freudenthal Formula:  $C|_{V_\Lambda} = \langle \Lambda, \Lambda + 2\delta \rangle_K \, \mathbf{I}$
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, Literal, Protocol, TypeVar, runtime_checkable

from algebrax.lie.classical import sl_n, su_n
from algebrax.lie.core import LieAlgebra, LieElement
from algebrax.lie.roots import RootSystem
from algebrax.matrix.core import add, dot, inverse, trace, transpose
from algebrax.rep.group import _prune_matrix, _scale_matrix
from algebrax.tensor.coupling import (
    clebsch_gordan_coefficient,
    clebsch_gordan_matrix,
    clebsch_gordan_tensor,
)
from algebrax.typing import SparseMatrix

K = TypeVar('K')


def _identity_matrix(dim: int) -> dict[int, dict[int, float]]:
    return {i: {i: 1.0} for i in range(dim)}


def _matrix_one_norm(mat: SparseMatrix[int, Any]) -> float:
    """Compute the induced 1-norm (maximum absolute column sum) of a sparse matrix."""
    col_sums: dict[int, float] = {}
    for row in mat.values():
        for c, val in row.items():
            col_sums[c] = col_sums.get(c, 0.0) + abs(complex(val))
    return max(col_sums.values(), default=0.0)


def _sparse_expm(
    mat: SparseMatrix[int, Any],
    dim: int,
    order: int = 18,
    tol: float = 1e-13,
) -> SparseMatrix[int, Any]:
    """Compute matrix exponential exp(A) via scaling-and-squaring with sparse Taylor series."""
    if dim <= 0:
        return {}
    if not mat:
        return _identity_matrix(dim)

    norm_a = _matrix_one_norm(mat)
    squarings = max(0, math.ceil(math.log2(norm_a / 0.5))) if norm_a > 0.5 else 0
    scaled = _scale_matrix(mat, 1.0 / (2**squarings), tol=tol) if squarings > 0 else mat

    acc: dict[int, dict[int, Any]] = _identity_matrix(dim)
    term: dict[int, dict[int, Any]] = _identity_matrix(dim)
    for k in range(1, order + 1):
        term = _prune_matrix(_scale_matrix(dot(term, scaled), 1.0 / k, tol=tol), tol=tol)
        if not term:
            break
        acc = _prune_matrix(add(acc, term), tol=tol)

    for _ in range(squarings):
        acc = _prune_matrix(dot(acc, acc), tol=tol)
    return acc


def _infer_matrix_dim(matrices: Sequence[SparseMatrix[int, Any]]) -> int:
    max_idx = -1
    for mat in matrices:
        for r, row in mat.items():
            max_idx = max(max_idx, r)
            for c in row:
                max_idx = max(max_idx, c)
    return max_idx + 1


def _normalize_weight_scalar(val: float | complex, tol: float) -> float | complex:
    c_val = complex(val)
    re = 0.0 if abs(c_val.real) <= tol else round(c_val.real, 9)
    im = 0.0 if abs(c_val.imag) <= tol else round(c_val.imag, 9)
    if im == 0.0:
        return float(re)
    return complex(re, im)


def _rref_nullspace(
    rows: list[list[complex]],
    n_cols: int,
    tol: float = 1e-9,
) -> list[list[complex]]:
    """Compute an orthonormal-normalized basis for the right nullspace of a small dense matrix."""
    if not rows:
        return [[1.0 + 0.0j if j == i else 0.0 + 0.0j for j in range(n_cols)] for i in range(n_cols)]

    mat = [list(r) for r in rows]
    n_rows = len(mat)
    pivot_cols: list[int] = []
    r_idx = 0

    for col in range(n_cols):
        if r_idx >= n_rows:
            break
        pivot_row = max(range(r_idx, n_rows), key=lambda i, c=col: abs(mat[i][c]))
        if abs(mat[pivot_row][col]) <= tol:
            continue
        mat[r_idx], mat[pivot_row] = mat[pivot_row], mat[r_idx]
        piv = mat[r_idx][col]
        mat[r_idx] = [v / piv for v in mat[r_idx]]
        for i in range(n_rows):
            if i != r_idx and abs(mat[i][col]) > tol:
                factor = mat[i][col]
                mat[i] = [mat[i][j] - factor * mat[r_idx][j] for j in range(n_cols)]
        pivot_cols.append(col)
        r_idx += 1

    pivot_set = set(pivot_cols)
    free_cols = [c for c in range(n_cols) if c not in pivot_set]
    basis: list[list[complex]] = []
    for free_c in free_cols:
        vec = [0.0 + 0.0j] * n_cols
        vec[free_c] = 1.0 + 0.0j
        for row_i, piv_c in enumerate(pivot_cols):
            vec[piv_c] = -mat[row_i][free_c]
        norm = math.sqrt(sum(abs(x) ** 2 for x in vec))
        if norm > tol:
            basis.append([x / norm for x in vec])
    return basis


@runtime_checkable
class LieRepresentation(Protocol[K]):
    r"""Protocol for a linear representation $\rho : \mathfrak{g} \to \mathfrak{gl}(V)$ over sparse matrices.

    Structurally conforms to `LieAlgebraHom[LieElement, SparseMatrix[int, K]]` with
    representation space dimension.

    Algebraic Signature:
        $\rho : \mathfrak{g} \longrightarrow \mathfrak{gl}_d(\mathbb{K}), \quad
        \rho([X, Y]) = [\rho(X), \rho(Y)]$
    """

    @property
    def dimension(self) -> int:
        """Dimension of the representation vector space $V$."""
        ...

    def __call__(self, x: LieElement) -> SparseMatrix[int, K]:
        r"""Evaluate the representation matrix $\rho(X)$ on a Lie algebra element $X \in \mathfrak{g}$."""
        ...


# Note: ExplicitLieRep conforms structurally to LieRepresentation[K] rather than subclassing
# the Protocol directly, because LieRepresentation.dimension is a read-only @property data
# descriptor that conflicts with @dataclass(frozen=True) field assignment.
@dataclass(frozen=True)
class ExplicitLieRep(Generic[K]):
    r"""Explicit finite-dimensional Lie algebra representation backed by sparse generator matrices.

    Algebraic Signature:
        $\rho : \mathfrak{g} \longrightarrow \mathfrak{gl}_d(\mathbb{K}), \quad
        X \longmapsto \sum_a X^a M_a \in \mathrm{SparseMatrix}[d \times d]$

    Attributes:
        algebra: Underlying `LieAlgebra` $\mathfrak{g}$.
        generator_matrices: Sequence of sparse matrices $[\rho(X_0), \dots, \rho(X_{\dim \mathfrak{g}-1})]$.
        dimension: Dimension $d = \dim V$ of the representation space.
    """

    algebra: LieAlgebra
    generator_matrices: Sequence[SparseMatrix[int, K]]
    dimension: int

    def __post_init__(self) -> None:
        if len(self.generator_matrices) != self.algebra.dim:
            raise ValueError(
                f'Expected {self.algebra.dim} generator matrices for LieAlgebra, '
                f'got {len(self.generator_matrices)}.'
            )
        if self.dimension <= 0:
            raise ValueError(f'Representation dimension must be positive, got {self.dimension}.')

    def generator_matrix(self, idx: int) -> SparseMatrix[int, K]:
        r"""Return the representation matrix $\rho(X_i)$ for basis generator index `idx`."""
        if not (0 <= idx < len(self.generator_matrices)):
            raise IndexError(
                f'Generator index {idx} out of range [0, {len(self.generator_matrices)}).'
            )
        return self.generator_matrices[idx]

    def __call__(
        self,
        element: LieElement | Sequence[float | complex] | Mapping[int | str, float | complex],
    ) -> SparseMatrix[int, Any]:
        r"""Evaluate $\rho(X) = \sum_a X^a \rho(X_a)$ for any Lie algebra element."""
        if isinstance(element, int):
            raise TypeError(
                'ExplicitLieRep.__call__ expects a LieElement (dict/sequence), not a bare int; '
                'use rep.generator_matrix(idx) or rep({idx: 1.0}) for a basis generator.'
            )
        coords = self.algebra._normalize_element(element)  # type: ignore[arg-type]
        acc: dict[int, dict[int, Any]] = {}
        for idx, coeff in coords.items():
            term = _scale_matrix(self.generator_matrices[idx], coeff)
            if term:
                acc = dict(add(acc, term))  # type: ignore[arg-type]
        return _prune_matrix(acc)

    def evaluate(
        self,
        element: LieElement | Sequence[float | complex] | Mapping[int | str, float | complex],
    ) -> SparseMatrix[int, Any]:
        r"""Evaluate $\rho(X) = \sum_a X^a \rho(X_a)$ for any Lie algebra coordinate or named vector."""
        return self(element)

    def exp_map(
        self,
        element: LieElement | Sequence[float | complex] | Mapping[int | str, float | complex],
        order: int = 18,
    ) -> SparseMatrix[int, Any]:
        r"""Bridge to the Lie group representation via the matrix exponential $\exp(\rho(X))$."""
        return _sparse_expm(self(element), self.dimension, order=order)

    def direct_sum(self, other: ExplicitLieRep[K]) -> ExplicitLieRep[K]:
        r"""Form the direct sum representation $(\rho_1 \oplus \rho_2)(X) = \mathrm{diag}(\rho_1(X), \rho_2(X))$."""
        return direct_sum_lie_rep([self, other])

    def tensor_product(self, other: ExplicitLieRep[K]) -> ExplicitLieRep[K]:
        r"""Form the Lie tensor product $(\rho_1 \otimes \rho_2)(X) = \rho_1(X) \otimes \mathbf{I}
        + \mathbf{I} \otimes \rho_2(X)$.
        """
        return tensor_product_lie_rep(self, other)

    def dual(self) -> ExplicitLieRep[K]:
        r"""Form the contragredient (dual) Lie representation $\rho^*(X) = -\rho(X)^T$."""
        dual_mats: list[SparseMatrix[int, Any]] = [
            _scale_matrix(transpose(mat), -1.0) for mat in self.generator_matrices
        ]
        return ExplicitLieRep(
            algebra=self.algebra,
            generator_matrices=tuple(dual_mats),
            dimension=self.dimension,
        )


def _rep_generator(rep: LieRepresentation[Any], idx: int) -> SparseMatrix[int, Any]:
    """Return representation matrix rho(X_idx) for a basis generator index."""
    if isinstance(rep, ExplicitLieRep):
        return rep.generator_matrix(idx)
    return rep({idx: 1.0})


def _same_lie_algebra(alg1: LieAlgebra, alg2: LieAlgebra, tol: float = 1e-12) -> bool:
    """Return True if two LieAlgebra instances have the same dimension and structure constants."""
    if alg1 is alg2:
        return True
    if alg1.dim != alg2.dim:
        return False
    t1 = alg1.structure_constants.tensor
    t2 = alg2.structure_constants.tensor
    for key in set(t1.keys()) | set(t2.keys()):
        if abs(complex(t1.get(key, 0.0)) - complex(t2.get(key, 0.0))) > tol:
            return False
    return True


def direct_sum_lie_rep(reps: Sequence[ExplicitLieRep[K]]) -> ExplicitLieRep[K]:
    r"""Construct the block-diagonal direct sum $\bigoplus_k \rho_k$ of Lie representations."""
    if not reps:
        raise ValueError('direct_sum_lie_rep requires at least one representation.')
    algebra = reps[0].algebra
    if any(not _same_lie_algebra(r.algebra, algebra) for r in reps[1:]):
        raise ValueError('All representations in direct_sum_lie_rep must share the same LieAlgebra.')

    dims = [r.dimension for r in reps]
    total_dim = sum(dims)
    gen_mats: list[SparseMatrix[int, K]] = []

    for gen_idx in range(algebra.dim):
        shifted: dict[int, dict[int, K]] = {}
        offset = 0
        for rep, dim in zip(reps, dims):
            for r_idx, row in rep.generator_matrix(gen_idx).items():
                shifted[r_idx + offset] = {c_idx + offset: val for c_idx, val in row.items()}
            offset += dim
        gen_mats.append(shifted)

    return ExplicitLieRep(algebra=algebra, generator_matrices=tuple(gen_mats), dimension=total_dim)


def tensor_product_lie_rep(
    rep_a: ExplicitLieRep[K],
    rep_b: ExplicitLieRep[K],
) -> ExplicitLieRep[K]:
    r"""Construct the Lie algebra tensor product $(\rho_a \otimes \rho_b)(X) =
    \rho_a(X) \otimes \mathbf{I}_{d_b} + \mathbf{I}_{d_a} \otimes \rho_b(X)$.

    Uses lexicographical basis index encoding $(i, j) \mapsto i \cdot d_b + j$.
    """
    if not _same_lie_algebra(rep_a.algebra, rep_b.algebra):
        raise ValueError('Representations in tensor_product_lie_rep must share the same LieAlgebra.')

    d_a = rep_a.dimension
    d_b = rep_b.dimension
    total_dim = d_a * d_b
    gen_mats: list[SparseMatrix[int, Any]] = []

    for gen_idx in range(rep_a.algebra.dim):
        ma = rep_a.generator_matrix(gen_idx)
        mb = rep_b.generator_matrix(gen_idx)
        combined: dict[int, dict[int, Any]] = {}

        # Term 1: rho_a(X) (x) I_{d_b}
        for r_a, row_a in ma.items():
            for j in range(d_b):
                out_row = combined.setdefault(r_a * d_b + j, {})
                for c_a, va in row_a.items():
                    col = c_a * d_b + j
                    out_row[col] = out_row.get(col, 0.0) + va

        # Term 2: I_{d_a} (x) rho_b(X)
        for i in range(d_a):
            base = i * d_b
            for r_b, row_b in mb.items():
                out_row = combined.setdefault(base + r_b, {})
                for c_b, vb in row_b.items():
                    col = base + c_b
                    out_row[col] = out_row.get(col, 0.0) + vb

        gen_mats.append(_prune_matrix(combined))

    return ExplicitLieRep(algebra=rep_a.algebra, generator_matrices=tuple(gen_mats), dimension=total_dim)


def trivial_lie_rep(algebra: LieAlgebra, dimension: int = 1) -> ExplicitLieRep[float]:
    r"""Construct the trivial Lie representation $\rho(X) = \mathbf{0}$ of dimension `dimension`."""
    mats: tuple[SparseMatrix[int, float], ...] = tuple({} for _ in range(algebra.dim))
    return ExplicitLieRep(algebra=algebra, generator_matrices=mats, dimension=dimension)


def adjoint_representation(algebra: LieAlgebra) -> ExplicitLieRep[float | complex]:
    r"""Construct the adjoint representation $\mathrm{ad}_X(Y) = [X, Y]$ delegating to `algebra.adjoint_matrix`."""
    mats = tuple(algebra.adjoint_matrix({i: 1.0}) for i in range(algebra.dim))
    return ExplicitLieRep(algebra=algebra, generator_matrices=mats, dimension=algebra.dim)


def defining_representation(
    algebra: LieAlgebra,
    dimension: int | None = None,
) -> ExplicitLieRep[float | complex]:
    r"""Wrap `algebra.matrix_basis` as an `ExplicitLieRep` without duplicating matrices."""
    if algebra.matrix_basis is None:
        raise ValueError('LieAlgebra does not carry a matrix_basis for defining_representation.')
    inferred_dim = _infer_matrix_dim(algebra.matrix_basis) if dimension is None else dimension
    return ExplicitLieRep(
        algebra=algebra,
        generator_matrices=tuple(algebra.matrix_basis),
        dimension=inferred_dim,
    )


def _spin_ladder_matrices(
    j_halves: int,
) -> tuple[dict[int, dict[int, float]], dict[int, dict[int, float]], dict[int, dict[int, float]]]:
    """Build Condon-Shortley ladder matrices (J_+, J_-, J_z) for spin j = j_halves / 2."""
    dim = j_halves + 1
    j_val = j_halves / 2.0
    j_plus: dict[int, dict[int, float]] = {}
    j_minus: dict[int, dict[int, float]] = {}
    j_z: dict[int, dict[int, float]] = {}

    for k in range(dim):
        m = j_val - k
        if abs(m) > 1e-14:
            j_z[k] = {k: m}
        if k > 0:
            coeff_up = math.sqrt((j_val - m) * (j_val + m + 1.0))
            if coeff_up > 1e-14:
                j_plus[k - 1] = {k: coeff_up}
        if k + 1 < dim:
            coeff_dn = math.sqrt((j_val + m) * (j_val - m + 1.0))
            if coeff_dn > 1e-14:
                j_minus[k + 1] = {k: coeff_dn}
    return j_plus, j_minus, j_z


def spin_representation(
    j_halves: int,
    *,
    form: Literal['su2', 'sl2'] = 'su2',
) -> ExplicitLieRep[complex]:
    r"""Construct the irreducible $(2j+1)$-dim spin-$j$ representation of $\mathfrak{su}(2)$ or $\mathfrak{sl}(2)$.

    Uses the standard Condon-Shortley basis $|j, m\rangle$ indexed in descending magnetic order
    $m = j, j-1, \dots, -j$:
    - `form='su2'` (default): matches `lie.su_n(2)` with skew-Hermitian generators
      $T_0 = \frac{1}{2}(J_+ - J_-)$, $T_1 = -\frac{i}{2}(J_+ + J_-)$, $T_2 = -i J_z$
      satisfying $[T_0, T_1] = T_2$, $[T_1, T_2] = T_0$, $[T_2, T_0] = T_1$.
    - `form='sl2'`: matches `lie.sl_n(2)` with Chevalley generators
      $E_{01} = J_+$, $E_{10} = J_-$, $H_0 = 2 J_z$
      satisfying $[H, E] = 2E$, $[H, F] = -2F$, $[E, F] = H$.

    Args:
        j_halves: Integer twice-spin $2j \in \mathbb{Z}_{\ge 0}$ (e.g., `1` for spin-$1/2$, `2` for spin-$1$).
        form: Real form `'su2'` (compact) or `'sl2'` (split Chevalley).

    Returns:
        Irreducible `ExplicitLieRep[complex]` of dimension `j_halves + 1`.
    """
    if not isinstance(j_halves, int) or isinstance(j_halves, bool) or j_halves < 0:
        raise ValueError(f'j_halves must be a non-negative integer (2j), got {j_halves!r}.')
    if form not in ('su2', 'sl2'):
        raise ValueError(f"form must be 'su2' or 'sl2', got {form!r}.")

    dim = j_halves + 1
    j_plus, j_minus, j_z = _spin_ladder_matrices(j_halves)

    if form == 'sl2':
        alg = sl_n(2)
        h_mat = _scale_matrix(j_z, 2.0)
        return ExplicitLieRep(
            algebra=alg,
            generator_matrices=(j_plus, j_minus, h_mat),
            dimension=dim,
        )

    alg = su_n(2)
    t0 = _prune_matrix(add(_scale_matrix(j_plus, 0.5), _scale_matrix(j_minus, -0.5)))
    t1 = _prune_matrix(add(_scale_matrix(j_plus, -0.5j), _scale_matrix(j_minus, -0.5j)))
    t2 = _prune_matrix(_scale_matrix(j_z, -1.0j))
    return ExplicitLieRep(
        algebra=alg,
        generator_matrices=(t0, t1, t2),
        dimension=dim,
    )


def _resolve_algebra(rep: LieRepresentation[Any], algebra: LieAlgebra | None) -> LieAlgebra:
    if algebra is not None:
        return algebra
    rep_alg = getattr(rep, 'algebra', None)
    if isinstance(rep_alg, LieAlgebra):
        return rep_alg
    raise ValueError('algebra must be supplied when rep does not expose an .algebra attribute.')


def is_lie_intertwiner(
    op: SparseMatrix[int, Any],
    rep1: LieRepresentation[Any],
    rep2: LieRepresentation[Any],
    algebra: LieAlgebra | None = None,
    tol: float = 1e-9,
) -> bool:
    r"""Check whether $T : V_1 \to V_2$ is a $\mathfrak{g}$-equivariant intertwiner ($T\rho_1(X) = \rho_2(X)T$)."""
    alg = _resolve_algebra(rep1, algebra)
    if algebra is None:
        rep2_alg = getattr(rep2, 'algebra', None)
        if isinstance(rep2_alg, LieAlgebra) and not _same_lie_algebra(alg, rep2_alg):
            raise ValueError('Representations in is_lie_intertwiner must share the same LieAlgebra.')
    for i in range(alg.dim):
        lhs = dot(op, _rep_generator(rep1, i))
        rhs = dot(_rep_generator(rep2, i), op)
        all_rows = set(lhs.keys()) | set(rhs.keys())
        for r in all_rows:
            row_l = lhs.get(r, {})
            row_r = rhs.get(r, {})
            for c in set(row_l.keys()) | set(row_r.keys()):
                if abs(complex(row_l.get(c, 0.0)) - complex(row_r.get(c, 0.0))) > tol:
                    return False
    return True


def _check_diagonal_cartan(mat: SparseMatrix[int, Any], gen_idx: int, tol: float) -> None:
    for r, row in mat.items():
        for c, val in row.items():
            if r != c and abs(complex(val)) > tol:
                raise ValueError(
                    f'Cartan generator index {gen_idx} is not diagonal at ({r}, {c})={val!r}; '
                    'weight_space_decomposition requires a diagonalized Cartan basis.'
                )


def weight_space_decomposition(
    rep: LieRepresentation[Any],
    cartan_indices: Sequence[int],
    tol: float = 1e-9,
) -> dict[tuple[float | complex, ...], list[dict[int, float]]]:
    r"""Decompose representation space $V = \bigoplus_\mu V_\mu$ into simultaneous Cartan weight spaces.

    Requires the Cartan generators $\rho(H_i)$ (`cartan_indices`) to be diagonal in the representation basis.

    Args:
        rep: Lie algebra representation $\rho : \mathfrak{g} \to \mathfrak{gl}(V)$.
        cartan_indices: Generator indices of the Cartan subalgebra $\mathfrak{h} \subset \mathfrak{g}$.
        tol: Numerical tolerance for verifying diagonality and grouping equal weight tuples.

    Returns:
        Mapping from weight tuple $\mu = (\mu(H_1), \dots, \mu(H_r))$ to list of sparse standard
        basis vectors spanning $V_\mu$.
    """
    if not cartan_indices:
        raise ValueError('cartan_indices must be a non-empty sequence of Cartan generator indices.')

    cartan_mats = [_rep_generator(rep, idx) for idx in cartan_indices]
    for idx, mat in zip(cartan_indices, cartan_mats):
        _check_diagonal_cartan(mat, idx, tol)

    spaces: dict[tuple[float | complex, ...], list[dict[int, float]]] = {}
    for basis_i in range(rep.dimension):
        weight = tuple(
            _normalize_weight_scalar(mat.get(basis_i, {}).get(basis_i, 0.0), tol) for mat in cartan_mats
        )
        spaces.setdefault(weight, []).append({basis_i: 1.0})
    return spaces


def _raising_subspace_rows(
    basis_indices: list[int],
    raising_mats: Sequence[SparseMatrix[int, Any]],
    tol: float,
) -> list[list[complex]]:
    """Assemble dense rows of stacked raising operators restricted to a single weight subspace."""
    col_map = {b_idx: pos for pos, b_idx in enumerate(basis_indices)}
    k = len(basis_indices)
    rows: list[list[complex]] = []
    for e_mat in raising_mats:
        for row_dict in e_mat.values():
            sub_row = [0.0 + 0.0j] * k
            non_zero = False
            for c_idx, val in row_dict.items():
                if c_idx in col_map and abs(complex(val)) > tol:
                    sub_row[col_map[c_idx]] = complex(val)
                    non_zero = True
            if non_zero:
                rows.append(sub_row)
    return rows


def highest_weight_vectors(
    rep: LieRepresentation[Any],
    cartan_indices: Sequence[int],
    raising_indices: Sequence[int],
    tol: float = 1e-9,
) -> list[tuple[tuple[float | complex, ...], dict[int, float | complex]]]:
    r"""Find all highest-weight vectors $v_\Lambda \in V_\Lambda$ satisfying $\rho(E_\alpha) v_\Lambda = \mathbf{0}$.

    Handles arbitrary weight space multiplicities (such as tensor products $V_{j_1} \otimes V_{j_2}$)
    by computing the simultaneous nullspace of all raising operators inside each weight space $V_\mu$.

    Args:
        rep: Lie algebra representation in a diagonalized Cartan basis.
        cartan_indices: Generator indices of the Cartan subalgebra $\mathfrak{h}$.
        raising_indices: Generator indices of the positive simple (or all positive) root vectors $E_\alpha$.
        tol: Numerical tolerance for weight equality and nullspace elimination.

    Returns:
        List of `(weight_tuple, sparse_vector)` pairs for every linearly independent highest-weight vector.
    """
    spaces = weight_space_decomposition(rep, cartan_indices, tol=tol)
    raising_mats = [_rep_generator(rep, idx) for idx in raising_indices]
    hw_vectors: list[tuple[tuple[float | complex, ...], dict[int, float | complex]]] = []

    for weight, basis_vecs in spaces.items():
        basis_indices = [next(iter(v.keys())) for v in basis_vecs]
        rows = _raising_subspace_rows(basis_indices, raising_mats, tol)
        null_basis = _rref_nullspace(rows, len(basis_indices), tol=tol)
        for coeffs in null_basis:
            sparse_vec: dict[int, float | complex] = {}
            for b_idx, c_val in zip(basis_indices, coeffs):
                if abs(c_val) > tol:
                    sparse_vec[b_idx] = c_val.real if abs(c_val.imag) <= tol else c_val
            if sparse_vec:
                hw_vectors.append((weight, sparse_vec))
    return hw_vectors


def quadratic_casimir(
    rep: LieRepresentation[K],
    algebra: LieAlgebra | None = None,
    killing_metric_inv: SparseMatrix[int, float | complex] | None = None,
    tol: float = 1e-12,
) -> SparseMatrix[int, Any]:
    r"""Compute the quadratic Casimir operator $C = \sum_{i, j} g^{ij} \rho(X_i)\rho(X_j)$.

    Defaults to the inverse Killing metric $g^{ij} = (K^{-1})_{ij}$ of `algebra`, which is
    basis-independent and satisfies $C|_{V_\Lambda} = \langle \Lambda, \Lambda + 2\delta \rangle_K \mathbf{I}$
    (e.g., $C = \frac{1}{2} j(j+1)\mathbf{I}$ on spin-$j$ of $\mathfrak{su}(2)/\mathfrak{sl}(2)$,
    and $C = \mathbf{I}$ on the adjoint representation of any simple Lie algebra). Passing a custom
    metric inverse (such as $g^{ij} = -\delta^{ij}$ for skew-Hermitian $\mathfrak{su}(2)$) yields
    the physics angular momentum Casimir $J^2 = j(j+1)\mathbf{I}$.

    Args:
        rep: Lie algebra representation $\rho$.
        algebra: Underlying `LieAlgebra` (inferred from `rep.algebra` if omitted).
        killing_metric_inv: Optional inverse invariant bilinear form $g^{ij}$.
        tol: Sparsity pruning tolerance.

    Returns:
        Sparse matrix representing the central Casimir operator $C$.
    """
    alg = _resolve_algebra(rep, algebra)
    if killing_metric_inv is None:
        if not alg.is_semisimple(tol=tol):
            raise ValueError(
                'Lie algebra Killing form is singular (not semisimple); '
                'provide an explicit killing_metric_inv to compute a quadratic Casimir.'
            )
        k_mat = alg.killing_matrix()
        try:
            g_inv: Mapping[int, Mapping[int, Any]] = inverse(k_mat, tol=tol)
        except ValueError as exc:
            raise ValueError(
                'Lie algebra Killing form is singular (not semisimple); '
                'provide an explicit killing_metric_inv to compute a quadratic Casimir.'
            ) from exc
    else:
        g_inv = killing_metric_inv

    acc: dict[int, dict[int, Any]] = {}
    for i, row in g_inv.items():
        rho_i = _rep_generator(rep, i)
        if not rho_i:
            continue
        for j, coeff in row.items():
            if abs(complex(coeff)) <= tol:
                continue
            rho_j = _rep_generator(rep, j)
            if not rho_j:
                continue
            prod = dot(rho_i, rho_j)
            if prod:
                term = _scale_matrix(prod, coeff, tol=tol)
                if term:
                    acc = dict(add(acc, term))  # type: ignore[arg-type]
    return _prune_matrix(acc, tol=tol)


def freudenthal_casimir_eigenvalue(
    root_system: RootSystem,
    highest_weight_dynkin: Sequence[int | float],
) -> float:
    r"""Compute Freudenthal's quadratic Casimir eigenvalue $\langle \Lambda, \Lambda + 2\delta \rangle_K$.

    Evaluates the exact Killing-form inner product on the weight lattice from the root system's
    Cartan Killing matrix $B_{ij} = \sum_{\alpha \in \Phi} \alpha(H_i)\alpha(H_j)$, where
    $\Lambda = (\Lambda(H_1), \dots, \Lambda(H_r))$ are the Dynkin labels and $\delta = (1, \dots, 1)$.

    Examples:
        - $A_1$ ($\mathfrak{sl}_2 / \mathfrak{su}_2$), $\Lambda = (2j)$: $\frac{1}{2} j(j+1)$.
        - $A_2$ ($\mathfrak{sl}_3$), fundamental $\Lambda = (1, 0)$: $\frac{4}{9}$; adjoint $\Lambda = (1, 1)$: $1$.

    Args:
        root_system: Simple `RootSystem` of rank $r$.
        highest_weight_dynkin: Sequence of $r$ Dynkin labels $\Lambda_i = \langle \Lambda, \alpha_i^\vee \rangle$.

    Returns:
        Exact scalar Casimir eigenvalue in the Killing-form normalization.
    """
    r = root_system.rank
    if len(highest_weight_dynkin) != r:
        raise ValueError(f'Expected {r} Dynkin labels for {root_system.dynkin_type}, got {len(highest_weight_dynkin)}.')
    if any(x < 0 for x in highest_weight_dynkin):
        raise ValueError(f'Highest-weight Dynkin labels must be non-negative, got {list(highest_weight_dynkin)!r}.')

    cartan = root_system.cartan_matrix
    b_cartan: dict[int, dict[int, float]] = {}
    for i in range(r):
        row_i: dict[int, float] = {}
        for j in range(r):
            val = 0.0
            for root in root_system.roots:
                ai = sum(root[k] * cartan[k][i] for k in range(r))
                aj = sum(root[k] * cartan[k][j] for k in range(r))
                val += float(ai * aj)
            if abs(val) > 1e-12:
                row_i[j] = val
        if row_i:
            b_cartan[i] = row_i

    b_inv = inverse(b_cartan, tol=1e-12)
    lam = [float(x) for x in highest_weight_dynkin]
    lam_plus_2rho = [x + 2.0 for x in lam]

    total = 0.0
    for i in range(r):
        row_i = b_inv.get(i, {})
        for j, inv_val in row_i.items():
            total += lam[i] * float(inv_val) * lam_plus_2rho[j]
    return total


def _raise_cubic_tensor_indices(
    d_lower: Mapping[tuple[int, int, int], float | complex],
    g_inv: Mapping[int, Mapping[int, Any]],
    tol: float,
) -> dict[tuple[int, int, int], float | complex]:
    """Raise all three indices of d_{abc} using inverse Killing metric g^{ia} g^{jb} g^{kc}."""
    # Factor three-stage sparse contraction: d_{abc} -> t1^{i}_{bc} -> t2^{ij}_{c} -> d^{ijk}
    t1: dict[tuple[int, int, int], complex] = {}
    for (a, b, c), val in d_lower.items():
        for i, row_i in g_inv.items():
            g_ia = row_i.get(a)
            if g_ia is not None:
                key = (i, b, c)
                t1[key] = t1.get(key, 0.0 + 0.0j) + complex(g_ia) * complex(val)

    t2: dict[tuple[int, int, int], complex] = {}
    for (i, b, c), val in t1.items():
        if abs(val) <= tol:
            continue
        for j, row_j in g_inv.items():
            g_jb = row_j.get(b)
            if g_jb is not None:
                key = (i, j, c)
                t2[key] = t2.get(key, 0.0 + 0.0j) + complex(g_jb) * val

    d_upper: dict[tuple[int, int, int], float | complex] = {}
    for (i, j, c), val in t2.items():
        if abs(val) <= tol:
            continue
        for k, row_k in g_inv.items():
            g_kc = row_k.get(c)
            if g_kc is not None:
                key = (i, j, k)
                prev = complex(d_upper.get(key, 0.0 + 0.0j))
                d_upper[key] = prev + complex(g_kc) * val

    cleaned: dict[tuple[int, int, int], float | complex] = {}
    for key, val in d_upper.items():
        c_val = complex(val)
        if abs(c_val) > tol:
            cleaned[key] = float(c_val.real) if abs(c_val.imag) <= tol else c_val
    return cleaned


def cubic_casimir_tensor(
    algebra: LieAlgebra,
    rep: LieRepresentation[Any] | None = None,
    tol: float = 1e-12,
) -> dict[tuple[int, int, int], float | complex]:
    r"""Compute the totally symmetric cubic invariant tensor:

    $$d_{ijk} = \operatorname{Tr}\!\bigl(\rho(X_i)\,(\rho(X_j)\rho(X_k) + \rho(X_k)\rho(X_j))\bigr)$$

    Defaults to `defining_representation(algebra)` when `algebra.matrix_basis` is present (and
    falls back to `adjoint_representation(algebra)` otherwise). Note that $d_{ijk}$ vanishes
    identically on self-dual representations (including the adjoint representation of any
    semisimple Lie algebra, as well as the defining representations of $\mathfrak{su}_2$,
    $\mathfrak{so}_n$, and $\mathfrak{sp}_n$), while being non-zero on the fundamental
    representation of $\mathfrak{sl}_n$ and $\mathfrak{su}_n$ for $n \ge 3$.

    Args:
        algebra: Underlying `LieAlgebra`.
        rep: Optional `LieRepresentation` on which to take the symmetrized cubic trace.
        tol: Sparsity pruning tolerance.

    Returns:
        Sparse dictionary mapping `(i, j, k) -> d_{ijk}` for all non-zero entries.
    """
    if rep is None:
        if algebra.matrix_basis is not None:
            active_rep: LieRepresentation[Any] = defining_representation(algebra)
        else:
            active_rep = adjoint_representation(algebra)
    else:
        active_rep = rep

    n = algebra.dim
    gens = [_rep_generator(active_rep, i) for i in range(n)]
    # Precompute pairwise products rho(X_j) rho(X_k) once for all j <= k
    prods: dict[tuple[int, int], SparseMatrix[int, Any]] = {}
    for j in range(n):
        if not gens[j]:
            continue
        for k in range(j, n):
            if not gens[k]:
                continue
            jk = _prune_matrix(dot(gens[j], gens[k]), tol=tol)
            kj = jk if j == k else _prune_matrix(dot(gens[k], gens[j]), tol=tol)
            anticomm = _prune_matrix(add(jk, kj), tol=tol)
            if anticomm:
                prods[(j, k)] = anticomm

    d_tensor: dict[tuple[int, int, int], float | complex] = {}
    for i in range(n):
        gi = gens[i]
        if not gi:
            continue
        for j in range(i, n):
            for k in range(j, n):
                anticomm = prods.get((j, k))
                if not anticomm:
                    continue
                raw = complex(trace(dot(gi, anticomm)))
                if abs(raw) <= tol:
                    continue
                val: float | complex = float(raw.real) if abs(raw.imag) <= tol else raw
                for perm in {(i, j, k), (i, k, j), (j, i, k), (j, k, i), (k, i, j), (k, j, i)}:
                    d_tensor[perm] = val
    return d_tensor


def cubic_casimir_operator(
    rep: LieRepresentation[K],
    algebra: LieAlgebra | None = None,
    d_tensor: Mapping[tuple[int, int, int], float | complex] | None = None,
    killing_metric_inv: SparseMatrix[int, float | complex] | None = None,
    tol: float = 1e-12,
) -> SparseMatrix[int, Any]:
    r"""Compute the central cubic Casimir operator $C_3 = \sum_{i,j,k} d^{ijk}\rho(X_i)\rho(X_j)\rho(X_k)$.

    Raises indices of the totally symmetric invariant tensor $d_{abc}$ via the inverse Killing
    metric $g^{ia} g^{jb} g^{kc}$. Commutes with all generators ($[C_3, \rho(X_m)] = \mathbf{0}$)
    and separates complex-conjugate irreps ($\mathbf{3}$ vs $\bar{\mathbf{3}}$ in $\mathfrak{sl}_3$
    and $\mathfrak{su}_3$) with opposite scalar eigenvalues $\pm\lambda_3 \mathbf{I}$.

    Args:
        rep: Lie algebra representation $\rho$.
        algebra: Underlying `LieAlgebra` (inferred from `rep.algebra` if omitted).
        d_tensor: Optional precomputed lower-index invariant 3-tensor $d_{abc}$.
        killing_metric_inv: Optional inverse invariant bilinear form $g^{ij}$.
        tol: Sparsity pruning tolerance.

    Returns:
        Sparse matrix representing the central cubic Casimir operator $C_3$.
    """
    alg = _resolve_algebra(rep, algebra)
    if killing_metric_inv is None:
        if not alg.is_semisimple(tol=tol):
            raise ValueError(
                'Lie algebra Killing form is singular (not semisimple); '
                'provide an explicit killing_metric_inv to compute a cubic Casimir operator.'
            )
        g_inv: Mapping[int, Mapping[int, Any]] = inverse(alg.killing_matrix(), tol=tol)
    else:
        g_inv = killing_metric_inv

    d_lower = cubic_casimir_tensor(alg, tol=tol) if d_tensor is None else d_tensor
    if not d_lower:
        return {}

    d_upper = _raise_cubic_tensor_indices(d_lower, g_inv, tol=tol)
    if not d_upper:
        return {}

    # Group non-zero triples by (i, j) so dot(rho_i, rho_j) is computed once per active pair
    by_ij: dict[tuple[int, int], list[tuple[int, float | complex]]] = {}
    for (i, j, k), coeff in d_upper.items():
        by_ij.setdefault((i, j), []).append((k, coeff))

    acc: dict[int, dict[int, Any]] = {}
    for (i, j), k_terms in by_ij.items():
        rho_i = _rep_generator(rep, i)
        rho_j = _rep_generator(rep, j)
        if not rho_i or not rho_j:
            continue
        ij_prod = _prune_matrix(dot(rho_i, rho_j), tol=tol)
        if not ij_prod:
            continue
        k_sum: dict[int, dict[int, Any]] = {}
        for k, coeff in k_terms:
            rho_k = _rep_generator(rep, k)
            if not rho_k:
                continue
            scaled_k = _scale_matrix(rho_k, coeff, tol=tol)
            if scaled_k:
                k_sum = dict(add(k_sum, scaled_k))  # type: ignore[arg-type]
        if k_sum:
            term = _prune_matrix(dot(ij_prod, k_sum), tol=tol)
            if term:
                acc = dict(add(acc, term))  # type: ignore[arg-type]
    return _prune_matrix(acc, tol=tol)


__all__ = [
    'ExplicitLieRep',
    'LieRepresentation',
    'adjoint_representation',
    'clebsch_gordan_coefficient',
    'clebsch_gordan_matrix',
    'clebsch_gordan_tensor',
    'cubic_casimir_operator',
    'cubic_casimir_tensor',
    'defining_representation',
    'direct_sum_lie_rep',
    'freudenthal_casimir_eigenvalue',
    'highest_weight_vectors',
    'is_lie_intertwiner',
    'quadratic_casimir',
    'spin_representation',
    'tensor_product_lie_rep',
    'trivial_lie_rep',
    'weight_space_decomposition',
]
