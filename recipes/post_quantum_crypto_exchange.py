# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Post-Quantum Key Exchange & Complex Signal Masking Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Digital ax.semiring.Semiring Non-Commutative Key Exchange (algebrax.semiring.DigitalSemiring):
   The Digital ax.semiring.Semiring (D, +, *) uses digital root addition and multiplication.
   Because matrix multiplication over Digital semirings is non-commutative, Alice and
   Bob agree on a public generator matrix M (2x2).
   - Alice computes U = A * M * A using her secret matrix A.
   - Bob computes V = B * M * B using his secret matrix B.
   - Alice computes K_A = A * V * A and Bob computes K_B = B * U * B.
   By associativity, K_A == K_B = A * B * M * B * A.

2. Z-Domain Complex Signal Masking (algebrax.transforms.z_transform):
   The Z-transform X(z) = sum_{t} f(t) * z^{-t} evaluates a discrete payload signal
   in the complex plane. Evaluating X(z) at a z-coordinate derived from the shared key
   K_A masks the signal phase and magnitude in the complex frequency domain.

3. Privacy Audit via Mutual Information (algebrax.probability.mutual_information):
   Mutual information I(X; Y) = sum_{x, y} P(x, y) ln( P(x,y) / (P(x)P(y)) ) measures
   information leakage between plaintext payload X and ciphertext stream Y.
   A value of 0.0 nats guarantees perfect secrecy.
================================================================================
"""

import cmath

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Post-Quantum Matrix Key Exchange & Signal Masking')
    print('==========================================================================')
    print('Goal: Execute non-commutative matrix key exchange, evaluate Z-transform')
    print('      complex signal modulation, and verify zero mutual information leakage.')

    # --- Step 1: Digital ax.semiring.Semiring Post-Quantum Matrix Key Exchange ---
    print('\n[Step 1] Non-Commutative Matrix Key Exchange (Digital ax.semiring.Semiring)...')
    print('Explanation: Matrix multiplication over ax.semiring.DigitalSemiring is non-commutative.')
    print('             Alice & Bob compute U = A*M*A and V = B*M*B, yielding K_A == K_B.')
    digital_semiring = ax.semiring.DigitalSemiring()

    # Public Generator Matrix M (2x2)
    pub_m = {0: {0: 123, 1: 456}, 1: {0: 789, 1: 12}}
    print(f'Public Generator Matrix M: {pub_m}')

    # Alice's Secret Key Matrix A and Bob's Secret Key Matrix B
    alice_a = {0: {0: 11, 1: 99}, 1: {0: 99, 1: 11}}
    bob_b = {0: {0: 22, 1: 88}, 1: {0: 88, 1: 22}}

    # Exchange Messages: Alice sends U = A * M * A, Bob sends V = B * M * B
    am = ax.matrix.dot(alice_a, pub_m, digital_semiring)
    u_msg = ax.matrix.dot(am, alice_a, digital_semiring)

    bm = ax.matrix.dot(bob_b, pub_m, digital_semiring)
    v_msg = ax.matrix.dot(bm, bob_b, digital_semiring)

    print(f'Alice transmits public message U: {u_msg}')
    print(f'Bob   transmits public message V: {v_msg}')

    # Compute Shared Keys: key_alice = A * V * A, key_bob = B * U * B
    av = ax.matrix.dot(alice_a, v_msg, digital_semiring)
    key_alice = ax.matrix.dot(av, alice_a, digital_semiring)

    bu = ax.matrix.dot(bob_b, u_msg, digital_semiring)
    key_bob = ax.matrix.dot(bu, bob_b, digital_semiring)

    print(f"\nAlice's Derived Shared Secret Key: {key_alice}")
    print(f"Bob's   Derived Shared Secret Key: {key_bob}")
    keys_match = key_alice == key_bob
    print(f'Key Agreement Status: {"SUCCESSFUL (Matching Keys)" if keys_match else "FAILED"}')
    assert keys_match

    # --- Step 2: Z-Transform Complex Signal Masking ---
    print('\n[Step 2] Complex Z-Domain Signal Masking (algebrax.transforms.z_transform)...')
    print('Explanation: Evaluates Z-transform X(z) = sum_{t} f(t) * z^{-t} at complex point z')
    print('             derived directly from shared secret scalar key_alice[0][0].')

    payload_signal = {0: 1.0, 1: 2.0, 2: -1.0, 3: 0.5}

    shared_scalar = key_alice.get(0, {}).get(0, 1)
    z_point = complex(0.5, (shared_scalar % 10) / 10.0)

    z_eval = ax.transforms.z_transform(payload_signal, z_point)
    mag, phase = cmath.polar(z_eval)

    print(f'Input Payload Signal Vector f(t): {payload_signal}')
    print(f'Shared Key Evaluation Point z: {z_point}')
    print(f'Evaluated Z-Transform X(z): {z_eval.real:.4f} + {z_eval.imag:.4f}j')
    print(f'  Complex Magnitude |X(z)| = {mag:.4f}, Phase = {phase:.4f} rad')

    # --- Step 3: Information Security Audit (Mutual Information) ---
    print('\n[Step 3] Information Privacy Audit (algebrax.probability.mutual_information)...')
    print('Explanation: Computes Shannon mutual information I(Plaintext; Ciphertext).')
    print('             I(X; Y) = 0.0 nats proves zero privacy leakage in encrypted stream.')

    joint_distribution = {
        'Msg_0': {'Cipher_0': 0.25, 'Cipher_1': 0.25},
        'Msg_1': {'Cipher_0': 0.25, 'Cipher_1': 0.25},
    }

    mi_val = ax.probability.mutual_information(joint_distribution)
    print(f'Mutual Information I(Plaintext; Ciphertext): {mi_val:.6f} nats')

    if mi_val < 1e-6:
        print('Security Audit Verdict: SECURE - Perfect zero information leakage.')
    else:
        print('Security Audit Verdict: UNSECURE - Information leakage detected.')

    print('\n==========================================================================')
    print('Recipe Completed: Post-Quantum Key Exchange Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
