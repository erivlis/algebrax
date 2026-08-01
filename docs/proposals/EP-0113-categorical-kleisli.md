---
title: "EP-0113: Categorical Morphisms, Kleisli Composition & Operads"
description: "Monadic Kleisli composition, string diagram wiring engines, and Kan extensions over semirings."
icon: lucide/git-graph
status: draft
---

# EP-0113: Categorical Morphisms, Kleisli Composition & Operads

| Field       | Value                    |
|:------------|:-------------------------|
| **EP**      | 0113                     |
| **Title**   | Categorical Morphisms, Kleisli Composition & Operads |
| **Author**  | Eran Rivlis & Antigravity |
| **Status**  | Draft                    |
| **Type**    | Standards Track          |
| **Created** | 2026-08-01               |
| **Updated** | 2026-08-01               |

## Abstract

This proposal specifies `algebrax.category`, building upon `SparseChainComplex` (`EP-0101`). It formalizes category-theoretic abstractions in `algebrax`, introducing **Kleisli Composition** $g \circ_T f$ for effectful monadic morphisms as semiring matrix multiplication, providing a multi-input/multi-output **Operad & String Diagram Wiring Engine**, and implementing left and right **Kan Extensions** over sparse categories.

---

## Deliverables

1. **Core Implementation**: `src/algebrax/category.py` (`Kleisli`, `compose_morphisms`, `kan_extension`, `operad_wire`).
2. **Unit Tests**: `tests/algebrax/test_category.py` (verifying monad laws, composition identity, and associative Kan extensions).
3. **Use Case Recipe**: `recipes/categorical_kleisli_monads.py` & `.ipynb`.
4. **Graphical Laboratory View**: View 24 (`view_categorical_monads_group`) in `recipes/lab.py`.
