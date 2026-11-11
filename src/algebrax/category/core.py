"""
Core Category Theory Protocols: Category, Functor, and OppositeCategory.

Aligned with Lean 4 Mathlib (`Mathlib.CategoryTheory.Category.Basic` and
`Mathlib.CategoryTheory.Functor.Basic`), adhering strictly to AlgebraX's
zero-overhead unboxed carrier architecture.
"""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar, runtime_checkable

Obj = TypeVar('Obj')
Mor = TypeVar('Mor')
Obj_co = TypeVar('Obj_co', covariant=True)
Mor_co = TypeVar('Mor_co', covariant=True)


@runtime_checkable
class Category(Protocol[Obj, Mor]):
    r"""A mathematical category $\mathcal{C} = \langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{id}, \circ \rangle$.

    Algebraic Signature:
        $\mathcal{C} = \langle \mathrm{Obj}(\mathcal{C}), \mathrm{Hom}_{\mathcal{C}}, \mathrm{id}, \circ \rangle$

    Operations:
        - `id(x)`: Identity morphism $\mathrm{id}_x \in \mathrm{Hom}(x, x)$.
        - `compose(f, g)`: Morphism composition $g \circ f$ ($f$ followed by $g$ in diagram order).
        - `source(f)`: Domain object $\mathrm{dom}(f)$.
        - `target(f)`: Codomain object $\mathrm{cod}(f)$.

    Axioms:
        - Left Identity: $\mathrm{compose}(f, \mathrm{id}(\mathrm{target}(f))) = f$.
        - Right Identity: $\mathrm{compose}(\mathrm{id}(\mathrm{source}(f)), f) = f$.
        - Associativity: $\mathrm{compose}(\mathrm{compose}(f, g), h) = \mathrm{compose}(f, \mathrm{compose}(g, h))$.
    """

    def id(self, x: Obj) -> Mor:
        r"""Identity morphism $\mathrm{id}_x : x \to x$."""
        ...

    def compose(self, f: Mor, g: Mor) -> Mor:
        r"""Composition of morphisms $g \circ f$ ($f$ followed by $g$)."""
        ...

    def source(self, f: Mor) -> Obj:
        r"""Source object $\mathrm{dom}(f)$."""
        ...

    def target(self, f: Mor) -> Obj:
        r"""Target object $\mathrm{cod}(f)$."""
        ...


@runtime_checkable
class Functor(Protocol[Obj, Mor, Obj_co, Mor_co]):
    r"""A covariant functor $F : \mathcal{C} \to \mathcal{D}$ between categories.

    Algebraic Signature:
        $F = \langle F_{\mathrm{Obj}}: \mathrm{Obj}(\mathcal{C}) \to \mathrm{Obj}(\mathcal{D}),
        \; F_{\mathrm{Mor}}: \mathrm{Hom}_{\mathcal{C}} \to \mathrm{Hom}_{\mathcal{D}} \rangle$

    Axioms:
        - Identity Preservation: $F(\mathrm{id}_x) = \mathrm{id}_{F(x)}$.
        - Composition Preservation: $F(g \circ_{\mathcal{C}} f) = F(g) \circ_{\mathcal{D}} F(f)$.
    """

    def map_obj(self, x: Obj) -> Obj_co:
        r"""Map an object $x \in \mathrm{Obj}(\mathcal{C})$ to $F(x) \in \mathrm{Obj}(\mathcal{D})$."""
        ...

    def map_mor(self, f: Mor) -> Mor_co:
        r"""Map a morphism $f \in \mathrm{Hom}_{\mathcal{C}}(x, y)$ to $F(f)$."""
        ...


class OppositeCategory(Category[Obj, Mor], Generic[Obj, Mor]):
    r"""The categorical dual (opposite category) $\mathcal{C}^{\mathrm{op}}$ of a category $\mathcal{C}$.

    Reverses the direction of all morphisms without boxing carrier elements:
        - $\mathrm{source}_{\mathcal{C}^{\mathrm{op}}}(f) = \mathrm{target}_{\mathcal{C}}(f)$
        - $\mathrm{target}_{\mathcal{C}^{\mathrm{op}}}(f) = \mathrm{source}_{\mathcal{C}}(f)$
        - $\mathrm{compose}_{\mathcal{C}^{\mathrm{op}}}(f, g) = \mathrm{compose}_{\mathcal{C}}(g, f)$
    """

    def __init__(self, base: Category[Obj, Mor]) -> None:
        self._base = base

    @property
    def base(self) -> Category[Obj, Mor]:
        """The underlying primal category."""
        return self._base

    def id(self, x: Obj) -> Mor:
        return self._base.id(x)

    def compose(self, f: Mor, g: Mor) -> Mor:
        return self._base.compose(g, f)

    def source(self, f: Mor) -> Obj:
        return self._base.target(f)

    def target(self, f: Mor) -> Obj:
        return self._base.source(f)

    def opposite(self) -> Category[Obj, Mor]:
        r"""Involution $(\mathcal{C}^{\mathrm{op}})^{\mathrm{op}} = \mathcal{C}$."""
        return self._base


__all__ = [
    'Category',
    'Functor',
    'OppositeCategory',
]
