---
title: "EP-0133: Jupyter Rich Display & CLI Inspector"
description: "Rich _repr_html_() for sparse matrices in Jupyter and a CLI tool for inspecting algebraic structures."
icon: lucide/terminal
status: final
---

# EP-0133: Jupyter Rich Display & CLI Inspector

| Field       | Value                                |
|:------------|:-------------------------------------|
| **EP**      | 0133                                 |
| **Title**   | Jupyter Rich Display & CLI Inspector |
| **Author**  | Eran Rivlis & Antigravity            |
| **Status**  | Final                                |
| **Type**    | Standards Track                      |
| **Created** | 2026-08-02                           |
| **Updated** | 2026-09-04                           |

## Abstract

This proposal adds two zero-friction integration surfaces for inspecting and exploring `algebrax`:

1. **Jupyter Rich Display (`algebrax.display`)**: Semantic HTML rendering of sparse matrices (`display_matrix`), sparse
   vectors (`display_vector`), multi-index tries (`display_trie`), and semiring property summary cards (`semiring_card`).
2. **CLI Inspector (`python -m algebrax`)**: A full-featured command-line utility for viewing the built-in semiring
   catalog, verifying algebraic axioms, and evaluating sparse matrix operations from JSON files or `stdin`.

## Motivation

**The Steward (Harmony):** *"Move forward with the least friction."* Users and researchers exploring algorithms need
immediate, zero-boilerplate visual feedback in Jupyter notebooks and direct evaluation capabilities from the terminal
without writing one-off Python scripts.

## Specification & Delivered Architecture

### 1. Jupyter Rich HTML Display (`algebrax.display`)

* **`display_matrix(matrix, title="")`**: Generates a responsive HTML table with cell coordinates and bold value styling.
* **`display_vector(vector, title="")`**: Formats key-value sparse vector dictionaries as tabular HTML cards.
* **`display_trie(trie, max_depth=4)`**: Visualizes nested prefix trees and multi-index paths ($\to$) with right-arrow
  derivations.
* **`semiring_card(semiring)`**: Produces an information card highlighting identity elements ($\mathbf{0}, \mathbf{1}$)
  and docstrings for interactive notebook exploration.

### 2. Command-Line Interface (`algebrax.__main__`)

The module enables command-line execution via standard Python invoking:

```bash
# Display package version
python -m algebrax --version

# Print formatted table of built-in semirings by mathematical domain
python -m algebrax catalog
python -m algebrax catalog --domain optimization

# Verify 9 algebraic semiring axioms (associativity, distributivity, identity, annihilation)
python -m algebrax verify --semiring Tropical
python -m algebrax verify --all

# Inspect sparse matrix files and evaluate matrix operations
python -m algebrax inspect graph.json --semiring tropical --power 5
python -m algebrax inspect m1.json --dot m2.json --format json
cat matrix.json | python -m algebrax inspect - --format html
```

## Backwards Compatibility

Purely additive. All display functions and CLI entrypoints integrate seamlessly with existing sparse dictionary representations.

## Change Log

* **2026-08-02:** Initial Draft.
* **2026-09-04:** Fully implemented `algebrax.display` (`display_matrix`, `display_vector`, `display_trie`, `semiring_card`) and `src/algebrax/__main__.py` with `catalog`, `verify`, and `inspect` subcommands. Status transitioned to Final.
