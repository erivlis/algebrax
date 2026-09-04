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
# # Combinatorial Dyck Paths, Catalan Numbers & Graph Walks
#
# ## Theory & Mathematical Foundation
#
# 1. **Catalan Numbers ($C_n$) & Dyck Paths**:
#    A Dyck path of length $2n$ is a lattice path in $\\mathbb{Z}^2$ from $(0, 0)$ to $(2n, 0)$ using
#    steps $(1, 1)$ (Up) and $(1, -1)$ (Down) that never descends below the horizontal axis ($y \\ge 0$).
#    The number of such paths is given by the $n$-th Catalan number:
#    $$C_n = \\frac{1}{n+1} \\binom{2n}{n}$$
#
# 2. **Algebraic Graph Walk Formulation**:
#    Dyck paths correspond to walks on a 1D line graph whose vertices represent heights $h \\in \\{0, \\dots, n\\}$.
#    The adjacency matrix $A$ has non-zero entries $A_{h, h+1} = 1$ and $A_{h, h-1} = 1$.
#    The number of closed walks starting and ending at height 0 in $2n$ steps is exactly:
#    $$C_n = (A^{2n})_{0, 0}$$
#
# 3. **Binary Exponentiation via `ax.matrix.power`**:
#    Using `StandardSemiring`, `ax.matrix.power(A, 2n)` calculates exact walk counts in
#    $\\mathcal{O}(n^3 \\log n)$ algebraic steps.

# %%
import algebrax as ax


def build_dyck_lattice_graph(n: int) -> dict[int, dict[int, int]]:
    """Construct 1D height lattice graph adjacency matrix for height bounds [0, n]."""
    adjacency: dict[int, dict[int, int]] = {}
    for h in range(n + 1):
        adjacency[h] = {}
        if h + 1 <= n:
            adjacency[h][h + 1] = 1
        if h - 1 >= 0:
            adjacency[h][h - 1] = 1
    return adjacency


def compute_catalan_dyck_paths(n: int) -> int:
    """Compute the n-th Catalan number via matrix power walk counting (A^(2n))_{0,0}."""
    if n == 0:
        return 1
    adj = build_dyck_lattice_graph(n)
    sem = ax.semiring.StandardSemiring()
    walk_powers = ax.matrix.power(adj, 2 * n, semiring=sem)
    return int(walk_powers.get(0, {}).get(0, 0))


def compute_bounded_dyck_paths(n: int, max_height: int) -> int:
    """Calculate Dyck paths restricted within a bounded height strip 0 <= y <= max_height."""
    if n == 0:
        return 1
    effective_h = min(n, max_height)
    adj = build_dyck_lattice_graph(effective_h)
    sem = ax.semiring.StandardSemiring()
    walk_powers = ax.matrix.power(adj, 2 * n, semiring=sem)
    return int(walk_powers.get(0, {}).get(0, 0))


# %% [markdown]
# ## Step 1: Exact Catalan Number Walk Counting
#
# ## Step 2: Strip-Bounded Dyck Path Invariants


def run_demo() -> None:
    """Run Dyck path counting and Catalan verification."""
    print('==========================================================================')
    print('Step 1: Catalan Number Verification via Matrix Power (A^(2n))_{0,0}')
    print('==========================================================================')
    known_catalan = [1, 1, 2, 5, 14, 42, 132, 429, 1430]
    for n, expected_c in enumerate(known_catalan):
        computed_c = compute_catalan_dyck_paths(n)
        print(f'  n={n}: Computed C_{n} = {computed_c:<6} | Expected = {expected_c}')
        assert computed_c == expected_c

    print('\n==========================================================================')
    print('Step 2: Height-Constrained Dyck Paths (Membrane / Strip Model)')
    print('==========================================================================')
    n_steps = 4  # 2n = 8 steps total
    c_unbounded = compute_catalan_dyck_paths(n_steps)
    c_bounded = compute_bounded_dyck_paths(n_steps, max_height=2)
    print(f'Total Unbounded Dyck Paths (n={n_steps}): {c_unbounded}')
    print(f'Bounded Paths (Height <= 2, n={n_steps}): {c_bounded}')
    assert c_bounded < c_unbounded


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('\n==========================================================================')
    print('Recipe: Combinatorial Dyck Paths & Catalan Numbers Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
