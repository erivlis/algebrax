"""
Tensor algebra and Einstein summation over arbitrary algebraic semirings.

This module provides tensor operations for arbitrary-rank sparse tensors,
including generalized Einstein summation (`einsum`), outer products (`outer_product`),
tensor contractions (`tensordot`), and nested dictionary conversion tools.

All tensor operations operate natively on `AlgebraicTrie` and tuple-indexed sparse mappings.
"""

from collections.abc import Mapping
from typing import Any, TypeVar

from algebrax.semiring import Semiring, StandardSemiring
from algebrax.trie import AlgebraicTrie

V = TypeVar('V')

__all__ = [
    'einsum',
    'flatten_tensor',
    'outer_product',
    'tensordot',
    'unflatten_tensor',
]


def _get_semiring_and_items(
        tensor: Any,
        default_semiring: Semiring[V] | None = None,
) -> tuple[Semiring[V], list[tuple[tuple, Any]]]:
    """Helper to extract semiring instance and item list from AlgebraicTrie or dict."""
    if isinstance(tensor, AlgebraicTrie):
        sr = tensor.semiring
        items = list(tensor.items())
    elif isinstance(tensor, Mapping):
        sr = default_semiring if default_semiring is not None else StandardSemiring[float]()
        items = list(tensor.items())
    else:
        raise TypeError(f'Expected AlgebraicTrie or Mapping, got {type(tensor)}')
    return sr, items


def einsum(
        subscripts: str,
        *tensors: Any,
        semiring: Semiring[V] | None = None,
) -> Any:
    """
    Perform generalized Einstein summation over arbitrary rank sparse tensors.

    Calculates contractions, outer products, and trace operations specified by `subscripts`
    using the provided `semiring` for elementwise multiplication and index summation.

    Example subscript formats:
        - Matrix Multiplication: "ij,jk->ik"
        - Tensor Contraction: "ijk,jkl->il"
        - Outer Product: "i,j->ij"
        - Trace: "ii->"
        - Vector Dot Product: "i,i->"

    Args:
        subscripts: Einstein summation index notation (e.g. "ijk,jkl->il").
        *tensors: Input tensors (`AlgebraicTrie` or tuple-indexed dicts).
        semiring: Semiring for arithmetic. Defaults to input AlgebraicTrie semiring or StandardSemiring.

    Returns:
        An `AlgebraicTrie` containing the result tensor.
    """
    if not tensors:
        raise ValueError('einsum requires at least one tensor argument.')

    # Determine semiring from first tensor if not explicitly passed
    if semiring is None:
        semiring = tensors[0].semiring if isinstance(tensors[0], AlgebraicTrie) else StandardSemiring()

    # Parse subscript notation
    if '->' in subscripts:
        in_str, out_str = subscripts.split('->')
    else:
        in_str = subscripts
        # Implicit output: indices that appear exactly once in lexicographical order
        all_chars = [c for c in in_str if c.isalpha()]
        char_counts = {c: all_chars.count(c) for c in set(all_chars)}
        out_str = ''.join(sorted([c for c, count in char_counts.items() if count == 1]))

    in_sub_list = [s.strip() for s in in_str.split(',')]
    if len(in_sub_list) != len(tensors):
        raise ValueError(
            f'Number of subscript terms ({len(in_sub_list)}) must match number of tensors ({len(tensors)}).'
        )

    # Extract items from tensors
    parsed_tensors = []
    for idx, t in enumerate(tensors):
        sub_pattern = in_sub_list[idx]
        _, items = _get_semiring_and_items(t, semiring)
        # Filter items matching subscript rank
        valid_items = []
        for key, val in items:
            if not isinstance(key, tuple):
                key = (key,)
            if len(key) == len(sub_pattern):
                valid_items.append((key, val))
        parsed_tensors.append((sub_pattern, valid_items))

    # Perform Einstein summation
    out_trie = AlgebraicTrie(semiring=type(semiring))
    zero = semiring.zero
    mul_op = semiring.mul
    add_op = semiring.add

    def _contract_recursive(
            tensor_idx: int,
            current_assignment: dict[str, Any],
            accumulated_val: Any,
    ) -> None:
        if tensor_idx == len(parsed_tensors):
            # Form output key tuple
            out_key = tuple(current_assignment[c] for c in out_str)
            current_val = out_trie.get(out_key, zero)
            new_val = add_op(current_val, accumulated_val)
            if new_val != zero:
                out_trie[out_key] = new_val
            return

        sub_pattern, items = parsed_tensors[tensor_idx]

        for key_tuple, val in items:
            # Check if key matches current assignment
            match = True
            temp_assignment = dict(current_assignment)

            for char, k_elem in zip(sub_pattern, key_tuple, strict=False):
                if char in temp_assignment:
                    if temp_assignment[char] != k_elem:
                        match = False
                        break
                else:
                    temp_assignment[char] = k_elem

            if match:
                next_val = val if tensor_idx == 0 else mul_op(accumulated_val, val)
                _contract_recursive(tensor_idx + 1, temp_assignment, next_val)

    _contract_recursive(0, {}, semiring.one)
    return out_trie


def outer_product(
        tensor_a: Any,
        tensor_b: Any,
        semiring: Semiring[V] | None = None,
) -> AlgebraicTrie[Any, V]:
    """
    Compute the outer tensor product A (x) B over a semiring.

    C_{i_1...i_m, j_1...j_n} = A_{i_1...i_m} (x) B_{j_1...j_n}

    Args:
        tensor_a: First input tensor.
        tensor_b: Second input tensor.
        semiring: Semiring for multiplication.

    Returns:
        An `AlgebraicTrie` representing the outer product tensor.
    """
    if semiring is None:
        semiring = tensor_a.semiring if isinstance(tensor_a, AlgebraicTrie) else StandardSemiring()

    _, items_a = _get_semiring_and_items(tensor_a, semiring)
    _, items_b = _get_semiring_and_items(tensor_b, semiring)

    out_trie = AlgebraicTrie(semiring=type(semiring))
    mul_op = semiring.mul

    for key_a, val_a in items_a:
        if not isinstance(key_a, tuple):
            key_a = (key_a,)
        for key_b, val_b in items_b:
            if not isinstance(key_b, tuple):
                key_b = (key_b,)
            combined_key = key_a + key_b
            combined_val = mul_op(val_a, val_b)
            if combined_val != semiring.zero:
                out_trie[combined_key] = combined_val

    return out_trie


def tensordot(
        tensor_a: Any,
        tensor_b: Any,
        axes: int | tuple[list[int], list[int]] = 1,
        semiring: Semiring[V] | None = None,
) -> AlgebraicTrie[Any, V]:
    """
    Compute tensor contraction over specified axes.

    Args:
        tensor_a: First tensor.
        tensor_b: Second tensor.
        axes: Either an integer N (contracts last N axes of A with first N axes of B),
              or a tuple `(axes_a, axes_b)` listing 0-indexed axes to contract.
        semiring: Semiring for contraction arithmetic.

    Returns:
        An `AlgebraicTrie` containing the contracted tensor.
    """
    sr_a, items_a = _get_semiring_and_items(tensor_a, semiring)
    if semiring is None:
        semiring = sr_a

    # Determine rank of tensors
    rank_a = max((len(k) if isinstance(k, tuple) else 1 for k, _ in items_a), default=0)
    _, items_b = _get_semiring_and_items(tensor_b, semiring)
    rank_b = max((len(k) if isinstance(k, tuple) else 1 for k, _ in items_b), default=0)

    if isinstance(axes, int):
        n_axes = axes
        axes_a = list(range(rank_a - n_axes, rank_a))
        axes_b = list(range(n_axes))
    else:
        axes_a, axes_b = axes

    # Build subscript string for einsum
    sub_a_chars = [chr(97 + i) for i in range(rank_a)]  # 'a', 'b', 'c'...
    sub_b_chars = [chr(97 + rank_a + i) for i in range(rank_b)]

    # Align contracted characters
    for idx_a, idx_b in zip(axes_a, axes_b, strict=False):
        sub_b_chars[idx_b] = sub_a_chars[idx_a]

    # Form output chars
    free_a = [sub_a_chars[i] for i in range(rank_a) if i not in axes_a]
    free_b = [sub_b_chars[i] for i in range(rank_b) if i not in axes_b]

    subscript = f'{"".join(sub_a_chars)},{"".join(sub_b_chars)}->{"".join(free_a + free_b)}'

    return einsum(subscript, tensor_a, tensor_b, semiring=semiring)


def flatten_tensor(nested: Mapping[Any, Any], current_prefix: tuple = ()) -> dict[tuple, Any]:
    """
    Recursively flatten a nested dictionary into a tuple-indexed tensor mapping.

    Args:
        nested: A recursively nested dictionary.
        current_prefix: Internal prefix tuple for recursion.

    Returns:
        A flat dictionary mapping index tuples `(i_1, i_2, ...)` to leaf values.
    """
    flat = {}
    for key, val in nested.items():
        new_prefix = (*current_prefix, key)
        if isinstance(val, Mapping) and not isinstance(val, AlgebraicTrie):
            flat.update(flatten_tensor(val, new_prefix))
        else:
            flat[new_prefix] = val
    return flat


def unflatten_tensor(flat: Mapping[tuple, Any]) -> dict[Any, Any]:
    """
    Unflatten a tuple-indexed tensor mapping back into a recursively nested dictionary.

    Args:
        flat: A dictionary mapping index tuples `(i_1, i_2, ...)` to leaf values.

    Returns:
        A recursively nested dictionary.
    """
    nested: dict[Any, Any] = {}
    for idx_tuple, val in flat.items():
        if not isinstance(idx_tuple, tuple):
            idx_tuple = (idx_tuple,)
        curr = nested
        for key in idx_tuple[:-1]:
            curr = curr.setdefault(key, {})
        curr[idx_tuple[-1]] = val
    return nested
