r"""
Alexander-Whitney Simplicial Chain Coalgebra (EP-0206).

Formalizes the Alexander-Whitney coproduct on simplicial chains $C_*(K)$:
$$\Delta(\sigma) = \sum_{i=1}^{n+1} \sigma[:i] \otimes \sigma[i-1:]$$
whose linear dual evaluation generates the cochain cup product $\smile$.
"""

from __future__ import annotations

from typing import Any

from algebrax.algebra._hopf import Coalgebra
from algebrax.typing import SparseVector


class SimplicialChainCoalgebra(Coalgebra[float, SparseVector[tuple[int, ...], float]]):
    r"""Simplicial chain complex $C_*(K)$ equipped with the Alexander-Whitney coproduct.

    - Carrier: `dict[tuple[int, ...], float]` (Sparse linear combination of oriented simplices).
    - Coproduct: Alexander-Whitney diagonal approximation $\Delta: C_*(K) \to C_*(K) \otimes C_*(K)$.
    - Counit: $\epsilon([v_0]) = 1$, $\epsilon(\sigma) = 0$ for $\dim(\sigma) \ge 1$.
    """

    @property
    def zero(self) -> SparseVector[tuple[int, ...], float]:
        return {}

    def add(
        self,
        a: SparseVector[tuple[int, ...], float],
        b: SparseVector[tuple[int, ...], float],
    ) -> SparseVector[tuple[int, ...], float]:
        res = dict(a)
        for k, v in b.items():
            res[k] = res.get(k, 0.0) + v
        return {k: v for k, v in res.items() if abs(v) > 1e-15}

    def neg(
        self,
        a: SparseVector[tuple[int, ...], float],
    ) -> SparseVector[tuple[int, ...], float]:
        return {k: -v for k, v in a.items() if abs(v) > 1e-15}

    def smul(
        self,
        r: float,
        a: SparseVector[tuple[int, ...], float],
    ) -> SparseVector[tuple[int, ...], float]:
        rf = float(r)
        if abs(rf) <= 1e-15:
            return {}
        return {k: rf * v for k, v in a.items() if abs(rf * v) > 1e-15}

    def coproduct(
        self,
        chain: SparseVector[tuple[int, ...], float],
    ) -> dict[tuple[tuple[int, ...], tuple[int, ...]], float]:
        r"""Compute the Alexander-Whitney coproduct:
        $$\Delta([v_0, \dots, v_n]) = \sum_{i=1}^{n+1} [v_0, \dots, v_{i-1}] \otimes [v_{i-1}, \dots, v_n]$$
        """
        tensor: dict[tuple[tuple[int, ...], tuple[int, ...]], float] = {}
        for simplex, coeff in chain.items():
            cf = float(coeff)
            if abs(cf) <= 1e-15:
                continue
            n = len(simplex)
            for i in range(1, n + 1):
                front_face = simplex[:i]
                back_face = simplex[i - 1 :]
                key = (front_face, back_face)
                tensor[key] = tensor.get(key, 0.0) + cf
        return {k: v for k, v in tensor.items() if abs(v) > 1e-15}

    def counit(self, chain: SparseVector[tuple[int, ...], float]) -> float:
        r"""Compute counit $\epsilon(\text{chain}) = \sum \{c_v : [v] \in \text{chain}, \dim([v]) = 0\}$."""
        return float(sum(coeff for simplex, coeff in chain.items() if len(simplex) == 1))
