"""
Property-based testing using Hypothesis.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from algebrax.matrix.core import add, dot, inner, trace, transpose
from algebrax.semiring import StandardSemiring
from algebrax.typing import SparseMatrix, SparseVector

# --- Custom Hypothesis Strategies ---

@st.composite
def sparse_vectors(
    draw, max_size=5, val_st=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)
):
    keys = draw(st.sets(st.integers(min_value=0, max_value=10), max_size=max_size))
    return {k: draw(val_st) for k in keys if draw(st.booleans())}


@st.composite
def sparse_matrices(
    draw, max_dim=5, val_st=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)
):
    row_keys = draw(st.sets(st.integers(min_value=0, max_value=max_dim), max_size=max_dim))
    mat = {}
    for r in row_keys:
        col_keys = draw(st.sets(st.integers(min_value=0, max_value=max_dim), max_size=max_dim))
        row = {c: draw(val_st) for c in col_keys if draw(st.booleans())}
        if row:
            mat[r] = row
    return mat


# --- Property Tests ---

@given(m1=sparse_matrices(), m2=sparse_matrices())
@settings(max_examples=100)
def test_matrix_addition_commutativity(m1: SparseMatrix, m2: SparseMatrix):
    """Property: A + B == B + A for sparse matrix addition."""
    sum1 = add(m1, m2)
    sum2 = add(m2, m1)
    assert sum1 == sum2


@given(m=sparse_matrices())
@settings(max_examples=100)
def test_matrix_transpose_involution(m: SparseMatrix):
    """Property: (A^T)^T == A for sparse matrix transpose."""
    t1 = transpose(m)
    t2 = transpose(t1)
    assert t2 == m


@given(m=sparse_matrices())
@settings(max_examples=100)
def test_matrix_trace_transpose_invariance(m: SparseMatrix):
    """Property: trace(A^T) == trace(A)."""
    t_m = transpose(m)
    assert trace(m) == trace(t_m)


@given(u=sparse_vectors(), v=sparse_vectors())
@settings(max_examples=100)
def test_vector_inner_commutativity(u: SparseVector, v: SparseVector):
    """Property: inner(u, v) == inner(v, u) over standard semiring."""
    val1 = inner(u, v)
    val2 = inner(v, u)
    assert val1 == val2


@given(m=sparse_matrices())
@settings(max_examples=50)
def test_matrix_identity_multiplication(m: SparseMatrix):
    """Property: I @ A == A where I is the identity matrix covering m's row keys."""
    from algebrax.converters import prune_sparse

    pruned_m = prune_sparse(m)
    if not pruned_m:
        return
    row_keys = set(pruned_m.keys())
    eye = {k: {k: 1.0} for k in row_keys}
    res = dot(eye, pruned_m)
    assert res == pruned_m
