"""
Type definitions for the algebra namespace.

This module provides generic type variables and type aliases used throughout
the algebra submodules to ensure consistent type hinting for sparse and dense
data structures.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import TypeAlias, TypeVar

__all__ = [
    'A',
    'DenseMatrix',
    'DenseVector',
    'K',
    'N',
    'S',
    'SparseMatrix',
    'SparseTensor',
    'SparseVector',
    'V',
]

# Type Variables
K = TypeVar('K')  # Key type (hashable)
"""Generic type for keys in sparse mappings (e.g., int, str, tuple)."""

N = TypeVar('N', int, float, complex, Decimal)  # Numeric value type
"""Generic type for numeric values (int, float, complex, Decimal)."""

V = TypeVar('V')  # Generic value type
"""Generic type for any value (used in structural operations like transpose)."""

S = TypeVar('S')  # State type (for automata)
"""Generic type for states in finite state machines."""

A = TypeVar('A')  # Alphabet/Symbol type (for automata)
"""Generic type for input symbols in finite state machines."""

# Sparse Types
SparseVector: TypeAlias = Mapping[K, V]
"""
A sparse vector represented as a mapping from keys to values.
Example: `{0: 1.0, 5: 2.5}` represents a vector with non-zero values at indices 0 and 5.
"""

SparseMatrix: TypeAlias = Mapping[K, Mapping[K, V]]
"""
A sparse matrix represented as a nested mapping (row -> column -> value).
Example: `{0: {1: 5.0}}` represents a matrix with value 5.0 at row 0, column 1.
"""

SparseTensor: TypeAlias = Mapping[K, 'SparseTensor[K, V] | V']  # Recursive definition
"""
A sparse N-dimensional tensor represented as a recursively nested mapping.
Example: `{0: {0: {1: 5.0}}}` represents a rank-3 tensor.
"""

# Dense Types
DenseVector: TypeAlias = Sequence[V]
"""
A dense vector represented as a sequence (list, tuple, etc.).
Example: `[1.0, 0.0, 0.0, 2.5]`.
"""

DenseMatrix: TypeAlias = Sequence[Sequence[V]]
"""
A dense matrix represented as a sequence of sequences.
Example: `[[0.0, 5.0], [0.0, 0.0]]`.
"""
