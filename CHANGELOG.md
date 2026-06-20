## v0.2.0 (2026-06-20)

### Feat

- Enhance Fenchel-Legendre transform to support multiple semirings
- Replaces Ollivier-Ricci with Forman-Ricci graph curvature.

### Fix

- Uses math.isclose for robust float comparison in graph weight check.

### Refactor

- **test_anlysis**: Improves analysis test precision using pytest.approx assertions.

## v0.1.1 (2026-04-09)

### Refactor

- update Semiring protocol to use TypeVar for improved type flexibility
- update semiring classes to use instance methods instead of static methods
