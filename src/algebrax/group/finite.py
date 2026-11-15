r"""
Finite Groups, Subgroups, Coset Decompositions, Conjugacy Classes, and Quotients.

Algebraic Signatures:
    Finite Group:      $\langle G, e, \cdot, ^{-1} \rangle$ with $|G| < \infty$
    Conjugacy Class:   $C_g = \{h g h^{-1} \mid h \in G\}$
    Left Coset Space:  $G / H = \{g H \mid g \in G\}$, \quad $|G| = [G : H] \cdot |H|$
    Double Cosets:     $H \backslash G / K = \{H g K \mid g \in G\}$
    Quotient Group:    $G / N = \{g N \mid g \in G\}$ when $N \trianglelefteq G$
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Hashable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar

from algebrax.algebra._group import CommGroup, Group
from algebrax.algebra._mixins import HasContains
from algebrax.typing import SparseMatrix

G = TypeVar('G', bound=Hashable)


def conjugacy_classes(
    elements: Sequence[G],
    mul: Callable[[G, G], G],
    inv: Callable[[G], G],
) -> list[tuple[G, ...]]:
    r"""Partition a finite group into its conjugacy classes $C_g = \{h g h^{-1} \mid h \in G\}$.

    Args:
        elements: All distinct elements of the finite group $G$.
        mul: Associative group multiplication $(g, h) \mapsto g h$.
        inv: Group inversion $g \mapsto g^{-1}$.

    Returns:
        List of disjoint tuples covering `elements`, ordered by first appearance
        with the identity class first if `elements[0]` is the identity.
    """
    assigned: set[G] = set()
    classes: list[tuple[G, ...]] = []

    for g in elements:
        if g in assigned:
            continue
        orbit: list[G] = []
        seen_in_orbit: set[G] = set()
        for h in elements:
            conj = mul(mul(h, g), inv(h))
            if conj not in seen_in_orbit:
                seen_in_orbit.add(conj)
                orbit.append(conj)
                assigned.add(conj)
        classes.append(tuple(orbit))

    return classes


def _is_commutative(elements: Sequence[G], mul: Callable[[G, G], G]) -> bool:
    for i, a in enumerate(elements):
        for b in elements[i + 1 :]:
            if mul(a, b) != mul(b, a):
                return False
    return True


@dataclass(frozen=True)
class FiniteGroup(Group[G], HasContains[G], Generic[G]):
    r"""Concrete finite group $\langle G, \mathbf{1}, \cdot, ^{-1} \rangle$ inheriting `Group[G]`
    (`HasOne`, `HasMul`, `HasInv`, `LawAssociative`) and `HasContains[G]`.

    Algebraic Signature:
        $\langle G, e, \cdot, ^{-1} \rangle$ with $|G| < \infty$, associative `mul`, two-sided `one`, and `inv`.

    Attributes:
        elements: Ordered tuple of all distinct elements of $G$.
        identity: Two-sided group identity element $e \in G$ (exposed via `.one`).
        mul_fn: Binary associative group product $(a, b) \mapsto a \cdot b$.
        inv_fn: Optional inversion callable $a \mapsto a^{-1}$ (inferred from `mul_fn` if omitted).
        name: Optional human-readable label (e.g. `'S_3'`, `'Q_8'`).
    """

    elements: tuple[G, ...]
    identity: G
    mul_fn: Callable[[G, G], G]
    inv_fn: Callable[[G], G] | None = None
    name: str = ''
    _element_set: frozenset[G] = field(init=False, repr=False, compare=False)
    _inv_cache: dict[G, G] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        elem_tuple = tuple(self.elements)
        if not elem_tuple:
            raise ValueError('FiniteGroup requires at least one element.')
        elem_set = frozenset(elem_tuple)
        if len(elem_set) != len(elem_tuple):
            raise ValueError('FiniteGroup elements must be distinct.')
        if self.identity not in elem_set:
            raise ValueError(f'Identity element {self.identity!r} is not in elements.')

        inv_cache: dict[G, G] = {}
        if self.inv_fn is None:
            for g in elem_tuple:
                found: G | None = None
                for h in elem_tuple:
                    if self.mul_fn(g, h) == self.identity and self.mul_fn(h, g) == self.identity:
                        found = h
                        break
                if found is None:
                    raise ValueError(f'Element {g!r} has no two-sided inverse in FiniteGroup.')
                inv_cache[g] = found

        object.__setattr__(self, 'elements', elem_tuple)
        object.__setattr__(self, '_element_set', elem_set)
        object.__setattr__(self, '_inv_cache', inv_cache)

    @classmethod
    def from_cayley_table(
        cls,
        table: Mapping[tuple[G, G], G],
        identity: G | None = None,
        name: str = '',
    ) -> FiniteGroup[G]:
        """Construct a `FiniteGroup` (or `FiniteCommGroup` if abelian) from `(g, h) -> g * h`."""
        if not table:
            raise ValueError('Cayley table cannot be empty.')
        elems = tuple(dict.fromkeys(g for pair in table for g in pair))
        inferred_id = identity
        if inferred_id is None:
            for candidate in elems:
                if all(table[(candidate, x)] == x and table[(x, candidate)] == x for x in elems):
                    inferred_id = candidate
                    break
        if inferred_id is None:
            raise ValueError('Could not infer identity element from Cayley table.')

        def _table_mul(a: G, b: G) -> G:
            return table[(a, b)]

        if cls is FiniteGroup and _is_commutative(elems, _table_mul):
            return FiniteCommGroup(
                elements=elems,
                identity=inferred_id,
                mul_fn=_table_mul,
                name=name,
                verify_commutative=False,
            )
        return cls(
            elements=elems,
            identity=inferred_id,
            mul_fn=_table_mul,
            name=name,
        )

    @property
    def one(self) -> G:
        """Neutral group identity element $e$ (satisfying `Group[G]`)."""
        return self.identity

    @property
    def order(self) -> int:
        """Cardinality $|G|$ of the finite group."""
        return len(self.elements)

    def __len__(self) -> int:
        return len(self.elements)

    def __iter__(self) -> Iterator[G]:
        return iter(self.elements)

    def contains(self, element: G) -> bool:
        """Return True iff `element` belongs to the underlying carrier set (satisfying `HasContains[G]`)."""
        return element in self._element_set

    def __contains__(self, item: object) -> bool:
        return item in self._element_set

    def mul(self, a: G, b: G) -> G:
        r"""Associative group multiplication $a \cdot b$."""
        return self.mul_fn(a, b)

    def inv(self, a: G) -> G:
        r"""Two-sided group inverse $a^{-1}$."""
        if self.inv_fn is not None:
            return self.inv_fn(a)
        return self._inv_cache[a]

    def div(self, a: G, b: G) -> G:
        r"""Right-quotient group operation $a \cdot b^{-1}$."""
        return self.mul_fn(a, self.inv(b))

    def cayley_table(self) -> dict[tuple[G, G], G]:
        """Materialize the complete multiplication table `{(g, h): g * h}`."""
        return {(g, h): self.mul_fn(g, h) for g in self.elements for h in self.elements}

    def regular_action_matrix(self, g: G) -> SparseMatrix[int, float]:
        r"""Return the sparse $|G| \times |G|$ left regular permutation matrix for $g \in G$."""
        idx = {el: i for i, el in enumerate(self.elements)}
        mat: dict[int, dict[int, float]] = {}
        for h in self.elements:
            mat.setdefault(idx[self.mul_fn(g, h)], {})[idx[h]] = 1.0
        return mat

    def order_of(self, g: G) -> int:
        r"""Return the multiplicative order $\min \{k \ge 1 : g^k = e\}$ of element $g$."""
        if g not in self._element_set:
            raise ValueError(f'Element {g!r} does not belong to group.')
        curr = g
        k = 1
        while curr != self.identity:
            curr = self.mul_fn(curr, g)
            k += 1
            if k > self.order:
                raise ValueError(f'Failed to close cyclic subgroup generated by {g!r}.')
        return k

    def conjugacy_classes(self) -> list[tuple[G, ...]]:
        r"""Partition $G$ into disjoint conjugacy classes $C_g = \{h g h^{-1} : h \in G\}$."""
        return conjugacy_classes(self.elements, self.mul_fn, self.inv)

    def is_abelian(self) -> bool:
        r"""Return True iff $g h = h g$ for all $g, h \in G$."""
        return _is_commutative(self.elements, self.mul_fn)

    def as_commutative(self) -> FiniteCommGroup[G]:
        """Promote this group to `FiniteCommGroup[G]` if abelian; raise `ValueError` otherwise."""
        if isinstance(self, FiniteCommGroup):
            return self
        if not self.is_abelian():
            raise ValueError(f'Group {self!r} is not abelian and cannot be narrowed to FiniteCommGroup.')
        return FiniteCommGroup(
            elements=self.elements,
            identity=self.identity,
            mul_fn=self.mul_fn,
            inv_fn=self.inv_fn,
            name=self.name,
            verify_commutative=False,
        )

    def _as_subgroup_elements(self, subgroup: FiniteGroup[G] | Iterable[G]) -> tuple[G, ...]:
        if isinstance(subgroup, FiniteGroup):
            sub_elems = subgroup.elements
        else:
            raw = tuple(dict.fromkeys(subgroup))
            sub_elems = raw
        sub_set = set(sub_elems)
        if self.identity not in sub_set:
            raise ValueError('Subgroup must contain the group identity.')
        for x in sub_elems:
            if x not in self._element_set:
                raise ValueError(f'Subgroup element {x!r} is not in parent group.')
            if self.inv(x) not in sub_set:
                raise ValueError(f'Subgroup is not closed under inversion at {x!r}.')
            for y in sub_elems:
                if self.mul_fn(x, y) not in sub_set:
                    raise ValueError(f'Subgroup is not closed under multiplication ({x!r}, {y!r}).')
        # Order consistently with parent elements
        return tuple(g for g in self.elements if g in sub_set)

    def _subgroup_elements(
        self,
        generators_or_elements: Iterable[G],
        *,
        generate: bool = False,
    ) -> tuple[G, ...]:
        seeds = list(generators_or_elements)
        for s in seeds:
            if s not in self._element_set:
                raise ValueError(f'Element {s!r} does not belong to parent group.')

        if not generate:
            return self._as_subgroup_elements(seeds)

        closed: set[G] = {self.identity}
        queue: deque[G] = deque()
        for s in seeds:
            if s not in closed:
                closed.add(s)
                queue.append(s)
            s_inv = self.inv(s)
            if s_inv not in closed:
                closed.add(s_inv)
                queue.append(s_inv)

        while queue:
            cur = queue.popleft()
            snapshot = list(closed)
            for other in snapshot:
                for prod in (self.mul_fn(cur, other), self.mul_fn(other, cur)):
                    if prod not in closed:
                        closed.add(prod)
                        queue.append(prod)
                prod_inv = self.inv(cur)
                if prod_inv not in closed:
                    closed.add(prod_inv)
                    queue.append(prod_inv)

        return tuple(g for g in self.elements if g in closed)

    def _make_subgroup(
        self,
        elems: tuple[G, ...],
        name: str = '',
        *,
        assume_commutative: bool = False,
    ) -> FiniteGroup[G]:
        if assume_commutative or _is_commutative(elems, self.mul_fn):
            return FiniteCommGroup(
                elements=elems,
                identity=self.identity,
                mul_fn=self.mul_fn,
                inv_fn=self.inv_fn,
                name=name,
                verify_commutative=False,
            )
        return FiniteGroup(
            elements=elems,
            identity=self.identity,
            mul_fn=self.mul_fn,
            inv_fn=self.inv_fn,
            name=name,
        )

    def subgroup(
        self,
        generators_or_elements: Iterable[G],
        *,
        generate: bool = False,
        name: str = '',
    ) -> FiniteGroup[G]:
        r"""Construct a subgroup $H \le G$ from explicit elements or by generating closure."""
        elems = self._subgroup_elements(generators_or_elements, generate=generate)
        return self._make_subgroup(elems, name=name)

    def _resolve_targets(self, target: G | Iterable[G]) -> list[G]:
        if target in self._element_set:
            return [target]  # type: ignore[list-item]
        targets = list(target)  # type: ignore[arg-type]
        for s in targets:
            if s not in self._element_set:
                raise ValueError(f'Element {s!r} does not belong to group.')
        return targets

    def centralizer(self, target: G | Iterable[G]) -> FiniteGroup[G]:
        r"""Return the centralizer subgroup $C_G(S) = \{g \in G : g s = s g \ \forall s \in S\}$."""
        targets = self._resolve_targets(target)
        elems = tuple(
            g for g in self.elements if all(self.mul_fn(g, s) == self.mul_fn(s, g) for s in targets)
        )
        return self._make_subgroup(elems, name=f'C({self.name})' if self.name else '')

    def center(self) -> FiniteCommGroup[G]:
        r"""Return the center subgroup $Z(G) = \{z \in G : z g = g z \ \forall g \in G\}$."""
        elems = tuple(
            g for g in self.elements if all(self.mul_fn(g, s) == self.mul_fn(s, g) for s in self.elements)
        )
        return FiniteCommGroup(
            elements=elems,
            identity=self.identity,
            mul_fn=self.mul_fn,
            inv_fn=self.inv_fn,
            name=f'Z({self.name})' if self.name else '',
            verify_commutative=False,
        )

    def normalizer(self, subgroup: FiniteGroup[G] | Iterable[G]) -> FiniteGroup[G]:
        r"""Return the normalizer $N_G(H) = \{g \in G : g H g^{-1} = H\}$."""
        h_elems = self._as_subgroup_elements(subgroup)
        h_set = set(h_elems)
        elems = tuple(
            g
            for g in self.elements
            if all(self.mul_fn(self.mul_fn(g, h), self.inv(g)) in h_set for h in h_elems)
        )
        return self._make_subgroup(elems, name=f'N({self.name})' if self.name else '')

    def is_normal(self, subgroup: FiniteGroup[G] | Iterable[G]) -> bool:
        r"""Return True iff $g H g^{-1} = H$ for all $g \in G$."""
        h_elems = self._as_subgroup_elements(subgroup)
        h_set = set(h_elems)
        return all(
            self.mul_fn(self.mul_fn(g, h), self.inv(g)) in h_set
            for g in self.elements
            for h in h_elems
        )

    def left_cosets(self, subgroup: FiniteGroup[G] | Iterable[G]) -> list[tuple[G, ...]]:
        r"""Partition $G$ into disjoint left cosets $g H = \{g h \mid h \in H\}$.

        The identity coset $e H = H$ is guaranteed to appear first.
        """
        h_elems = self._as_subgroup_elements(subgroup)
        elem_pos = {el: idx for idx, el in enumerate(self.elements)}
        assigned: set[G] = set()
        cosets: list[tuple[G, ...]] = []

        ordered_seeds = [self.identity] + [g for g in self.elements if g != self.identity]
        for g in ordered_seeds:
            if g in assigned:
                continue
            coset = tuple(sorted({self.mul_fn(g, h) for h in h_elems}, key=lambda x: elem_pos[x]))
            assigned.update(coset)
            cosets.append(coset)
        return cosets

    def left_coset_representatives(self, subgroup: FiniteGroup[G] | Iterable[G]) -> list[G]:
        """Return a complete set of left coset representatives `[g_0, ..., g_{m-1}]` with `g_0 == identity`."""
        cosets = self.left_cosets(subgroup)
        reps: list[G] = []
        for coset in cosets:
            reps.append(self.identity if self.identity in coset else coset[0])
        return reps

    def coset_action(
        self,
        subgroup: FiniteGroup[G] | Iterable[G],
    ) -> tuple[list[G], Callable[[G, int], tuple[int, G]]]:
        r"""Return left coset representatives and the permutation-residual action map.

        For coset representatives $g_0, \dots, g_{m-1}$ of $G / H$ and any $g \in G$, computes
        the unique $(i, h)$ with $0 \le i < m$ and $h \in H$ such that $g \cdot g_j = g_i \cdot h$.
        """
        h_elems = self._as_subgroup_elements(subgroup)
        h_set = set(h_elems)
        reps = self.left_coset_representatives(h_elems)
        coset_of: dict[G, int] = {}
        for i, rep_g in enumerate(reps):
            for h in h_elems:
                coset_of[self.mul_fn(rep_g, h)] = i

        def action(g: G, j: int) -> tuple[int, G]:
            prod = self.mul_fn(g, reps[j])
            i = coset_of[prod]
            h = self.mul_fn(self.inv(reps[i]), prod)
            if h not in h_set:
                raise RuntimeError('Internal coset action inconsistency.')
            return i, h

        return reps, action

    def double_cosets(
        self,
        left_subgroup: FiniteGroup[G] | Iterable[G],
        right_subgroup: FiniteGroup[G] | Iterable[G],
    ) -> list[tuple[G, ...]]:
        r"""Partition $G$ into disjoint double cosets $H g K = \{h g k \mid h \in H, k \in K\}$."""
        h_elems = self._as_subgroup_elements(left_subgroup)
        k_elems = self._as_subgroup_elements(right_subgroup)
        elem_pos = {el: idx for idx, el in enumerate(self.elements)}
        assigned: set[G] = set()
        d_cosets: list[tuple[G, ...]] = []

        ordered_seeds = [self.identity] + [g for g in self.elements if g != self.identity]
        for g in ordered_seeds:
            if g in assigned:
                continue
            orbit = {self.mul_fn(self.mul_fn(h, g), k) for h in h_elems for k in k_elems}
            dc = tuple(sorted(orbit, key=lambda x: elem_pos[x]))
            assigned.update(dc)
            d_cosets.append(dc)
        return d_cosets

    def double_coset_representatives(
        self,
        left_subgroup: FiniteGroup[G] | Iterable[G],
        right_subgroup: FiniteGroup[G] | Iterable[G],
    ) -> list[G]:
        r"""Return canonical representatives for each double coset in $H \backslash G / K$."""
        d_cosets = self.double_cosets(left_subgroup, right_subgroup)
        return [self.identity if self.identity in dc else dc[0] for dc in d_cosets]

    def _quotient_data(
        self,
        normal_subgroup: FiniteGroup[G] | Iterable[G],
        name: str = '',
        *,
        assume_normal: bool = False,
    ) -> tuple[
        tuple[tuple[G, ...], ...],
        tuple[G, ...],
        Callable[[tuple[G, ...], tuple[G, ...]], tuple[G, ...]],
        Callable[[tuple[G, ...]], tuple[G, ...]],
        str,
    ]:
        n_elems = self._as_subgroup_elements(normal_subgroup)
        if not assume_normal and not self.is_normal(n_elems):
            raise ValueError('Cannot form quotient group: subgroup is not normal.')
        cosets = tuple(self.left_cosets(n_elems))
        coset_of: dict[G, tuple[G, ...]] = {}
        for c in cosets:
            for el in c:
                coset_of[el] = c

        id_coset = coset_of[self.identity]

        def q_mul(c1: tuple[G, ...], c2: tuple[G, ...]) -> tuple[G, ...]:
            return coset_of[self.mul_fn(c1[0], c2[0])]

        def q_inv(c: tuple[G, ...]) -> tuple[G, ...]:
            return coset_of[self.inv(c[0])]

        q_name = name or (f'{self.name}/N' if self.name else '')
        return cosets, id_coset, q_mul, q_inv, q_name

    def quotient(
        self,
        normal_subgroup: FiniteGroup[G] | Iterable[G],
        name: str = '',
    ) -> FiniteGroup[tuple[G, ...]]:
        r"""Construct the quotient group $G / N$ over canonical coset tuples.

        Returns `FiniteCommGroup` automatically when $G / N$ is abelian.

        Raises:
            ValueError: If `normal_subgroup` is not a normal subgroup of $G$.
        """
        cosets, id_coset, q_mul, q_inv, q_name = self._quotient_data(normal_subgroup, name=name)
        if _is_commutative(cosets, q_mul):
            return FiniteCommGroup(
                elements=cosets,
                identity=id_coset,
                mul_fn=q_mul,
                inv_fn=q_inv,
                name=q_name,
                verify_commutative=False,
            )
        return FiniteGroup(
            elements=cosets,
            identity=id_coset,
            mul_fn=q_mul,
            inv_fn=q_inv,
            name=q_name,
        )

    def __repr__(self) -> str:
        label = f"'{self.name}', " if self.name else ''
        return f'FiniteGroup({label}order={self.order})'


@dataclass(frozen=True)
class FiniteCommGroup(FiniteGroup[G], CommGroup[G], Generic[G]):
    r"""Concrete finite abelian group $\langle G, \mathbf{1}, \cdot, ^{-1} \rangle$ inheriting
    `FiniteGroup[G]` and `CommGroup[G]` (`HasOne`, `HasMul`, `HasInv`, `LawAssociative`, `LawCommutative`).

    Algebraic Signature:
        $\langle G, e, \cdot, ^{-1} \rangle$ with $|G| < \infty$ and $a \cdot b = b \cdot a$.
    """

    verify_commutative: bool = field(default=True, repr=False, compare=False, kw_only=True)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.verify_commutative and not _is_commutative(self.elements, self.mul_fn):
            raise ValueError('FiniteCommGroup multiplication must be commutative.')

    def is_abelian(self) -> Literal[True]:
        r"""Always returns `True` in $O(1)$ time for a `FiniteCommGroup`."""
        return True

    def as_commutative(self) -> FiniteCommGroup[G]:
        """Return `self`, as this group is already a `FiniteCommGroup[G]`."""
        return self

    def conjugacy_classes(self) -> list[tuple[G, ...]]:
        r"""Return singleton conjugacy classes $[(g,) \text{ for } g \in G]$ in $O(|G|)$ time."""
        return [(g,) for g in self.elements]

    def center(self) -> FiniteCommGroup[G]:
        r"""Return `self` in $O(1)$ time, since $Z(G) = G$ for any abelian group."""
        return self

    def centralizer(self, target: G | Iterable[G]) -> FiniteCommGroup[G]:
        r"""Validate target membership and return `self`, since $C_G(S) = G$."""
        self._resolve_targets(target)
        return self

    def is_normal(self, subgroup: FiniteGroup[G] | Iterable[G]) -> Literal[True]:
        r"""Validate subgroup closure and return `True` (every subgroup is normal)."""
        self._as_subgroup_elements(subgroup)
        return True

    def normalizer(self, subgroup: FiniteGroup[G] | Iterable[G]) -> FiniteCommGroup[G]:
        r"""Validate subgroup closure and return `self`, since $N_G(H) = G$."""
        self._as_subgroup_elements(subgroup)
        return self

    def subgroup(
        self,
        generators_or_elements: Iterable[G],
        *,
        generate: bool = False,
        name: str = '',
    ) -> FiniteCommGroup[G]:
        r"""Construct an abelian subgroup $H \le G$ as a `FiniteCommGroup[G]`."""
        elems = self._subgroup_elements(generators_or_elements, generate=generate)
        return FiniteCommGroup(
            elements=elems,
            identity=self.identity,
            mul_fn=self.mul_fn,
            inv_fn=self.inv_fn,
            name=name,
            verify_commutative=False,
        )

    def quotient(
        self,
        normal_subgroup: FiniteGroup[G] | Iterable[G],
        name: str = '',
    ) -> FiniteCommGroup[tuple[G, ...]]:
        r"""Construct the abelian quotient group $G / N$ as a `FiniteCommGroup`."""
        cosets, id_coset, q_mul, q_inv, q_name = self._quotient_data(
            normal_subgroup,
            name=name,
            assume_normal=True,
        )
        return FiniteCommGroup(
            elements=cosets,
            identity=id_coset,
            mul_fn=q_mul,
            inv_fn=q_inv,
            name=q_name,
            verify_commutative=False,
        )

    def __repr__(self) -> str:
        label = f"'{self.name}', " if self.name else ''
        return f'FiniteCommGroup({label}order={self.order})'


__all__ = [
    'FiniteCommGroup',
    'FiniteGroup',
    'conjugacy_classes',
]
