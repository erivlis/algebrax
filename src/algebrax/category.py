"""
Categorical Morphisms, Kleisli Composition & Operads.

Summary:
    Pipeline composition with side-effects — chains functions over semirings using
    Kleisli matrix composition and Kan extensions.

This module provides formal category-theoretic abstractions: Kleisli monadic composition (g o_T f),
string diagram wiring engines, and Kan extensions over sparse semiring matrices.
"""

from typing import TypeVar

from algebrax.matrix.core import dot
from algebrax.semiring import Semiring, StandardSemiring
from algebrax.typing import SparseMatrix

K = TypeVar('K')
V = TypeVar('V')
W = TypeVar('W')
T_Coeff = TypeVar('T_Coeff')


def kleisli_compose(
    f: SparseMatrix[K, T_Coeff],
    g: SparseMatrix[V, T_Coeff],
    semiring: Semiring[T_Coeff] | None = None,
) -> SparseMatrix[K, T_Coeff]:
    """
    Compose effectful monadic morphisms f: K -> T(V) and g: V -> T(W)
    using Kleisli matrix composition (g o_T f) over the monad's semiring.

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
    s = semiring if semiring is not None else StandardSemiring()
    return dot(f, g, semiring=s)


def kan_extension_left(
    functor_p: SparseMatrix,
    functor_f: SparseMatrix,
    semiring: Semiring | None = None,
) -> SparseMatrix:
    """
    Compute Left Kan Extension Lan_P F over sparse categories.

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
    s = semiring if semiring is not None else StandardSemiring()
    return dot(functor_f, functor_p, semiring=s)
