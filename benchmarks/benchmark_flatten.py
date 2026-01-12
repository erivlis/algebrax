import random
import timeit
from mappingtools.operators import flatten
from algebrax.converters import nested_to_flat
from algebrax.sparsity import deepness, uniformness, wideness

def create_nested_dict(depth, width):
    if depth == 0:
        return 1
    return {i: create_nested_dict(depth - 1, width) for i in range(width)}

def create_unbalanced_dict(depth, max_width):
    if depth == 0:
        return 1
    
    # Randomly stop early to create depth imbalance
    if random.random() < 0.1:
        return 1
        
    width = random.randint(1, max_width)
    return {i: create_unbalanced_dict(depth - 1, max_width) for i in range(width)}

def run_benchmark(name, data, number=1000):
    print(f'\nScenario: {name}')
    
    # Calculate metrics
    d = deepness(data)
    w = wideness(data)
    u = uniformness(data)
    print(f'  Metrics: Depth={d}, Width={w}, Uniformness={u:.2f}')
    
    t1 = timeit.timeit(lambda: flatten(data, delimiter=None), number=number)
    print(f'  operators.flatten:          {t1:.4f}s')

    t2 = timeit.timeit(lambda: nested_to_flat(data), number=number)
    print(f'  algebra.nested_to_flat:     {t2:.4f}s')

    if t2 > 0:
        ratio = t1 / t2
        print(f'  Ratio (flatten / nested_to_flat): {ratio:.2f}x')
    else:
        print('  Ratio: Inf (too fast)')

def benchmark():
    # 1. Balanced (Medium)
    data_balanced = create_nested_dict(depth=5, width=5) # 3125 leaves
    run_benchmark('Balanced (Depth=5, Width=5)', data_balanced)

    # 2. Wide & Shallow
    data_wide = create_nested_dict(depth=2, width=100) # 10000 leaves
    run_benchmark('Wide & Shallow (Depth=2, Width=100)', data_wide)

    # 3. Thin & Deep
    # Recursion limit might be hit if too deep. Python default is 1000.
    data_deep = create_nested_dict(depth=100, width=1) # 1 leaf, 100 nodes
    run_benchmark('Thin & Deep (Depth=100, Width=1)', data_deep)

    # 4. Unbalanced
    random.seed(42)
    data_unbalanced = create_unbalanced_dict(depth=6, max_width=4)
    run_benchmark('Unbalanced (Depth=6, MaxWidth=4)', data_unbalanced)

if __name__ == '__main__':
    benchmark()
