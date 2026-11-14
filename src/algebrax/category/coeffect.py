r"""
Semiring-Graded Coeffects & Resource-Sensitive Context Algebras.

Formalizes coeffect typing contexts $\Gamma: V \to S$ over an arbitrary `Semiring[S]`,
unifying:
- Linear / Bounded Variable Reuse Tracking over $(\mathbb{N}, +, \times, 0, 1)$
- Dead-Code & Liveness Analysis over `BooleanSemiring` $(\mathbb{B}, \lor, \land, \bot, \top)$
- Latency / Privacy Sensitivity Budgets over `TropicalSemiring` $(\mathbb{R} \cup \{\infty\}, \min, +, \infty, 0)$

Context Operations:
- Context Addition ($\Gamma_1 + \Gamma_2$): Pointwise semiring addition
  $(\Gamma_1 + \Gamma_2)(x) = \Gamma_1(x) \oplus \Gamma_2(x)$ governing parallel / sequential variable splitting.
- Context Scaling ($r \cdot \Gamma$): Pointwise left semiring multiplication $(r \cdot \Gamma)(x) = r \otimes \Gamma(x)$
  governing nested modal / loop amplification.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Generic, TypeVar

from algebrax.algebra._module import Semimodule
from algebrax.algebra._semiring import Semiring

K = TypeVar('K')
S = TypeVar('S')


class CoeffectContext(Semimodule[S, dict[K, S]], Generic[K, S]):
    r"""Semiring-graded coeffect context algebra over unboxed sparse mappings `dict[K, S]`.

    Algebraic Signature:
        $\langle S^K, \mathbf{0}, \oplus, \cdot_S \rangle$ (Left $S$-Semimodule of typing contexts)

    Laws:
        - Left Distributivity of Scaling over Context Addition:
          $r \cdot (\Gamma_1 + \Gamma_2) = (r \cdot \Gamma_1) + (r \cdot \Gamma_2)$
        - Right Distributivity of Semiring Addition over Scaling:
          $(r \oplus s) \cdot \Gamma = (r \cdot \Gamma) + (s \cdot \Gamma)$
        - Multiplicative Associativity of Nested Modalities:
          $(r \otimes s) \cdot \Gamma = r \cdot (s \cdot \Gamma)$
        - Unitality & Annihilation:
          $\mathbf{1}_S \cdot \Gamma = \Gamma$ and $\mathbf{0}_S \cdot \Gamma = \mathbf{0}$
    """

    def __init__(self, semiring: Semiring[S]) -> None:
        self.semiring = semiring

    @property
    def zero(self) -> dict[K, S]:
        r"""Empty zero-usage context $\mathbf{0}$."""
        return {}

    def singleton(self, var: K, grade: S | None = None) -> dict[K, S]:
        r"""Single-variable context $[x : r]$ (defaults to $r = \mathbf{1}_S$)."""
        g = self.semiring.one if grade is None else grade
        if g == self.semiring.zero:
            return {}
        return {var: g}

    def grade_of(self, ctx: Mapping[K, S], var: K) -> S:
        r"""Query the coeffect grade $\Gamma(x) \in S$ (returns $\mathbf{0}_S$ if absent)."""
        return ctx.get(var, self.semiring.zero)

    def add(self, ctx1: Mapping[K, S], ctx2: Mapping[K, S]) -> dict[K, S]:
        r"""Combine two contexts $(\Gamma_1 + \Gamma_2)(x) = \Gamma_1(x) \oplus \Gamma_2(x)$."""
        s = self.semiring
        z = s.zero
        keys = set(ctx1.keys()) | set(ctx2.keys())
        out: dict[K, S] = {}
        for k in keys:
            val = s.add(ctx1.get(k, z), ctx2.get(k, z))
            if val != z:
                out[k] = val
        return out

    def scale(self, grade: S, ctx: Mapping[K, S]) -> dict[K, S]:
        r"""Scale a context by an outer modal grade $(r \cdot \Gamma)(x) = r \otimes \Gamma(x)$."""
        s = self.semiring
        z = s.zero
        if grade == z:
            return {}
        out: dict[K, S] = {}
        for k, v in ctx.items():
            prod = s.mul(grade, v)
            if prod != z:
                out[k] = prod
        return out

    def smul(self, r: S, m: Mapping[K, S]) -> dict[K, S]:
        r"""Left scalar action $r \cdot_S \Gamma$ (`HasScale` / `Semimodule` interface)."""
        return self.scale(r, m)


class SemiringCoeffectTracker(Generic[K, S]):
    r"""Imperative and compositional resource tracker graded by a `Semiring[S]`."""

    def __init__(self, semiring: Semiring[S]) -> None:
        self.semiring = semiring
        self.context_algebra: CoeffectContext[K, S] = CoeffectContext(semiring)
        self._costs: dict[K, S] = {}

    @property
    def costs(self) -> dict[K, S]:
        """Return a snapshot of recorded operation grades."""
        return dict(self._costs)

    def record_cost(self, operation: K, cost: S) -> None:
        r"""Accumulate resource usage for `operation` via semiring addition $\oplus$."""
        if operation in self._costs:
            self._costs[operation] = self.semiring.add(self._costs[operation], cost)
        else:
            self._costs[operation] = cost

    def get_cost(self, operation: K) -> S:
        r"""Return recorded cost for `operation`, or $\mathbf{0}_S$ if unused."""
        return self._costs.get(operation, self.semiring.zero)

    def compose_parallel(self, op1: K, op2: K) -> S:
        r"""Combine costs of two co-occurring operations via semiring addition $c_1 \oplus c_2$."""
        c1 = self._costs.get(op1, self.semiring.zero)
        c2 = self._costs.get(op2, self.semiring.zero)
        return self.semiring.add(c1, c2)

    def compose_sequence(self, op1: K, op2: K) -> S:
        r"""Compose nested/chained operation costs via semiring multiplication $c_1 \otimes c_2$."""
        c1 = self._costs.get(op1, self.semiring.one)
        c2 = self._costs.get(op2, self.semiring.one)
        return self.semiring.mul(c1, c2)


__all__ = [
    'CoeffectContext',
    'SemiringCoeffectTracker',
]
