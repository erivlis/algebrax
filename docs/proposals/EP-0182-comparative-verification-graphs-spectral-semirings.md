---
title: "EP-0182: Comparative Verification — Graph Calculus, Spectral Theory & Path Semirings (NetworkX & SciPy.csgraph Oracles)"
description: "Establishes comparative differential verification tests pitting AlgebraX semiring shortest-path closures, graph Laplacians, Fiedler vectors, and Algebraic PageRank against NetworkX and SciPy csgraph reference implementations."
icon: lucide/network
status: draft
---

# EP-0182: Comparative Verification — Graph Calculus, Spectral Theory & Path Semirings (`NetworkX` &

`SciPy.csgraph` Oracles)

| Field             | Value                                                                                                              |
|:------------------|:-------------------------------------------------------------------------------------------------------------------|
| **EP**            | 0182                                                                                                               |
| **Title**         | Comparative Verification — Graph Calculus, Spectral Theory & Path Semirings (`NetworkX` & `SciPy.csgraph` Oracles) |
| **Author**        | Eran Rivlis & Antigravity (Council Agent)                                                                          |
| **Sponsor**       | The Council                                                                                                        |
| **Delegate**      | 🔬 Karl Popper (Falsifiability), ⚖️ Emmy Noether (Symmetry), ⚡ Claude Shannon (Efficiency) & 🧩 Bertrand Russell  |
| **Status**        | Draft                                                                                                              |
| **Type**          | Standards Track                                                                                                    |
| **Created**       | 2026-10-24                                                                                                         |
| **Updated**       | 2026-10-24                                                                                                         |
| **Replaces**      | None                                                                                                               |
| **Superseded-By** | None                                                                                                               |

---

## Abstract

This proposal specifies **Wave 1B** of the Phase 5 Mathematical Verification Track
([EP-0180](EP-0180-multi-layered-verification-suite.md)): a **Comparative Verification Suite** validating `algebrax`
graph analysis, spectral graph theory (`algebrax.analysis`), and optimization/logic path semirings
(`algebrax.semiring.optimization`, `algebrax.semiring.logic`) directly against **NetworkX** and **SciPy**
(`scipy.sparse.csgraph`, `scipy.linalg.eigh`). This suite proves that AlgebraX's flagship unifying abstraction—computing
graph algorithms via polymorphic semiring matrix multiplication and Kleene closure—yields the exact same results as
specialized combinatorial graph algorithms (Floyd–Warshall, Bellman–Ford, Dijkstra, Warshall transitive closure, and
power-iteration PageRank).

---

## Motivation

A central thesis of `algebrax` is **Baras & Theodorakopoulos's Path Algebra Isomorphism**: classical graph algorithms
are simply matrix multiplication and Kleene star closure $A^* = \bigoplus_{k=0}^{N-1} A^k$ over specialized semirings:

1. **Proving the Semiring-Graph Isomorphism in Practice:** Claiming that
   `ax.matrix.kleene_star(adj, semiring=TropicalSemiring())` computes all-pairs shortest paths is a bold mathematical
   statement. Pitting it against `scipy.sparse.csgraph.floyd_warshall` and `networkx.floyd_warshall_numpy` across random
   weighted directed graphs provides an irrefutable empirical proof of this isomorphism.
2. **Spectral Graph Theory Parity:** `algebrax.analysis` implements combinatorial, symmetric normalized
   ($L_{\text{sym}} = D^{-1/2} L D^{-1/2}$), and random-walk normalized ($L_{\text{rw}} = D^{-1} L$) graph Laplacians,
   Fiedler vector spectral bisection, algebraic connectivity ($\lambda_2$), and PageRank. Comparing these against
   `networkx.laplacian_matrix`, `networkx.normalized_laplacian_matrix`, `networkx.algebraic_connectivity`, and
   `networkx.pagerank` establishes immediate trust for network science users.
3. **Discrete Vector Calculus Identities:** Graph `gradient`, `divergence`, and `laplacian` operators must satisfy the
   fundamental adjoint identity $\operatorname{div} (\operatorname{grad} (f)) = L f$ and Green's integration-by-parts
   identity $\langle \operatorname{grad} f, F \rangle_E = \langle f, \operatorname{div} F \rangle_V$.

---

## Rationale

- **🔬 Falsifiability (Popper):** Tests randomized Erdős–Rényi, Barabási–Albert, disconnected, and DAG topologies via
  Hypothesis, ensuring disconnected components ($\infty$ in Tropical, `False` in Boolean) and self-loops are handled
  identically to `scipy.sparse.csgraph` and `networkx`.
- **⚖️ Symmetry (Noether):** Validates the fundamental duality between algebraic semiring closures and combinatorial
  path search across 5 distinct path dioids (`Tropical`, `Arctic`, `Boolean`, `Bottleneck`, `Viterbi`/`Reliability`).
- **⚡ Efficiency (Shannon):** Uses `scipy.sparse.csgraph` as a primary C-accelerated oracle alongside `networkx`,
  keeping test execution under $1.5\text{s}$.
- **🧩 Consistency (Russell):** Verifies that `algebrax.analysis.laplacian_matrix` and `algebrax.analysis.pagerank` agree
  across unnormalized, symmetric, and random-walk conventions.

---

## Specification

### 1. Target Modules & Comparative Verification Matrix

Tests are housed in `tests/verifications/test_differential_graphs.py`:

| AlgebraX Operation                             | Semiring / Mode                                 | Industry Reference Oracle                                                           | Mathematical Equivalence Checked                                                                |
|:-----------------------------------------------|:------------------------------------------------|:------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------|
| `matrix.kleene_star(W, TropicalSemiring())`    | $(\min, +, \infty, 0)$                          | `scipy.sparse.csgraph.floyd_warshall(W)` / `nx.floyd_warshall`                      | All-pairs shortest path distances $D_{ij}$ match exactly                                        |
| `matrix.kleene_star(A, BooleanSemiring())`     | $(\lor, \land, \text{False}, \text{True})$      | `nx.transitive_closure_dag` / `csgraph.floyd_warshall(unweighted=True) < inf`       | Reachability / transitive closure matrix parity                                                 |
| `matrix.kleene_star(W, ArcticSemiring())`      | $(\max, +, -\infty, 0)$                         | `nx.dag_longest_path_length` (on random DAGs)                                       | Critical-path / longest-path distances on DAGs                                                  |
| `matrix.kleene_star(C, BottleneckSemiring())`  | $(\max, \min, 0, \infty)$                       | Minimax widest-path reference via `csgraph.minimum_spanning_tree` / Dijkstra        | Maximum bottleneck capacity between all node pairs                                              |
| `matrix.kleene_star(P, ViterbiSemiring())`     | $(\max, \times, 0, 1)$                          | `csgraph.floyd_warshall(-np.log(P))` via $\exp(-D)$ log-isomorphism                 | Most probable path probabilities match $\exp(-\text{shortest}_{\log})$                          |
| `matrix.laplacian_matrix(W, normalized=None)`  | Combinatorial $L = D - W$                       | `nx.laplacian_matrix(G)` / `csgraph.laplacian(W, normed=False)`                     | Entrywise matrix equality ($10^{-12}$)                                                          |
| `matrix.laplacian_matrix(W, normalized='sym')` | Symmetric $I - D^{-1/2} W D^{-1/2}$             | `nx.normalized_laplacian_matrix(G)` / `csgraph.laplacian(W, normed=True)`           | Entrywise matrix equality ($10^{-11}$)                                                          |
| `analysis.laplacian_spectrum(W)`               | Eigenvalues $\lambda_1 \le \dots \le \lambda_n$ | `scipy.linalg.eigvalsh(L)`                                                          | Sorted Laplacian spectrum parity ($10^{-7}$)                                                    |
| `analysis.fiedler_vector(W)`                   | $\lambda_2$ & eigenvector $v_2$                 | `nx.algebraic_connectivity(G)` & `nx.fiedler_vector(G)`                             | $\lambda_2$ match & $\|v_{\text{ax}} \pm v_{\text{nx}}\|_2 \le 10^{-5}$ (on simple $\lambda_2$) |
| `analysis.pagerank(W, alpha=0.85)`             | Stationary distribution $\pi$                   | `nx.pagerank(G, alpha=0.85)` / left eigenvector of Google matrix                    | $\|\pi_{\text{ax}} - \pi_{\text{nx}}\|_1 \le 10^{-6}$ and $\sum \pi_i = 1$                      |
| `analysis.gradient` & `analysis.divergence`    | Discrete calculus on $G=(V,E)$                  | Incidence matrix $B$: $\nabla f = B f$, $\operatorname{div} F = B^T F$, $L = B^T B$ | $\operatorname{div}(\operatorname{grad}(f)) = L f$ and adjoint inner-product duality            |

### 2. Log-Domain Isomorphism Oracle for Viterbi / Reliability Semirings

Because `scipy.sparse.csgraph` does not natively provide a `Viterbi` (max-product) solver, the comparative test exploits
the exact **Logarithmic Semiring Isomorphism**:
$$\Phi: ([0, 1], \max, \times, 0, 1) \xrightarrow{p \mapsto -\ln p} ([0, \infty], \min, +, \infty, 0)$$
Computing `kleene_star` in `ViterbiSemiring` on edge probabilities $P_{uv} \in (0, 1]$ must
equal $\exp (-\text{floyd\_warshall} (-\ln P_{uv}))$ computed by `scipy.sparse.csgraph.floyd_warshall`.

---

## Backwards Compatibility

Purely additive verification test suite under `tests/verifications/test_differential_graphs.py`. Zero runtime impact on
`src/algebrax`.

---

## How to Teach This / Documentation Plan

1. Add the Semiring-to-Graph-Algorithm Equivalence Table to the documentation guide under `docs/guide/`.
2. Reference `test_differential_graphs.py` in `EP-0180` as the empirical verification of path algebras and spectral
   graph operators.

---

## Reference Implementation

- `tests/verifications/test_differential_graphs.py`

---

## Rejected Ideas

1. **Testing `ArcticSemiring` Kleene Star on Graphs with Positive Cycles:** Rejected because longest-path over positive
   cycles diverges to $+\infty$. Hypothesis generators for `ArcticSemiring` construct strictly upper-triangular
   adjacency matrices (guaranteed Directed Acyclic Graphs) so longest paths are finite and well-defined.

---

## Open Questions

None.

---

## Change Log

- **2026-10-24**: Initial draft created as Wave 1B of the Phase 5 Comparative Verification series.
