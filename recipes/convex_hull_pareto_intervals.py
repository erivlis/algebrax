# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Convex Hull Semiring, Pareto Frontiers & Interval Uncertainty
#
# ## Theory & Mathematical Foundation
#
# 1. **Dyer Convex Hull Semiring (Dyer 2013)**:
#    In robust control, guaranteed reachability, and multi-objective optimization, exact values
#    are often unknown or represent trade-off frontiers.
#    The Convex Hull Semiring defines:
#    - **Addition ($\oplus$)**: Convex Hull of the union:
#      $\text{Conv}(A \cup B) = [\min(a_1, b_1), \max(a_2, b_2)]$.
#    - **Multiplication ($\otimes$)**: Minkowski Sum:
#      $A + B = \{a + b \mid a \in A, b \in B\} = [a_1 + b_1, a_2 + b_2]$.
#
# 2. **Multi-Criterion Routing & Pareto Uncertainty**:
#    When routing autonomous vehicles under weather or latency jitter, each edge incurs an interval
#    cost $[\\text{min\\_delay}, \\text{max\\_delay}]$.
#    Composing edges via Minkowski addition yields guaranteed hard worst-case and best-case performance bounds.

# %%
import algebrax as ax

Interval = tuple[float, float]


class IntervalSemiring(ax.semiring.Semiring[Interval]):
    """Convex Hull Interval Semiring over bounding intervals."""

    @property
    def zero(self) -> Interval:
        return (float('inf'), float('-inf'))

    @property
    def one(self) -> Interval:
        return (0.0, 0.0)

    def add(self, a: Interval, b: Interval) -> Interval:
        return (min(a[0], b[0]), max(a[1], b[1]))

    def mul(self, a: Interval, b: Interval) -> Interval:
        return (a[0] + b[0], a[1] + b[1])


def propagate_interval_path(
    edge_intervals: list[Interval],
    semiring: IntervalSemiring | None = None,
) -> Interval:
    """Accumulate cumulative Minkowski uncertainty intervals along a path."""
    sem = semiring if semiring is not None else IntervalSemiring()
    curr = sem.one
    for iv in edge_intervals:
        curr = sem.mul(curr, iv)
    return curr


def evaluate_pareto_network_reachability(
    graph: dict[int, dict[int, Interval]],
    steps: int = 3,
) -> dict[int, dict[int, Interval]]:
    """Compute all-pairs guaranteed bounding intervals over multi-hop routing paths."""
    sem = IntervalSemiring()
    return ax.matrix.power(graph, steps, semiring=sem)


# %% [markdown]
# ## Step 1: Interval Convex Hull & Minkowski Sum Arithmetic
#
# ## Step 2: Multi-Hop Robust Routing Uncertainty Propagation


def run_demo() -> None:
    """Run interval arithmetic and guaranteed reachability demonstrations."""
    sem = IntervalSemiring()

    print('==========================================================================')
    print('Step 1: Convex Hull Union & Minkowski Sum Primitives')
    print('==========================================================================')
    iv_a = (1.0, 4.0)
    iv_b = (3.0, 7.0)

    hull_union = sem.add(iv_a, iv_b)
    minkowski_sum = sem.mul(iv_a, iv_b)

    print(f'Interval A: {iv_a}')
    print(f'Interval B: {iv_b}')
    print(f'Convex Hull Union A (+) B:   {hull_union} (Enclosing Span)')
    print(f'Minkowski Sum A (*) B:       {minkowski_sum} (Combined Bound)')
    assert hull_union == (1.0, 7.0)
    assert minkowski_sum == (4.0, 11.0)

    print('\n==========================================================================')
    print('Step 2: 3-Hop Robust Network Route Latency Guarantees')
    print('==========================================================================')
    network = {
        0: {1: (2.0, 5.0), 2: (1.0, 3.0)},
        1: {3: (4.0, 8.0)},
        2: {3: (6.0, 12.0)},
        3: {},
    }

    path1 = propagate_interval_path([network[0][1], network[1][3]])
    path2 = propagate_interval_path([network[0][2], network[2][3]])
    robust_envelope = sem.add(path1, path2)

    print(f'Route 0 -> 1 -> 3 Latency Range: {path1} ms')
    print(f'Route 0 -> 2 -> 3 Latency Range: {path2} ms')
    print(f'Combined Robust Envelope (Hull):  {robust_envelope} ms')
    assert robust_envelope[0] <= min(path1[0], path2[0])
    assert robust_envelope[1] >= max(path1[1], path2[1])


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('\n==========================================================================')
    print('Recipe: Convex Hull Semiring & Pareto Uncertainty Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
