---
title: "EP-0112: Galois Finite Fields & Cryptographic Arithmetic"
description: "Polynomial exponent quotient semirings GF(p^m), AES GF(2^8) field arithmetic, and Reed-Solomon matrices."
icon: lucide/shield-check
status: final
---

# EP-0112: Galois Finite Fields & Cryptographic Arithmetic

| Field       | Value                                           |
|:------------|:------------------------------------------------|
| **EP**      | 0112                                            |
| **Title**   | Galois Finite Fields & Cryptographic Arithmetic |
| **Author**  | Eran Rivlis & Antigravity                       |
| **Status**  | Final                                           |
| **Type**    | Standards Track                                 |
| **Created** | 2026-08-01                                      |
| **Updated** | 2026-08-01                                      |

## Abstract

This proposal specifies `algebrax.galois`, building upon `QuotientMonoidAlgebraSemiring` (`EP-0100`). It introduces **Galois Finite Fields** $\text{GF}(p^m)$ as polynomial modulo quotient semirings, enabling sparse matrix operations over finite fields, supporting AES $\text{GF}(2^8)$ field arithmetic, Reed-Solomon error correction matrices, and QAP polynomial evaluations for zero-knowledge proofs.

---

## Deliverables

1. **Core Implementation**: `src/algebrax/galois.py` (`GaloisFieldSemiring`, `gf_matrix_mul`, `reed_solomon_generator`).
2. **Unit Tests**: `tests/algebrax/test_galois.py` (verifying field identity, AES MixColumns matrix multiplication, and error correction).
3. **Use Case Recipe**: `recipes/galois_field_cryptography.py` & `.ipynb`.
4. **Graphical Laboratory View**: View 23 (`view_galois_finite_fields_group`) in `recipes/lab.py`.
