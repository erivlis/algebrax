r"""
Contravariant polynomial morphisms, GIT syzygy varieties, Grassmannians, and coordinate Hopf algebras.

Provides:
- `PolynomialMap`: A polynomial morphism $\phi: V \to W$ realizing contravariant pullback
  $\phi^*: k[W] \to k[V]$ as an explicit `RingHom`.
- `syzygy_variety`: Compute the algebraic relation / GIT quotient variety $V // G \subseteq k^m$
  among invariant polynomials via tag-variable elimination.
- `plucker_grassmannian_variety`: Construct the Plücker affine cone over $\operatorname{Gr}(k, n)$
  cut out by quadratic Grassmann-Plücker relations.
- `CoordinateHopfAlgebra`: Equip the coordinate ring $k[G]$ of an affine algebraic matrix group
  $G \subseteq \operatorname{GL}_n(k)$ with commutative `HopfAlgebra` operations
  ($\Delta, \epsilon, S$).
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from typing import Any, Literal, TypeVar

from algebrax.algebra import (
    Field,
    HopfAlgebra,
    LawAssociative,
    LawCommutative,
    Monomial,
    MultivariatePolynomialAlgebra,
    RingHom,
    SparseMPoly,
    groebner_basis,
    monomial_add,
)
from algebrax.variety.affine import AffineVariety, _fields_compatible
from algebrax.variety.k_theory import coordinate_ring_unit_inverse

V = TypeVar('V')


def _freeze_coeff(coeff: Any) -> Any:
    """Convert mutable dict field scalars (e.g. GaloisField elements) into hashable tuples."""
    if isinstance(coeff, dict):
        return tuple(sorted((k, _freeze_coeff(v)) for k, v in coeff.items()))
    return coeff


def _poly_pow(
    ring: MultivariatePolynomialAlgebra[V],
    base: SparseMPoly[V],
    exp: int,
    reduce_fn: Callable[[SparseMPoly[V]], SparseMPoly[V]] | None = None,
) -> SparseMPoly[V]:
    """Compute base ** exp in a polynomial or quotient ring via O(log exp) binary exponentiation."""
    if exp == 0:
        res = ring.one
        return reduce_fn(res) if reduce_fn is not None else res
    res = ring.one
    cur = reduce_fn(base) if reduce_fn is not None else base
    k = exp
    while k > 0:
        if k & 1:
            res = ring.mul(res, cur)
            if reduce_fn is not None:
                res = reduce_fn(res)
        k >>= 1
        if k:
            cur = ring.mul(cur, cur)
            if reduce_fn is not None:
                cur = reduce_fn(cur)
    return res


def _substitute_poly(
    target_ring: MultivariatePolynomialAlgebra[V],
    poly: SparseMPoly[V],
    components: Sequence[SparseMPoly[V]],
    *,
    reduce_fn: Callable[[SparseMPoly[V]], SparseMPoly[V]] | None = None,
) -> SparseMPoly[V]:
    r"""Substitute $x_j \mapsto \text{components}[j]$ into `poly`, returning a polynomial in `target_ring`."""
    expected_arity = len(components)
    power_cache: dict[tuple[int, int], SparseMPoly[V]] = {}
    acc: SparseMPoly[V] = target_ring.zero
    for mon, coeff in poly.items():
        if len(mon) != expected_arity:
            raise ValueError(
                f'Polynomial monomial {mon!r} has arity {len(mon)}, expected {expected_arity}.'
            )
        if target_ring.field.is_zero(coeff):
            continue
        term: SparseMPoly[V] = target_ring.const(coeff)
        for var_idx, exp in enumerate(mon):
            if exp == 0:
                continue
            key = (var_idx, exp)
            powered = power_cache.get(key)
            if powered is None:
                powered = _poly_pow(target_ring, components[var_idx], exp, reduce_fn=reduce_fn)
                power_cache[key] = powered
            term = target_ring.mul(term, powered)
            if reduce_fn is not None:
                term = reduce_fn(term)
        acc = target_ring.add(acc, term)
    return reduce_fn(acc) if reduce_fn is not None else acc


class PolynomialMap(RingHom[SparseMPoly[V], SparseMPoly[V]]):
    r"""A polynomial morphism $\phi: V \to W$ together with its contravariant pullback $\phi^*: k[W] \to k[V]$.

    Algebraic Signature:
        $\langle \phi: V \to W,\; \phi^*: k[W] \to k[V] \rangle$

    Carrier:
        Tuple of canonical component polynomials $(\phi_1, \dots, \phi_m) \in k[V]^m$ satisfying
        $\phi^*(I(W)) = \{0\}$ in $k[V]$.

    Operations:
        - `eval_point(p)`: Forward geometric morphism $p \mapsto (\phi_1(p), \dots, \phi_m(p)) \in W$.
        - `pullback(g)` / `__call__(g)`: Contravariant `RingHom`
          $g \mapsto \overline{g(\phi_1, \dots, \phi_m)}^{I(V)} \in k[V]$.
        - `compose(other)`: Geometric composition $\phi \circ \psi$ (dual to $\psi^* \circ \phi^*$).
        - `identity(variety)`: Identity morphism $\operatorname{id}_V: V \to V$.

    Properties:
        Satisfies `RingHom[SparseMPoly[V], SparseMPoly[V]]` and the adjunction
        $(\phi^* g)(p) = g(\phi(p))$ for all $p \in V$ and $g \in k[W]$.

    Args:
        domain: Source affine variety $V \subseteq k^n$.
        codomain: Target affine variety $W \subseteq k^m$.
        components: Sequence of $m$ polynomials in $k[x_1, \dots, x_n]$ defining $\phi$.
        verify_well_defined: If True (default), verify $\phi^*(g) = 0 \bmod I(V)$ for all $g \in I(W)$.
    """

    def __init__(
        self,
        domain: AffineVariety[V],
        codomain: AffineVariety[V],
        components: Sequence[SparseMPoly[V]],
        *,
        verify_well_defined: bool = True,
    ) -> None:
        if len(components) != codomain.ambient_dimension:
            raise ValueError(
                f'PolynomialMap requires {codomain.ambient_dimension} component polynomials '
                f'matching codomain ambient dimension, got {len(components)}.'
            )
        if not _fields_compatible(domain.ring.field, codomain.ring.field):
            raise TypeError(
                f'Incompatible fields between domain ({domain.ring.field!r}) '
                f'and codomain ({codomain.ring.field!r}).'
            )
        dom_n = domain.ambient_dimension
        for idx, comp in enumerate(components):
            for mon in comp:
                if len(mon) != dom_n:
                    raise ValueError(
                        f'Component {idx} monomial {mon!r} has arity {len(mon)}, expected {dom_n}.'
                    )
        self.domain: AffineVariety[V] = domain
        self.codomain: AffineVariety[V] = codomain
        self._components: tuple[SparseMPoly[V], ...] = tuple(
            domain.ideal.reduce(c) for c in components
        )

        if verify_well_defined:
            for gen in codomain.ideal.basis:
                pulled = self.pullback(gen)
                if pulled:
                    raise ValueError(
                        'PolynomialMap is not well-defined: image of domain does not lie in codomain '
                        f'(non-zero pullback {pulled!r} for codomain generator {gen!r}).'
                    )

    @property
    def components(self) -> tuple[SparseMPoly[V], ...]:
        """Defensive copies of the canonical component polynomials in $k[V]$."""
        return tuple(dict(c) for c in self._components)

    @classmethod
    def identity(cls, variety: AffineVariety[V]) -> PolynomialMap[V]:
        r"""Construct the identity morphism $\operatorname{id}_V: V \to V$."""
        gens = [variety.ring.gen(i) for i in range(variety.ambient_dimension)]
        return cls(variety, variety, gens, verify_well_defined=False)

    def pullback(self, poly: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Contravariant pullback $\phi^*(g) = \overline{g(\phi_1, \dots, \phi_m)}^{I(V)} \in k[V]$."""
        return _substitute_poly(
            self.domain.ring,
            poly,
            self._components,
            reduce_fn=self.domain.ideal.reduce,
        )

    def __call__(self, x: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Apply the coordinate-ring pullback `RingHom` $\phi^*: k[W] \to k[V]$."""
        return self.pullback(x)

    def eval_point(self, point: Sequence[V]) -> tuple[V, ...]:
        r"""Evaluate the geometric morphism $\phi(p) = (\phi_1(p), \dots, \phi_m(p)) \in W$.

        Args:
            point: Coordinate sequence $p \in V \subseteq k^n$.

        Raises:
            ValueError: If `len(point) != self.domain.ambient_dimension`.
        """
        if len(point) != self.domain.ambient_dimension:
            raise ValueError(
                f'Expected point of length {self.domain.ambient_dimension}, got {len(point)}.'
            )
        return tuple(self.domain.ring.eval(comp, point) for comp in self._components)

    def compose(self, other: PolynomialMap[V]) -> PolynomialMap[V]:
        r"""Geometric morphism composition $(\phi \circ \psi)(p) = \phi(\psi(p))$, dual to $\psi^* \circ \phi^*$.

        Note that `self` is the outer morphism $\phi: W \to Z$ and `other` is the inner
        morphism $\psi: V \to W'$ with $W' \subseteq W$ (i.e. $I(W) \subseteq I(W')$).

        Args:
            other: Inner morphism $\psi: V \to W'$ whose codomain lies inside `self.domain`.

        Raises:
            TypeError: If coefficient fields are incompatible.
            ValueError: If ambient dimensions differ or `other.codomain` is not contained in `self.domain`.
        """
        if not _fields_compatible(other.codomain.ring.field, self.domain.ring.field):
            raise TypeError(
                f'Cannot compose PolynomialMaps over incompatible fields: '
                f'{other.codomain.ring.field!r} vs {self.domain.ring.field!r}.'
            )
        if other.codomain.ambient_dimension != self.domain.ambient_dimension:
            raise ValueError(
                'Cannot compose PolynomialMaps: codomain of inner map does not match domain of outer map.'
            )
        if not all(other.codomain.ideal.contains(g) for g in self.domain.ideal.basis):
            raise ValueError(
                'Cannot compose PolynomialMaps: codomain of inner map is not contained in domain of outer map.'
            )
        composed_comps = tuple(other.pullback(comp) for comp in self._components)
        return PolynomialMap(other.domain, self.codomain, composed_comps, verify_well_defined=True)


def syzygy_variety(
    ring: MultivariatePolynomialAlgebra[V],
    invariant_polys: Sequence[SparseMPoly[V]],
) -> AffineVariety[V]:
    r"""Compute the GIT quotient / syzygy variety $V // G \subseteq k^m$ of invariant polynomials.

    Constructs the tag-variable ideal
    $\langle y_1 - \pi_1(x), \dots, y_m - \pi_m(x) \rangle \triangleleft k[x_1, \dots, x_n, y_1, \dots, y_m]$
    and eliminates $x_1, \dots, x_n$ via a `lex` Gröbner basis to return the variety of
    algebraic relations (syzygies) $I_{\text{syz}} \triangleleft k[y_1, \dots, y_m]$.

    Args:
        ring: Ambient polynomial ring $k[x_1, \dots, x_n]$ of the invariants.
        invariant_polys: Non-empty sequence of invariant polynomials $\pi_1, \dots, \pi_m \in k[X]$.

    Raises:
        ValueError: If `invariant_polys` is empty.
    """
    m = len(invariant_polys)
    if m < 1:
        raise ValueError('syzygy_variety requires at least one invariant polynomial.')
    n = ring.n_vars
    ext_ring = MultivariatePolynomialAlgebra(ring.field, n + m, order='lex')

    tag_gens: list[SparseMPoly[V]] = []
    for idx, inv_poly in enumerate(invariant_polys):
        yj = ext_ring.gen(n + idx)
        lifted_inv = {(*mon, *(0,) * m): coeff for mon, coeff in ring.clean(inv_poly).items()}
        tag_gens.append(ext_ring.sub(yj, lifted_inv))

    lex_gb = groebner_basis(ext_ring, tag_gens)
    elim_gens: list[SparseMPoly[V]] = [
        {mon[n:]: coeff for mon, coeff in poly.items()}
        for poly in lex_gb
        if all(all(mon[i] == 0 for i in range(n)) for mon in poly)
    ]
    target_ring = MultivariatePolynomialAlgebra(ring.field, m, order=ring.order)
    return AffineVariety(target_ring, elim_gens)


def plucker_grassmannian_variety(
    field: Field[V],
    k_subspace: int,
    n_ambient: int,
) -> AffineVariety[V]:
    r"""Construct the affine cone over the Grassmannian $\operatorname{Gr}(k, n)$ cut out by Plücker relations.

    Ambient coordinates correspond to the $\binom{n}{k}$ sorted $k$-subsets
    $I \subset \{0, \dots, n-1\}$ in lexicographic order. For every $(k-1)$-subset $I$
    and $(k+1)$-subset $J$, imposes the quadratic Grassmann-Plücker identity:
    $$\sum_{r=0}^{k} (-1)^r \operatorname{sgn}(I, j_r)\,
    p_{\operatorname{sort}(I \cup \{j_r\})} p_{J \setminus \{j_r\}} = 0$$

    Args:
        field: Exact coefficient field $k$ (including $\mathbb{Q}$, $\mathbb{F}_p$, and $\mathrm{GF}(p^m)$).
        k_subspace: Subspace dimension $k$ ($1 \le k < n$).
        n_ambient: Ambient vector-space dimension $n$.

    Raises:
        ValueError: If `not (1 <= k_subspace < n_ambient)`.
    """
    if not (1 <= k_subspace < n_ambient):
        raise ValueError(
            f'Grassmannian Gr(k, n) requires 1 <= k < n, got k={k_subspace}, n={n_ambient}.'
        )
    subsets = list(itertools.combinations(range(n_ambient), k_subspace))
    sub_idx = {s: idx for idx, s in enumerate(subsets)}
    ring = MultivariatePolynomialAlgebra(field, len(subsets), order='grevlex')

    one = field.one
    neg_one = field.neg(one)
    relations: list[SparseMPoly[V]] = []
    seen_monic: set[tuple[tuple[Monomial, Any], ...]] = set()

    for left_i in itertools.combinations(range(n_ambient), k_subspace - 1):
        left_set = set(left_i)
        for right_j in itertools.combinations(range(n_ambient), k_subspace + 1):
            poly: SparseMPoly[V] = ring.zero
            for r, elem in enumerate(right_j):
                if elem in left_set:
                    continue
                inversions = sum(1 for x in left_i if x > elem)
                sign_parity = (r + inversions) % 2
                coeff = neg_one if sign_parity else one

                merged = tuple(sorted((*left_i, elem)))
                reduced_j = (*right_j[:r], *right_j[r + 1 :])
                term = ring.smul(coeff, ring.mul(ring.gen(sub_idx[merged]), ring.gen(sub_idx[reduced_j])))
                poly = ring.add(poly, term)

            if poly:
                monic = ring.make_monic(poly)
                sig = tuple((m, _freeze_coeff(c)) for m, c in sorted(monic.items()))
                if sig not in seen_monic:
                    seen_monic.add(sig)
                    relations.append(monic)

    return AffineVariety(ring, relations)


def _symbolic_det(
    ring: MultivariatePolynomialAlgebra[V],
    mat: list[list[SparseMPoly[V]]],
    reduce_fn: Callable[[SparseMPoly[V]], SparseMPoly[V]] | None,
) -> SparseMPoly[V]:
    """Compute exact symbolic determinant of a small square matrix of polynomials via cofactor expansion."""
    size = len(mat)
    if size == 0:
        return reduce_fn(ring.one) if reduce_fn is not None else ring.one
    if size == 1:
        return reduce_fn(mat[0][0]) if reduce_fn is not None else mat[0][0]
    if size == 2:
        ad = ring.mul(mat[0][0], mat[1][1])
        bc = ring.mul(mat[0][1], mat[1][0])
        res = ring.sub(ad, bc)
        return reduce_fn(res) if reduce_fn is not None else res

    acc: SparseMPoly[V] = ring.zero
    for col in range(size):
        entry = mat[0][col]
        if not entry:
            continue
        submat = [row[:col] + row[col + 1 :] for row in mat[1:]]
        minor = _symbolic_det(ring, submat, reduce_fn)
        term = ring.mul(entry, minor)
        acc = ring.add(acc, term) if col % 2 == 0 else ring.sub(acc, term)
    return reduce_fn(acc) if reduce_fn is not None else acc


class CoordinateHopfAlgebra(HopfAlgebra[V, SparseMPoly[V]], LawAssociative, LawCommutative):
    r"""Coordinate Hopf Algebra $k[G] = k[x_{11}, \dots, x_{nn}] / I(G)$ of an affine algebraic matrix group.

    Algebraic Signature:
        $\langle k, k[G], \cdot_s, \emptyset, +, -, \{0: 1\}, \cdot, \Delta, \epsilon, S \rangle$

    Carrier:
        Canonical reduced polynomials `SparseMPoly[V]` in `group_variety.coordinate_ring`
        for a closed algebraic subgroup $G \subseteq \operatorname{GL}_n(k)$ in which
        $\det(X)$ is a polynomial unit in $k[G]$ (such as $\operatorname{SL}_n(k)$,
        $\operatorname{SO}_n(k)$, $\operatorname{O}_n(k)$, or unipotent subgroups).

    Operations:
        - Ring / Algebra operations (`zero`, `one`, `add`, `neg`, `sub`, `mul`, `smul`) on $k[G]$.
        - Comultiplication $\Delta(x_{ij}) = \sum_{k=0}^{n-1} x_{ik} \otimes x_{kj}$ (dual to matrix product).
        - Counit $\epsilon(x_{ij}) = \delta_{ij}$ (dual to identity matrix $I_n \in G$).
        - Antipode $S(X) = \det(X)^{-1} \operatorname{adj}(X) \pmod{I(G)}$ (dual to matrix inversion).

    Properties:
        Satisfies `HopfAlgebra`, `Bialgebra`, `Coalgebra`, `Algebra`, and `CommRing`.
        Validates at construction that $I_n \in G$, $\det(X) \in k[G]^\times$, and that $I(G)$
        is closed under matrix multiplication ($\Delta(I(G)) = 0$) and matrix inversion ($S(I(G)) = 0$).

    Args:
        n_dim: Matrix dimension $n \ge 1$ ($G \subseteq \operatorname{GL}_n(k)$).
        group_variety: Affine variety $G \subseteq \mathbb{A}^{n^2}$ with row-major coordinates $x_{ij}$.

    Raises:
        ValueError: If `n_dim < 1`, ambient dimension is not $n^2$, $I_n \notin G$,
            $\det(X) \notin k[G]^\times$, or `group_variety` is not closed under
            matrix multiplication or inversion.
    """

    def __init__(self, n_dim: int, group_variety: AffineVariety[V]) -> None:
        if n_dim < 1:
            raise ValueError(f'Matrix group dimension n_dim must be >= 1, got {n_dim}.')
        if group_variety.ambient_dimension != n_dim * n_dim:
            raise ValueError(
                f'CoordinateHopfAlgebra of n_dim={n_dim} expects ambient dimension '
                f'{n_dim * n_dim}, got {group_variety.ambient_dimension}.'
            )
        self.n_dim: int = n_dim
        self.group_variety: AffineVariety[V] = group_variety
        self.ring: MultivariatePolynomialAlgebra[V] = group_variety.ring
        self.field: Field[V] = self.ring.field
        self.coordinate_ring = group_variety.coordinate_ring

        # 1. Verify identity matrix I_n lies on G
        self._identity_point: tuple[V, ...] = tuple(
            self.field.one if r == c else self.field.zero
            for r in range(n_dim)
            for c in range(n_dim)
        )
        if not group_variety.contains_point(self._identity_point):
            raise ValueError('group_variety does not contain the identity matrix I_n.')

        # 2. Precompute antipode images S(x_{ij}) = (X^{-1})_{ij} mod I(G)
        reduce_fn = group_variety.ideal.reduce
        x_mat: list[list[SparseMPoly[V]]] = [
            [reduce_fn(self.ring.gen(r * n_dim + c)) for c in range(n_dim)]
            for r in range(n_dim)
        ]
        det_poly = _symbolic_det(self.ring, x_mat, reduce_fn)
        det_inv = coordinate_ring_unit_inverse(group_variety, det_poly)
        if det_inv is None:
            raise ValueError(
                'det(X) is not a unit in k[G]; group_variety is not a closed subgroup of GL_n.'
            )

        s_images: list[SparseMPoly[V]] = []
        for r in range(n_dim):
            for c in range(n_dim):
                # Entry (r, c) of adjugate is (-1)^(r+c) * minor(c, r)
                submat = [
                    row[:r] + row[r + 1 :]
                    for row_idx, row in enumerate(x_mat)
                    if row_idx != c
                ]
                minor = _symbolic_det(self.ring, submat, reduce_fn)
                cofactor = self.ring.neg(minor) if (r + c) % 2 else minor
                s_entry = reduce_fn(self.ring.mul(det_inv, cofactor))
                s_images.append(s_entry)
        self._antipode_images: tuple[SparseMPoly[V], ...] = tuple(s_images)

        # 3. Precompute generator coproducts in tensor dict form
        self._gen_coproducts: tuple[dict[tuple[Monomial, Monomial], V], ...] = tuple(
            self._build_generator_tensor(idx // n_dim, idx % n_dim)
            for idx in range(n_dim * n_dim)
        )

        # 4. Validate exact algebraic group closure: Delta(I(G)) == 0 and S(I(G)) == 0
        for gen in group_variety.ideal.basis:
            if self._coproduct_raw(gen):
                raise ValueError(
                    'group_variety is not closed under matrix multiplication: '
                    f'Delta({gen!r}) is non-zero in k[G] (x) k[G].'
                )
            if _substitute_poly(self.ring, gen, self._antipode_images, reduce_fn=reduce_fn):
                raise ValueError(
                    'group_variety is not closed under matrix inversion: '
                    f'S({gen!r}) is non-zero in k[G].'
                )

    @property
    def is_associative(self) -> Literal[True]:
        return True

    @property
    def is_commutative(self) -> Literal[True]:
        return True

    def _build_generator_tensor(self, row: int, col: int) -> dict[tuple[Monomial, Monomial], V]:
        n = self.n_dim
        reduce_fn = self.group_variety.ideal.reduce
        f_add = self.field.add
        f_mul = self.field.mul
        is_zero = self.field.is_zero
        tensor: dict[tuple[Monomial, Monomial], V] = {}
        for k in range(n):
            left = reduce_fn(self.ring.gen(row * n + k))
            right = reduce_fn(self.ring.gen(k * n + col))
            for m1, c1 in left.items():
                for m2, c2 in right.items():
                    key = (m1, m2)
                    val = f_add(tensor.get(key, self.field.zero), f_mul(c1, c2))
                    if is_zero(val):
                        tensor.pop(key, None)
                    else:
                        tensor[key] = val
        return tensor

    def _tensor_mul(
        self,
        t1: dict[tuple[Monomial, Monomial], V],
        t2: dict[tuple[Monomial, Monomial], V],
    ) -> dict[tuple[Monomial, Monomial], V]:
        """Multiply two reduced tensor elements in k[G] (x) k[G]."""
        if not t1 or not t2:
            return {}
        reduce_fn = self.group_variety.ideal.reduce
        f_mul = self.field.mul
        f_add = self.field.add
        is_zero = self.field.is_zero
        one = self.field.one
        red_cache: dict[Monomial, SparseMPoly[V]] = {}

        def _red_mon(mon: Monomial) -> SparseMPoly[V]:
            cached = red_cache.get(mon)
            if cached is None:
                cached = reduce_fn({mon: one})
                red_cache[mon] = cached
            return cached

        res: dict[tuple[Monomial, Monomial], V] = {}
        for (a1, b1), c1 in t1.items():
            for (a2, b2), c2 in t2.items():
                coeff = f_mul(c1, c2)
                if is_zero(coeff):
                    continue
                prod_a = _red_mon(monomial_add(a1, a2))
                prod_b = _red_mon(monomial_add(b1, b2))
                for ma, ca in prod_a.items():
                    c_a = f_mul(coeff, ca)
                    for mb, cb in prod_b.items():
                        val = f_mul(c_a, cb)
                        key = (ma, mb)
                        nv = f_add(res.get(key, self.field.zero), val)
                        if is_zero(nv):
                            res.pop(key, None)
                        else:
                            res[key] = nv
        return res

    def _tensor_pow(
        self,
        base: dict[tuple[Monomial, Monomial], V],
        exp: int,
    ) -> dict[tuple[Monomial, Monomial], V]:
        if exp == 0:
            return {(self.ring.zero_key, self.ring.zero_key): self.field.one}
        if exp == 1:
            return base
        res: dict[tuple[Monomial, Monomial], V] | None = None
        cur = base
        k = exp
        while k > 0:
            if k & 1:
                res = cur if res is None else self._tensor_mul(res, cur)
            k >>= 1
            if k:
                cur = self._tensor_mul(cur, cur)
        return res if res is not None else {(self.ring.zero_key, self.ring.zero_key): self.field.one}

    def _coproduct_raw(self, poly: SparseMPoly[V]) -> dict[tuple[Monomial, Monomial], V]:
        """Evaluate ambient coproduct Delta(poly) in k[G] (x) k[G] without pre-reducing poly."""
        if not poly:
            return {}
        f_add = self.field.add
        f_mul = self.field.mul
        is_zero = self.field.is_zero
        unit_tensor: dict[tuple[Monomial, Monomial], V] = {
            (self.ring.zero_key, self.ring.zero_key): self.field.one
        }
        pow_cache: dict[tuple[int, int], dict[tuple[Monomial, Monomial], V]] = {}
        result: dict[tuple[Monomial, Monomial], V] = {}

        for mon, coeff in poly.items():
            if is_zero(coeff):
                continue
            mon_tensor: dict[tuple[Monomial, Monomial], V] | None = None
            for var_idx, exp in enumerate(mon):
                if exp > 0:
                    key_p = (var_idx, exp)
                    factor = pow_cache.get(key_p)
                    if factor is None:
                        factor = self._tensor_pow(self._gen_coproducts[var_idx], exp)
                        pow_cache[key_p] = factor
                    mon_tensor = factor if mon_tensor is None else self._tensor_mul(mon_tensor, factor)
            active_tensor = unit_tensor if mon_tensor is None else mon_tensor
            for key, t_val in active_tensor.items():
                nv = f_add(result.get(key, self.field.zero), f_mul(coeff, t_val))
                if is_zero(nv):
                    result.pop(key, None)
                else:
                    result[key] = nv
        return result

    # --- Algebra / Ring Operations on k[G] ---

    @property
    def zero(self) -> SparseMPoly[V]:
        r"""Additive identity $0 \in k[G]$."""
        return self.coordinate_ring.zero

    @property
    def one(self) -> SparseMPoly[V]:
        r"""Multiplicative identity $1 \in k[G]$."""
        return self.coordinate_ring.one

    def add(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Return canonical sum $a + b \bmod I(G)$."""
        return self.coordinate_ring.add(a, b)

    def neg(self, a: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Return canonical additive inverse $-a \bmod I(G)$."""
        return self.coordinate_ring.neg(a)

    def sub(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Return canonical difference $a - b \bmod I(G)$."""
        return self.coordinate_ring.sub(a, b)

    def mul(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Return canonical product $a \cdot b \bmod I(G)$."""
        return self.coordinate_ring.mul(a, b)

    def smul(self, r: V, m: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Return canonical scalar multiple $r \cdot m \bmod I(G)$."""
        return self.group_variety.ideal.reduce(self.ring.smul(r, m))

    # --- Coalgebra & Hopf Operations on k[G] ---

    def comultiply_generator(self, row: int, col: int) -> list[tuple[SparseMPoly[V], SparseMPoly[V]]]:
        r"""Return non-zero generator coproduct terms $\Delta(x_{ij}) = \sum_{k=0}^{n-1} x_{ik} \otimes x_{kj}$.

        Args:
            row: Row index $i \in \{0, \dots, n - 1\}$.
            col: Column index $j \in \{0, \dots, n - 1\}$.

        Raises:
            IndexError: If `row` or `col` is out of range.
        """
        n = self.n_dim
        if not (0 <= row < n and 0 <= col < n):
            raise IndexError(f'Generator indices ({row}, {col}) out of range for n_dim={n}.')
        reduce_fn = self.group_variety.ideal.reduce
        pairs: list[tuple[SparseMPoly[V], SparseMPoly[V]]] = []
        for k in range(n):
            left = reduce_fn(self.ring.gen(row * n + k))
            right = reduce_fn(self.ring.gen(k * n + col))
            if left and right:
                pairs.append((left, right))
        return pairs

    def coproduct(self, c: SparseMPoly[V]) -> dict[tuple[Monomial, Monomial], V]:
        r"""Evaluate the algebra homomorphism comultiplication $\Delta: k[G] \to k[G] \otimes_k k[G]$."""
        return self._coproduct_raw(self.group_variety.ideal.reduce(c))

    def counit(self, f: SparseMPoly[V]) -> V:
        r"""Evaluate the counit $\epsilon(f) = f(I_n)$ (evaluation at the identity matrix)."""
        return self.ring.eval(self.group_variety.ideal.reduce(f), self._identity_point)

    def antipode(self, f: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Evaluate the antipode $S(f)(X) = f(X^{-1}) \pmod{I(G)}$."""
        return _substitute_poly(
            self.ring,
            self.group_variety.ideal.reduce(f),
            self._antipode_images,
            reduce_fn=self.group_variety.ideal.reduce,
        )


__all__ = [
    'CoordinateHopfAlgebra',
    'PolynomialMap',
    'plucker_grassmannian_variety',
    'syzygy_variety',
]
