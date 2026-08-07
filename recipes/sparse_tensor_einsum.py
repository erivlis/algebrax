# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Sparse Tensor Einstein Summation & Multimodal Data Fusion Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Generalized Einstein Summation over Semirings (algebrax.tensor.einsum):
   `ax.tensor.einsum` evaluates arbitrary-rank tensor contractions over any algebraic semiring.
   C_{i, l} = \\bigoplus_{j, k} A_{i, j, k} \\otimes B_{j, k, l} computes multidimensional
   tensor contractions for multimodal data fusion.

2. Polymorphic Tropical Tensor Products (algebrax.semiring.TropicalSemiring):
   Executing `ax.tensor.einsum` over `ax.semiring.TropicalSemiring` computes min-plus tensor shortest-path
   optimizations for multi-hop network routing tensors.

3. Tensor Outer Products & Nesting Converters (outer_product, flatten_tensor, unflatten_tensor):
   `outer_product` computes C = A (x) B, while `flatten_tensor` and `unflatten_tensor`
   convert between hierarchical nested dictionaries and tuple-indexed AlgebraicTries.
================================================================================
"""

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Sparse Tensor Einstein Summation & Multimodal Data Fusion')
    print('==========================================================================')
    print('Goal: Combine 5 distinct algebraic tools from algebrax to evaluate arbitrary')
    print('      rank tensor ax.tensor.einsum contractions, tropical min-plus tensor products,')
    print('      tensor outer products, and nested dictionary conversions.')

    # --- Step 1: Rank-3 Tensor Contraction via ax.tensor.einsum ---
    print('\n[Step 1] Rank-3 Multimodal Tensor Contraction via ax.tensor.einsum...')
    print('Explanation: C(i, l) = sum_{j, k} A(i, j, k) * B(j, k, l) contracts rank-3 tensors.')

    # Tensor A: User (i) x Item (j) x Context (k)
    tensor_a = ax.trie.AlgebraicTrie(semiring=ax.semiring.StandardSemiring)
    tensor_a[('User_1', 'Movie_A', 'Home')] = 4.5
    tensor_a[('User_1', 'Movie_B', 'Work')] = 2.0
    tensor_a[('User_2', 'Movie_A', 'Home')] = 5.0
    tensor_a[('User_2', 'Movie_C', 'Work')] = 3.5

    # Tensor B: Item (j) x Context (k) x Category (l)
    tensor_b = ax.trie.AlgebraicTrie(semiring=ax.semiring.StandardSemiring)
    tensor_b[('Movie_A', 'Home', 'Sci-Fi')] = 0.9
    tensor_b[('Movie_B', 'Work', 'Comedy')] = 0.8
    tensor_b[('Movie_C', 'Work', 'Drama')] = 0.95

    # Contraction over shared (j, k) axes via ax.tensor.einsum("ijk,jkl->il")
    fused_tensor = ax.tensor.einsum('ijk,jkl->il', tensor_a, tensor_b)

    print("\nContracted User-Category Tensor C(i, l) = ax.tensor.einsum('ijk,jkl->il', A, B):")
    for key, weight in sorted(fused_tensor.items()):
        print(f'  User-Category Pair {key}: Contracted Score = {weight:.2f}')

    # --- Step 2: Tropical Min-Plus Tensor Contraction ---
    print('\n[Step 2] Tropical Min-Plus Tensor Contraction (ax.semiring.TropicalSemiring)...')
    print('Explanation: ax.tensor.einsum over ax.semiring.TropicalSemiring computes min-plus shortest latency.')

    trop_a = ax.trie.AlgebraicTrie(semiring=ax.semiring.TropicalSemiring)
    trop_a[('Node_1', 'Node_2', 'Route_A')] = 10.0
    trop_a[('Node_1', 'Node_3', 'Route_B')] = 25.0

    trop_b = ax.trie.AlgebraicTrie(semiring=ax.semiring.TropicalSemiring)
    trop_b[('Node_2', 'Route_A', 'Dest_X')] = 15.0
    trop_b[('Node_3', 'Route_B', 'Dest_X')] = 5.0

    # Min-Plus Contraction: C(i, l) = min_{j, k} (A(i, j, k) + B(j, k, l))
    trop_fused = ax.tensor.einsum('ijk,jkl->il', trop_a, trop_b, semiring=ax.semiring.TropicalSemiring())

    print('\nTropical Min-Plus Latency Tensor:')
    for key, latency in sorted(trop_fused.items()):
        print(f'  Route Pair {key}: Minimum Path Latency = {latency:.1f} ms')

    # --- Step 3: Tensor Outer Product & Axis Tensordot ---
    print('\n[Step 3] Tensor Outer Product & Axis Contraction (outer_product & tensordot)...')
    print('Explanation: Outer product C = A (x) B expands rank; tensordot contracts specified axes.')

    vec_a = {(0,): 2.0, (1,): 3.0}
    vec_b = {(0,): 4.0, (1,): 5.0}

    outer_c = ax.tensor.outer_product(vec_a, vec_b)
    contract_c = ax.tensor.tensordot(vec_a, vec_b, axes=1)

    print('\nOuter Tensor Product (Rank 1 (x) Rank 1 = Rank 2):')
    for key, val in sorted(outer_c.items()):
        print(f'  Tensor Index {key}: Value = {val:.1f}')

    print(f'\nTensordot Axis Contraction Vector Dot Product: {contract_c[()]:.1f}')

    # --- Step 4: Nested Dictionary Tensor Converters ---
    print('\n[Step 4] Nested Dictionary Tensor Converters (flatten_tensor & unflatten_tensor)...')
    print('Explanation: Bidirectional conversions between nested dicts and tuple-indexed Tries.')

    nested_dict = {
        'User_1': {'Movie_A': 4.5, 'Movie_B': 2.0},
        'User_2': {'Movie_C': 3.5},
    }

    flat_trie = ax.tensor.flatten_tensor(nested_dict)
    reconstructed_nested = ax.tensor.unflatten_tensor(flat_trie)

    print('\nOriginal Nested Dictionary: ', nested_dict)
    print('Flattened Tuple Tensor Trie: ', flat_trie)
    print('Reconstructed Nested Dict:  ', reconstructed_nested)

    print('\n==========================================================================')
    print('Use Case Completed: Sparse Tensor Einstein Summation Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
