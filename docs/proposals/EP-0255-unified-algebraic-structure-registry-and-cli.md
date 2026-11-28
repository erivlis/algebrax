---
title: "EP-0255: Unified Algebraic Structure Registry, Structure Cards & CLI Overhaul"
description: "Generalize semiring discovery into a read-only, pure-data AlgebraX structure registry (`algebrax.registry`) with falsifiable protocol/law metadata, generalized display cards, and a hardened protocol-aware CLI (`algebrax.__main__`)."
icon: lucide/library
status: accepted
---

# EP-0255: Unified Algebraic Structure Registry, Structure Cards & CLI Overhaul

| Field             | Value                                                                                                  |
|:------------------|:-------------------------------------------------------------------------------------------------------|
| **EP**            | 0255                                                                                                   |
| **Title**         | Unified Algebraic Structure Registry, Structure Cards & CLI Overhaul                                   |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                            |
| **Sponsor**       | The Grand Council                                                                                      |
| **Delegate**      | ⚖️ Noether (Symmetry), 🧩 Russell (Type Theory), ⚡ Shannon (Efficiency), 🛡️ Golem (Safety), 💡 Feynman (Clarity) & 🔬 Popper (Falsifiability) |
| **Status**        | Accepted                                                                                               |
| **Type**          | Standards Track                                                                                        |
| **Created**       | 2026-11-27                                                                                             |
| **Updated**       | 2026-11-28                                                                                             |
| **Replaces**      | —                                                                                                      |
| **Superseded-By** | —                                                                                                      |

**Prerequisites**: Runs **last** in Phase 8.5 (`EP-0250` → `EP-0251` → `EP-0252` → `EP-0253` → `EP-0254` → `EP-0255`), building on truthful `EP-0250` protocol/law witnesses, `EP-0253` hardened verifiers, and `EP-0254`'s escaped `display.py` / `RichDisplayable` foundation and decomposed `verification/` package. Owns all `src/algebrax/__main__.py` CLI hardening handed off from [`EP-0254`](EP-0254-ergonomics-state-safety-ecosystem-bridges-and-hygiene.md).

---

## Abstract

This proposal generalizes [`algebrax.semiring._registry`](../../src/algebrax/semiring/_registry.py) into a package-wide, immutable, pure-data structure catalog at **`algebrax.registry`** (`ax.registry`)—**without** introducing a nominal `Structure` base class or violating [`EP-0005`](EP-0005-universal-algebraic-protocol-architecture.md)'s Law of Flat Protocol Composition. Every built-in concrete algebraic, categorical, and geometric-variety structure provider (both classes and canonical factory families such as `so_n`, `symmetric_group`, and `dynkin_quiver`) is described by a frozen, slotted `StructureEntry` record carrying reified Layer-2 protocols, truthful `Law*` witnesses, constructor parameter contracts, cross-cutting tags, and lazy [`EP-0002`](EP-0002-mathematical-docstring-standards-and-algebraic-signatures.md) AMDS metadata. On top of this single source of truth, the proposal generalizes `display.semiring_card` into a decoupled `display.structure_card`, adds a unidirectional `algebrax.verification.verify_structure` bridge, hardens `Semiring.catalog()`/`registry()` against cache-mutation state gravity via `MappingProxyType`, and replaces the brittle, semiring-only CLI in `src/algebrax/__main__.py` with a safe, protocol-aware, JSON-scriptable CLI (`catalog`, `describe`, `inspect`, `verify`) that also unlocks Phase 9–11 discovery and [`EP-0120`](EP-0120-algebraic-web-explorer.md)'s Web Explorer manifest.

---

## Motivation

AlgebraX has expanded across 24 submodules into a multi-continent mathematical library—semirings, rings, fields, finite groups, Lie algebras, Clifford algebras, non-associative algebras, coalgebras & Hopf algebras, normed spaces, categories/groupoids, quivers, and affine algebraic varieties—with tropical varieties (`EP-0222`), harmonic transforms (Phase 10), and Weyl/Ore differential algebras (Phase 11) next on the roadmap. Yet structure discovery, metadata reflection, and CLI tooling remain trapped in a semiring-only era:

1. **Fragmented & Drifting Catalogs**:
   - `src/algebrax/semiring/_registry.py` already leaks outside `algebrax.semiring` to list `CliffordAlgebra`, `GaloisField`, `PolynomialAlgebra`, and `DualNumberAlgebra`, while Lie algebras, finite groups, Hopf algebras, non-associative algebras, categories, quivers, and affine varieties have **no programmatic catalog**.
   - Three disconnected lists have already drifted out of sync: `semiring_catalog()` (33 entries), `verification/_semiring.py:get_semiring_samples()` (hardcoded 33-entry map), `tests/algebrax/test_docstrings.py` (19 hand-listed non-semiring classes), and `tests/verifications/test_axiomatic_properties.py` (stale "34 built-in semirings" references).
   - `StandardField` defines a custom docstring without an `Algebraic Signature:` line, returning `None` from `extract_algebraic_signature`, and `src/algebrax/__init__.py:29` still mentions nonexistent `so3`, `sl2`, `se3` instead of `so_n`, `sl_n`, `se_n`.
2. **State Gravity in Cached Registries**:
   - `Semiring.catalog()`, `Semiring.registry()`, `semiring_catalog()`, and `DOMAIN_TAGS` all expose **mutable `dict`s** (the first three behind `@cache`). Any accidental mutation (e.g., `.clear()` or key assignment) silently corrupts process-wide state, including `Semiring.normalize()`.
3. **Brittle, Unsafe CLI (`src/algebrax/__main__.py`)**:
   - `cmd_inspect --semiring Polynomial` (and any parameterized semiring) catches `Exception` and silently falls back to `StandardSemiring()` with exit code `0`.
   - `cmd_catalog` hardcodes a stale 5-domain map (misclassifying `String`/`KCollapsed` under `'logic'` and `Clifford*` under `'algebraic'`) and swallows all constructor errors under blanket `except Exception:`.
   - `cmd_verify --all` hardcodes 12 of 33 semirings, performs case-sensitive lookup (breaking `--semiring tropical`), prints bogus headers like `CliffordSemiring` and `GaloisFieldSemiring`, and ignores stronger protocol witnesses (`KleeneAlgebra`, `StarSemiring`, `Field`, `LieAlgebra`, `HopfAlgebra`).
   - `get_version()` carries a stale `'0.8.0'` fallback; `_parse_matrix_dict` uses Unicode `.isdigit()` (`'²'.isdigit() == True` crashes `int()`); `--dot` skips root `dict` validation; missing/malformed JSON files and non-JSON carrier values raise raw tracebacks.
4. **Phase 9–11 & Web Explorer Readiness**:
   - Phase 11 (`EP-0240`–`0243`) requires exact fields (`Field` + `tag='exact'`); `EP-0222` (`TropicalHypersurface`) and `EP-0241` (`OreAlgebra.shift` / `.differential` presets) require first-class support for parameterized constructors and mode-factory presets; and `EP-0120` (static Web Studio) needs a build-time JSON manifest (`python -m algebrax catalog --format json`).

---

## Rationale

This design synthesizes the full **Grand Council Review** across all nine pillars:

- **🧩 Bertrand Russell (Type Theory & Paradox Avoidance) & ⚖️ Emmy Noether (Symmetry)**:
  The operational intersection across AlgebraX's domains (`FiniteGroup`, `Coalgebra`, `Category`, `Semiring`, `AffineVariety`) is $\bigcap_i \Sigma_i = \emptyset$. A universal `Structure(Protocol)` collapses into Russell's universal set (`isinstance(42, Structure) == True`), while a nominal `Structure` ABC breaks [`EP-0005`](EP-0005-universal-algebraic-protocol-architecture.md)'s Law of Flat Protocol Composition, reintroduces MRO diamonds, and excludes factory families (`so_n`, `symmetric_group`). A pure-data frozen `StructureEntry` record treats classes and canonical factories symmetrically while keeping 0-cell algebraic structures strictly disjoint from data containers (`AlgebraicTrie`, `SimplicialComplex`), 1-cells (morphisms, functors, representations, sheaves), and subobjects (ideals).
- **⚡ Claude Shannon (Minimal Representation & Zero Overhead) & 🛡️ The Golem (Safety & State Gravity)**:
  `src/algebrax/registry.py` contains **zero top-level domain imports**—resolving concrete reified Python symbols inside a single `@cache`-decorated builder returning `MappingProxyType[str, StructureEntry]`. This guarantees circular-import immunity, preserves static type checking (`pyrefly`/`ruff`), avoids eager AMDS regex parsing at import time, and eliminates global mutable state (rejecting mutable `register()` in favor of a pure functional `extend_catalog()`).
- **🔬 Karl Popper (Falsifiability) & 🧪 Francis Bacon (Empiricism)**:
  Every registry entry is a falsifiable hypothesis verified in CI: reified `@runtime_checkable` protocols/laws, runtime `isinstance(inst, p/law)` and empirical axiom execution, anti-vacuity guards on star/Kleene verifiers, 100% AMDS docstring signature coverage, exact module completeness checks against `__all__` + an explicit exclusion set, and bidirectional `required_params` contract verification. Keeping `registry` strictly free of `verification` imports enforces a clean unidirectional dependency DAG.
- **💡 Richard Feynman (Clarity & Freshman Test) & 🌿 The Steward (Harmony)**:
  Naming the module `algebrax.registry` (with `catalog()`, `get()`, `describe()`, `domains()`, `kinds()`) avoids `catalog.catalog()` stutter and matches `ax.display`/`ax.converters`/`ax.verification` in `algebrax.__init__`. Adding a dedicated `describe <name>` CLI subcommand avoids overloading `inspect <file>` with file-vs-name heuristics.
- **🧭 The Explorer (Future Frontiers)**:
  Supporting `target: type | Callable`, `example` factories, orthogonal `(kind, domain, tags)`, `to_dict()` / `--format json`, and a decoupled `display.structure_card(obj, *, extra_rows=None)` future-proofs Phases 9–11 and powers `EP-0120`'s static "Algebraic Periodic Table" from one source of truth.

---

## Specification

### 1. Immutable Layer-3.5 Registry (`src/algebrax/registry.py`)

Export `registry` from `src/algebrax/__init__.py` (under *Section 4: Tools & Ecosystem Bridges* as `ax.registry`).

#### 1.1 Unidirectional Layering (Zero Circular Imports)
```text
Layer 1–2: algebrax.algebra        (Protocols, Law* mixins; Semiring.catalog()/registry() lazy proxies)
              ▲
Layer 3:   algebrax.{semiring,clifford,group,lie,topology,variety,category,analysis,rep,...}
              ▲
Layer 3.5: algebrax.registry       (StructureEntry, @cache builder, query/describe/extend — ZERO verification imports)
              ▲
Layer 4:   algebrax.verification   (PROTOCOL_VERIFIERS, StructureFixture, verify_structure(key))
              ▲
Layer 5:   algebrax.__main__       (CLI: catalog/describe/inspect use registry; verify lazily imports verification)
```
- `src/algebrax/registry.py` MUST have **zero top-level imports** of Layer-3 domain modules (`semiring`, `lie`, `group`, `clifford`, `variety`, `topology`, `rep`, `category`) and **zero imports** of `algebrax.verification` anywhere in the module.
- Built-in entries are constructed inside a single `@cache`-decorated `_build_catalog() -> MappingProxyType[str, StructureEntry]` using function-local `from algebrax.<domain> import ...` imports (reified Python symbols, never dotted string paths).
- AMDS docstrings are **never** parsed and classes are **never** instantiated during `_build_catalog()`; metadata is extracted lazily on demand and cached per entry.

#### 1.2 Frozen `StructureEntry` Data Model
```python
@dataclass(frozen=True, slots=True)
class StructureEntry:
    """Immutable metadata record for a concrete AlgebraX structure class or factory."""

    key: str                                    # Canonical lookup key, e.g. 'Tropical', 'Clifford', 'so_n', 'AffineVariety'
    target: type[Any] | Callable[..., Any]      # Concrete class or canonical factory/preset callable
    product_type: type[Any]                     # Guaranteed return type (target for classes; e.g. LieAlgebra for so_n)
    kind: str                                   # Algebraic genus: 'semiring', 'ring', 'field', 'group', 'lie',
                                                #   'algebra', 'coalgebra', 'hopf', 'normed', 'category', 'variety'
    domain: str                                 # Continent/namespace: 'arithmetic', 'optimization', 'logic',
                                                #   'statistical', 'structures', 'algebraic', 'clifford', 'group',
                                                #   'lie', 'hopf', 'normed', 'topology', 'category', 'variety'
    protocols: tuple[type[Any], ...]            # Reified Layer-2 @runtime_checkable protocols
    laws: tuple[type[Any], ...]                 # Reified Layer-1 Law* witness protocols
    required_params: tuple[str, ...] = ()       # Mandatory positional/keyword-only params from inspect.signature(target)
    tags: frozenset[str] = frozenset()          # Cross-cutting traits: 'exact', 'finite', 'parameterized', 'web-explorer', ...
    aliases: tuple[str, ...] = ()               # Case-insensitive resolution aliases
    example: Callable[[], Any] | None = None    # Zero-arg factory for a small canonical instance (None => target() when zero-arg)

    @property
    def is_factory(self) -> bool:
        """Return True if target is a factory function/preset rather than a class."""
        return not isinstance(self.target, type)

    @property
    def zero_arg(self) -> bool:
        """Return True iff target can be invoked with zero arguments."""
        return len(self.required_params) == 0

    def sample_instance(self) -> Any:
        """Return a canonical instance using example() if provided, else target()."""
        ...

    def metadata(self) -> AlgebraicMeta:
        """Lazily extract and cache AMDS metadata via algebrax.display.get_algebraic_metadata."""
        ...

    @property
    def signature(self) -> str: ...             # From metadata().signature
    @property
    def summary(self) -> str: ...               # From metadata().summary

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot (for CLI --format json and Web Explorer manifests)."""
        ...

    def _repr_html_(self) -> str:
        """Render a Jupyter structure card lazily via algebrax.display.structure_card(self)."""
        ...
```
*Note: The field name `kind` (never `category`) is used deliberately so it never collides with `algebrax.category`.*

#### 1.3 Sound Protocol & Law Derivation (Zero `issubclass` Traps, Zero Isomer False Positives)
To eliminate manual drift without falling into Python's structural protocol pitfalls:
1. **Never call `issubclass(cls, Proto)`** on property-bearing `@runtime_checkable` protocols (raises `TypeError` in Python 3.11+).
2. **Derive `protocols` and `laws` from `product_type.__mro__` + `EP-0005` witness-complete mixin closure**:
   - Extract all `Law*` mixins and Layer-2 protocols present in `product_type.__mro__`.
   - Add witness-complete Layer-2 protocols $P$ whose flat Layer-1 mixin basis $\operatorname{Spec}(P)$ is a subset of $\operatorname{Mixins}(\text{product\_type.__mro__})$ (e.g., `DualNumberAlgebra` automatically infers `CommRing`, `Ring`, `Semiring`), plus method-only structural protocols (e.g., `category.Quiver` for `FiniteQuiver`).
   - **Explicitly exclude the 7 lawless isomer protocols** (`Semigroup`, `Band`, `CommMonoid`, `AddCommMonoid`, `OpCommMonoid`, `DistributiveLattice`, `VectorSpace`) from structural inference, and do **not** infer `StarSemiring` from `StandardSemiring`'s partial `.star()`.
   - **Never hand-declare un-witnessed `Law*` entries** and never declare conditional instance-only properties (`PoissonAlgebra` on `MultivariatePolynomialAlgebra`, `CommGroup` on `dihedral_group`) as unconditional class-level protocols.
3. **Derive `required_params`** directly from `inspect.signature(target)` (collecting parameters without defaults, excluding `self`/`*args`/`**kwargs`).

#### 1.4 Public Functional Query API (`algebrax.registry.__all__`)
- `StructureEntry`
- `catalog(*, domain: str | None = None, kind: str | None = None, protocol: type[Any] | None = None, law: type[Any] | None = None, tag: str | None = None, zero_arg: bool | None = None) -> Mapping[str, StructureEntry]`
  - Returns an immutable `MappingProxyType[str, StructureEntry]` (zero-arg call returns the cached full catalog; filtered calls return a fresh `MappingProxyType`).
- `get(name: str) -> StructureEntry`
  - Case-insensitive lookup resolving canonical `key`, `target.__name__`, `product_type.__name__` (when unambiguous), explicit `aliases`, or suffix-stripped semiring names (e.g., `'tropical'`, `'TropicalSemiring'`). Raises `KeyError` with close suggestions on miss.
- `describe(target: str | type[Any] | Any) -> StructureEntry`
  - Resolves a registry key, class, factory, or live instance to its `StructureEntry`, falling back cleanly to on-the-fly AMDS + MRO introspection for unregistered user-defined structures.
- `domains() -> tuple[str, ...]` and `kinds() -> tuple[str, ...]`
  - Sorted, immutable tuples derived dynamically from the catalog.
- `protocols() -> Mapping[str, type[Any]]` and `laws() -> Mapping[str, type[Any]]`
  - Read-only `MappingProxyType[str, type]` views of all canonical Layer-2 `@runtime_checkable` protocols and Layer-1 `Law*` witnesses, reusing the internal lookup tables required for MRO/mixin derivation, CLI `--protocol`/`--law` resolution, AMDS introspection, and verifier completeness checks.
- `extend_catalog(entries: Mapping[str, StructureEntry], *, base: Mapping[str, StructureEntry] | None = None, override: bool = False) -> Mapping[str, StructureEntry]`
  - Pure functional combiner returning a new `MappingProxyType` without mutating the built-in catalog; raises `ValueError` on duplicate keys unless `override=True`.

#### 1.5 Backwards-Compatible Semiring Projections, CommSemiring Alignment & Cache Hardening
- **`CommSemiring` Law Alignment (`src/algebrax/semiring/{arithmetic,optimization,logic,statistical,structures,algebraic}.py`)**:
  - Promote all unconditionally commutative built-in semirings to inherit `CommSemiring` (`LawCommutative`) so `catalog(law=LawCommutative)` and `isinstance(..., CommSemiring)` truthfully reflect their mathematical properties:
    - `StandardSemiring`, `ModularSemiring`
    - `TropicalSemiring`, `ArcticSemiring`, `ViterbiSemiring` (and `ReliabilitySemiring`), `BottleneckSemiring`, `MinTimesSemiring`
    - `BooleanSemiring`, `LukasiewiczSemiring`, `DigitalSemiring`
    - `LogSemiring`, `BivariateVarianceSemiring`, `BinomialConvolutionSemiring` (and subclasses `StatisticalMomentSemiring`, `VarianceSemiring`, `SkewnessSemiring`, `KurtosisSemiring`), `MultivariateBinomialConvolutionSemiring` (and `MultivariateMomentSemiring`)
    - `KCollapsedSemiring`
  - Keep non-commutative or arbitrary-coefficient semirings (`StringSemiring`, `MonoidAlgebraSemiring`, `QuotientMonoidAlgebraSemiring`, `KnotSemiring`, `ProvenanceSemiring` unless coefficient-constrained, `PolynomialAlgebra`, `CliffordAlgebra`, `GeneralizedCliffordAlgebra`, `QuantumCliffordAlgebra`) strictly non-`CommSemiring`. Every promoted class is empirically verified under Popper's `LawCommutative` CI invariant.
- `src/algebrax/semiring/_registry.py`:
  - `semiring_catalog() -> Mapping[str, type[Semiring[Any]]]` projects the 33 built-in semiring catalog classes from `algebrax.registry` (imported lazily inside the `@cache` function) and returns `MappingProxyType` (eliminating cache mutation).
  - `DOMAIN_TAGS` becomes a `MappingProxyType[str, str]` projected from the same canonical keys.
- `src/algebrax/algebra/_semiring.py`:
  - `Semiring.catalog()` and `Semiring.registry()` return `MappingProxyType` (no mutable `dict` leaks).
  - `Semiring.normalize(key)` for a `zero_arg=False` catalog entry raises a descriptive `TypeError` listing `entry.required_params` (instead of an opaque `TypeError: __init__() missing ...`).
  - **Do NOT** add `.catalog()`, `.registry()`, or `.normalize()` to any other Layer-2 protocol (`Ring`, `Field`, `Group`, `HopfAlgebra`, `Category`, etc.).

---

### 2. Strict 0-Cell Inclusion/Exclusion Taxonomy

**Inclusion Rule**: Register concrete Layer-3 **0-cell structure providers** (classes or canonical factory families) implementing at least one Layer-2 algebraic, categorical, or geometric-variety protocol over unboxed carriers:
- **Semirings / Star / Kleene / Action**: All 33 entries of `Semiring.catalog()` (29 classes in `algebrax.semiring.*` + `DualNumberAlgebra`, `PolynomialAlgebra`, `GaloisField`, `CliffordAlgebra`, `GeneralizedCliffordAlgebra`, `QuantumCliffordAlgebra`) plus `QuotientSemiring` and `RelationActionAlgebra`.
- **Rings & Associative Algebras**: `MonoidAlgebra`, `CommMonoidAlgebra`, `QuotientMonoidAlgebra`, `MultivariatePolynomialAlgebra`, `QuotientRing`, `CommQuotientRing`, `QuotientAlgebra`, `GrothendieckRing`, `CommGrothendieckRing`, `PathAlgebra`, `IwahoriHeckeAlgebra`, `CochainAlgebra`, `TopologicalKTheoryRing`.
- **Fields**: `StandardField`, `ModularField`, `GaloisField`, `PAdicField`.
- **Groups**: `FiniteGroup`, `FiniteCommGroup`, `GrothendieckGroup`; factories `cyclic_group`, `dihedral_group`, `quaternion_group`, `symmetric_group`, `alternating_group`, `direct_product`.
- **Lie Algebras**: `LieAlgebra`; factories `so_n`, `su_n`, `u_n`, `sp_n`, `sl_n`, `se_n`, `clifford_lie_algebra`, `g2`, `f4`, `e6`, `e7`, `e8`, `chevalley_lie_algebra`.
- **Non-Associative Algebras**: `SymmetricMatrixJordanAlgebra`, `OctonionAlgebra`, `ImaginaryOctonionMalcevAlgebra`.
- **Coalgebras & Hopf Algebras**: `DividedPowerCoalgebra`, `SimplicialChainCoalgebra`, `GroupHopfAlgebra`, `QuantumSL2`, `CoordinateHopfAlgebra`.
- **Normed / Inner Product Spaces**: `EuclideanSpace`.
- **Categories, Groupoids & Quivers**: `MatrixCategory`, `LawvereMetricCategory`, `CellPosetCategory`, `FiniteSetCCC`, `OppositeCategory`, `SimplicialPathGroupoid`, `FiniteQuiver`; factories `dynkin_quiver`, `kronecker_quiver`, `cycle_quiver`.
- **Algebraic Varieties**: `AffineVariety`; factories `boolean_variety`, `syzygy_variety`, `plucker_grassmannian_variety`.

**Strict Exclusions** (verified via explicit `EXPLICIT_EXCLUSIONS` set in CI):
- **Data Containers & Carriers**: `AlgebraicTrie`, `SparseChainComplex`, `SimplicialComplex`, `FilteredSimplicialComplex`, `Cochain`, `StructureConstants`, `RootSystem`, `Cell`, `FaceInclusion`, `PersistenceInterval`, `HodgeDecomposition`, `Character`, `CharacterTable`, `MolienSeries`, `DiscreteConnection`, `DiscreteOrthogonalConnection`, `CoeffectContext`, `SemiringCoeffectTracker`.
- **1-Cells (Morphisms, Functors, Representations & Sheaves)**: `CallableHomomorphism`, `PolynomialMap`, `TransposeFunctor`, `SemiringChangeOfBaseFunctor`, `ExplicitGroupRep`, `ExplicitLieRep`, `QuiverRepresentation`, `CellularSheaf`, `ConstantSheaf`, `FunctorialSheaf`.
- **Subobjects (Ideals)**: `PrincipalIdeal`, `FinitelyGeneratedIdeal`, `GroebnerIdeal`, `IntegerModuloIdeal`, `KernelIdeal`, `NilpotentIdeal`, `PolynomialTruncationIdeal`, `SubspaceLieIdeal`.
- **Abstract Protocols, Aliases & Solvers**: All Layer-1 `Has*`/`Law*` mixins, Layer-2 protocols (including `algebra/_lattice.py` where zero concrete lattice classes exist today), `RationalField`/`RealField`/`ComplexField` aliases, `BanachContractionVerifier`, `ReproducingKernelHilbertSpace`.

**Immediate Docstring Drift Fixes Included**:
- Add an `EP-0002` AMDS `Algebraic Signature:` block to `StandardField` (`src/algebrax/algebra/_field.py`) and any other registered structure missing an own parseable signature.
- Update `src/algebrax/__init__.py:29` (`so3, sl2, se3` → `so_n, sl_n, se_n`) and add `registry` to Section 4 of the root docstring and `__all__`.

---

### 3. Decoupled Rich Display Generalization (`src/algebrax/display.py`)

- Add and export **`structure_card(obj: Any, *, extra_rows: Mapping[str, Any] | None = None) -> str`** in `algebrax.display`:
  - Accepts **any** structure instance, class, or `StructureEntry` (including unregistered user classes) via pure AMDS reflection and lightweight protocol/attribute inspection—**zero imports of `algebrax.registry` or Layer-3 domain modules**.
  - Renders HTML-escaped header (`name`, `summary`, KaTeX `$$signature$$`), protocol/law/domain badges when present, adaptive property rows (`zero`/`one` via `HasZero`/`HasOne`, `identity` via `HasIdentity`, `bottom`/`top` via `HasBounds`, `required_params` if uninstantiated), and optional `extra_rows` (for Phase 9–11 `RichDisplayable` classes like `TropicalHypersurface`).
- Refactor `semiring_card(semiring)` into a thin wrapper delegating to `structure_card(semiring)`.

---

### 4. Unidirectional Verification Bridge (`src/algebrax/verification/`)

Owned entirely by Layer-4 `algebrax.verification` (depending downward on `algebrax.registry`):
- **`PROTOCOL_VERIFIERS: Mapping[type[Any], Callable[..., dict[str, bool]]]`**: Reified dispatch mapping Layer-2 protocols (`Semiring`, `StarSemiring`, `KleeneAlgebra`, `ActionAlgebra`, `Ring`, `CommRing`, `Field`, `Group`, `CommGroup`, `LieAlgebra`, `JordanAlgebra`, `AlternativeAlgebra`, `MalcevAlgebra`, `HopfAlgebra`, `NormedSpace`, `InnerProductSpace`, etc.) to their verifiers.
- **`StructureFixture`** (frozen dataclass): Carries `instance`, `samples`, and optional auxiliary carriers (`scalars`, `scalar_samples`, `ideal_samples`) for multi-carrier verifiers (`LieAlgebra`, `Algebra`, `QuotientRing`).
- **`get_structure_fixture(key: str) -> StructureFixture`**: Generalized fixture lookup; `get_semiring_samples(name)` becomes a thin wrapper over it (eliminating the duplicated 33-entry `catalog_map` in `verification/_semiring.py`).
- **`verify_structure(key: str, *, tol: float = 1e-7) -> dict[str, dict[str, bool]]`**: Looks up `entry = registry.get(key)`, retrieves its fixture, and executes all mapped protocol verifiers + law checks.
- **Anti-Vacuity Hardening**: Update `verify_star_semiring_laws` and `verify_kleene_algebra_laws` so catching `(ValueError, ZeroDivisionError, OverflowError, NotImplementedError)` on *every* sample (0 evaluated samples) fails (`False`) instead of vacuously returning `True`.
- **Stale Test Drift Fix**: Update `tests/verifications/test_axiomatic_properties.py` to remove hardcoded "34" count references and dynamically use the registry count.

---

### 5. Unified Command-Line Interface Overhaul (`src/algebrax/__main__.py`)

Owns 100% of `src/algebrax/__main__.py` (handed off cleanly from [`EP-0254`](EP-0254-ergonomics-state-safety-ecosystem-bridges-and-hygiene.md)), fixing all 10 audit defects and upgrading to 4 crisp subcommands:

1. **`python -m algebrax catalog [--domain ...] [--kind ...] [--protocol ...] [--law ...] [--verifiable] [--format text|json]`**
   - Dynamically populates `--domain` and `--kind` filters from `ax.registry.domains()` / `kinds()`.
   - Uses `ax.__version__` directly (removes stale `'0.8.0'` fallback and duplicate `importlib.metadata` logic).
   - Eliminates blanket `except Exception:` speculative instantiation: renders zero-arg `Zero`/`One` when `--kind semiring` and explicit `<requires: ...>` from `entry.required_params` otherwise.
   - `--format json` emits a clean `StructureEntry.to_dict()` manifest ready for CI and `EP-0120`'s Web Explorer.
2. **`python -m algebrax describe <name> [--format text|json|html]`**
   - Dedicated structure card command (matching `ax.registry.describe(name)` — never overloading `inspect <file>`).
   - Displays import path, domain, kind, summary, AMDS signature, protocols, laws, constructor requirements, and identities (or HTML via `display.structure_card`). Unknown name prints concise error to `stderr` and exits `1`.
3. **`python -m algebrax inspect <file|-> [--semiring NAME] [--power N] [--dot FILE] [--format text|json|html]`**
   - Resolves `--semiring` via `ax.registry.get(name)` (case-insensitive, supporting aliases and class names):
     - Unknown name, non-semiring structure, or parameterized semiring (`not entry.zero_arg`, e.g., `Polynomial`, `Clifford`, `GaloisField`) writes an actionable error naming required parameters to `stderr` and returns exit code `1` (**never** silently falls back to `StandardSemiring`; **never** uses `eval()`).
   - Validates both primary and `--dot` JSON roots as `dict`; restricts `_parse_matrix_dict` integer key restoration to strict ASCII base-10 canonical integers (`re.fullmatch(r'-?(?:0|[1-9][0-9]*)', k)`) to eliminate Unicode `'²'.isdigit()` crashes and `"00"` key collisions.
   - Catches `(OSError, json.JSONDecodeError, ValueError, TypeError)` cleanly at the CLI boundary with concise `stderr` diagnostics and exit code `1`; handles non-JSON / non-finite JSON outputs cleanly without raw tracebacks.
4. **`python -m algebrax verify [name] [--semiring NAME] [--all] [--domain ...] [--kind ...] [--format text|json]`**
   - Supports positional structure name (`python -m algebrax verify Tropical`), `--semiring` (preserved), and `--all` (dynamically verifies **every** verifiable entry in `algebrax.registry`, covering all 33 semirings + verifiable non-semiring structures).
   - Uses canonical case-insensitive registry lookup and displays real `entry.target.__name__` (fixing bogus `CliffordSemiring` / `GaloisFieldSemiring` headers).
   - Dispatches protocol-aware verification via `algebrax.verification.verify_structure`, reporting failing `(entry, protocol, axiom)` triples cleanly and exiting non-zero on any failure.

---

## Acceptance Criteria

1. **Single Source of Truth & Immutability**: `algebrax.registry.catalog()`, `Semiring.catalog()`, `Semiring.registry()`, `semiring_catalog()`, and `DOMAIN_TAGS` all return read-only `MappingProxyType` views with zero duplicated structure lists; attempting item assignment or `.clear()` raises `TypeError`.
2. **Unidirectional Import Isolation**: A fresh-process import of `algebrax.registry` loads zero modules from `algebrax.verification`; AST audit confirms `src/algebrax/algebra/` has zero top-level imports of `algebrax.registry`, and `src/algebrax/display.py` has zero imports of `algebrax.registry`.
3. **Falsifiable Registry Invariants (`tests/algebrax/test_registry_invariants.py`)**:
   - **I-1 (Reified Types)**: Every item in `entry.protocols` and `entry.laws` is a `type` with `_is_runtime_protocol is True`.
   - **I-2 (Protocol & Law Honesty + Anti-Vacuity + Negative Control)**: Every entry's sample instance satisfies `isinstance(inst, p)` for all `p in entry.protocols` and `law in entry.laws`, passes `verify_structure(entry.key)`, star/Kleene verifiers fail on 0 evaluated samples, and a negative-control test proves attaching a false law witness (e.g., `LawCommutative` on `CliffordAlgebra`) fails verification.
   - **I-3 (100% AMDS Coverage)**: Every registered entry yields a non-empty, non-`N/A` `extract_algebraic_signature` and `get_algebraic_metadata` (including `StandardField`).
   - **I-4 (Completeness Audit)**: Zero unregistered concrete `Semiring` subclasses in `algebrax.semiring`, and zero unregistered concrete 0-cell algebraic structures across audited domains outside the documented `EXPLICIT_EXCLUSIONS` frozenset.
   - **I-5 (Bidirectional `zero_arg` Contract)**: `entry.zero_arg is True` implies `entry.target()` succeeds; `entry.zero_arg is False` implies `entry.target()` raises `TypeError`, `entry.sample_instance()` succeeds, and `Semiring.normalize(key)` raises a descriptive `TypeError` naming `entry.required_params`.
4. **Decoupled Display Cards**: `display.structure_card(obj)` renders escaped HTML for both registered structures (`TropicalSemiring()`, `StructureEntry`) and unregistered custom classes without importing `algebrax.registry`; `semiring_card` delegates cleanly to `structure_card`.
5. **Hardened CLI (`tests/algebrax/test_cli.py`)**:
   - `python -m algebrax inspect <file> --semiring Polynomial` exits `1` with required parameters on `stderr` (never falls back to `StandardSemiring`).
   - `python -m algebrax catalog --format json` outputs valid JSON matching `ax.registry.catalog()`; `python -m algebrax describe GaloisField` displays signature, protocols, and constructor requirements.
   - `python -m algebrax verify --all` verifies all 33 semirings plus verifiable non-semiring structures dynamically, displays accurate class names (never `CliffordSemiring`), and exits `0` iff all pass.
   - Unicode key `'²'`, malformed JSON, missing file, non-dict `--dot`, and non-finite/unserializable JSON matrix cases all exit `1` cleanly with `stderr` diagnostics and zero tracebacks.
6. **Drift Cleanup**: Stale `"34"` semiring references in `tests/verifications/test_axiomatic_properties.py` and stale `so3/sl2/se3` references in `src/algebrax/__init__.py` are fixed; `ruff check .`, `pyrefly check src tests`, `pytest -q`, and `zensical build --clean` all pass with zero `EP-\d{4}` leakage in `src/`.

---

## Backwards Compatibility

- **Preserved Public APIs**:
  - `Semiring.catalog()`, `Semiring.registry()`, `Semiring.default()`, `Semiring.normalize()`, `semiring._registry.semiring_catalog()`, `semiring._registry.DOMAIN_TAGS`, `display.semiring_card()`, and `verification.get_semiring_samples()` remain available with identical keys and semantics, upgraded to read-only `MappingProxyType` views.
  - Existing CLI invocations (`catalog`, `inspect <file> --semiring ...`, `verify --semiring ...`, `verify --all`) continue to work.
- **Intentional Clean Cuts & Bug Fixes**:
  - Mutating the return value of `Semiring.catalog()`, `Semiring.registry()`, `semiring_catalog()`, or `DOMAIN_TAGS` now raises `TypeError` (`MappingProxyType`).
  - `python -m algebrax inspect --semiring Polynomial` (and other parameterized semirings) now exits with code `1` and prints required parameters to `stderr` instead of silently falling back to `StandardSemiring`.
  - `Semiring.normalize('Polynomial')` raises a descriptive `TypeError` listing required parameters.
  - `algebrax.__main__.get_version()` delegates directly to `algebrax.__version__` (removing the stale `'0.8.0'` fallback).

---

## How to Teach This / Documentation Plan

- Add a concise user guide section covering `algebrax.registry` (`catalog`, `get`, `describe`, `extend_catalog`), `display.structure_card`, and the upgraded `python -m algebrax` CLI (`catalog`, `describe`, `inspect`, `verify`, `--format json`).
- Update [`docs/guide/index.md`](../guide/index.md) or the relevant CLI/display guide pages to document the unified catalog and `describe` command.
- Document the `StructureEntry` registration checklist for future Phases 9–11 proposals (`EP-0222`, `EP-0230`–`0232`, `EP-0240`–`0243`).

---

## Reference Implementation

Target files:
- `src/algebrax/registry.py` *(new)*
- `src/algebrax/__init__.py` *(export `registry`; fix stale `so3/sl2/se3` docstring)*
- `src/algebrax/semiring/{_registry,arithmetic,optimization,logic,statistical,structures,algebraic}.py` & `src/algebrax/algebra/_semiring.py` *(read-only `MappingProxyType` projections, `CommSemiring` alignment & descriptive `normalize()` error)*
- `src/algebrax/algebra/_field.py` *(add missing AMDS signature to `StandardField`)*
- `src/algebrax/display.py` *(add `structure_card`; `semiring_card` delegates)*
- `src/algebrax/verification/` *(add `PROTOCOL_VERIFIERS`, `StructureFixture`, `get_structure_fixture`, `verify_structure`; anti-vacuity guards)*
- `src/algebrax/__main__.py` *(4-subcommand CLI overhaul)*
- `tests/algebrax/test_registry_invariants.py` *(new)*, `tests/algebrax/test_cli.py`, `tests/algebrax/test_docstrings.py`, `tests/verifications/test_axiomatic_properties.py`

---

## Rejected Ideas

1. **Introducing a Nominal `Structure` ABC or Universal `Structure(Protocol)`**:
   - *Rejected*: The operational intersection across AlgebraX structures is $\emptyset$ (empty protocol collapses to universal `isinstance(42, Structure) == True`), while a nominal ABC violates [`EP-0005`](EP-0005-universal-algebraic-protocol-architecture.md)'s Law of Flat Protocol Composition, reintroduces MRO diamonds, and excludes factory families (`so_n`, `symmetric_group`, `dynkin_quiver`).
2. **Global Mutable `register(entry)` / `@register_structure` Decorator**:
   - *Rejected*: Introduces import-order sensitivity (unimported submodules silently vanish from the catalog) and global mutable state gravity that breaks test isolation under `pytest-randomly` and `pytest-xdist`. Pure functional `extend_catalog(...)` achieves extensibility with zero global state.
3. **Replicating `.catalog()` / `.registry()` / `.normalize()` Onto Other Layer-2 Protocols (`Ring`, `Field`, `Group`, `Category`)**:
   - *Rejected*: Institutionalizes upward Layer-2 → Layer-3 coupling and lacks coherent `.default()` semantics for parameterized structures.
4. **Dotted Import-Path Strings (`"algebrax.lie:so_n"`) in the Registry Table**:
   - *Rejected*: Violates *Reified Accessors* (`PRINCIPLES.md`), hides typos until runtime, and blinds static type checkers (`pyrefly`) and IDE refactoring. Function-local imports inside a `@cache` builder give both static verification and circular-import immunity.
5. **Auto-Inferring Lawless Isomer Protocols or Calling `issubclass` on Property-Bearing Protocols**:
   - *Rejected*: `issubclass` raises `TypeError` on property-bearing protocols in Python 3.11+, and blind structural `isinstance` falsely brands non-commutative structures as `CommMonoid`/`Band`.
6. **Coupling `StructureEntry` Directly to `algebrax.verification` Callables**:
   - *Rejected*: Creates circular import cycles (`verification` imports Layer-3 structures) and forces untyped wrappers over heterogeneous verifier arities. Unidirectional Layer-4 dispatch (`PROTOCOL_VERIFIERS`) keeps boundaries clean.
7. **Overloading `python -m algebrax inspect <file>` to Guess Between File Paths and Structure Names**:
   - *Rejected*: Violates *Explicit over Implicit* (a typo'd JSON path produces misleading structure errors). A dedicated `describe <name>` subcommand matches `ax.registry.describe()` 1:1.
8. **Auto-Parsing Arbitrary CLI Constructor Strings (`--semiring "Modular(7)"`) via `eval()`**:
   - *Rejected*: Severe code-execution security hazard violating Golem's Safety pillar.

---

## Open Questions

None. Both Council open questions are resolved: unconditionally commutative built-in semirings are promoted to `CommSemiring` (`§1.5`), and the CLI adds the dedicated 4th subcommand `python -m algebrax describe <name>` (`§5`).

---

## Change Log

* **2026-11-27:**
  * Initial Draft authored from the Grand Council Review (Noether, Russell, Shannon, Golem, Feynman, Steward, Popper, Bacon, Explorer), absorbing `src/algebrax/__main__.py` CLI hardening cleanly from [`EP-0254`](EP-0254-ergonomics-state-safety-ecosystem-bridges-and-hygiene.md).
* **2026-11-28:**
  * Resolved Open Questions: promoted unconditionally commutative built-in semirings to `CommSemiring` (`§1.5`), added read-only `protocols()` and `laws()` views (`§1.4`), and finalized the dedicated `python -m algebrax describe <name>` subcommand (`§5`); promoted status to `Accepted`.
