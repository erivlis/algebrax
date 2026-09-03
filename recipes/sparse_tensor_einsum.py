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
# # Sparse Tensor Einstein Summation & Multimodal Data Fusion
#
# ## Theory & Mathematical Foundation
#
# 1. **Generalized Einstein Summation over Semirings (`algebrax.tensor.einsum`)**:
#    `einsum` evaluates arbitrary-rank tensor contractions over any algebraic semiring:
#    $$C_{i, l} = \bigoplus_{j, k} A_{i, j, k} \otimes B_{j, k, l}$$
#    computes multidimensional tensor contractions for multimodal data fusion.
#
# 2. **Polymorphic Tropical Tensor Products (`algebrax.semiring.TropicalSemiring`)**:
#    Executing `einsum` over `TropicalSemiring` computes min-plus tensor shortest-path optimizations.
#
# 3. **Tensor Outer Products & Nesting Converters (`outer_product`, `flatten_tensor`, `unflatten_tensor`)**:
#    `outer_product` computes $C = A \otimes B$, while `flatten_tensor` and `unflatten_tensor`
#    convert between hierarchical nested dictionaries and tuple-indexed `AlgebraicTrie` objects.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Rank-3 Multimodal Tensor Contraction (`tensor.einsum`)
# $C(i, l) = \sum_{j, k} A(i, j, k) \times B(j, k, l)$ contracts rank-3 tensors.

# %%
tensor_a = ax.trie.AlgebraicTrie(semiring=ax.semiring.StandardSemiring)
tensor_a[('User_1', 'Movie_A', 'Home')] = 4.5
tensor_a[('User_1', 'Movie_B', 'Work')] = 2.0
tensor_a[('User_2', 'Movie_A', 'Home')] = 5.0
tensor_a[('User_2', 'Movie_C', 'Work')] = 3.5

tensor_b = ax.trie.AlgebraicTrie(semiring=ax.semiring.StandardSemiring)
tensor_b[('Movie_A', 'Home', 'Sci-Fi')] = 0.9
tensor_b[('Movie_B', 'Work', 'Comedy')] = 0.8
tensor_b[('Movie_C', 'Work', 'Drama')] = 0.95

fused_tensor = ax.tensor.einsum('ijk,jkl->il', tensor_a, tensor_b)

print("\nContracted User-Category Tensor C(i, l) = einsum('ijk,jkl->il', A, B):")
for key, weight in sorted(fused_tensor.items()):
    print(f'  User-Category Pair {key}: Contracted Score = {weight:.2f}')

# %% [markdown]
# ## Step 2: Tropical Min-Plus Tensor Contraction (`TropicalSemiring`)
# `einsum` over `TropicalSemiring` computes min-plus shortest latency.

# %%
trop_a = ax.trie.AlgebraicTrie(semiring=ax.semiring.TropicalSemiring)
trop_a[('Node_1', 'Node_2', 'Route_A')] = 10.0
trop_a[('Node_1', 'Node_3', 'Route_B')] = 25.0

trop_b = ax.trie.AlgebraicTrie(semiring=ax.semiring.TropicalSemiring)
trop_b[('Node_2', 'Route_A', 'Dest_X')] = 15.0
trop_b[('Node_3', 'Route_B', 'Dest_X')] = 5.0

trop_fused = ax.tensor.einsum('ijk,jkl->il', trop_a, trop_b, semiring=ax.semiring.TropicalSemiring())

print('\nTropical Min-Plus Latency Tensor:')
for key, latency in sorted(trop_fused.items()):
    print(f'  Route Pair {key}: Minimum Path Latency = {latency:.1f} ms')

# %% [markdown]
# ## Step 3: Tensor Outer Product & Axis Contraction (`outer_product` & `tensordot`)

# %%
vec_a = {(0,): 2.0, (1,): 3.0}
vec_b = {(0,): 4.0, (1,): 5.0}

outer_c = ax.tensor.outer_product(vec_a, vec_b)
contract_c = ax.tensor.einsum('i,i->', vec_a, vec_b)

print('\nOuter Tensor Product (Rank 1 (x) Rank 1 = Rank 2):')
for key, val in sorted(outer_c.items()):
    print(f'  Tensor Index {key}: Value = {val:.1f}')

print(f'\nTensor Einstein Contraction Vector Dot Product: {contract_c[()]:.1f}')

# %% [markdown]
# ## Step 4: Nested Dictionary Tensor Converters (`flatten_tensor` & `unflatten_tensor`)

# %%
nested_dict = {
    'User_1': {'Movie_A': 4.5, 'Movie_B': 2.0},
    'User_2': {'Movie_C': 3.5},
}

flat_trie = ax.tensor.flatten_tensor(nested_dict)
reconstructed_nested = ax.tensor.unflatten_tensor(flat_trie)

print('\nOriginal Nested Dictionary: ', nested_dict)
print('Flattened Tuple Tensor Trie: ', flat_trie)
print('Reconstructed Nested Dict:  ', reconstructed_nested)


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Sparse Tensor Einstein Summation Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
