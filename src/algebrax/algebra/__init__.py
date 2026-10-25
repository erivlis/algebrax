"""
Unified algebraic hierarchy — Lean 4 Mathlib-aligned protocols for abstract algebra.
"""

from algebrax.algebra._group import (
    AbelianGroup,
    AddCommGroup,
    AddGroup,
    CommGroup,
    Group,
    GroupAction,
)
from algebrax.algebra._helpers import (
    fold_add,
    fold_mul,
    fold_op,
    nsum,
    power,
    zpow,
    zsmul,
)
from algebrax.algebra._lattice import (
    BooleanAlgebra,
    BoundedLattice,
    DistributiveLattice,
    JoinSemilattice,
    Lattice,
    MeetSemilattice,
)
from algebrax.algebra._magma import (
    AddMagma,
    AddSemigroup,
    Band,
    Magma,
    OpMagma,
    OpSemigroup,
    Quasigroup,
    Semigroup,
)
from algebrax.algebra._monoid import (
    AddCommMonoid,
    AddMonoid,
    CommMonoid,
    CommutativeMonoid,
    Monoid,
    OpCommMonoid,
    OpMonoid,
)

__all__ = [
    'AbelianGroup',
    'AddCommGroup',
    'AddCommMonoid',
    'AddGroup',
    'AddMagma',
    'AddMonoid',
    'AddSemigroup',
    'Band',
    'BooleanAlgebra',
    'BoundedLattice',
    'CommGroup',
    'CommMonoid',
    'CommutativeMonoid',
    'DistributiveLattice',
    'Group',
    'GroupAction',
    'JoinSemilattice',
    'Lattice',
    'Magma',
    'MeetSemilattice',
    'Monoid',
    'OpCommMonoid',
    'OpMagma',
    'OpMonoid',
    'OpSemigroup',
    'Quasigroup',
    'Semigroup',
    'fold_add',
    'fold_mul',
    'fold_op',
    'nsum',
    'power',
    'zpow',
    'zsmul',
]
