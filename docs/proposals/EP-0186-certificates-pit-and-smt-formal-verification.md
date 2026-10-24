---
title: "EP-0186: Proof-Carrying Solver Certificates, Schwartz–Zippel PIT & SMT Formal Verification (Z3 Oracle)"
description: "Establishes universal O(nnz) proof-carrying solver certificates across all decompositions and linear/spectral solvers, high-degree Schwartz–Zippel polynomial identity tests (Cayley–Hamilton, exceptional Lie algebras), and automated SMT/Z3 formal proofs."
icon: lucide/award
status: draft
---

# EP-0186: Proof-Carrying Solver Certificates, Schwartz–Zippel PIT & SMT Formal Verification (`Z3` Oracle)

| Field             | Value                                                                                                          |
|:------------------|:---------------------------------------------------------------------------------------------------------------|
| **EP**            | 0186                                                                                                           |
| **Title**         | Proof-Carrying Solver Certificates, Schwartz–Zippel PIT & SMT Formal Verification (`Z3` Oracle)                |
| **Author**        | Eran Rivlis & Antigravity (Council Agent)                                                                      |
| **Sponsor**       | The Council                                                                                                    |
| **Delegate**      | 🛡️ The Golem (Safety), ⚡ Claude Shannon (Efficiency), 🔬 Karl Popper (Falsifiability) & 🧭 The Explorer       |
| **Status**        | Draft                                                                                                          |
| **Type**          | Standards Track                                                                                                |
| **Created**       | 2026-10-24                                                                                                     |
| **Updated**       | 2026-10-24                                                                                                     |
| **Replaces**      | None                                                                                                           |
| **Superseded-By** | None                                                                                                           |

---

## Abstract

This proposal specifies **Wave 2B** of the Phase 5 Mathematical Verification Track ([EP-0180](EP-0180-multi-layered-verification-suite.md)): the **Deductive & Certified Tier** of `tests/verifications/`. It unites three high-assurance formal verification techniques:
1. **Universal Proof-Carrying Solver Certificates (Layer 7):** Extending `test_certificates.py` so every $O(N^3)$ factorization (`lu`, `qr`, `svd`, `cholesky`), linear solver (`solve`, `cg_solve`), spectral solver (`fiedler_vector`, `pagerank`), and topological decomposition (`helmholtz_hodge_decomposition`) is verified by a fast $O(\text{nnz})$ algebraic witness checker.
2. **Expanded Schwartz–Zippel Randomized PIT (Layer 5):** Extending `test_pit_symbolic.py` to verify the **Cayley–Hamilton Theorem** ($p_A(A) = 0$), high-dimensional Lie Jacobi identities across all classical and exceptional families ($\mathfrak{su}_n, \mathfrak{sp}_n, \mathfrak{f}_4, \mathfrak{e}_6, \mathfrak{e}_7, \mathfrak{e}_8$), and multivariate polynomial ring identities in milliseconds with false-positive probability $\le 10^{-16}$.
3. **Automated SMT / Z3 Formal Verification (Layer 8):** Using `z3-solver` to symbolically prove that AlgebraX's semiring, dioid, and lattice equations hold universally over unbounded reals, integers, and bit-vectors (`s.check(Not(Axiom)) == unsat`).

---

## Motivation

1. **Asymmetric Verification Complexity ($O(N^3)$ Solve vs $O(\text{nnz})$ Check):** Computing an SVD, LU factorization, or Helmholtz–Hodge decomposition is an iterative or cubic-time operation, but verifying that a returned tuple $(L, U, P)$ satisfies $P A = L U$ with $L$ unit lower-triangular and $U$ upper-triangular takes linear $O(\text{nnz})$ time and requires **zero external libraries**. Universal certificate checkers turn every solver output into a self-verifying mathematical proof.
2. **Defeating Monomial Blowup in High-Degree Identities:** Testing the Cayley–Hamilton theorem $p_A(A) = \mathbf{0}$ or verifying Jacobi identities on 52-dimensional $\mathfrak{f}_4$ or 78-dimensional $\mathfrak{e}_6$ via symbolic expansion triggers combinatorial explosion. Schwartz–Zippel PIT verifies these identities in milliseconds over exact rationals or bounded integer floats.
3. **Unbounded Deductive Proofs via SMT (`Z3`):** Empirical testing (even with Hypothesis) samples finitely many points. By encoding tropical $(\min, +)$, arctic $(\max, +)$, Łukasiewicz, bottleneck, and Boolean semiring operations into `z3-solver` ASTs and proving `Not(Law)` is `unsat`, we elevate verification from empirical falsification to **deductive mathematical proof**.

---

## Rationale

- **🛡️ Safety (The Golem):** Proof-carrying certificates guarantee that no solver can return an unconverged, non-orthogonal, or structurally invalid factorization without immediate detection.
- **⚡ Efficiency (Shannon):** Replaces $O(2^N)$ symbolic expansion with $O(N)$ randomized PIT evaluations and $O(\text{nnz})$ witness verification.
- **🔬 Falsifiability & Deductive Rigor (Popper & Russell):** If an algebraic law is violated anywhere in $\mathbb{R}^3$ or $\mathbb{Z}^3$, Z3 synthesizes an explicit counterexample model `s.model()`; if `unsat` is returned, the law holds universally.
- **🧭 Curiosity (The Explorer):** Bridges pure-Python scientific computing with formal methods (SMT solvers).

---

## Specification

### 1. Verification Matrix

Tests reside in `tests/verifications/test_certificates.py`, `tests/verifications/test_pit_symbolic.py`, and `tests/verifications/test_smt_z3_proofs.py`:

| Layer | Target Function / Structure | Certificate / Identity / SMT Proof Checked | Complexity / Guarantee |
|:---|:---|:---|:---|
| **L7 Certificates** | `matrix.decompose.lu(A)` | Witness: $\|P A - L U\|_\infty \le \epsilon$, $L_{ii}=1, L_{ij}=0 (j>i)$, $U_{ij}=0 (i>j)$ | $O(\text{nnz})$ deterministic check |
| **L7 Certificates** | `matrix.decompose.qr(A)` | Witness: $\|A - Q R\|_\infty \le \epsilon$, $\|Q^T Q - I\|_\infty \le \epsilon$, $R_{ij}=0 (i>j)$ | $O(N^2)$ orthogonality witness |
| **L7 Certificates** | `matrix.decompose.cholesky(A)` | Witness: $\|A - L L^T\|_\infty \le \epsilon$, $L_{ii} > 0$, $L_{ij}=0 (j>i)$ | $O(\text{nnz})$ deterministic check |
| **L7 Certificates** | `matrix.decompose.svd(A)` | Witness: $\|A - U \Sigma V^T\|_\infty \le \epsilon$, $\|U^T U - I\| \le \epsilon$, $\|V^T V - I\| \le \epsilon$, $\sigma_1 \ge \sigma_2 \ge 0$ | $O(N^2)$ singular witness |
| **L7 Certificates** | `matrix.solve` & `cg_solve` | Residual witness: $\|A x - b\|_\infty / \|b\|_\infty \le \epsilon$ | $O(\text{nnz})$ linear check |
| **L7 Certificates** | `analysis.pagerank` & `fiedler_vector` | Eigenpair witness: $\|P^T \pi - \pi\|_1 \le \epsilon$ and $\|L v_2 - \lambda_2 v_2\|_2 \le \epsilon, \langle v_2, \mathbf{1} \rangle = 0$ | $O(|E|)$ linear check |
| **L7 Certificates** | `homology.helmholtz_hodge_decomposition` | Witness: $\omega = d\alpha + \delta\beta + \gamma$, mutual $L^2$ orthogonality, $d(d\alpha)=0$, $\delta(\delta\beta)=0$ | $O(|E|)$ linear check |
| **L5 PIT** | Cayley–Hamilton Theorem | $p_A(A) = \sum_{k=0}^n c_k A^k = \mathbf{0}$ over exact `Fraction` matrices | Error $\le (n/|S|)^k = 0$ over $\mathbb{Q}$ |
| **L5 PIT** | Classical & Exceptional Lie Algebras | Jacobi identity & Adjoint homomorphism $[\operatorname{ad}_X, \operatorname{ad}_Y] = \operatorname{ad}_{[X,Y]}$ on $\mathfrak{so}_n, \mathfrak{su}_n, \mathfrak{sp}_n, \mathfrak{g}_2, \mathfrak{f}_4$ | Error $\le 10^{-16}$ |
| **L8 SMT (Z3)** | `Tropical`, `Arctic`, `Bottleneck`, `Lukasiewicz`, `Boolean` | Symbolic Z3 proof of Associativity, Commutativity, Distributivity, Identity, Annihilation, and Idempotence | **`unsat` (Universal Proof over $\mathbb{R}$ / $\mathbb{B}$)** |

---

## Backwards Compatibility

Purely additive verification test modules under `tests/verifications/`. `z3-solver` is guarded by `@pytest.mark.formal_smt` and `pytest.importorskip("z3")` so environments without Z3 skip cleanly without failure.

---

## How to Teach This / Documentation Plan

1. Document the Certificate Pattern ($O(N^3)$ solve, $O(\text{nnz})$ check) in `docs/proposals/EP-0180-multi-layered-verification-suite.md`.
2. Add instructions for running Z3 formal proofs (`uv run pytest tests/verifications/ -m formal_smt`).

---

## Reference Implementation

- `tests/verifications/test_certificates.py`
- `tests/verifications/test_pit_symbolic.py`
- `tests/verifications/test_smt_z3_proofs.py`

---

## Rejected Ideas

1. **Embedding Runtime Certificate Checks Inside Hot Loops by Default:** Rejected per Shannon's Efficiency pillar—checking $Q^T Q = I$ on every internal call would add overhead in production. Keeping universal certificate verifiers in `tests/verifications/test_certificates.py` (and optional debug assertions) gives 100% test assurance with zero runtime overhead.

---

## Open Questions

None.

---

## Change Log

- **2026-10-24**: Initial draft created as Wave 2B of the Phase 5 Mathematical Verification Track.
