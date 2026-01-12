from collections import defaultdict
from collections.abc import Iterable, MutableMapping
from typing import Generic, TypeVar

from algebrax.semiring import Semiring, StandardSemiring

V = TypeVar('V')
K = TypeVar('K')


class AlgebraicTrie(MutableMapping[tuple[K, ...], V], Generic[K, V]):
    """
    A Trie (Prefix Tree) that behaves as a Sparse Tensor over a Semiring.

    Unlike a standard Trie which just stores values, an AlgebraicTrie uses the
    Semiring's `plus` operation to merge values at the same path, and can
    perform algebraic contractions (sums) over subtrees.

    This structure can be viewed as an infinite-dimensional sparse tensor where
    indices are sequences of keys.

    Args:
        semiring: The Semiring class to use for operations (default: StandardSemiring).
    """

    def __init__(self, semiring: type[Semiring[V]] = StandardSemiring):
        # Instantiate the semiring to access properties like zero/one
        self.semiring = semiring()
        # The recursive factory for the sparse structure: infinite depth
        self._factory = lambda: defaultdict(self._factory)
        self._data = self._factory()
        self._value_key = object()  # Unique sentinel key to store the value at a node

    def __setitem__(self, key: Iterable[K], value: V) -> None:
        """
        Sets the value at the given path.
        Note: This OVERWRITES the existing value. To merge, use `add`.
        """
        node = self._data
        for k in key:
            node = node[k]
        node[self._value_key] = value

    def __getitem__(self, key: Iterable[K]) -> V:
        """
        Retrieves the exact value at the given path.
        Raises KeyError if the path or value does not exist.
        """
        node = self._data
        for k in key:
            if k not in node:
                raise KeyError(key)
            node = node[k]

        if self._value_key not in node:
            raise KeyError(key)

        return node[self._value_key]

    def __delitem__(self, key: Iterable[K]) -> None:
        """Deletes the value at the given path."""
        path = list(key)
        if not path:
            if self._value_key in self._data:
                del self._data[self._value_key]
            else:
                raise KeyError(key)
            return

        # Stack to track nodes for potential cleanup
        stack = [(None, self._data)]
        for k in path:
            parent = stack[-1][1]
            if k not in parent:
                raise KeyError(key)
            stack.append((k, parent[k]))

        target_node = stack[-1][1]
        if self._value_key not in target_node:
            raise KeyError(key)

        del target_node[self._value_key]

        # Cleanup empty branches up the tree
        while len(stack) > 1:
            k, node = stack.pop()
            parent = stack[-1][1]
            if not node:  # Empty dict (no children, no value)
                del parent[k]
            else:
                break

    def __iter__(self):
        """Iterates over all keys (paths) that have a value."""
        # DFS traversal
        stack = [(self._data, [])]
        while stack:
            node, path = stack.pop()
            if self._value_key in node:
                yield tuple(path)

            for k, v in node.items():
                if k != self._value_key:
                    stack.append((v, [*path, k]))

    def __len__(self) -> int:
        """Returns the number of set values in the Trie."""
        return sum(1 for _ in self)

    def add(self, key: Iterable[K], value: V) -> None:
        """
        Algebraic Addition: Merges the value into the given path using `semiring.add`.

        T[key] = T[key] + value
        """
        node = self._data
        for k in key:
            node = node[k]

        current = node.get(self._value_key, self.semiring.zero)
        node[self._value_key] = self.semiring.add(current, value)

    def contract(self, prefix: Iterable[K] = ()) -> V:
        """
        Algebraic Contraction: Sums all values in the subtree defined by `prefix`.

        Returns: Sum_over_subtree(T[prefix...])
        """
        node = self._data
        for k in prefix:
            if k not in node:
                return self.semiring.zero
            node = node[k]

        # Traverse subtree and sum values
        total = self.semiring.zero
        stack = [node]
        while stack:
            curr = stack.pop()
            if self._value_key in curr:
                total = self.semiring.add(total, curr[self._value_key])

            for k, v in curr.items():
                if k != self._value_key:
                    stack.append(v)

        return total
