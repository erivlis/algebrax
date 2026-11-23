r"""
Quantum Groups, Yang-Baxter Equation & Braided Categories.

Implements the non-cocommutative Drinfeld-Jimbo quantum group $U_q(\mathfrak{sl}_2)$ as a
concrete `HopfAlgebra` over an unboxed PBW basis, its finite-dimensional $q$-deformed spin-$j$
representations, the fundamental $4 \times 4$ universal $R$-matrix solving the Quantum
Yang-Baxter Equation (QYBE), Artin braid group representations, quantum trace, and the
Jones polynomial invariant of knots and links via the Reshetikhin-Turaev functor.

Algebraic Signatures:
    Quantum Group:        $K E K^{-1} = q^2 E,\quad K F K^{-1} = q^{-2} F,\quad
                           [E, F] = \dfrac{K - K^{-1}}{q - q^{-1}}$
    Non-cocommutative:    $\Delta(E) = E \otimes 1 + K \otimes E,\quad
                           \Delta(F) = F \otimes K^{-1} + 1 \otimes F,\quad
                           \Delta(K) = K \otimes K$
    Non-involutive S:     $S(E) = -K^{-1} E,\quad S(F) = -F K,\quad S(K) = K^{-1}$
    Yang-Baxter (QYBE):   $R_{12} R_{13} R_{23} = R_{23} R_{13} R_{12}$
    Braiding Operator:    $B = P \circ R,\quad B_1 B_2 B_1 = B_2 B_1 B_2$
    Jones Polynomial:     $V_L(t)\big|_{t = q^{-2}} = (-1)^{n - 1 + w(\beta)} q^{-2 w(\beta)}
                           \dfrac{\mathrm{Tr}_q(\rho(\beta))}{q + q^{-1}}$
"""

from __future__ import annotations

import cmath
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from algebrax.algebra._hopf import HopfAlgebra
from algebrax.matrix.core import dot
from algebrax.rep.group import _prune_matrix
from algebrax.typing import SparseMatrix, SparseVector

PBWKey = tuple[int, int, int]
QuantumElement = SparseVector[PBWKey, complex]
TensorElement = dict[tuple[PBWKey, PBWKey], complex]

__all__ = [
    'PBWKey',
    'QuantumElement',
    'QuantumSL2',
    'TensorElement',
    'braid_to_matrix',
    'braiding_operator',
    'jones_polynomial_eval',
    'quantum_trace',
    'universal_r_matrix_sl2_fundamental',
]


def _validate_q(q: complex) -> complex:
    """Validate that deformation parameter q is finite and non-zero."""
    qc = complex(q)
    if not (math.isfinite(qc.real) and math.isfinite(qc.imag)):
        raise ValueError(f'Quantum deformation parameter q must be finite, got {q!r}.')
    if abs(qc) <= 1e-15:
        raise ValueError('Quantum deformation parameter q must be non-zero.')
    return qc


def _q_bracket_val(q: complex, n: int) -> complex:
    r"""Evaluate the symmetric $q$-integer $[n]_q = (q^n - q^{-n}) / (q - q^{-1})$ smoothly at $q = \pm 1$."""
    if n == 0:
        return 0.0 + 0.0j
    if abs(q - 1.0) < 1e-12:
        return complex(n)
    if abs(q + 1.0) < 1e-12:
        return complex(((-1) ** (n - 1)) * n)
    return (q**n - q ** (-n)) / (q - 1.0 / q)


def _prune_vector(vec: Mapping[PBWKey, complex], tol: float = 1e-13) -> dict[PBWKey, complex]:
    """Remove near-zero entries from a sparse PBW vector."""
    return {k: complex(v) for k, v in vec.items() if abs(v) > tol}


def _prune_tensor(
    tensor: Mapping[tuple[PBWKey, PBWKey], complex],
    tol: float = 1e-13,
) -> TensorElement:
    """Remove near-zero entries from a sparse tensor-product element."""
    return {k: complex(v) for k, v in tensor.items() if abs(v) > tol}


def _sparse_identity(dim: int) -> SparseMatrix[int, complex]:
    """Construct an unboxed sparse complex identity matrix of size dim x dim."""
    return {i: {i: 1.0 + 0.0j} for i in range(dim)}


def _sparse_mat_mul(
    a: SparseMatrix[int, complex],
    b: SparseMatrix[int, complex],
    tol: float = 1e-13,
) -> SparseMatrix[int, complex]:
    """Multiply two sparse complex matrices and prune near-zero entries."""
    return _prune_matrix(dot(a, b), tol=tol)


def _sparse_mat_pow(
    mat: SparseMatrix[int, complex],
    exp: int,
    dim: int,
    tol: float = 1e-13,
) -> SparseMatrix[int, complex]:
    """Compute mat ** exp for non-negative integer exp via binary exponentiation."""
    result = _sparse_identity(dim)
    base = mat
    power = exp
    while power > 0:
        if power & 1:
            result = _sparse_mat_mul(result, base, tol=tol)
        power >>= 1
        if power > 0:
            base = _sparse_mat_mul(base, base, tol=tol)
    return result


def _embed_two_site_operator(
    op: SparseMatrix[int, complex],
    site: int,
    num_strands: int,
    dim: int = 2,
    tol: float = 1e-13,
) -> SparseMatrix[int, complex]:
    """Embed a dim^2 x dim^2 sparse operator on adjacent strands (site, site + 1) in V^{tensor n}."""
    left_dim = dim**site
    right_dim = dim ** (num_strands - site - 2)
    block_dim = dim * dim
    out: dict[int, dict[int, complex]] = {}

    for r_op, row in op.items():
        for c_op, val in row.items():
            cval = complex(val)
            if abs(cval) <= tol:
                continue
            for left_idx in range(left_dim):
                row_prefix = (left_idx * block_dim + r_op) * right_dim
                col_prefix = (left_idx * block_dim + c_op) * right_dim
                for right_idx in range(right_dim):
                    r_full = row_prefix + right_idx
                    c_full = col_prefix + right_idx
                    out.setdefault(r_full, {})[c_full] = cval

    return out


def _embed_r13_operator(
    r_matrix: SparseMatrix[int, complex],
    dim: int = 2,
    tol: float = 1e-13,
) -> SparseMatrix[int, complex]:
    """Embed R_{13} acting on factors (1, 3) of V^{tensor 3} directly in sparse coordinates."""
    out: dict[int, dict[int, complex]] = {}
    for r_op, row in r_matrix.items():
        i, k = divmod(r_op, dim)
        for c_op, val in row.items():
            cval = complex(val)
            if abs(cval) <= tol:
                continue
            i_prime, k_prime = divmod(c_op, dim)
            for j in range(dim):
                r_full = (i * dim + j) * dim + k
                c_full = (i_prime * dim + j) * dim + k_prime
                out.setdefault(r_full, {})[c_full] = cval
    return out


@dataclass
class QuantumSL2(HopfAlgebra[complex, QuantumElement]):
    r"""Drinfeld-Jimbo quantum enveloping algebra $U_q(\mathfrak{sl}_2)$ as a `HopfAlgebra`.

    Elements are represented over the Poincare-Birkhoff-Witt (PBW) ordered basis
    $\{E^a K^b F^c \mid a, c \in \mathbb{Z}_{\ge 0},\; b \in \mathbb{Z}\}$ as unboxed sparse
    dictionaries `dict[tuple[int, int, int], complex]` mapping `(a, b, c) -> coeff`.

    Unlike group algebras and classical enveloping algebras, $U_q(\mathfrak{sl}_2)$ is
    genuinely non-commutative, non-cocommutative ($\Delta \neq \Delta^{\mathrm{op}}$), and
    possesses a non-involutive antipode ($S^2(E) = q^{-2} E \neq E$ for $q^2 \neq 1$).
    """

    q: complex
    tol: float = 1e-13

    def __post_init__(self) -> None:
        self.q = _validate_q(self.q)

    def q_bracket(self, n: int) -> complex:
        r"""Compute the symmetric $q$-number $[n]_q = (q^n - q^{-n}) / (q - q^{-1})$."""
        return _q_bracket_val(self.q, n)

    def q_factorial(self, n: int) -> complex:
        r"""Compute the $q$-factorial $[n]_q! = \prod_{k=1}^{n} [k]_q$ for $n \ge 0$."""
        if n < 0:
            raise ValueError(f'q_factorial requires n >= 0, got {n}.')
        acc = 1.0 + 0.0j
        for k in range(1, n + 1):
            acc *= self.q_bracket(k)
        return acc

    def q_binomial(self, n: int, k: int) -> complex:
        r"""Compute the Gaussian $q$-binomial coefficient $\binom{n}{k}_q$."""
        if n < 0:
            raise ValueError(f'q_binomial requires n >= 0, got {n}.')
        if k < 0 or k > n:
            return 0.0 + 0.0j
        k_eff = min(k, n - k)
        num = 1.0 + 0.0j
        den = 1.0 + 0.0j
        for i in range(k_eff):
            num *= self.q_bracket(n - i)
            den *= self.q_bracket(i + 1)
        if abs(den) <= 1e-15:
            raise ValueError(f'q_binomial denominator vanished at q={self.q!r}, n={n}, k={k}.')
        return num / den

    @property
    def zero(self) -> QuantumElement:
        """Additive identity 0."""
        return {}

    @property
    def one(self) -> QuantumElement:
        r"""Multiplicative unit $\mathbf{1} = E^0 K^0 F^0$."""
        return {(0, 0, 0): 1.0 + 0.0j}

    @property
    def E(self) -> QuantumElement:  # noqa: N802
        """Raising generator E."""
        return {(1, 0, 0): 1.0 + 0.0j}

    @property
    def F(self) -> QuantumElement:  # noqa: N802
        """Lowering generator F."""
        return {(0, 0, 1): 1.0 + 0.0j}

    @property
    def K(self) -> QuantumElement:  # noqa: N802
        r"""Cartan group-like generator $K = q^H$."""
        return {(0, 1, 0): 1.0 + 0.0j}

    @property
    def K_inv(self) -> QuantumElement:  # noqa: N802
        r"""Inverse Cartan generator $K^{-1} = q^{-H}$."""
        return {(0, -1, 0): 1.0 + 0.0j}

    def add(self, a: QuantumElement, b: QuantumElement) -> QuantumElement:
        """Vector addition in PBW basis."""
        res = {k: complex(v) for k, v in a.items()}
        for k, v in b.items():
            res[k] = res.get(k, 0.0 + 0.0j) + complex(v)
        return _prune_vector(res, self.tol)

    def neg(self, a: QuantumElement) -> QuantumElement:
        """Additive inverse."""
        return {k: -complex(v) for k, v in a.items() if abs(v) > self.tol}

    def smul(self, r: complex, a: QuantumElement) -> QuantumElement:
        """Scalar multiplication by complex scalar r."""
        rc = complex(r)
        if abs(rc) <= self.tol:
            return {}
        return {k: rc * complex(v) for k, v in a.items() if abs(rc * complex(v)) > self.tol}

    def _left_mul_f(self, vec: QuantumElement) -> QuantumElement:
        r"""Compute $F \cdot x$ in PBW form using exact $q$-commutation."""
        q = self.q
        q_diff = q - 1.0 / q
        out: dict[PBWKey, complex] = {}
        for (a, b, c), coeff in vec.items():
            cc = complex(coeff)
            if abs(cc) <= self.tol:
                continue
            # Direct pass-through term: q^{2b} E^a K^b F^{c+1}
            key_pass = (a, b, c + 1)
            out[key_pass] = out.get(key_pass, 0.0 + 0.0j) + cc * (q ** (2 * b))
            if a > 0:
                if abs(q_diff) <= 1e-14:
                    raise ValueError(
                        'PBW commutation F * E requires q != +/- 1 (singular denominator q - q^-1). '
                        'Use spin_representation() for smooth q -> 1 evaluation.'
                    )
                scale = -cc * self.q_bracket(a) / q_diff
                key_plus = (a - 1, b + 1, c)
                key_minus = (a - 1, b - 1, c)
                out[key_plus] = out.get(key_plus, 0.0 + 0.0j) + scale * (q ** (a - 1))
                out[key_minus] = out.get(key_minus, 0.0 + 0.0j) - scale * (q ** (1 - a))
        return _prune_vector(out, self.tol)

    def _left_mul_k_pow(self, power: int, vec: QuantumElement) -> QuantumElement:
        r"""Compute $K^{\mathrm{power}} \cdot x$ via $K^r E^a = q^{2ar} E^a K^r$."""
        if power == 0:
            return _prune_vector(vec, self.tol)
        q = self.q
        out: dict[PBWKey, complex] = {}
        for (a, b, c), coeff in vec.items():
            cc = complex(coeff)
            if abs(cc) <= self.tol:
                continue
            key = (a, b + power, c)
            out[key] = out.get(key, 0.0 + 0.0j) + cc * (q ** (2 * a * power))
        return _prune_vector(out, self.tol)

    def _left_mul_e_pow(self, power: int, vec: QuantumElement) -> QuantumElement:
        r"""Compute $E^{\mathrm{power}} \cdot x$ directly in PBW form."""
        if power == 0:
            return _prune_vector(vec, self.tol)
        return {(a + power, b, c): complex(v) for (a, b, c), v in vec.items() if abs(v) > self.tol}

    def _mul_basis_left(self, key: PBWKey, rhs: QuantumElement) -> QuantumElement:
        """Compute (E^a K^b F^c) * rhs in PBW form."""
        a, b, c = key
        cur = rhs
        for _ in range(c):
            cur = self._left_mul_f(cur)
        if b != 0:
            cur = self._left_mul_k_pow(b, cur)
        if a != 0:
            cur = self._left_mul_e_pow(a, cur)
        return cur

    def mul(self, a: QuantumElement, b: QuantumElement) -> QuantumElement:
        r"""Associative non-commutative multiplication in $U_q(\mathfrak{sl}_2)$."""
        if not a or not b:
            return {}
        out: dict[PBWKey, complex] = {}
        for key, coeff in a.items():
            cc = complex(coeff)
            if abs(cc) <= self.tol:
                continue
            term = self._mul_basis_left(key, b)
            for tkey, tval in term.items():
                out[tkey] = out.get(tkey, 0.0 + 0.0j) + cc * tval
        return _prune_vector(out, self.tol)

    def _mul_tensor(self, left: TensorElement, right: TensorElement) -> TensorElement:
        r"""Componentwise product in $U_q(\mathfrak{sl}_2) \otimes U_q(\mathfrak{sl}_2)$."""
        if not left or not right:
            return {}
        out: dict[tuple[PBWKey, PBWKey], complex] = {}
        for (u1, v1), c1 in left.items():
            for (u2, v2), c2 in right.items():
                scalar = c1 * c2
                if abs(scalar) <= self.tol:
                    continue
                u_prod = self._mul_basis_left(u1, {u2: 1.0 + 0.0j})
                v_prod = self._mul_basis_left(v1, {v2: 1.0 + 0.0j})
                for uk, uv in u_prod.items():
                    for vk, vv in v_prod.items():
                        val = scalar * uv * vv
                        if abs(val) > self.tol:
                            tkey = (uk, vk)
                            out[tkey] = out.get(tkey, 0.0 + 0.0j) + val
        return _prune_tensor(out, self.tol)

    def _coproduct_basis(self, key: PBWKey) -> TensorElement:
        r"""Compute $\Delta(E^a K^b F^c) = \Delta(E)^a \Delta(K^b) \Delta(F)^c$."""
        a, b, c = key
        delta_e: TensorElement = {
            ((1, 0, 0), (0, 0, 0)): 1.0 + 0.0j,
            ((0, 1, 0), (1, 0, 0)): 1.0 + 0.0j,
        }
        delta_f: TensorElement = {
            ((0, 0, 1), (0, -1, 0)): 1.0 + 0.0j,
            ((0, 0, 0), (0, 0, 1)): 1.0 + 0.0j,
        }
        result: TensorElement = {((0, 0, 0), (0, 0, 0)): 1.0 + 0.0j}
        for _ in range(a):
            result = self._mul_tensor(result, delta_e)
        if b != 0:
            result = self._mul_tensor(result, {((0, b, 0), (0, b, 0)): 1.0 + 0.0j})
        for _ in range(c):
            result = self._mul_tensor(result, delta_f)
        return result

    def coproduct(self, x: QuantumElement) -> TensorElement:
        r"""Non-cocommutative comultiplication $\Delta : U_q(\mathfrak{sl}_2) \to U_q \otimes U_q$."""
        out: dict[tuple[PBWKey, PBWKey], complex] = {}
        for key, coeff in x.items():
            cc = complex(coeff)
            if abs(cc) <= self.tol:
                continue
            for tkey, tval in self._coproduct_basis(key).items():
                out[tkey] = out.get(tkey, 0.0 + 0.0j) + cc * tval
        return _prune_tensor(out, self.tol)

    def counit(self, x: QuantumElement) -> complex:
        r"""Counit $\epsilon(E) = \epsilon(F) = 0$, $\epsilon(K^b) = 1$."""
        total = 0.0 + 0.0j
        for (a, _b, c), coeff in x.items():
            if a == 0 and c == 0:
                total += complex(coeff)
        return total

    def antipode(self, x: QuantumElement) -> QuantumElement:
        r"""Non-involutive antipode $S(E^a K^b F^c) = S(F)^c S(K^b) S(E)^a$."""
        q = self.q
        s_e: QuantumElement = {(1, -1, 0): -(q ** (-2))}
        s_f: QuantumElement = {(0, 1, 1): -(q**2)}
        out: dict[PBWKey, complex] = {}
        for (a, b, c), coeff in x.items():
            cc = complex(coeff)
            if abs(cc) <= self.tol:
                continue
            term: QuantumElement = self.one
            for _ in range(c):
                term = self.mul(term, s_f)
            if b != 0:
                term = self.mul(term, {(0, -b, 0): 1.0 + 0.0j})
            for _ in range(a):
                term = self.mul(term, s_e)
            for tkey, tval in term.items():
                out[tkey] = out.get(tkey, 0.0 + 0.0j) + cc * tval
        return _prune_vector(out, self.tol)

    def spin_representation(self, j_halves: int) -> dict[str, SparseMatrix[int, complex]]:
        r"""Construct the $(2j + 1)$-dimensional $q$-deformed spin-$j$ module $V_j$.

        Args:
            j_halves: Twice the spin ($2j \in \mathbb{Z}_{\ge 0}$). For example, `1` gives
                the 2-dimensional fundamental spin-1/2 module and `2` gives the 3-dimensional
                spin-1 adjoint module.

        Returns:
            Dictionary with keys `'E'`, `'F'`, `'K'`, `'K_inv'` mapping to sparse complex
            matrices in the Condon-Shortley weight basis $|j, j\rangle, \dots, |j, -j\rangle$.
            Smoothly recovers `algebrax.rep.lie.spin_representation(j_halves, form='sl2')`
            as $q \to 1$.
        """
        if j_halves < 0:
            raise ValueError(f'j_halves must be a non-negative integer, got {j_halves}.')
        dim = j_halves + 1
        q = self.q

        k_mat: dict[int, dict[int, complex]] = {}
        k_inv_mat: dict[int, dict[int, complex]] = {}
        e_mat: dict[int, dict[int, complex]] = {}
        f_mat: dict[int, dict[int, complex]] = {}

        for idx in range(dim):
            two_m = j_halves - 2 * idx
            k_val = q**two_m
            k_inv_val = q ** (-two_m)
            if abs(k_val) > self.tol:
                k_mat[idx] = {idx: k_val}
            if abs(k_inv_val) > self.tol:
                k_inv_mat[idx] = {idx: k_inv_val}

        for p in range(1, dim):
            coeff = cmath.sqrt(self.q_bracket(p) * self.q_bracket(dim - p))
            if abs(coeff) > self.tol:
                e_mat.setdefault(p - 1, {})[p] = coeff
                f_mat.setdefault(p, {})[p - 1] = coeff

        return {
            'E': e_mat,
            'F': f_mat,
            'K': k_mat,
            'K_inv': k_inv_mat,
        }

    def evaluate_rep(
        self,
        element: QuantumElement,
        rep: Mapping[str, SparseMatrix[int, complex]],
    ) -> SparseMatrix[int, complex]:
        r"""Evaluate a PBW element $\sum \alpha_{a,b,c} E^a K^b F^c$ inside a matrix representation."""
        k_mat = rep['K']
        dim = max(k_mat.keys(), default=-1) + 1
        if dim == 0:
            return {}
        e_mat = rep['E']
        f_mat = rep['F']
        k_inv_mat = rep['K_inv']

        acc: dict[int, dict[int, complex]] = {}
        for (a, b, c), coeff in element.items():
            cc = complex(coeff)
            if abs(cc) <= self.tol:
                continue
            term = _sparse_mat_pow(e_mat, a, dim, self.tol)
            if b > 0:
                term = _sparse_mat_mul(term, _sparse_mat_pow(k_mat, b, dim, self.tol), self.tol)
            elif b < 0:
                term = _sparse_mat_mul(term, _sparse_mat_pow(k_inv_mat, -b, dim, self.tol), self.tol)
            if c > 0:
                term = _sparse_mat_mul(term, _sparse_mat_pow(f_mat, c, dim, self.tol), self.tol)
            for r, row in term.items():
                target = acc.setdefault(r, {})
                for col, val in row.items():
                    target[col] = target.get(col, 0.0 + 0.0j) + cc * val

        return _prune_matrix(acc, tol=self.tol)


def universal_r_matrix_sl2_fundamental(q: complex) -> SparseMatrix[int, complex]:
    r"""Construct the fundamental $4 \times 4$ sparse $R$-matrix for $U_q(\mathfrak{sl}_2)$ on $V_{1/2}^{\otimes 2}$.

    Ordered in the tensor basis $\{|00\rangle, |01\rangle, |10\rangle, |11\rangle\}$:
    $$R = \begin{pmatrix}
        q & 0 & 0 & 0 \\
        0 & 1 & 0 & 0 \\
        0 & q - q^{-1} & 1 & 0 \\
        0 & 0 & 0 & q
    \end{pmatrix}$$
    Compatible with the coproduct $\Delta(E) = E \otimes 1 + K \otimes E$,
    $\Delta(F) = F \otimes K^{-1} + 1 \otimes F$, $\Delta(K) = K \otimes K$, so that
    $B = P \circ R$ intertwines $\Delta(x)$ for all $x \in U_q(\mathfrak{sl}_2)$ and $R$
    satisfies the Quantum Yang-Baxter Equation $R_{12} R_{13} R_{23} = R_{23} R_{13} R_{12}$.
    """
    qc = _validate_q(q)
    off_diag = qc - 1.0 / qc
    row2: dict[int, complex] = {2: 1.0 + 0.0j}
    if abs(off_diag) > 1e-13:
        row2[1] = off_diag
    return {
        0: {0: qc},
        1: {1: 1.0 + 0.0j},
        2: row2,
        3: {3: qc},
    }


def braiding_operator(
    r_matrix: SparseMatrix[int, complex],
    dim: int = 2,
) -> SparseMatrix[int, complex]:
    r"""Compute the braided isomorphism $B = P \circ R$ on $V \otimes V$ from an $R$-matrix.

    Here $P(|i\rangle \otimes |j\rangle) = |j\rangle \otimes |i\rangle$ is the tensor flip
    automorphism. When $R$ satisfies the Quantum Yang-Baxter Equation, $B$ satisfies the
    Artin braid relation $(B \otimes I)(I \otimes B)(B \otimes I) = (I \otimes B)(B \otimes I)(I \otimes B)$.
    """
    if dim < 1:
        raise ValueError(f'dim must be >= 1, got {dim}.')
    out: dict[int, dict[int, complex]] = {}
    for row_idx, row in r_matrix.items():
        i, j = divmod(row_idx, dim)
        flipped_row = j * dim + i
        cleaned = {c: complex(v) for c, v in row.items() if abs(v) > 1e-13}
        if cleaned:
            out[flipped_row] = cleaned
    return out


def _braiding_operator_inverse_fundamental(q: complex) -> SparseMatrix[int, complex]:
    r"""Exact inverse $B^{-1} = B - (q - q^{-1}) I_4$ from the Hecke relation $(B - qI)(B + q^{-1}I) = 0$."""
    qc = _validate_q(q)
    b_mat = braiding_operator(universal_r_matrix_sl2_fundamental(qc), dim=2)
    diff = qc - 1.0 / qc
    inv: dict[int, dict[int, complex]] = {r: dict(row) for r, row in b_mat.items()}
    for i in range(4):
        row = inv.setdefault(i, {})
        row[i] = row.get(i, 0.0 + 0.0j) - diff
    return _prune_matrix(inv, tol=1e-13)


def braid_to_matrix(
    braid_word: Sequence[int],
    num_strands: int,
    q: complex,
) -> SparseMatrix[int, complex]:
    r"""Represent a braid group element $\beta \in B_n$ as a sparse $2^n \times 2^n$ operator on $V_{1/2}^{\otimes n}$.

    Args:
        braid_word: Sequence of signed Artin generator indices in $\{\pm 1, \dots, \pm(n - 1)\}$.
            Positive integer $+i$ denotes $\sigma_i$ (using $B = P \circ R$ on strands $(i - 1, i)$);
            negative integer $-i$ denotes $\sigma_i^{-1}$ (using $B^{-1}$).
        num_strands: Number of strands $n \ge 1$.
        q: Non-zero complex deformation parameter.

    Returns:
        Sparse $2^n \times 2^n$ complex matrix $\rho(\beta)$.
    """
    if num_strands < 1:
        raise ValueError(f'num_strands must be >= 1, got {num_strands}.')
    qc = _validate_q(q)
    for gen in braid_word:
        if gen == 0 or abs(gen) >= num_strands:
            raise ValueError(
                f'Braid generator {gen} out of bounds for {num_strands} strands '
                f'(valid range: +/-1 .. +/-{num_strands - 1}).'
            )

    full_dim = 2**num_strands
    result = _sparse_identity(full_dim)
    if not braid_word:
        return result

    b_pos = braiding_operator(universal_r_matrix_sl2_fundamental(qc), dim=2)
    b_neg = _braiding_operator_inverse_fundamental(qc)

    pos_cache: dict[int, SparseMatrix[int, complex]] = {}
    neg_cache: dict[int, SparseMatrix[int, complex]] = {}

    for gen in braid_word:
        site = abs(gen) - 1
        if gen > 0:
            if site not in pos_cache:
                pos_cache[site] = _embed_two_site_operator(b_pos, site, num_strands, dim=2)
            step = pos_cache[site]
        else:
            if site not in neg_cache:
                neg_cache[site] = _embed_two_site_operator(b_neg, site, num_strands, dim=2)
            step = neg_cache[site]
        result = _sparse_mat_mul(result, step, tol=1e-13)

    return result


def quantum_trace(
    mat: SparseMatrix[int, complex],
    num_strands: int,
    q: complex,
) -> complex:
    r"""Compute the $U_q(\mathfrak{sl}_2)$ quantum trace $\mathrm{Tr}_q(M) = \mathrm{Tr}(K^{\otimes n} M)$.

    On the $2^n$-dimensional tensor space $V_{1/2}^{\otimes n}$ where $K = \mathrm{diag}(q, q^{-1})$,
    the diagonal weight of basis state $|s\rangle$ ($0 \le s < 2^n$) is $q^{n - 2\,\mathrm{popcount}(s)}$.
    In particular, $\mathrm{Tr}_q(I_{2^n}) = (q + q^{-1})^n = [2]_q^n$.
    """
    if num_strands < 1:
        raise ValueError(f'num_strands must be >= 1, got {num_strands}.')
    qc = _validate_q(q)
    full_dim = 2**num_strands
    total = 0.0 + 0.0j
    for idx, row in mat.items():
        if idx < 0 or idx >= full_dim:
            raise ValueError(f'Matrix index {idx} out of bounds for {num_strands} strands (dim {full_dim}).')
        diag_val = row.get(idx)
        if diag_val is not None:
            exponent = num_strands - 2 * idx.bit_count()
            total += (qc**exponent) * complex(diag_val)
    return total


def jones_polynomial_eval(
    braid_word: Sequence[int],
    num_strands: int,
    q: complex,
) -> complex:
    r"""Evaluate the Jones polynomial $V_L(t)$ of the braid closure $L = \widehat{\beta}$ at $t = q^{-2}$.

    Uses the Markov-invariant Reshetikhin-Turaev normalization:
    $$V_L(t)\big|_{t = q^{-2}} = (-1)^{n - 1 + w(\beta)} q^{-2 w(\beta)}
      \frac{\mathrm{Tr}_q(\rho(\beta))}{q + q^{-1}}$$
    where $w(\beta) = \sum_k \operatorname{sgn}(\text{gen}_k)$ is the braid writhe.

    Satisfies the canonical Jones skein relation:
    $$t^{-1} V_{L_+}(t) - t V_{L_-}(t) = (t^{1/2} - t^{-1/2}) V_{L_0}(t), \qquad V_{\text{unknot}}(t) = 1.$$

    Reference values (with $t = q^{-2}$):
        - Unknot (`[]`, `n=1` or `[1]`, `n=2`): $1$
        - 2-component unlink (`[]`, `n=2`): $-(t^{1/2} + t^{-1/2})$
        - Positive Hopf link (`[1, 1]`, `n=2`): $-(t^{1/2} + t^{5/2})$
        - Right-handed trefoil $3_1$ (`[1, 1, 1]`, `n=2`): $t + t^3 - t^4$
        - Left-handed trefoil $\overline{3_1}$ (`[-1, -1, -1]`, `n=2`): $t^{-1} + t^{-3} - t^{-4}$
        - Figure-eight knot $4_1$ (`[1, -2, 1, -2]`, `n=3`): $t^{-2} - t^{-1} + 1 - t + t^2$
    """
    qc = _validate_q(q)
    q_dim = qc + 1.0 / qc
    if abs(q_dim) <= 1e-13:
        raise ValueError(
            f'Quantum dimension [2]_q = q + q^-1 vanishes at q={qc!r}; '
            'Jones polynomial normalization is singular at q = +/-i.'
        )
    mat = braid_to_matrix(braid_word, num_strands, qc)
    qtr = quantum_trace(mat, num_strands, qc)
    writhe = sum(1 if gen > 0 else -1 for gen in braid_word)
    sign = -1.0 if ((num_strands - 1 + writhe) % 2) else 1.0
    return sign * (qc ** (-2 * writhe)) * qtr / q_dim
