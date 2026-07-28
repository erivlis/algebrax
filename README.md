<p align="center">
  <img src="docs/assets/images/banner.png" alt="AlgebraX Banner" width="100%">
</p>

<h1 align="center">AlgebraX</h1>

<p align="center">
  <b>Algebraic Primitives for Sparse Data Structures in Python</b>
</p>

<p align="center">
  <a href="https://github.com/erivlis/algebrax/actions"><img src="https://img.shields.io/badge/tests-230%20passed-brightgreen.svg" alt="Tests"></a>
  <a href="https://pypi.org/project/algebrax/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python Version"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Ruff"></a>
  <a href="https://github.com/erivlis/algebrax/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</p>

---

`algebrax` treats Python's native `dict` as a first-class sparse algebraic object, unifying linear algebra, graph
algorithms, formal language theory, signal transforms, and information metrics under a single polymorphic framework.

## Key Features

* ⚡ **Zero Heavy Dependencies**: Pure Python core requiring no C++ build steps. Includes native bidirectional converters
  between sparse dict mappings and dense multidimensional arrays.
* 🔄 **Polymorphic Semiring Computing**: By swapping the algebraic semiring $(\oplus, \otimes)$, the exact same matrix
  algorithms compute standard linear algebra, tropical shortest path latencies, or symbolic rule provenance.
* 🌌 **Sparse Multidimensional Tensors**: Arbitrary nested mappings behave as infinite-dimensional sparse tensors, tries,
  and lattices (`AlgebraicTrie`) with custom key operators.
* 🔬 **Interactive Desktop GUI**: Built-in [DearPyGui](https://github.com/hoffstadt/DearPyGui) laboratory with 12
  interactive modules, dynamic texture previews, force-directed graph canvases, and signal transforms.

---

## Installation

```bash
# Using uv (recommended)
uv add algebrax

# Using pip
pip install algebrax
```

---

## 5-Minute Quickstart

By changing the `semiring` parameter in `matrix.dot`, you can transform standard linear matrix multiplication into
shortest-path solvers or symbolic rule derivation tracking:

```python
from algebrax.matrix import dot
from algebrax.semiring import ProvenanceSemiring, StandardSemiring, TropicalSemiring

# Define a Sparse Graph Adjacency / Distance Matrix
graph = {
    0: {1: 2.0, 2: 10.0},
    1: {2: 3.0},
}

# 1. Standard Linear Matrix Multiplication (+, *)
linear_mult = dot(graph, graph, semiring=StandardSemiring())
print('Linear Combination (0->2):', linear_mult[0][2])
# Output: 30.0

# 2. Tropical Shortest Path (min, +)
shortest_path = dot(graph, graph, semiring=TropicalSemiring())
print('Shortest Path Cost (0->1->2):', shortest_path[0][2])
# Output: 5.0

# 3. Symbolic Provenance Rule Tracking
provenance_graph = {
    0: {1: {('rule_A',): 1}, 2: {('rule_C',): 1}},
    1: {2: {('rule_B',): 1}},
}
provenance_mult = dot(provenance_graph, provenance_graph, semiring=ProvenanceSemiring())
print('Symbolic Derivation Polynomial:', provenance_mult[0][2])
# Output: {('rule_A', 'rule_B'): 1}
```

---

## Use Case Recipes & Jupyter Notebooks

The [`reciepes/`](reciepes) directory contains standalone CLI scripts and matching interactive `.ipynb` notebooks for 10
real-world scenarios:

| Category                   | Use Case Recipe Script                                                            | Jupyter Notebook                                                                        | Core Algebraic Components                                                                   |
|:---------------------------|:----------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------|
| **Image Processing**       | [`image_processing.py`](reciepes/image_processing.py)                             | [`image_processing.ipynb`](reciepes/image_processing.ipynb)                             | `transforms.convolve`, `StandardSemiring`, `ArcticSemiring`, `TropicalSemiring`             |
| **Traffic Resilience**     | [`traffic_network_resilience.py`](reciepes/traffic_network_resilience.py)         | [`traffic_network_resilience.ipynb`](reciepes/traffic_network_resilience.ipynb)         | `semiring.TropicalSemiring`, `matrix.power`, `analysis.forman_ricci_curvature`              |
| **NLP Parsing**            | [`nlp_provenance_parser.py`](reciepes/nlp_provenance_parser.py)                   | [`nlp_provenance_parser.ipynb`](reciepes/nlp_provenance_parser.ipynb)                   | `matrix.dot`, `semiring.ProvenanceSemiring`, `probability.entropy`                          |
| **Post-Quantum Security**  | [`post_quantum_crypto_exchange.py`](reciepes/post_quantum_crypto_exchange.py)     | [`post_quantum_crypto_exchange.ipynb`](reciepes/post_quantum_crypto_exchange.ipynb)     | `semiring.DigitalSemiring`, `transforms.z_transform`, `probability.mutual_information`      |
| **Supply Chain Logistics** | [`supply_chain_optimal_transport.py`](reciepes/supply_chain_optimal_transport.py) | [`supply_chain_optimal_transport.ipynb`](reciepes/supply_chain_optimal_transport.ipynb) | `trie.AlgebraicTrie`, `lattice.join`, `lattice.meet`, `probability.kl_divergence`           |
| **Financial Risk**         | [`financial_risk_portfolio.py`](reciepes/financial_risk_portfolio.py)             | [`financial_risk_portfolio.ipynb`](reciepes/financial_risk_portfolio.ipynb)             | `automata.simulate_dfa`, `matrix.academic.eigen_centrality`, `semiring.VarianceSemiring`    |
| **Structural Analysis**    | [`vibration_structural_analysis.py`](reciepes/vibration_structural_analysis.py)   | [`vibration_structural_analysis.ipynb`](reciepes/vibration_structural_analysis.ipynb)   | `group.compose`, `group.signature`, `matrix.academic.determinant`, `transforms.hilbert`     |
| **Telecommunications**     | [`telecom_fractal_network.py`](reciepes/telecom_fractal_network.py)               | [`telecom_fractal_network.ipynb`](reciepes/telecom_fractal_network.ipynb)               | `transforms.walsh_hadamard`, `analysis.laplacian`, `metrics.box_counting_dimension`         |
| **Quantum Optimization**   | [`quantum_convex_optimization.py`](reciepes/quantum_convex_optimization.py)       | [`quantum_convex_optimization.ipynb`](reciepes/quantum_convex_optimization.ipynb)       | `transforms.legendre_fenchel`, `matrix.block_diag`, `matrix.trace`, `automata.simulate_nfa` |
| **Sensor Reliability**     | [`sensor_network_reliability.py`](reciepes/sensor_network_reliability.py)         | [`sensor_network_reliability.ipynb`](reciepes/sensor_network_reliability.ipynb)         | `semiring.ViterbiSemiring`, `matrix.power`, `analysis.gaussian_kernel`, `analysis.gradient` |

Run any recipe using `uv`:

```bash
uv run reciepes/image_processing.py
```

---

## Graphical Desktop Laboratory

Launch the interactive [DearPyGui](https://github.com/hoffstadt/DearPyGui) laboratory application featuring 12
interactive modules, live image convolution texture previews, force-directed graph canvases, signal transforms, and
information theory calculators:

```bash
uv run reciepes/dearpygui_lab.py
```

---

## Documentation

Comprehensive documentation is hosted online and structured into 3 Diátaxis pillars:

* 🚀 [**Start**](docs/index.md): Installation, quickstart, and core philosophy.
* 📖 [**Tutorials**](docs/tutorials/semirings/semiring_standard.md): In-depth guides for Semirings, Tries, Transforms,
  Graphs, and Benchmarks.
* 🍳 [**Recipes & GUI Lab**](docs/recipes.md): Real-world use cases and laboratory documentation.

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.
