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
#    `KnotSemiring` $\mathbb{R}[\text{Knots}]$ models Skein modules over the knot connected sum $(\#)$ monoid.
#    Values are formal linear combinations $\sum_k a_k K_k$ where multiplication is the
#    connected sum $(\#)$ of knot topologies (e.g. Trefoil $3_1 \#$ Figure-8 $4_1 = 3_1\#4_1$).
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

# %% [markdown]
# ## Step 1: Skein Module Formal Sums & Connected Sums (`KnotSemiring`)
# `KnotSemiring` $\mathbb{R}[\text{Knots}]$ multiplies knot topologies via connected sum $(\#)$.

# %%
knot_algebra = ax.semiring.KnotSemiring(ax.semiring.StandardSemiring[float]())

knot_a = {"3_1": 2.0, "U": 3.0}
knot_b = {"4_1": 1.0, "U": 4.0}

composite_knot = knot_algebra.mul(knot_a, knot_b)

print("Knot State A: ", knot_a)
print("Knot State B: ", knot_b)
print("\nConnected Sum Topological Product A (#) B:")
for knot_id, coeff in sorted(composite_knot.items()):
    print(f"  Knot Topology '{knot_id}': Formal Coefficient = {coeff:.2f}")

# %% [markdown]
# ## Step 2: Braid Group Crossing Permutations & Parity Signatures
# Braid generators $\sigma_i \in B_n$ map to permutation mappings in $S_n$.

# %%
sigma_1 = {0: 1, 1: 0, 2: 2, 3: 3}
sigma_2 = {0: 0, 1: 2, 2: 1, 3: 3}

w_12 = ax.group.compose(sigma_1, sigma_2)
braid_word = ax.group.compose(w_12, sigma_1)

sig_s1 = ax.group.signature(sigma_1)
sig_word = ax.group.signature(braid_word)

print("\nBraid Generator sigma_1 Strand Mapping: ", sigma_1)
print("Braid Generator sigma_2 Strand Mapping: ", sigma_2)
print(f"Composed Braid Word w = sigma_1*sigma_2*sigma_1: {braid_word}")

print(f"\nGenerator sigma_1 Parity Signature: {sig_s1:+d} (Odd Crossing)")
print(f"Composed Braid Word Parity Signature:  {sig_word:+d} (Odd Composite Crossing)")

# %% [markdown]
# ## Step 3: Laurent Jones Polynomial Ring Arithmetic (`MonoidAlgebraSemiring`)
# Computes Jones polynomial multiplication $V(K_1 \# K_2) = V(K_1) \times V(K_2)$.

# %%
poly_algebra = ax.semiring.MonoidAlgebraSemiring(ax.semiring.StandardSemiring[float](), zero_key=0)

# Trefoil Knot '3_1' Jones Polynomial V(3_1) = -t^{-4} + t^{-3} + t^{-1}
v_trefoil = {-4: -1.0, -3: 1.0, -1: 1.0}

# Figure-Eight Knot '4_1' Jones Polynomial V(4_1) = t^{-2} - t^{-1} + 1 - t^1 + t^2
v_figure8 = {-2: 1.0, -1: -1.0, 0: 1.0, 1: -1.0, 2: 1.0}

v_composite = poly_algebra.mul(v_trefoil, v_figure8)

print("\nTrefoil V(3_1) Jones Polynomial Coefficients:  ", v_trefoil)
print("Figure-8 V(4_1) Jones Polynomial Coefficients: ", v_figure8)
print("\nComposite Knot V(3_1 # 4_1) Polynomial Product:")
for exp in sorted(v_composite.keys()):
    print(f"  Term t^{exp:+d}: Coefficient = {v_composite[exp]:+5.1f}")


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Algebraic Knot Theory & Invariants Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
