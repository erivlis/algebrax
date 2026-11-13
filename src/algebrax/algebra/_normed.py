r"""
Normed, Banach, and Inner Product (Hilbert) space protocols.

Algebraic Signatures:
    Normed Space:         $\langle R, V, \cdot_s, \mathbf{0}, +, -, \|\cdot\| \rangle$
    Inner Product Space:  $\langle R, V, \cdot_s, \mathbf{0}, +, -, \|\cdot\|, \langle \cdot, \cdot \rangle \rangle$
"""

import math
from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import HasAdd, HasInner, HasNeg, HasNorm, HasScale, HasZero

R = TypeVar('R')
V = TypeVar('V')


@runtime_checkable
class NormedSpace(HasZero[V], HasAdd[V], HasNeg[V], HasScale[R, V], HasNorm[V], Protocol):
    r"""A vector space $V$ over field $R$ equipped with a norm $\|\cdot\| : V \to \mathbb{R}_{\ge 0}$.

    Algebraic Signature:
        $\langle R, V, \cdot_s, \mathbf{0}, +, -, \|\cdot\| \rangle$

    Axioms:
        - Absolute Scalability: $\|\alpha \cdot_s v\| = |\alpha| \cdot \|v\|$.
        - Subadditivity (Triangle Inequality): $\|u + v\| \le \|u\| + \|v\|$.
        - Definiteness: $\|v\| = 0 \iff v = \mathbf{0}$.
    """

    def sub(self, a: V, b: V) -> V:
        r"""Vector difference $a - b = a + (-b)$."""
        return self.add(a, self.neg(b))

    def distance(self, u: V, v: V) -> float:
        r"""Induced metric distance $d(u, v) = \|u - v\|_V$."""
        return self.norm(self.sub(u, v))


@runtime_checkable
class InnerProductSpace(
    HasZero[V], HasAdd[V], HasNeg[V], HasScale[R, V], HasNorm[V], HasInner[R, V], Protocol
):
    r"""An inner product space (finite-dimensional Hilbert space) equipped with $\langle u, v \rangle$.

    Algebraic Signature:
        $\langle R, V, \cdot_s, \mathbf{0}, +, -, \|\cdot\|, \langle \cdot, \cdot \rangle \rangle$

    Axioms:
        - Linearity in first argument:
          $\langle \alpha u + v, w \rangle = \alpha \langle u, w \rangle + \langle v, w \rangle$.
        - Conjugate/Real Symmetry: $\langle u, v \rangle = \overline{\langle v, u \rangle}$.
        - Positive Definiteness: $\langle v, v \rangle \ge 0$, and $\langle v, v \rangle = 0 \iff v = \mathbf{0}$.
        - Induced Norm: $\|v\| = \sqrt{\langle v, v \rangle}$.
    """

    def sub(self, a: V, b: V) -> V:
        r"""Vector difference $a - b = a + (-b)$."""
        return self.add(a, self.neg(b))

    def norm(self, v: V) -> float:
        r"""Induced Euclidean norm $\|v\| = \sqrt{\langle v, v \rangle}$."""
        val = self.inner(v, v)
        if isinstance(val, complex):
            return math.sqrt(max(0.0, val.real))
        return math.sqrt(max(0.0, float(val)))  # type: ignore[arg-type]

    def distance(self, u: V, v: V) -> float:
        r"""Induced metric distance $d(u, v) = \|u - v\| = \sqrt{\langle u-v, u-v \rangle}$."""
        return self.norm(self.sub(u, v))
