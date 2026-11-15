r"""
Character Theory, Conjugacy Classes, and Orthonormal Character Tables for Finite Groups.

Algebraic Signatures:
    Group Character:      $\chi_\rho(g) = \operatorname{tr}(\rho(g))$
    Schur Inner Product:  $\langle \chi_a, \chi_b \rangle =
                          \frac{1}{|G|} \sum_{j} |C_j| \, \chi_a(C_j)\overline{\chi_b(C_j)}$
    Maschke Multiplicity: $V \cong \bigoplus_i m_i V_i, \quad m_i = \langle \chi_V, \chi_i \rangle$
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from algebrax.group.finite import FiniteGroup, conjugacy_classes
from algebrax.matrix.core import trace
from algebrax.rep.group import GroupRepresentation

G = TypeVar('G', bound=Hashable)


@dataclass(frozen=True)
class Character(Generic[G]):
    r"""Class function character $\chi_\rho(g) = \operatorname{tr}(\rho(g))$ of a finite group representation.

    Algebraic Signature:
        $\chi : \mathrm{Conj}(G) \longrightarrow \mathbb{C}, \quad \chi(h g h^{-1}) = \chi(g)$

    Attributes:
        values: Mapping from conjugacy class key (or element) to trace value.
        degree: Representation degree $\chi(e) = \dim V$.
    """

    values: dict[Any, complex]
    degree: int

    def __call__(self, c_class: Any) -> complex:
        r"""Evaluate $\chi(c)$ at conjugacy class key `c_class`."""
        return self.values.get(c_class, 0.0 + 0.0j)

    def norm_squared(self, group_order: int, class_sizes: Mapping[Any, int]) -> float:
        r"""Compute $\langle \chi, \chi \rangle = \frac{1}{|G|} \sum_c |C_c| |\chi(c)|^2$."""
        total = sum(class_sizes[c] * abs(self.values.get(c, 0.0 + 0.0j)) ** 2 for c in class_sizes)
        return float(total / group_order)

    def is_irreducible(self, group_order: int, class_sizes: Mapping[Any, int], tol: float = 1e-9) -> bool:
        r"""Test irreducibility via Schur's criterion $\langle \chi, \chi \rangle = 1$."""
        return abs(self.norm_squared(group_order, class_sizes) - 1.0) < tol

    @classmethod
    def from_representation(
        cls,
        rep: GroupRepresentation[Any, G],
        class_representatives: Mapping[Any, G],
    ) -> Character[G]:
        r"""Compile a `Character` directly from a `GroupRepresentation` and class representatives."""
        vals = {c_key: complex(trace(rep(g_rep))) for c_key, g_rep in class_representatives.items()}
        return cls(values=vals, degree=rep.dimension)

    @classmethod
    def from_group(
        cls,
        rep: GroupRepresentation[Any, G],
        group: FiniteGroup[G],
    ) -> Character[G]:
        r"""Compile a `Character` keyed by conjugacy class tuples directly from a `FiniteGroup`."""
        classes = group.conjugacy_classes()
        vals = {c: complex(trace(rep(c[0]))) for c in classes}
        return cls(values=vals, degree=rep.dimension)


@dataclass(frozen=True)
class CharacterTable:
    r"""Orthonormal character table of a finite group $G$.

    Algebraic Signature:
        Rows are irreducible characters $\chi_i$; columns are conjugacy classes $C_j$:
        $$\langle \chi_i, \chi_j \rangle =
        \frac{1}{|G|} \sum_{a} |C_a| \chi_i(C_a) \overline{\chi_j(C_a)} = \delta_{ij}$$

    Attributes:
        classes: Labels of conjugacy classes (with identity class at index 0 by convention).
        class_sizes: Cardinalities $|C_j|$ matching `classes`.
        irreps: Labels of irreducible representations.
        table: Character matrix `table[irrep_idx][class_idx]`.
        group_order: Total order $|G| = \sum_j |C_j|$.
        tol: Numerical tolerance for cyclotomic inner product verification and rounding checks.
    """

    classes: Sequence[str]
    class_sizes: Sequence[int]
    irreps: Sequence[str]
    table: list[list[complex]]
    group_order: int
    tol: float = 1e-9

    def inner_product(self, chi_a: Sequence[complex], chi_b: Sequence[complex]) -> complex:
        r"""Compute weighted Schur inner product $\frac{1}{|G|} \sum_j |C_j| \chi_a(C_j) \overline{\chi_b(C_j)}$."""
        if len(chi_a) != len(self.class_sizes) or len(chi_b) != len(self.class_sizes):
            raise ValueError(
                f'Character lengths ({len(chi_a)}, {len(chi_b)}) '
                f'must match number of classes ({len(self.class_sizes)}).'
            )
        return (
            sum(size * complex(a) * complex(b).conjugate() for size, a, b in zip(self.class_sizes, chi_a, chi_b))
            / self.group_order
        )

    def _as_row(self, character: Sequence[complex] | Character[Any]) -> list[complex]:
        if isinstance(character, Character):
            return [character(label) for label in self.classes]
        return [complex(x) for x in character]

    def irrep_row(self, name: str) -> list[complex]:
        """Return the character vector corresponding to irreducible representation `name`."""
        idx = list(self.irreps).index(name)
        return list(self.table[idx])

    def irrep_character(self, name: str) -> Character[Any]:
        """Return a `Character` object for irreducible representation `name`."""
        row = self.irrep_row(name)
        deg = round(row[0].real)
        return Character(values=dict(zip(self.classes, row)), degree=deg)

    def irrep_dimensions(self, identity_idx: int = 0) -> dict[str, int]:
        """Return mapping from irrep name to its dimension $\\dim V_i = \\chi_i(e)$."""
        return {name: round(row[identity_idx].real) for name, row in zip(self.irreps, self.table)}

    def is_irreducible(self, character: Sequence[complex] | Character[Any]) -> bool:
        r"""Test whether an arbitrary character vector is irreducible ($\langle \chi, \chi \rangle = 1$)."""
        row = self._as_row(character)
        norm_sq = self.inner_product(row, row)
        return abs(norm_sq.imag) <= self.tol and abs(norm_sq.real - 1.0) <= self.tol

    def tensor_product_character(
        self,
        chi_a: Sequence[complex] | Character[Any],
        chi_b: Sequence[complex] | Character[Any],
    ) -> list[complex]:
        r"""Compute the tensor product character $(\chi_a \cdot \chi_b)(C_j) = \chi_a(C_j)\chi_b(C_j)$."""
        row_a = self._as_row(chi_a)
        row_b = self._as_row(chi_b)
        return [a * b for a, b in zip(row_a, row_b)]

    def decompose(self, character: Sequence[complex] | Character[Any]) -> dict[str, int]:
        r"""Decompose an arbitrary reducible character into irrep multiplicities $m_i = \langle \chi, \chi_i \rangle$.

        Guards against cyclotomic rounding drift (e.g. roots of unity summing to `0.99999999998`)
        and rejects non-character vectors with significant non-integer or imaginary residuals.
        """
        row = self._as_row(character)
        multiplicities: dict[str, int] = {}
        for name, chi_irrep in zip(self.irreps, self.table):
            val = self.inner_product(row, chi_irrep)
            if abs(val.imag) > self.tol * 10:
                raise ValueError(f'Non-real multiplicity residual {val.imag} for irrep {name} (numerical instability)')
            m = round(val.real)
            if abs(val.real - m) > self.tol:
                raise ValueError(
                    f'Non-integer multiplicity residual {val.real} for irrep {name} (invalid class function)'
                )
            if m < 0:
                raise ValueError(
                    f'Negative multiplicity {m} for irrep {name} (virtual character, not a representation)'
                )
            if m > 0:
                multiplicities[name] = m
        return multiplicities


__all__ = [
    'Character',
    'CharacterTable',
    'conjugacy_classes',
]
