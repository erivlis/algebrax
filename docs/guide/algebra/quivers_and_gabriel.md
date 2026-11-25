---
title: Quiver Representations, Path Algebras & Gabriel's ADE Theorem
description: Quiver representations, path algebras KQ, Tits quadratic form, Gabriel's ADE classification, BGP reflections, and cellular sheaf bridges.
---

# Quiver Representations, Path Algebras & Gabriel's ADE Theorem

A **quiver** $Q = (V_Q, E_Q, s, t)$ is simply a directed multigraph: a set of vertices connected by directed arrows (parallel arrows and self-loops are both allowed). A **representation** of $Q$ assigns a vector space $V_i \cong K^{d_i}$ to every vertex $i \in V_Q$ and a linear map $M_\alpha : V_{s(\alpha)} \to V_{t(\alpha)}$ to every arrow $\alpha \in E_Q$.

This seemingly modest abstraction unifies matrix pencils ($\bullet \rightrightarrows \bullet$), persistence modules in topological data analysis ($A_n$), 1-dimensional cellular sheaves, and — via Pierre Gabriel's landmark 1972 theorem — the **simply-laced ADE Dynkin classification** of simple Lie algebras.

In AlgebraX, quiver representations, Gabriel's ADE classification, BGP/Weyl dimension reflections, and `CellularSheaf` bridges live in `algebrax.rep.quiver` (re-exported from `algebrax.rep`), while the associative unital path algebra $KQ$ lives in `algebrax.algebra.PathAlgebra` (`path_algebra`).

---

## 1. Quivers, Representations, Morphisms & Persistence Intervals

A single $m \times n$ matrix is a representation of the $A_2$ quiver $0 \to 1$. More generally, a persistence module along a filtration of length $n$ is a representation of the linear $A_n$ quiver $0 \to 1 \to \cdots \to n-1$, whose indecomposables are the **interval modules** $\mathbb{I}[b, d]$ (`interval_representation`).

A **morphism** $f : M \to N$ between representations of the same quiver is a family of vertex matrices $\{f_v : M_v \to N_v\}_{v \in V_Q}$ making every arrow square commute:

$$f_{t(\alpha)} \circ M_\alpha = N_\alpha \circ f_{s(\alpha)} \qquad \forall \alpha \in E_Q.$$

```python
from algebrax.rep import (
    QuiverRepresentation,
    direct_sum_quiver_rep,
    dynkin_quiver,
    interval_representation,
    simple_representation,
)
from algebrax.verification import (
    verify_quiver_direct_sum,
    verify_quiver_morphism_commutation,
)

# Linear A_3 quiver: 0 --e0--> 1 --e1--> 2
q_a3 = dynkin_quiver('A', 3)
assert q_a3.is_acyclic()
assert q_a3.num_vertices == 3
assert q_a3.num_edges == 2

# Indecomposable interval persistence modules on A_3
iv_02 = interval_representation(q_a3, [0, 1, 2])  # dim vector (1, 1, 1)
iv_11 = simple_representation(q_a3, 1)            # dim vector (0, 1, 0)
assert iv_02.dimension_vector == (1, 1, 1)
assert iv_11.dimension_vector == (0, 1, 0)

# Direct sum M = I[0, 2] (+) S_1 has dimension vector (1, 2, 1)
combined = direct_sum_quiver_rep(iv_02, iv_11)
assert combined.dimension_vector == (1, 2, 1)
assert all(verify_quiver_direct_sum(iv_02, iv_11, combined).values())

# Canonical projection morphism pi: I[0, 2] (+) S_1 -> I[0, 2]
proj = {
    0: {0: {0: 1.0}},
    1: {0: {0: 1.0}},
    2: {0: {0: 1.0}},
}
assert all(verify_quiver_morphism_commutation(combined, iv_02, proj).values())
```

---

## 2. Path Algebras $KQ$ & Module Action ($\mathbf{Rep}(Q) \simeq KQ\text{-}\mathbf{Mod}$)

Given any finite quiver $Q$, its **path algebra** $KQ$ (`PathAlgebra` / `path_algebra`) is the associative unital $K$-algebra spanned by all directed paths in $Q$:

- **Unboxed Basis Keys**: `(start_vertex, (e_1, ..., e_k))` where length-0 stationary paths `(v, ())` are the primitive orthogonal idempotents $e_v$.
- **Orthogonal Idempotents & Unit**:
  $$e_u \cdot e_v = \delta_{uv} e_v, \qquad \sum_{v \in V_Q} e_v = \mathbf{1}_{KQ}.$$
- **Path Concatenation**: $p \cdot q = pq$ when $\operatorname{target}(p) = \operatorname{source}(q)$ and $0$ otherwise. For cyclic quivers, passing `max_path_length=L` constructs the finite-dimensional quotient $KQ / J^{L+1}$.
- **Categorical Equivalence**: Evaluating elements of $KQ$ on any `QuiverRepresentation` via `kq.evaluate_in_rep(elem, rep)` embeds every path $p = \alpha_1 \cdots \alpha_k : u \to v$ as the block endomorphism $M_{\alpha_k} \cdots M_{\alpha_1}$ on $\bigoplus_{v \in V_Q} V_v$, satisfying the right-module law $\Phi(p \cdot q) = \Phi(q)\,\Phi(p)$.

```python
from fractions import Fraction
from algebrax.algebra import Algebra, PathAlgebra, Ring, path_algebra
from algebrax.matrix.core import dot
from algebrax.rep import QuiverRepresentation, cycle_quiver, dynkin_quiver
from algebrax.semiring import StandardSemiring
from algebrax.verification import verify_algebra_laws, verify_ring_laws

q = dynkin_quiver('A', 3)
qq = StandardSemiring(Fraction)
kq = path_algebra(q, coeff_semiring=qq)
assert isinstance(kq, PathAlgebra)
assert isinstance(kq, Ring)
assert isinstance(kq, Algebra)

e0, e1, e2 = (kq.vertex_idempotent(i) for i in range(3))
a0 = kq.arrow('e0')
a1 = kq.arrow('e1')
a01 = kq.path_element(('e0', 'e1'))

# Complete orthogonal idempotent decomposition of unity & non-commutative concatenation
assert kq.add(kq.add(e0, e1), e2) == kq.one
assert kq.mul(e0, e1) == kq.zero
assert kq.mul(a0, a1) == a01
assert kq.mul(a1, a0) == kq.zero

# Exact Ring & Algebra axioms over Q
samples = [kq.zero, kq.one, e0, a0, a1, a01]
assert all(verify_ring_laws(kq, samples).values())
assert all(verify_algebra_laws(kq, qq, [Fraction(0), Fraction(1), Fraction(-2)], samples).values())

# Evaluate KQ as endomorphisms on a concrete representation of A_3
kq_f = path_algebra(q)
rep = QuiverRepresentation(
    quiver=q,
    dimensions={0: 1, 1: 2, 2: 1},
    edge_maps={
        'e0': {0: {0: 2.0}, 1: {0: -1.0}},
        'e1': {0: {0: 3.0, 1: 4.0}},
    },
)
phi_a0 = kq_f.evaluate_in_rep(kq_f.arrow('e0'), rep)
phi_a1 = kq_f.evaluate_in_rep(kq_f.arrow('e1'), rep)
phi_a01 = kq_f.evaluate_in_rep(kq_f.path_element(('e0', 'e1')), rep)
# Left-to-right path multiplication acts as a right module: Phi(a0 * a1) = Phi(a1) @ Phi(a0)
assert phi_a01 == dot(phi_a1, phi_a0)

# Cyclic quiver path algebra truncated at length 2 (KQ / J^3)
kq_cycle = path_algebra(cycle_quiver(2), max_path_length=2)
c0, c1 = kq_cycle.arrow('e0'), kq_cycle.arrow('e1')
assert len(kq_cycle.basis()) == 6  # 2 vertices + 2 length-1 + 2 length-2 paths
assert kq_cycle.mul(kq_cycle.mul(c0, c1), c0) == kq_cycle.zero  # length 3 annihilated
```

---

## 3. Euler–Tits Form, Gabriel's ADE Theorem & BGP Reflections

For any dimension vector $\mathbf{d} = (d_i)_{i \in V_Q} \in \mathbb{Z}^{V_Q}$, the **Euler bilinear form** and **Tits quadratic form** are:

$$\langle \mathbf{d}, \mathbf{e} \rangle_Q = \sum_{i \in V_Q} d_i e_i - \sum_{\alpha \in E_Q} d_{s(\alpha)} e_{t(\alpha)}, \qquad q_Q(\mathbf{d}) = \langle \mathbf{d}, \mathbf{d} \rangle_Q = \frac{1}{2} \mathbf{d}^\top C_Q \mathbf{d},$$

where $C_Q = E_Q + E_Q^\top$ is the symmetric Cartan matrix of the underlying undirected graph of $Q$.

**Gabriel's Theorem (1972) & Tame–Wild Trichotomy** (`classify_representation_type`, `classify_dynkin_type`, `gabriel_positive_roots`):

| Tits Form $q_Q(\mathbf{d})$ | Underlying Undirected Graph | Representation Type | Indecomposables |
|:---|:---|:---|:---|
| **Positive definite** ($C_Q \succ 0$) | Disjoint union of ADE Dynkin diagrams ($A_n, D_n, E_6, E_7, E_8$) | `'finite'` | Finite; in exact 1-to-1 bijection with $\Phi^+$ (with $q_Q(\mathbf{d}) = 1$) |
| **Positive semidefinite** ($C_Q \succeq 0$, singular) | Contains Euclidean/affine diagrams ($\widetilde{A}_n, \widetilde{D}_n, \widetilde{E}_6, \widetilde{E}_7, \widetilde{E}_8$) | `'tame'` | Infinite; 1-parameter families plus radical vectors $\delta$ with $q_Q(\delta) = 0$ |
| **Indefinite** ($q_Q(\mathbf{d}) < 0$ for some $\mathbf{d}$) | All remaining graphs (e.g., 3-arrow Kronecker, 5-star) | `'wild'` | Contains the representation theory of every finitely generated algebra |

AlgebraX determines definiteness with **zero floating-point roundoff** via exact `fractions.Fraction` congruence diagonalization $U^\top C_Q U = D$, and bridges finite ADE quivers directly to `algebrax.lie.RootSystem` to enumerate $\Phi^+$ and apply **Bernstein–Gelfand–Ponomarev (BGP) / Weyl reflections** $s_v(\mathbf{d})$ (`bgp_reflect_dimension`) preserving $q_Q$.

```python
from algebrax.rep import (
    bgp_reflect_dimension,
    classify_dynkin_type,
    classify_representation_type,
    cycle_quiver,
    dynkin_quiver,
    euler_form,
    gabriel_positive_roots,
    kronecker_quiver,
    tits_quadratic_form,
)
from algebrax.verification import verify_tits_positive_definiteness

# 1. Finite ADE quivers: exact positive root counts |Phi^+|
expected_counts = {
    ('A', 4): ('A4', 10),
    ('D', 4): ('D4', 12),
    ('E6', None): ('E6', 36),
    ('E7', None): ('E7', 63),
    ('E8', None): ('E8', 120),
}
for (fam, rank), (label, n_roots) in expected_counts.items():
    q_ade = dynkin_quiver(fam, rank)
    assert classify_representation_type(q_ade) == 'finite'
    assert classify_dynkin_type(q_ade) == label
    roots = gabriel_positive_roots(q_ade)
    assert len(roots) == n_roots
    assert all(tits_quadratic_form(q_ade, r) == 1 for r in roots)

# Alternating vs linear orientation leaves q_Q and Gabriel's root bijection invariant
q_d4_alt = dynkin_quiver('D', 4, orientation='alternating')
assert classify_representation_type(q_d4_alt) == 'finite'
assert len(gabriel_positive_roots(q_d4_alt)) == 12
assert all(verify_tits_positive_definiteness(q_d4_alt).values())

# BGP / Weyl reflection at a sink/source preserves the Tits quadratic form
d_test = {0: 1, 1: 2, 2: 1, 3: 1}
d_reflected = bgp_reflect_dimension(q_d4_alt, d_test, vertex=1)
assert tits_quadratic_form(q_d4_alt, d_reflected) == tits_quadratic_form(q_d4_alt, d_test)

# 2. Tame Euclidean quivers: Kronecker (~A_1) and n-cycles (~A_{n-1}) have radical q_Q(delta) == 0
q_kron2 = kronecker_quiver(2)
assert classify_representation_type(q_kron2) == 'tame'
assert classify_dynkin_type(q_kron2) == '~A1'
assert tits_quadratic_form(q_kron2, {0: 1, 1: 1}) == 0

q_c4 = cycle_quiver(4)
assert classify_representation_type(q_c4) == 'tame'
assert classify_dynkin_type(q_c4) == '~A3'
assert euler_form(q_c4, [1, 1, 1, 1], [1, 1, 1, 1]) == 0

# 3. Wild quivers: 3-arrow Kronecker has q_Q(1, 1) = 1 + 1 - 3 = -1 < 0
q_kron3 = kronecker_quiver(3)
assert classify_representation_type(q_kron3) == 'wild'
assert tits_quadratic_form(q_kron3, {0: 1, 1: 1}) == -1
assert not verify_tits_positive_definiteness(q_kron3)['positive_definite']
```

---

## 4. Bidirectional `CellularSheaf` Equivalence

A representation of a simple, loop-free quiver $Q$ with positive vertex dimensions is canonically equivalent to a 1-dimensional `CellularSheaf` (`algebrax.topology.sheaf`) via `to_cellular_sheaf` and `from_cellular_sheaf`:

- For each arrow $\alpha : u \to v$, `to_cellular_sheaf(rep)` sets the edge stalk $\mathcal{F}(e) = V_v$ with restriction maps $\rho_{u \trianglelefteq e} = M_\alpha$ and $\rho_{v \trianglelefteq e} = \mathbf{I}_{d_v}$.
- The sheaf coboundary condition $(\delta_{\mathcal{F}} x)_e = x_v - M_\alpha x_u = 0$ means global sections $H^0(G; \mathcal{F}) = \ker \delta_{\mathcal{F}}$ are precisely the vectors compatible with all quiver arrows.
- Conversely, `from_cellular_sheaf(sheaf, mode='auto')` recovers a direct `QuiverRepresentation` whenever one endpoint restriction is the identity matrix (`mode='direct'`), or converts **any** general `CellularSheaf` into its canonical bipartite vertex-to-edge incidence quiver representation (`mode='incidence'`).

```python
from algebrax.rep import (
    QuiverRepresentation,
    dynkin_quiver,
    from_cellular_sheaf,
    to_cellular_sheaf,
)
from algebrax.topology import CellularSheaf

# 1. Direct round-trip between QuiverRepresentation and CellularSheaf
q = dynkin_quiver('A', 3)
rep = QuiverRepresentation(
    quiver=q,
    dimensions={0: 1, 1: 2, 2: 1},
    edge_maps={
        'e0': {0: {0: 2.0}, 1: {0: -1.0}},
        'e1': {0: {0: 1.0, 1: 3.0}},
    },
)
sheaf = to_cellular_sheaf(rep)
assert isinstance(sheaf, CellularSheaf)

# Compatible signal x0 = [1], x1 = [2, -1], x2 = [-1] is an exact global section
global_sec = {(0, 0): 1.0, (1, 0): 2.0, (1, 1): -1.0, (2, 0): -1.0}
assert sheaf.dirichlet_energy(global_sec) < 1e-12
assert sheaf.global_sections_dimension() == 1

recovered = from_cellular_sheaf(sheaf, mode='direct')
assert recovered.dimensions == rep.dimensions
assert recovered.quiver.num_edges == 2

# 2. Arbitrary general CellularSheaf -> bipartite incidence QuiverRepresentation
gen_sheaf = CellularSheaf()
gen_sheaf.add_vertex('u', dim=2)
gen_sheaf.add_vertex('v', dim=2)
gen_sheaf.add_edge(
    'u', 'v', dim=1,
    rho_u={0: {0: 1.0, 1: -1.0}},
    rho_v={0: {0: 2.0, 1: 1.0}},
)
inc_rep = from_cellular_sheaf(gen_sheaf, mode='incidence')
assert inc_rep.quiver.num_vertices == 3  # 2 original vertices + 1 edge vertex
assert inc_rep.quiver.num_edges == 2     # u -> e and v -> e
```

---

## 5. Automated Verification & Falsification

`algebrax.verification` exposes falsifiable verifiers for quiver invariants:

- **`verify_quiver_morphism_commutation(rep1, rep2, morphism_maps, tol=1e-9)`**: Checks vertex map presence, dimension compatibility, and square commutation $f_{t(\alpha)} \circ M_\alpha = N_\alpha \circ f_{s(\alpha)}$ across every edge $\alpha \in E_Q$.
- **`verify_quiver_direct_sum(rep1, rep2, direct_sum_rep, tol=1e-9)`**: Verifies dimension additivity and canonical inclusion/projection morphisms $\iota_k, \pi_k$ satisfying $\pi_k \iota_k = I$, $\pi_j \iota_k = 0$ ($j \ne k$), and $\iota_1 \pi_1 + \iota_2 \pi_2 = I$.
- **`verify_tits_positive_definiteness(quiver)`**: Performs exact rational congruence diagonalization on $C_Q = E_Q + E_Q^\top$ and confirms agreement between positive definiteness, `classify_representation_type(quiver) == 'finite'`, and $q_Q(\alpha) = 1$ on all Gabriel positive roots $\alpha \in \Phi^+$.

See also [Lie Algebras, Root Systems & BCH Dynamics](lie_algebras.md) for `RootSystem` and Dynkin diagrams, [Lie Algebra Representations, Weights & Clebsch–Gordan Tensors](lie_representations.md) for weight-space representations, [Quantum Groups, Yang–Baxter & Braids](quantum_groups_and_braids.md) for braided Hopf algebras, [Persistent Homology & Topological Barcodes](../topology/persistence.md) for $A_n$ persistence modules, and [Cellular Sheaves & Network Laplacians](../topology/sheaf.md) for higher-dimensional sheaf Laplacians and cohomology.
