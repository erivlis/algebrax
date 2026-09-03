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
# # Algebraic Knot Theory & Topological Invariants
#
# ## Theory & Mathematical Foundation
#
# 1. **Skein Module & Connected Sum Invariants (`algebrax.semiring.KnotSemiring`)**:
#    `KnotSemiring` $\\mathbb{R}[\\text{Knots}]$ models Skein modules over the knot connected sum $(\\#)$ monoid.
#    Values are formal linear combinations $\\sum_k a_k K_k$ where multiplication is the
#    connected sum $(\\#)$ of knot topologies (e.g. Trefoil $3_1 \\#$ Figure-8 $4_1 = 3_1\\#4_1$).
#
# 2. **Braid Group Permutations & Parity Signatures (`algebrax.group.compose` & `ax.group.signature`)**:
#    The Artin Braid group $B_n$ projects onto the symmetric permutation group $S_n$.
#    `group.compose` evaluates sequential strand crossings, while `group.signature` computes
#    crossing parity $(-1)^n$ to determine topological orientation.
#
# 3. **Polynomial Invariants (`algebrax.semiring.MonoidAlgebraSemiring`)**:
#    `MonoidAlgebraSemiring` computes Jones and Alexander polynomial multiplications under knot tensor operations.

# %%
import algebrax as ax


def compute_connected_sum(
    knot_a: dict[str, float],
    knot_b: dict[str, float],
) -> dict[str, float]:
    """Compute Skein module topological connected sum A (#) B."""
    knot_algebra = ax.semiring.KnotSemiring(ax.semiring.StandardSemiring[float]())
    return knot_algebra.mul(knot_a, knot_b)


def evaluate_braid_word(
    crossings: list[int],
    n_strands: int | None = None,
) -> tuple[dict[int, int], int]:
    """Evaluate Artin braid word into strand permutation mapping and crossing parity signature."""
    if n_strands is None:
        n_strands = max(max(crossings, default=1) + 1, 2)
    perm: dict[int, int] = {i: i for i in range(n_strands)}
    for c in crossings:
        if 1 <= c < n_strands:
            swap_gen = {i: i for i in range(n_strands)}
            swap_gen[c - 1], swap_gen[c] = c, c - 1
            perm = ax.group.compose(perm, swap_gen)
    sig = ax.group.signature(perm)
    return perm, sig


def multiply_jones_polynomials(
    p1: dict[int, float],
    p2: dict[int, float],
) -> dict[int, float]:
    """Multiply Laurent Jones polynomials V(K1 # K2) = V(K1) * V(K2)."""
    poly_algebra = ax.semiring.MonoidAlgebraSemiring(ax.semiring.StandardSemiring[float](), zero_key=0)
    return poly_algebra.mul(p1, p2)

# %% [markdown]
# ## Step 1: Skein Module Formal Sums & Connected Sums (`KnotSemiring`)
#
# ## Step 2: Braid Group Crossing Permutations & Parity Signatures
#
# ## Step 3: Laurent Jones Polynomial Ring Arithmetic (`MonoidAlgebraSemiring`)


def run_demo() -> None:
    """Run knot connected sums, braid signatures, and Jones polynomials."""
    knot_a = {'3_1': 2.0, 'U': 3.0}
    knot_b = {'4_1': 1.0, 'U': 4.0}
    composite_knot = compute_connected_sum(knot_a, knot_b)
    print('Knot State A: ', knot_a)
    print('Knot State B: ', knot_b)
    print('\nConnected Sum Topological Product A (#) B:')
    for knot_id, coeff in sorted(composite_knot.items()):
        print(f"  Knot Topology '{knot_id}': Formal Coefficient = {coeff:.2f}")

    crossings_seq = [1, 2, 1]
    braid_word, sig_word = evaluate_braid_word(crossings_seq, n_strands=4)
    print(f'Composed Braid Word w from crossings {crossings_seq}: {braid_word}')
    print(f'Composed Braid Word Parity Signature: {sig_word:+d} ({"Even" if sig_word == 1 else "Odd"})')

    v_trefoil = {-4: -1.0, -3: 1.0, -1: 1.0}
    v_figure8 = {-2: 1.0, -1: -1.0, 0: 1.0, 1: -1.0, 2: 1.0}
    v_composite = multiply_jones_polynomials(v_trefoil, v_figure8)
    print('\nTrefoil V(3_1) Jones Polynomial Coefficients:  ', v_trefoil)
    print('Figure-8 V(4_1) Jones Polynomial Coefficients: ', v_figure8)
    print('\nComposite Knot V(3_1 # 4_1) Polynomial Product:')
    for exp in sorted(v_composite.keys()):
        print(f'  Term t^{exp:+d}: Coefficient = {v_composite[exp]:+5.1f}')


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Algebraic Knot Theory & Invariants Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
