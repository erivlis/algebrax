"""
Categorical Morphisms, Kleisli Composition & Operads (EP-0113).

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
    """
    s = semiring if semiring is not None else StandardSemiring()
    return dot(functor_f, functor_p, semiring=s)
