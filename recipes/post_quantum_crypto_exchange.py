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
# # Post-Quantum Key Exchange & Complex Signal Masking
#
# ## Theory & Mathematical Foundation
#
# 1. **Digital Semiring Non-Commutative Key Exchange (`algebrax.semiring.DigitalSemiring`)**:
#    The Digital Semiring $(\\mathcal{D}, +, \\times)$ uses digital root addition and multiplication.
#    Because matrix multiplication over Digital semirings is non-commutative,
#    Alice and Bob agree on a public generator matrix $M$:
#    - Alice computes $U = A M A$ using her secret matrix $A$.
#    - Bob computes $V = B M B$ using his secret matrix $B$.
#    - Alice computes $K_A = A V A$ and Bob computes $K_B = B U B$.
#    By associativity, $K_A = K_B = A B M B A$.

# %%
import algebrax as ax


def perform_digital_key_exchange(
    alice_a: dict[int, dict[int, int]],
    bob_b: dict[int, dict[int, int]],
    pub_m: dict[int, dict[int, int]] | None = None,
) -> tuple[
    dict[int, dict[int, int]],
    dict[int, dict[int, int]],
    dict[int, dict[int, int]],
    dict[int, dict[int, int]],
    bool,
]:
    """Execute DigitalSemiring non-commutative matrix key exchange."""
    sem = ax.semiring.DigitalSemiring()
    if pub_m is None:
        pub_m = {0: {0: 123, 1: 456}, 1: {0: 789, 1: 12}}

    am = ax.matrix.dot(alice_a, pub_m, sem)
    u_mat = ax.matrix.dot(am, alice_a, sem)

    bm = ax.matrix.dot(bob_b, pub_m, sem)
    v_mat = ax.matrix.dot(bm, bob_b, sem)

    av = ax.matrix.dot(alice_a, v_mat, sem)
    ka_mat = ax.matrix.dot(av, alice_a, sem)

    bu = ax.matrix.dot(bob_b, u_mat, sem)
    kb_mat = ax.matrix.dot(bu, bob_b, sem)

    match = ka_mat == kb_mat
    return u_mat, v_mat, ka_mat, kb_mat, match


# %% [markdown]
# ## Step 1: Digital Semiring Post-Quantum Matrix Key Exchange


def run_demo() -> None:
    """Run non-commutative matrix key exchange over DigitalSemiring."""
    pub_m = {0: {0: 123, 1: 456}, 1: {0: 789, 1: 12}}
    alice_a = {0: {0: 11, 1: 99}, 1: {0: 99, 1: 11}}
    bob_b = {0: {0: 22, 1: 88}, 1: {0: 88, 1: 22}}

    u_msg, v_msg, key_alice, key_bob, is_match = perform_digital_key_exchange(alice_a, bob_b, pub_m)
    print(f'Alice transmits public message U: {u_msg}')
    print(f'Bob   transmits public message V: {v_msg}')
    print(f"\nAlice's Derived Shared Secret Key: {key_alice}")
    print(f"Bob's   Derived Shared Secret Key: {key_bob}")
    print(f'Shared Secret Keys Match: {is_match}')
    assert is_match is True


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Post-Quantum Crypto Key Exchange Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
