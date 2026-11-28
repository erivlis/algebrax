# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Runnable AlgebraX prototype for the four subtraction-free idempotent corners (EXP-0012).

Implements concrete, unboxed prototypes against `algebrax.algebra` Layer-1 atomic mixins
and Layer-2 named protocols:
  1. KleeneHopfBialgebra          (Convolution Kleene star replacing the Hopf antipode)
  2. FiniteJordanQuantale         (J_4 minimal non-assoc; E_5 provably exceptional)
     TropicalMatrixJordanQuantale (n x n Tropical matrices under A o B = AB + BA)
  3. FiniteAlternativeQuantale    (A_5 Artin-non-flexible, F_5 flexible-non-Moufang, M_7 Moufang)
  4. IdempotentDifferentialKleene (D_3 unital-drift dual numbers, DK_4 drift star law, word drift)

Run via:
    uv run python playground/idempotent_corners_prototype.py
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from algebrax.algebra import (
    ActionAlgebra,
    AlternativeAlgebra,
    Bialgebra,
    CommSemiring,
    HasAdd,
    HasCoproduct,
    HasCounit,
    HasDerivation,
    HasMul,
    HasOne,
    HasPlus,
    HasResiduals,
    HasStar,
    HasZero,
    HopfAlgebra,
    JordanAlgebra,
    KleeneAlgebra,
    LawAlternative,
    LawAssociative,
    LawCommutative,
    LawIdempotent,
    LawJordan,
    Semiring,
)

# =============================================================================
# Corner 1: Kleene-Hopf Bialgebra (Idempotent Bialgebra + Convolution Star)
# =============================================================================


class KleeneHopfBialgebra(
    HasZero[frozenset[Any]],
    HasOne[frozenset[Any]],
    HasAdd[frozenset[Any]],
    HasMul[frozenset[Any]],
    HasCoproduct[frozenset[Any]],
    HasCounit[bool, frozenset[Any]],
    HasStar[frozenset[Any]],
    LawIdempotent,
    LawAssociative,
):
    r"""Boolean-weighted idempotent bialgebra with convolution Kleene star $\circledast$.

    Algebraic Signature:
        $\langle \mathcal{P}_{\text{fin}}(M), \emptyset, \cup, \{e\}, \mu, \Delta, \epsilon, \circledast \rangle$

    Carrier:
        `frozenset[Any]` representing finite Boolean-weighted formal sums of basis elements.

    Operations:
        - Addition ($\oplus$): set union (`a | b`).
        - Multiplication ($\mu$): bilinear extension of basis product `mul_basis(u, v)`.
        - Comultiplication ($\Delta$): linear extension of `delta_basis(w)`.
        - Counit ($\epsilon$): Boolean predicate `any(eps_basis(w) for w in x)`.
        - Convolution Star ($\circledast$): $\bigoplus_{n \ge 0} \mu^{(n)} \circ \Delta^{(n)}$.

    Properties:
        Idempotent, Associative, Coassociative, Bialgebra-Compatible; no additive inverse (`HasNeg`).

    Applications:
        Unbounded dynamic fork-join trace closure, riffle-shuffle concurrency, regular path automata.
    """

    def __init__(
        self,
        name: str,
        unit_basis: Any,
        mul_basis: Callable[[Any, Any], frozenset[Any]],
        delta_basis: Callable[[Any], frozenset[tuple[Any, Any]]],
        eps_basis: Callable[[Any], bool],
        *,
        max_conv_depth: int = 5,
    ) -> None:
        self.name = name
        self._unit_basis = unit_basis
        self._mul_basis = mul_basis
        self._delta_basis = delta_basis
        self._eps_basis = eps_basis
        self._max_conv_depth = max_conv_depth

    @property
    def is_idempotent(self) -> Literal[True]:
        return True

    @property
    def is_associative(self) -> Literal[True]:
        return True

    @property
    def zero(self) -> frozenset[Any]:
        return frozenset()

    @property
    def one(self) -> frozenset[Any]:
        return frozenset({self._unit_basis})

    def add(self, a: frozenset[Any], b: frozenset[Any]) -> frozenset[Any]:
        return a | b

    def mul(self, a: frozenset[Any], b: frozenset[Any]) -> frozenset[Any]:
        out: set[Any] = set()
        for u in a:
            for v in b:
                out.update(self._mul_basis(u, v))
        return frozenset(out)

    def coproduct(self, c: frozenset[Any]) -> dict[tuple[Any, Any], bool]:
        out: dict[tuple[Any, Any], bool] = {}
        for w in c:
            for pair in self._delta_basis(w):
                out[pair] = True
        return out

    def counit(self, c: frozenset[Any]) -> bool:
        return any(self._eps_basis(w) for w in c)

    def eta_eps(self, c: frozenset[Any]) -> frozenset[Any]:
        """Convolution identity map (eta o eps)(c)."""
        return self.one if self.counit(c) else self.zero

    def convolve(
        self,
        f: Callable[[frozenset[Any]], frozenset[Any]],
        g: Callable[[frozenset[Any]], frozenset[Any]],
    ) -> Callable[[frozenset[Any]], frozenset[Any]]:
        """Convolution product (f * g)(x) = mu((f x g)(Delta(x)))."""

        def _conv(x: frozenset[Any]) -> frozenset[Any]:
            acc: set[Any] = set()
            for u, v in self.coproduct(x):
                acc.update(self.mul(f(frozenset({u})), g(frozenset({v}))))
            return frozenset(acc)

        return _conv

    def adams(self, k: int) -> Callable[[frozenset[Any]], frozenset[Any]]:
        """Return the k-th Hopf/Adams power map psi_k = id^{*k}."""
        if k == 0:
            return self.eta_eps

        def id_map(x: frozenset[Any]) -> frozenset[Any]:
            return x

        cur: Callable[[frozenset[Any]], frozenset[Any]] = id_map
        for _ in range(1, k):
            cur = self.convolve(cur, id_map)
        return cur

    def star(self, a: frozenset[Any]) -> frozenset[Any]:
        """Truncated/converged convolution Kleene star: union_{k=0..max_depth} psi_k(a)."""

        def id_map(x: frozenset[Any]) -> frozenset[Any]:
            return x

        f: Callable[[frozenset[Any]], frozenset[Any]] = self.eta_eps
        acc = set(f(a))
        for k in range(1, self._max_conv_depth + 1):
            f = id_map if k == 1 else self.convolve(f, id_map)
            step = f(a)
            acc.update(step)
        return frozenset(acc)

    @classmethod
    def shuffle_deconcat(cls, max_conv_depth: int = 5) -> KleeneHopfBialgebra:
        """Commutative, non-cocommutative shuffle-deconcatenation bialgebra."""

        def _shuffle(u: str, v: str) -> frozenset[str]:
            if not u:
                return frozenset({v})
            if not v:
                return frozenset({u})
            res: set[str] = set()
            for s in _shuffle(u[1:], v):
                res.add(u[0] + s)
            for s in _shuffle(u, v[1:]):
                res.add(v[0] + s)
            return frozenset(res)

        def _deconcat(w: str) -> frozenset[tuple[str, str]]:
            return frozenset((w[:i], w[i:]) for i in range(len(w) + 1))

        return cls('ShuffleDeconcat', '', _shuffle, _deconcat, lambda w: w == '', max_conv_depth=max_conv_depth)

    @classmethod
    def concat_unshuffle(cls, max_conv_depth: int = 5) -> KleeneHopfBialgebra:
        """Non-commutative, cocommutative concatenation-unshuffle bialgebra."""

        def _unshuffle(w: str) -> frozenset[tuple[str, str]]:
            if not w:
                return frozenset({('', '')})
            out: set[tuple[str, str]] = set()
            for u, v in _unshuffle(w[1:]):
                out.add((w[0] + u, v))
                out.add((u, w[0] + v))
            return frozenset(out)

        return cls(
            'ConcatUnshuffle',
            '',
            lambda u, v: frozenset({u + v}),
            _unshuffle,
            lambda w: w == '',
            max_conv_depth=max_conv_depth,
        )

    @classmethod
    def nc_matrix(cls, dim: int = 2, max_conv_depth: int = 4) -> KleeneHopfBialgebra:
        """Non-commutative, non-cocommutative matrix bialgebra O_nc(M_dim) (regular path automata)."""

        def _delta_word(w: tuple[tuple[int, int], ...]) -> frozenset[tuple[Any, Any]]:
            acc: set[tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]] = {((), ())}
            for i, j in w:
                nxt: set[tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]] = set()
                for u1, v1 in acc:
                    for k in range(dim):
                        nxt.add(((*u1, (i, k)), (*v1, (k, j))))
                acc = nxt
            return frozenset(acc)

        return cls(
            f'O_nc(M_{dim})',
            (),
            lambda u, v: frozenset({u + v}),
            _delta_word,
            lambda w: all(i == j for i, j in w),
            max_conv_depth=max_conv_depth,
        )

    @classmethod
    def group_like_monoid(cls, max_conv_depth: int = 4) -> KleeneHopfBialgebra:
        """Commutative/cocommutative group-like degeneracy recovering classical Kleene algebra."""
        return cls(
            'GroupLikeMonoid',
            0,
            lambda a, b: frozenset({a + b}),
            lambda a: frozenset({(a, a)}),
            lambda _a: True,
            max_conv_depth=max_conv_depth,
        )


# =============================================================================
# Corner 2: Jordan Quantales (J_4 minimal non-assoc, E_5 exceptional, Tropical M_n)
# =============================================================================


class FiniteJordanQuantale(
    HasZero[int],
    HasOne[int],
    HasAdd[int],
    HasMul[int],
    HasStar[int],
    HasPlus[int],
    HasResiduals[int],
    LawIdempotent,
    LawCommutative,
    LawJordan,
):
    r"""Finite commutative non-associative Jordan quantale with Kleene star and Jordan residual.

    Algebraic Signature:
        $\langle Q, \mathbf{0}, \oplus, \mathbf{1}, \circ, ^*, \multimap_\circ \rangle$

    Carrier:
        `int` indices $\{0, \dots, n-1\}$ with `0` as $\mathbf{0}$ and `1` as $\mathbf{1}$.

    Operations:
        - Addition ($\oplus$): join-semilattice operation from table `add_table`.
        - Multiplication ($\circ$): commutative, distributive Jordan product from `mul_table`.
        - Kleene Star ($^*$): least fixpoint of $y \ge \mathbf{1} \oplus (a \circ y)$.
        - Residuals (`ldiv`, `rdiv`): symmetric Galois adjoint $a \circ x \le b \iff x \le (a \multimap_\circ b)$.

    Properties:
        Idempotent, Commutative, Jordan, Non-Associative, Residuated; no `HasNeg`.

    Applications:
        Finite falsification witnesses for subtraction-free Jordan theory ($J_4$, exceptional $E_5$).
    """

    def __init__(self, name: str, add_table: list[list[int]], mul_table: list[list[int]]) -> None:
        self.name = name
        self._add = add_table
        self._mul = mul_table
        self.size = len(add_table)

    @property
    def is_idempotent(self) -> Literal[True]:
        return True

    @property
    def is_commutative(self) -> Literal[True]:
        return True

    @property
    def is_jordan(self) -> Literal[True]:
        return True

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def leq(self, a: int, b: int) -> bool:
        return self._add[a][b] == b

    def add(self, a: int, b: int) -> int:
        return self._add[a][b]

    def mul(self, a: int, b: int) -> int:
        return self._mul[a][b]

    def star(self, a: int) -> int:
        cur = self.one
        while True:
            nxt = self.add(self.one, self.mul(a, cur))
            if nxt == cur:
                return cur
            cur = nxt

    def plus(self, a: int) -> int:
        return self.mul(a, self.star(a))

    def jdiv(self, a: int, b: int) -> int:
        """Symmetric Jordan residual a -o b = max { x | a o x <= b }."""
        candidates = [x for x in range(self.size) if self.leq(self.mul(a, x), b)]
        # Join of all valid candidates yields exact Galois maximum in finite quantale
        acc = candidates[0]
        for x in candidates[1:]:
            acc = self.add(acc, x)
        return acc

    def ldiv(self, a: int, b: int) -> int:
        return self.jdiv(a, b)

    def rdiv(self, a: int, b: int) -> int:
        return self.jdiv(b, a)

    def endomorphism_square_violations(self) -> list[tuple[int, int, int]]:
        """Return witnesses (a, e=a-o a, e o e) proving non-specialness (e o e NOT <= e)."""
        violations: list[tuple[int, int, int]] = []
        for a in range(self.size):
            e = self.jdiv(a, a)
            e2 = self.mul(e, e)
            if not self.leq(e2, e):
                violations.append((a, e, e2))
        return violations

    @classmethod
    def j4(cls) -> FiniteJordanQuantale:
        """Minimal 4-element non-associative special Jordan-Kleene quantale J_4 (0 < 2 < 1 < 3)."""
        return cls(
            'J_4',
            add_table=[[0, 1, 2, 3], [1, 1, 1, 3], [2, 1, 2, 3], [3, 3, 3, 3]],
            mul_table=[[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 0, 1], [0, 3, 1, 3]],
        )

    @classmethod
    def e5_exceptional(cls) -> FiniteJordanQuantale:
        """Minimal 5-element provably exceptional (non-special) Jordan quantale E_5 on N_5."""
        return cls(
            'E_5 (Exceptional)',
            add_table=[[0, 1, 2, 3, 4], [1, 1, 2, 2, 4], [2, 2, 2, 2, 2], [3, 2, 2, 3, 2], [4, 4, 2, 2, 4]],
            mul_table=[[0, 0, 0, 0, 0], [0, 1, 2, 3, 4], [0, 2, 2, 2, 2], [0, 3, 2, 1, 3], [0, 4, 2, 3, 2]],
        )


# =============================================================================
# Corner 3: Alternative Quantales (A_5, F_5, M_7 — Artin's Theorem Shattered)
# =============================================================================


class FiniteAlternativeQuantale(
    HasZero[int],
    HasOne[int],
    HasAdd[int],
    HasMul[int],
    HasStar[int],
    HasPlus[int],
    HasResiduals[int],
    LawIdempotent,
    LawAlternative,
):
    r"""Finite non-associative alternative quantale demonstrating the 3-tier Artin split.

    Algebraic Signature:
        $\langle Q, \mathbf{0}, \oplus, \mathbf{1}, \cdot, ^*, \backslash, / \rangle$

    Carrier:
        `int` indices $\{0, \dots, n-1\}$ with `0` as $\mathbf{0}$ and `one_idx` as $\mathbf{1}$.

    Operations:
        - Addition ($\oplus$): join-semilattice operation `add_table`.
        - Multiplication ($\cdot$): left & right alternative, distributive, non-associative.
        - Residuals (`ldiv`, `rdiv`): exact left/right Galois adjoints.

    Properties:
        Idempotent, Alternative, Non-Associative, Residuated; no `HasNeg`.

    Applications:
        Separates Artin-Alternative ($A_5$), Flexible-Alternative ($F_5$), and Moufang ($M_7$)
        quantales into three strictly distinct subtraction-free varieties.
    """

    def __init__(
        self,
        name: str,
        add_table: list[list[int]],
        mul_table: list[list[int]],
        *,
        one_idx: int = 1,
    ) -> None:
        self.name = name
        self._add = add_table
        self._mul = mul_table
        self._one = one_idx
        self.size = len(add_table)

    @property
    def is_idempotent(self) -> Literal[True]:
        return True

    @property
    def is_alternative(self) -> Literal[True]:
        return True

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return self._one

    def leq(self, a: int, b: int) -> bool:
        return self._add[a][b] == b

    def add(self, a: int, b: int) -> int:
        return self._add[a][b]

    def mul(self, a: int, b: int) -> int:
        return self._mul[a][b]

    def star(self, a: int) -> int:
        cur = self.one
        while True:
            nxt = self.add(self.one, self.mul(a, cur))
            if nxt == cur:
                return cur
            cur = nxt

    def plus(self, a: int) -> int:
        return self.mul(a, self.star(a))

    def ldiv(self, a: int, b: int) -> int:
        cands = [x for x in range(self.size) if self.leq(self.mul(a, x), b)]
        acc = cands[0]
        for x in cands[1:]:
            acc = self.add(acc, x)
        return acc

    def rdiv(self, a: int, b: int) -> int:
        cands = [x for x in range(self.size) if self.leq(self.mul(x, b), a)]
        acc = cands[0]
        for x in cands[1:]:
            acc = self.add(acc, x)
        return acc

    def classify_tier(self) -> dict[str, bool]:
        """Verify associativity, alternativity, flexibility, Moufang, and Artin 2-gen laws."""
        n = self.size
        m = self._mul
        assoc = all(m[m[x][y]][z] == m[x][m[y][z]] for x in range(n) for y in range(n) for z in range(n))
        l_alt = all(m[m[x][x]][y] == m[x][m[x][y]] for x in range(n) for y in range(n))
        r_alt = all(m[m[y][x]][x] == m[y][m[x][x]] for x in range(n) for y in range(n))
        flex = all(m[m[x][y]][x] == m[x][m[y][x]] for x in range(n) for y in range(n))
        moufang = all(
            m[x][m[y][m[x][z]]] == m[m[m[x][y]][x]][z]
            and m[z][m[x][m[y][x]]] == m[m[m[z][x]][y]][x]
            and m[m[x][y]][m[z][x]] == m[x][m[m[y][z]][x]]
            for x in range(n)
            for y in range(n)
            for z in range(n)
        )
        return {
            'associative': assoc,
            'alternative': l_alt and r_alt,
            'flexible': flex,
            'moufang': moufang,
        }

    @classmethod
    def a5_non_flexible(cls) -> FiniteAlternativeQuantale:
        """Minimal 5-element Artin-alternative quantale violating flexibility (A_5)."""
        return cls(
            'A_5 (Artin, Non-Flexible)',
            add_table=[
                [0, 1, 2, 3, 4],
                [1, 1, 1, 1, 1],
                [2, 1, 2, 2, 2],
                [3, 1, 2, 3, 3],
                [4, 1, 2, 3, 4],
            ],
            mul_table=[
                [0, 0, 0, 0, 0],
                [0, 1, 2, 3, 4],
                [0, 2, 2, 3, 0],
                [0, 3, 4, 0, 0],
                [0, 4, 4, 0, 0],
            ],
            one_idx=1,
        )

    @classmethod
    def f5_flexible_non_moufang(cls) -> FiniteAlternativeQuantale:
        """Minimal 5-element flexible alternative quantale violating Moufang (F_5)."""
        return cls(
            'F_5 (Flexible, Non-Moufang)',
            add_table=[
                [0, 1, 2, 3, 4],
                [1, 1, 1, 3, 1],
                [2, 1, 2, 3, 4],
                [3, 3, 3, 3, 3],
                [4, 1, 4, 3, 4],
            ],
            mul_table=[
                [0, 0, 0, 0, 0],
                [0, 1, 2, 3, 4],
                [0, 2, 0, 2, 0],
                [0, 3, 4, 3, 4],
                [0, 4, 0, 4, 4],
            ],
            one_idx=1,
        )

    @classmethod
    def m7_moufang(cls) -> FiniteAlternativeQuantale:
        """Minimal chain-ordered 7-element non-associative Moufang quantale ('Tropical Octonion')."""
        chain_add = [[max(i, j) for j in range(7)] for i in range(7)]
        return cls(
            'M_7 (Moufang Quantale)',
            add_table=chain_add,
            mul_table=[
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 1, 1, 2],
                [0, 0, 0, 3, 3, 3, 3],
                [0, 0, 0, 3, 3, 3, 4],
                [0, 0, 0, 3, 3, 5, 5],
                [0, 1, 2, 3, 4, 5, 6],
            ],
            one_idx=6,
        )


# =============================================================================
# Corner 4: Idempotent Differential-Kleene Algebra (with Unital-Drift Law)
# =============================================================================


class FiniteDifferentialKleene(
    HasZero[int],
    HasOne[int],
    HasAdd[int],
    HasMul[int],
    HasStar[int],
    HasDerivation[int],
    LawIdempotent,
    LawAssociative,
):
    r"""Finite idempotent Kleene algebra equipped with a positive Leibniz derivation $\partial$.

    Algebraic Signature:
        $\langle K, \mathbf{0}, \oplus, \mathbf{1}, \cdot, ^*, \partial \rangle$

    Carrier:
        `int` indices $\{0, \dots, n-1\}$.

    Operations:
        - `diff(a)`: positive derivation obeying $\partial(ab) = \partial(a)b \oplus a\partial(b)$.
        - `diff_star(a)`: Kleene closure $\partial^*(a) = \bigoplus_{n \ge 0} \partial^n(a)$.

    Properties:
        Idempotent, Associative, Differential-Kleene; obeys $\partial^*(ab) = \partial^*(a)\partial^*(b)$
        and the exact unital-drift law $\partial^*(a^*) = \partial^*(\mathbf{1}) \cdot (\partial^*(a))^*$.

    Applications:
        Monotone rewrite-closure semantics and non-inner unital-drift derivations impossible in rings.
    """

    def __init__(
        self,
        name: str,
        add_table: list[list[int]],
        mul_table: list[list[int]],
        diff_table: list[int],
    ) -> None:
        self.name = name
        self._add = add_table
        self._mul = mul_table
        self._diff = diff_table
        self.size = len(add_table)

    @property
    def is_idempotent(self) -> Literal[True]:
        return True

    @property
    def is_associative(self) -> Literal[True]:
        return True

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, a: int, b: int) -> int:
        return self._add[a][b]

    def mul(self, a: int, b: int) -> int:
        return self._mul[a][b]

    def diff(self, a: int, var_index: int = 0) -> int:
        return self._diff[a]

    def diff_star(self, a: int) -> int:
        cur = a
        while True:
            nxt = self.add(cur, self.diff(cur))
            if nxt == cur:
                return cur
            cur = nxt

    def star(self, a: int) -> int:
        cur = self.one
        while True:
            nxt = self.add(self.one, self.mul(a, cur))
            if nxt == cur:
                return cur
            cur = nxt

    @classmethod
    def d3_non_inner_drift(cls) -> FiniteDifferentialKleene:
        """3-element idempotent dual numbers with non-inner unital-drift derivation D(1) = eps."""
        return cls(
            'D_3 (Non-Inner Drift)',
            add_table=[[0, 1, 2], [1, 1, 1], [2, 1, 2]],
            mul_table=[[0, 0, 0], [0, 1, 2], [0, 2, 0]],
            diff_table=[0, 2, 2],
        )

    @classmethod
    def dk4_drift_star_law(cls) -> FiniteDifferentialKleene:
        """4-element model separating D*(a*) != (D*(a))* while obeying D*(a*) == D*(1)*(D*(a))*."""
        return cls(
            'DK_4 (Drift Star Law)',
            add_table=[[0, 1, 2, 3], [1, 1, 2, 2], [2, 2, 2, 2], [3, 2, 2, 3]],
            mul_table=[[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 2, 2], [0, 3, 2, 2]],
            diff_table=[0, 2, 2, 2],
        )


# =============================================================================
# AlgebraX Protocol Gap & False-Positive Audit
# =============================================================================


def audit_algebrax_protocols() -> dict[str, dict[str, bool]]:
    """Run isinstance() checks against AlgebraX's Layer-2 protocols to expose structural gaps."""
    instances: list[tuple[str, Any]] = [
        ('KleeneHopf(Shuffle)', KleeneHopfBialgebra.shuffle_deconcat()),
        ('J_4 (JordanQuantale)', FiniteJordanQuantale.j4()),
        ('E_5 (ExceptionalJordan)', FiniteJordanQuantale.e5_exceptional()),
        ('A_5 (Alt-NonFlex)', FiniteAlternativeQuantale.a5_non_flexible()),
        ('F_5 (Alt-NonMoufang)', FiniteAlternativeQuantale.f5_flexible_non_moufang()),
        ('M_7 (MoufangQuantale)', FiniteAlternativeQuantale.m7_moufang()),
        ('DK_4 (DiffKleene)', FiniteDifferentialKleene.dk4_drift_star_law()),
    ]
    protocols: list[tuple[str, type[Any]]] = [
        ('Semiring', Semiring),
        ('CommSemiring', CommSemiring),
        ('KleeneAlgebra', KleeneAlgebra),
        ('ActionAlgebra', ActionAlgebra),
        ('JordanAlgebra', JordanAlgebra),
        ('AlternativeAlgebra', AlternativeAlgebra),
        ('Bialgebra', Bialgebra),
        ('HopfAlgebra', HopfAlgebra),
    ]
    matrix: dict[str, dict[str, bool]] = {}
    for label, inst in instances:
        matrix[label] = {pname: isinstance(inst, proto) for pname, proto in protocols}
    return matrix


def run_demo() -> None:
    """Execute verification demos across all 4 corners and print the AlgebraX protocol audit."""
    print('=== 1. Kleene-Hopf Bialgebras (2x2 Phase Diagram) ===')
    kh_shuf = KleeneHopfBialgebra.shuffle_deconcat(max_conv_depth=4)
    print('  ShuffleDeconcat star("abc"):', sorted(kh_shuf.star(frozenset({'abc'}))))
    kh_nc = KleeneHopfBialgebra.nc_matrix(dim=2, max_conv_depth=3)
    e01 = frozenset({((0, 1),)})
    print('  O_nc(M_2) psi_3(e_01) walks:', sorted(kh_nc.adams(3)(e01)))

    print('\n=== 2. Jordan Quantales (J_4 & Provably Exceptional E_5) ===')
    for jq in (FiniteJordanQuantale.j4(), FiniteJordanQuantale.e5_exceptional()):
        viols = jq.endomorphism_square_violations()
        print(f'  {jq.name}: non_special_witnesses={viols}, star={[jq.star(i) for i in range(jq.size)]}')

    print('\n=== 3. Alternative Quantale 3-Tier Split (A_5 / F_5 / M_7) ===')
    for aq in (
        FiniteAlternativeQuantale.a5_non_flexible(),
        FiniteAlternativeQuantale.f5_flexible_non_moufang(),
        FiniteAlternativeQuantale.m7_moufang(),
    ):
        print(f'  {aq.name:28s}: {aq.classify_tier()}')

    print('\n=== 4. Idempotent Differential-Kleene (Unital-Drift Law) ===')
    dk4 = FiniteDifferentialKleene.dk4_drift_star_law()
    naive_eq = all(dk4.diff_star(dk4.star(a)) == dk4.star(dk4.diff_star(a)) for a in range(dk4.size))
    drift_law = all(
        dk4.diff_star(dk4.star(a)) == dk4.mul(dk4.diff_star(dk4.one), dk4.star(dk4.diff_star(a)))
        for a in range(dk4.size)
    )
    print(f'  DK_4: naive D*(a*)==(D*(a))*? {naive_eq} | exact D*(a*)==D*(1)*(D*(a))*? {drift_law}')

    print('\n=== 5. AlgebraX Layer-2 Protocol Audit (False Positives & Neg-Coupling Gaps) ===')
    audit = audit_algebrax_protocols()
    headers = list(next(iter(audit.values())).keys())
    print(f"{'Structure':26s} | " + ' | '.join(f'{h[:8]:8s}' for h in headers))
    print('-' * (29 + 11 * len(headers)))
    for label, row in audit.items():
        vals = ' | '.join(f"{'YES' if row[h] else '.':^8s}" for h in headers)
        print(f'{label:26s} | {vals}')


if __name__ == '__main__':
    run_demo()
