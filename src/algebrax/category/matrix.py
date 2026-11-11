"""
The Category Mat(S) of Sparse Matrices over a Semiring and Transpose Functor Duality.

Follows Stephen Dolan (2013), "Fun with Semirings", realizing sparse dictionary
matrices as unboxed morphisms in the category of finite free semimodules.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

from algebrax.algebra import Semiring
from algebrax.category.core import Category, Functor, OppositeCategory
from algebrax.matrix.core import dot, transpose
from algebrax.typing import SparseMatrix

K = TypeVar('K')
V = TypeVar('V')
W = TypeVar('W')


class MatrixCategory(Category[frozenset[K], SparseMatrix[K, V]], Generic[K, V]):
    r"""The Category $\mathbf{Mat}(\mathcal{S})$ of sparse dictionary matrices over a Semiring $\mathcal{S}$.

    Algebraic Signature:
        $\mathbf{Mat}(\mathcal{S}) = \langle \mathcal{P}_{\mathrm{fin}}(K), \; \mathcal{S}^{A \times B},
        \; \mathbf{I}_A, \; \mathrm{dot}_{\mathcal{S}} \rangle$

    Carrier:
        - **Objects**: Finite index sets `frozenset[K]` (or any `Iterable[K]`).
        - **Morphisms**: Unboxed sparse dictionary matrices `SparseMatrix[K, V]` (`dict[K, dict[K, V]]`).
        - **Identity**: $\mathrm{id}_A = \{k: \{k: \mathbf{1}_{\mathcal{S}}\} \mid k \in A\}$.
        - **Composition**: $\mathrm{compose}(f, g) = \mathrm{dot}(f, g, \mathrm{semiring}=\mathcal{S})$.

    Properties:
        Satisfies left identity, right identity, and associativity over any associative semiring $\mathcal{S}$.
    """

    def __init__(self, semiring: Semiring[V] | type[Semiring[V]] | str | None = None) -> None:
        self._semiring: Semiring[V] = Semiring.normalize(semiring)

    @property
    def semiring(self) -> Semiring[V]:
        """The underlying coefficient semiring S."""
        return self._semiring

    def id(self, x: Iterable[K]) -> SparseMatrix[K, V]:
        r"""Construct the sparse identity matrix $\mathbf{I}_x = \{k: \{k: 1_{\mathcal{S}}\} \mid k \in x\}$."""
        one = self._semiring.one
        zero = self._semiring.zero
        if one == zero:
            return {}
        return {k: {k: one} for k in x}

    def compose(self, f: SparseMatrix[K, V], g: SparseMatrix[K, V]) -> SparseMatrix[K, V]:
        r"""Compose matrix morphisms $f$ and $g$ via semiring matrix multiplication $\mathrm{dot}(f, g)$."""
        return dot(f, g, semiring=self._semiring)

    def source(self, f: SparseMatrix[K, V]) -> frozenset[K]:
        r"""Return the active row index support $\mathrm{dom}(f) = \{r \mid f_r \ne \emptyset\}$."""
        return frozenset(r for r, row in f.items() if row)

    def target(self, f: SparseMatrix[K, V]) -> frozenset[K]:
        r"""Return the active column index support $\mathrm{cod}(f) = \bigcup_r \mathrm{keys}(f_r)$."""
        targets: set[K] = set()
        for row in f.values():
            targets.update(row.keys())
        return frozenset(targets)

    def opposite(self) -> OppositeCategory[frozenset[K], SparseMatrix[K, V]]:
        r"""Return the opposite category $\mathbf{Mat}(\mathcal{S})^{\mathrm{op}}$."""
        return OppositeCategory(self)


class TransposeFunctor(Functor[frozenset[K], SparseMatrix[K, V], frozenset[K], SparseMatrix[K, V]], Generic[K, V]):
    r"""Duality functor $(-)^T : \mathbf{Mat}(\mathcal{S})^{\mathrm{op}} \xrightarrow{\sim} \mathbf{Mat}(\mathcal{S})$.

    For any commutative semiring $\mathcal{S}$, matrix transposition is an isomorphism of categories
    between $\mathbf{Mat}(\mathcal{S})^{\mathrm{op}}$ and $\mathbf{Mat}(\mathcal{S})$:
        $(f \cdot g)^T = g^T \cdot f^T \quad \text{and} \quad (\mathbf{I}_A)^T = \mathbf{I}_A$.
    """

    def map_obj(self, x: frozenset[K]) -> frozenset[K]:
        return x

    def map_mor(self, f: SparseMatrix[K, V]) -> SparseMatrix[K, V]:
        return transpose(f)


class SemiringChangeOfBaseFunctor(
    Functor[frozenset[K], SparseMatrix[K, V], frozenset[K], SparseMatrix[K, W]],
    Generic[K, V, W],
):
    r"""Scalar change-of-base functor $\mathbf{Mat}(\phi): \mathbf{Mat}(\mathcal{R}) \to \mathbf{Mat}(\mathcal{S})$.

    Given a semiring homomorphism $\phi: \mathcal{R} \to \mathcal{S}$ preserving $0, 1, +, \cdot$,
    applying $\phi$ entrywise to every sparse matrix entry induces a strict functor between matrix categories.
    """

    def __init__(
        self,
        scalar_map: Callable[[V], W],
        target_semiring: Semiring[W] | type[Semiring[W]] | str | None = None,
    ) -> None:
        self._phi = scalar_map
        self._target_semiring = Semiring.normalize(target_semiring)

    def map_obj(self, x: frozenset[K]) -> frozenset[K]:
        return x

    def map_mor(self, f: SparseMatrix[K, V]) -> SparseMatrix[K, W]:
        zero_w = self._target_semiring.zero
        phi = self._phi
        out: dict[K, dict[K, W]] = {}
        for r, row in f.items():
            mapped_row = {c: mapped_val for c, val in row.items() if (mapped_val := phi(val)) != zero_w}
            if mapped_row:
                out[r] = mapped_row
        return out


__all__ = [
    'MatrixCategory',
    'SemiringChangeOfBaseFunctor',
    'TransposeFunctor',
]
