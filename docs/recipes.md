---
title: Recipes & Applications
description: Practical use-case recipes and interactive laboratory applications for algebrax.
icon: lucide/chef-hat
---

# Recipes & Applications

The [`reciepes/`](https://github.com/erivlis/algebrax/tree/main/reciepes) folder contains runnable use-case scripts, Jupyter Notebooks (`.ipynb`), and an interactive graphical laboratory demonstrating `algebrax` in real-world scenarios.

---

## Use Cases

### 2D Image Processing
* **Files**: [`image_processing.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/image_processing.py) | [`image_processing.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/image_processing.ipynb)
* **Run**: `uv run reciepes/image_processing.py`
* **Components**: `transforms.convolve`, `StandardSemiring`, `ArcticSemiring`, `TropicalSemiring`
* **Summary**: Applies 2D spatial convolution (`key_op = add_2d`) for linear image filtering (Sobel edge detection, sharpening) and non-linear mathematical morphology (Dilation via Max-Plus, Erosion via Min-Plus). Includes PIL Image support.

---

### Urban Traffic Resilience
* **Files**: [`traffic_network_resilience.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/traffic_network_resilience.py) | [`traffic_network_resilience.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/traffic_network_resilience.ipynb)
* **Run**: `uv run reciepes/traffic_network_resilience.py`
* **Components**: `semiring.TropicalSemiring`, `matrix.core.power`, `analysis.forman_ricci_curvature`, `probability.markov_steady_state`
* **Summary**: Combines Tropical matrix powers ($M^k$) for shortest-path travel latency, Forman-Ricci edge curvature ($K < 0$) to identify highway choke points, and Markov steady-state analysis for equilibrium traffic distribution.

---

### Natural Language Parsing
* **Files**: [`nlp_provenance_parser.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/nlp_provenance_parser.py) | [`nlp_provenance_parser.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/nlp_provenance_parser.ipynb)
* **Run**: `uv run reciepes/nlp_provenance_parser.py`
* **Components**: `matrix.core.dot`, `semiring.ProvenanceSemiring`, `probability.entropy`
* **Summary**: Executes CYK Context-Free Grammar parsing via matrix multiplication (`dot`), tracks symbolic rule derivation polynomials with `ProvenanceSemiring`, and audits syntactic ambiguity using Shannon entropy $H(\text{Trees})$.

---

### Post-Quantum Cryptography
* **Files**: [`post_quantum_crypto_exchange.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/post_quantum_crypto_exchange.py) | [`post_quantum_crypto_exchange.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/post_quantum_crypto_exchange.ipynb)
* **Run**: `uv run reciepes/post_quantum_crypto_exchange.py`
* **Components**: `semiring.DigitalSemiring`, `matrix.core.dot`, `transforms.z_transform`, `probability.mutual_information`
* **Summary**: Demonstrates non-commutative matrix key exchange ($U = A M A, V = B M B$) over `DigitalSemiring`, complex Z-transform modulation $X(z)$ at shared key coordinates, and mutual information verification ($I(X; Y) = 0$).

---

### Supply Chain Logistics
* **Files**: [`supply_chain_optimal_transport.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/supply_chain_optimal_transport.py) | [`supply_chain_optimal_transport.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/supply_chain_optimal_transport.ipynb)
* **Run**: `uv run reciepes/supply_chain_optimal_transport.py`
* **Components**: `trie.AlgebraicTrie`, `lattice.join`, `lattice.meet`, `probability.kl_divergence`
* **Summary**: Stores 3D demand tensors `(Warehouse, Region, Season)` with subtree contraction via `AlgebraicTrie`, calculates peak ($\vee$) and baseline ($\wedge$) capacity bounds with lattice join/meet, and audits allocation mismatch using KL divergence.

---

### Financial Risk & Portfolio
* **Files**: [`financial_risk_portfolio.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/financial_risk_portfolio.py) | [`financial_risk_portfolio.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/financial_risk_portfolio.ipynb)
* **Run**: `uv run reciepes/financial_risk_portfolio.py`
* **Components**: `automata.simulate_dfa`, `matrix.academic.eigen_centrality`, `semiring.VarianceSemiring`, `matrix.core.power`
* **Summary**: Simulates automated trade execution state machines (`simulate_dfa`), computes dominant eigenvector asset centrality (`eigen_centrality`) on cross-asset correlation matrices, and calculates expected return $E[X]$ and variance $\text{Var}(X)$ over multi-step market transition paths.

---

## Graphical Laboratory

### DearPyGui Interactive Lab
* **File**: [`dearpygui_lab.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/dearpygui_lab.py)
* **Run**: `uv run reciepes/dearpygui_lab.py`
* **Summary**: Desktop GUI built with DearPyGui featuring 12 interactive modules: real image file convolution with side-by-side texture preview, force-directed graph curvature visualization, semiring matrix powers, CYK parsing, DFA/NFA simulators, signal transforms, and information theory tools.
