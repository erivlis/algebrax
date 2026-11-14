r"""
Atomic operational mixin protocols for single-principle categorical capabilities.

Algebraic Signatures:
    HasQuiver:       $\langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{source}, \mathrm{target} \rangle$
    HasCatId:        $\langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{id} \rangle$
    HasCompose:      $\langle \mathrm{Hom}, \circ \rangle$
    HasMorInv:       $\langle \mathrm{Hom}, ()^{-1} \rangle$
    HasTerminal:     $\langle \mathrm{Obj}, \mathbf{1} \rangle$
    HasProducts:     $\langle \mathrm{Obj}, \mathrm{Hom}, \times, \pi_1, \pi_2, \langle -,- \rangle \rangle$
    HasExponentials: $\langle \mathrm{Obj}, \mathrm{Hom}, B^A, \mathrm{eval}, \mathrm{curry}, \mathrm{uncurry} \rangle$
    HasMapObj:       $\langle \mathrm{Obj}_{\mathcal{C}}, \mathrm{Obj}_{\mathcal{D}}, F_{\mathrm{Obj}} \rangle$
    HasMapMor:       $\langle \mathrm{Hom}_{\mathcal{C}}, \mathrm{Hom}_{\mathcal{D}}, F_{\mathrm{Mor}} \rangle$
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

Obj = TypeVar('Obj')
Mor = TypeVar('Mor')
Obj_co = TypeVar('Obj_co', covariant=True)
Mor_co = TypeVar('Mor_co', covariant=True)


@runtime_checkable
class HasQuiver(Protocol[Obj, Mor]):
    r"""Directed multigraph (quiver) capability assigning source and target objects to each morphism.

    Algebraic Signature:
        $\langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{source}, \mathrm{target} \rangle$
    """

    def source(self, f: Mor) -> Obj:
        r"""Source (domain) object $\mathrm{dom}(f)$."""
        ...

    def target(self, f: Mor) -> Obj:
        r"""Target (codomain) object $\mathrm{cod}(f)$."""
        ...


@runtime_checkable
class HasCatId(Protocol[Obj, Mor]):
    r"""Categorical identity morphism capability $\mathrm{id}_x : x \to x$.

    Algebraic Signature:
        $\langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{id} \rangle$
    """

    def id(self, x: Obj) -> Mor:
        r"""Identity morphism $\mathrm{id}_x : x \to x$."""
        ...


@runtime_checkable
class HasCompose(Protocol[Mor]):
    r"""Categorical morphism composition capability $\circ$.

    Algebraic Signature:
        $\langle \mathrm{Hom}, \circ \rangle$
    """

    def compose(self, f: Mor, g: Mor) -> Mor:
        r"""Compose morphisms $f$ and $g$."""
        ...


@runtime_checkable
class HasMorInv(Protocol[Mor]):
    r"""Groupoid morphism inversion capability $f \mapsto f^{-1}$.

    Algebraic Signature:
        $\langle \mathrm{Hom}, ()^{-1} \rangle$
    """

    def invert_path(self, path: Mor) -> Mor:
        r"""Invert a morphism $f : x \to y$ into $f^{-1} : y \to x$."""
        ...


@runtime_checkable
class HasTerminal(Protocol[Obj]):
    r"""Terminal object capability $\mathbf{1}$.

    Algebraic Signature:
        $\langle \mathrm{Obj}, \mathbf{1} \rangle$
    """

    @property
    def terminal(self) -> Obj:
        r"""Terminal object $\mathbf{1}$."""
        ...


@runtime_checkable
class HasProducts(Protocol[Obj, Mor]):
    r"""Binary Cartesian product capability $A \times B$ with universal projections and pairing.

    Algebraic Signature:
        $\langle \mathrm{Obj}, \mathrm{Hom}, \times, \pi_1, \pi_2, \langle -,- \rangle \rangle$
    """

    def product(self, a: Obj, b: Obj) -> Obj:
        r"""Binary product object $A \times B$."""
        ...

    def proj1(self, a: Obj, b: Obj) -> Mor:
        r"""First projection morphism $\pi_1 : A \times B \to A$."""
        ...

    def proj2(self, a: Obj, b: Obj) -> Mor:
        r"""Second projection morphism $\pi_2 : A \times B \to B$."""
        ...

    def pair(self, f: Mor, g: Mor) -> Mor:
        r"""Universal product pairing $\langle f, g \rangle : X \to A \times B$."""
        ...


@runtime_checkable
class HasExponentials(Protocol[Obj, Mor]):
    r"""Internal hom (exponential object $B^A$), evaluation, and currying bijection capability.

    Algebraic Signature:
        $\langle \mathrm{Obj}, \mathrm{Hom}, B^A, \mathrm{eval}, \mathrm{curry}, \mathrm{uncurry} \rangle$
    """

    def exponential(self, base: Obj, exp: Obj) -> Obj:
        r"""Exponential object $B^A$ representing the internal hom $A \Rightarrow B$."""
        ...

    def eval_mor(self, base: Obj, exp: Obj) -> Mor:
        r"""Evaluation morphism $\mathrm{eval}_{B, A} : B^A \times A \to B$."""
        ...

    def curry(self, mor: Mor, a: Obj, b: Obj) -> Mor:
        r"""Curry a morphism $f : A \times B \to C$ into $\lambda f : A \to C^B$."""
        ...

    def uncurry(self, mor: Mor, a: Obj, b: Obj, c: Obj) -> Mor:
        r"""Uncurry $g : A \to C^B$ into $\mathrm{eval} \circ (g \times \mathrm{id}_B) : A \times B \to C$."""
        ...


@runtime_checkable
class HasMapObj(Protocol[Obj, Obj_co]):
    r"""Functorial object-mapping capability $F_{\mathrm{Obj}}$.

    Algebraic Signature:
        $\langle \mathrm{Obj}_{\mathcal{C}}, \mathrm{Obj}_{\mathcal{D}}, F_{\mathrm{Obj}} \rangle$
    """

    def map_obj(self, x: Obj) -> Obj_co:
        r"""Map an object $x \in \mathrm{Obj}(\mathcal{C})$ to $F(x) \in \mathrm{Obj}(\mathcal{D})$."""
        ...


@runtime_checkable
class HasMapMor(Protocol[Mor, Mor_co]):
    r"""Functorial morphism-mapping capability $F_{\mathrm{Mor}}$.

    Algebraic Signature:
        $\langle \mathrm{Hom}_{\mathcal{C}}, \mathrm{Hom}_{\mathcal{D}}, F_{\mathrm{Mor}} \rangle$
    """

    def map_mor(self, f: Mor) -> Mor_co:
        r"""Map a morphism $f \in \mathrm{Hom}_{\mathcal{C}}(x, y)$ to $F(f)$."""
        ...


__all__ = [
    'HasCatId',
    'HasCompose',
    'HasExponentials',
    'HasMapMor',
    'HasMapObj',
    'HasMorInv',
    'HasProducts',
    'HasQuiver',
    'HasTerminal',
]
