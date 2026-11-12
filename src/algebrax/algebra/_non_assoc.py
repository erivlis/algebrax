r"""
Non-Associative & Quantum Algebras: Jordan, Alternative, Octonions, Malcev & Poisson Algebras.

Implements flat Layer 2 protocols (`JordanAlgebra`, `AlternativeAlgebra`, `MalcevAlgebra`,
`PoissonAlgebra`) composed directly from Layer 1 atomic mixins (`HasScale`, `HasZero`,
`HasAdd`, `HasNeg`, `HasMul`, `HasBracket`) in accordance with EP-0194, together with
unboxed sparse implementations (`SymmetricMatrixJordanAlgebra`, `OctonionAlgebra`,
`ImaginaryOctonionMalcevAlgebra`).
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import (
    HasAdd,
    HasBracket,
    HasMul,
    HasNeg,
    HasScale,
    HasZero,
)
from algebrax.algebra._semiring import Semiring
from algebrax.typing import SparseMatrix, SparseVector

R = TypeVar('R')
M = TypeVar('M')

__all__ = [
    'AlternativeAlgebra',
    'ImaginaryOctonionMalcevAlgebra',
    'JordanAlgebra',
    'MalcevAlgebra',
    'OctonionAlgebra',
    'PoissonAlgebra',
    'SymmetricMatrixJordanAlgebra',
]


@runtime_checkable
class JordanAlgebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M]):
    r"""A commutative non-associative algebra satisfying the Jordan identity:
    $$(x \circ y) \circ x^2 = x \circ (y \circ x^2)$$
    where `mul(x, y)` denotes the symmetric Jordan product $x \circ y = y \circ x$.

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, +, -, \circ \rangle$

    Axioms:
        - Commutativity: $x \circ y = y \circ x$.
        - Jordan Identity: $(x \circ y) \circ (x \circ x) = x \circ (y \circ (x \circ x))$.
    """

    ...


@runtime_checkable
class AlternativeAlgebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M]):
    r"""A non-associative algebra whose associator $[x, y, z] = (xy)z - x(yz)$ is alternating:
    $$x(xy) = (xx)y \quad \text{(Left Alternative)} \qquad (yx)x = y(xx) \quad \text{(Right Alternative)}$$

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$
    """

    ...


@runtime_checkable
class MalcevAlgebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M]):
    r"""A non-associative anticommutative algebra satisfying the Malcev identity:
    $$J(x, y, x \cdot z) = J(x, y, z) \cdot x$$
    where $J(x, y, z) = (x \cdot y) \cdot z + (y \cdot z) \cdot x + (z \cdot x) \cdot y$ is the Jacobian.

    Algebraic Signature:
        $\langle R, M, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$
    """

    ...


@runtime_checkable
class PoissonAlgebra(
    HasScale[R, M],
    HasZero[M],
    HasAdd[M],
    HasNeg[M],
    HasMul[M],
    HasBracket[M],
    Protocol[R, M],
):
    r"""A Poisson algebra $\langle R, P, \cdot_s, \mathbf{0}, +, -, \cdot, \{\cdot, \cdot\} \rangle$.

    Combines a commutative associative algebra $\langle P, +, \cdot \rangle$ (`mul`) with a
    Lie algebra $\langle P, +, \{\cdot, \cdot\} \rangle$ (`bracket`) satisfying the Leibniz rule:
    $$\{f, g \cdot h\} = \{f, g\} \cdot h + g \cdot \{f, h\}$$
    """

    ...


class SymmetricMatrixJordanAlgebra(JordanAlgebra[float, SparseMatrix[Any, float]]):
    r"""Special Jordan algebra of sparse real matrices under the anticommutator product:
    $$A \circ B = \frac{1}{2}(AB + BA)$$

    Algebraic Signature:
        $\langle \mathbb{R}, \mathrm{Mat}_n(\mathbb{R}), \cdot_s, \mathbf{0}, +, -, \circ \rangle$
    """

    def __init__(self, base_semiring: Semiring[float] | None = None) -> None:
        if base_semiring is None:
            from algebrax.semiring.arithmetic import StandardSemiring

            base_semiring = StandardSemiring(float)
        self.base_semiring: Semiring[float] = base_semiring

    @property
    def zero(self) -> SparseMatrix[Any, float]:
        return {}

    def add(
        self,
        a: SparseMatrix[Any, float],
        b: SparseMatrix[Any, float],
    ) -> SparseMatrix[Any, float]:
        from algebrax.matrix.core import add

        return add(a, b, semiring=self.base_semiring)

    def neg(self, a: SparseMatrix[Any, float]) -> SparseMatrix[Any, float]:
        return self.smul(-1.0, a)

    def smul(self, r: float, m: SparseMatrix[Any, float]) -> SparseMatrix[Any, float]:
        rf = float(r)
        if abs(rf) <= 1e-15:
            return {}
        out: dict[Any, dict[Any, float]] = {}
        for row_k, row in m.items():
            scaled_row = {
                col_k: self.base_semiring.mul(rf, float(val))
                for col_k, val in row.items()
                if abs(self.base_semiring.mul(rf, float(val))) > 1e-15
            }
            if scaled_row:
                out[row_k] = scaled_row
        return out

    def mul(
        self,
        a: SparseMatrix[Any, float],
        b: SparseMatrix[Any, float],
    ) -> SparseMatrix[Any, float]:
        from algebrax.matrix.core import add, dot

        ab = dot(a, b, semiring=self.base_semiring)
        ba = dot(b, a, semiring=self.base_semiring)
        return self.smul(0.5, add(ab, ba, semiring=self.base_semiring))


def _build_fano_table() -> dict[tuple[int, int], tuple[int, float]]:
    fano_lines = (
        (1, 2, 3),
        (1, 4, 5),
        (1, 7, 6),
        (2, 4, 6),
        (2, 5, 7),
        (3, 4, 7),
        (3, 6, 5),
    )
    table: dict[tuple[int, int], tuple[int, float]] = {}
    for i in range(8):
        table[(0, i)] = (i, 1.0)
        table[(i, 0)] = (i, 1.0)
    for i in range(1, 8):
        table[(i, i)] = (0, -1.0)
    for a, b, c in fano_lines:
        table[(a, b)] = (c, 1.0)
        table[(b, c)] = (a, 1.0)
        table[(c, a)] = (b, 1.0)
        table[(b, a)] = (c, -1.0)
        table[(c, b)] = (a, -1.0)
        table[(a, c)] = (b, -1.0)
    return table


_FANO_TABLE = _build_fano_table()


class OctonionAlgebra(AlternativeAlgebra[float, SparseVector[int, float]]):
    r"""The 8-dimensional real alternative normed division algebra $\mathbb{O}$.

    Algebraic Signature:
        $\mathbb{O} = \mathrm{span}_{\mathbb{R}}\{e_0 = 1, e_1, e_2, e_3, e_4, e_5, e_6, e_7\}$

    Carrier:
        `SparseVector[int, float]` (`dict[int, float]` with basis keys $i \in \{0, \dots, 7\}$).

    Properties:
        - Normed Division Algebra (Hurwitz Theorem): $\|a \cdot b\|^2 = \|a\|^2 \|b\|^2$.
        - Alternative Laws: $x(xy) = (xx)y$ and $(yx)x = y(xx)$.
        - Non-Associative: $(e_1 e_2) e_4 = e_3 e_4 = e_7 \neq -e_7 = e_1 e_6 = e_1 (e_2 e_4)$.
    """

    FANO_LINES = (
        (1, 2, 3),
        (1, 4, 5),
        (1, 7, 6),
        (2, 4, 6),
        (2, 5, 7),
        (3, 4, 7),
        (3, 6, 5),
    )

    def __init__(self, tol: float = 1e-15) -> None:
        self.tol = tol

    @property
    def zero(self) -> SparseVector[int, float]:
        return {}

    @property
    def one(self) -> SparseVector[int, float]:
        return {0: 1.0}

    def add(
        self,
        a: SparseVector[int, float],
        b: SparseVector[int, float],
    ) -> SparseVector[int, float]:
        out: dict[int, float] = dict(a)
        for i, val in b.items():
            new_val = out.get(i, 0.0) + float(val)
            if abs(new_val) > self.tol:
                out[i] = new_val
            else:
                out.pop(i, None)
        return out

    def neg(self, a: SparseVector[int, float]) -> SparseVector[int, float]:
        return {i: -float(val) for i, val in a.items() if abs(float(val)) > self.tol}

    def smul(self, r: float, m: SparseVector[int, float]) -> SparseVector[int, float]:
        rf = float(r)
        if abs(rf) <= self.tol:
            return {}
        return {i: rf * float(val) for i, val in m.items() if abs(rf * float(val)) > self.tol}

    def mul(
        self,
        a: SparseVector[int, float],
        b: SparseVector[int, float],
    ) -> SparseVector[int, float]:
        out: dict[int, float] = {}
        for i, va in a.items():
            for j, vb in b.items():
                k, sign = _FANO_TABLE[(int(i), int(j))]
                prod = float(va) * float(vb) * sign
                new_val = out.get(k, 0.0) + prod
                if abs(new_val) > self.tol:
                    out[k] = new_val
                else:
                    out.pop(k, None)
        return out

    def conjugate(self, a: SparseVector[int, float]) -> SparseVector[int, float]:
        r"""Octonion conjugation $\bar{a} = a_0 e_0 - \sum_{i=1}^7 a_i e_i$."""
        return {
            i: (float(val) if i == 0 else -float(val))
            for i, val in a.items()
            if abs(float(val)) > self.tol
        }

    def norm_sq(self, a: SparseVector[int, float]) -> float:
        r"""Squared Euclidean norm $\|a\|^2 = \sum_{i=0}^7 a_i^2$."""
        return float(sum(float(v) * float(v) for v in a.values()))

    def inv(self, a: SparseVector[int, float]) -> SparseVector[int, float]:
        r"""Multiplicative inverse $a^{-1} = \bar{a} / \|a\|^2$ for non-zero octonion $a$."""
        n2 = self.norm_sq(a)
        if n2 <= self.tol:
            raise ZeroDivisionError('Cannot invert zero octonion.')
        return self.smul(1.0 / n2, self.conjugate(a))

    def associator(
        self,
        x: SparseVector[int, float],
        y: SparseVector[int, float],
        z: SparseVector[int, float],
    ) -> SparseVector[int, float]:
        r"""Evaluate the associator $[x, y, z] = (x \cdot y) \cdot z - x \cdot (y \cdot z)$."""
        return self.sub(self.mul(self.mul(x, y), z), self.mul(x, self.mul(y, z)))


class ImaginaryOctonionMalcevAlgebra(MalcevAlgebra[float, SparseVector[int, float]]):
    r"""The 7-dimensional Malcev algebra on imaginary octonions $\mathrm{Im}(\mathbb{O})$
    equipped with the commutator product $[x, y] = \frac{1}{2}(x y - y x)$.
    """

    def __init__(self, tol: float = 1e-15) -> None:
        self._oct = OctonionAlgebra(tol=tol)

    @property
    def zero(self) -> SparseVector[int, float]:
        return {}

    def add(
        self,
        a: SparseVector[int, float],
        b: SparseVector[int, float],
    ) -> SparseVector[int, float]:
        return self._oct.add(a, b)

    def neg(self, a: SparseVector[int, float]) -> SparseVector[int, float]:
        return self._oct.neg(a)

    def smul(self, r: float, m: SparseVector[int, float]) -> SparseVector[int, float]:
        return self._oct.smul(r, m)

    def mul(
        self,
        a: SparseVector[int, float],
        b: SparseVector[int, float],
    ) -> SparseVector[int, float]:
        ab = self._oct.mul(a, b)
        ba = self._oct.mul(b, a)
        diff = self._oct.sub(ab, ba)
        # Project to imaginary subspace (drop index 0 if any numerical drift)
        diff.pop(0, None)
        return self._oct.smul(0.5, diff)
