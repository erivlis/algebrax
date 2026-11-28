# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Runnable AlgebraX prototype across all 5 regions of the Lattice & Order Continent (EXP-0013).

Regions demonstrated and benchmarked with zero external dependencies:
  Region I   - FinitePoset, FiniteLattice, Hasse covers, Rota Zeta/Mobius, Birkhoff M3/N5
               constructive witnesses, Birkhoff duality L ~= O(J(L)), Dedekind-MacNeille
               completion, SubgroupLattice(S_3, A_4, D_4), PartitionLattice, SubspaceLattice(F_2^3)
  Region II  - GaloisConnection, Tarski fixed-point lattice, Formal Concept Analysis (NextClosure)
               and Duquenne-Guigues canonical implication basis
  Region III - HeytingAlgebra / Alexandroff Locale (double-negation skeleton), Lukasiewicz MVAlgebra,
               OrthomodularLattice (O_6 falsification witness vs. MO_2 spin-1/2 quantum logic)
  Region IV  - Graphic & Linear Matroids, Geometric Flat Lattice, Characteristic Polynomial
               via Rota Mobius function (K_4 chromatic match), Tutte Polynomial (Cayley trees)
  Region V   - FiniteQuantale bridge (EXP-0012) & Live AlgebraX Protocol Audit

Run via:
    uv run python playground/lattice_continent_prototype.py
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from algebrax.algebra import (
    BooleanAlgebra,
    BoundedLattice,
    DistributiveLattice,
    Lattice,
    ModularField,
)
from algebrax.group import alternating_group, dihedral_group, symmetric_group
from algebrax.semiring.logic import LukasiewiczSemiring

T = TypeVar('T')
U = TypeVar('U')


# =============================================================================
# Region I: FinitePoset, FiniteLattice, Rota Mobius, Birkhoff & MacNeille
# =============================================================================


class FinitePoset(Generic[T]):
    r"""Finite partially ordered set $(P, \le)$ with bitmask-accelerated order queries.

    Algebraic Signature:
        $\langle P, \le \rangle$ (reflexive, antisymmetric, transitive)

    Carrier:
        Arbitrary finite hashable elements `T` indexed into integers $\{0, \dots, n-1\}$.

    Operations:
        - `leq(a, b)`: $O(1)$ bitmask order test.
        - `covers()`: Hasse diagram cover edges (transitive reduction).
        - `order_ideals()`: Distributive lattice $\mathcal{O}(P)$ of down-sets.
        - `mobius_matrix()`: Exact Rota Mobius function $\mu(x, y)$ in the incidence algebra.
        - `zeta_transform(f)` / `mobius_transform(f)`: Exact incidence transforms.

    Properties:
        Reflexive, Antisymmetric, Transitive.

    Applications:
        Hasse diagrams, Rota combinatorics (EP-0231), Birkhoff duality, Alexandroff topologies.
    """

    def __init__(self, elements: Sequence[T], leq_masks: list[int]) -> None:
        self.elements: tuple[T, ...] = tuple(elements)
        self._index: dict[T, int] = {e: i for i, e in enumerate(self.elements)}
        self._n: int = len(self.elements)
        # leq_masks[i] has bit j set iff elements[i] <= elements[j]
        self._up_masks: list[int] = list(leq_masks)
        self._down_masks: list[int] = [0] * self._n
        for i in range(self._n):
            mask = self._up_masks[i]
            for j in range(self._n):
                if (mask >> j) & 1:
                    self._down_masks[j] |= 1 << i

    @classmethod
    def from_leq(cls, elements: Iterable[T], leq_fn: Callable[[T, T], bool]) -> FinitePoset[T]:
        """Construct a FinitePoset directly from an order predicate."""
        elems = list(elements)
        n = len(elems)
        masks = [0] * n
        for i in range(n):
            m = 0
            for j in range(n):
                if leq_fn(elems[i], elems[j]):
                    m |= 1 << j
            masks[i] = m
        return cls(elems, masks)

    @classmethod
    def from_covers(cls, elements: Iterable[T], cover_edges: Iterable[tuple[T, T]]) -> FinitePoset[T]:
        """Construct a FinitePoset from cover edges (u < v) via reflexive-transitive closure."""
        elems = list(elements)
        idx = {e: i for i, e in enumerate(elems)}
        n = len(elems)
        masks = [1 << i for i in range(n)]
        for u, v in cover_edges:
            masks[idx[u]] |= 1 << idx[v]
        # Warshall transitive closure over bitmasks
        for k in range(n):
            bit_k = 1 << k
            for i in range(n):
                if masks[i] & bit_k:
                    masks[i] |= masks[k]
        return cls(elems, masks)

    def __len__(self) -> int:
        return self._n

    def leq(self, a: T, b: T) -> bool:
        return bool((self._up_masks[self._index[a]] >> self._index[b]) & 1)

    def lt(self, a: T, b: T) -> bool:
        return a != b and self.leq(a, b)

    def up_set(self, a: T) -> frozenset[T]:
        m = self._up_masks[self._index[a]]
        return frozenset(self.elements[j] for j in range(self._n) if (m >> j) & 1)

    def down_set(self, a: T) -> frozenset[T]:
        m = self._down_masks[self._index[a]]
        return frozenset(self.elements[j] for j in range(self._n) if (m >> j) & 1)

    def covers(self) -> list[tuple[T, T]]:
        """Return Hasse diagram cover edges (a, b) where a < b and no c has a < c < b."""
        edges: list[tuple[T, T]] = []
        for i in range(self._n):
            strict_up = self._up_masks[i] & ~(1 << i)
            for j in range(self._n):
                if (strict_up >> j) & 1:
                    strict_down_j = self._down_masks[j] & ~(1 << j)
                    if (strict_up & strict_down_j) == 0:
                        edges.append((self.elements[i], self.elements[j]))
        return edges

    def linear_extension_indices(self) -> list[int]:
        """Return topological ordering of element indices compatible with <=."""
        indeg = [0] * self._n
        adj: list[list[int]] = [[] for _ in range(self._n)]
        for i in range(self._n):
            m = self._up_masks[i] & ~(1 << i)
            for j in range(self._n):
                if (m >> j) & 1:
                    adj[i].append(j)
                    indeg[j] += 1
        q = deque(i for i in range(self._n) if indeg[i] == 0)
        order: list[int] = []
        while q:
            u = q.popleft()
            order.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        return order

    def order_ideals(self) -> list[frozenset[T]]:
        """Enumerate all down-sets (order ideals) O(P) of the poset."""
        ideals_masks: set[int] = {0}
        queue: deque[int] = deque([0])
        while queue:
            cur = queue.popleft()
            for i in range(self._n):
                if not ((cur >> i) & 1):
                    # Can add i iff all strict predecessors of i are already in cur
                    strict_down = self._down_masks[i] & ~(1 << i)
                    if (strict_down & cur) == strict_down:
                        nxt = cur | (1 << i)
                        if nxt not in ideals_masks:
                            ideals_masks.add(nxt)
                            queue.append(nxt)
        return [
            frozenset(self.elements[i] for i in range(self._n) if (mask >> i) & 1)
            for mask in sorted(ideals_masks)
        ]

    def mobius_matrix(self) -> dict[tuple[T, T], int]:
        """Compute exact Rota Mobius function mu(x, y) for all x <= y."""
        topo = self.linear_extension_indices()
        mu: dict[tuple[int, int], int] = {}
        for pos_i, i in enumerate(topo):
            mu[(i, i)] = 1
            for j in topo[pos_i + 1 :]:
                if (self._up_masks[i] >> j) & 1:
                    interval_mask = self._up_masks[i] & self._down_masks[j] & ~(1 << j)
                    total = 0
                    for k in topo[pos_i:]:
                        if (interval_mask >> k) & 1:
                            total += mu[(i, k)]
                    mu[(i, j)] = -total
        return {(self.elements[i], self.elements[j]): val for (i, j), val in mu.items() if val != 0}

    def zeta_transform(self, f: dict[T, int]) -> dict[T, int]:
        """Downward Zeta transform: F(y) = sum_{x <= y} f(x)."""
        out: dict[T, int] = {}
        for j, y in enumerate(self.elements):
            m = self._down_masks[j]
            out[y] = sum(f.get(self.elements[i], 0) for i in range(self._n) if (m >> i) & 1)
        return out

    def mobius_transform(self, big_f: dict[T, int]) -> dict[T, int]:
        """Exact Mobius inversion recovering f(y) = sum_{x <= y} mu(x, y) * F(x)."""
        mu = self.mobius_matrix()
        out: dict[T, int] = {}
        for y in self.elements:
            val = sum(coeff * big_f.get(x, 0) for (x, target), coeff in mu.items() if target == y)
            if val != 0:
                out[y] = val
        return out


class FiniteLattice(FinitePoset[T], BoundedLattice[T]):
    r"""Concrete finite bounded lattice with constructive Birkhoff M3/N5 witness certificates.

    Algebraic Signature:
        $\langle L, \vee, \wedge, \bot, \top \rangle$

    Carrier:
        Arbitrary finite hashable elements `T`.

    Operations:
        - `join(a, b)`: Least upper bound $a \vee b$.
        - `meet(a, b)`: Greatest lower bound $a \wedge b$.
        - `bot` / `top`: Global bounds $\bot, \top$.
        - `find_n5_witness()` / `find_m3_witness()`: Constructive Birkhoff non-modularity /
          non-distributivity sublattice witnesses.

    Properties:
        Bounded Lattice; dynamically verifiable for Modularity, Distributivity, Semimodularity,
        Atomicity, and Complementedness.

    Applications:
        Subgroup lattices, partition lattices, subspace geometries, concept lattices, Heyting locales.
    """

    def __init__(self, elements: Sequence[T], leq_masks: list[int]) -> None:
        super().__init__(elements, leq_masks)
        all_mask = (1 << self._n) - 1
        self._join_idx: list[list[int]] = [[0] * self._n for _ in range(self._n)]
        self._meet_idx: list[list[int]] = [[0] * self._n for _ in range(self._n)]

        # Precompute bitcount-sorted candidates for exact lub/glb lookup
        for i in range(self._n):
            for j in range(self._n):
                ubs = self._up_masks[i] & self._up_masks[j]
                lbs = self._down_masks[i] & self._down_masks[j]
                lub = self._least_in_mask(ubs)
                glb = self._greatest_in_mask(lbs)
                if lub is None or glb is None:
                    msg = f'Poset is not a lattice: pair ({self.elements[i]}, {self.elements[j]}) lacks lub/glb.'
                    raise ValueError(msg)
                self._join_idx[i][j] = lub
                self._meet_idx[i][j] = glb

        bot_idx = self._least_in_mask(all_mask)
        top_idx = self._greatest_in_mask(all_mask)
        if bot_idx is None or top_idx is None:
            raise ValueError('Finite lattice must have unique bot and top.')
        self._bot_idx = bot_idx
        self._top_idx = top_idx

    def _least_in_mask(self, mask: int) -> int | None:
        for k in range(self._n):
            if ((mask >> k) & 1) and ((self._up_masks[k] & mask) == mask):
                return k
        return None

    def _greatest_in_mask(self, mask: int) -> int | None:
        for k in range(self._n):
            if ((mask >> k) & 1) and ((self._down_masks[k] & mask) == mask):
                return k
        return None

    @classmethod
    def from_poset(cls, poset: FinitePoset[T]) -> FiniteLattice[T]:
        return cls(poset.elements, poset._up_masks)

    @property
    def bot(self) -> T:
        return self.elements[self._bot_idx]

    @property
    def top(self) -> T:
        return self.elements[self._top_idx]

    def join(self, a: T, b: T) -> T:
        return self.elements[self._join_idx[self._index[a]][self._index[b]]]

    def meet(self, a: T, b: T) -> T:
        return self.elements[self._meet_idx[self._index[a]][self._index[b]]]

    def join_all(self, xs: Iterable[T]) -> T:
        acc = self._bot_idx
        for x in xs:
            acc = self._join_idx[acc][self._index[x]]
        return self.elements[acc]

    def meet_all(self, xs: Iterable[T]) -> T:
        acc = self._top_idx
        for x in xs:
            acc = self._meet_idx[acc][self._index[x]]
        return self.elements[acc]

    def join_irreducibles(self) -> list[T]:
        """Return J(L): elements covering exactly one element in the Hasse diagram."""
        lower_cover_count = [0] * self._n
        for u, v in self.covers():
            lower_cover_count[self._index[v]] += 1
        return [self.elements[i] for i in range(self._n) if lower_cover_count[i] == 1]

    def atoms(self) -> list[T]:
        """Return atoms (elements directly covering bot)."""
        return [v for u, v in self.covers() if u == self.bot]

    def find_n5_witness(self) -> tuple[T, T, T, T, T] | None:
        """Constructive Birkhoff N5 pentagon finder (o, a, c, b, i) with a < c, a v b = i, c ^ b = o."""
        n = self._n
        jm, mm = self._join_idx, self._meet_idx
        for a in range(n):
            strict_up_a = self._up_masks[a] & ~(1 << a)
            for c in range(n):
                if not ((strict_up_a >> c) & 1):
                    continue
                for b in range(n):
                    # Modular law failure: a < c and a v (b ^ c) != (a v b) ^ c
                    if jm[a][mm[b][c]] != mm[jm[a][b]][c]:
                        o = mm[b][c]
                        i = jm[a][b]
                        # Canonical pentagon elements: o < a_p < c_p < i and o < b < i
                        a_p = jm[a][o]
                        c_p = mm[c][i]
                        return (
                            self.elements[o],
                            self.elements[a_p],
                            self.elements[c_p],
                            self.elements[b],
                            self.elements[i],
                        )
        return None

    def find_m3_witness(self) -> tuple[T, T, T, T, T] | None:
        """Constructive Birkhoff M3 diamond finder (o, x, y, z, i) for modular non-distributive lattices."""
        n = self._n
        jm, mm = self._join_idx, self._meet_idx
        for x in range(n):
            for y in range(x + 1, n):
                for z in range(y + 1, n):
                    # Check if x, y, z form an antichain with pairwise same join i and same meet o
                    i = jm[x][y]
                    o = mm[x][y]
                    if (
                        i == jm[y][z] == jm[x][z]
                        and o == mm[y][z] == mm[x][z]
                        and len({o, x, y, z, i}) == 5
                    ):
                        return (
                            self.elements[o],
                            self.elements[x],
                            self.elements[y],
                            self.elements[z],
                            self.elements[i],
                        )
        return None

    def is_modular(self) -> bool:
        return self.find_n5_witness() is None

    def is_distributive(self) -> bool:
        return self.find_n5_witness() is None and self.find_m3_witness() is None

    def is_atomistic(self) -> bool:
        """Every element is a join of atoms."""
        atom_list = self.atoms()
        for x in self.elements:
            below = [a for a in atom_list if self.leq(a, x)]
            if self.join_all(below) != x:
                return False
        return True

    def ranks(self) -> dict[T, int] | None:
        """Return rank function if the lattice is graded (all maximal chains have same length)."""
        covers = self.covers()
        adj: dict[T, list[T]] = {e: [] for e in self.elements}
        for u, v in covers:
            adj[u].append(v)
        r: dict[T, int] = {self.bot: 0}
        q: deque[T] = deque([self.bot])
        while q:
            u = q.popleft()
            for v in adj[u]:
                cand = r[u] + 1
                if v in r and r[v] != cand:
                    return None
                if v not in r:
                    r[v] = cand
                    q.append(v)
        return r

    def is_upper_semimodular(self) -> bool:
        """Check Birkhoff upper semimodularity: graded with r(x) + r(y) >= r(x v y) + r(x ^ y)."""
        r = self.ranks()
        if r is None:
            return False
        for x in self.elements:
            for y in self.elements:
                if r[x] + r[y] < r[self.join(x, y)] + r[self.meet(x, y)]:
                    return False
        return True

    def is_geometric(self) -> bool:
        """A finite lattice is geometric iff it is atomistic and upper semimodular."""
        return self.is_atomistic() and self.is_upper_semimodular()

    def birkhoff_dual(self) -> tuple[FinitePoset[T], FiniteLattice[frozenset[T]]]:
        """Compute J(L) and O(J(L)), verifying Birkhoff's Representation Theorem L ~= O(J(L))."""
        j_elems = self.join_irreducibles()
        j_poset = FinitePoset.from_leq(j_elems, self.leq)
        ideals = j_poset.order_ideals()
        ideal_lat = FiniteLattice.from_poset(FinitePoset.from_leq(ideals, lambda a, b: a <= b))
        return j_poset, ideal_lat


def dedekind_macneille(poset: FinitePoset[T]) -> FiniteLattice[frozenset[T]]:
    """Compute the minimal complete lattice completion DM(P) of any finite poset P."""
    n = len(poset)
    all_mask = (1 << n) - 1

    def upper_bounds(mask: int) -> int:
        res = all_mask
        for i in range(n):
            if (mask >> i) & 1:
                res &= poset._up_masks[i]
        return res

    def lower_bounds(mask: int) -> int:
        res = all_mask
        for i in range(n):
            if (mask >> i) & 1:
                res &= poset._down_masks[i]
        return res

    # Closure operator c(A) = (A^u)^l
    closed_masks: set[int] = set()
    # Generate from cuts of singletons and intersections (exact for small/medium posets)
    frontier: deque[int] = deque([lower_bounds(upper_bounds(0))])
    for i in range(n):
        frontier.append(lower_bounds(upper_bounds(1 << i)))
    while frontier:
        cur = frontier.popleft()
        if cur in closed_masks:
            continue
        closed_masks.add(cur)
        for i in range(n):
            if not ((cur >> i) & 1):
                nxt = lower_bounds(upper_bounds(cur | (1 << i)))
                if nxt not in closed_masks:
                    frontier.append(nxt)
    cuts = [frozenset(poset.elements[i] for i in range(n) if (m >> i) & 1) for m in sorted(closed_masks)]
    return FiniteLattice.from_poset(FinitePoset.from_leq(cuts, lambda a, b: a <= b))


# --- Canonical Lattice Factories ---


def divisor_lattice(n: int) -> FiniteLattice[int]:
    """Divisibility lattice D_n (always distributive!)."""
    divs = [d for d in range(1, n + 1) if n % d == 0]
    return FiniteLattice.from_poset(FinitePoset.from_leq(divs, lambda a, b: b % a == 0))


def partition_lattice(n: int) -> FiniteLattice[frozenset[frozenset[int]]]:
    """Set partition lattice Pi_n (ordered by refinement; always geometric!)."""

    def _gen_parts(items: list[int]) -> list[list[list[int]]]:
        if not items:
            return [[]]
        first, rest = items[0], items[1:]
        out: list[list[list[int]]] = []
        for sub in _gen_parts(rest):
            out.append([[first], *sub])
            for idx in range(len(sub)):
                nxt = [list(b) for b in sub]
                nxt[idx] = [first, *nxt[idx]]
                out.append(nxt)
        return out

    parts = [frozenset(frozenset(b) for b in p) for p in _gen_parts(list(range(n)))]

    def refines(p: frozenset[frozenset[int]], q: frozenset[frozenset[int]]) -> bool:
        return all(any(bp <= bq for bq in q) for bp in p)

    return FiniteLattice.from_poset(FinitePoset.from_leq(parts, refines))


def subgroup_lattice(group: Any) -> FiniteLattice[frozenset[Any]]:
    """Compute the subgroup lattice Sub(G) directly from an algebrax.group.FiniteGroup."""
    elems = list(group.elements)
    subgroups: set[frozenset[Any]] = {frozenset({group.one})}
    queue: deque[frozenset[Any]] = deque(subgroups)
    while queue:
        sub = queue.popleft()
        for g in elems:
            if g not in sub:
                gen = frozenset(group.subgroup([*sub, g], generate=True).elements)
                if gen not in subgroups:
                    subgroups.add(gen)
                    queue.append(gen)
    return FiniteLattice.from_poset(FinitePoset.from_leq(sorted(subgroups, key=len), lambda a, b: a <= b))


def subspace_lattice_fq(dim: int, p: int) -> FiniteLattice[frozenset[tuple[int, ...]]]:
    """Compute projective subspace lattice Sub(F_p^dim) over algebrax.algebra.ModularField(p)."""
    field = ModularField(p)

    def vec_add(u: tuple[int, ...], v: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(field.add(a, b) for a, b in zip(u, v, strict=True))

    def vec_smul(c: int, u: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(field.mul(c, a) for a in u)

    def span(vecs: Iterable[tuple[int, ...]]) -> frozenset[tuple[int, ...]]:
        zero = (0,) * dim
        cur: set[tuple[int, ...]] = {zero}
        for v in vecs:
            nxt = set(cur)
            for u in cur:
                for c in range(1, p):
                    nxt.add(vec_add(u, vec_smul(c, v)))
            cur = nxt
        return frozenset(cur)

    # Generate all vectors in F_p^dim
    all_vecs: list[tuple[int, ...]] = [()]
    for _ in range(dim):
        all_vecs = [(*v, c) for v in all_vecs for c in range(p)]

    zero_sub = frozenset({(0,) * dim})
    subs: set[frozenset[tuple[int, ...]]] = {zero_sub}
    q: deque[frozenset[tuple[int, ...]]] = deque([zero_sub])
    while q:
        s = q.popleft()
        for v in all_vecs:
            if v not in s:
                nxt = span([*s, v])
                if nxt not in subs:
                    subs.add(nxt)
                    q.append(nxt)
    return FiniteLattice.from_poset(FinitePoset.from_leq(sorted(subs, key=len), lambda a, b: a <= b))


# =============================================================================
# Region II: Galois Connections, Tarski Fixed Points & Formal Concept Analysis
# =============================================================================


@dataclass(frozen=True)
class GaloisConnection(Generic[T, U]):
    """Order-preserving Galois connection f -| g: f(p) <=_Q q <=> p <=_P g(q)."""

    poset_p: FinitePoset[T]
    poset_q: FinitePoset[U]
    lower: Callable[[T], U]
    upper: Callable[[U], T]

    def verify_adjunction(self) -> bool:
        return all(
            self.poset_q.leq(self.lower(p), q) == self.poset_p.leq(p, self.upper(q))
            for p in self.poset_p.elements
            for q in self.poset_q.elements
        )

    def closure(self, p: T) -> T:
        return self.upper(self.lower(p))

    def interior(self, q: U) -> U:
        return self.lower(self.upper(q))


def tarski_fixpoints(lat: FiniteLattice[T], f: Callable[[T], T]) -> FiniteLattice[T]:
    """Compute the complete sublattice of fixed points of a monotone map f: L -> L (Tarski 1955)."""
    fps = [x for x in lat.elements if f(x) == x]
    return FiniteLattice.from_poset(FinitePoset.from_leq(fps, lat.leq))


class FormalContext:
    """Formal Concept Analysis context (G, M, I) with Ganter's NextClosure & Duquenne-Guigues basis."""

    def __init__(self, objects: Sequence[str], attributes: Sequence[str], incidence: dict[str, set[str]]) -> None:
        self.objects = tuple(objects)
        self.attributes = tuple(attributes)
        self._n_obj = len(self.objects)
        self._n_attr = len(self.attributes)
        # Bitmask of objects possessing each attribute
        self._attr_ext: list[int] = [0] * self._n_attr
        for g_idx, g in enumerate(self.objects):
            attrs = incidence.get(g, set())
            for m_idx, m in enumerate(self.attributes):
                if m in attrs:
                    self._attr_ext[m_idx] |= 1 << g_idx
        self._all_obj_mask = (1 << self._n_obj) - 1
        self._all_attr_mask = (1 << self._n_attr) - 1

    def extent_mask(self, intent_mask: int) -> int:
        res = self._all_obj_mask
        for m in range(self._n_attr):
            if (intent_mask >> m) & 1:
                res &= self._attr_ext[m]
        return res

    def intent_mask(self, extent_mask: int) -> int:
        res = 0
        for m in range(self._n_attr):
            if (self._attr_ext[m] & extent_mask) == extent_mask:
                res |= 1 << m
        return res

    def close_intent(self, mask: int) -> int:
        return self.intent_mask(self.extent_mask(mask))

    def _next_closure_step(self, cur: int, closure_fn: Callable[[int], int]) -> int | None:
        for i in range(self._n_attr - 1, -1, -1):
            bit_i = 1 << i
            if not (cur & bit_i):
                prefix_mask = bit_i - 1
                cand = closure_fn((cur & prefix_mask) | bit_i)
                # Lectic check: cand agrees with cur on all bits < i
                if (cand & prefix_mask) == (cur & prefix_mask):
                    return cand
        return None

    def concept_lattice(self) -> FiniteLattice[tuple[frozenset[str], frozenset[str]]]:
        """Enumerate all formal concepts via Ganter's NextClosure and build the Concept Lattice."""
        intents: list[int] = []
        cur: int | None = self.close_intent(0)
        while cur is not None:
            intents.append(cur)
            cur = self._next_closure_step(cur, self.close_intent)
        concepts = [
            (
                frozenset(self.objects[g] for g in range(self._n_obj) if (self.extent_mask(im) >> g) & 1),
                frozenset(self.attributes[m] for m in range(self._n_attr) if (im >> m) & 1),
            )
            for im in intents
        ]
        # Concept order: (A1, B1) <= (A2, B2) iff A1 <= A2 (equivalently B2 <= B1)
        return FiniteLattice.from_poset(FinitePoset.from_leq(concepts, lambda c1, c2: c1[0] <= c2[0]))

    def duquenne_guigues_basis(self) -> list[tuple[frozenset[str], frozenset[str]]]:
        """Compute canonical Duquenne-Guigues implication basis via pseudo-intents (NextClosure)."""
        implications: list[tuple[int, int]] = []

        def lin_closure(mask: int) -> int:
            cur = mask
            while True:
                changed = False
                for prem, conc in implications:
                    if (cur & prem) == prem and (cur | conc) != cur:
                        cur |= conc
                        changed = True
                if not changed:
                    return cur

        cur: int | None = lin_closure(0)
        while cur is not None:
            closed = self.close_intent(cur)
            if closed != cur:
                implications.append((cur, closed))
            cur = self._next_closure_step(cur, lin_closure)

        return [
            (
                frozenset(self.attributes[m] for m in range(self._n_attr) if (prem >> m) & 1),
                frozenset(self.attributes[m] for m in range(self._n_attr) if ((conc & ~prem) >> m) & 1),
            )
            for prem, conc in implications
        ]


# =============================================================================
# Region III: Non-Classical Logics (Heyting/Locale, MV, Orthomodular)
# =============================================================================


class FiniteHeytingAlgebra(Generic[T]):
    """Heyting algebra / finite Locale derived canonically from any finite distributive lattice."""

    def __init__(self, lat: FiniteLattice[T]) -> None:
        if not lat.is_distributive():
            raise ValueError('FiniteHeytingAlgebra requires a distributive lattice.')
        self.lattice = lat

    def implies(self, a: T, b: T) -> T:
        """Relative pseudo-complement a -> b = sup { x | a ^ x <= b }."""
        return self.lattice.join_all(x for x in self.lattice.elements if self.lattice.leq(self.lattice.meet(a, x), b))

    def pseudo_complement(self, a: T) -> T:
        """Intuitionistic negation ~a = (a -> bot)."""
        return self.implies(a, self.lattice.bot)

    def double_negation(self, a: T) -> T:
        """Lawvere-Tierney double-negation closure ~~a."""
        return self.pseudo_complement(self.pseudo_complement(a))

    def boolean_skeleton(self) -> list[T]:
        """Regular elements { a | ~~a == a } forming a Boolean algebra (Glivenko's theorem)."""
        return [a for a in self.lattice.elements if self.double_negation(a) == a]

    def is_boolean(self) -> bool:
        return all(self.lattice.join(a, self.pseudo_complement(a)) == self.lattice.top for a in self.lattice.elements)


class LukasiewiczMVAlgebra:
    """MV-Algebra over [0, 1] extending algebrax.semiring.logic.LukasiewiczSemiring with residuation."""

    def __init__(self) -> None:
        self._semi = LukasiewiczSemiring()

    def join(self, a: float, b: float) -> float:
        return max(a, b)

    def meet(self, a: float, b: float) -> float:
        return min(a, b)

    def tnorm(self, a: float, b: float) -> float:
        return self._semi.mul(a, b)

    def implies(self, a: float, b: float) -> float:
        """Lukasiewicz residual a -> b = min(1, 1 - a + b)."""
        return min(1.0, 1.0 - a + b)

    def neg(self, a: float) -> float:
        return 1.0 - a

    def verify_residuation(self, samples: Sequence[float]) -> bool:
        eps = 1e-12
        return all(
            (self.tnorm(a, x) <= b + eps) == (x <= self.implies(a, b) + eps)
            for a in samples
            for b in samples
            for x in samples
        )


class Ortholattice(Generic[T]):
    """Bounded lattice with antitone involutive orthocomplement; detects O_6 orthomodular failures."""

    def __init__(self, lat: FiniteLattice[T], ortho_map: dict[T, T]) -> None:
        self.lattice = lat
        self._ortho = dict(ortho_map)

    def ortho(self, a: T) -> T:
        return self._ortho[a]

    def verify_orthocomplement(self) -> bool:
        lat = self.lattice
        for x in lat.elements:
            ox = self.ortho(x)
            if self.ortho(ox) != x or lat.join(x, ox) != lat.top or lat.meet(x, ox) != lat.bot:
                return False
            for y in lat.elements:
                if lat.leq(x, y) and not lat.leq(self.ortho(y), ox):
                    return False
        return True

    def find_orthomodular_violation(self) -> tuple[T, T, T] | None:
        """Return (a, b, a v (b ^ a')) violating orthomodular law a <= b => b == a v (b ^ a')."""
        lat = self.lattice
        for a in lat.elements:
            for b in lat.elements:
                if lat.leq(a, b):
                    rhs = lat.join(a, lat.meet(b, self.ortho(a)))
                    if rhs != b:
                        return (a, b, rhs)
        return None

    def is_orthomodular(self) -> bool:
        return self.find_orthomodular_violation() is None

    @classmethod
    def benzene_o6(cls) -> Ortholattice[str]:
        """The 6-element benzene hexagon O_6: orthocomplemented yet NOT orthomodular."""
        lat = FiniteLattice.from_poset(
            FinitePoset.from_covers(
                ['0', 'a', 'b', 'c', 'd', '1'],
                [('0', 'a'), ('a', 'b'), ('b', '1'), ('0', 'c'), ('c', 'd'), ('d', '1')],
            )
        )
        return cls(lat, {'0': '1', '1': '0', 'a': 'd', 'd': 'a', 'b': 'c', 'c': 'b'})

    @classmethod
    def quantum_mo2(cls) -> Ortholattice[str]:
        """The 6-element Chinese lantern MO_2 (spin-1/2 quantum logic): orthomodular, non-distributive."""
        lat = FiniteLattice.from_poset(
            FinitePoset.from_covers(
                ['0', 'x+', 'x-', 'z+', 'z-', '1'],
                [
                    ('0', 'x+'), ('0', 'x-'), ('0', 'z+'), ('0', 'z-'),
                    ('x+', '1'), ('x-', '1'), ('z+', '1'), ('z-', '1'),
                ],
            )
        )
        return cls(lat, {'0': '1', '1': '0', 'x+': 'x-', 'x-': 'x+', 'z+': 'z-', 'z-': 'z+'})


# =============================================================================
# Region IV: Matroids & Geometric Lattices (Whitney-Rota Cryptomorphism)
# =============================================================================


class FiniteMatroid:
    """Finite matroid specified by its ground set and rank function; constructs its Geometric Flat Lattice."""

    def __init__(self, ground: Sequence[Any], rank_fn: Callable[[frozenset[Any]], int]) -> None:
        self.ground = tuple(ground)
        self._rank_fn = rank_fn
        self._n = len(self.ground)

    def rank(self, subset: frozenset[Any]) -> int:
        return self._rank_fn(subset)

    def closure(self, subset: frozenset[Any]) -> frozenset[Any]:
        r = self.rank(subset)
        return frozenset(e for e in self.ground if e in subset or self.rank(subset | {e}) == r)

    def flat_lattice(self) -> FiniteLattice[frozenset[Any]]:
        """Compute the lattice of flats L(M) (always a geometric lattice for simple matroids!)."""
        bot = self.closure(frozenset())
        flats: set[frozenset[Any]] = {bot}
        q: deque[frozenset[Any]] = deque([bot])
        while q:
            f = q.popleft()
            for e in self.ground:
                if e not in f:
                    nxt = self.closure(f | {e})
                    if nxt not in flats:
                        flats.add(nxt)
                        q.append(nxt)
        return FiniteLattice.from_poset(FinitePoset.from_leq(sorted(flats, key=len), lambda a, b: a <= b))

    def characteristic_polynomial(self) -> dict[int, int]:
        """Compute chi_M(t) = sum_{F in L(M)} mu(bot, F) * t^(r(M) - r(F)) via Rota Mobius."""
        lat = self.flat_lattice()
        mu = lat.mobius_matrix()
        full_rank = self.rank(frozenset(self.ground))
        poly: dict[int, int] = {}
        for flat in lat.elements:
            coeff = mu.get((lat.bot, flat), 0)
            if coeff != 0:
                deg = full_rank - self.rank(flat)
                poly[deg] = poly.get(deg, 0) + coeff
        return {deg: c for deg, c in sorted(poly.items(), reverse=True) if c != 0}

    def tutte_polynomial(self) -> dict[tuple[int, int], int]:
        """Compute Tutte polynomial T_M(x, y) = sum_{A <= E} (x-1)^(r(E)-r(A)) (y-1)^(|A|-r(A))."""
        full_rank = self.rank(frozenset(self.ground))
        # Expand (x - 1)^a * (y - 1)^b via binomial coefficients
        from math import comb

        poly: dict[tuple[int, int], int] = {}
        for mask in range(1 << self._n):
            sub = frozenset(self.ground[i] for i in range(self._n) if (mask >> i) & 1)
            r_sub = self.rank(sub)
            a = full_rank - r_sub
            b = len(sub) - r_sub
            for i in range(a + 1):
                cx = comb(a, i) * ((-1) ** (a - i))
                for j in range(b + 1):
                    cy = comb(b, j) * ((-1) ** (b - j))
                    poly[(i, j)] = poly.get((i, j), 0) + cx * cy
        return {k: v for k, v in sorted(poly.items()) if v != 0}

    @classmethod
    def from_graph(cls, vertices: Iterable[int], edges: Sequence[tuple[int, int]]) -> FiniteMatroid:
        """Graphic matroid M(G): rank(A) = |V| - connected_components(V, A)."""
        verts = list(vertices)

        def rank_fn(edge_sub: frozenset[tuple[int, int]]) -> int:
            parent = {v: v for v in verts}

            def find(x: int) -> int:
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            comps = len(verts)
            for u, v in edge_sub:
                ru, rv = find(u), find(v)
                if ru != rv:
                    parent[ru] = rv
                    comps -= 1
            return len(verts) - comps

        return cls(edges, rank_fn)


# =============================================================================
# Demo, Benchmarks & Live AlgebraX Protocol Audit
# =============================================================================


def run_demo() -> None:
    """Execute end-to-end demonstrations and benchmarks across all 5 regions."""
    print('=== REGION I: Finite Posets, Canonical Lattices & Birkhoff Duality ===')
    d12 = divisor_lattice(12)
    j_poset, ideal_lat = d12.birkhoff_dual()
    print(
        f'  D_12: |L|={len(d12)}, distributive={d12.is_distributive()}, '
        f'|J(L)|={len(j_poset)}, |O(J(L))|={len(ideal_lat)}'
    )

    # Zeta / Mobius round-trip on D_12
    signal = {d: d for d in d12.elements}
    z = d12.zeta_transform(signal)
    recovered = d12.mobius_transform(z)
    print(f'  D_12 Rota Zeta/Mobius exact round-trip: {recovered == signal}')

    # Dedekind-MacNeille completion of the 4-element crown poset (not a lattice!)
    crown = FinitePoset.from_covers(['a1', 'a2', 'b1', 'b2'], [('a1', 'b1'), ('a1', 'b2'), ('a2', 'b1'), ('a2', 'b2')])
    dm_crown = dedekind_macneille(crown)
    print(
        f'  Dedekind-MacNeille(4-Crown): |P|={len(crown)} -> |DM(P)|={len(dm_crown)}, '
        f'modular={dm_crown.is_modular()}'
    )

    # Subgroup lattices directly from algebrax.group!
    for name, grp in [('S_3', symmetric_group(3)), ('D_4', dihedral_group(4)), ('A_4', alternating_group(4))]:
        sub_l = subgroup_lattice(grp)
        n5 = sub_l.find_n5_witness()
        m3 = sub_l.find_m3_witness()
        print(
            f'  Sub({name}): |L|={len(sub_l)}, modular={n5 is None}, distributive={n5 is None and m3 is None}, '
            f'N5_found={n5 is not None}, M3_found={m3 is not None}'
        )

    pi4 = partition_lattice(4)
    print(
        f'  PartitionLattice(4): |Pi_4|={len(pi4)} (Bell B_4=15), '
        f'geometric={pi4.is_geometric()}, modular={pi4.is_modular()}'
    )

    fano = subspace_lattice_fq(3, 2)
    print(f'  SubspaceLattice(F_2^3): |L|={len(fano)}, geometric={fano.is_geometric()}, modular={fano.is_modular()}')

    print('\n=== REGION II: Galois Connections, Tarski & Formal Concept Analysis ===')
    # AlgebraX structure-trait context!
    ctx = FormalContext(
        objects=['Semiring', 'Ring', 'Field', 'KleeneAlgebra', 'JordanAlgebra', 'BooleanAlgebra'],
        attributes=['assoc', 'comm', 'idem', 'has_neg', 'has_inv', 'residuated'],
        incidence={
            'Semiring': {'assoc'},
            'Ring': {'assoc', 'has_neg'},
            'Field': {'assoc', 'comm', 'has_neg', 'has_inv'},
            'KleeneAlgebra': {'assoc', 'idem'},
            'JordanAlgebra': {'comm', 'has_neg'},
            'BooleanAlgebra': {'assoc', 'comm', 'idem', 'residuated'},
        },
    )
    t0 = time.perf_counter()
    cl = ctx.concept_lattice()
    dg = ctx.duquenne_guigues_basis()
    dt_ms = (time.perf_counter() - t0) * 1000
    print(f'  FCA AlgebraX Trait Context: |Concepts|={len(cl)}, |DG Basis|={len(dg)} ({dt_ms:.2f} ms)')
    for prem, conc in dg:
        print(f'    {sorted(prem)}  ==>  {sorted(conc)}')

    # Tarski fixpoints of double-negation closure on a non-Boolean Heyting algebra
    p3 = FinitePoset.from_covers(['0', '1', '2'], [('0', '1'), ('1', '2')])
    l3 = FiniteLattice.from_poset(p3)
    h3 = FiniteHeytingAlgebra(l3)
    tarski_l = tarski_fixpoints(l3, h3.double_negation)
    print(f'  Tarski fixpoints of ~~ on C_3: {list(tarski_l.elements)} (Boolean skeleton size={len(tarski_l)})')

    print('\n=== REGION III: Non-Classical Logics (Heyting, MV, Quantum Orthomodular) ===')
    # Alexandroff open-set locale of a 3-element V-poset
    v_poset = FinitePoset.from_covers(['r', 'x', 'y'], [('r', 'x'), ('r', 'y')])
    alex_lat = FiniteLattice.from_poset(FinitePoset.from_leq(v_poset.order_ideals(), lambda a, b: a <= b))
    alex_heyting = FiniteHeytingAlgebra(alex_lat)
    print(
        f'  Alexandroff Locale O(V_3): |L|={len(alex_lat)}, is_boolean={alex_heyting.is_boolean()}, '
        f'|Boolean skeleton|={len(alex_heyting.boolean_skeleton())}'
    )
    mv = LukasiewiczMVAlgebra()
    print(f'  Lukasiewicz MV-Algebra residuation exact on 6-grid: {mv.verify_residuation([i / 5 for i in range(6)])}')
    o6 = Ortholattice.benzene_o6()
    mo2 = Ortholattice.quantum_mo2()
    print(
        f'  Benzene O_6: ortho={o6.verify_orthocomplement()}, '
        f'orthomodular={o6.is_orthomodular()}, witness={o6.find_orthomodular_violation()}'
    )
    print(
        f'  Quantum MO_2: ortho={mo2.verify_orthocomplement()}, '
        f'orthomodular={mo2.is_orthomodular()}, distributive={mo2.lattice.is_distributive()}'
    )

    print('\n=== REGION IV: Matroids & Geometric Lattices (K_4 Chromatic & Tutte) ===')
    k4_edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    m_k4 = FiniteMatroid.from_graph(range(4), k4_edges)
    flats_k4 = m_k4.flat_lattice()
    chi_k4 = m_k4.characteristic_polynomial()
    tutte_k4 = m_k4.tutte_polynomial()
    spanning_trees = sum(tutte_k4.values())
    print(f'  Graphic Matroid M(K_4): |Flats|={len(flats_k4)}, geometric={flats_k4.is_geometric()}')
    print(f'  Characteristic polynomial chi_K4(t): {chi_k4}  (expected (t-1)(t-2)(t-3) = t^3 - 6t^2 + 11t - 6)')
    print(f'  Tutte T_K4(1, 1) = {spanning_trees} spanning trees (Cayley 4^2 = 16)')

    print('\n=== REGION V: Live AlgebraX Protocol Audit (Isomer Blindness!) ===')
    n5_lat = FiniteLattice.from_poset(
        FinitePoset.from_covers(['0', 'a', 'c', 'b', '1'], [('0', 'a'), ('a', 'c'), ('c', '1'), ('0', 'b'), ('b', '1')])
    )
    print(f'  isinstance(N_5, Lattice):             {isinstance(n5_lat, Lattice)}  (Expected True)')
    print(f'  isinstance(N_5, BoundedLattice):      {isinstance(n5_lat, BoundedLattice)}  (Expected True)')
    print(
        f'  isinstance(N_5, DistributiveLattice): {isinstance(n5_lat, DistributiveLattice)}  '
        '(BUG: N_5 is NON-MODULAR!)'
    )
    print(f'  isinstance(N_5, BooleanAlgebra):      {isinstance(n5_lat, BooleanAlgebra)}  (Expected False)')


if __name__ == '__main__':
    run_demo()
