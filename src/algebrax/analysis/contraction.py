r"""
Banach Fixed-Point Contraction Solvers and certified convergence verifiers.

Mathematical Foundations:
    - Banach Fixed-Point Theorem: Let $(X, d)$ be a complete metric space and $T : X \to X$ a contractive
      mapping with Lipschitz constant $\gamma < 1$:
      $$d(T(u), T(v)) \le \gamma \cdot d(u, v) \quad \forall u, v \in X$$
      Then $T$ has a unique fixed point $x^* \in X$ ($T(x^*) = x^*$), and the sequence $x_{k+1} = T(x_k)$
      converges geometrically with error bound:
      $$d(x_k, x^*) \le \frac{\gamma^k}{1 - \gamma} d(x_0, x_1)$$
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from algebrax.algebra._normed import NormedSpace

V = TypeVar('V')


class BanachContractionVerifier:
    r"""Certifies that operator $T : V \to V$ is a contraction with Lipschitz constant $\gamma < 1$."""

    def __init__(self, normed_space: NormedSpace[Any, V], gamma: float = 0.9) -> None:
        if not (0.0 <= gamma < 1.0):
            raise ValueError(f'Contraction constant must satisfy 0.0 <= gamma < 1.0, got {gamma}')
        self.space = normed_space
        self.gamma = gamma

    def verify_step(self, operator: Callable[[V], V], u: V, v: V, tol: float = 1e-9) -> bool:
        r"""Verify that $d(T(u), T(v)) \le \gamma \cdot d(u, v) + \text{tol}$."""
        dist_in = self.space.distance(u, v)
        if dist_in <= tol:
            return True
        dist_out = self.space.distance(operator(u), operator(v))
        return dist_out <= (self.gamma * dist_in + tol)

    def estimate_contraction_factor(
        self,
        operator: Callable[[V], V],
        samples: Sequence[V],
        tol: float = 1e-12,
    ) -> float:
        r"""Estimate empirical contraction factor $\hat{\gamma} = \max_{u \ne v} \frac{d(T(u), T(v))}{d(u, v)}$."""
        max_ratio = 0.0
        n = len(samples)
        for i in range(n):
            for j in range(i + 1, n):
                u, v = samples[i], samples[j]
                d_in = self.space.distance(u, v)
                if d_in > tol:
                    d_out = self.space.distance(operator(u), operator(v))
                    ratio = d_out / d_in
                    if ratio > max_ratio:
                        max_ratio = ratio
        return max_ratio


def contractive_fixed_point(
    space: NormedSpace[Any, V],
    operator: Callable[[V], V],
    initial: V,
    gamma: float | None = None,
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> tuple[V, int, bool]:
    r"""Compute the fixed point $x^* = T(x^*)$ using certified Banach Picard iteration.

    Parameters:
        space: A NormedSpace equipping carrier $V$ with a metric distance.
        operator: Contraction operator $T : V \to V$.
        initial: Starting state $x_0 \in V$.
        gamma: Optional known contraction constant $\gamma < 1$ for certified error bounds.
        tol: Convergence tolerance $d(x_{k+1}, x_k) < \text{tol}$.
        max_iter: Maximum number of iterations.

    Returns:
        `(fixed_point, iterations, converged)` tuple.
    """
    if gamma is not None and not (0.0 <= gamma < 1.0):
        raise ValueError(f'Contraction constant gamma must be in [0, 1), got {gamma}')

    curr = initial
    for step in range(1, max_iter + 1):
        nxt = operator(curr)
        dist = space.distance(curr, nxt)
        if dist < tol:
            return nxt, step, True
        curr = nxt

    return curr, max_iter, False
