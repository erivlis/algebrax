"""
Tensor algebra and Einstein summation over arbitrary algebraic semirings.

This module provides tensor operations for arbitrary-rank sparse tensors,
including generalized Einstein summation (`einsum`), outer products (`outer_product`),
tensor contractions (`tensordot`), and nested dictionary conversion tools.

All tensor operations operate natively on `AlgebraicTrie` and tuple-indexed sparse mappings.
"""

from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from algebrax.converters import flat_to_nested, make_zero_predicate, nested_to_flat
from algebrax.semiring import Semiring, StandardSemiring
from algebrax.trie import AlgebraicTrie

V = TypeVar('V')

__all__ = [
    'dot',
    'einsum',
    'flatten_tensor',
    'outer_product',
    'permute_tensor',
    'unflatten_tensor',
    'unpermute_tensor',
]


def _semirings_equivalent(a: Any, b: Any) -> bool:
    """Check whether two semiring instances represent the same algebraic structure."""
    if a is b:
        return True
    if type(a) is not type(b):
        return False
    if a == b:
        return True
    da = getattr(a, '__dict__', None)
    db = getattr(b, '__dict__', None)
    if da is None or db is None or da.keys() != db.keys():
        return False
    for key in da:
        va, vb = da[key], db[key]
        if callable(va) and callable(vb) and not isinstance(va, type) and not isinstance(vb, type):
            continue
        if isinstance(va, Semiring) and isinstance(vb, Semiring):
            if not _semirings_equivalent(va, vb):
                return False
        elif va != vb:
            return False
    return True


def _resolve_semiring(
    semiring: Semiring[Any] | type[Semiring[Any]] | str | None,
    *tensors: Any,
) -> Semiring[Any]:
    """Normalize explicit semiring or inherit live semiring from input AlgebraicTrie(s)."""
    if semiring is not None:
        return Semiring.normalize(semiring)
    inferred: Semiring[Any] | None = None
    for t in tensors:
        if isinstance(t, AlgebraicTrie):
            if inferred is None:
                inferred = t.semiring
            elif not _semirings_equivalent(inferred, t.semiring):
                raise ValueError(
                    f'Conflicting semirings across AlgebraicTrie operands: '
                    f'{type(inferred).__name__} vs {type(t.semiring).__name__}. '
                    f'Pass semiring=... explicitly to override.'
                )
    return inferred if inferred is not None else StandardSemiring[float]()


def _get_semiring_and_items(
    tensor: Any,
    default_semiring: Semiring[V] | None = None,
) -> tuple[Semiring[V], list[tuple[tuple[Any, ...], Any]]]:
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


def _parse_einsum_subscripts(subscripts: str, n_tensors: int) -> tuple[list[str], str]:
    """Parse explicit or implicit Einstein subscript specification."""
    if '->' in subscripts:
        in_str, out_str = (part.strip() for part in subscripts.split('->', 1))
    else:
        in_str = subscripts.strip()
        all_chars = [c for c in in_str if c.isalpha()]
        char_counts = {c: all_chars.count(c) for c in set(all_chars)}
        out_str = ''.join(sorted(c for c, count in char_counts.items() if count == 1))

    in_sub_list = [s.strip() for s in in_str.split(',')]
    if len(in_sub_list) != n_tensors:
        raise ValueError(
            f'Number of subscript terms ({len(in_sub_list)}) must match number of tensors ({n_tensors}).'
        )
    all_in_chars = set().union(*in_sub_list)
    for c in out_str:
        if c not in all_in_chars:
            raise ValueError(f"Output subscript '{c}' does not appear in input subscripts.")
    return in_sub_list, out_str


def _extract_tensor_entries(
    tensor: Any,
    sub_pattern: str,
    sr: Semiring[Any],
    is_zero: Callable[[Any], bool],
) -> tuple[tuple[str, ...], list[tuple[tuple[Any, ...], Any]]]:
    """Filter tensor entries by rank and internal repeated-index constraints."""
    _, raw_items = _get_semiring_and_items(tensor, sr)
    unique_chars: list[str] = []
    first_pos: dict[str, int] = {}
    repeat_pairs: list[tuple[int, int]] = []
    for pos, ch in enumerate(sub_pattern):
        if ch in first_pos:
            repeat_pairs.append((first_pos[ch], pos))
        else:
            first_pos[ch] = pos
            unique_chars.append(ch)

    unique_positions = [first_pos[ch] for ch in unique_chars]
    pat_len = len(sub_pattern)
    valid_items: list[tuple[tuple[Any, ...], Any]] = []
    for key, val in raw_items:
        norm_key = key if isinstance(key, tuple) else (key,)
        if len(norm_key) != pat_len or is_zero(val):
            continue
        if repeat_pairs and any(norm_key[p1] != norm_key[p2] for p1, p2 in repeat_pairs):
            continue
        reduced_key = tuple(norm_key[p] for p in unique_positions) if repeat_pairs else norm_key
        valid_items.append((reduced_key, val))

    return tuple(unique_chars), valid_items


def _project_first_tensor(
    chars: tuple[str, ...],
    entries: list[tuple[tuple[Any, ...], Any]],
    keep_set: set[str],
    add_op: Callable[[Any, Any], Any],
    is_zero: Callable[[Any], bool],
) -> tuple[tuple[str, ...], dict[tuple[Any, ...], Any]]:
    """Aggregate the initial tensor onto indices needed by subsequent steps or output."""
    next_chars = tuple(c for c in chars if c in keep_set)
    keep_pos = [i for i, c in enumerate(chars) if c in keep_set]
    acc: dict[tuple[Any, ...], Any] = {}
    same_schema = len(keep_pos) == len(chars)
    for key, val in entries:
        out_k = key if same_schema else tuple(key[i] for i in keep_pos)
        if out_k in acc:
            combined = add_op(acc[out_k], val)
            if is_zero(combined):
                del acc[out_k]
            else:
                acc[out_k] = combined
        else:
            acc[out_k] = val
    return next_chars, acc


def _hash_join_step(
    acc_chars: tuple[str, ...],
    acc: dict[tuple[Any, ...], Any],
    t_chars: tuple[str, ...],
    t_entries: list[tuple[tuple[Any, ...], Any]],
    keep_set: set[str],
    add_op: Callable[[Any, Any], Any],
    mul_op: Callable[[Any, Any], Any],
    is_zero: Callable[[Any], bool],
) -> tuple[tuple[str, ...], dict[tuple[Any, ...], Any]]:
    """Perform a left-to-right hash join of accumulator with the next tensor."""
    acc_pos = {c: i for i, c in enumerate(acc_chars)}
    shared_chars = [c for c in t_chars if c in acc_pos]
    acc_shared_idx = [acc_pos[c] for c in shared_chars]
    t_pos = {c: i for i, c in enumerate(t_chars)}
    t_shared_idx = [t_pos[c] for c in shared_chars]

    # Build output schema preserving deterministic order: kept from acc, then newly introduced kept from t
    acc_keep_idx = [i for i, c in enumerate(acc_chars) if c in keep_set]
    t_new_keep_idx = [i for i, c in enumerate(t_chars) if c not in acc_pos and c in keep_set]
    next_chars = tuple(acc_chars[i] for i in acc_keep_idx) + tuple(t_chars[i] for i in t_new_keep_idx)

    # Hash-index incoming tensor by shared subscript tuple
    t_index: dict[tuple[Any, ...], list[tuple[tuple[Any, ...], Any]]] = {}
    for t_key, t_val in t_entries:
        join_key = tuple(t_key[i] for i in t_shared_idx)
        rem_key = tuple(t_key[i] for i in t_new_keep_idx)
        t_index.setdefault(join_key, []).append((rem_key, t_val))

    next_acc: dict[tuple[Any, ...], Any] = {}
    for acc_key, acc_val in acc.items():
        join_key = tuple(acc_key[i] for i in acc_shared_idx)
        matches = t_index.get(join_key)
        if not matches:
            continue
        acc_kept = tuple(acc_key[i] for i in acc_keep_idx)
        for rem_key, t_val in matches:
            prod = mul_op(acc_val, t_val)
            if is_zero(prod):
                continue
            out_k = acc_kept + rem_key
            if out_k in next_acc:
                combined = add_op(next_acc[out_k], prod)
                if is_zero(combined):
                    del next_acc[out_k]
                else:
                    next_acc[out_k] = combined
            else:
                next_acc[out_k] = prod

    return next_chars, next_acc


def einsum(
    subscripts: str,
    *tensors: Any,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> AlgebraicTrie[Any, V]:
    """
    Perform generalized Einstein summation over arbitrary rank sparse tensors.

    Calculates contractions, outer products, and trace operations specified by `subscripts`
    using the provided `semiring` for elementwise multiplication and index summation via
    left-to-right hash-join indexing.

    Example subscript formats:
        - Matrix Multiplication: "ij,jk->ik"
        - Tensor Contraction: "ijk,jkl->il"
        - Outer Product: "i,j->ij"
        - Trace: "ii->"
        - Vector Dot Product: "i,i->"

    Args:
        subscripts: Einstein summation index notation (e.g. "ijk,jkl->il").
        *tensors: Input tensors (`AlgebraicTrie` or tuple-indexed dicts).
        semiring: Semiring instance, class, or catalog name. Defaults to input `AlgebraicTrie`
            semiring or `StandardSemiring`.

    Returns:
        An `AlgebraicTrie` containing the result tensor with the live semiring preserved.
    """
    if not tensors:
        raise ValueError('einsum requires at least one tensor argument.')

    sr = _resolve_semiring(semiring, *tensors)
    in_sub_list, out_str = _parse_einsum_subscripts(subscripts, len(tensors))
    is_zero = make_zero_predicate(sr)

    parsed_tensors: list[tuple[tuple[str, ...], list[tuple[tuple[Any, ...], Any]]]] = []
    for idx, t in enumerate(tensors):
        u_chars, valid_items = _extract_tensor_entries(t, in_sub_list[idx], sr, is_zero)
        parsed_tensors.append((u_chars, valid_items))

    out_trie: AlgebraicTrie[Any, V] = AlgebraicTrie(semiring=sr)
    if any(not items for _, items in parsed_tensors):
        return out_trie

    out_set = set(out_str)
    add_op = sr.add
    mul_op = sr.mul

    # Precompute indices still needed after each contraction step
    n_tensors = len(parsed_tensors)
    needed_after: list[set[str]] = [set(out_set) for _ in range(n_tensors)]
    running_needed = set(out_set)
    for idx in range(n_tensors - 1, 0, -1):
        running_needed = running_needed | set(parsed_tensors[idx][0])
        needed_after[idx - 1] = set(running_needed)

    acc_chars, acc = _project_first_tensor(
        parsed_tensors[0][0], parsed_tensors[0][1], needed_after[0], add_op, is_zero
    )
    for idx in range(1, n_tensors):
        if not acc:
            return out_trie
        acc_chars, acc = _hash_join_step(
            acc_chars,
            acc,
            parsed_tensors[idx][0],
            parsed_tensors[idx][1],
            needed_after[idx],
            add_op,
            mul_op,
            is_zero,
        )

    # Reorder / duplicate output axes to match out_str and load AlgebraicTrie once
    acc_pos = {c: i for i, c in enumerate(acc_chars)}
    out_order = [acc_pos[c] for c in out_str]
    same_order = len(out_order) == len(acc_chars) and out_order == list(range(len(acc_chars)))
    for key, val in acc.items():
        if is_zero(val):
            continue
        out_key = key if same_order else tuple(key[i] for i in out_order)
        out_trie[out_key] = val

    return out_trie


def outer_product(
    tensor_a: Any,
    tensor_b: Any,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> AlgebraicTrie[Any, V]:
    """
    Compute the outer tensor product A (x) B over a semiring.

    C_{i_1...i_m, j_1...j_n} = A_{i_1...i_m} (x) B_{j_1...j_n}

    Args:
        tensor_a: First input tensor.
        tensor_b: Second input tensor.
        semiring: Semiring instance, class, or catalog name for multiplication.

    Returns:
        An `AlgebraicTrie` representing the outer product tensor.
    """
    sr = _resolve_semiring(semiring, tensor_a, tensor_b)
    is_zero = make_zero_predicate(sr)

    _, items_a = _get_semiring_and_items(tensor_a, sr)
    _, items_b = _get_semiring_and_items(tensor_b, sr)

    out_trie: AlgebraicTrie[Any, V] = AlgebraicTrie(semiring=sr)
    mul_op = sr.mul

    for key_a, val_a in items_a:
        norm_a = key_a if isinstance(key_a, tuple) else (key_a,)
        if is_zero(val_a):
            continue
        for key_b, val_b in items_b:
            norm_b = key_b if isinstance(key_b, tuple) else (key_b,)
            if is_zero(val_b):
                continue
            combined_val = mul_op(val_a, val_b)
            if not is_zero(combined_val):
                out_trie[norm_a + norm_b] = combined_val

    return out_trie


def dot(
    tensor_a: Any,
    tensor_b: Any,
    axes: int | tuple[list[int], list[int]] = 1,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> AlgebraicTrie[Any, V]:
    """
    Compute tensor contraction over specified axes.

    Args:
        tensor_a: First tensor.
        tensor_b: Second tensor.
        axes: Either an integer N (contracts last N axes of A with first N axes of B),
              or a tuple `(axes_a, axes_b)` listing 0-indexed axes to contract.
        semiring: Semiring instance, class, or catalog name for contraction arithmetic.

    Returns:
        An `AlgebraicTrie` containing the contracted tensor.
    """
    sr = _resolve_semiring(semiring, tensor_a, tensor_b)
    if not isinstance(tensor_a, (AlgebraicTrie, Mapping)):
        raise TypeError(f'Expected AlgebraicTrie or Mapping, got {type(tensor_a)}')
    if not isinstance(tensor_b, (AlgebraicTrie, Mapping)):
        raise TypeError(f'Expected AlgebraicTrie or Mapping, got {type(tensor_b)}')

    if len(tensor_a) == 0 or len(tensor_b) == 0:
        return AlgebraicTrie(semiring=sr)

    # Determine rank of tensors from keys without materializing item lists twice
    rank_a = max((len(k) if isinstance(k, tuple) else 1 for k in tensor_a), default=0)
    rank_b = max((len(k) if isinstance(k, tuple) else 1 for k in tensor_b), default=0)

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

    return einsum(subscript, tensor_a, tensor_b, semiring=sr)


def flatten_tensor(nested: Mapping[Any, Any], current_prefix: tuple = ()) -> dict[tuple, Any]:
    """
    Recursively flatten a nested dictionary into a tuple-indexed tensor mapping.
    Delegates to `converters.nested_to_flat` for zero-redundancy conversion.

    Args:
        nested: A recursively nested dictionary.
        current_prefix: Internal prefix tuple for recursion.

    Returns:
        A flat dictionary mapping index tuples `(i_1, i_2, ...)` to leaf values.
    """
    flat = dict(nested_to_flat(nested))
    if current_prefix:
        return {(*current_prefix, *k) if isinstance(k, tuple) else (*current_prefix, k): v for k, v in flat.items()}
    return flat


def unflatten_tensor(flat: Mapping[tuple, Any]) -> dict[Any, Any]:
    """
    Unflatten a tuple-indexed tensor mapping back into a recursively nested dictionary.
    Delegates to `converters.flat_to_nested` for zero-redundancy conversion.

    Args:
        flat: A dictionary mapping index tuples `(i_1, i_2, ...)` to leaf values.

    Returns:
        A recursively nested dictionary.
    """
    return dict(flat_to_nested(flat))


def permute_tensor(
    tensor: Mapping[tuple, Any],
    permutation: tuple[int, ...],
) -> dict[tuple, Any]:
    """
    Permute the dimensions of a sparse tensor.
    The tensor is represented as a mapping from coordinate tuples to values.

    Args:
        tensor: The input sparse tensor, e.g., {(0, 1, 0): val}.
        permutation: A tuple specifying the new order of axes, e.g., (2, 0, 1).

    Returns:
        A new sparse tensor with permuted dimensions.
    """
    result = {}
    for coords, val in tensor.items():
        new_coords = tuple(coords[i] for i in permutation)
        result[new_coords] = val
    return result


def unpermute_tensor(
    tensor: Mapping[tuple, Any],
    permutation: tuple[int, ...],
) -> dict[tuple, Any]:
    """
    Invert a tensor dimension permutation to restore the original index order.

    Args:
        tensor: Sparse tensor with permuted coordinate tuple keys.
        permutation: The permutation tuple that was previously applied.

    Returns:
        A new sparse tensor with original index ordering restored.
    """
    inv_perm = [0] * len(permutation)
    for idx, orig_pos in enumerate(permutation):
        inv_perm[orig_pos] = idx
    return permute_tensor(tensor, tuple(inv_perm))
