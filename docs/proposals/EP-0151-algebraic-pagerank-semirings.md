---
title: "EP-0151: Algebraic PageRank & Semiring Random Walks with Restart"
description: "Formulates PageRank algebraically as the stationary distribution of random walks and resolvents over closed semirings."
icon: lucide/network
status: final
---

# EP-0151: Algebraic PageRank & Semiring Random Walks with Restart

| Field        | Value                                                       |
|:-------------|:------------------------------------------------------------|
| **EP**       | 0151                                                        |
| **Title**    | Algebraic PageRank & Semiring Random Walks with Restart     |
| **Author**   | Eran Rivlis                                                 |
| **Sponsor**  | The Council                                                 |
| **Delegate** | ⚖️ Emmy Noether (Symmetry) & ⚡ Claude Shannon (Efficiency) |
| **Status**   | Final                                                       |
| **Type**     | Standards Track                                             |
| **Created**  | 2026-09-05                                                  |
| **Updated**  | 2026-09-05                                                  |

---

## Abstract

This proposal introduces an algebraic formulation of the **PageRank** and **Random Walk with Restart (RWR)** algorithms
within AlgebraX. By casting the classical Google PageRank Markov chain into the language of semirings, linear algebraic
resolvents, and matrix Kleene stars, we unify:

1. **Classical PageRank** over the real field $(\mathbb{R}, +, \times)$ with dangling-node mass redistribution.
2. **Personalized PageRank (PPR)** / Topic-Sensitive Search driven by custom restart probability
   distributions $\mathbf{v}$.
3. **Tropical / Bottleneck Path Centrality** over idempotent dioids where teleportation acts as a penalty barrier.
4. **Log-Sum-Exp PageRank** over $\langle \mathbb{R} \cup \{-\infty\}, \oplus_{\log}, +, -\infty, 0 \rangle$ for
   numerically stable deep-walk inference.

The algorithm is implemented natively in `algebrax.analysis.pagerank`, leveraging sparse dictionary
representation, $O (|E|)$ memory, and complete interoperability with AlgebraX's `SparseMatrix`, `SparseVector`, and
`Semiring` protocols.

---

## Motivation

Graph centrality and path importance metrics are foundational to network analysis, recommendation engines, fraud
detection, and computational biology. Currently, AlgebraX features:

- `algebrax.probability.markov_steady_state`: Computes $\boldsymbol{\pi} = \boldsymbol{\pi} \mathbf{P}$ without damping,
  dead-end redistribution, or personalization vectors.
- `algebrax.matrix.academic.eigen_centrality`: Computes dominant
  eigenvector $\mathbf{M} \mathbf{v} = \lambda \mathbf{v}$ via unweighted column iteration, lacking restart dynamics.

Users currently cannot run:

1. **Personalized PageRank (PPR)** to compute local neighborhood relevance biased toward specific seed vertices.
2. **Weighted Transitions** with rigorous dead-end (dangling node) conservation of total probability mass.
3. **Semiring Random Walks** that combine edge weights and restart penalties using non-field algebras (such as Tropical
   shortest-path importance or Provenance lineage polynomials).

By formalizing PageRank as an algebraic contraction mapping and resolvent over semirings, AlgebraX fulfills its core
mission: treating sparse mappings as first-class mathematical entities governed by algebraic structures.

---

## Rationale & The Council Alignment

The design is evaluated against the 8 Pillars of The Council Framework:

### 1. Symmetry (Noether)

- **Mass Conservation:** The update rule strictly conserves total probability $\sum_{i} p_i = 1$ in stochastic semirings
  by uniformly or personally redistributing leaking mass from sink vertices (dangling nodes where out-degree is 0).
- **Dual Vector-Matrix Product:** State updates utilize the canonical vector-matrix product
  `vec_mat(p, P, semiring=sem)` preserving horizontal/vertical dualities.

### 2. Falsifiability (Popper)

- **Analytical Test Oracles:** The power iteration will be tested against closed-form analytical solutions on symmetric
  networks (e.g., 2-cycles, cliques, star graphs, disconnected components, self-loops).
- **Edge Cases:** Explicit verification for zero-edge graphs, complete graphs, single-node dangling sinks, and extreme
  damping boundaries ($\alpha \to 0$ and $\alpha \to 1$).

### 3. Efficiency (Shannon)

- **Sparse Teleportation:** The teleportation matrix $\mathbf{E} = \mathbf{e} \mathbf{v}^T$ is rank-1. We never
  construct a dense $N \times N$ matrix. Teleportation and dangling contributions are computed as $O (1)$ scalar
  aggregations and broadcast in $O (|V|)$, maintaining strict $O (|E| + |V|)$ time and space complexity per iteration.

### 4. Safety (The Golem)

- **Zero Division Protection:** Sinks with zero row sum ($\sum_j W_{ij} = 0$) are explicitly identified at
  initialization and handled without division by zero.
- **Immutability:** The input adjacency structure and personalization vectors are never mutated; a freshly allocated
  sparse vector dictionary is returned.

### 5. Clarity (Feynman)

- **The Freshman Test:** The algorithm is explained through the classic random surfer metaphor: at each step, the surfer
  follows a weighted link with probability $\alpha$, or teleports to a personalization node with
  probability $1 - \alpha$.
- **AMDS Compliance:** Conforms to the AlgebraX Mathematical Docstring Standard (AMDS) with full LaTeX signature and
  property blocks.

### 6. Consistency (Russell)

- Placed in `algebrax.analysis` alongside discrete graph operators (`laplacian`, `divergence`,
  `forman_ricci_curvature`), with cross-exports in `algebrax.probability`.

### 7. Harmony (The Steward)

- Default parameters match industry standards ($\alpha = 0.85$, $\text{tol} = 10^{-6}$, $\text{max\_iter} = 100$). Works
  seamlessly with plain Python dictionaries `dict[K, dict[K, float]]`.

### 8. Curiosity (The Explorer)

- Unlocks algebraic path provenance and min-plus tropical centrality where path traversal costs and restart barriers
  interact algebraically.

---

## Specification

### 1. Mathematical Formulation

Given a directed graph $G = (V, E)$ with edge weights $W_{ij} \ge 0$:

1. **Out-degree normalizer:** $d_i = \sum_{j} W_{ij}$.
2. **Transition Probability:**
   $$P_{ij} = \begin{cases} \frac{W_{ij}}{d_i} & \text{if } d_i > 0 \\ 0 & \text{if } d_i = 0 \text{ (dangling)} \end{cases}$$
3. **Personalization Vector:** $\mathbf{v} \in \mathbb{R}^{|V|}$ such that $\sum_{i} v_i = 1$ (default $v_i = 1/|V|$).
4. **Power Iteration Step:**
   At iteration $t$, let $m_{\text{dangling}}^{ (t)} = \sum_{i: d_i = 0} p_i^{ (t)}$ be the lost probability mass. The
   stationary distribution evolves as:
   $$\mathbf{p}^{ (t+1)} = \alpha \left (\mathbf{p}^{ (t)} \mathbf{P} + m_{\text{dangling}}^{ (t)} \mathbf{v} \right) + (1 - \alpha) \mathbf{v}$$

### 2. Semiring Resolvent Generalization

In a general semiring $\langle S, \oplus, \otimes, \mathbb{0}, \mathbb{1} \rangle$, the fixed point satisfies:
$$\mathbf{p} = (\alpha \otimes \mathbf{p} \mathbf{P}) \oplus ((1 - \alpha) \otimes \mathbf{v})$$
Which is formally the Neumann series / Kleene star solution:
$$\mathbf{p}^* = ((1 - \alpha) \otimes \mathbf{v}) \otimes (\alpha \otimes \mathbf{P})^*$$
where $\mathbf{M}^* = \bigoplus_{k=0}^\infty \mathbf{M}^k$.

### 3. Proposed Function Signature

```python
def pagerank(
        graph: SparseMatrix[K, V],
        damping: float = 0.85,
        personalization: SparseVector[K, float] | None = None,
        semiring: Semiring[V] | None = None,
        max_iter: int = 100,
        tol: float = 1e-6,
        dangling: SparseVector[K, float] | None = None,
) -> SparseVector[K, V]:
    r"""Compute algebraic PageRank / Random Walk with Restart over a semiring.

    Algebraic Signature:
        $\mathbf{p}^{(t+1)} = (\alpha \otimes \mathbf{p}^{(t)} \mathbf{P}) \oplus ((1 - \alpha) \otimes \mathbf{v})$

    Carrier:
        `SparseVector[K, V]` (Mapping from vertex identifier to centrality score).

    Operations:
        - Out-Degree Normalization: Row-stochastic projection $P_{ij} = W_{ij} / \sum_k W_{ik}$.
        - Dangling Mass Redistribution: Scalar aggregation of dead-end probability mass.
        - Power Iteration Contraction: Iterative sparse vector-matrix contraction.

    Properties:
        Conserves total mass ($\sum p_i = 1$) for stochastic semirings; geometrically convergent with rate $\alpha$.

    Applications:
        Web page ranking, entity resolution, protein-protein interaction networks,
        recommendation subgraphs, fraud detection.
    """
```

---

## Backwards Compatibility

- **Pure Addition:** Introduces new function `algebrax.analysis.pagerank`.
- **Existing Functions:** `algebrax.probability.markov_steady_state` and `algebrax.matrix.academic.eigen_centrality`
  remain unchanged and backward compatible.
- **Zero Breaking Changes:** Fully compatible with all existing semirings and sparse matrix representations.

---

## How to Teach This / Documentation Plan

1. **Guide Chapter:** Add PageRank and Random Walk with Restart subsection to `docs/guide/discrete/algebra.md` or
   `docs/guide/probability/information.md`.
2. **Interactive Laboratory:** Ensure View 3 in `recipes/lab.py` (PageRank Algorithm) connects seamlessly to the
   algebraic implementation.
3. **Recipe Demonstration:** Highlight topic-sensitive search and graph walk restart in
   `recipes/financial_risk_portfolio.py` or a dedicated network graph recipe.

---

## Reference Implementation

```python
def pagerank(
        graph: SparseMatrix[K, float],
        damping: float = 0.85,
        personalization: SparseVector[K, float] | None = None,
        semiring: Semiring[float] | None = None,
        max_iter: int = 100,
        tol: float = 1e-6,
        dangling: SparseVector[K, float] | None = None,
) -> SparseVector[K, float]:
    nodes = set(graph.keys()) | {dst for row in graph.values() for dst in row}
    if personalization:
        nodes |= set(personalization.keys())
    if not nodes:
        return {}

    n = len(nodes)
    p_vec = {k: 1.0 / n for k in nodes} if personalization is None else dict(personalization)
    p_sum = sum(p_vec.values())
    if p_sum > 0:
        p_vec = {k: v / p_sum for k, v in p_vec.items()}

    dangling_vec = p_vec if dangling is None else dict(dangling)

    # Normalize outgoing transition matrix
    trans_matrix: SparseMatrix[K, float] = {}
    dangling_nodes = set()
    for u in nodes:
        row = graph.get(u, {})
        row_sum = sum(row.values())
        if row_sum > 0:
            trans_matrix[u] = {v: w / row_sum for v, w in row.items()}
        else:
            dangling_nodes.add(u)

    # Power iteration
    rank = dict(p_vec)
    for _ in range(max_iter):
        dangling_mass = sum(rank[u] for u in dangling_nodes if u in rank)
        next_rank = vec_mat(rank, trans_matrix)

        # Teleportation + dangling mass injection
        teleport_coeff = (1.0 - damping) + damping * dangling_mass
        for u in nodes:
            next_rank[u] = next_rank.get(u, 0.0) * damping + teleport_coeff * p_vec.get(u, 0.0)

        # L1 convergence check
        err = sum(abs(next_rank.get(u, 0.0) - rank.get(u, 0.0)) for u in nodes)
        rank = next_rank
        if err < tol:
            break

    return rank
```

---

## Rejected Ideas

1. **Densifying the Google Matrix:**
    - *Proposal:* Build $\mathbf{G} = \alpha \mathbf{P} + (1 - \alpha) \frac{1}{N} \mathbf{J}$.
    - *Rejected:* Destroys sparsity, turning $O (|E|)$ memory and time into $O (|V|^2)$, making web-scale graphs
      impossible to process in pure Python.
2. **Overloading `markov_steady_state` with PageRank Flags:**
    - *Proposal:* Add `damping` and `restart` parameters directly to `markov_steady_state`.
    - *Rejected:* Violates Single Responsibility (Russell) and Principle of Harmony (Steward). Markov steady state
      operates on general ergodic chains $\boldsymbol{\pi} = \boldsymbol{\pi} \mathbf{P}$ without teleportation;
      PageRank specifically encodes random walks with restart.

---

## Open Questions

- [x] Should `dangling` default to the `personalization` vector? *(Yes, standard PageRank redistributes sink mass
  according to the personalization distribution).*
- [ ] Should we provide a closed-form Kleene star solver `pagerank_resolvent(..., method='star')` for exact
  fractional/symbolic semirings? *(Deferred to a future performance/symbolic track).*

---

## Change Log

* **2026-09-05:**
    * Initial Draft.
