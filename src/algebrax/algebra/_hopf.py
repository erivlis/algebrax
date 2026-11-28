r"""
Coalgebras, Bialgebras, and Hopf Algebras (EP-0206).

Completes the arrow-reversal categorical duality of algebraic structures:
- Coalgebras with comultiplication $\Delta: C \to C \otimes C$ and counit $\epsilon: C \to R$
- Bialgebras combining compatible algebra and coalgebra structures
- Hopf algebras equipped with an antipode $S: H \to H$ (quantum inverse)
- Concrete Group Hopf algebras, Divided Power coalgebras, and Primitive Enveloping Hopf algebras

All tensor products $C \otimes C$ are represented using unboxed sparse tuple keys `(k1, k2)`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, Literal, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._field import StandardField
from algebrax.algebra._group import Group
from algebrax.algebra._mixins import (
    HasAdd,
    HasAntipode,
    HasCoproduct,
    HasCounit,
    HasMul,
    HasNeg,
    HasOne,
    HasScale,
    HasZero,
    LawAssociative,
)
from algebrax.algebra._monoid_algebra import MonoidAlgebra
from algebrax.algebra._ring import Ring
from algebrax.converters import make_zero_predicate
from algebrax.typing import SparseVector

R = TypeVar('R')
C = TypeVar('C')
T = TypeVar('T')


@runtime_checkable
class Coalgebra(
    HasScale[R, C],
    HasZero[C],
    HasAdd[C],
    HasNeg[C],
    HasCoproduct[C],
    HasCounit[R, C],
    Protocol[R, C],
):
    r"""A coalgebra $\langle R, C, \cdot_s, \mathbf{0}, +, -, \Delta, \epsilon \rangle$ over ring/field $R$.

    Axioms:
        - Coassociativity: $(\Delta \otimes \mathrm{id}) \circ \Delta = (\mathrm{id} \otimes \Delta) \circ \Delta$.
        - Counitality:
          $(\epsilon \otimes \mathrm{id}) \circ \Delta = \mathrm{id} = (\mathrm{id} \otimes \epsilon) \circ \Delta$.
    """

    def sub(self, a: C, b: C) -> C:
        r"""Vector difference $a - b = a + (-b)$."""
        return self.add(a, self.neg(b))


@runtime_checkable
class Bialgebra(
    HasScale[R, C],
    HasZero[C],
    HasAdd[C],
    HasNeg[C],
    HasOne[C],
    HasMul[C],
    HasCoproduct[C],
    HasCounit[R, C],
    LawAssociative,
    Protocol[R, C],
):
    r"""A bialgebra: flat composition of Algebra and Coalgebra atomic mixins.

    Axioms:
        - Algebra axioms: $(C, +, \mathbf{0}, \cdot, \mathbf{1}, \cdot_s)$ is an associative unital algebra.
        - Coalgebra axioms: $(C, \Delta, \epsilon)$ is a coassociative counital coalgebra.
        - Homomorphism Compatibility:
            $\Delta(a \cdot b) = \Delta(a) \cdot \Delta(b)$,
            $\Delta(\mathbf{1}) = \mathbf{1} \otimes \mathbf{1}$,
            $\epsilon(a \cdot b) = \epsilon(a) \epsilon(b)$,
            $\epsilon(\mathbf{1}) = 1_R$.
    """

    @property
    def is_associative(self) -> Literal[True]:
        return True

    def sub(self, a: C, b: C) -> C:
        r"""Vector difference $a - b = a + (-b)$."""
        return self.add(a, self.neg(b))


@runtime_checkable
class HopfAlgebra(
    HasScale[R, C],
    HasZero[C],
    HasAdd[C],
    HasNeg[C],
    HasOne[C],
    HasMul[C],
    HasCoproduct[C],
    HasCounit[R, C],
    HasAntipode[C],
    LawAssociative,
    Protocol[R, C],
):
    r"""A Hopf algebra: a bialgebra equipped with an antipode $S: C \to C$ satisfying:
    $$\mu \circ (S \otimes \mathrm{id}) \circ \Delta = \eta \circ \epsilon$$
    $$\mu \circ (\mathrm{id} \otimes S) \circ \Delta = \eta \circ \epsilon$$
    where $\mu(a \otimes b) = a \cdot b$ and $\eta(r) = r \cdot_s \mathbf{1}$.
    """

    @property
    def is_associative(self) -> Literal[True]:
        return True

    def sub(self, a: C, b: C) -> C:
        r"""Vector difference $a - b = a + (-b)$."""
        return self.add(a, self.neg(b))


class GroupHopfAlgebra(MonoidAlgebra[Any, T], HopfAlgebra[T, SparseVector[Any, T]], Generic[T]):
    r"""Group Hopf algebra $R[G]$ over unboxed sparse group linear combinations `dict[G, T]`.

    - Multiplication: Group convolution $g \cdot h$ (inherited from `MonoidAlgebra`).
    - Coproduct: $\Delta(\sum c_g g) = \sum c_g (g \otimes g)$ (all group elements are group-like).
    - Counit: $\epsilon(\sum c_g g) = \sum c_g$.
    - Antipode: $S(\sum c_g g) = \sum c_g g^{-1}$.
    """

    def __init__(self, group: Group[Any], coeff_semiring: Ring[T] | None = None) -> None:
        if coeff_semiring is None:
            coeff_semiring = StandardField(float)  # type: ignore[assignment]
        elif not isinstance(coeff_semiring, Ring):
            raise TypeError(
                f'GroupHopfAlgebra requires a Ring coefficient structure, got {type(coeff_semiring).__name__}.'
            )
        key_op = getattr(group, 'mul', getattr(group, 'op', None))
        zero_key = getattr(group, 'one', getattr(group, 'identity', getattr(group, 'zero', 0)))
        super().__init__(coeff_semiring, key_op=key_op, zero_key=zero_key)
        self.group = group
        self._is_zero = make_zero_predicate(self.coeff_semiring)

    def coproduct(self, x: SparseVector[Any, T]) -> dict[tuple[Any, Any], T]:
        r"""Comultiplication $\Delta(g) = g \otimes g$."""
        is_zero = self._is_zero
        return {(g, g): coeff for g, coeff in x.items() if not is_zero(coeff)}

    def counit(self, x: SparseVector[Any, T]) -> T:
        r"""Counit $\epsilon(\sum c_g g) = \sum c_g$."""
        acc = self.coeff_semiring.zero
        add_fn = self.coeff_semiring.add
        for coeff in x.values():
            acc = add_fn(acc, coeff)
        return acc

    def antipode(self, x: SparseVector[Any, T]) -> SparseVector[Any, T]:
        r"""Antipode $S(g) = g^{-1}$ extended by linearity."""
        res: dict[Any, T] = {}
        add_fn = self.coeff_semiring.add
        zero = self.coeff_semiring.zero
        inv_fn = self.group.inv
        is_zero = self._is_zero
        for g, coeff in x.items():
            if is_zero(coeff):
                continue
            inv_g = inv_fn(g)
            new_c = add_fn(res.get(inv_g, zero), coeff)
            if is_zero(new_c):
                res.pop(inv_g, None)
            else:
                res[inv_g] = new_c
        return res


class DividedPowerCoalgebra(Coalgebra[float, SparseVector[int, float]]):
    r"""Divided power coalgebra $\Gamma(x) = \bigoplus_{n \ge 0} R \cdot x^{[n]}$.

    Coproduct:
        $$\Delta(x^{[n]}) = \sum_{k=0}^n x^{[k]} \otimes x^{[n-k]}$$
    Counit:
        $$\epsilon(x^{[n]}) = \delta_{n, 0}$$
    """

    @property
    def zero(self) -> SparseVector[int, float]:
        return {}

    def add(
        self,
        a: SparseVector[int, float],
        b: SparseVector[int, float],
    ) -> SparseVector[int, float]:
        res = dict(a)
        for k, v in b.items():
            res[k] = res.get(k, 0.0) + v
        return {k: v for k, v in res.items() if abs(v) > 1e-15}

    def neg(self, a: SparseVector[int, float]) -> SparseVector[int, float]:
        return {k: -v for k, v in a.items() if abs(v) > 1e-15}

    def smul(self, r: float, a: SparseVector[int, float]) -> SparseVector[int, float]:
        rf = float(r)
        if abs(rf) <= 1e-15:
            return {}
        return {k: rf * v for k, v in a.items() if abs(rf * v) > 1e-15}

    def coproduct(self, c: SparseVector[int, float]) -> dict[tuple[int, int], float]:
        r"""Compute $\Delta(x^{[n]}) = \sum_{k=0}^n x^{[k]} \otimes x^{[n-k]}$."""
        tensor: dict[tuple[int, int], float] = {}
        for n, coeff in c.items():
            cf = float(coeff)
            if abs(cf) <= 1e-15:
                continue
            for k in range(n + 1):
                key = (k, n - k)
                tensor[key] = tensor.get(key, 0.0) + cf
        return {k: v for k, v in tensor.items() if abs(v) > 1e-15}

    def counit(self, c: SparseVector[int, float]) -> float:
        r"""Compute $\epsilon(c) = c_0$ (degree 0 coefficient)."""
        return float(c.get(0, 0.0))
