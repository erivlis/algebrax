import random
import timeit

from algebrax.converters import sparse_to_dense_matrix
from algebrax.matrix import dot
from algebrax.semiring import StandardSemiring
from algebrax.sparsity import density as calculate_density


def generate_sparse_matrix(rows, cols, density=0.1):
    """Generate a sparse dict-of-dicts matrix."""
    matrix = {}
    for r in range(rows):
        row_data = {}
        for c in range(cols):
            if random.random() < density:
                row_data[c] = 1.0
        if row_data:
            matrix[r] = row_data
    return matrix


def naive_multiply(A, B):
    """Standard O(N^3) list-of-lists multiplication."""
    rows_A = len(A)
    cols_A = len(A[0])
    rows_B = len(B)
    cols_B = len(B[0])

    if cols_A != rows_B:
        raise ValueError('Incompatible dimensions')

    C = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]

    for i in range(rows_A):
        for j in range(cols_B):
            total = 0.0
            for k in range(cols_A):
                total += A[i][k] * B[k][j]
            C[i][j] = total
    return C


def run_benchmark(N, target_density, iterations):
    # Setup Data (Apples to Apples)
    sparse_A = generate_sparse_matrix(N, N, target_density)
    sparse_B = generate_sparse_matrix(N, N, target_density)

    # Use library converter
    dense_A = sparse_to_dense_matrix(sparse_A, shape=(N, N))
    dense_B = sparse_to_dense_matrix(sparse_B, shape=(N, N))

    # Calculate actual density using library function
    actual_density_A = calculate_density(sparse_A, capacity=N * N)
    actual_density_B = calculate_density(sparse_B, capacity=N * N)
    avg_density = (actual_density_A + actual_density_B) / 2

    # 1. Naive List-of-Lists
    t_naive = timeit.timeit(lambda: naive_multiply(dense_A, dense_B), number=iterations)
    avg_naive = t_naive / iterations

    # 2. MappingTools Sparse
    t_sparse = timeit.timeit(lambda: dot(sparse_A, sparse_B, semiring=StandardSemiring()), number=iterations)
    avg_sparse = t_sparse / iterations

    speedup = avg_naive / avg_sparse

    print(f'{avg_density * 100:8.2f}% | {avg_naive:10.6f}s | {avg_sparse:10.6f}s | {speedup:7.2f}x')


def benchmark():
    N = 10
    iterations = 1000
    densities = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

    print(f'Benchmark: Matrix Multiplication ({N}x{N})')
    print(f'Iterations: {iterations}')
    print('-' * 60)
    print(f'{"Density":8} | {"Naive":10} | {"Sparse":10} | {"Speedup":7}')
    print('-' * 60)

    for d in densities:
        run_benchmark(N, d, iterations)


if __name__ == '__main__':
    benchmark()
