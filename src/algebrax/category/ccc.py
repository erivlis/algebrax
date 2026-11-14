r"""
Cartesian & Cartesian Closed Categories (CCC) and the Curry-Howard-Lambek Correspondence.

Formalizes the flat `CartesianCategory` and `CartesianClosedCategory` protocols
composed from Layer-1 atomic categorical mixins (`HasQuiver`, `HasCatId`, `HasCompose`,
`HasTerminal`, `HasProducts`, `HasExponentials`), together with the concrete `FiniteSetCCC`
category of finite sets and total functions:
- Terminal object $\mathbf{1}$ (`terminal`)
- Binary products $A \times B$ (`product`, `proj1`, `proj2`, `pair`)
- Exponential objects $B^A = \mathrm{Hom}(A, B)$ (`exponential`, `eval_mor`)
- The Curry-Howard-Lambek adjunction isomorphism:
  $$\mathrm{curry}: \mathrm{Hom}(A \times B, C) \xrightarrow{\sim} \mathrm{Hom}(A, C^B), \qquad
  \mathrm{uncurry}: \mathrm{Hom}(A, C^B) \xrightarrow{\sim} \mathrm{Hom}(A \times B, C)$$
"""

from __future__ import annotations

import itertools
from typing import Any, Protocol, TypeVar, runtime_checkable

from algebrax.category._mixins import (
    HasCatId,
    HasCompose,
    HasExponentials,
    HasProducts,
    HasQuiver,
    HasTerminal,
)

Obj = TypeVar('Obj')
Mor = TypeVar('Mor')

FiniteObj = frozenset[Any]
FiniteMor = tuple[FiniteObj, FiniteObj, dict[Any, Any]]


@runtime_checkable
class CartesianCategory(
    HasQuiver[Obj, Mor],
    HasCatId[Obj, Mor],
    HasCompose[Mor],
    HasTerminal[Obj],
    HasProducts[Obj, Mor],
    Protocol[Obj, Mor],
):
    r"""A flat Cartesian Category $\langle \mathcal{C}, \mathbf{1}, \times \rangle$ with terminal and products."""


@runtime_checkable
class CartesianClosedCategory(
    HasQuiver[Obj, Mor],
    HasCatId[Obj, Mor],
    HasCompose[Mor],
    HasTerminal[Obj],
    HasProducts[Obj, Mor],
    HasExponentials[Obj, Mor],
    Protocol[Obj, Mor],
):
    r"""A flat Cartesian Closed Category (CCC) $\langle \mathcal{C}, \mathbf{1}, \times, (-)^A \rangle$.

    Algebraic Signature:
        $\langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{id}, \circ, \mathbf{1}, \times, \pi_1, \pi_2,
        \langle -,- \rangle, B^A, \mathrm{eval}, \mathrm{curry}, \mathrm{uncurry} \rangle$

    Axioms:
        - Category Laws: Left/Right identity and associativity of `compose`.
        - Product Universal Property: $\pi_1 \circ \langle f, g \rangle = f$ and $\pi_2 \circ \langle f, g \rangle = g$.
        - Exponential Adjunction (Beta): $\mathrm{eval} \circ (\mathrm{curry}(f) \times \mathrm{id}_B) = f$.
        - Currying Bijection (Eta): $\mathrm{uncurry}(\mathrm{curry}(f)) = f$ and
          $\mathrm{curry}(\mathrm{uncurry}(g)) = g$.
    """


class FiniteSetCCC(CartesianClosedCategory[FiniteObj, FiniteMor]):
    r"""Concrete Cartesian Closed Category $\mathbf{FinSet}$ of finite sets and total functions.

    Carrier Conventions (Unboxed):
        - Objects (`FiniteObj`): `frozenset` of hashable elements.
        - Morphisms (`FiniteMor`): Triples `(dom, cod, mapping_dict)` representing $f: \mathrm{dom} \to \mathrm{cod}$.
        - Exponential elements in $C^B$: Canonical sorted tuples of `(b, c)` pairs for total functions $B \to C$.
    """

    @property
    def terminal(self) -> FiniteObj:
        r"""Singleton terminal object $\mathbf{1} = \{()\}$."""
        return frozenset({()})

    def id(self, x: FiniteObj) -> FiniteMor:
        return (x, x, {elem: elem for elem in x})

    def source(self, f: FiniteMor) -> FiniteObj:
        return f[0]

    def target(self, f: FiniteMor) -> FiniteObj:
        return f[1]

    def compose(self, f: FiniteMor, g: FiniteMor) -> FiniteMor:
        dom_f, cod_f, map_f = f
        dom_g, cod_g, map_g = g
        if cod_f != dom_g:
            raise ValueError(f'Cannot compose morphisms: target(f)={cod_f} != source(g)={dom_g}.')
        return (dom_f, cod_g, {x: map_g[map_f[x]] for x in dom_f})

    def to_terminal(self, a: FiniteObj) -> FiniteMor:
        r"""Unique terminal morphism $!_A : A \to \mathbf{1}$."""
        term = self.terminal
        return (a, term, dict.fromkeys(a, ()))

    def product(self, a: FiniteObj, b: FiniteObj) -> FiniteObj:
        return frozenset(itertools.product(a, b))

    def proj1(self, a: FiniteObj, b: FiniteObj) -> FiniteMor:
        prod = self.product(a, b)
        return (prod, a, {pair: pair[0] for pair in prod})

    def proj2(self, a: FiniteObj, b: FiniteObj) -> FiniteMor:
        prod = self.product(a, b)
        return (prod, b, {pair: pair[1] for pair in prod})

    def pair(self, f: FiniteMor, g: FiniteMor) -> FiniteMor:
        dom_f, cod_f, map_f = f
        dom_g, cod_g, map_g = g
        if dom_f != dom_g:
            raise ValueError(f'Cannot pair morphisms with distinct domains: {dom_f} != {dom_g}.')
        prod = self.product(cod_f, cod_g)
        return (dom_f, prod, {x: (map_f[x], map_g[x]) for x in dom_f})

    def product_mor(self, f: FiniteMor, g: FiniteMor) -> FiniteMor:
        r"""Parallel product of morphisms $f \times g : A_1 \times A_2 \to B_1 \times B_2$."""
        a1, a2 = f[0], g[0]
        p1 = self.compose(self.proj1(a1, a2), f)
        p2 = self.compose(self.proj2(a1, a2), g)
        return self.pair(p1, p2)

    def exponential(self, base: FiniteObj, exp: FiniteObj) -> FiniteObj:
        r"""Internal hom $B^A$ of all total functions $A \to B$, encoded as sorted tuples of `(a, b)` pairs."""
        sorted_exp = sorted(exp, key=repr)
        if not sorted_exp:
            return frozenset({()})
        base_list = sorted(base, key=repr)
        if not base_list:
            return frozenset()
        funcs: set[tuple[tuple[Any, Any], ...]] = set()
        for images in itertools.product(base_list, repeat=len(sorted_exp)):
            funcs.add(tuple(zip(sorted_exp, images, strict=True)))
        return frozenset(funcs)

    def eval_mor(self, base: FiniteObj, exp: FiniteObj) -> FiniteMor:
        r"""Evaluation map $\mathrm{eval}_{B, A} : B^A \times A \to B$ sending $(h, a) \mapsto h(a)$."""
        exp_obj = self.exponential(base, exp)
        dom = self.product(exp_obj, exp)
        mapping: dict[Any, Any] = {}
        for h_tuple, a_val in dom:
            h_dict = dict(h_tuple)
            mapping[(h_tuple, a_val)] = h_dict[a_val]
        return (dom, base, mapping)

    def curry(self, mor: FiniteMor, a: FiniteObj, b: FiniteObj) -> FiniteMor:
        r"""Curry $f : A \times B \to C$ into $\lambda f : A \to C^B$."""
        dom, c_obj, map_f = mor
        expected_dom = self.product(a, b)
        if dom != expected_dom:
            raise ValueError(f'Morphism domain {dom} does not match A x B = {expected_dom}.')
        exp_cb = self.exponential(c_obj, b)
        sorted_b = sorted(b, key=repr)
        curried_map: dict[Any, Any] = {}
        for a_val in a:
            curried_map[a_val] = tuple((b_val, map_f[(a_val, b_val)]) for b_val in sorted_b)
        return (a, exp_cb, curried_map)

    def uncurry(self, mor: FiniteMor, a: FiniteObj, b: FiniteObj, c: FiniteObj) -> FiniteMor:
        r"""Uncurry $g : A \to C^B$ into $\mathrm{eval}_{C, B} \circ (g \times \mathrm{id}_B) : A \times B \to C$."""
        g_times_id = self.product_mor(mor, self.id(b))
        ev = self.eval_mor(c, b)
        return self.compose(g_times_id, ev)


__all__ = [
    'CartesianCategory',
    'CartesianClosedCategory',
    'FiniteMor',
    'FiniteObj',
    'FiniteSetCCC',
]
