r"""
Atomic operational mixin protocols for single-principle algebraic capabilities.

Algebraic Signatures:
    HasZero:       $\langle V, \mathbf{0} \rangle$
    HasZeroPred:   $\langle V, \operatorname{is\_zero} \rangle$
    HasOne:        $\langle V, \mathbf{1} \rangle$
    HasAdd:        $\langle V, + \rangle$
    HasNeg:        $\langle V, - \rangle$
    HasMul:        $\langle V, \cdot \rangle$
    HasInv:        $\langle V, ^{-1} \rangle$
    HasScale:      $\langle R, M, \cdot_s \rangle$
    HasStar:       $\langle V, ^* \rangle$
    HasJoin:       $\langle V, \vee \rangle$
    HasMeet:       $\langle V, \wedge \rangle$
    HasBounds:     $\langle V, \bot, \top \rangle$
    HasComplement: $\langle V, \neg \rangle$
    HasOp:         $\langle V, \operatorname{op} \rangle$
    HasIdentity:   $\langle V, \operatorname{identity} \rangle$
    HasBracket:    $\langle V, [\cdot, \cdot] \rangle$
"""

from typing import Protocol, TypeVar, runtime_checkable

V = TypeVar('V')
R = TypeVar('R')
M = TypeVar('M')


@runtime_checkable
class HasZero(Protocol[V]):
    r"""Additive neutral element $\mathbf{0}$.

    Algebraic Signature:
        $\langle V, \mathbf{0} \rangle$
    """

    @property
    def zero(self) -> V: ...


@runtime_checkable
class HasZeroPred(Protocol[V]):
    r"""Zero-divisor predicate `is_zero(a)` testing whether an element equals $\mathbf{0}$.

    Algebraic Signature:
        $\langle V, \operatorname{is\_zero} \rangle$
    """

    def is_zero(self, a: V) -> bool:
        """Return True if element is the additive zero."""
        return a == self.zero  # type: ignore[attr-defined]


@runtime_checkable
class HasOne(Protocol[V]):
    r"""Multiplicative neutral element $\mathbf{1}$.

    Algebraic Signature:
        $\langle V, \mathbf{1} \rangle$
    """

    @property
    def one(self) -> V: ...


@runtime_checkable
class HasAdd(Protocol[V]):
    r"""Binary addition operation $+: V \times V \to V$.

    Algebraic Signature:
        $\langle V, + \rangle$
    """

    def add(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasNeg(Protocol[V]):
    r"""Additive inverse $-: V \to V$ and derived subtraction $a - b = a + (-b)$.

    Algebraic Signature:
        $\langle V, - \rangle$
    """

    def neg(self, a: V) -> V: ...

    def sub(self, a: V, b: V) -> V:
        """Difference a - b = a + neg(b)."""
        return self.add(a, self.neg(b))  # type: ignore[attr-defined]


@runtime_checkable
class HasMul(Protocol[V]):
    r"""Binary multiplication operation $\cdot: V \times V \to V$.

    Algebraic Signature:
        $\langle V, \cdot \rangle$
    """

    def mul(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasInv(Protocol[V]):
    r"""Multiplicative inverse $^{-1}: V \to V$ and derived quotient $a / b = a \cdot b^{-1}$.

    Algebraic Signature:
        $\langle V, ^{-1} \rangle$
    """

    def inv(self, a: V) -> V: ...

    def div(self, a: V, b: V) -> V:
        """Quotient a / b = a * inv(b)."""
        return self.mul(a, self.inv(b))  # type: ignore[attr-defined]


@runtime_checkable
class HasScale(Protocol[R, M]):
    r"""External scalar multiplication $\cdot_s: R \times M \to M$.

    Algebraic Signature:
        $\langle R, M, \cdot_s \rangle$
    """

    def smul(self, r: R, m: M) -> M: ...



@runtime_checkable
class HasStar(Protocol[V]):
    r"""Kleene closure operation $a^* = \mathbf{1} \oplus a \oplus a^2 \oplus \cdots$.

    Note: Denotes idempotent/convergent Kleene star closure in semirings and automata,
    distinct from involutive conjugate/adjoint operations ($a^\dagger$) in $^*$-algebras.

    Algebraic Signature:
        $\langle V, ^* \rangle$
    """

    def star(self, a: V) -> V: ...


@runtime_checkable
class HasJoin(Protocol[V]):
    r"""Lattice least upper bound (join) $\vee: V \times V \to V$.

    Algebraic Signature:
        $\langle V, \vee \rangle$
    """

    def join(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasMeet(Protocol[V]):
    r"""Lattice greatest lower bound (meet) $\wedge: V \times V \to V$.

    Algebraic Signature:
        $\langle V, \wedge \rangle$
    """

    def meet(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasBounds(Protocol[V]):
    r"""Lattice bottom ($\bot$) and top ($\top$) bounds.

    Algebraic Signature:
        $\langle V, \bot, \top \rangle$
    """

    @property
    def bot(self) -> V: ...

    @property
    def top(self) -> V: ...


@runtime_checkable
class HasComplement(Protocol[V]):
    r"""Unary lattice complement $\neg: V \to V$.

    Algebraic Signature:
        $\langle V, \neg \rangle$
    """

    def complement(self, a: V) -> V: ...


@runtime_checkable
class HasOp(Protocol[V]):
    r"""Domain-agnostic binary operation $\operatorname{op}: V \times V \to V$.

    Algebraic Signature:
        $\langle V, \operatorname{op} \rangle$
    """

    def op(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasIdentity(Protocol[V]):
    r"""Domain-agnostic neutral identity element.

    Algebraic Signature:
        $\langle V, \operatorname{identity} \rangle$
    """

    @property
    def identity(self) -> V: ...


@runtime_checkable
class HasBracket(Protocol[V]):
    r"""Bilinear bracket operation $[\cdot, \cdot]: V \times V \to V$.

    Algebraic Signature:
        $\langle V, [\cdot, \cdot] \rangle$
    """

    def bracket(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasContains(Protocol[V]):
    r"""Substructure membership predicate `contains(element)` ($\in$).

    Algebraic Signature:
        $\langle V, \operatorname{contains} \rangle$
    """

    def contains(self, element: V) -> bool: ...


@runtime_checkable
class HasReduce(Protocol[V]):
    r"""Canonical normal-form / coset reduction `reduce(element)` ($\bmod I$).

    Algebraic Signature:
        $\langle V, \operatorname{reduce} \rangle$
    """

    def reduce(self, element: V) -> V: ...


@runtime_checkable
class HasGenerator(Protocol[V]):
    r"""Single principal generating element `generator` ($a$ in $I = (a)$).

    Algebraic Signature:
        $\langle V, \operatorname{generator} \rangle$
    """

    @property
    def generator(self) -> V: ...

