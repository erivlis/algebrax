# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
#     "dearpygui",
#     "pillow",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
# AlgebraX Graphical Laboratory (`recipes/lab.py`)

The **AlgebraX Graphical Laboratory** (`recipes/lab.py`) is an interactive desktop application
built with DearPyGui. It provides a real-time, visual sandbox for exploring all 19 real-world
Use Case recipes of the `algebrax` library.

---

## 1. Quick Start

Run the lab with `uv`:

```bash
uv run recipes/lab.py
```

---

## 2. Navigation Sitemap & Module Overview

The sidebar is organized into **6 domain categories** covering all 19 interactive views:

```text
├── Matrix & Graph Algorithms
│   ├── Semiring Matrix Power          (View 1: Tropical, Arctic, Viterbi, Expectation, Provenance, etc.)
│   ├── Forman-Ricci Curvature         (View 2: Discrete Ricci curvature & geometry classification)
│   ├── PageRank Algorithm             (View 3: Stationary distribution of random walks over semirings)
│   └── Network Curvature Vis          (View 12: Interactive force-directed layout & edge curvature chart)
├── Automata, Parsing & Risk
│   ├── Automata Simulator             (View 8: Step-by-step DFA & NFA/probabilistic transition logging)
│   ├── CYK Grammar Parser             (View 6: Parsing chart matrix closure over GrammarSemiring)
│   └── Financial Portfolio Risk       (View 18: Market signal trade DFA & asset spectral centrality)
├── Transforms, Signals & Waves
│   ├── Slope Transform                (View 7: Idempotent Fenchel-Legendre convex conjugate transform)
│   ├── Signal Transforms              (View 10: Discrete Fourier, Hilbert, Convolution & Z-Transforms)
│   ├── 2D Image Convolution           (View 11: Real image downsampling & spatial 2D grid convolutions)
│   └── Optical Holography             (View 17: Coherent wavefront interference & Fourier spectrum)
├── Tensors, Tries & Physics
│   ├── Algebraic Trie / Tensor        (View 4: Sparse tensor dimension contraction/marginalization)
│   ├── Sparse Tensor Einsum           (View 14: Arbitrary-rank einsum over Standard & Tropical semirings)
│   ├── Trajectoid Kinematics          (View 15: Non-holonomic rolling velocity & SO(3) 3x3 rotation)
│   ├── Schwarzschild Black Hole       (View 13: Metric components, light deflection & Hawking entropy)
│   └── 3D Gaussian Splatting          (View 20: 3D spatial covariance Sigma & 2D projective screen splatting)
├── Topology & Geometry
│   ├── Knot Theory & Skein            (View 16: Knot connected sum (#) & Artin braid crossing signatures)
│   ├── Sheaf Cohomology               (View 19: Cellular sheaf coboundary gradient & sensor consensus)
│   ├── Simplicial Homology            (View 21: Boundary nilpotency D_{k-1} o D_k = 0 & Betti barcodes)
│   ├── Clifford Geometric Algebra     (View 22: Cl(3,0) multivectors & 3D rotor rotation sandwiching)
│   ├── Galois Finite Fields           (View 23: GF(2^8) polynomial modulo arithmetic & AES MixColumns)
│   └── Categorical Kleisli Monads     (View 24: Monadic Kleisli composition g o_T f across semirings)
└── Information & Crypto
    ├── Markov & Info Theory           (View 9: Markov steps, steady state & Shannon/KL info metrics)
    └── Post-Quantum Key Exchange      (View 3: Diffie-Hellman matrix key exchange over Digital Semiring)
```

---

## 3. Mandatory Architectural Guidelines for Future Additions

To ensure stability, high aesthetics, and a smooth user experience, all future views and UI modifications MUST
follow these four architectural directives:

### **Directive 1: DearPyGui / ImGui C++ Table Lifecycle Rules**

In Dear ImGui, table column definitions are locked once a table is rendered. Calling `dpg.add_table_column` on an
already-rendered table during a button callback raises a CPython
`SystemError: <built-in function add_table_column> returned a result with an exception set`.

1. **Fixed-Column Tables**:
    * Define table columns **ONCE** during view construction using `create_bordered_table(tag=..., columns=[...])`.
    * `create_bordered_table` **MUST** use the `with dpg.table(**kwargs)` context manager so columns are registered
      inside the active table scope:
      ```python
      with dpg.table(**kwargs) as tbl:
          if columns:
              for col_label in columns:
                  dpg.add_table_column(label=col_label)
      ```
    * When updating fixed-column tables in callbacks, **DO NOT** delete columns or call `add_table_column`. Use
      `clear_table_rows(table_tag)` (which clears only slot 1 row children):
      ```python
      def clear_table_rows(table_tag: str) -> None:
          if dpg.does_item_exist(table_tag):
              children = dpg.get_item_children(table_tag, 1)
              if children:
                  for child in children:
                      dpg.delete_item(child)
      ```

2. **Dynamic-Column Matrix Tables** (e.g. `display_matrix_in_table`):
    * When matrix dimensions or column keys change dynamically based on user input, place a container group around the
      table: `with dpg.group(tag=f"{table_tag}_container"): pass`.
    * `display_matrix_in_table` clears the container and recreates the `dpg.table` cleanly inside the container group:
      ```python
      container_tag = f"{table_tag}_container"
      if dpg.does_item_exist(container_tag):
          dpg.delete_item(container_tag, children_only=True)
          with dpg.table(tag=table_tag, parent=container_tag, ...):
              # add columns & rows
      ```

---

### **Directive 2: Text Selection & Clipboard Accessibility (`Ctrl+C` / `Ctrl+A`)**

Standard `dpg.add_text()` labels are non-interactive in ImGui. Users cannot highlight or copy text from static labels.

* **Use Read-Only Input Text**: All result readouts, status messages, multiline logs, and table cell values **MUST** be
  rendered using `dpg.add_input_text(readonly=True, ...)` (or `multiline=True, readonly=True`).
* **Benefits**:
    * Mouse click & drag text selection.
    * Native keyboard shortcuts (`Ctrl+C` to copy, `Ctrl+A` to select all).
    * Read-only protection preventing accidental user editing.
* **Configure Item Note**: `dpg.configure_item(tag, color=...)` is only supported on static `dpg.add_text()`
  items. Read-only `dpg.add_input_text()` widgets do NOT accept a `color` parameter in `configure_item()`; update
  values using `dpg.set_value(tag, text)` instead.
* **Table Cell Pattern**:
  ```python
  with dpg.table_row(parent=table_tag):
      dpg.add_input_text(default_value=key, readonly=True, width=-1)
      dpg.add_input_text(default_value=val_str, readonly=True, width=-1)
  ```

---

### **Directive 3: Layout Containment & Viewport Insulation**

`dpg.add_separator()` draws a full-width horizontal rule (`<hr>`). If used inside an uncontained column or group, the
rule can bleed into adjacent side-by-side columns or show through transparent canvas viewports.

1. **Opaque Viewport Backgrounds**:
    * Any `dpg.drawlist` canvas (e.g. force-directed graph canvas) **MUST** draw a solid opaque background rectangle as
      its very first element in `_redraw_canvas()`:
      ```python
      dpg.draw_rectangle(
          (0, 0), (width, height), fill=(18, 18, 24), color=(60, 60, 80), thickness=1, parent="vis_canvas"
      )
      ```
    * This prevents underlying window elements or separator rules from showing through the canvas background.

2. **Bordered Child Window Panels (`dpg.child_window`)**:
    * Whenever creating multi-column or side-by-side tool panels (e.g., control sidebars, dual calculators, or
      multi-matrix displays), enclose each column in a `dpg.child_window(border=True)`:
      ```python
      with dpg.group(horizontal=True):
          with dpg.child_window(width=310, height=520, border=True):
              dpg.add_text("CONTROL PANEL")
              dpg.add_separator()  # Safely clipped inside sidebar!
          with dpg.group():
              # Main content / canvas area
      ```

---

### **Directive 4: Step-by-Step Checklist for Adding a New View**

When adding a new Use Case experiment view to `recipes/lab.py`:

1. **Define Callback Handler**:
   Create `run_<feature_name>() -> None` with clear `try...except` handling that updates status strings and calls
   `clear_table_rows()` or `display_matrix_in_table()`.
2. **Define View Builder**:
   Create `build_view_<feature_name>() -> None` wrapped in a group:
   `with dpg.group(tag="view_<feature_name>_group", show=False):`. Add title text and `dpg.add_separator()`.
3. **Register in `VIEWS` List**:
   Add `"<feature_name>"` to the global `VIEWS: list[str]` array.
4. **Add Sidebar Selectable**:
   In `build_navigation_sidebar()`, add `dpg.add_selectable` under the appropriate tree node:
   ```python
   dpg.add_selectable(
       label="Feature Name",
       tag="sel_<feature_name>",
       callback=change_view,
       user_data="<feature_name>",
   )
   ```
5. **Instantiate View in `main()`**:
   Add `build_view_<feature_name>()` inside `main()` under the main window child view group.
6. **Code Quality Verification**:
   Run formatters, type checks, and unit tests before declaring success:
   ```bash
   uv run ruff format recipes/lab.py
   uv run ruff check recipes/lab.py
   uv run pytest
   ```
"""

import cmath
import json
import math
import os
import random
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import Any

import dearpygui.dearpygui as dpg

from algebrax.analysis import forman_ricci_curvature
from algebrax.automata import dfa_step, nfa_step
from algebrax.probability import (
    cross_entropy,
    entropy,
    kl_divergence,
    markov_steady_state,
    markov_step,
    mutual_information,
)
from algebrax.semiring import ArcticSemiring, Semiring, StandardSemiring, TropicalSemiring
from algebrax.transforms import convolve, dft, hilbert, idft, legendre_fenchel, z_transform

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

TEXTURE_WIDTH: int = 64
TEXTURE_HEIGHT: int = 64

# --- Global State for Curvature Visualization Presets ---
current_nodes: list[int | str] = []
current_edges: list[tuple[int | str, int | str]] = []
current_curvatures: dict[tuple[int | str, int | str], float] = {}
pos: dict[int | str, list[float]] = {}
vel: dict[int | str, list[float]] = {}
dragged_node: int | str | None = None


# --- UI Helper Utilities ---
def create_bordered_table(
    tag: str,
    columns: list[str] | None = None,
    width: int | None = None,
    height: int | None = None,
    parent: str | int | None = None,
) -> int | str:
    """Helper to create a standard bordered table in DearPyGui with optional fixed columns."""
    kwargs: dict[str, Any] = {
        'header_row': True,
        'tag': tag,
        'borders_innerH': True,
        'borders_innerV': True,
        'borders_outerH': True,
        'borders_outerV': True,
    }
    if parent:
        kwargs['parent'] = parent
    if width is not None:
        kwargs['width'] = width
    if height is not None:
        kwargs['height'] = height

    with dpg.table(**kwargs) as tbl:
        if columns:
            for col_label in columns:
                dpg.add_table_column(label=col_label)
    return tbl


def clear_table_rows(table_tag: str) -> None:
    """Helper to clear only row children (slot 1) without touching locked C++ table columns."""
    if dpg.does_item_exist(table_tag):
        children = dpg.get_item_children(table_tag, 1)
        if children:
            for child in children:
                dpg.delete_item(child)


# Global helper to display dynamic matrix in a DearPyGui table container with selectable text
def display_matrix_in_table(matrix: Mapping[Any, Mapping[Any, Any]], table_tag: str) -> None:
    container_tag = f'{table_tag}_container'
    if dpg.does_item_exist(container_tag):
        dpg.delete_item(container_tag, children_only=True)
        if not matrix:
            return

        rows: list[Any] = list(matrix.keys())
        cols: set[Any] = set()
        for r in rows:
            cols.update(matrix[r].keys())
        sorted_cols: list[Any] = sorted(cols)

        with dpg.table(
            tag=table_tag,
            parent=container_tag,
            header_row=True,
            borders_innerH=True,
            borders_innerV=True,
            borders_outerH=True,
            borders_outerV=True,
        ):
            dpg.add_table_column(label='Row/Col')
            for col in sorted_cols:
                dpg.add_table_column(label=str(col))

            for r in sorted(rows):
                with dpg.table_row():
                    dpg.add_input_text(default_value=str(r), readonly=True, width=-1)
                    for c in sorted_cols:
                        val: Any = matrix[r].get(c, '.')
                        if isinstance(val, float):
                            val_str = f'{val:.4f}'.rstrip('0').rstrip('.')
                        elif isinstance(val, set):
                            sorted_set = sorted(val)
                            val_str = '{' + ', '.join(sorted_set) + '}' if val else '{}'
                        elif isinstance(val, tuple) and len(val) == 2:
                            val_str = f'[{val[0]}, {val[1]}]'
                        elif isinstance(val, complex):
                            val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                        else:
                            val_str = str(val)
                        dpg.add_input_text(default_value=val_str, readonly=True, width=-1)


# --- Custom Semiring for CYK Parsing ---
class GrammarSemiring(Semiring[set[str]]):
    def __init__(self, rules: dict[tuple[str, str], set[str]]) -> None:
        self._rules = rules

    @property
    def zero(self) -> set[str]:
        return set()

    @property
    def one(self) -> set[str]:
        return set()

    def add(self, a: set[str], b: set[str]) -> set[str]:
        return a | b

    def mul(self, a: set[str], b: set[str]) -> set[str]:
        res: set[str] = set()
        for lhs in a:
            for rhs in b:
                if (lhs, rhs) in self._rules:
                    res.update(self._rules[(lhs, rhs)])
        return res


# --- Custom Semiring for Convex Hull (Intervals) ---
class IntervalSemiring(Semiring[tuple[float, float]]):
    @property
    def zero(self) -> tuple[float, float]:
        return (float('inf'), float('-inf'))

    @property
    def one(self) -> tuple[float, float]:
        return (0.0, 0.0)

    def add(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        return (min(a[0], b[0]), max(a[1], b[1]))

    def mul(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        return (a[0] + b[0], a[1] + b[1])


# --- Callbacks ---


def semiring_change_callback(sender: int | str, app_data: str) -> None:
    semiring_name: str = app_data
    if semiring_name in ('Tropical', 'Arctic'):
        val = '{\n  "0": {"1": 2.0, "2": 8.0},\n  "1": {"2": 3.0},\n  "2": {"0": 1.0}\n}'
    elif semiring_name == 'Viterbi':
        val = '{\n  "0": {"1": 0.5, "2": 0.1},\n  "1": {"2": 0.5},\n  "2": {"0": 0.9}\n}'
    elif semiring_name == 'String':
        val = '{\n  "0": {"1": ["cd"], "2": ["ab"]},\n  "1": {"2": ["bd"]},\n  "2": {"0": ["da"], "1": ["dc"]}\n}'
    elif semiring_name == 'Expectation':
        val = '{\n  "0": {"1": [0.5, 1.0], "2": [0.1, 1.0]},\n  "1": {"2": [0.5, 1.5]},\n  "2": {"0": [0.9, 0.9]}\n}'
    elif semiring_name == 'Provenance':
        val = '{\n  "0": {"1": {"x": 1}, "2": {"z": 1}},\n  "1": {"2": {"y": 1}},\n  "2": {"0": {"w": 1}}\n}'
    elif semiring_name == 'Variance':
        val = '{\n  "0": {"1": [0.5, 1.0, 1.0, 2.0]},\n  "1": {"2": [1.0, 8.0, 8.0, 64.0]}\n}'
    elif semiring_name == 'Digital':
        val = '{\n  "0": {"0": 123, "1": 456},\n  "1": {"0": 789, "1": 12}\n}'
    elif semiring_name == 'Interval (Convex Hull)':
        val = '{\n  "0": {"1": [1.0, 2.0], "2": [3.0, 4.0]},\n  "1": {"2": [5.0, 6.0]}\n}'
    else:  # Standard
        val = '{\n  "0": {"1": 0.5, "2": 0.1},\n  "1": {"2": 0.5},\n  "2": {"0": 0.9}\n}'

    dpg.set_value('semiring_graph_input', val)


def run_semiring_power() -> None:
    semiring_name: str = dpg.get_value('semiring_select')
    power_val: int = dpg.get_value('semiring_power')
    graph_str: str = dpg.get_value('semiring_graph_input')

    try:
        custom_g: dict[str, dict[str, Any]] = json.loads(graph_str)
        parsed_g: dict[Any, dict[Any, Any]] = {}

        if semiring_name == 'Tropical':
            semiring: Semiring[Any] = TropicalSemiring()
            parser = float
        elif semiring_name == 'Arctic':
            semiring = ArcticSemiring()
            parser = float
        elif semiring_name == 'Viterbi':
            from algebrax.semiring import ViterbiSemiring

            semiring = ViterbiSemiring()
            parser = float
        elif semiring_name == 'String':
            from algebrax.semiring import StringSemiring

            semiring = StringSemiring()
            parser = set
        elif semiring_name == 'Expectation':
            from algebrax.semiring import ExpectationSemiring

            semiring = ExpectationSemiring()

            def parse_expectation(x: list[Any]) -> tuple[float, float]:
                return (float(x[0]), float(x[1]))

            parser = parse_expectation
        elif semiring_name == 'Provenance':
            from algebrax.semiring import ProvenanceSemiring

            semiring = ProvenanceSemiring()

            def parse_provenance(d: dict[str, int]) -> dict[tuple[str, ...], int]:
                return {tuple(k.split(',')) if isinstance(k, str) else tuple(k): int(v) for k, v in d.items()}

            parser = parse_provenance
        elif semiring_name == 'Variance':
            from algebrax.semiring import VarianceSemiring

            semiring = VarianceSemiring()

            def parse_variance(x: list[Any]) -> tuple[float, float, float, float]:
                return (float(x[0]), float(x[1]), float(x[2]), float(x[3]))

            parser = parse_variance
        elif semiring_name == 'Digital':
            from algebrax.semiring import DigitalSemiring

            semiring = DigitalSemiring()
            parser = int
        elif semiring_name == 'Interval (Convex Hull)':
            semiring = IntervalSemiring()

            def parse_interval(x: list[Any]) -> tuple[float, float]:
                return (float(x[0]), float(x[1]))

            parser = parse_interval
        else:
            semiring = StandardSemiring()
            parser = float

        for u, neighbors in custom_g.items():
            u_key = int(u) if u.isdigit() else u
            row: dict[Any, Any] = {}
            for v, w in neighbors.items():
                v_key = int(v) if v.isdigit() else v
                row[v_key] = parser(w)
            parsed_g[u_key] = row

        from algebrax.matrix.core import power

        res = power(parsed_g, power_val, semiring=semiring)

        display_matrix_in_table(res, 'table_semiring_res')
        dpg.set_value('semiring_status', f'Computed {semiring_name} power {power_val} successfully.')
    except Exception as e:
        dpg.set_value('semiring_status', f'Error: {e}')


def run_curvature() -> None:
    graph_str: str = dpg.get_value('curvature_graph_input')
    is_weighted: bool = dpg.get_value('curvature_weighted')
    is_augmented: bool = dpg.get_value('curvature_augmented')

    try:
        raw_g: dict[str, Any] = json.loads(graph_str)
        graph: dict[Any, dict[Any, float]] = {}
        for u, neighbors in raw_g.items():
            u_key = int(u) if u.isdigit() else u
            if isinstance(neighbors, dict):
                graph[u_key] = {
                    int(v) if v.isdigit() else v: float(w) if is_weighted else 1.0 for v, w in neighbors.items()
                }
            elif isinstance(neighbors, list):
                graph[u_key] = {int(v) if str(v).isdigit() else v: 1.0 for v in neighbors}

        res = forman_ricci_curvature(graph, augmented=is_augmented)

        clear_table_rows('table_curvature')
        for (u, v), k_val in sorted(res.items()):
            if k_val < -1e-5:
                k_type = 'Hyperbolic (K < 0)'
            elif k_val > 1e-5:
                k_type = 'Spherical (K > 0)'
            else:
                k_type = 'Flat / Euclidean (K = 0)'

            with dpg.table_row(parent='table_curvature'):
                dpg.add_input_text(default_value=f'({u}, {v})', readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{k_val:.4f}', readonly=True, width=-1)
                dpg.add_input_text(default_value=k_type, readonly=True, width=-1)

        dpg.set_value('curvature_status', 'Successfully computed Forman-Ricci curvature.')
    except Exception as e:
        dpg.set_value('curvature_status', f'Error: {e}')


def run_crypto_exchange() -> None:
    from algebrax.matrix.core import dot
    from algebrax.semiring import DigitalSemiring

    try:
        s_semiring = DigitalSemiring()
        a1: int = int(dpg.get_value('crypto_a1'))
        a2: int = int(dpg.get_value('crypto_a2'))
        b1: int = int(dpg.get_value('crypto_b1'))
        b2: int = int(dpg.get_value('crypto_b2'))

        m_mat: dict[int, dict[int, int]] = {0: {0: 123, 1: 456}, 1: {0: 789, 1: 12}}
        a_mat: dict[int, dict[int, int]] = {0: {0: a1, 1: a2}, 1: {0: a2, 1: a1}}
        b_mat: dict[int, dict[int, int]] = {0: {0: b1, 1: b2}, 1: {0: b2, 1: b1}}

        am_mat = dot(a_mat, m_mat, s_semiring)
        u_mat = dot(am_mat, a_mat, s_semiring)

        bm_mat = dot(b_mat, m_mat, s_semiring)
        v_mat = dot(bm_mat, b_mat, s_semiring)

        av_mat = dot(a_mat, v_mat, s_semiring)
        ka_mat = dot(av_mat, a_mat, s_semiring)

        bu_mat = dot(b_mat, u_mat, s_semiring)
        kb_mat = dot(bu_mat, b_mat, s_semiring)

        display_matrix_in_table(u_mat, 'table_crypto_u')
        display_matrix_in_table(v_mat, 'table_crypto_v')
        display_matrix_in_table(ka_mat, 'table_crypto_ka')
        display_matrix_in_table(kb_mat, 'table_crypto_kb')

        match: bool = ka_mat == kb_mat
        dpg.set_value('crypto_match_text', f'Keys Match: {match}')
        dpg.set_value('crypto_status', 'Successfully performed key exchange simulation.')
    except Exception as e:
        dpg.set_value('crypto_status', f'Error: {e}')


def run_trie_operations() -> None:
    from algebrax.trie import AlgebraicTrie

    try:
        trie: AlgebraicTrie[Any, float] = AlgebraicTrie(semiring=StandardSemiring)
        points_str: str = dpg.get_value('trie_points_input')
        points: list[tuple[list[Any], float]] = json.loads(points_str)

        for coord, val in points:
            trie.add(tuple(coord), float(val))

        contract_dim_str: str = dpg.get_value('trie_contract_dims')
        contract_dims: tuple[int, ...] = tuple(json.loads(contract_dim_str))

        res = trie.contract(contract_dims)

        trie_lines: list[str] = []
        for path in sorted(trie):
            trie_lines.append(f'  Path {path}: {trie[path]}')

        dpg.set_value('trie_contents_text', '\n'.join(trie_lines))
        dpg.set_value('trie_result_text', f'Contracted Result at {contract_dims}: {res}')
        dpg.set_value('trie_status', 'Successfully performed trie operations.')
    except Exception as e:
        dpg.set_value('trie_status', f'Error: {e}')


def run_pagerank() -> None:
    graph_str: str = dpg.get_value('pagerank_graph')
    alpha: float = dpg.get_value('pagerank_alpha')
    iterations: int = dpg.get_value('pagerank_iterations')

    try:
        graph: dict[str, dict[str, float]] = json.loads(graph_str)

        m_matrix: dict[str, dict[str, float]] = {}
        nodes: set[str] = set(graph.keys())
        for u, neighbors in graph.items():
            nodes.update(neighbors.keys())
            degree = len(neighbors)
            if degree > 0:
                m_matrix[u] = dict.fromkeys(neighbors, 1.0 / degree)
            else:
                m_matrix[u] = {u: 1.0}

        all_nodes: list[str] = sorted(nodes)
        n_nodes: int = len(all_nodes)

        v_vec: dict[str, float] = dict.fromkeys(all_nodes, 1.0 / n_nodes)

        from algebrax.matrix.core import dot

        semiring = StandardSemiring()

        for _ in range(iterations):
            v_matrix = {'0': v_vec}
            res_matrix = dot(v_matrix, m_matrix, semiring=semiring)
            v_next_raw = res_matrix.get('0', {})

            v_next: dict[str, float] = {}
            teleport = (1.0 - alpha) / n_nodes
            for node in all_nodes:
                val = v_next_raw.get(node, 0.0)
                v_next[node] = alpha * val + teleport
            v_vec = v_next

        clear_table_rows('table_pagerank')
        sorted_ranks = sorted(v_vec.items(), key=lambda x: x[1], reverse=True)
        for node, rank in sorted_ranks:
            with dpg.table_row(parent='table_pagerank'):
                dpg.add_input_text(default_value=str(node), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{rank:.6f}', readonly=True, width=-1)

        dpg.set_value('pagerank_status', 'Successfully computed PageRank.')
    except Exception as e:
        dpg.set_value('pagerank_status', f'Error: {e}')


def run_cyk_parsing() -> None:
    sentence_str: str = dpg.get_value('cyk_sentence')
    lexicon_str: str = dpg.get_value('cyk_lexicon')
    rules_str: str = dpg.get_value('cyk_rules')

    try:
        sentence: list[str] = sentence_str.strip().split()
        parsed_lexicon: dict[str, list[str]] = json.loads(lexicon_str)
        parsed_rules: dict[str, list[str]] = json.loads(rules_str)

        lexicon: dict[str, set[str]] = {k: set(v) for k, v in parsed_lexicon.items()}
        rules: dict[tuple[str, ...], set[str]] = {tuple(k.split(',')): set(v) for k, v in parsed_rules.items()}

        n_len: int = len(sentence)
        chart: dict[int, dict[int, set[str]]] = {}
        for i, word in enumerate(sentence):
            if i not in chart:
                chart[i] = {}
            chart[i][i + 1] = lexicon.get(word, set())

        from algebrax.matrix.core import dot

        semiring = GrammarSemiring(rules)

        for _ in range(n_len):
            new_spans = dot(chart, chart, semiring=semiring)
            for r, row in new_spans.items():
                if r not in chart:
                    chart[r] = {}
                for c, val in row.items():
                    current = chart[r].get(c, set())
                    chart[r][c] = current | val

        final_tags = chart.get(0, {}).get(n_len, set())

        dpg.set_value('cyk_result_text', f'Sentence parses as final non-terminals: {list(final_tags)}')
        display_matrix_in_table(chart, 'table_cyk_chart')
        dpg.set_value('cyk_status', 'Successfully parsed sentence.')
    except Exception as e:
        dpg.set_value('cyk_status', f'Error: {e}')


def run_legendre_fenchel() -> None:
    signal_str: str = dpg.get_value('fenchel_signal')
    slopes_str: str = dpg.get_value('fenchel_slopes')

    try:
        signal: dict[str, float] = json.loads(signal_str)
        parsed_signal: dict[int | float, float] = {
            float(k) if '.' in k else int(k): float(v) for k, v in signal.items()
        }
        slopes: list[float] = json.loads(slopes_str)

        clear_table_rows('table_fenchel')
        for s in sorted(slopes):
            val = legendre_fenchel(parsed_signal, s)
            with dpg.table_row(parent='table_fenchel'):
                dpg.add_input_text(default_value=f'{s:.2f}'.rstrip('0').rstrip('.'), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{val:.4f}'.rstrip('0').rstrip('.'), readonly=True, width=-1)

        dpg.set_value('fenchel_status', 'Successfully computed Fenchel-Legendre Transform.')
    except Exception as e:
        dpg.set_value('fenchel_status', f'Error: {e}')


def automata_type_callback(sender: int | str, app_data: str) -> None:
    m_type: str = app_data
    if m_type == 'DFA':
        dpg.set_value(
            'automata_transitions',
            '{\n  "q0": {"0": "q0", "1": "q1"},\n  "q1": {"0": "q2", "1": "q0"},\n  "q2": {"0": "q1", "1": "q2"}\n}',
        )
        dpg.set_value('automata_start', '"q0"')
        dpg.set_value('automata_accept', '["q1"]')
        dpg.set_value('automata_input', '1010')
    else:  # NFA
        dpg.set_value(
            'automata_transitions',
            '{\n  "q0": {\n    "0": {"q0": 0.5, "q1": 0.5},\n    "1": {"q1": 1.0}\n  },\n'
            '  "q1": {\n    "0": {"q2": 1.0},\n    "1": {"q0": 0.5, "q2": 0.5}\n  },\n'
            '  "q2": {\n    "0": {"q2": 1.0},\n    "1": {"q2": 1.0}\n  }\n}',
        )
        dpg.set_value('automata_start', '{"q0": 1.0}')
        dpg.set_value('automata_accept', '["q2"]')
        dpg.set_value('automata_input', '01')


def _simulate_dfa_step_by_step(
    seq: list[str],
    start_str: str,
    accept_states: list[Any],
    transitions: dict[Any, dict[Any, Any]],
) -> tuple[list[str], str, tuple[int, int, int]]:
    start_state: Any = start_str.strip().strip('"').strip("'")
    if isinstance(start_state, str) and start_state.isdigit():
        start_state = int(start_state)

    normalized_transitions: dict[Any, dict[Any, Any]] = {}
    for s, trans in transitions.items():
        s_key = int(s) if str(s).isdigit() else s
        normalized_transitions[s_key] = {}
        for sym, ns in trans.items():
            sym_key = int(sym) if str(sym).isdigit() else sym
            ns_val = int(ns) if isinstance(ns, str) and ns.isdigit() else ns
            normalized_transitions[s_key][sym_key] = ns_val

    normalized_accept: set[Any] = {int(ac) if isinstance(ac, str) and ac.isdigit() else ac for ac in accept_states}

    current: Any = start_state
    steps_log: list[str] = [f'Start state: {current}']

    for idx, symbol in enumerate(seq):
        sym_key = int(symbol) if symbol.isdigit() else symbol
        next_state = dfa_step(current, sym_key, normalized_transitions)
        if next_state is None:
            steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> No transition defined from '{current}' (Crashed)")
            current = None
            break
        steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> {current} to {next_state}")
        current = next_state

    if current is not None and current in normalized_accept:
        status = f'ACCEPTED (Final state: {current})'
        status_color = (100, 255, 100)
    else:
        status = f'REJECTED (Final state: {current})'
        status_color = (255, 100, 100)
    return steps_log, status, status_color


def _simulate_nfa_step_by_step(
    seq: list[str],
    start_str: str,
    accept_states: list[Any],
    transitions: dict[Any, dict[Any, Any]],
) -> tuple[list[str], str, tuple[int, int, int]]:
    start_states: Any = json.loads(start_str)
    if isinstance(start_states, str):
        s_val = int(start_states) if start_states.isdigit() else start_states
        start_dist: dict[Any, float] = {s_val: 1.0}
    elif isinstance(start_states, list):
        start_dist = {int(s) if str(s).isdigit() else s: 1.0 for s in start_states}
    elif isinstance(start_states, dict):
        start_dist = {int(k) if str(k).isdigit() else k: float(v) for k, v in start_states.items()}
    else:
        start_dist = {}

    if not start_dist:
        return (
            ['Error: Invalid format for start states.'],
            'REJECTED (Error)',
            (255, 100, 100),
        )

    normalized_transitions: dict[Any, dict[Any, dict[Any, float]]] = {}
    for s, trans in transitions.items():
        s_key = int(s) if str(s).isdigit() else s
        normalized_transitions[s_key] = {}
        for sym, nexts in trans.items():
            sym_key = int(sym) if str(sym).isdigit() else sym
            normalized_transitions[s_key][sym_key] = {}
            if isinstance(nexts, list):
                for ns in nexts:
                    ns_key = int(ns) if str(ns).isdigit() else ns
                    normalized_transitions[s_key][sym_key][ns_key] = 1.0
            elif isinstance(nexts, dict):
                for ns, w in nexts.items():
                    ns_key = int(ns) if str(ns).isdigit() else ns
                    normalized_transitions[s_key][sym_key][ns_key] = float(w)
            else:
                ns_key = int(nexts) if str(nexts).isdigit() else nexts
                normalized_transitions[s_key][sym_key][ns_key] = 1.0

    normalized_accept = {int(ac) if isinstance(ac, str) and ac.isdigit() else ac for ac in accept_states}

    current = start_dist
    steps_log = [f'Start states distribution: {current}']

    for idx, symbol in enumerate(seq):
        sym_key = int(symbol) if symbol.isdigit() else symbol
        next_states = nfa_step(current, sym_key, normalized_transitions)
        if not next_states:
            steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> No active transitions (Crashed)")
            current = {}
            break
        steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> Distribution: {next_states}")
        current = next_states

    accept_weight = sum(w for s, w in current.items() if s in normalized_accept)
    if accept_weight > 1e-9:
        status = f'ACCEPTED (Accepting Weight: {accept_weight:.4f})'
        status_color = (100, 255, 100)
    else:
        status = 'REJECTED (No accepting weight)'
        status_color = (255, 100, 100)
    return steps_log, status, status_color


def run_automata_sim() -> None:
    auto_type: str = dpg.get_value('automata_type')
    start_str: str = dpg.get_value('automata_start')
    accept_str: str = dpg.get_value('automata_accept')
    input_str: str = dpg.get_value('automata_input')
    trans_str: str = dpg.get_value('automata_transitions')

    try:
        accept_states: list[Any] = json.loads(accept_str)
        transitions: dict[Any, dict[Any, Any]] = json.loads(trans_str)

        seq: list[str] = (
            [s.strip() for s in input_str.split(',') if s.strip()] if ',' in input_str else list(input_str.strip())
        )

        if auto_type == 'DFA':
            steps_log, status, _ = _simulate_dfa_step_by_step(seq, start_str, accept_states, transitions)
        else:
            steps_log, status, _ = _simulate_nfa_step_by_step(seq, start_str, accept_states, transitions)

        dpg.set_value('automata_result_text', status)
        dpg.set_value('automata_log_text', '\n'.join(steps_log))
        dpg.set_value('automata_status', f'Successfully simulated {auto_type}.')
    except Exception as e:
        dpg.set_value('automata_status', f'Error: {e}')


def run_markov_simulation() -> None:
    matrix_str: str = dpg.get_value('markov_matrix')
    state_str: str = dpg.get_value('markov_state')
    steps: int = dpg.get_value('markov_steps')

    try:
        raw_matrix: dict[str, dict[str, float]] = json.loads(matrix_str)
        raw_state: dict[str, float] = json.loads(state_str)

        matrix: dict[Any, dict[Any, float]] = {
            int(u) if u.isdigit() else u: {int(v) if v.isdigit() else v: float(w) for v, w in n.items()}
            for u, n in raw_matrix.items()
        }
        state: dict[Any, float] = {int(k) if k.isdigit() else k: float(v) for k, v in raw_state.items()}

        curr_state = state
        for _ in range(steps):
            curr_state = markov_step(curr_state, matrix)

        steady = markov_steady_state(matrix)

        clear_table_rows('table_markov_steps')
        for s_key, prob in sorted(curr_state.items()):
            with dpg.table_row(parent='table_markov_steps'):
                dpg.add_input_text(default_value=str(s_key), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{prob:.4f}', readonly=True, width=-1)

        clear_table_rows('table_markov_steady')
        for s_key, prob in sorted(steady.items()):
            with dpg.table_row(parent='table_markov_steady'):
                dpg.add_input_text(default_value=str(s_key), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{prob:.4f}', readonly=True, width=-1)

        dpg.set_value('markov_status', f'Successfully computed {steps} Markov step(s) & steady state.')
    except Exception as e:
        dpg.set_value('markov_status', f'Error: {e}')


def run_info_theory() -> None:
    p_str: str = dpg.get_value('info_p')
    q_str: str = dpg.get_value('info_q')
    joint_str: str = dpg.get_value('info_joint')

    try:
        p_dist: dict[Any, float] = {int(k) if k.isdigit() else k: float(v) for k, v in json.loads(p_str).items()}
        q_dist: dict[Any, float] = {int(k) if k.isdigit() else k: float(v) for k, v in json.loads(q_str).items()}

        raw_joint: dict[str, dict[str, float]] = json.loads(joint_str)
        joint_dist: dict[Any, dict[Any, float]] = {
            int(u) if u.isdigit() else u: {int(v) if v.isdigit() else v: float(w) for v, w in n.items()}
            for u, n in raw_joint.items()
        }

        h_p = entropy(p_dist)
        h_q = entropy(q_dist)
        h_cross = cross_entropy(p_dist, q_dist)
        kl_div = kl_divergence(p_dist, q_dist)
        mi_val = mutual_information(joint_dist)

        dpg.set_value('info_hp_val', f'{h_p:.4f} bits')
        dpg.set_value('info_hq_val', f'{h_q:.4f} bits')
        dpg.set_value('info_hcross_val', f'{h_cross:.4f} bits')
        dpg.set_value('info_kl_val', f'{kl_div:.4f} bits')
        dpg.set_value('info_mi_val', f'{mi_val:.4f} bits')

        dpg.set_value('info_status', 'Successfully computed information metrics.')
    except Exception as e:
        dpg.set_value('info_status', f'Error: {e}')


def signal_op_change_callback(sender: int | str, app_data: str) -> None:
    op: str = app_data
    dpg.show_item('signal_g_group') if op == 'Convolution' else dpg.hide_item('signal_g_group')
    dpg.show_item('signal_z_group') if op == 'Z-Transform' else dpg.hide_item('signal_z_group')


def run_signal_transforms() -> None:
    op: str = dpg.get_value('signal_op_select')
    f_str: str = dpg.get_value('signal_f')

    try:
        raw_f: dict[str, Any] = json.loads(f_str)
        f_vec: dict[int, Any] = {int(k): complex(v) if isinstance(v, str) else float(v) for k, v in raw_f.items()}

        if op == 'DFT':
            res = dft(f_vec)
        elif op == 'IDFT':
            res = idft(f_vec)
        elif op == 'Hilbert Transform':
            res = hilbert(f_vec)
        elif op == 'Convolution':
            g_str: str = dpg.get_value('signal_g')
            raw_g: dict[str, Any] = json.loads(g_str)
            g_vec = {int(k): float(v) for k, v in raw_g.items()}
            res = convolve(f_vec, g_vec)
        elif op == 'Z-Transform':
            z_str: str = dpg.get_value('signal_z_input')
            z_val = complex(z_str)
            res_val = z_transform(f_vec, z_val)
            res = {0: res_val}
        else:
            res = {}

        clear_table_rows('table_signal_res')
        for k in sorted(res.keys()):
            val = res[k]
            with dpg.table_row(parent='table_signal_res'):
                dpg.add_input_text(default_value=str(k), readonly=True, width=-1)
                if isinstance(val, complex):
                    val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                else:
                    val_str = f'{val:.4f}'
                dpg.add_input_text(default_value=val_str, readonly=True, width=-1)

        dpg.set_value('signal_status', f'Successfully evaluated {op}.')
    except Exception as e:
        dpg.set_value('signal_status', f'Error: {e}')


def run_blackhole_sim() -> None:
    try:
        r_s: float = float(dpg.get_value('bh_rs'))
        r: float = float(dpg.get_value('bh_r'))
        b: float = float(dpg.get_value('bh_b'))

        g_tt = -(1.0 - r_s / r) if r != 0 else 0.0
        g_rr = (1.0 / (1.0 - r_s / r)) if (r != r_s and r != 0) else float('inf')

        deflect_rad = (2.0 * r_s) / b if b != 0 else 0.0
        deflect_deg = math.degrees(deflect_rad)

        horizon_area = 4.0 * math.pi * (r_s**2)
        hawking_entropy = horizon_area / 4.0

        clear_table_rows('table_bh_res')
        rows = [
            ('Schwarzschild Radius (r_s)', f'{r_s:.2f} km'),
            ('Observation Radius (r)', f'{r:.2f} km'),
            ('Time Metric Component g_tt(r)', f'{g_tt:.6f}'),
            ('Radial Metric Component g_rr(r)', f'{g_rr:.6f}'),
            ('Photon Deflection Angle (Delta phi)', f'{deflect_rad:.4f} rad ({deflect_deg:.2f} deg)'),
            ('Event Horizon Area (A)', f'{horizon_area:.2f} km^2'),
            ('Bekenstein-Hawking Entropy (S_BH)', f'{hawking_entropy:.2f} nats'),
        ]

        for prop, val in rows:
            with dpg.table_row(parent='table_bh_res'):
                dpg.add_input_text(default_value=prop, readonly=True, width=-1)
                dpg.add_input_text(default_value=val, readonly=True, width=-1)

        dpg.set_value('bh_status', 'Successfully evaluated Schwarzschild spacetime metric.')
    except Exception as e:
        dpg.set_value('bh_status', f'Error: {e}')


def run_sparse_tensor_einsum() -> None:
    from algebrax.tensor import einsum
    from algebrax.trie import AlgebraicTrie

    subscripts: str = dpg.get_value('tensor_subscripts')
    semiring_name: str = dpg.get_value('tensor_semiring')
    a_str: str = dpg.get_value('tensor_a_input')
    b_str: str = dpg.get_value('tensor_b_input')

    try:
        raw_a: list[tuple[list[Any], float]] = json.loads(a_str)
        raw_b: list[tuple[list[Any], float]] = json.loads(b_str)

        trie_a: AlgebraicTrie[Any, float] = AlgebraicTrie(semiring=StandardSemiring)
        for coord, val in raw_a:
            trie_a[tuple(coord)] = float(val)

        trie_b: AlgebraicTrie[Any, float] = AlgebraicTrie(semiring=StandardSemiring)
        for coord, val in raw_b:
            trie_b[tuple(coord)] = float(val)

        if 'Tropical' in semiring_name:
            semiring: Semiring[float] = TropicalSemiring()
        elif 'Arctic' in semiring_name:
            semiring = ArcticSemiring()
        else:
            semiring = StandardSemiring()

        res_trie = einsum(subscripts, trie_a, trie_b, semiring=semiring)

        clear_table_rows('table_tensor_einsum_res')
        for key in sorted(res_trie):
            with dpg.table_row(parent='table_tensor_einsum_res'):
                dpg.add_input_text(default_value=str(key), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{res_trie[key]:.4f}', readonly=True, width=-1)

        dpg.set_value('tensor_einsum_status', f"Successfully evaluated einsum('{subscripts}').")
    except Exception as e:
        dpg.set_value('tensor_einsum_status', f'Error: {e}')


def run_trajectoid_sim() -> None:
    from algebrax.analysis import gradient
    from algebrax.matrix.core import dot

    steps: int = dpg.get_value('trajectoid_steps')
    freq: float = dpg.get_value('trajectoid_freq')

    try:
        t_vals = [i * (2.0 * math.pi / steps) for i in range(steps)]
        x_path = {i: math.cos(t_vals[i]) for i in range(steps)}
        y_path = {i: math.sin(freq * t_vals[i]) for i in range(steps)}

        time_graph = {i: [(i + 1) % steps] for i in range(steps)}
        grad_x = gradient(x_path, time_graph)
        grad_y = gradient(y_path, time_graph)

        vx = {i: grad_x[i][(i + 1) % steps] for i in range(steps)}
        vy = {i: grad_y[i][(i + 1) % steps] for i in range(steps)}

        state_mat: dict[int, dict[int, float]] = {
            0: {0: 1.0, 1: 0.0, 2: 0.0},
            1: {0: 0.0, 1: 1.0, 2: 0.0},
            2: {0: 0.0, 1: 0.0, 2: 1.0},
        }
        for i in range(min(steps, 10)):
            w_x = vx.get(i, 0.0) * 0.1
            w_y = vy.get(i, 0.0) * 0.1
            dr = {
                0: {0: 1.0, 1: 0.0, 2: w_y},
                1: {0: 0.0, 1: 1.0, 2: -w_x},
                2: {0: -w_y, 1: w_x, 2: 1.0},
            }
            state_mat = dot(state_mat, dr)

        display_matrix_in_table(state_mat, 'table_trajectoid_so3')
        dpg.set_value('trajectoid_status', 'Successfully integrated non-holonomic SO(3) rolling trajectory.')
    except Exception as e:
        dpg.set_value('trajectoid_status', f'Error: {e}')


def run_knot_theory() -> None:
    from algebrax.group import compose, signature
    from algebrax.semiring import KnotSemiring

    knot_a_name: str = dpg.get_value('knot_a_select')
    knot_b_name: str = dpg.get_value('knot_b_select')
    crossings_str: str = dpg.get_value('knot_crossings')

    try:
        knot_algebra = KnotSemiring(StandardSemiring[float]())
        knot_a = {knot_a_name: 1.0}
        knot_b = {knot_b_name: 1.0}

        composite_knot = knot_algebra.mul(knot_a, knot_b)

        crossings: list[int] = json.loads(crossings_str)
        n_strands = max(max(crossings, default=1) + 1, 2)
        perm: dict[int, int] = {i: i for i in range(n_strands)}
        for c in crossings:
            if 1 <= c < n_strands:
                swap_gen = {i: i for i in range(n_strands)}
                swap_gen[c - 1], swap_gen[c] = c, c - 1
                perm = compose(perm, swap_gen)

        sig = signature(perm)

        clear_table_rows('table_knot_res')
        rows = [
            ('Knot A Topology', knot_a_name),
            ('Knot B Topology', knot_b_name),
            ('Connected Sum A (#) B', str(composite_knot)),
            ('Artin Braid Strand Count', str(n_strands)),
            ('Artin Braid Permutation', str(perm)),
            ('Braid Crossing Parity Signature', f'{sig} ({"Even (+1)" if sig == 1 else "Odd (-1)"})'),
        ]

        for prop, val in rows:
            with dpg.table_row(parent='table_knot_res'):
                dpg.add_input_text(default_value=prop, readonly=True, width=-1)
                dpg.add_input_text(default_value=val, readonly=True, width=-1)

        dpg.set_value('knot_status', 'Successfully evaluated Knot connected sum & Braid signatures.')
    except Exception as e:
        dpg.set_value('knot_status', f'Error: {e}')


def run_optical_holography() -> None:
    from algebrax.probability import entropy
    from algebrax.transforms import dft

    ref_phase: float = float(dpg.get_value('hologram_ref_phase'))
    object_str: str = dpg.get_value('hologram_object_input')

    try:
        raw_obj: dict[str, Any] = json.loads(object_str)
        obj_wave: dict[int, complex] = {
            int(k): complex(v) if isinstance(v, str) else complex(float(v), 0.0) for k, v in raw_obj.items()
        }

        ref_wave: dict[int, complex] = {k: cmath.exp(1j * ref_phase * k) for k in obj_wave}

        interf_intensity: dict[int, float] = {}
        for k in obj_wave:
            total_field = obj_wave[k] + ref_wave[k]
            interf_intensity[k] = float(abs(total_field) ** 2)

        spectrum = dft({k: complex(v, 0.0) for k, v in interf_intensity.items()})

        total_int = sum(interf_intensity.values())
        prob_dist = {k: interf_intensity[k] / total_int for k in interf_intensity} if total_int > 0 else {}
        fringe_entropy = entropy(prob_dist)

        clear_table_rows('table_hologram_res')
        for k in sorted(interf_intensity.keys()):
            val_i = interf_intensity[k]
            val_f = spectrum.get(k, 0.0 + 0.0j)
            f_str = f'{val_f.real:.2f}+{val_f.imag:.2f}j' if isinstance(val_f, complex) else f'{val_f:.2f}'
            with dpg.table_row(parent='table_hologram_res'):
                dpg.add_input_text(default_value=str(k), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{val_i:.4f}', readonly=True, width=-1)
                dpg.add_input_text(default_value=f_str, readonly=True, width=-1)

        dpg.set_value(
            'hologram_status',
            f'Successfully recorded optical hologram (Fringe Entropy: {fringe_entropy:.4f} bits).',
        )
    except Exception as e:
        dpg.set_value('hologram_status', f'Error: {e}')


def run_financial_risk() -> None:
    from algebrax.automata import simulate_dfa
    from algebrax.matrix.academic import eigen_centrality

    signal_input: str = dpg.get_value('fin_signals')
    corr_str: str = dpg.get_value('fin_corr_matrix')

    try:
        signals = [s.strip() for s in signal_input.split(',') if s.strip()]

        dfa = {
            'Cash': {'buy_signal': 'Invested', 'hold': 'Cash', 'risk_alert': 'Risk_Hedge'},
            'Invested': {'sell_signal': 'Cash', 'risk_alert': 'Risk_Hedge', 'hold': 'Invested'},
            'Risk_Hedge': {'clear_alert': 'Cash', 'hold': 'Risk_Hedge'},
        }

        final_state = simulate_dfa('Cash', signals, dfa)

        raw_corr: dict[str, dict[str, float]] = json.loads(corr_str)
        centrality = eigen_centrality(raw_corr)

        clear_table_rows('table_fin_centrality')
        for asset, val in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
            with dpg.table_row(parent='table_fin_centrality'):
                dpg.add_input_text(default_value=asset, readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{val:.4f}', readonly=True, width=-1)

        dpg.set_value('fin_result_text', f'Final Trade Strategy State: {final_state}')
        dpg.set_value('fin_status', 'Successfully computed portfolio centrality & trade DFA execution.')
    except Exception as e:
        dpg.set_value('fin_status', f'Error: {e}')


def run_sheaf_cohomology() -> None:
    from algebrax.analysis import laplacian

    sensor_str: str = dpg.get_value('sheaf_states_input')
    steps: int = dpg.get_value('sheaf_steps')

    try:
        raw_states: dict[str, float] = json.loads(sensor_str)
        agent_states: dict[int, float] = {int(k): float(v) for k, v in raw_states.items()}

        comm_graph: dict[int, dict[int, float]] = {
            0: {1: 1.0, 2: 1.0},
            1: {0: 1.0, 3: 1.0},
            2: {0: 1.0, 3: 1.0},
            3: {1: 1.0, 2: 1.0},
        }

        curr_states = dict(agent_states)
        dt = 0.1
        for _ in range(steps):
            l_val = laplacian(curr_states, comm_graph)
            for u in curr_states:
                curr_states[u] -= dt * l_val.get(u, 0.0)

        clear_table_rows('table_sheaf_res')
        for u in sorted(agent_states.keys()):
            with dpg.table_row(parent='table_sheaf_res'):
                dpg.add_input_text(default_value=str(u), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{agent_states[u]:.2f}', readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{curr_states[u]:.2f}', readonly=True, width=-1)

        dpg.set_value('sheaf_status', f'Successfully evaluated cellular sheaf consensus after {steps} steps.')
    except Exception as e:
        dpg.set_value('sheaf_status', f'Error: {e}')


def run_gaussian_splatting() -> None:
    from gaussian_splatting_rendering import compute_2d_projected_covariance, compute_3d_covariance

    try:
        sx: float = float(dpg.get_value('gs_scale_x'))
        sy: float = float(dpg.get_value('gs_scale_y'))
        sz: float = float(dpg.get_value('gs_scale_z'))

        pitch: float = math.radians(float(dpg.get_value('gs_rot_pitch')))
        yaw: float = math.radians(float(dpg.get_value('gs_rot_yaw')))
        roll: float = math.radians(float(dpg.get_value('gs_rot_roll')))

        px: float = float(dpg.get_value('gs_pos_x'))
        py: float = float(dpg.get_value('gs_pos_y'))
        pz: float = float(dpg.get_value('gs_pos_z'))
        focal: float = float(dpg.get_value('gs_focal'))

        sigma_3d = compute_3d_covariance((sx, sy, sz), (pitch, yaw, roll))
        sigma_2d = compute_2d_projected_covariance(sigma_3d, (px, py, pz), focal_length=focal)

        display_matrix_in_table(sigma_3d, 'table_gs_3d_cov')
        display_matrix_in_table(sigma_2d, 'table_gs_2d_cov')

        # Redraw 2D Projected Gaussian Ellipse Canvas
        if dpg.does_item_exist('gs_canvas'):
            dpg.delete_item('gs_canvas', children_only=True)
            # Opaque viewport background (Directive 3)
            dpg.draw_rectangle(
                (0, 0), (700, 320), fill=(18, 18, 24), color=(60, 60, 80), thickness=1, parent='gs_canvas'
            )

            # Screen center
            center_x, center_y = 350, 160
            tz = max(pz, 0.1)
            proj_x = center_x + int(focal * px / tz * 50.0)
            proj_y = center_y - int(focal * py / tz * 50.0)

            # Draw projected Gaussian ellipse using 2D covariance eigenvalues/radii
            cov_xx = sigma_2d.get(0, {}).get(0, 0.1)
            cov_yy = sigma_2d.get(1, {}).get(1, 0.1)
            cov_xy = sigma_2d.get(0, {}).get(1, 0.0)

            # Eigenvalues of 2D covariance
            tr = cov_xx + cov_yy
            det = max(cov_xx * cov_yy - cov_xy * cov_xy, 1e-6)
            term = max((tr / 2.0) ** 2 - det, 0.0) ** 0.5
            l1 = max(tr / 2.0 + term, 0.01)
            l2 = max(tr / 2.0 - term, 0.01)

            r1 = min(max(int(math.sqrt(l1) * 80.0), 5), 180)
            r2 = min(max(int(math.sqrt(l2) * 80.0), 5), 180)

            p_min = (proj_x - r1, proj_y - r2)
            p_max = (proj_x + r1, proj_y + r2)

            dpg.draw_ellipse(
                p_min, p_max, color=(255, 120, 80, 220), fill=(255, 100, 50, 60), thickness=2, parent='gs_canvas'
            )
            dpg.draw_circle((proj_x, proj_y), radius=4, color=(255, 255, 255), fill=(255, 255, 255), parent='gs_canvas')
            dpg.draw_text(
                (proj_x + 10, proj_y - 10),
                f'3D Splat mu=({px:.1f}, {py:.1f}, {pz:.1f})',
                color=(220, 220, 255),
                size=13,
                parent='gs_canvas',
            )

        dpg.set_value('gs_status', 'Successfully evaluated 3D spatial covariance & 2D projective screen splatting.')
    except Exception as e:
        dpg.set_value('gs_status', f'Error: {e}')


def run_topological_homology() -> None:
    from algebrax.homology import SimplicialComplex

    try:
        max_k: int = int(dpg.get_value('homology_max_k'))
        sc = SimplicialComplex([(0, 1, 2, 3)])
        betti = sc.betti_numbers(max_k=max_k)

        betti_data = [{'dim': f'beta_{k}', 'count': betti.get(k, 0)} for k in range(max_k + 1)]
        display_matrix_in_table(betti_data, 'table_homology_res')
        dpg.set_value('homology_status', f'Successfully evaluated Simplicial Homology Betti numbers up to k={max_k}.')
    except Exception as e:
        dpg.set_value('homology_status', f'Error: {e}')


def run_clifford_geometric_algebra() -> None:
    import math

    from algebrax.clifford import CliffordSemiring, rotor_rotation

    try:
        e1: float = float(dpg.get_value('clifford_v_e1'))
        e2: float = float(dpg.get_value('clifford_v_e2'))
        angle_deg: float = float(dpg.get_value('clifford_angle'))

        cs = CliffordSemiring(p=3, q=0, r=0)
        v = {(1,): e1, (2,): e2}
        v_sq = cs.mul(v, v)
        v_rot = rotor_rotation(v, bivector=(1, 2), angle_rad=math.radians(angle_deg), p=3, q=0, r=0)

        dpg.set_value('clifford_v_sq_text', f'Vector Squared v^2 = {v_sq.get((), 0.0):.3f}')

        rot_data = [
            {'comp': 'e1 Component', 'orig': e1, 'rot': v_rot.get((1,), 0.0)},
            {'comp': 'e2 Component', 'orig': e2, 'rot': v_rot.get((2,), 0.0)},
        ]
        display_matrix_in_table(rot_data, 'table_clifford_res')
        dpg.set_value(
            'clifford_status', f'Successfully evaluated 3D Rotor rotation by {angle_deg:.1f} deg in e12 plane.'
        )
    except Exception as e:
        dpg.set_value('clifford_status', f'Error: {e}')


def run_galois_finite_fields() -> None:
    from algebrax.galois import GaloisFieldSemiring, gf_matrix_mul

    try:
        exp1: int = int(dpg.get_value('galois_exp1'))
        exp2: int = int(dpg.get_value('galois_exp2'))

        gf = GaloisFieldSemiring(p=2, irreduc_poly=(1, 1, 0, 1, 1, 0, 0, 0, 1))
        res_poly = gf.mul({exp1: 1}, {exp2: 1})

        dpg.set_value('galois_poly_res_text', f'x^{exp1} * x^{exp2} mod P(x) = {res_poly}')

        mix_col = {0: {0: {1: 1}, 1: {0: 1}}, 1: {0: {0: 1}, 1: {1: 1}}}
        state = {0: {0: {exp1: 1}}, 1: {0: {exp2: 1}}}
        out_state = gf_matrix_mul(mix_col, state, p=2)

        gf_data = [{'col': f'Col {c}', 'out': str(out_state.get(c, {}))} for c in [0, 1]]
        display_matrix_in_table(gf_data, 'table_galois_res')
        dpg.set_value('galois_status', 'Successfully evaluated AES GF(2^8) MixColumns matrix product.')
    except Exception as e:
        dpg.set_value('galois_status', f'Error: {e}')


def run_categorical_kleisli() -> None:
    from algebrax.category import kleisli_compose
    from algebrax.semiring import BooleanSemiring, TropicalSemiring, ViterbiSemiring

    try:
        f_val: float = float(dpg.get_value('kleisli_f_val'))
        g_val: float = float(dpg.get_value('kleisli_g_val'))

        f_prob = {'A': {'B': f_val}}
        g_prob = {'B': {'C': g_val}}

        vit = kleisli_compose(f_prob, g_prob, semiring=ViterbiSemiring())
        trop = kleisli_compose({'A': {'B': f_val}}, {'B': {'C': g_val}}, semiring=TropicalSemiring())
        boo = kleisli_compose({'A': {'B': True}}, {'B': {'C': True}}, semiring=BooleanSemiring())

        cat_data = [
            {'monad': 'Viterbi Probabilistic Monad', 'res': f'{vit.get("A", {}).get("C", 0.0):.4f}'},
            {'monad': 'Tropical Lawvere Cost Monad', 'res': f'{trop.get("A", {}).get("C", 0.0):.4f}'},
            {'monad': 'Boolean Reachability Monad', 'res': str(boo.get('A', {}).get('C', False))},
        ]
        display_matrix_in_table(cat_data, 'table_kleisli_res')
        dpg.set_value('kleisli_status', 'Successfully evaluated Kleisli monadic compositions.')
    except Exception as e:
        dpg.set_value('kleisli_status', f'Error: {e}')


# --- Image Convolution Helpers ---
IMAGE_PRESETS: dict[str, str] = {
    'Cross Pattern (8x8)': (
        '{\n'
        '  "0,3": 1.0, "1,3": 1.0, "2,3": 1.0, "3,3": 1.0, "4,3": 1.0, "5,3": 1.0, "6,3": 1.0, "7,3": 1.0,\n'
        '  "3,0": 1.0, "3,1": 1.0, "3,2": 1.0, "3,4": 1.0, "3,5": 1.0, "3,6": 1.0, "3,7": 1.0\n'
        '}'
    ),
    'Diagonal Line (8x8)': (
        '{\n  "0,0": 1.0, "1,1": 1.0, "2,2": 1.0, "3,3": 1.0,\n  "4,4": 1.0, "5,5": 1.0, "6,6": 1.0, "7,7": 1.0\n}'
    ),
    'Box Square (8x8)': (
        '{\n'
        '  "2,2": 1.0, "2,3": 1.0, "2,4": 1.0, "2,5": 1.0,\n'
        '  "3,2": 1.0, "3,5": 1.0, "4,2": 1.0, "4,5": 1.0,\n'
        '  "5,2": 1.0, "5,3": 1.0, "5,4": 1.0, "5,5": 1.0\n'
        '}'
    ),
}

KERNEL_PRESETS: dict[str, str] = {
    'Sobel Horizontal (Edge)': (
        '{\n  "-1,-1": -1.0, "-1,0": -2.0, "-1,1": -1.0,\n  "1,-1": 1.0, "1,0": 2.0, "1,1": 1.0\n}'
    ),
    'Sobel Vertical (Edge)': (
        '{\n  "-1,-1": -1.0, "0,-1": -2.0, "1,-1": -1.0,\n  "-1,1": 1.0, "0,1": 2.0, "1,1": 1.0\n}'
    ),
    'Gaussian Blur (3x3)': (
        '{\n'
        '  "-1,-1": 0.0625, "-1,0": 0.125, "-1,1": 0.0625,\n'
        '  "0,-1": 0.125, "0,0": 0.25, "0,1": 0.125,\n'
        '  "1,-1": 0.0625, "1,0": 0.125, "1,1": 0.0625\n'
        '}'
    ),
    'Sharpen Kernel': '{\n  "0,-1": -1.0, "-1,0": -1.0, "0,0": 5.0, "1,0": -1.0, "0,1": -1.0\n}',
    'Morphological Dilation (Max-Plus)': '{\n  "0,-1": 0.0, "-1,0": 0.0, "0,0": 0.0, "1,0": 0.0, "0,1": 0.0\n}',
}


def image_preset_change_callback(sender: int | str, app_data: str) -> None:
    if app_data in IMAGE_PRESETS:
        dpg.set_value('img_conv_image_input', IMAGE_PRESETS[app_data])


def kernel_preset_change_callback(sender: int | str, app_data: str) -> None:
    if app_data in KERNEL_PRESETS:
        dpg.set_value('img_conv_kernel_input', KERNEL_PRESETS[app_data])


def open_file_dialog_callback(sender: int | str, app_data: Any) -> None:
    def file_selected_callback(sender: int | str, app_data: dict[str, Any]) -> None:
        if 'file_path_name' in app_data:
            filepath: str = app_data['file_path_name']
            dpg.set_value('img_conv_filepath_input', filepath)
            load_image_file_into_lab(filepath)

    with dpg.file_dialog(
        directory_selector=False,
        show=True,
        callback=file_selected_callback,
        width=700,
        height=400,
        modal=True,
    ):
        dpg.add_file_extension('.*', color=(255, 255, 255, 255))
        dpg.add_file_extension('.png', color=(0, 255, 0, 255))
        dpg.add_file_extension('.jpg', color=(0, 255, 0, 255))
        dpg.add_file_extension('.bmp', color=(0, 255, 0, 255))


def load_image_file_into_lab(filepath: str) -> None:
    if not HAS_PILLOW:
        dpg.set_value('img_conv_status', 'Error: Pillow library is not installed.')
        return

    try:
        img = Image.open(filepath).convert('L')
        img = img.resize((TEXTURE_WIDTH, TEXTURE_HEIGHT), Image.Resampling.BILINEAR)

        dict_image: dict[str, float] = {}
        texture_data: list[float] = []
        for r in range(TEXTURE_HEIGHT):
            for c in range(TEXTURE_WIDTH):
                pixel: int = img.getpixel((c, r))
                norm_val: float = pixel / 255.0
                if norm_val > 1e-4:
                    dict_image[f'{r},{c}'] = round(norm_val, 4)
                texture_data.extend([norm_val, norm_val, norm_val, 1.0])

        dpg.set_value('img_conv_image_input', json.dumps(dict_image, indent=2))
        dpg.set_value('texture_img_input', texture_data)
        dpg.set_value('img_conv_status', f'Successfully loaded and downsampled image: {filepath}')
    except Exception as e:
        dpg.set_value('img_conv_status', f'Error loading image: {e}')


def _update_texture_from_2d_dict(data_dict: Mapping[tuple[int, int], float], texture_tag: str) -> None:
    texture_data: list[float] = []
    max_val: float = max(data_dict.values(), default=1.0)
    min_val: float = min(data_dict.values(), default=0.0)
    val_range: float = max_val - min_val if max_val != min_val else 1.0

    for r in range(TEXTURE_HEIGHT):
        for c in range(TEXTURE_WIDTH):
            val = data_dict.get((r, c), 0.0)
            norm = (val - min_val) / val_range
            texture_data.extend([norm, norm, norm, 1.0])

    dpg.set_value(texture_tag, texture_data)


def run_image_convolution_2d() -> None:
    img_str: str = dpg.get_value('img_conv_image_input')
    kernel_str: str = dpg.get_value('img_conv_kernel_input')
    semiring_name: str = dpg.get_value('img_conv_semiring_select')

    try:
        raw_img: dict[str, float] = json.loads(img_str)
        raw_kernel: dict[str, float] = json.loads(kernel_str)

        image_2d: dict[tuple[int, int], float] = {}
        for k, v in raw_img.items():
            r, c = map(int, k.split(','))
            image_2d[(r, c)] = float(v)

        kernel_2d: dict[tuple[int, int], float] = {}
        for k, v in raw_kernel.items():
            r, c = map(int, k.split(','))
            kernel_2d[(r, c)] = float(v)

        if 'Arctic' in semiring_name:
            semiring: Semiring[float] = ArcticSemiring()
        elif 'Tropical' in semiring_name:
            semiring = TropicalSemiring()
        else:
            semiring = StandardSemiring()

        def add_2d(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
            return (p1[0] + p2[0], p1[1] + p2[1])

        convolved_2d = convolve(image_2d, kernel_2d, key_op=add_2d, semiring=semiring)

        _update_texture_from_2d_dict(image_2d, 'texture_img_input')
        _update_texture_from_2d_dict(convolved_2d, 'texture_img_output')

        rows = [r for r, c in convolved_2d]
        cols = [c for r, c in convolved_2d]
        min_r, max_r = (min(rows), max(rows)) if rows else (0, 7)
        min_c, max_c = (min(cols), max(cols)) if cols else (0, 7)

        ascii_lines: list[str] = []
        density_chars = ' .:-=+*#%@'
        for r in range(min_r, min(max_r + 1, min_r + 16)):
            line = ''
            for c in range(min_c, min(max_c + 1, min_c + 16)):
                val = convolved_2d.get((r, c), 0.0)
                char_idx = int(max(0.0, min(1.0, val)) * (len(density_chars) - 1))
                line += density_chars[char_idx] + ' '
            ascii_lines.append(line)

        dpg.set_value('img_conv_ascii_preview', '\n'.join(ascii_lines))

        display_matrix: dict[int, dict[int, float]] = {}
        for (r, c), val in convolved_2d.items():
            if r not in display_matrix:
                display_matrix[r] = {}
            display_matrix[r][c] = val
        display_matrix_in_table(display_matrix, 'table_img_conv_res')

        dpg.set_value('img_conv_status', 'Successfully evaluated 2D spatial convolution!')
    except Exception as e:
        dpg.set_value('img_conv_status', f'Error: {e}')


# --- Network Curvature Physics Simulator Callbacks ---


def _all_node_pairs(nodes: list[int | str]) -> Iterator[tuple[int | str, int | str]]:
    for i, u in enumerate(nodes):
        for v in nodes[i + 1 :]:
            yield (u, v)


def _apply_pairwise_forces(
    pairs: Iterable[tuple[int | str, int | str]],
    force_func: Callable[[float], float],
    forces: dict[int | str, list[float]],
    epsilon: float = 1e-4,
) -> None:
    for u, v in pairs:
        dx = pos[u][0] - pos[v][0]
        dy = pos[u][1] - pos[v][1]
        dist = math.sqrt(dx * dx + dy * dy) + epsilon
        f_mag = force_func(dist)
        fx = (dx / dist) * f_mag
        fy = (dy / dist) * f_mag
        forces[u][0] += fx
        forces[u][1] += fy
        forces[v][0] -= fx
        forces[v][1] -= fy


def _coulomb_force(dist: float, k_repulsion: float = 6000.0) -> float:
    return k_repulsion / (dist * dist + 1.0)


def _hooke_force(dist: float, k_spring: float = 0.08, l_rest: float = 120.0) -> float:
    return -k_spring * (dist - l_rest)


def _compute_physics_forces() -> None:
    damping = 0.85
    forces: dict[int | str, list[float]] = {u: [0.0, 0.0] for u in current_nodes}

    # Coulomb Repulsion across all node pairs
    _apply_pairwise_forces(_all_node_pairs(current_nodes), _coulomb_force, forces)

    # Hooke Spring Attraction along graph edges
    _apply_pairwise_forces(current_edges, _hooke_force, forces)

    # Center Gravity Pull
    center_x, center_y = 350.0, 225.0
    for u in current_nodes:
        forces[u][0] += (center_x - pos[u][0]) * 0.005
        forces[u][1] += (center_y - pos[u][1]) * 0.005

    # Update Positions
    for u in current_nodes:
        if u == dragged_node:
            vel[u] = [0.0, 0.0]
            continue
        vel[u][0] = (vel[u][0] + forces[u][0] * 0.1) * damping
        vel[u][1] = (vel[u][1] + forces[u][1] * 0.1) * damping
        pos[u][0] = max(30.0, min(670.0, pos[u][0] + vel[u][0]))
        pos[u][1] = max(30.0, min(420.0, pos[u][1] + vel[u][1]))


def _handle_mouse_dragging() -> None:
    global dragged_node
    if not pos:
        return

    mouse_pos: list[float] = dpg.get_drawing_mouse_pos()
    is_left_down: bool = dpg.is_mouse_button_down(dpg.mvMouseButton_Left)

    if is_left_down:
        if dragged_node is None:
            for u in current_nodes:
                p = pos[u]
                dx = mouse_pos[0] - p[0]
                dy = mouse_pos[1] - p[1]
                if math.sqrt(dx * dx + dy * dy) <= 18.0:
                    dragged_node = u
                    break
        else:
            pos[dragged_node][0] = max(30.0, min(670.0, mouse_pos[0]))
            pos[dragged_node][1] = max(30.0, min(420.0, mouse_pos[1]))
    else:
        dragged_node = None


def recalculate_and_reset_layout() -> None:
    global current_nodes, current_edges, current_curvatures, pos, vel
    preset: str = dpg.get_value('vis_preset')
    is_augmented: bool = dpg.get_value('vis_augmented')

    graph: dict[int | str, dict[int | str, float]] = {}
    if preset == 'Barbell Graph':
        graph = {
            1: {2: 1, 3: 1},
            2: {1: 1, 3: 1},
            3: {1: 1, 2: 1, 4: 1},
            4: {3: 1, 5: 1, 6: 1},
            5: {4: 1, 6: 1},
            6: {4: 1, 5: 1},
        }
    elif preset == 'Star Graph':
        graph = {1: {2: 1, 3: 1, 4: 1, 5: 1, 6: 1}, 2: {1: 1}, 3: {1: 1}, 4: {1: 1}, 5: {1: 1}, 6: {1: 1}}
    elif preset == 'Cycle Graph':
        graph = {1: {2: 1, 6: 1}, 2: {1: 1, 3: 1}, 3: {2: 1, 4: 1}, 4: {3: 1, 5: 1}, 5: {4: 1, 6: 1}, 6: {5: 1, 1: 1}}
    elif preset == 'Tree Graph':
        graph = {1: {2: 1, 3: 1}, 2: {1: 1, 4: 1, 5: 1}, 3: {1: 1, 6: 1}, 4: {2: 1}, 5: {2: 1}, 6: {3: 1}}
    elif preset == 'Grid Graph':
        graph = {
            1: {2: 1, 4: 1},
            2: {1: 1, 3: 1, 5: 1},
            3: {2: 1, 6: 1},
            4: {1: 1, 5: 1},
            5: {2: 1, 4: 1, 6: 1},
            6: {3: 1, 5: 1},
        }

    current_nodes = sorted(graph.keys())
    edges_set: set[tuple[int | str, int | str]] = set()
    for u, neighbors in graph.items():
        for v in neighbors:
            if u < v:
                edges_set.add((u, v))
            elif v < u:
                edges_set.add((v, u))
    current_edges = sorted(edges_set)

    current_curvatures = forman_ricci_curvature(graph, augmented=is_augmented)

    # Reset positions
    random.seed(42)
    pos = {}
    vel = {}
    for i, u in enumerate(current_nodes):
        angle = (2 * math.pi * i) / len(current_nodes)
        radius = 140.0
        pos[u] = [350.0 + radius * math.cos(angle), 225.0 + radius * math.sin(angle)]
        vel[u] = [0.0, 0.0]

    # Update Chart Plot
    if dpg.does_item_exist('curvature_plot_series'):
        dpg.delete_item('curvature_plot_series')

    x_data = list(range(1, len(current_edges) + 1))
    y_data = [current_curvatures.get(edge, 0.0) for edge in current_edges]

    dpg.add_line_series(
        x_data,
        y_data,
        label='Forman-Ricci Curvature K',
        parent='curvature_y_axis',
        tag='curvature_plot_series',
    )
    dpg.set_value('vis_status', f'Loaded {preset} ({len(current_nodes)} nodes, {len(current_edges)} edges).')


def jostle_graph_callback() -> None:
    for u in current_nodes:
        vel[u] = [random.uniform(-15.0, 15.0), random.uniform(-15.0, 15.0)]


def _redraw_canvas() -> None:
    if not dpg.does_item_exist('vis_canvas'):
        return
    dpg.delete_item('vis_canvas', children_only=True)

    # Draw solid opaque canvas viewport background
    dpg.draw_rectangle((0, 0), (700, 450), fill=(18, 18, 24), color=(60, 60, 80), thickness=1, parent='vis_canvas')

    # Draw Edges
    for u, v in current_edges:
        p1 = pos[u]
        p2 = pos[v]
        k_val = current_curvatures.get((u, v), current_curvatures.get((v, u), 0.0))

        if k_val < -1e-5:
            color = (255, 80, 80, 220)
            thickness = max(1.5, min(8.0, 1.5 - 3.0 * k_val))
        elif k_val > 1e-5:
            color = (80, 180, 255, 220)
            thickness = max(1.5, min(8.0, 1.5 + 3.0 * k_val))
        else:
            color = (200, 200, 200, 128)
            thickness = 1.5

        dpg.draw_line(p1, p2, color=color, thickness=thickness, parent='vis_canvas')
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        dpg.draw_text((mid_x - 12, mid_y - 8), f'{k_val:.2f}', color=(220, 220, 220), size=12, parent='vis_canvas')

    # Draw Nodes
    for u in current_nodes:
        p = pos[u]
        dpg.draw_circle(p, radius=14, color=(140, 140, 180), fill=(48, 48, 72), thickness=2, parent='vis_canvas')
        dpg.draw_text((p[0] - 6, p[1] - 9), str(u), color=(255, 255, 255), size=14, parent='vis_canvas')


def update_graph_simulation() -> None:
    run_physics: bool = dpg.get_value('vis_run_physics')
    if run_physics and pos:
        _compute_physics_forces()
    _handle_mouse_dragging()
    _redraw_canvas()


# --- View Builder Functions ---


def build_view_semiring() -> None:
    with dpg.group(tag='view_semiring_matrix_power_group', show=True):
        dpg.add_text(
            'Evaluate matrix multiplication and powers over various algebraic semirings.', color=(180, 180, 180)
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Select Semiring:')
            dpg.add_combo(
                [
                    'Standard',
                    'Tropical',
                    'Arctic',
                    'Viterbi',
                    'String',
                    'Expectation',
                    'Provenance',
                    'Variance',
                    'Digital',
                    'Interval (Convex Hull)',
                ],
                default_value='Standard',
                callback=semiring_change_callback,
                tag='semiring_select',
                width=200,
            )
            dpg.add_text('Matrix Power:')
            dpg.add_input_int(default_value=2, min_value=1, tag='semiring_power', width=100)

        dpg.add_text('Adjacency Graph (JSON format):')
        default_graph = '{\n  "0": {"1": 0.5, "2": 0.1},\n  "1": {"2": 0.5},\n  "2": {"0": 0.9}\n}'
        dpg.add_input_text(
            default_value=default_graph, multiline=True, tag='semiring_graph_input', height=150, width=800
        )
        dpg.add_button(label='Compute Matrix Power', callback=run_semiring_power)
        dpg.add_text('', tag='semiring_status', color=(255, 200, 100))
        dpg.add_text('Result Matrix (Selectable text):')
        with dpg.group(tag='table_semiring_res_container'):
            pass


def build_view_curvature() -> None:
    with dpg.group(tag='view_forman_ricci_curvature_group', show=False):
        dpg.add_text('Compute discrete Forman-Ricci curvature on weighted/unweighted networks.', color=(180, 180, 180))
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label='Weighted Graph', default_value=False, tag='curvature_weighted')
            dpg.add_checkbox(label='Augmented Curvature (Triangles)', default_value=True, tag='curvature_augmented')

        dpg.add_text('Adjacency Graph (JSON format):')
        default_curv_graph = (
            '{\n  "0": {"1": 1, "2": 1},\n  "1": {"0": 1, "2": 1},\n  "2": {"0": 1, "1": 1, "3": 1},\n'
            '  "3": {"2": 1, "4": 1, "5": 1},\n  "4": {"3": 1},\n  "5": {"3": 1}\n}'
        )
        dpg.add_input_text(
            default_value=default_curv_graph, multiline=True, tag='curvature_graph_input', height=150, width=800
        )
        dpg.add_button(label='Analyze Graph Curvature', callback=run_curvature)
        dpg.add_text('', tag='curvature_status', color=(255, 200, 100))
        dpg.add_text('Calculated Edge Curvatures (Selectable cells):')
        create_bordered_table(
            tag='table_curvature',
            columns=['Edge (u, v)', 'Forman-Ricci Curvature', 'Geometry Type'],
        )


def build_view_crypto() -> None:
    with dpg.group(tag='view_pq_key_exchange_group', show=False):
        dpg.add_text('Simulation of Diffie-Hellman key exchange over the Digital Semiring.', color=(180, 180, 180))
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Alice Private Key (a1, a2):')
            dpg.add_input_int(default_value=12, tag='crypto_a1', width=100)
            dpg.add_input_int(default_value=34, tag='crypto_a2', width=100)
        with dpg.group(horizontal=True):
            dpg.add_text('Bob Private Key (b1, b2):')
            dpg.add_input_int(default_value=56, tag='crypto_b1', width=100)
            dpg.add_input_int(default_value=78, tag='crypto_b2', width=100)

        dpg.add_button(label='Execute Key Exchange', callback=run_crypto_exchange)
        dpg.add_text('', tag='crypto_status', color=(255, 200, 100))
        dpg.add_input_text(default_value='Keys Match: Not Run', readonly=True, tag='crypto_match_text', width=400)

        with dpg.group(horizontal=True):
            with dpg.child_window(width=205, height=180, border=True):
                dpg.add_text('Alice Public U:')
                with dpg.group(tag='table_crypto_u_container'):
                    pass
            with dpg.child_window(width=205, height=180, border=True):
                dpg.add_text('Bob Public V:')
                with dpg.group(tag='table_crypto_v_container'):
                    pass
            with dpg.child_window(width=205, height=180, border=True):
                dpg.add_text('Alice Shared Key K_A:')
                with dpg.group(tag='table_crypto_ka_container'):
                    pass
            with dpg.child_window(width=205, height=180, border=True):
                dpg.add_text('Bob Shared Key K_B:')
                with dpg.group(tag='table_crypto_kb_container'):
                    pass


def build_view_trie() -> None:
    with dpg.group(tag='view_algebraic_trie_group', show=False):
        dpg.add_text(
            'Algebraic Tries represent nested sparse tensors capable of contracting/marginalizing dimensions.',
            color=(180, 180, 180),
        )
        dpg.add_separator()
        dpg.add_text('Tensor Points [[coordinate_tuple, value], ...]:')
        default_points = '[\n  [[0, 0, 0], 1.0],\n  [[0, 0, 0], 2.0],\n  [[0, 1, 0], 5.0],\n  [[1, 0, 0], 10.0]\n]'
        dpg.add_input_text(default_value=default_points, multiline=True, tag='trie_points_input', height=120, width=800)
        dpg.add_text('Contract Dimensions (JSON list of indices, e.g. [0] or [0, 0]):')
        dpg.add_input_text(default_value='[0]', tag='trie_contract_dims', width=300)
        dpg.add_button(label='Contract Sparse Tensor', callback=run_trie_operations)
        dpg.add_text('', tag='trie_status', color=(255, 200, 100))
        dpg.add_text('Trie Contents (Selectable text):')
        dpg.add_input_text(
            default_value='  (No data populated yet)',
            multiline=True,
            readonly=True,
            tag='trie_contents_text',
            height=100,
            width=800,
        )
        dpg.add_text('Contracted Result:')
        dpg.add_input_text(
            default_value='Contracted Result at [0]: None',
            readonly=True,
            tag='trie_result_text',
            width=800,
        )


def build_view_pagerank() -> None:
    with dpg.group(tag='view_pagerank_group', show=False):
        dpg.add_text('Compute PageRank (algebraic stationary distribution of a random walk).', color=(180, 180, 180))
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Damping (alpha):')
            dpg.add_input_float(default_value=0.85, tag='pagerank_alpha', width=120)
            dpg.add_text('Iterations:')
            dpg.add_input_int(default_value=20, tag='pagerank_iterations', width=100)

        dpg.add_text('Web Graph Adjacency List (JSON format):')
        default_web = '{\n  "A": {"B": 1, "C": 1},\n  "B": {"C": 1},\n  "C": {"A": 1}\n}'
        dpg.add_input_text(default_value=default_web, multiline=True, tag='pagerank_graph', height=120, width=800)
        dpg.add_button(label='Compute PageRank', callback=run_pagerank)
        dpg.add_text('', tag='pagerank_status', color=(255, 200, 100))
        dpg.add_text('Resulting Ranks (Selectable cells):')
        create_bordered_table(
            tag='table_pagerank',
            columns=['Node', 'Rank'],
            width=300,
        )


def build_view_cyk() -> None:
    with dpg.group(tag='view_cyk_parser_group', show=False):
        dpg.add_text(
            'Grammar syntax parsing representing CYK chart combination as a matrix multiplication closure.',
            color=(180, 180, 180),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Sentence to Parse:')
            dpg.add_input_text(default_value='I love Python', tag='cyk_sentence', width=400)

        dpg.add_text('Lexicon Grammar Mapping (JSON format):')
        default_cyk_lexicon = '{\n  "I": ["NP"],\n  "love": ["V"],\n  "Python": ["NP"]\n}'
        dpg.add_input_text(default_value=default_cyk_lexicon, multiline=True, tag='cyk_lexicon', height=100, width=800)
        dpg.add_text('Chomsky Normal Form Grammar Rules (comma-separated inputs, JSON format):')
        default_cyk_rules = '{\n  "NP,VP": ["S"],\n  "V,NP": ["VP"]\n}'
        dpg.add_input_text(default_value=default_cyk_rules, multiline=True, tag='cyk_rules', height=100, width=800)
        dpg.add_button(label='Parse Sentence', callback=run_cyk_parsing)
        dpg.add_text('', tag='cyk_status', color=(255, 200, 100))
        dpg.add_input_text(default_value='Parses as: None', readonly=True, tag='cyk_result_text', width=800)
        dpg.add_text('Parsing Chart Spans (Selectable cells):')
        with dpg.group(tag='table_cyk_chart_container'):
            pass


def build_view_slope() -> None:
    with dpg.group(tag='view_slope_transform_group', show=False):
        dpg.add_text(
            'Evaluate the Fenchel-Legendre Transform (Tropical/Idempotent Fourier analog) of a signal.',
            color=(180, 180, 180),
        )
        dpg.add_separator()
        dpg.add_text('Signal Vector f(x) (JSON format):')
        default_signal = '{\n  "0": 0.0,\n  "1": 1.0,\n  "2": 4.0,\n  "3": 9.0\n}'
        dpg.add_input_text(default_value=default_signal, multiline=True, tag='fenchel_signal', height=100, width=800)
        dpg.add_text('Slopes to Evaluate (s) (JSON list):')
        default_slopes = '[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]'
        dpg.add_input_text(default_value=default_slopes, tag='fenchel_slopes', width=400)
        dpg.add_button(label='Compute Convex Conjugates', callback=run_legendre_fenchel)
        dpg.add_text('', tag='fenchel_status', color=(255, 200, 100))
        dpg.add_text('Convex Conjugate Values f*(s) = sup_x (s*x - f(x)) (Selectable cells):')
        create_bordered_table(
            tag='table_fenchel',
            columns=['Slope (s)', 'Convex Conjugate f*(s)'],
            width=350,
        )


def build_view_automata() -> None:
    with dpg.group(tag='view_automata_simulator_group', show=False):
        dpg.add_text(
            'Simulate Deterministic and Nondeterministic/Probabilistic Finite Automata.', color=(180, 180, 180)
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Automaton Type:')
            dpg.add_combo(
                ['DFA', 'NFA / Probabilistic'],
                default_value='DFA',
                callback=automata_type_callback,
                tag='automata_type',
                width=200,
            )
            dpg.add_text('Start State(s):')
            dpg.add_input_text(default_value='"q0"', tag='automata_start', width=150)
        with dpg.group(horizontal=True):
            dpg.add_text('Accept States (JSON list):')
            dpg.add_input_text(default_value='["q1"]', tag='automata_accept', width=250)
            dpg.add_text('Input Symbols (string or comma-separated):')
            dpg.add_input_text(default_value='1010', tag='automata_input', width=250)

        dpg.add_text('Transition Table (JSON format):')
        default_dfa_trans = (
            '{\n  "q0": {"0": "q0", "1": "q1"},\n  "q1": {"0": "q2", "1": "q0"},\n  "q2": {"0": "q1", "1": "q2"}\n}'
        )
        dpg.add_input_text(
            default_value=default_dfa_trans, multiline=True, tag='automata_transitions', height=150, width=800
        )
        dpg.add_button(label='Simulate Automaton', callback=run_automata_sim)
        dpg.add_text('', tag='automata_status', color=(255, 200, 100))
        dpg.add_input_text(default_value='Result: Not Run', readonly=True, tag='automata_result_text', width=800)
        dpg.add_text('Simulation Trajectory Log (Selectable text):')
        dpg.add_input_text(multiline=True, tag='automata_log_text', readonly=True, height=150, width=800)


def build_view_markov_info() -> None:
    with dpg.group(tag='view_markov_info_theory_group', show=False):
        dpg.add_text(
            'Simulate Markov chain steps, find stationary states, and compute information theory metrics.',
            color=(180, 180, 180),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=415, height=530, border=True):
                dpg.add_text('MARKOV CHAIN SIMULATOR', color=(150, 180, 255))
                dpg.add_separator()
                dpg.add_text('Transition Matrix (Row Stochastic JSON):')
                default_markov_matrix = '{\n  "A": {"A": 0.1, "B": 0.9},\n  "B": {"A": 0.5, "B": 0.5}\n}'
                dpg.add_input_text(
                    default_value=default_markov_matrix, multiline=True, tag='markov_matrix', height=100, width=380
                )
                dpg.add_text('Initial Distribution State:')
                dpg.add_input_text(default_value='{"A": 1.0, "B": 0.0}', tag='markov_state', width=380)
                with dpg.group(horizontal=True):
                    dpg.add_text('Steps (N):')
                    dpg.add_input_int(default_value=5, min_value=1, tag='markov_steps', width=120)

                dpg.add_button(label='Compute Markov Simulation', callback=run_markov_simulation)
                dpg.add_text('', tag='markov_status', color=(255, 200, 100))
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text('Distribution after N steps:')
                        create_bordered_table(tag='table_markov_steps', columns=['State', 'Prob'], width=180)
                    with dpg.group():
                        dpg.add_text('Analytical Steady State:')
                        create_bordered_table(tag='table_markov_steady', columns=['State', 'Steady Prob'], width=180)

            with dpg.child_window(width=415, height=530, border=True):
                dpg.add_text('INFORMATION THEORY LAB', color=(150, 180, 255))
                dpg.add_separator()
                dpg.add_text('Distribution P (True):')
                dpg.add_input_text(default_value='{"A": 0.5, "B": 0.25, "C": 0.25}', tag='info_p', width=380)
                dpg.add_text('Distribution Q (Reference/Model):')
                dpg.add_input_text(default_value='{"A": 0.4, "B": 0.3, "C": 0.3}', tag='info_q', width=380)
                dpg.add_text('Joint Distribution P(X, Y) (JSON matrix):')
                default_joint = '{\n  "X1": {"Y1": 0.25, "Y2": 0.25},\n  "X2": {"Y1": 0.25, "Y2": 0.25}\n}'
                dpg.add_input_text(default_value=default_joint, multiline=True, tag='info_joint', height=80, width=380)
                dpg.add_button(label='Compute Information Metrics', callback=run_info_theory)
                dpg.add_text('', tag='info_status', color=(255, 200, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Entropy H(P):')
                    dpg.add_text('0.0', tag='info_hp_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Entropy H(Q):')
                    dpg.add_text('0.0', tag='info_hq_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Cross Entropy H(P, Q):')
                    dpg.add_text('0.0', tag='info_hcross_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('KL Divergence D_KL(P||Q):')
                    dpg.add_text('0.0', tag='info_kl_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Mutual Info I(X; Y):')
                    dpg.add_text('0.0', tag='info_mi_val', color=(100, 255, 100))


def build_view_signal_transforms() -> None:
    with dpg.group(tag='view_signal_transforms_group', show=False):
        dpg.add_text(
            'Apply Discrete Fourier, Hilbert, Convolution, or Z-Transforms to sparse signal vectors.',
            color=(180, 180, 180),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Select Operation:')
            dpg.add_combo(
                ['DFT', 'IDFT', 'Hilbert Transform', 'Convolution', 'Z-Transform'],
                default_value='DFT',
                callback=signal_op_change_callback,
                tag='signal_op_select',
                width=200,
            )

        dpg.add_text('Signal Vector f(t) (JSON format with integer keys):')
        default_f = '{\n  "0": 1.0,\n  "1": 0.0,\n  "2": -1.0,\n  "3": 0.0\n}'
        dpg.add_input_text(default_value=default_f, multiline=True, tag='signal_f', height=100, width=800)

        with dpg.group(tag='signal_g_group', show=False):
            dpg.add_text('Kernel Vector g(t) (JSON format with integer keys, for Convolution):')
            default_g = '{\n  "0": 0.5,\n  "1": 0.5\n}'
            dpg.add_input_text(default_value=default_g, multiline=True, tag='signal_g', height=80, width=800)

        with dpg.group(tag='signal_z_group', show=False):
            dpg.add_text('Complex z coordinate (for Z-Transform):')
            dpg.add_input_text(default_value='0.5+0.5j', tag='signal_z_input', width=200)

        dpg.add_button(label='Process Signal Transform', callback=run_signal_transforms)
        dpg.add_text('', tag='signal_status', color=(255, 200, 100))
        dpg.add_text('Resulting Signal Coefficients (Selectable cells):')
        create_bordered_table(
            tag='table_signal_res',
            columns=['Index (k/t)', 'Value / Coefficient'],
        )


def build_view_image_conv() -> None:
    with dpg.group(tag='view_image_convolution_2d_group', show=False):
        dpg.add_text(
            'Perform 2D Image & Grid Convolution via algebrax.transforms.convolve using 2D vector key addition.',
            color=(180, 180, 180),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Load Real Image File:')
            dpg.add_input_text(tag='img_conv_filepath_input', hint='Path to PNG, JPG, BMP image file...', width=380)
            dpg.add_button(label='Browse...', callback=open_file_dialog_callback)
            dpg.add_button(
                label='Load Image', callback=lambda: load_image_file_into_lab(dpg.get_value('img_conv_filepath_input'))
            )

        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Image Preset:')
            dpg.add_combo(
                list(IMAGE_PRESETS.keys()),
                default_value='Cross Pattern (8x8)',
                callback=image_preset_change_callback,
                tag='img_conv_image_preset',
                width=180,
            )
            dpg.add_spacer(width=10)
            dpg.add_text('Kernel Preset:')
            dpg.add_combo(
                list(KERNEL_PRESETS.keys()),
                default_value='Sobel Horizontal (Edge)',
                callback=kernel_preset_change_callback,
                tag='img_conv_kernel_preset',
                width=180,
            )
            dpg.add_spacer(width=10)
            dpg.add_text('Semiring:')
            dpg.add_combo(
                [
                    'Standard (+, *)',
                    'Arctic / Max-Plus (Dilation)',
                    'Tropical / Min-Plus (Erosion)',
                ],
                default_value='Standard (+, *)',
                tag='img_conv_semiring_select',
                width=200,
            )

        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text('Image Mapping JSON {"r,c": intensity}:')
                dpg.add_input_text(
                    default_value=IMAGE_PRESETS['Cross Pattern (8x8)'],
                    multiline=True,
                    tag='img_conv_image_input',
                    height=120,
                    width=380,
                )
            with dpg.group():
                dpg.add_text('Kernel Mapping JSON {"dr,dc": weight}:')
                dpg.add_input_text(
                    default_value=KERNEL_PRESETS['Sobel Horizontal (Edge)'],
                    multiline=True,
                    tag='img_conv_kernel_input',
                    height=120,
                    width=380,
                )

        dpg.add_button(label='Compute 2D Image Convolution', callback=run_image_convolution_2d)
        dpg.add_text('', tag='img_conv_status', color=(255, 200, 100))

        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text('Input Image Texture (64x64):')
                dpg.add_image('texture_img_input', width=160, height=160)
            with dpg.group():
                dpg.add_text('Output Convolved Texture (64x64):')
                dpg.add_image('texture_img_output', width=160, height=160)
            with dpg.group():
                dpg.add_text('ASCII Grid Preview (Selectable text):')
                dpg.add_input_text(
                    default_value='',
                    multiline=True,
                    tag='img_conv_ascii_preview',
                    height=160,
                    width=220,
                    readonly=True,
                )
            with dpg.group():
                dpg.add_text('Result Table (Selectable cells):')
                with dpg.group(tag='table_img_conv_res_container'):
                    pass


def build_view_network_vis() -> None:
    with dpg.group(tag='view_network_curvature_vis_group', show=False):
        dpg.add_text('Interactive Force-Directed Layout & Forman-Ricci Curvature Visualization', color=(150, 180, 255))
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('GRAPH SETTINGS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_text('Graph Preset:')
                dpg.add_combo(
                    ['Barbell Graph', 'Star Graph', 'Cycle Graph', 'Tree Graph', 'Grid Graph'],
                    default_value='Barbell Graph',
                    tag='vis_preset',
                    callback=recalculate_and_reset_layout,
                )
                dpg.add_checkbox(
                    label='Weighted Graph',
                    default_value=False,
                    tag='vis_weighted',
                    callback=recalculate_and_reset_layout,
                )
                dpg.add_checkbox(
                    label='Augmented Curvature (Triangles)',
                    default_value=True,
                    tag='vis_augmented',
                    callback=recalculate_and_reset_layout,
                )

                dpg.add_spacer(height=10)
                dpg.add_text('PHYSICS SIMULATION', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_checkbox(label='Run Physics Layout', default_value=True, tag='vis_run_physics')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Jostle Graph', callback=jostle_graph_callback)
                    dpg.add_button(label='Reset Positions', callback=recalculate_and_reset_layout)

                dpg.add_spacer(height=10)
                dpg.add_text('STATUS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_text('Initializing...', tag='vis_status', color=(255, 200, 100))

                dpg.add_spacer(height=10)
                dpg.add_text('CURVATURE CHART', color=(100, 255, 100))
                dpg.add_separator()
                with dpg.plot(label='Curvature Profile', height=180, width=270):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label='Edge Index', tag='curvature_x_axis')
                    dpg.add_plot_axis(dpg.mvYAxis, label='Curvature', tag='curvature_y_axis')

            with dpg.group():
                dpg.add_text('Force-Directed Canvas (Drag nodes to interact!):', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=450, tag='vis_canvas'):
                    pass
                with dpg.group(horizontal=True):
                    dpg.add_text('Legend: ')
                    dpg.add_text('Red (Hyperbolic / K < 0)', color=(255, 80, 80))
                    dpg.add_text(' | ')
                    dpg.add_text('Gray (Flat / K = 0)', color=(200, 200, 200))
                    dpg.add_text(' | ')
                    dpg.add_text('Blue (Spherical / K > 0)', color=(80, 180, 255))


def build_view_blackhole() -> None:
    with dpg.group(tag='view_blackhole_spacetime_group', show=False):
        dpg.add_text(
            'Schwarzschild Black Hole Spacetime Metric & Gravitational Lensing Simulation',
            color=(150, 180, 255),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Schwarzschild Radius (r_s km):')
            dpg.add_input_float(default_value=29.5, tag='bh_rs', width=120)
            dpg.add_text('Observation Radius (r km):')
            dpg.add_input_float(default_value=59.0, tag='bh_r', width=120)
            dpg.add_text('Impact Parameter (b km):')
            dpg.add_input_float(default_value=40.0, tag='bh_b', width=120)

        dpg.add_button(label='Compute Spacetime Geometry & Deflection', callback=run_blackhole_sim)
        dpg.add_text('', tag='bh_status', color=(255, 200, 100))
        dpg.add_text('Schwarzschild Spacetime Metric Components & Deflection Angle (Selectable cells):')
        create_bordered_table(
            tag='table_bh_res',
            columns=['Physical Property', 'Evaluated Value'],
            width=700,
        )


def build_view_sparse_tensor_einsum() -> None:
    with dpg.group(tag='view_sparse_tensor_einsum_group', show=False):
        dpg.add_text(
            'Arbitrary-Rank Sparse Tensor Einstein Summation Contractions over Algebraic Semirings',
            color=(150, 180, 255),
        )
        with dpg.group(horizontal=True):
            dpg.add_text("Einstein Subscript (e.g. 'ik,kj->ij' or 'i,j->ij'):")
            dpg.add_input_text(default_value='ik,kj->ij', tag='tensor_subscripts', width=250)
            dpg.add_text('Semiring:')
            dpg.add_combo(
                ['Standard (+, *)', 'Tropical / Min-Plus', 'Arctic / Max-Plus'],
                default_value='Standard (+, *)',
                tag='tensor_semiring',
                width=200,
            )

        dpg.add_text('Tensor A Coordinates & Values [[[i, k], val], ...]:')
        default_a = '[\n  [["U1", "M_A"], 4.5],\n  [["U1", "M_B"], 2.0],\n  [["U2", "M_A"], 5.0]\n]'
        dpg.add_input_text(default_value=default_a, multiline=True, tag='tensor_a_input', height=100, width=800)

        dpg.add_text('Tensor B Coordinates & Values [[[k, j], val], ...]:')
        default_b = '[\n  [["M_A", "Sci-Fi"], 0.9],\n  [["M_B", "Comedy"], 0.8]\n]'
        dpg.add_input_text(default_value=default_b, multiline=True, tag='tensor_b_input', height=100, width=800)

        dpg.add_button(label='Execute Tensor Einsum Contraction', callback=run_sparse_tensor_einsum)
        dpg.add_text('', tag='tensor_einsum_status', color=(255, 200, 100))
        dpg.add_text('Result Contracted Tensor Entries (Selectable cells):')
        create_bordered_table(
            tag='table_tensor_einsum_res',
            columns=['Result Index Key', 'Value'],
            width=400,
        )


def build_view_trajectoid() -> None:
    with dpg.group(tag='view_trajectoid_kinematics_group', show=False):
        dpg.add_text(
            'Trajectoid Non-Holonomic Rolling Kinematics & SO(3) Rotation Matrix Composition',
            color=(150, 180, 255),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Trajectory Steps:')
            dpg.add_input_int(default_value=32, min_value=8, tag='trajectoid_steps', width=120)
            dpg.add_text('Path Frequency (k):')
            dpg.add_input_float(default_value=2.0, tag='trajectoid_freq', width=120)

        dpg.add_button(label='Integrate SO(3) Trajectoid Rotation', callback=run_trajectoid_sim)
        dpg.add_text('', tag='trajectoid_status', color=(255, 200, 100))
        dpg.add_text('Integrated SO(3) 3x3 Orientation Matrix R_t (Selectable cells):')
        with dpg.group(tag='table_trajectoid_so3_container'):
            pass


def build_view_knot_theory() -> None:
    with dpg.group(tag='view_algebraic_knot_theory_group', show=False):
        dpg.add_text(
            'Algebraic Knot Theory, Skein Modules (#) and Artin Braid Group Crossing Signatures',
            color=(150, 180, 255),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Knot Topology A:')
            dpg.add_combo(['3_1', '4_1', 'U'], default_value='3_1', tag='knot_a_select', width=150)
            dpg.add_text('Knot Topology B:')
            dpg.add_combo(['4_1', '2_1^2', 'U'], default_value='4_1', tag='knot_b_select', width=150)

        dpg.add_text('Artin Braid Strand Crossings (JSON list of adjacent strand index swaps):')
        dpg.add_input_text(default_value='[1, 2, 1]', tag='knot_crossings', width=300)

        dpg.add_button(label='Analyze Knot Connected Sum & Braid Signature', callback=run_knot_theory)
        dpg.add_text('', tag='knot_status', color=(255, 200, 100))
        dpg.add_text('Topological Invariants & Braid Permutation (Selectable cells):')
        create_bordered_table(
            tag='table_knot_res',
            columns=['Topological Invariant / Property', 'Value / Result'],
            width=650,
        )


def build_view_optical_holography() -> None:
    with dpg.group(tag='view_optical_holography_group', show=False):
        dpg.add_text(
            'Optical Holography Interference Pattern Recording & Discrete Wavefront Reconstruction',
            color=(150, 180, 255),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Reference Beam Phase Shift (phi rad):')
            dpg.add_input_float(default_value=0.5, tag='hologram_ref_phase', width=150)

        dpg.add_text('Object Wavefront Apertures (JSON dict {index: amplitude}):')
        default_obj = '{\n  "0": 0.0, "1": 0.0, "2": 1.0, "3": 0.0,\n  "4": 0.0, "5": 0.8, "6": 0.0, "7": 0.0\n}'
        dpg.add_input_text(
            default_value=default_obj, multiline=True, tag='hologram_object_input', height=100, width=800
        )

        dpg.add_button(label='Record Hologram & Reconstruct Wavefront', callback=run_optical_holography)
        dpg.add_text('', tag='hologram_status', color=(255, 200, 100))
        dpg.add_text('Interference Intensity I(x) & Discrete Fourier Spectrum (Selectable cells):')
        create_bordered_table(
            tag='table_hologram_res',
            columns=['Spatial Grid Index (x)', 'Hologram Intensity I(x)', 'Fourier Spectrum F(u)'],
            width=600,
        )


def build_view_financial_risk() -> None:
    with dpg.group(tag='view_financial_risk_group', show=False):
        dpg.add_text(
            'Financial Risk Engineering, Spectral Asset Centrality & Algorithmic Trade DFAs',
            color=(150, 180, 255),
        )
        dpg.add_text('Market Trade Signal Stream (comma-separated):')
        dpg.add_input_text(
            default_value='buy_signal, hold, risk_alert, hold, clear_alert, buy_signal', tag='fin_signals', width=600
        )

        dpg.add_text('Cross-Asset Correlation Matrix (JSON format):')
        default_corr = (
            '{\n'
            '  "BTC": {"BTC": 1.0, "ETH": 0.8, "SPX": 0.4},\n'
            '  "ETH": {"BTC": 0.8, "ETH": 1.0, "SPX": 0.3},\n'
            '  "SPX": {"BTC": 0.4, "ETH": 0.3, "SPX": 1.0}\n'
            '}'
        )
        dpg.add_input_text(default_value=default_corr, multiline=True, tag='fin_corr_matrix', height=120, width=800)

        dpg.add_button(label='Evaluate Portfolio Risk & Execute Trade Strategy', callback=run_financial_risk)
        dpg.add_text('', tag='fin_status', color=(255, 200, 100))
        dpg.add_input_text(default_value='Trade Strategy State: Cash', readonly=True, tag='fin_result_text', width=600)
        dpg.add_text('Asset Spectral Eigen Centralities (Selectable cells):')
        create_bordered_table(
            tag='table_fin_centrality',
            columns=['Asset', 'Spectral Eigen Centrality'],
            width=400,
        )


def build_view_sheaf_cohomology() -> None:
    with dpg.group(tag='view_sheaf_cohomology_group', show=False):
        dpg.add_text(
            'Cellular Sheaf Cohomology, Coboundary Gradient & Multi-Agent Network Consensus',
            color=(150, 180, 255),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Consensus Steps (N):')
            dpg.add_input_int(default_value=5, min_value=1, tag='sheaf_steps', width=120)

        dpg.add_text('Initial Robot Local Sensor Estimates (JSON dict):')
        default_sensors = '{\n  "0": 10.0, "1": 30.0, "2": 20.0, "3": 40.0\n}'
        dpg.add_input_text(
            default_value=default_sensors, multiline=True, tag='sheaf_states_input', height=100, width=600
        )

        dpg.add_button(label='Harmonize Sheaf Network Consensus', callback=run_sheaf_cohomology)
        dpg.add_text('', tag='sheaf_status', color=(255, 200, 100))
        dpg.add_text('Multi-Agent Sensor States Convergence (Selectable cells):')
        create_bordered_table(
            tag='table_sheaf_res',
            columns=['Agent ID', 'Initial Sensor State', 'Harmonized State (t=N)'],
            width=500,
        )


def build_view_gaussian_splatting() -> None:
    with dpg.group(tag='view_gaussian_splatting_group', show=False):
        dpg.add_text(
            '3D Gaussian Splatting, Projective Screen Covariance & Volumetric Rasterization',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('3D GAUSSIAN SCALE (S)', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_input_float(
                    default_value=0.8,
                    tag='gs_scale_x',
                    label='Scale X',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )
                dpg.add_input_float(
                    default_value=0.3,
                    tag='gs_scale_y',
                    label='Scale Y',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )
                dpg.add_input_float(
                    default_value=0.3,
                    tag='gs_scale_z',
                    label='Scale Z',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )

                dpg.add_spacer(height=10)
                dpg.add_text('SO(3) ROTATION (R)', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_input_float(
                    default_value=12.0,
                    tag='gs_rot_pitch',
                    label='Pitch (deg)',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )
                dpg.add_input_float(
                    default_value=30.0,
                    tag='gs_rot_yaw',
                    label='Yaw (deg)',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )
                dpg.add_input_float(
                    default_value=0.0,
                    tag='gs_rot_roll',
                    label='Roll (deg)',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )

                dpg.add_spacer(height=10)
                dpg.add_text('3D POSITION & CAMERA', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_input_float(
                    default_value=0.0,
                    tag='gs_pos_x',
                    label='Pos X',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )
                dpg.add_input_float(
                    default_value=0.0,
                    tag='gs_pos_y',
                    label='Pos Y',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )
                dpg.add_input_float(
                    default_value=4.0,
                    tag='gs_pos_z',
                    label='Pos Z (Depth)',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )
                dpg.add_input_float(
                    default_value=2.5,
                    tag='gs_focal',
                    label='Focal Length f',
                    width=120,
                    callback=lambda: run_gaussian_splatting(),
                )

                dpg.add_spacer(height=10)
                dpg.add_button(label='Render Gaussian Splat', callback=run_gaussian_splatting)
                dpg.add_text('', tag='gs_status', color=(255, 200, 100))

            with dpg.group():
                dpg.add_text('2D Screen Projective Splat Viewport:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=320, tag='gs_canvas'):
                    pass
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text('3D Spatial Covariance Sigma:')
                        with dpg.group(tag='table_gs_3d_cov_container'):
                            pass
                    with dpg.group():
                        dpg.add_text("2D Screen Covariance Sigma':")
                        with dpg.group(tag='table_gs_2d_cov_container'):
                            pass


def build_view_topological_homology() -> None:
    with dpg.group(tag='view_topological_homology_group', show=False):
        dpg.add_text(
            'Simplicial Homology, Boundary Nilpotency (D_{k-1} o D_k = 0) & Betti Barcodes',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Max Topological Dimension (k):')
            dpg.add_input_int(default_value=2, min_value=1, max_value=3, tag='homology_max_k', width=120)

        dpg.add_button(label='Evaluate Simplicial Homology Betti Numbers', callback=run_topological_homology)
        dpg.add_text('', tag='homology_status', color=(255, 200, 100))
        dpg.add_text('Betti Numbers Barcode Invariants (Selectable cells):')
        create_bordered_table(
            tag='table_homology_res',
            columns=['Dimension (beta_k)', 'Hole Count (Rank)'],
            width=400,
        )


def build_view_clifford_geometric_algebra() -> None:
    with dpg.group(tag='view_clifford_geometric_algebra_group', show=False):
        dpg.add_text(
            'Clifford Geometric Algebra Cl(3,0), Multivector Products & 3D Rotor Rotations',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_input_float(default_value=3.0, tag='clifford_v_e1', label='e1 Component', width=120)
            dpg.add_input_float(default_value=4.0, tag='clifford_v_e2', label='e2 Component', width=120)
            dpg.add_input_float(default_value=90.0, tag='clifford_angle', label='Rotation Deg (e12)', width=120)

        dpg.add_spacer(height=5)
        dpg.add_button(label='Rotate Vector via Rotor R = exp(-theta/2 * B)', callback=run_clifford_geometric_algebra)
        dpg.add_text('', tag='clifford_status', color=(255, 200, 100))
        dpg.add_text('v^2 Magnitude Squared:', color=(180, 180, 180))
        dpg.add_text('Vector Squared v^2 = 25.000', tag='clifford_v_sq_text', color=(100, 255, 100))
        dpg.add_spacer(height=5)
        dpg.add_text('3D Rotor Transformation Comparison (Selectable cells):')
        create_bordered_table(
            tag='table_clifford_res',
            columns=['Blade Component', 'Original Vector v', "Rotor Transformed v'"],
            width=500,
        )


def build_view_galois_finite_fields() -> None:
    with dpg.group(tag='view_galois_finite_fields_group', show=False):
        dpg.add_text(
            'Galois Finite Field GF(2^8) & AES Cryptographic MixColumns Matrix Arithmetic',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_input_int(default_value=4, tag='galois_exp1', label='x^a Exponent', width=120)
            dpg.add_input_int(default_value=4, tag='galois_exp2', label='x^b Exponent', width=120)

        dpg.add_button(label='Multiply Field Elements & MixColumns', callback=run_galois_finite_fields)
        dpg.add_text('', tag='galois_status', color=(255, 200, 100))
        dpg.add_text('Polynomial Multiplication Modulo P(x) = x^8 + x^4 + x^3 + x + 1:', color=(180, 180, 180))
        dpg.add_text('x^4 * x^4 mod P(x) = {0: 1, 1: 1, 3: 1, 4: 1}', tag='galois_poly_res_text', color=(100, 255, 100))
        dpg.add_spacer(height=5)
        dpg.add_text('AES MixColumns Output State (Selectable cells):')
        create_bordered_table(
            tag='table_galois_res',
            columns=['Column Index', 'Transformed GF(2^8) Output Polynomial'],
            width=600,
        )


def build_view_categorical_kleisli() -> None:
    with dpg.group(tag='view_categorical_kleisli_group', show=False):
        dpg.add_text(
            'Categorical Morphisms, Kleisli Monadic Composition (g o_T f) & Kan Extensions',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_input_float(default_value=0.8, tag='kleisli_f_val', label='f(A->B) Weight', width=120)
            dpg.add_input_float(default_value=0.9, tag='kleisli_g_val', label='g(B->C) Weight', width=120)

        dpg.add_button(label='Compose Morphisms Across Monad Semirings', callback=run_categorical_kleisli)
        dpg.add_text('', tag='kleisli_status', color=(255, 200, 100))
        dpg.add_text('Kleisli Monadic Compositions (g o_T f)(A, C) (Selectable cells):')
        create_bordered_table(
            tag='table_kleisli_res',
            columns=['Monad Semiring Category', 'Composed Morphism Result (g o_T f)'],
            width=600,
        )


# --- Navigation Sidebar Builder ---
VIEWS: list[str] = [
    'semiring_matrix_power',
    'forman_ricci_curvature',
    'pq_key_exchange',
    'algebraic_trie',
    'pagerank',
    'cyk_parser',
    'slope_transform',
    'automata_simulator',
    'markov_info_theory',
    'signal_transforms',
    'image_convolution_2d',
    'network_curvature_vis',
    'blackhole_spacetime',
    'sparse_tensor_einsum',
    'trajectoid_kinematics',
    'algebraic_knot_theory',
    'optical_holography',
    'financial_risk',
    'sheaf_cohomology',
    'gaussian_splatting',
    'topological_homology',
    'clifford_geometric_algebra',
    'galois_finite_fields',
    'categorical_kleisli',
]


def change_view(sender: int | str, app_data: Any, user_data: str) -> None:
    selected_view: str = user_data
    for v in VIEWS:
        dpg.set_value(f'sel_{v}', (v == selected_view))
        if v == selected_view:
            dpg.show_item(f'view_{v}_group')
        else:
            dpg.hide_item(f'view_{v}_group')


def build_navigation_sidebar() -> None:
    with dpg.child_window(width=280, height=-1, border=True):
        dpg.add_text('ALGEBRAIC EXPLORER', color=(100, 255, 100))
        dpg.add_separator()
        dpg.add_spacer(height=5)

        with dpg.tree_node(label='Matrix & Graph Algorithms', default_open=True):
            dpg.add_selectable(
                label='Semiring Matrix Power',
                tag='sel_semiring_matrix_power',
                callback=change_view,
                user_data='semiring_matrix_power',
                default_value=True,
            )
            dpg.add_selectable(
                label='Forman-Ricci Curvature',
                tag='sel_forman_ricci_curvature',
                callback=change_view,
                user_data='forman_ricci_curvature',
            )
            dpg.add_selectable(
                label='PageRank Algorithm',
                tag='sel_pagerank',
                callback=change_view,
                user_data='pagerank',
            )
            dpg.add_selectable(
                label='Network Curvature Vis',
                tag='sel_network_curvature_vis',
                callback=change_view,
                user_data='network_curvature_vis',
            )

        with dpg.tree_node(label='Automata, Parsing & Risk', default_open=True):
            dpg.add_selectable(
                label='Automata Simulator',
                tag='sel_automata_simulator',
                callback=change_view,
                user_data='automata_simulator',
            )
            dpg.add_selectable(
                label='CYK Grammar Parser',
                tag='sel_cyk_parser',
                callback=change_view,
                user_data='cyk_parser',
            )
            dpg.add_selectable(
                label='Financial Portfolio Risk',
                tag='sel_financial_risk',
                callback=change_view,
                user_data='financial_risk',
            )

        with dpg.tree_node(label='Transforms, Signals & Waves', default_open=True):
            dpg.add_selectable(
                label='Slope Transform',
                tag='sel_slope_transform',
                callback=change_view,
                user_data='slope_transform',
            )
            dpg.add_selectable(
                label='Signal Transforms',
                tag='sel_signal_transforms',
                callback=change_view,
                user_data='signal_transforms',
            )
            dpg.add_selectable(
                label='2D Image Convolution',
                tag='sel_image_convolution_2d',
                callback=change_view,
                user_data='image_convolution_2d',
            )
            dpg.add_selectable(
                label='Optical Holography',
                tag='sel_optical_holography',
                callback=change_view,
                user_data='optical_holography',
            )

        with dpg.tree_node(label='Tensors, Tries & Physics', default_open=True):
            dpg.add_selectable(
                label='Algebraic Trie / Tensor',
                tag='sel_algebraic_trie',
                callback=change_view,
                user_data='algebraic_trie',
            )
            dpg.add_selectable(
                label='Sparse Tensor Einsum',
                tag='sel_sparse_tensor_einsum',
                callback=change_view,
                user_data='sparse_tensor_einsum',
            )
            dpg.add_selectable(
                label='Trajectoid Kinematics',
                tag='sel_trajectoid_kinematics',
                callback=change_view,
                user_data='trajectoid_kinematics',
            )
            dpg.add_selectable(
                label='Schwarzschild Black Hole',
                tag='sel_blackhole_spacetime',
                callback=change_view,
                user_data='blackhole_spacetime',
            )
            dpg.add_selectable(
                label='3D Gaussian Splatting',
                tag='sel_gaussian_splatting',
                callback=change_view,
                user_data='gaussian_splatting',
            )

        with dpg.tree_node(label='Topology & Geometry', default_open=True):
            dpg.add_selectable(
                label='Knot Theory & Skein',
                tag='sel_algebraic_knot_theory',
                callback=change_view,
                user_data='algebraic_knot_theory',
            )
            dpg.add_selectable(
                label='Sheaf Cohomology',
                tag='sel_sheaf_cohomology',
                callback=change_view,
                user_data='sheaf_cohomology',
            )
            dpg.add_selectable(
                label='Simplicial Homology',
                tag='sel_topological_homology',
                callback=change_view,
                user_data='topological_homology',
            )
            dpg.add_selectable(
                label='Clifford Geometric Algebra',
                tag='sel_clifford_geometric_algebra',
                callback=change_view,
                user_data='clifford_geometric_algebra',
            )
            dpg.add_selectable(
                label='Galois Finite Fields',
                tag='sel_galois_finite_fields',
                callback=change_view,
                user_data='galois_finite_fields',
            )
            dpg.add_selectable(
                label='Categorical Kleisli Monads',
                tag='sel_categorical_kleisli',
                callback=change_view,
                user_data='categorical_kleisli',
            )

        with dpg.tree_node(label='Information & Crypto', default_open=True):
            dpg.add_selectable(
                label='Markov & Info Theory',
                tag='sel_markov_info_theory',
                callback=change_view,
                user_data='markov_info_theory',
            )
            dpg.add_selectable(
                label='Post-Quantum Key Exchange',
                tag='sel_pq_key_exchange',
                callback=change_view,
                user_data='pq_key_exchange',
            )


# --- Dear PyGui Context & Theme Initialization ---

dpg.create_context()

init_texture_data: list[float] = [0.1, 0.1, 0.1, 1.0] * (TEXTURE_WIDTH * TEXTURE_HEIGHT)
with dpg.texture_registry(show=False):
    dpg.add_dynamic_texture(
        width=TEXTURE_WIDTH, height=TEXTURE_HEIGHT, default_value=init_texture_data, tag='texture_img_input'
    )
    dpg.add_dynamic_texture(
        width=TEXTURE_WIDTH, height=TEXTURE_HEIGHT, default_value=init_texture_data, tag='texture_img_output'
    )

dpg.create_viewport(title='AlgebraX Graphical Laboratory', width=1200, height=900)


def setup_window_icon() -> None:
    png_path = 'site/assets/images/favicon.png'
    ico_path = 'recipes/logo.ico'

    if not os.path.exists(ico_path) and os.path.exists(png_path):
        try:
            img = Image.open(png_path)
            img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        except Exception:
            pass

    if os.path.exists(ico_path):
        try:
            dpg.set_viewport_small_icon(ico_path)
            dpg.set_viewport_large_icon(ico_path)
        except Exception:
            pass


setup_window_icon()

with dpg.theme() as global_theme, dpg.theme_component(dpg.mvAll):
    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (23, 23, 27))
    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (45, 45, 55))
    dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 80))
    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 110))
    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 140))
    dpg.add_theme_color(dpg.mvThemeCol_Header, (40, 40, 50))
    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (32, 32, 40))
    dpg.add_theme_color(dpg.mvThemeCol_Tab, (40, 40, 50))
    dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (60, 60, 80))
    dpg.add_theme_color(dpg.mvThemeCol_TabActive, (80, 80, 100))

dpg.bind_theme(global_theme)


# --- Main Window Builder ---
def main() -> None:
    with dpg.window(
        label='AlgebraX Graphical Lab',
        width=1180,
        height=860,
        no_title_bar=True,
        no_move=True,
        no_resize=True,
    ) as main_window:
        dpg.add_text('ALGEBRAX GRAPHICAL LABORATORY', color=(150, 180, 255))
        dpg.add_separator()

        with dpg.group(horizontal=True):
            build_navigation_sidebar()
            with dpg.child_window(width=-1, height=-1, border=False):
                build_view_semiring()
                build_view_curvature()
                build_view_crypto()
                build_view_trie()
                build_view_pagerank()
                build_view_cyk()
                build_view_slope()
                build_view_automata()
                build_view_markov_info()
                build_view_signal_transforms()
                build_view_image_conv()
                build_view_network_vis()
                build_view_blackhole()
                build_view_sparse_tensor_einsum()
                build_view_trajectoid()
                build_view_knot_theory()
                build_view_optical_holography()
                build_view_financial_risk()
                build_view_sheaf_cohomology()
                build_view_gaussian_splatting()
                build_view_topological_homology()
                build_view_clifford_geometric_algebra()
                build_view_galois_finite_fields()
                build_view_categorical_kleisli()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(main_window, True)

    recalculate_and_reset_layout()

    while dpg.is_dearpygui_running():
        update_graph_simulation()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == '__main__':
    main()
