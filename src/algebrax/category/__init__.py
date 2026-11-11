"""
Categorical Morphisms, Enriched Matrix Categories, Kleisli Composition & Kan Extensions.

Summary:
    Unifies Lean 4 Mathlib-aligned Category and Functor protocols (`Category`, `Functor`,
    `OppositeCategory`), the Matrix Category `Mat(S)` (`MatrixCategory`, `TransposeFunctor`,
    `SemiringChangeOfBaseFunctor`), Lawvere Metric Spaces (`LawvereMetricCategory`),
    and monadic Kleisli / Kan extension operators (`kleisli_compose`, `kan_extension_left`).
"""

from __future__ import annotations

from typing import TypeVar

from algebrax.category.core import Category, Functor, OppositeCategory
from algebrax.category.enriched import LawvereMetricCategory
from algebrax.category.matrix import (
    MatrixCategory,
    SemiringChangeOfBaseFunctor,
    TransposeFunctor,
)
from algebrax.matrix.core import dot
from algebrax.semiring import Semiring
from algebrax.typing import SparseMatrix

K = TypeVar('K')
V = TypeVar('V')
W = TypeVar('W')
T_Coeff = TypeVar('T_Coeff')


def kleisli_compose(
    f: SparseMatrix[K, T_Coeff],
    g: SparseMatrix[V, T_Coeff],
    semiring: Semiring[T_Coeff] | type[Semiring[T_Coeff]] | None = None,
) -> SparseMatrix[K, T_Coeff]:
    r"""Compose effectful monadic morphisms $f: K \to T(V)$ and $g: V \to T(W)$.

    Algebraic Signature:
        $f: A \to T(B), \quad g: B \to T(C) \implies g \circ_T f: A \to T(C) \quad \text{in} \quad \mathbf{Kl}(T)$

    Composition Law (Kleisli Fish Operator):
        $(g \circ_T f)(x) = \mu_C(T(g)(f(x)))$

    Monad Laws:
        - Left Identity: $\eta_B \circ_T f = f$
        - Right Identity: $f \circ_T \eta_A = f$
        - Associativity: $(h \circ_T g) \circ_T f = h \circ_T (g \circ_T f)$

    Args:
        f: First monadic matrix morphism.
        g: Second monadic matrix morphism.
        semiring: Underlying semiring for monadic composition.

    Returns:
        The composed Kleisli matrix (g o_T f).

    Example:
        >>> f = {'a': {'b': 2.0}}
        >>> g = {'b': {'c': 3.0}}
        >>> res = kleisli_compose(f, g)
        >>> res == {'a': {'c': 6.0}}
        True
    """
    s = Semiring.normalize(semiring)
    return dot(f, g, semiring=s)


def kan_extension_left(
    functor_p: SparseMatrix[K, V],
    functor_f: SparseMatrix[V, W],
    semiring: Semiring | type[Semiring] | None = None,
) -> SparseMatrix[K, W]:
    r"""Compute Left Kan Extension $\mathrm{Lan}_P F$ over sparse categories.

    Algebraic Signature:
        $\mathrm{Lan}_P F(c) \cong \mathrm{colim}_{(P(d) \to c)} F(d)$

    Args:
        functor_p: Sparse matrix functor P.
        functor_f: Sparse matrix functor F.
        semiring: Semiring structure for composition.

    Returns:
        Left Kan extension matrix.

    Example:
        >>> p = {0: {1: 1.0}}
        >>> f = {0: {0: 2.0}}
        >>> lan = kan_extension_left(p, f)
        >>> lan == {0: {1: 2.0}}
        True
    """
    s = Semiring.normalize(semiring)
    return dot(functor_f, functor_p, semiring=s)


__all__ = [
    'Category',
    'Functor',
    'LawvereMetricCategory',
    'MatrixCategory',
    'OppositeCategory',
    'SemiringChangeOfBaseFunctor',
    'TransposeFunctor',
    'kan_extension_left',
    'kleisli_compose',
]
