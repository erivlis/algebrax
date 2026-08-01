---
title: Recipes & Applications
description: Practical use-case recipes and interactive laboratory applications for algebrax.
icon: lucide/chef-hat
---

# Recipes & Applications

The [`../recipes/`](https://github.com/erivlis/algebrax/tree/main/reciepes) folder contains runnable use-case scripts, Jupyter Notebooks (`.ipynb`), and an interactive graphical laboratory demonstrating `algebrax` in real-world scenarios.

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

### Vibration & Structural Analysis
* **Files**: [`vibration_structural_analysis.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/vibration_structural_analysis.py) | [`vibration_structural_analysis.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/vibration_structural_analysis.ipynb)
* **Run**: `uv run reciepes/vibration_structural_analysis.py`
* **Components**: `group.compose`, `group.signature`, `matrix.academic.determinant`, `transforms.hilbert`
* **Summary**: Models rotational and reflectional permutation symmetries (`compose`, `signature`) across turbine assemblies, evaluates mechanical stiffness determinants (`determinant`), and extracts instantaneous vibration amplitude envelopes (`hilbert`) for fatigue detection.

---

### Telecommunications & Fractal Dynamics
* **Files**: [`telecom_fractal_network.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/telecom_fractal_network.py) | [`telecom_fractal_network.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/telecom_fractal_network.ipynb)
* **Run**: `uv run reciepes/telecom_fractal_network.py`
* **Components**: `transforms.walsh_hadamard`, `analysis.laplacian`, `analysis.divergence`, `metrics.box_counting_dimension`
* **Summary**: Encodes telemetry streams into orthogonal Hadamard spectra (`walsh_hadamard`) with dual self-inverse reconstruction, evaluates graph Laplacian signal diffusion (`laplacian`) and net flow divergence (`divergence`), and measures spatial cell tower coverage dimension (`box_counting_dimension`).

---

### Quantum Spin-Chain & Convex Optimization
* **Files**: [`quantum_convex_optimization.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/quantum_convex_optimization.py) | [`quantum_convex_optimization.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/quantum_convex_optimization.ipynb)
* **Run**: `uv run reciepes/quantum_convex_optimization.py`
* **Components**: `transforms.legendre_fenchel`, `matrix.core.block_diag`, `matrix.core.trace`, `automata.simulate_nfa`
* **Summary**: Computes dual Fenchel-Legendre convex conjugate values (`legendre_fenchel`) for primal loss functions, constructs block diagonal quantum Hamiltonians (`block_diag`) with matrix trace invariants (`trace`), and simulates probabilistic superposition decay (`simulate_nfa`).

---

### Sensor Network Reliability & Heat Gradient Analysis
* **Files**: [`sensor_network_reliability.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/sensor_network_reliability.py) | [`sensor_network_reliability.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/sensor_network_reliability.ipynb)
* **Run**: `uv run reciepes/sensor_network_reliability.py`
* **Components**: `semiring.ViterbiSemiring`, `matrix.core.power`, `analysis.gaussian_kernel`, `analysis.gradient`, `metrics.sparsity`
* **Summary**: Calculates multi-hop maximum transmission success probabilities ($P_{\max}$) across lossy wireless links using `ViterbiSemiring` $(\max, \times)$, computes spatial Gaussian RBF similarity matrices (`gaussian_kernel`) with sparsity audits, and isolates thermal flux boundaries via discrete scalar field gradients (`gradient`).

---

### Holographic Bulk-Boundary Duality & Entanglement Entropy
* **Files**: [`holographic_bulk_boundary.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/holographic_bulk_boundary.py) | [`holographic_bulk_boundary.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/holographic_bulk_boundary.ipynb)
* **Run**: `uv run reciepes/holographic_bulk_boundary.py`
* **Components**: `analysis.forman_ricci_curvature`, `analysis.divergence`, `trie.AlgebraicTrie`, `probability.entropy`, `probability.mutual_information`
* **Summary**: Evaluates discrete negative Forman-Ricci curvature ($K < 0$) on hyperbolic bulk graphs ($\text{AdS}_3$), proves the discrete Holographic Gauss-Stokes divergence theorem ($\int_{\text{Bulk}} \text{div}(F) = \oint_{\partial} F$), contracts MERA tensor network scale trees (`AlgebraicTrie`), and calculates Ryu-Takayanagi boundary entanglement entropy $S(A) = \frac{\text{Area}(\gamma_A)}{4 G_N}$.

---

### Optical Holography Simulation & Wavefront Reconstruction
* **Files**: [`optical_holography_simulation.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/optical_holography_simulation.py) | [`optical_holography_simulation.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/optical_holography_simulation.ipynb)
* **Run**: `uv run reciepes/optical_holography_simulation.py`
* **Components**: `transforms.dft`, `transforms.idft`, `probability.entropy`
* **Summary**: Simulates physical optical interference patterns $I(x) = |O(x) + R(x)|^2$ between object and reference plane waves, reconstructs virtual object wavefronts via reference illumination ($R \cdot I$), evaluates angular frequency diffraction spectra using `dft` and `idft`, and audits Michelson fringe visibility ($V = 98\%$) and Shannon entropy.

---

### Topological Data Analysis (TDA) & Persistent Homology
* **Files**: [`topological_data_analysis.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/topological_data_analysis.py) | [`topological_data_analysis.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/topological_data_analysis.ipynb)
* **Run**: `uv run reciepes/topological_data_analysis.py`
* **Components**: `semiring.BooleanSemiring`, `matrix.power`, `analysis.forman_ricci_curvature`, `matrix.academic.determinant`
* **Summary**: Evaluates transitive closure matrices over `BooleanSemiring` $(\lor, \land)$ to extract connected component equivalence classes and zeroth Betti numbers $b_0(\epsilon)$ across Vietoris-Rips point-cloud filtrations, isolates topological inter-cluster bridges via negative Forman-Ricci edge curvature ($K < 0$), and audits boundary operator Laplacians via determinant singularities.

---

### Control Theory & State-Space Systems
* **Files**: [`control_theory_state_space.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/control_theory_state_space.py) | [`control_theory_state_space.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/control_theory_state_space.ipynb)
* **Run**: `uv run reciepes/control_theory_state_space.py`
* **Components**: `matrix.core.power`, `transforms.z_transform`, `matrix.academic.determinant`
* **Summary**: Computes multi-step discrete state transition trajectories $x[k] = A^k x[0]$, evaluates Z-domain transfer functions $H(z) = \sum h[n] z^{-n}$ for impulse response sequences, and audits system asymptotic stability via characteristic matrix determinants $\det(I - A)$.

---

### Algebraic Knot Theory & Topological Invariants
* **Files**: [`algebraic_knot_theory.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/algebraic_knot_theory.py) | [`algebraic_knot_theory.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/algebraic_knot_theory.ipynb)
* **Run**: `uv run reciepes/algebraic_knot_theory.py`
* **Components**: `semiring.KnotSemiring`, `semiring.MonoidAlgebraSemiring`, `group.compose`, `group.signature`
* **Summary**: Multiplies formal Skein module knot states over the connected sum monoid ($\#$), composes Artin braid group strand crossings $B_n$ with parity signature invariants ($\pm 1$), and evaluates Laurent Jones polynomial multiplications $V(K_1 \# K_2) = V(K_1) \cdot V(K_2)$.

---

### Sheaf Cohomology & Multi-Agent Network Consensus
* **Files**: [`sheaf_cohomology_consensus.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/sheaf_cohomology_consensus.py) | [`sheaf_cohomology_consensus.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/sheaf_cohomology_consensus.ipynb)
* **Run**: `uv run reciepes/sheaf_cohomology_consensus.py`
* **Components**: `analysis.gradient`, `analysis.laplacian`, `semiring.MonoidAlgebraSemiring`
* **Summary**: Measures edge channel state inconsistencies via coboundary gradients $\delta_0(f)$, diffuses multi-robot state estimates toward global mean consensus via Sheaf Laplacian iterations ($L_\mathcal{F} = \text{div}(\text{grad} f)$), and aggregates localized agent observation sections in formal monoid linear combinations.

---

### Trajectoid Rolling Kinematics & SO(3) Path Tracing
* **Files**: [`trajectoid_rolling_kinematics.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/trajectoid_rolling_kinematics.py) | [`trajectoid_rolling_kinematics.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/trajectoid_rolling_kinematics.ipynb)
* **Run**: `uv run reciepes/trajectoid_rolling_kinematics.py`
* **Components**: `analysis.gradient`, `matrix.core.dot`, `metrics.sparsity`
* **Summary**: Evaluates discrete velocity vectors along periodic 2D figure-eight lemniscate curves via `gradient`, integrates 3D non-holonomic spatial orientation matrix steps $R_{k+1} = R_k \cdot dR_k$ in $SO(3)$, and audits contact matrix sparsity and closed-loop trajectory tracking precision.

---

### Sparse Tensor Einstein Summation & Multimodal Fusion
* **Files**: [`sparse_tensor_einsum.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/sparse_tensor_einsum.py) | [`sparse_tensor_einsum.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/sparse_tensor_einsum.ipynb)
* **Run**: `uv run reciepes/sparse_tensor_einsum.py`
* **Components**: `tensor.einsum`, `tensor.outer_product`, `tensor.tensordot`, `tensor.flatten_tensor`
* **Summary**: Evaluates arbitrary-rank sparse tensor contractions $C_{i, l} = \bigoplus_{j, k} A_{i, j, k} \otimes B_{j, k, l}$ over polymorphic semirings (Standard and Tropical Min-Plus), computes rank-expanding tensor outer products $A \otimes B$, and handles bidirectional nested dict conversions.

---

### Schwarzschild Black Hole Spacetime & Gravitational Lensing
* **Files**: [`blackhole_spacetime_simulation.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/blackhole_spacetime_simulation.py) | [`blackhole_spacetime_simulation.ipynb`](https://github.com/erivlis/algebrax/blob/main/reciepes/blackhole_spacetime_simulation.ipynb)
* **Run**: `uv run reciepes/blackhole_spacetime_simulation.py`
* **Components**: `tensor.einsum`, `transforms.z_transform`, `analysis.gradient`, `analysis.forman_ricci_curvature`, `probability.entropy`, `probability.kl_divergence`
* **Summary**: Constructs Schwarzschild spacetime metric tensors $g_{\mu \nu}$ around event horizon $r_s$, contracts inverse metrics $g^{\mu \alpha} g_{\alpha \nu} = \delta^\mu_\nu$ via `tensor.einsum`, models gravitational redshift spectral modulation via `z_transform`, evaluates photon deflection angles $\Delta \phi = \frac{4GM}{c^2 b}$ and spatial curvature near the photon sphere, and audits Bekenstein-Hawking entropy $S_{\text{BH}} = \frac{A}{4 \ell_P^2}$ and Hawking radiation quantum information scrambling.

---

### 3D Gaussian Splatting & Projective Screen Rendering
* **Files**: [`gaussian_splatting_rendering.py`](https://github.com/erivlis/algebrax/blob/main/recipes/gaussian_splatting_rendering.py) | [`gaussian_splatting_rendering.ipynb`](https://github.com/erivlis/algebrax/blob/main/recipes/gaussian_splatting_rendering.ipynb)
* **Run**: `uv run recipes/gaussian_splatting_rendering.py`
* **Components**: `matrix.core.dot`, `matrix.core.transpose`, `analysis.gaussian_kernel`
* **Summary**: Constructs 3D spatial Gaussian covariance matrices $\Sigma = R S S^T R^T$ via $SO(3)$ Euler rotation matrix compositions, projects 3D spatial ellipsoids into 2D screen coordinate covariance matrices $\Sigma' = J W \Sigma W^T J^T$ using perspective Jacobian transformations, and performs depth-sorted volumetric $\alpha$-compositing ray-marching.

---

### Simplicial Homology & Topological Betti Barcodes (EP-0110)
* **Files**: [`topological_homology_betti.py`](https://github.com/erivlis/algebrax/blob/main/recipes/topological_homology_betti.py) | [`topological_homology_betti.ipynb`](https://github.com/erivlis/algebrax/blob/main/recipes/topological_homology_betti.ipynb)
* **Run**: `uv run recipes/topological_homology_betti.py`
* **Components**: `homology.SimplicialComplex`, `homology.betti_numbers`, `analysis.SparseChainComplex`
* **Summary**: Constructs $k$-simplices $(v_0, \dots, v_k)$, evaluates sparse boundary matrices $D_k$, verifies homological nilpotency $D_{k-1} \circ D_k = \mathbf{0}$, and computes Betti number invariants $\beta_k = \dim(\ker D_k) - \text{rank}(D_{k+1})$.

---

### Clifford Geometric Algebra & 3D Rotor Rotations (EP-0111)
* **Files**: [`clifford_rotor_kinematics.py`](https://github.com/erivlis/algebrax/blob/main/recipes/clifford_rotor_kinematics.py) | [`clifford_rotor_kinematics.ipynb`](https://github.com/erivlis/algebrax/blob/main/recipes/clifford_rotor_kinematics.ipynb)
* **Run**: `uv run recipes/clifford_rotor_kinematics.py`
* **Components**: `clifford.CliffordSemiring`, `clifford.rotor_rotation`, `semiring.QuotientMonoidAlgebraSemiring`
* **Summary**: Implements multivector geometric product $A B = A \cdot B + A \wedge B$ over $Cl(p,q,r)$ blade keys and performs 3D spatial rotor rotations $v' = R v R^\dagger$ without gimbal lock.

---

### Galois Finite Fields & Cryptographic Arithmetic (EP-0112)
* **Files**: [`galois_field_cryptography.py`](https://github.com/erivlis/algebrax/blob/main/recipes/galois_field_cryptography.py) | [`galois_field_cryptography.ipynb`](https://github.com/erivlis/algebrax/blob/main/recipes/galois_field_cryptography.ipynb)
* **Run**: `uv run recipes/galois_field_cryptography.py`
* **Components**: `galois.GaloisFieldSemiring`, `galois.gf_matrix_mul`, `semiring.QuotientMonoidAlgebraSemiring`
* **Summary**: Evaluates finite field arithmetic $\text{GF}(p^m)$ over polynomial modulo quotient semirings $P(x) = x^8 + x^4 + x^3 + x + 1$ and computes AES MixColumns matrix products.
## Graphical Laboratory

### DearPyGui Interactive Lab
* **File**: [`lab.py`](https://github.com/erivlis/algebrax/blob/main/reciepes/lab.py)
* **Run**: `uv run reciepes/lab.py`
* **Summary**: Desktop GUI built with DearPyGui featuring 12 interactive modules: real image file convolution with side-by-side texture preview, force-directed graph curvature visualization, semiring matrix powers, CYK parsing, DFA/NFA simulators, signal transforms, and information theory tools.
