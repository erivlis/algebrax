# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Algebraic Knot Theory & Topological Invariants Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Skein Module & Connected Sum Invariants (algebrax.semiring.KnotSemiring):
   KnotSemiring R[Knots] models Skein modules over the knot connected sum (#) monoid.
   Values are formal linear combinations sum_k a_k * K_k where multiplication is the
   connected sum (#) of knot topologies (e.g. Trefoil '3_1' (#) Figure-8 '4_1' = '3_1#4_1').

2. Braid Group Permutations & Parity Signatures (algebrax.group.compose & signature):
   The Artin Braid group B_n projects onto the symmetric permutation group S_n.
   `compose` evaluates sequential strand crossings, while `signature` computes
   crossing parity (-1)^n to determine topological orientation.

3. Polynomial Polynomial Invariants (algebrax.semiring.MonoidAlgebraSemiring):
   PolynomialSemiring / MonoidAlgebraSemiring computes Jones and Alexander polynomial
   multiplications under knot tensor operations.
================================================================================
"""

from algebrax.group import compose, signature
from algebrax.semiring import KnotSemiring, MonoidAlgebraSemiring, StandardSemiring


def main() -> None:
    print('==========================================================================')
    print('Use Case: Algebraic Knot Theory & Topological Invariants')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to evaluate Skein module')
    print('      connected sums, Jones polynomial convolutions, and Braid group signatures.')

    # --- Step 1: Skein Module Connected Sums (KnotSemiring) ---
    print('\n[Step 1] Skein Module Formal Sums & Connected Sums (KnotSemiring)...')
    print('Explanation: KnotSemiring R[Knots] multiplies knot topologies via connected sum (#).')

    knot_algebra = KnotSemiring(StandardSemiring[float]())

    # Formal knot state A: 2 * Trefoil ('3_1') + 3 * Unknot ('U')
    knot_a = {'3_1': 2.0, 'U': 3.0}

    # Formal knot state B: 1 * Figure-Eight ('4_1') + 4 * Unknot ('U')
    knot_b = {'4_1': 1.0, 'U': 4.0}

    # Connected Sum Multiplication: A (#) B
    composite_knot = knot_algebra.mul(knot_a, knot_b)

    print('\nKnot State A: ', knot_a)
    print('Knot State B: ', knot_b)
    print('\nConnected Sum Topological Product A (#) B:')
    for knot_id, coeff in sorted(composite_knot.items()):
        print(f"  Knot Topology '{knot_id}': Formal Coefficient = {coeff:.2f}")

    # --- Step 2: Braid Group Crossing Permutations & Parity Signatures ---
    print('\n[Step 2] Braid Group Strand Crossings (compose & signature)...')
    print('Explanation: B_n braid crossings sigma_i map to permutation mappings in S_n.')

    # Braid Generators sigma_1 and sigma_2 for 4-strand braid
    sigma_1 = {0: 1, 1: 0, 2: 2, 3: 3}  # Swap strands 0 and 1
    sigma_2 = {0: 0, 1: 2, 2: 1, 3: 3}  # Swap strands 1 and 2

    # Braid Word: w = sigma_1 * sigma_2 * sigma_1
    w_12 = compose(sigma_1, sigma_2)
    braid_word = compose(w_12, sigma_1)

    sig_s1 = signature(sigma_1)
    sig_word = signature(braid_word)

    print('\nBraid Generator sigma_1 Strand Mapping: ', sigma_1)
    print('Braid Generator sigma_2 Strand Mapping: ', sigma_2)
    print(f'Composed Braid Word w = sigma_1*sigma_2*sigma_1: {braid_word}')

    print(f'\nGenerator sigma_1 Parity Signature: {sig_s1:+d} (Odd Crossing)')
    print(f'Composed Braid Word Parity Signature:  {sig_word:+d} (Odd Composite Crossing)')

    # --- Step 3: Laurent Jones Polynomial Invariant Multiplication ---
    print('\n[Step 3] Laurent Jones Polynomial Ring Arithmetic (MonoidAlgebraSemiring)...')
    print('Explanation: Computes Jones polynomial multiplication V(K1 # K2) = V(K1) * V(K2).')

    # Laurent polynomial ring over variable exponent key t^k
    poly_algebra = MonoidAlgebraSemiring(StandardSemiring[float](), zero_key=0)

    # Trefoil Knot '3_1' Jones Polynomial V(3_1) = -t^{-4} + t^{-3} + t^{-1}
    v_trefoil = {-4: -1.0, -3: 1.0, -1: 1.0}

    # Figure-Eight Knot '4_1' Jones Polynomial V(4_1) = t^{-2} - t^{-1} + 1 - t^1 + t^2
    v_figure8 = {-2: 1.0, -1: -1.0, 0: 1.0, 1: -1.0, 2: 1.0}

    # Composite Knot Jones Polynomial V(3_1 # 4_1) = V(3_1) * V(4_1)
    v_composite = poly_algebra.mul(v_trefoil, v_figure8)

    print('\nTrefoil V(3_1) Jones Polynomial Coefficients:  ', v_trefoil)
    print('Figure-8 V(4_1) Jones Polynomial Coefficients: ', v_figure8)
    print('\nComposite Knot V(3_1 # 4_1) Polynomial Product:')
    for exp in sorted(v_composite.keys()):
        print(f'  Term t^{exp:+d}: Coefficient = {v_composite[exp]:+5.1f}')

    print('\n==========================================================================')
    print('Use Case Completed: Algebraic Knot Theory & Invariants Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
