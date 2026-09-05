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
│   ├── ax.semiring.Semiring Matrix Power          (View 1: Tropical, Arctic, Viterbi, Expectation, Provenance, etc.)
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
│   ├── Sparse Tensor Einsum           (View 14: Arbitrary-rank ax.tensor.einsum over Standard & Tropical semirings)
│   ├── Trajectoid Kinematics          (View 15: Non-holonomic rolling velocity & SO(3) 3x3 rotation)
│   ├── Schwarzschild Black Hole       (View 13: Metric components, light deflection & Hawking ax.probability.entropy)
│   └── 3D Gaussian Splatting          (View 20: 3D spatial covariance Sigma & 2D projective screen splatting)
├── Topology & Geometry
│   ├── Knot Theory & Skein            (View 16: Knot connected sum (#) & Artin braid crossing signatures)
│   ├── Sheaf Cohomology               (View 19: Cellular sheaf coboundary & sensor consensus)
│   ├── Simplicial Homology            (View 21: Boundary nilpotency D_{k-1} o D_k = 0 & Betti barcodes)
│   ├── Clifford Geometric Algebra     (View 22: Cl(3,0) multivectors & 3D rotor rotation sandwiching)
│   ├── Galois Finite Fields           (View 23: GF(2^8) polynomial modulo arithmetic & AES MixColumns)
│   └── Categorical Kleisli Monads     (View 24: Monadic Kleisli composition g o_T f across semirings)
└── Information & Crypto
    ├── Markov & Info Theory           (View 9: Markov steps, steady state & Shannon/KL info metrics)
    └── Post-Quantum Key Exchange      (View 3: Diffie-Hellman matrix key exchange over Digital ax.semiring.Semiring)
├── Automatic Differentiation & Neural Networks
│   ├── Forward-Mode Autodiff          (View 25: Quotient polynomial ring DualNumber & gradient bundles)
│   ├── Sparse Neural Backprop         (View 26: Adjoint pullback W^T * z_bar & outer-product weight gradients)
│   └── Functional Autograd Engine     (View 27: Dynamic computation DAG, reverse topological VJPs & optimization)
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
              # ax.matrix.add columns & rows
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
   In `build_navigation_sidebar()`, ax.matrix.add `dpg.add_selectable` under the appropriate tree node:
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
import sys
from collections.abc import Callable, Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

import dearpygui.dearpygui as dpg

# Ensure repo root and src dir are accessible
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import algebrax as ax  # noqa: E402
from recipes.algebraic_knot_theory import (  # noqa: E402
    compute_connected_sum,
    evaluate_braid_word,
)
from recipes.blackhole_spacetime_simulation import (  # noqa: E402
    evaluate_schwarzschild_simulation,
)
from recipes.categorical_kleisli_monads import (  # noqa: E402
    compose_kleisli_arrows,
)
from recipes.clifford_rotor_kinematics import (  # noqa: E402
    apply_rotor_rotation,
    compute_geometric_magnitude,
)
from recipes.distributed_vector_clocks import (  # noqa: E402
    compare_vector_clocks,
    compute_causal_dag_analysis,
    compute_causality_matrix,
    merge_vector_clocks,
    simulate_distributed_cluster,
    synchronize_crdt_replicas,
)
from recipes.extreme_risk_tail_moments import (  # noqa: E402
    audit_tail_risk_comparison,
    evaluate_multivariate_joint_risk,
    propagate_cascading_moments,
)
from recipes.financial_risk_portfolio import (  # noqa: E402
    compute_portfolio_centralities,
    evaluate_portfolio_path_variance,
    simulate_trading_strategy,
)
from recipes.forward_mode_autodiff import DualNumber, evaluate_dual, evaluate_dual_graph  # noqa: E402
from recipes.functional_autograd_engine import Value, build_and_evaluate_dag  # noqa: E402
from recipes.galois_field_cryptography import (  # noqa: E402
    gf_mix_columns,
    gf_multiply,
)
from recipes.nlp_provenance_parser import GrammarSemiring, parse_cyk  # noqa: E402
from recipes.optical_holography_simulation import (  # noqa: E402
    record_hologram,
)
from recipes.post_quantum_crypto_exchange import (  # noqa: E402
    perform_digital_key_exchange,
)
from recipes.quantum_feynman_path_integral import (  # noqa: E402
    simulate_aharonov_bohm_effect,
    simulate_double_slit,
    simulate_two_path_interference,
)
from recipes.relativistic_dirac_spinor import (  # noqa: E402
    boost_spinor,
    compute_dirac_current,
    create_dirac_spinor,
    rotate_spinor,
)
from recipes.sheaf_cohomology_consensus import (  # noqa: E402
    simulate_sheaf_consensus,
)
from recipes.sparse_neural_backprop import SparseLinearLayer, SparseMLP, train_sparse_mlp  # noqa: E402
from recipes.topological_homology_betti import (  # noqa: E402
    evaluate_simplicial_complex,
    get_homology_preset,
)
from recipes.trajectoid_rolling_kinematics import (  # noqa: E402
    simulate_trajectoid_kinematics,
)

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


# --- Custom Semirings ---
class IntervalSemiring(ax.semiring.Semiring[tuple[float, float]]):
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
        val = '{\n  "0": {"1": [0.5, 1.0, 2.0]},\n  "1": {"2": [1.0, 8.0, 64.0]}\n}'
    elif semiring_name == 'BivariateVariance':
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
            semiring: ax.semiring.Semiring[Any] = ax.semiring.TropicalSemiring()
            parser = float
        elif semiring_name == 'Arctic':
            semiring = ax.semiring.ArcticSemiring()
            parser = float
        elif semiring_name == 'Viterbi':
            semiring = ax.semiring.ViterbiSemiring()
            parser = float
        elif semiring_name == 'String':
            semiring = ax.semiring.StringSemiring()
            parser = set
        elif semiring_name == 'Expectation':
            semiring = ax.semiring.ExpectationSemiring()

            def parse_expectation(x: list[Any]) -> tuple[float, float]:
                return (float(x[0]), float(x[1]))

            parser = parse_expectation
        elif semiring_name == 'Provenance':
            semiring = ax.semiring.ProvenanceSemiring()

            def parse_provenance(d: dict[str, int]) -> dict[tuple[str, ...], int]:
                return {tuple(k.split(',')) if isinstance(k, str) else tuple(k): int(v) for k, v in d.items()}

            parser = parse_provenance
        elif semiring_name == 'Variance':
            semiring = ax.semiring.VarianceSemiring()

            def parse_variance(x: list[Any]) -> tuple[float, float, float]:
                return (float(x[0]), float(x[1]), float(x[2]))

            parser = parse_variance
        elif semiring_name == 'BivariateVariance':
            semiring = ax.semiring.BivariateVarianceSemiring()

            def parse_biv_variance(x: list[Any]) -> tuple[float, float, float, float]:
                return (float(x[0]), float(x[1]), float(x[2]), float(x[3]))

            parser = parse_biv_variance
        elif semiring_name == 'Digital':
            semiring = ax.semiring.DigitalSemiring()
            parser = int
        elif semiring_name == 'Modular':
            semiring = ax.semiring.ModularSemiring(p=5)
            parser = int
        elif semiring_name == 'Interval (Convex Hull)':
            semiring = IntervalSemiring()

            def parse_interval(x: list[Any]) -> tuple[float, float]:
                return (float(x[0]), float(x[1]))

            parser = parse_interval
        else:
            semiring = ax.semiring.StandardSemiring()
            parser = float

        for u, neighbors in custom_g.items():
            u_key = int(u) if u.isdigit() else u
            row: dict[Any, Any] = {}
            for v, w in neighbors.items():
                v_key = int(v) if v.isdigit() else v
                row[v_key] = parser(w)
            parsed_g[u_key] = row

        res = ax.matrix.power(parsed_g, power_val, semiring=semiring)

        display_matrix_in_table(res, 'table_semiring_res')
        dpg.set_value('semiring_status', f'Computed {semiring_name} ax.matrix.power {power_val} successfully.')
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

        res = ax.analysis.forman_ricci_curvature(graph, augmented=is_augmented)

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
    try:
        a1: int = int(dpg.get_value('crypto_a1'))
        a2: int = int(dpg.get_value('crypto_a2'))
        b1: int = int(dpg.get_value('crypto_b1'))
        b2: int = int(dpg.get_value('crypto_b2'))

        a_mat: dict[int, dict[int, int]] = {0: {0: a1, 1: a2}, 1: {0: a2, 1: a1}}
        b_mat: dict[int, dict[int, int]] = {0: {0: b1, 1: b2}, 1: {0: b2, 1: b1}}

        u_mat, v_mat, ka_mat, kb_mat, match = perform_digital_key_exchange(a_mat, b_mat)

        display_matrix_in_table(u_mat, 'table_crypto_u')
        display_matrix_in_table(v_mat, 'table_crypto_v')
        display_matrix_in_table(ka_mat, 'table_crypto_ka')
        display_matrix_in_table(kb_mat, 'table_crypto_kb')

        dpg.set_value('crypto_match_text', f'Keys Match: {match}')
        dpg.set_value('crypto_status', 'Successfully performed key exchange simulation.')
    except Exception as e:
        dpg.set_value('crypto_status', f'Error: {e}')


def run_trie_operations() -> None:

    try:
        trie: ax.trie.AlgebraicTrie[Any, float] = ax.trie.AlgebraicTrie(semiring=ax.semiring.StandardSemiring)
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
        rank_vec = ax.analysis.pagerank(graph, damping=alpha, max_iter=iterations)

        clear_table_rows('table_pagerank')
        sorted_ranks = sorted(rank_vec.items(), key=lambda x: x[1], reverse=True)
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
        rules: dict[tuple[str, str], set[str]] = {
            (parts[0].strip(), parts[1].strip()): set(v)
            for k, v in parsed_rules.items()
            if len(parts := k.split(',')) == 2
        }

        final_tags, chart = parse_cyk(sentence, lexicon, rules)

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
            val = ax.transforms.legendre_fenchel(parsed_signal, s)
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
        next_state = ax.automata.dfa_step(current, sym_key, normalized_transitions)
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
        next_states = ax.automata.nfa_step(current, sym_key, normalized_transitions)
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
            curr_state = ax.probability.markov_step(curr_state, matrix)

        steady = ax.probability.markov_steady_state(matrix)

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

        h_p = ax.probability.entropy(p_dist)
        h_q = ax.probability.entropy(q_dist)
        h_cross = ax.probability.cross_entropy(p_dist, q_dist)
        kl_div = ax.probability.kl_divergence(p_dist, q_dist)
        mi_val = ax.probability.mutual_information(joint_dist)

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
            res = ax.transforms.dft(f_vec)
        elif op == 'IDFT':
            res = ax.transforms.idft(f_vec)
        elif op == 'Hilbert Transform':
            res = ax.transforms.hilbert(f_vec)
        elif op == 'Convolution':
            g_str: str = dpg.get_value('signal_g')
            raw_g: dict[str, Any] = json.loads(g_str)
            g_vec = {int(k): float(v) for k, v in raw_g.items()}
            res = ax.transforms.convolve(f_vec, g_vec)
        elif op == 'Z-Transform':
            z_str: str = dpg.get_value('signal_z_input')
            z_val = complex(z_str)
            res_val = ax.transforms.z_transform(f_vec, z_val)
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

        sim = evaluate_schwarzschild_simulation(r_s, r, b)

        clear_table_rows('table_bh_res')
        rows = [
            ('Schwarzschild Radius (r_s)', f'{sim["r_s"]:.2f} km'),
            ('Observation Radius (r)', f'{sim["r"]:.2f} km'),
            ('Time Metric Component g_tt(r)', f'{sim["g_tt"]:.6f}'),
            ('Radial Metric Component g_rr(r)', f'{sim["g_rr"]:.6f}'),
            ('Photon Deflection Angle (Delta phi)', f'{sim["deflect_rad"]:.4f} rad ({sim["deflect_deg"]:.2f} deg)'),
            ('Event Horizon Area (A)', f'{sim["horizon_area"]:.2f} km^2'),
            ('Bekenstein-Hawking Entropy (S_BH)', f'{sim["hawking_entropy"]:.2f} nats'),
        ]

        for prop, val in rows:
            with dpg.table_row(parent='table_bh_res'):
                dpg.add_input_text(default_value=prop, readonly=True, width=-1)
                dpg.add_input_text(default_value=val, readonly=True, width=-1)

        dpg.set_value('bh_status', 'Successfully evaluated Schwarzschild spacetime metric.')
    except Exception as e:
        dpg.set_value('bh_status', f'Error: {e}')


def run_sparse_tensor_einsum() -> None:

    subscripts: str = dpg.get_value('tensor_subscripts')
    semiring_name: str = dpg.get_value('tensor_semiring')
    a_str: str = dpg.get_value('tensor_a_input')
    b_str: str = dpg.get_value('tensor_b_input')

    try:
        raw_a: list[tuple[list[Any], float]] = json.loads(a_str)
        raw_b: list[tuple[list[Any], float]] = json.loads(b_str)

        trie_a: ax.trie.AlgebraicTrie[Any, float] = ax.trie.AlgebraicTrie(semiring=ax.semiring.StandardSemiring)
        for coord, val in raw_a:
            trie_a[tuple(coord)] = float(val)

        trie_b: ax.trie.AlgebraicTrie[Any, float] = ax.trie.AlgebraicTrie(semiring=ax.semiring.StandardSemiring)
        for coord, val in raw_b:
            trie_b[tuple(coord)] = float(val)

        if 'Tropical' in semiring_name:
            semiring: ax.semiring.Semiring[float] = ax.semiring.TropicalSemiring()
        elif 'Arctic' in semiring_name:
            semiring = ax.semiring.ArcticSemiring()
        else:
            semiring = ax.semiring.StandardSemiring()

        res_trie = ax.tensor.einsum(subscripts, trie_a, trie_b, semiring=semiring)

        clear_table_rows('table_tensor_einsum_res')
        for key in sorted(res_trie):
            with dpg.table_row(parent='table_tensor_einsum_res'):
                dpg.add_input_text(default_value=str(key), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{res_trie[key]:.4f}', readonly=True, width=-1)

        dpg.set_value('tensor_einsum_status', f"Successfully evaluated ax.tensor.einsum('{subscripts}').")
    except Exception as e:
        dpg.set_value('tensor_einsum_status', f'Error: {e}')


def run_trajectoid_sim() -> None:
    steps: int = dpg.get_value('trajectoid_steps')
    freq: float = dpg.get_value('trajectoid_freq')

    try:
        res = simulate_trajectoid_kinematics(steps=steps, freq=freq)
        display_matrix_in_table(res['final_rotation'], 'table_trajectoid_so3')
        dpg.set_value('trajectoid_status', 'Successfully integrated non-holonomic SO(3) rolling trajectory.')
    except Exception as e:
        dpg.set_value('trajectoid_status', f'Error: {e}')


def run_knot_theory() -> None:
    knot_a_name: str = dpg.get_value('knot_a_select')
    knot_b_name: str = dpg.get_value('knot_b_select')
    crossings_str: str = dpg.get_value('knot_crossings')

    try:
        knot_a = {knot_a_name: 1.0}
        knot_b = {knot_b_name: 1.0}
        composite_knot = compute_connected_sum(knot_a, knot_b)

        crossings: list[int] = json.loads(crossings_str)
        n_strands = max(max(crossings, default=1) + 1, 2)
        perm, sig = evaluate_braid_word(crossings, n_strands=n_strands)

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

    ref_phase: float = float(dpg.get_value('hologram_ref_phase'))
    object_str: str = dpg.get_value('hologram_object_input')

    try:
        raw_obj: dict[str, Any] = json.loads(object_str)
        obj_wave: dict[int, complex] = {
            int(k): complex(v) if isinstance(v, str) else complex(float(v), 0.0) for k, v in raw_obj.items()
        }

        interf_intensity, spectrum, fringe_entropy = record_hologram(obj_wave, ref_phase=ref_phase)

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
    signal_input: str = dpg.get_value('fin_signals')
    corr_str: str = dpg.get_value('fin_corr_matrix')

    try:
        signals = [s.strip() for s in signal_input.split(',') if s.strip()]
        final_state = simulate_trading_strategy(signals)

        raw_corr: dict[str, dict[str, float]] = json.loads(corr_str)
        centrality = compute_portfolio_centralities(raw_corr)

        clear_table_rows('table_fin_centrality')
        for asset, val in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
            with dpg.table_row(parent='table_fin_centrality'):
                dpg.add_input_text(default_value=str(asset), readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{val:.4f}', readonly=True, width=-1)

        dpg.set_value('fin_result_text', f'Final Trade Strategy State: {final_state}')
        dpg.set_value('fin_status', 'Successfully computed portfolio centrality & trade DFA execution.')
    except Exception as e:
        dpg.set_value('fin_status', f'Error: {e}')


def run_extreme_tail_risk() -> None:
    try:
        # Step 1: Comparative Tail Risk Audit (from recipes.extreme_risk_tail_moments)
        tail_comparison = audit_tail_risk_comparison()
        clear_table_rows('table_tail_risk_comparison')
        for route_name, stats in tail_comparison.items():
            risk_desc = 'Low Risk (Symmetric)' if 'Gaussian' in route_name else 'HIGH CRASH RISK (Left Tail)'
            with dpg.table_row(parent='table_tail_risk_comparison'):
                dpg.add_input_text(default_value=route_name, readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{stats["mean"]:.2f}', readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{stats["variance"]:.2f}', readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{stats["skewness"]:+.2f}', readonly=True, width=-1)
                dpg.add_input_text(default_value=f'{stats["kurtosis"]:.2f}', readonly=True, width=-1)
                dpg.add_input_text(default_value=risk_desc, readonly=True, width=-1)

        # Step 2: 5th-Order Cascading Moment Propagation (from recipes.extreme_risk_tail_moments)
        step2_res = propagate_cascading_moments(order=5, steps=3)
        dpg.set_value(
            'tail_moment5_summary',
            f'3-Hop Cascade (Order 5) -> Mean: {step2_res["mean"]:.2f}, Var: {step2_res["variance"]:.2f}, '
            f'Skewness: {step2_res["skewness"]:+.4f}, Kurtosis: {step2_res["kurtosis"]:.4f}, '
            f'Hyperskewness: {step2_res["hyperskewness"]:+.4f}',
        )

        # Step 3: Multivariate Moment Covariance Matrix (from recipes.extreme_risk_tail_moments)
        step3_res = evaluate_multivariate_joint_risk(num_vars=2, order=2, steps=2)
        cov_matrix = step3_res['covariance_matrix']
        mean_vec = step3_res['mean_vector']
        corr_12 = step3_res['correlation']

        clear_table_rows('table_joint_cov_res')
        with dpg.table_row(parent='table_joint_cov_res'):
            dpg.add_input_text(default_value='Feature 1: Cost ($)', readonly=True, width=-1)
            dpg.add_input_text(default_value=f'{cov_matrix[0][0]:+.4f} (Var Cost)', readonly=True, width=-1)
            dpg.add_input_text(default_value=f'{cov_matrix[0][1]:+.4f} (Cov Cost,Lat)', readonly=True, width=-1)

        with dpg.table_row(parent='table_joint_cov_res'):
            dpg.add_input_text(default_value='Feature 2: Latency (ms)', readonly=True, width=-1)
            dpg.add_input_text(default_value=f'{cov_matrix[1][0]:+.4f} (Cov Lat,Cost)', readonly=True, width=-1)
            dpg.add_input_text(default_value=f'{cov_matrix[1][1]:+.4f} (Var Lat)', readonly=True, width=-1)

        dpg.set_value(
            'joint_cov_summary',
            f'Mean Vector [E[Cost], E[Latency]]: [{mean_vec[0]:.2f} $, {mean_vec[1]:.2f} ms] | '
            f'Cross-Correlation ρ(Cost, Lat): {corr_12:+.4f}',
        )
        dpg.set_value('tail_risk_status', 'Successfully evaluated higher-order moments & multivariate covariance!')
    except Exception as e:
        dpg.set_value('tail_risk_status', f'Error: {e}')


def run_sheaf_cohomology() -> None:
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

        curr_states = simulate_sheaf_consensus(agent_states, comm_graph=comm_graph, steps=steps, dt=0.1)

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
    try:
        from gaussian_splatting_rendering import compute_2d_projected_covariance, compute_3d_covariance
    except ImportError:
        from recipes.gaussian_splatting_rendering import compute_2d_projected_covariance, compute_3d_covariance

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

    try:
        preset: str = dpg.get_value('homology_preset')
        dpg.delete_item('homology_canvas', children_only=True)

        simplices, coords, max_k = get_homology_preset(preset)
        res = evaluate_simplicial_complex(simplices, max_k=max_k)
        sc = res['complex']
        betti = res['betti']

        for s in sc._simplices.get(2, set()):
            p1, p2, p3 = coords[s[0]], coords[s[1]], coords[s[2]]
            dpg.draw_triangle(p1, p2, p3, color=(80, 160, 255, 100), fill=(40, 100, 200, 80), parent='homology_canvas')

        for s in sc._simplices.get(1, set()):
            p1, p2 = coords[s[0]], coords[s[1]]
            dpg.draw_line(p1, p2, color=(50, 255, 150, 220), thickness=2, parent='homology_canvas')

        for v, pos in coords.items():
            dpg.draw_circle(pos, 10, color=(255, 200, 50), fill=(255, 100, 50), parent='homology_canvas')
            dpg.draw_text((pos[0] - 4, pos[1] - 6), str(v), color=(255, 255, 255), size=14, parent='homology_canvas')

        betti_data = {
            k: {
                'Dimension': f'beta_{k}',
                'Simplex Count': len(sc._simplices.get(k, set())),
                'Betti Hole Count': betti.get(k, 0),
                'Topological Interpretation': (
                    'Connected Components' if k == 0 else ('1D Topological Loops' if k == 1 else '2D Enclosed Voids')
                ),
            }
            for k in range(max_k + 1)
        }
        display_matrix_in_table(betti_data, 'table_homology_res')

        nilpotency_str = 'VERIFIED: D_0 o D_1 = 0' if res['nilpotency'] else 'FAILED'
        v_cnt = res['num_vertices']
        e_cnt = res['num_edges']
        dpg.set_value('homology_status', f'Complex: {v_cnt} vertices, {e_cnt} edges. {nilpotency_str}')
    except Exception as e:
        dpg.set_value('homology_status', f'Error: {e}')


def run_clifford_geometric_algebra() -> None:
    import math

    try:
        e1: float = float(dpg.get_value('clifford_v_e1'))
        e2: float = float(dpg.get_value('clifford_v_e2'))
        angle_deg: float = float(dpg.get_value('clifford_angle'))
        plane: str = dpg.get_value('clifford_plane')

        v = {(1,): e1, (2,): e2}
        mag = compute_geometric_magnitude(v, p=3, q=0, r=0)
        v_sq_val = mag**2

        bivector = (1, 2) if plane == 'e12 Plane (XY)' else ((2, 3) if plane == 'e23 Plane (YZ)' else (3, 1))
        v_rot = apply_rotor_rotation(v, angle_rad=math.radians(angle_deg), plane=bivector, p=3, q=0, r=0)

        dpg.delete_item('clifford_canvas', children_only=True)
        cx, cy = 200, 200
        scale = 25.0

        dpg.draw_line((30, cy), (370, cy), color=(100, 100, 120), thickness=1, parent='clifford_canvas')
        dpg.draw_line((cx, 30), (cx, 370), color=(100, 100, 120), thickness=1, parent='clifford_canvas')
        dpg.draw_text((350, cy + 5), 'e1', color=(180, 180, 180), parent='clifford_canvas')
        dpg.draw_text((cx + 5, 35), 'e2', color=(180, 180, 180), parent='clifford_canvas')

        vx, vy = cx + e1 * scale, cy - e2 * scale
        dpg.draw_line((cx, cy), (vx, vy), color=(50, 220, 255), thickness=3, parent='clifford_canvas')
        dpg.draw_circle((vx, vy), 4, color=(50, 220, 255), fill=(50, 220, 255), parent='clifford_canvas')
        dpg.draw_text((vx + 5, vy - 10), 'v (Original)', color=(50, 220, 255), parent='clifford_canvas')

        rot_e1, rot_e2 = v_rot.get((1,), 0.0), v_rot.get((2,), 0.0)
        rvx, rvy = cx + rot_e1 * scale, cy - rot_e2 * scale
        dpg.draw_line((cx, cy), (rvx, rvy), color=(50, 255, 100), thickness=3, parent='clifford_canvas')
        dpg.draw_circle((rvx, rvy), 4, color=(50, 255, 100), fill=(50, 255, 100), parent='clifford_canvas')
        dpg.draw_text((rvx + 5, rvy - 10), "v' (Rotor Transformed)", color=(50, 255, 100), parent='clifford_canvas')

        dpg.draw_circle((cx, cy), int(scale * 2), color=(255, 200, 50, 120), parent='clifford_canvas')

        dpg.set_value('clifford_v_sq_text', f'Multivector Magnitude Squared v^2 = {v_sq_val:.3f}')

        rot_data = {
            0: {
                'Blade Component': 'e1 Vector Blade',
                'Original Vector v': f'{e1:.3f}',
                "Rotor Transformed v'": f'{rot_e1:.3f}',
            },
            1: {
                'Blade Component': 'e2 Vector Blade',
                'Original Vector v': f'{e2:.3f}',
                "Rotor Transformed v'": f'{rot_e2:.3f}',
            },
            2: {
                'Blade Component': 'Rotor R = exp(-theta/2 * B)',
                'Original Vector v': 'R = 1.0',
                "Rotor Transformed v'": (
                    f'{math.cos(math.radians(angle_deg) / 2):.3f} - {math.sin(math.radians(angle_deg) / 2):.3f} e12'
                ),
            },
        }
        display_matrix_in_table(rot_data, 'table_clifford_res')
        dpg.set_value(
            'clifford_status',
            f'Cl(3,0) Rotor Rotation: theta={angle_deg:.1f} deg in {plane}. v^2 magnitude invariant under rotation.',
        )
    except Exception as e:
        dpg.set_value('clifford_status', f'Error: {e}')


def run_galois_finite_fields() -> None:
    try:
        hex1_str: str = dpg.get_value('galois_byte1')
        hex2_str: str = dpg.get_value('galois_byte2')

        byte1 = int(hex1_str, 16) if hex1_str.startswith('0x') else int(hex1_str)
        byte2 = int(hex2_str, 16) if hex2_str.startswith('0x') else int(hex2_str)

        def byte_to_poly(b: int) -> dict[int, int]:
            return {i: 1 for i in range(8) if (b & (1 << i))}

        def poly_to_byte(p: dict[int, float]) -> int:
            return sum((1 << exp) for exp, val in p.items() if int(val) % 2 == 1)

        res_poly = gf_multiply(byte_to_poly(byte1), byte_to_poly(byte2))
        res_byte = poly_to_byte(res_poly)

        dpg.set_value(
            'galois_poly_res_text',
            f'GF(2^8) Product: 0x{byte1:02X} * 0x{byte2:02X} mod P(x) = 0x{res_byte:02X} ({res_poly})',
        )

        mix_col = {
            0: {0: byte_to_poly(0x02), 1: byte_to_poly(0x03), 2: byte_to_poly(0x01), 3: byte_to_poly(0x01)},
            1: {0: byte_to_poly(0x01), 1: byte_to_poly(0x02), 2: byte_to_poly(0x03), 3: byte_to_poly(0x01)},
            2: {0: byte_to_poly(0x01), 1: byte_to_poly(0x01), 2: byte_to_poly(0x02), 3: byte_to_poly(0x03)},
            3: {0: byte_to_poly(0x03), 1: byte_to_poly(0x01), 2: byte_to_poly(0x01), 3: byte_to_poly(0x02)},
        }

        input_state_bytes = [
            [byte1, 0x87, 0x46, 0x8C],
            [byte2, 0x6E, 0x47, 0x40],
            [0x01, 0x46, 0x72, 0x98],
            [0x02, 0xA6, 0x5C, 0x93],
        ]

        state = {r: {c: byte_to_poly(input_state_bytes[r][c]) for c in range(4)} for r in range(4)}
        out_state = gf_mix_columns(state, mix_col_matrix=mix_col)

        dpg.delete_item('galois_canvas', children_only=True)

        for r in range(4):
            for c in range(4):
                val = input_state_bytes[r][c]
                dpg.draw_rectangle(
                    (30 + c * 35, 30 + r * 35),
                    (60 + c * 35, 60 + r * 35),
                    color=(100, 150, 255),
                    fill=(val, val // 2, 255 - val),
                    parent='galois_canvas',
                )
                dpg.draw_text(
                    (34 + c * 35, 38 + r * 35),
                    f'{val:02X}',
                    color=(255, 255, 255),
                    size=12,
                    parent='galois_canvas',
                )

        dpg.draw_text((190, 80), '--- MixColumns --->', color=(100, 255, 100), size=14, parent='galois_canvas')

        out_grid = []
        for r in range(4):
            row_vals = []
            for c in range(4):
                poly = out_state.get(r, {}).get(c, {})
                b_val = poly_to_byte(poly)
                row_vals.append(b_val)
                dpg.draw_rectangle(
                    (360 + c * 35, 30 + r * 35),
                    (390 + c * 35, 60 + r * 35),
                    color=(50, 255, 100),
                    fill=(b_val, 255 - b_val, b_val // 2),
                    parent='galois_canvas',
                )
                dpg.draw_text(
                    (364 + c * 35, 38 + r * 35),
                    f'{b_val:02X}',
                    color=(255, 255, 255),
                    size=12,
                    parent='galois_canvas',
                )
            out_grid.append(row_vals)

        gf_data = {
            r: {
                'Input State Bytes (Hex)': ' '.join(f'{input_state_bytes[r][c]:02X}' for c in range(4)),
                'MixColumns Transformed Output Bytes': ' '.join(f'{out_grid[r][c]:02X}' for c in range(4)),
            }
            for r in range(4)
        }
        display_matrix_in_table(gf_data, 'table_galois_res')
        dpg.set_value(
            'galois_status',
            'Evaluated AES GF(2^8) 4x4 MixColumns matrix transformation over irreduc poly P(x) = 0x11B.',
        )
    except Exception as e:
        dpg.set_value('galois_status', f'Error: {e}')


def run_categorical_kleisli() -> None:
    try:
        w_ab: float = float(dpg.get_value('kleisli_w_ab'))
        w_bc: float = float(dpg.get_value('kleisli_w_bc'))
        topology: str = dpg.get_value('kleisli_topology')

        dpg.delete_item('kleisli_canvas', children_only=True)

        if topology == 'Pipeline (A -> B -> C)':
            f = {'A': {'B': w_ab}}
            g = {'B': {'C': w_bc}}
            nodes = {'A': (70, 100), 'B': (200, 100), 'C': (330, 100)}
            edges = [('A', 'B', f'f={w_ab}'), ('B', 'C', f'g={w_bc}')]
            target = ('A', 'C')
        else:
            f = {'A': {'B': w_ab, 'C': 0.5}}
            g = {'B': {'D': w_bc}, 'C': {'D': 0.7}}
            nodes = {'A': (60, 100), 'B': (200, 40), 'C': (200, 160), 'D': (340, 100)}
            edges = [
                ('A', 'B', f'{w_ab}'),
                ('A', 'C', '0.5'),
                ('B', 'D', f'{w_bc}'),
                ('C', 'D', '0.7'),
            ]
            target = ('A', 'D')

        for src, dst, label in edges:
            p1, p2 = nodes[src], nodes[dst]
            dpg.draw_line(p1, p2, color=(100, 200, 255), thickness=2, parent='kleisli_canvas')
            mx, my = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
            dpg.draw_text((mx, my - 12), label, color=(255, 200, 50), size=12, parent='kleisli_canvas')

        for n, pos in nodes.items():
            dpg.draw_circle(pos, 16, color=(255, 100, 255), fill=(80, 40, 100), parent='kleisli_canvas')
            dpg.draw_text((pos[0] - 5, pos[1] - 7), n, color=(255, 255, 255), size=15, parent='kleisli_canvas')

        vit = compose_kleisli_arrows(f, g, semiring=ax.semiring.ViterbiSemiring())
        trop = compose_kleisli_arrows(f, g, semiring=ax.semiring.TropicalSemiring())
        boo_a = {'A': {'B': True}}
        boo_b = {'B': {'C': True}}
        boo = compose_kleisli_arrows(boo_a, boo_b, semiring=ax.semiring.BooleanSemiring())
        std = compose_kleisli_arrows(f, g, semiring=ax.semiring.StandardSemiring())

        src_node, dst_node = target
        cat_data = {
            0: {
                'Monad ax.semiring.Semiring Category': 'Viterbi Monad (Max-Product)',
                'Monad Binary Operator': 'a * b (Max Path Prob)',
                'Composed Result (g o_T f)': f'{vit.get(src_node, {}).get(dst_node, 0.0):.4f}',
            },
            1: {
                'Monad ax.semiring.Semiring Category': 'Tropical Monad (Min-Sum)',
                'Monad Binary Operator': 'a + b (Shortest Distance)',
                'Composed Result (g o_T f)': f'{trop.get(src_node, {}).get(dst_node, 0.0):.4f}',
            },
            2: {
                'Monad ax.semiring.Semiring Category': 'Boolean Monad (OR-AND)',
                'Monad Binary Operator': 'a and b (Reachability)',
                'Composed Result (g o_T f)': str(boo.get(src_node, {}).get(dst_node, False)),
            },
            3: {
                'Monad ax.semiring.Semiring Category': 'Standard Monad (Sum-Product)',
                'Monad Binary Operator': 'a * b (Path Count Weight)',
                'Composed Result (g o_T f)': f'{std.get(src_node, {}).get(dst_node, 0.0):.4f}',
            },
        }
        display_matrix_in_table(cat_data, 'table_kleisli_res')
        dpg.set_value(
            'kleisli_status',
            f'Evaluated Kleisli Monadic Composition (g o_T f)({src_node} -> {dst_node}) across 4 semiring monads.',
        )
    except Exception as e:
        dpg.set_value('kleisli_status', f'Error: {e}')


# --- Automatic Differentiation & Neural Backprop Callbacks ---


def run_forward_mode_autodiff() -> None:
    try:
        x_val = float(dpg.get_value('ad_input_x'))
        fn_choice = dpg.get_value('ad_fn_select')
        if 'ln(x)*sqrt(x) + sin(x)' in fn_choice and x_val <= 0:
            dpg.set_value('ad_status', 'Error: x must be strictly positive for ln(x) and sqrt(x).')
            return

        res_dual, formula = evaluate_dual(fn_choice, x_val)

        edge_x = float(dpg.get_value('ad_edge_x'))
        edge_y = float(dpg.get_value('ad_edge_y'))
        path_val = evaluate_dual_graph(edge_x, edge_y)

        dpg.set_value('ad_primal_res', f'{res_dual.val:.6f}')
        dpg.set_value('ad_tangent_res', f'{res_dual.der:.6f}')

        if dpg.does_item_exist('ad_canvas'):
            dpg.delete_item('ad_canvas', children_only=True)
            dpg.draw_rectangle(
                (0, 0), (700, 200), fill=(18, 18, 24), color=(60, 60, 80), thickness=1, parent='ad_canvas'
            )

            p0 = (100, 100)
            p1 = (350, 60)
            p2_pos = (600, 100)

            dpg.draw_line(p0, p1, color=(100, 200, 255), thickness=3, parent='ad_canvas')
            dpg.draw_text(
                (180, 55),
                f'Edge(0->1): x={edge_x:.1f} (seed dx=1.0)',
                color=(255, 200, 50),
                size=13,
                parent='ad_canvas',
            )

            dpg.draw_line(p1, p2_pos, color=(100, 200, 255), thickness=3, parent='ad_canvas')
            dpg.draw_text(
                (430, 55), f'Edge(1->2): y={edge_y:.1f} (dy=0.0)', color=(255, 200, 50), size=13, parent='ad_canvas'
            )

            dpg.draw_line(p0, p2_pos, color=(80, 80, 100), thickness=1, parent='ad_canvas')

            for pt, lbl in [(p0, '0'), (p1, '1'), (p2_pos, '2')]:
                dpg.draw_circle(pt, 18, color=(255, 100, 255), fill=(60, 30, 80), thickness=2, parent='ad_canvas')
                dpg.draw_text((pt[0] - 6, pt[1] - 8), lbl, color=(255, 255, 255), size=16, parent='ad_canvas')

            dpg.draw_text(
                (120, 150),
                f'2-Hop Path Transmission (0 -> 1 -> 2): Value={path_val.val:.2f}, Sensitivity d/dx={path_val.der:.2f}',
                color=(100, 255, 150),
                size=14,
                parent='ad_canvas',
            )

        table_data = {
            0: {
                'Expression / Path': fn_choice,
                'Primal Value': f'{res_dual.val:.6f}',
                'Exact Derivative (d/dx)': f'{res_dual.der:.6f}',
                'Mathematical Formula': formula,
            },
            1: {
                'Expression / Path': 'Graph Path (0 -> 1 -> 2)',
                'Primal Value': f'{path_val.val:.4f}',
                'Exact Derivative (d/dx)': f'{path_val.der:.4f}',
                'Mathematical Formula': 'd/dx (x * y) = y * (dx/dx)',
            },
        }
        display_matrix_in_table(table_data, 'table_ad_res')
        dpg.set_value('ad_status', 'Evaluated exact forward-mode automatic differentiation via DualNumber!')
    except Exception as e:
        dpg.set_value('ad_status', f'Error: {e}')


def run_sparse_neural_backprop() -> None:
    try:
        ds_choice = dpg.get_value('backprop_dataset')
        hidden_units = int(dpg.get_value('backprop_hidden'))
        lr = float(dpg.get_value('backprop_lr'))
        epochs = int(dpg.get_value('backprop_epochs'))

        if 'XOR' in ds_choice:
            data = [
                ({0: 0.0, 1: 0.0}, {0: 0.0}),
                ({0: 0.0, 1: 1.0}, {0: 1.0}),
                ({0: 1.0, 1: 0.0}, {0: 1.0}),
                ({0: 1.0, 1: 1.0}, {0: 0.0}),
            ]
        elif 'OR' in ds_choice:
            data = [
                ({0: 0.0, 1: 0.0}, {0: 0.0}),
                ({0: 0.0, 1: 1.0}, {0: 1.0}),
                ({0: 1.0, 1: 0.0}, {0: 1.0}),
                ({0: 1.0, 1: 1.0}, {0: 1.0}),
            ]
        else:
            data = [
                ({0: 0.0, 1: 0.0}, {0: 0.0}),
                ({0: 0.0, 1: 1.0}, {0: 0.0}),
                ({0: 1.0, 1: 0.0}, {0: 0.0}),
                ({0: 1.0, 1: 1.0}, {0: 1.0}),
            ]

        mlp = SparseMLP(layer_sizes=[2, hidden_units, 1], seed=42)
        total_epoch_loss = train_sparse_mlp(mlp, data, epochs=epochs, learning_rate=lr)

        dpg.set_value('backprop_loss_text', f'Final MSE Loss: {total_epoch_loss:.6f} (Epochs: {epochs})')

        if dpg.does_item_exist('backprop_canvas'):
            dpg.delete_item('backprop_canvas', children_only=True)
            dpg.draw_rectangle(
                (0, 0), (700, 220), fill=(18, 18, 24), color=(60, 60, 80), thickness=1, parent='backprop_canvas'
            )

            in_pos = [(120, 70), (120, 150)]
            h_step = 180 / (hidden_units + 1)
            hid_pos = [(350, int(20 + (i + 1) * h_step)) for i in range(hidden_units)]
            out_pos = [(580, 110)]

            for ip in in_pos:
                for hp in hid_pos:
                    dpg.draw_line(ip, hp, color=(70, 120, 180, 160), thickness=1, parent='backprop_canvas')
            for hp in hid_pos:
                for op in out_pos:
                    dpg.draw_line(hp, op, color=(180, 90, 70, 160), thickness=1, parent='backprop_canvas')

            for ip, lbl in zip(in_pos, ['x0', 'x1']):
                dpg.draw_circle(ip, 14, color=(100, 255, 100), fill=(30, 80, 30), parent='backprop_canvas')
                dpg.draw_text((ip[0] - 8, ip[1] - 7), lbl, color=(255, 255, 255), size=12, parent='backprop_canvas')

            for i, hp in enumerate(hid_pos):
                dpg.draw_circle(hp, 12, color=(100, 200, 255), fill=(30, 60, 90), parent='backprop_canvas')
                dpg.draw_text((hp[0] - 6, hp[1] - 6), f'h{i}', color=(255, 255, 255), size=11, parent='backprop_canvas')

            dpg.draw_circle(out_pos[0], 16, color=(255, 120, 100), fill=(90, 40, 30), parent='backprop_canvas')
            dpg.draw_text(
                (out_pos[0][0] - 5, out_pos[0][1] - 8), 'y', color=(255, 255, 255), size=14, parent='backprop_canvas'
            )

            dpg.draw_text(
                (30, 195),
                'Forward: z = W*x  |  Backward Pullback: x_bar = W^T * z_bar  |  Grad: z_bar (x) x^T',
                color=(255, 200, 100),
                size=13,
                parent='backprop_canvas',
            )

        table_data = {}
        for idx, (x_in, y_target) in enumerate(data):
            y_pred = mlp.forward(x_in)
            err = y_pred[0] - y_target[0]
            table_data[idx] = {
                'Input (x0, x1)': f'({x_in[0]:.0f}, {x_in[1]:.0f})',
                'Target (y)': f'{y_target[0]:.1f}',
                'Predicted Output': f'{y_pred[0]:.4f}',
                'Error (y - y*)': f'{err:+.4f}',
            }
        display_matrix_in_table(table_data, 'table_backprop_res')
        dpg.set_value('backprop_status', f'Successfully trained {ds_choice} MLP with adjoint backprop!')
    except Exception as e:
        dpg.set_value('backprop_status', f'Error: {e}')


def run_functional_autograd_engine() -> None:
    try:
        expr_choice = dpg.get_value('autograd_expr')
        vx = float(dpg.get_value('autograd_var_x'))
        vy = float(dpg.get_value('autograd_var_y'))
        vz = float(dpg.get_value('autograd_var_z'))

        out, x, y, z, _ = build_and_evaluate_dag(expr_choice, vx, vy, vz)

        dpg.set_value('autograd_f_val', f'{out.data:.6f}')
        dpg.set_value('autograd_grad_x', f'{x.grad:.6f}')
        dpg.set_value('autograd_grad_y', f'{y.grad:.6f}')

        if dpg.does_item_exist('autograd_canvas'):
            dpg.delete_item('autograd_canvas', children_only=True)
            dpg.draw_rectangle(
                (0, 0), (700, 220), fill=(18, 18, 24), color=(60, 60, 80), thickness=1, parent='autograd_canvas'
            )

            pos_x = (80, 50)
            pos_y = (80, 110)
            pos_z = (80, 170)
            pos_mid1 = (280, 70)
            pos_mid2 = (280, 150)
            pos_root = (540, 110)

            dpg.draw_line(pos_x, pos_mid1, color=(100, 200, 255), thickness=2, parent='autograd_canvas')
            dpg.draw_line(pos_y, pos_mid1, color=(100, 200, 255), thickness=2, parent='autograd_canvas')
            dpg.draw_line(pos_y, pos_mid2, color=(100, 200, 255), thickness=2, parent='autograd_canvas')
            dpg.draw_line(pos_z, pos_mid2, color=(100, 200, 255), thickness=2, parent='autograd_canvas')
            dpg.draw_line(pos_mid1, pos_root, color=(255, 180, 100), thickness=2, parent='autograd_canvas')
            dpg.draw_line(pos_mid2, pos_root, color=(255, 180, 100), thickness=2, parent='autograd_canvas')

            for p, lbl, val, gr in [
                (pos_x, 'x', x.data, x.grad),
                (pos_y, 'y', y.data, y.grad),
                (pos_z, 'z', z.data, z.grad),
            ]:
                dpg.draw_circle(p, 16, color=(100, 255, 100), fill=(30, 80, 30), parent='autograd_canvas')
                dpg.draw_text((p[0] - 6, p[1] - 8), lbl, color=(255, 255, 255), size=14, parent='autograd_canvas')
                dpg.draw_text(
                    (p[0] + 20, p[1] - 8),
                    f'val={val:.2f}, grad={gr:.4f}',
                    color=(180, 220, 255),
                    size=12,
                    parent='autograd_canvas',
                )

            dpg.draw_circle(pos_root, 20, color=(255, 100, 100), fill=(90, 30, 30), parent='autograd_canvas')
            dpg.draw_text(
                (pos_root[0] - 12, pos_root[1] - 8), 'Out', color=(255, 255, 255), size=14, parent='autograd_canvas'
            )
            dpg.draw_text(
                (pos_root[0] - 60, pos_root[1] + 25),
                f'Root Val={out.data:.4f}, Adjoint=1.0',
                color=(255, 200, 100),
                size=13,
                parent='autograd_canvas',
            )

        table_data = {
            0: {
                'Node / Variable': 'Root Output L',
                'Forward Value': f'{out.data:.6f}',
                'Accumulated Adjoint (dL/du)': f'{out.grad:.4f}',
                'Role': 'Objective Loss / Root DAG Node',
            },
            1: {
                'Node / Variable': 'Leaf Variable x',
                'Forward Value': f'{x.data:.4f}',
                'Accumulated Adjoint (dL/du)': f'{x.grad:.6f}',
                'Role': 'Input Feature / Tunable Parameter',
            },
            2: {
                'Node / Variable': 'Leaf Variable y',
                'Forward Value': f'{y.data:.4f}',
                'Accumulated Adjoint (dL/du)': f'{y.grad:.6f}',
                'Role': 'Input Feature / Tunable Parameter',
            },
            3: {
                'Node / Variable': 'Leaf Variable z',
                'Forward Value': f'{z.data:.4f}',
                'Accumulated Adjoint (dL/du)': f'{z.grad:.6f}',
                'Role': 'Input Feature / Tunable Parameter',
            },
        }
        display_matrix_in_table(table_data, 'table_autograd_res')
        dpg.set_value('autograd_status', 'Evaluated reverse-mode DAG backpropagation via Vector-Jacobian Products!')
    except Exception as e:
        dpg.set_value('autograd_status', f'Error: {e}')


def run_quantum_feynman_path_integral() -> None:
    try:
        exp_type = dpg.get_value('quantum_exp_type')
        slit_sep = float(dpg.get_value('quantum_slit_sep'))
        wavelength = float(dpg.get_value('quantum_wavelength'))
        flux = float(dpg.get_value('quantum_flux'))

        if dpg.does_item_exist('quantum_path_canvas'):
            dpg.delete_item('quantum_path_canvas', children_only=True)
            dpg.draw_rectangle(
                (0, 0), (700, 220), fill=(15, 18, 26), color=(50, 60, 90), thickness=1, parent='quantum_path_canvas'
            )

        table_data: dict[int | str, dict[str, str]] = {}

        if 'Double-Slit' in exp_type:
            results = simulate_double_slit(
                slit_separation=slit_sep,
                screen_distance=10.0,
                wavelength=wavelength,
                num_detectors=15,
            )
            # Draw Double-Slit Geometry & Wave Fringes on Canvas
            if dpg.does_item_exist('quantum_path_canvas'):
                # Source
                dpg.draw_circle((60, 110), 12, color=(100, 255, 255), fill=(30, 80, 100), parent='quantum_path_canvas')
                dpg.draw_text((45, 130), 'Source', color=(200, 240, 255), size=12, parent='quantum_path_canvas')

                # Slits barrier
                dpg.draw_line((220, 20), (220, 90), color=(180, 180, 200), thickness=4, parent='quantum_path_canvas')
                dpg.draw_line((220, 130), (220, 200), color=(180, 180, 200), thickness=4, parent='quantum_path_canvas')
                dpg.draw_circle((220, 95), 6, color=(255, 200, 100), fill=(255, 255, 100), parent='quantum_path_canvas')
                dpg.draw_circle(
                    (220, 125), 6, color=(255, 200, 100), fill=(255, 255, 100), parent='quantum_path_canvas'
                )
                dpg.draw_text((230, 85), 'Slit A', color=(255, 200, 100), size=11, parent='quantum_path_canvas')
                dpg.draw_text((230, 125), 'Slit B', color=(255, 200, 100), size=11, parent='quantum_path_canvas')

                # Rays to center screen
                dpg.draw_line(
                    (60, 110), (220, 95), color=(100, 200, 255, 140), thickness=1, parent='quantum_path_canvas'
                )
                dpg.draw_line(
                    (60, 110), (220, 125), color=(100, 200, 255, 140), thickness=1, parent='quantum_path_canvas'
                )

                # Draw Screen Detector Fringes (Intensity Bar Chart)
                max_p = max(r['probability'] for r in results) if results else 1.0
                max_p = max(max_p, 1e-9)

                for i, r in enumerate(results):
                    y_scr = int(25 + i * (170 / (len(results) - 1)))
                    bar_len = int((r['probability'] / max_p) * 200)
                    # Screen line
                    dpg.draw_line(
                        (450, y_scr),
                        (450 + bar_len, y_scr),
                        color=(100, 255, 150),
                        thickness=6,
                        parent='quantum_path_canvas',
                    )
                    dpg.draw_text(
                        (455 + bar_len, y_scr - 6),
                        f'{r["probability"]:.3f}',
                        color=(200, 255, 200),
                        size=10,
                        parent='quantum_path_canvas',
                    )
                    dpg.draw_line(
                        (220, 95), (450, y_scr), color=(80, 120, 180, 40), thickness=1, parent='quantum_path_canvas'
                    )
                    dpg.draw_line(
                        (220, 125), (450, y_scr), color=(80, 120, 180, 40), thickness=1, parent='quantum_path_canvas'
                    )

                dpg.draw_text(
                    (450, 10),
                    'Detector Screen Intensity P = |K|^2',
                    color=(100, 255, 150),
                    size=13,
                    parent='quantum_path_canvas',
                )

            for idx, r in enumerate(results):
                table_data[idx] = {
                    'Screen Detector': r['detector'],
                    'Spatial y': f'{r["y_pos"]:+6.2f}',
                    'Complex Amplitude': f'{r["amplitude"]}',
                    'Born Probability P': f'{r["probability"]:.6f}',
                }
            dpg.set_value('quantum_path_status', 'Simulated 2-step Feynman sum-over-histories with wave interference!')

        elif 'Aharonov-Bohm' in exp_type:
            z_ab, p_ab = simulate_aharonov_bohm_effect(magnetic_flux=flux)
            if dpg.does_item_exist('quantum_path_canvas'):
                dpg.draw_circle(
                    (350, 110), 30, color=(255, 100, 100), fill=(80, 20, 20), thickness=2, parent='quantum_path_canvas'
                )
                dpg.draw_text(
                    (310, 105), 'Solenoid (B=0)', color=(255, 150, 150), size=12, parent='quantum_path_canvas'
                )
                dpg.draw_text(
                    (330, 125), f'Flux Φ={flux:.2f}π', color=(255, 220, 100), size=11, parent='quantum_path_canvas'
                )
                # Top path
                dpg.draw_line((100, 110), (350, 40), color=(100, 200, 255), thickness=2, parent='quantum_path_canvas')
                dpg.draw_line((350, 40), (600, 110), color=(100, 200, 255), thickness=2, parent='quantum_path_canvas')
                dpg.draw_text((280, 20), 'Path 1: +qΦ/2ħ', color=(100, 200, 255), size=12, parent='quantum_path_canvas')
                # Bottom path
                dpg.draw_line((100, 110), (350, 180), color=(100, 255, 180), thickness=2, parent='quantum_path_canvas')
                dpg.draw_line((350, 180), (600, 110), color=(100, 255, 180), thickness=2, parent='quantum_path_canvas')
                dpg.draw_text(
                    (280, 195), 'Path 2: -qΦ/2ħ', color=(100, 255, 180), size=12, parent='quantum_path_canvas'
                )
                # Detector
                dpg.draw_circle((600, 110), 16, color=(255, 255, 100), fill=(90, 90, 20), parent='quantum_path_canvas')
                dpg.draw_text(
                    (570, 140), f'Detector P = {p_ab:.4f}', color=(255, 255, 150), size=13, parent='quantum_path_canvas'
                )

            table_data[0] = {
                'Experiment': 'Aharonov-Bohm Gauge Shift',
                'Magnetic Flux (Φ)': f'{flux:.4f} rad',
                'Total Amplitude K': f'{z_ab}',
                'Interference Probability P': f'{p_ab:.6f}',
            }
            dpg.set_value(
                'quantum_path_status', f'Calculated topological Aharonov-Bohm phase shift with Flux={flux:.2f}!'
            )

        display_matrix_in_table(table_data, 'table_quantum_path_res')
    except Exception as e:
        dpg.set_value('quantum_path_status', f'Error: {e}')


def run_relativistic_dirac_spinor() -> None:
    try:
        tr_type = dpg.get_value('dirac_transform_type')
        angle_deg = float(dpg.get_value('dirac_angle_deg'))
        rapidity = float(dpg.get_value('dirac_rapidity'))
        scalar_val = float(dpg.get_value('dirac_scalar'))
        biv12_val = float(dpg.get_value('dirac_spin_12'))

        psi_init = create_dirac_spinor(scalar=scalar_val, bivector_12=biv12_val)

        if 'Rotation' in tr_type:
            rad = math.radians(angle_deg)
            psi_transformed = rotate_spinor(psi_init, angle_rad=rad, plane=(2, 3))
            tr_desc = f'Spatial Rotation in (x,y)-plane by {angle_deg:.1f}° (4π Periodicity)'
        else:
            psi_transformed = boost_spinor(psi_init, rapidity=rapidity, axis=1)
            tr_desc = f'Relativistic Lorentz Boost along x-axis with Rapidity ξ = {rapidity:.2f}'

        # Compute conserved Dirac 4-current
        current_init = compute_dirac_current(psi_init)
        current_trans = compute_dirac_current(psi_transformed)

        # Draw Spinor Circle and 4-Current vectors on Canvas
        if dpg.does_item_exist('dirac_spinor_canvas'):
            dpg.delete_item('dirac_spinor_canvas', children_only=True)
            dpg.draw_rectangle(
                (0, 0), (700, 220), fill=(18, 16, 24), color=(60, 45, 80), thickness=1, parent='dirac_spinor_canvas'
            )

            # Left side: 4π Double-Covering Spinor Cycle
            center_spinor = (180, 110)
            radius = 70
            dpg.draw_circle(center_spinor, radius, color=(120, 80, 180), thickness=1, parent='dirac_spinor_canvas')
            dpg.draw_line(
                (center_spinor[0] - radius - 10, center_spinor[1]),
                (center_spinor[0] + radius + 10, center_spinor[1]),
                color=(60, 60, 80),
                parent='dirac_spinor_canvas',
            )
            dpg.draw_line(
                (center_spinor[0], center_spinor[1] - radius - 10),
                (center_spinor[0], center_spinor[1] + radius + 10),
                color=(60, 60, 80),
                parent='dirac_spinor_canvas',
            )

            # Half-angle spinor orientation: theta_spinor = angle_deg / 2
            half_rad = math.radians(angle_deg) / 2.0 if 'Rotation' in tr_type else 0.0
            pt_x = int(center_spinor[0] + radius * math.cos(half_rad))
            pt_y = int(center_spinor[1] - radius * math.sin(half_rad))

            dpg.draw_line(center_spinor, (pt_x, pt_y), color=(255, 100, 200), thickness=3, parent='dirac_spinor_canvas')
            dpg.draw_circle((pt_x, pt_y), 6, color=(255, 200, 255), fill=(255, 100, 200), parent='dirac_spinor_canvas')
            dpg.draw_text(
                (center_spinor[0] - 80, 15),
                'Spin-1/2 Rotor R = exp(-θ/2 B_12)',
                color=(255, 180, 220),
                size=12,
                parent='dirac_spinor_canvas',
            )
            dpg.draw_text(
                (center_spinor[0] - 60, 195),
                f'Rotor Half-Angle: {math.degrees(half_rad):.1f}°',
                color=(200, 160, 255),
                size=11,
                parent='dirac_spinor_canvas',
            )

            # Right side: Conserved Dirac Current J^mu Flow
            center_j = (520, 110)
            dpg.draw_circle(center_j, 60, color=(70, 100, 150), thickness=1, parent='dirac_spinor_canvas')
            j0_val = current_trans.get((1,), 0.0)
            j1_val = current_trans.get((2,), 0.0)

            j_vec_end = (int(center_j[0] + j1_val * 35), int(center_j[1] - j0_val * 35))
            dpg.draw_line(center_j, j_vec_end, color=(100, 255, 150), thickness=3, parent='dirac_spinor_canvas')
            dpg.draw_circle(j_vec_end, 5, color=(200, 255, 200), fill=(100, 255, 150), parent='dirac_spinor_canvas')
            dpg.draw_text(
                (center_j[0] - 80, 15),
                'Dirac 4-Current J = ψ γ_0 ψ^†',
                color=(100, 255, 150),
                size=12,
                parent='dirac_spinor_canvas',
            )
            dpg.draw_text(
                (center_j[0] - 70, 195),
                f'Density J^0: {j0_val:.4f} > 0',
                color=(150, 255, 200),
                size=11,
                parent='dirac_spinor_canvas',
            )

        table_data = {
            0: {
                'Spinor State / Multivector': 'Initial State ψ(0)',
                'Scalar α': f'{psi_init.get((), 0.0):.4f}',
                'Spin Bivector B_12': f'{psi_init.get((2, 3), 0.0):.4f}',
                'Boost Bivector B_01': f'{psi_init.get((1, 2), 0.0):.4f}',
                'Current Density J^0': f'{current_init.get((1,), 0.0):.4f}',
            },
            1: {
                'Spinor State / Multivector': f'Transformed State ψ ({tr_desc})',
                'Scalar α': f'{psi_transformed.get((), 0.0):.4f}',
                'Spin Bivector B_12': f'{psi_transformed.get((2, 3), 0.0):.4f}',
                'Boost Bivector B_01': f'{psi_transformed.get((1, 2), 0.0):.4f}',
                'Current Density J^0': f'{current_trans.get((1,), 0.0):.4f}',
            },
        }
        display_matrix_in_table(table_data, 'table_dirac_res')
        dpg.set_value('dirac_status', f'Computed relativistic Dirac spinor rotor transformation: {tr_desc}!')
    except Exception as e:
        dpg.set_value('dirac_status', f'Error: {e}')


def run_distributed_vector_clocks() -> None:
    try:
        view_mode = dpg.get_value('vclock_view_mode')
        trace = simulate_distributed_cluster()

        if dpg.does_item_exist('vclock_canvas'):
            dpg.delete_item('vclock_canvas', children_only=True)
            dpg.draw_rectangle(
                (0, 0), (700, 220), fill=(16, 20, 28), color=(45, 60, 90), thickness=1, parent='vclock_canvas'
            )

            if 'Event Log' in view_mode:
                # Process horizontal lanes
                proc_y = {'P0': 50, 'P1': 110, 'P2': 170}
                for proc, y in proc_y.items():
                    dpg.draw_line((60, y), (660, y), color=(60, 75, 100), thickness=2, parent='vclock_canvas')
                    dpg.draw_text((15, y - 8), proc, color=(150, 200, 255), size=14, parent='vclock_canvas')

                # Event positions x along timeline
                event_x = {
                    'e0_1': 100,
                    'e0_2': 180,
                    'e1_1': 140,
                    'e1_2': 280,
                    'e2_1': 220,
                    'e1_3': 380,
                    'e2_2': 480,
                }

                # Draw Message Transmission Arrows
                # M1: e0_2 (180, 50) -> e1_2 (280, 110)
                dpg.draw_line(
                    (event_x['e0_2'], proc_y['P0']),
                    (event_x['e1_2'], proc_y['P1']),
                    color=(255, 200, 100, 180),
                    thickness=2,
                    parent='vclock_canvas',
                )
                dpg.draw_text((200, 70), 'Msg M1 (P0->P1)', color=(255, 220, 120), size=11, parent='vclock_canvas')

                # M2: e1_3 (380, 110) -> e2_2 (480, 170)
                dpg.draw_line(
                    (event_x['e1_3'], proc_y['P1']),
                    (event_x['e2_2'], proc_y['P2']),
                    color=(100, 255, 200, 180),
                    thickness=2,
                    parent='vclock_canvas',
                )
                dpg.draw_text((400, 130), 'Msg M2 (P1->P2)', color=(120, 255, 220), size=11, parent='vclock_canvas')

                # Draw Event Nodes
                for e_id, info in trace.items():
                    px = event_x.get(e_id, 300)
                    py = proc_y.get(info['process'], 110)
                    color_node = (
                        (100, 220, 255)
                        if info['type'] == 'LOCAL'
                        else (255, 180, 100)
                        if info['type'] == 'SEND'
                        else (100, 255, 150)
                    )
                    dpg.draw_circle(
                        (px, py), 8, color=(255, 255, 255), fill=color_node, thickness=1, parent='vclock_canvas'
                    )
                    v_compact = ','.join(str(info['vector_clock'].get(p, 0)) for p in ['P0', 'P1', 'P2'])
                    dpg.draw_text((px - 12, py - 24), e_id, color=(220, 230, 255), size=12, parent='vclock_canvas')
                    dpg.draw_text(
                        (px - 18, py + 12),
                        f'V=<{v_compact}>',
                        color=(180, 200, 220),
                        size=10,
                        parent='vclock_canvas',
                    )

            elif 'Causality Matrix' in view_mode:
                # Draw 7x7 Graphical Causality Grid
                event_keys = list(trace.keys())
                causal_mat = compute_causality_matrix(trace)
                cell_size = 24
                start_x, start_y = 90, 30

                # Column headers
                for j, ej in enumerate(event_keys):
                    dpg.draw_text(
                        (start_x + j * cell_size + 4, start_y - 18),
                        ej[1:],
                        color=(200, 220, 255),
                        size=11,
                        parent='vclock_canvas',
                    )

                # Grid cells
                for i, ei in enumerate(event_keys):
                    dpg.draw_text(
                        (start_x - 35, start_y + i * cell_size + 4),
                        ei,
                        color=(200, 220, 255),
                        size=11,
                        parent='vclock_canvas',
                    )
                    for j, ej in enumerate(event_keys):
                        rel = causal_mat[ei][ej]
                        if rel == 'precedes':
                            fill_c = (40, 160, 80)
                            sym = '->'
                        elif rel == 'succeeds':
                            fill_c = (40, 80, 180)
                            sym = '<-'
                        elif rel == 'concurrent':
                            fill_c = (180, 50, 160)
                            sym = '||'
                        else:
                            fill_c = (50, 50, 60)
                            sym = '='

                        cx = start_x + j * cell_size
                        cy = start_y + i * cell_size
                        dpg.draw_rectangle(
                            (cx, cy),
                            (cx + cell_size - 2, cy + cell_size - 2),
                            fill=fill_c,
                            color=(80, 90, 120),
                            parent='vclock_canvas',
                        )
                        dpg.draw_text((cx + 5, cy + 3), sym, color=(255, 255, 255), size=11, parent='vclock_canvas')

                # Legend on right side
                dpg.draw_text(
                    (310, 25),
                    'Causality Partial Order (Happened-Before):',
                    color=(150, 200, 255),
                    size=13,
                    parent='vclock_canvas',
                )
                dpg.draw_rectangle((310, 55), (325, 70), fill=(40, 160, 80), parent='vclock_canvas')
                dpg.draw_text(
                    (335, 55), 'Precedes (a -> b)  [c1 < c2]', color=(100, 255, 150), size=12, parent='vclock_canvas'
                )

                dpg.draw_rectangle((310, 85), (325, 100), fill=(40, 80, 180), parent='vclock_canvas')
                dpg.draw_text(
                    (335, 85), 'Succeeds (b -> a)  [c1 > c2]', color=(100, 180, 255), size=12, parent='vclock_canvas'
                )

                dpg.draw_rectangle((310, 115), (325, 130), fill=(180, 50, 160), parent='vclock_canvas')
                dpg.draw_text(
                    (335, 115),
                    'Concurrent (a || b) [Incomparable]',
                    color=(255, 120, 240),
                    size=12,
                    parent='vclock_canvas',
                )

                dpg.draw_rectangle((310, 145), (325, 160), fill=(50, 50, 60), parent='vclock_canvas')
                dpg.draw_text(
                    (335, 145),
                    'Identity (a == b)  [Identical event]',
                    color=(180, 180, 180),
                    size=12,
                    parent='vclock_canvas',
                )

            else:
                # Mode 3: CRDT Join-Semilattice Supremum Tree
                rep_a = {'node_1': 4, 'node_2': 2, 'node_3': 0}
                rep_b = {'node_1': 1, 'node_2': 5, 'node_3': 3}
                merged, _ = synchronize_crdt_replicas(rep_a, rep_b)

                # Replica Alpha Box (Top Left)
                dpg.draw_rectangle(
                    (40, 25), (250, 95), fill=(20, 35, 55), color=(60, 140, 220), thickness=2, parent='vclock_canvas'
                )
                dpg.draw_text(
                    (50, 30), 'Replica Alpha (Divergent)', color=(100, 200, 255), size=12, parent='vclock_canvas'
                )
                dpg.draw_text(
                    (50, 50), 'State: <n1:4, n2:2, n3:0>', color=(200, 230, 255), size=12, parent='vclock_canvas'
                )
                # Component bars
                dpg.draw_line((50, 75), (50 + 4 * 18, 75), color=(100, 200, 255), thickness=6, parent='vclock_canvas')
                dpg.draw_line((50, 85), (50 + 2 * 18, 85), color=(100, 200, 255), thickness=6, parent='vclock_canvas')

                # Replica Beta Box (Bottom Left)
                dpg.draw_rectangle(
                    (40, 120), (250, 190), fill=(45, 30, 20), color=(220, 140, 60), thickness=2, parent='vclock_canvas'
                )
                dpg.draw_text(
                    (50, 125), 'Replica Beta (Divergent)', color=(255, 180, 100), size=12, parent='vclock_canvas'
                )
                dpg.draw_text(
                    (50, 145), 'State: <n1:1, n2:5, n3:3>', color=(255, 220, 180), size=12, parent='vclock_canvas'
                )
                # Component bars
                dpg.draw_line((50, 168), (50 + 1 * 18, 168), color=(255, 180, 100), thickness=5, parent='vclock_canvas')
                dpg.draw_line((50, 176), (50 + 5 * 18, 176), color=(255, 180, 100), thickness=5, parent='vclock_canvas')
                dpg.draw_line((50, 184), (50 + 3 * 18, 184), color=(255, 180, 100), thickness=5, parent='vclock_canvas')

                # Merge Convergence Arrows
                dpg.draw_line((250, 60), (390, 100), color=(255, 255, 150), thickness=2, parent='vclock_canvas')
                dpg.draw_line((250, 155), (390, 115), color=(255, 255, 150), thickness=2, parent='vclock_canvas')
                dpg.draw_text((275, 95), 'Join ∨ (LUB)', color=(255, 255, 150), size=12, parent='vclock_canvas')

                # Merged State Box (Right)
                dpg.draw_rectangle(
                    (390, 45), (660, 170), fill=(20, 45, 30), color=(60, 220, 120), thickness=2, parent='vclock_canvas'
                )
                dpg.draw_text(
                    (405, 55),
                    'CRDT Lattice Supremum (Merged)',
                    color=(100, 255, 150),
                    size=13,
                    parent='vclock_canvas',
                )
                dpg.draw_text(
                    (405, 80),
                    'V_merged = <n1:4, n2:5, n3:3>',
                    color=(220, 255, 220),
                    size=13,
                    parent='vclock_canvas',
                )
                dpg.draw_text(
                    (405, 105),
                    'Resolved via component-wise max',
                    color=(160, 220, 180),
                    size=11,
                    parent='vclock_canvas',
                )

                # Component bars for merged
                dpg.draw_line(
                    (405, 130), (405 + 4 * 18, 130), color=(100, 255, 150), thickness=5, parent='vclock_canvas'
                )
                dpg.draw_line(
                    (405, 142), (405 + 5 * 18, 142), color=(100, 255, 150), thickness=5, parent='vclock_canvas'
                )
                dpg.draw_line(
                    (405, 154), (405 + 3 * 18, 154), color=(100, 255, 150), thickness=5, parent='vclock_canvas'
                )

        table_data: dict[int | str, dict[str, str]] = {}
        if 'Event Log' in view_mode:
            for idx, (e_id, info) in enumerate(trace.items()):
                v_str = ', '.join(f'{p}:{info["vector_clock"].get(p, 0)}' for p in ['P0', 'P1', 'P2'])
                table_data[idx] = {
                    'Event ID': e_id,
                    'Process': info['process'],
                    'Type': info['type'],
                    'Lamport Clock (L)': str(info['scalar_clock']),
                    'Vector Clock (V)': f'<{v_str}>',
                    'Description': info['desc'],
                }
            dpg.set_value(
                'vclock_status', 'Simulated asynchronous multi-process message trace with Vector Clock joins!'
            )
        elif 'Causality Matrix' in view_mode:
            causal_mat = compute_causality_matrix(trace)
            for idx, e1 in enumerate(trace):
                row_dict = {'Event': e1}
                for e2 in trace:
                    row_dict[e2] = causal_mat[e1][e2]
                table_data[idx] = row_dict
            dpg.set_value(
                'vclock_status', 'Computed pairwise causal precedence (precedes, succeeds, concurrent) matrix!'
            )
        else:
            rep_a = {'node_1': 4, 'node_2': 2, 'node_3': 0}
            rep_b = {'node_1': 1, 'node_2': 5, 'node_3': 3}
            merged, rel = synchronize_crdt_replicas(rep_a, rep_b)
            table_data = {
                0: {
                    'Replica State': 'Replica Alpha (Local)',
                    'node_1': '4',
                    'node_2': '2',
                    'node_3': '0',
                    'Causal Relation': rel,
                },
                1: {
                    'Replica State': 'Replica Beta (Remote)',
                    'node_1': '1',
                    'node_2': '5',
                    'node_3': '3',
                    'Causal Relation': rel,
                },
                2: {
                    'Replica State': 'Lattice Join (Supremum)',
                    'node_1': str(merged['node_1']),
                    'node_2': str(merged['node_2']),
                    'node_3': str(merged['node_3']),
                    'Causal Relation': 'Merged Convergence',
                },
            }
            dpg.set_value('vclock_status', 'Synchronized divergent CRDT replicas via Join-Semilattice supremum!')

        display_matrix_in_table(table_data, 'table_vclock_res')
    except Exception as e:
        dpg.set_value('vclock_status', f'Error: {e}')


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
            semiring: ax.semiring.Semiring[float] = ax.semiring.ArcticSemiring()
        elif 'Tropical' in semiring_name:
            semiring = ax.semiring.TropicalSemiring()
        else:
            semiring = ax.semiring.StandardSemiring()

        def add_2d(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
            return (p1[0] + p2[0], p1[1] + p2[1])

        convolved_2d = ax.transforms.convolve(image_2d, kernel_2d, key_op=add_2d, semiring=semiring)

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

    current_curvatures = ax.analysis.forman_ricci_curvature(graph, augmented=is_augmented)

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
            dpg.add_text('Select ax.semiring.Semiring:')
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
                    'BivariateVariance',
                    'Digital',
                    'Modular',
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
        dpg.add_text('Simulation of Diffie-Hellman key exchange over the DigitalSemiring.', color=(180, 180, 180))
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
            dpg.add_text('ax.semiring.Semiring:')
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
            dpg.add_text('ax.semiring.Semiring:')
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


def build_view_extreme_risk_tail_moments() -> None:
    with dpg.group(tag='view_extreme_risk_tail_moments_group', show=False):
        dpg.add_text(
            'Extreme Tail Risk, Higher-Order Moments (Kurtosis, Hyperskewness) & Covariance Tensors',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        dpg.add_text('1. Comparative Tail Risk Audit (Gaussian vs Black-Swan Jump Risk):')
        create_bordered_table(
            tag='table_tail_risk_comparison',
            columns=[
                'Execution Route',
                'Mean (μ)',
                'Variance (σ²)',
                'Skewness (γ1)',
                'Kurtosis (β2)',
                'Risk Profile',
            ],
            width=850,
        )
        dpg.add_spacer(height=5)
        dpg.add_text('2. Multi-Hop Cascading Shock Propagation (Order 5 Hyperskewness):')
        dpg.add_input_text(
            default_value='Press "Evaluate Extreme Moments & Covariance" to compute 3-hop cascade...',
            readonly=True,
            tag='tail_moment5_summary',
            width=850,
        )
        dpg.add_spacer(height=5)
        dpg.add_text('3. Multi-Objective Joint Risk Covariance Matrix Σ (Cost vs Latency):')
        create_bordered_table(
            tag='table_joint_cov_res',
            columns=['Feature', 'Feature 1: Cost ($)', 'Feature 2: Latency (ms)'],
            width=700,
        )
        dpg.add_input_text(
            default_value='Cross-feature correlation metrics will appear here...',
            readonly=True,
            tag='joint_cov_summary',
            width=850,
        )
        dpg.add_spacer(height=10)
        dpg.add_button(label='Evaluate Extreme Moments & Covariance', callback=run_extreme_tail_risk)
        dpg.add_text('', tag='tail_risk_status', color=(255, 200, 100))


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
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('TOPOLOGY PRESETS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=[
                        '1D Circle (S^1)',
                        'Solid Triangle (2-Simplex)',
                        'Double Loop (Figure 8)',
                        '3D Solid Tetrahedron',
                        'Hollow Sphere Boundary',
                    ],
                    default_value='1D Circle (S^1)',
                    tag='homology_preset',
                    width=250,
                    callback=lambda: run_topological_homology(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(label='Evaluate Simplicial Homology', callback=run_topological_homology, width=250)
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='homology_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('2D Simplicial Mesh Visualization Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=360, tag='homology_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('Betti Numbers Barcode Invariants (Selectable cells):')
                with dpg.group(tag='table_homology_res_container'):
                    pass


def build_view_clifford_geometric_algebra() -> None:
    with dpg.group(tag='view_clifford_geometric_algebra_group', show=False):
        dpg.add_text(
            'Clifford Geometric Algebra Cl(3,0), Multivector Products & 3D Rotor Rotations',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('MULTIVECTOR & ROTOR INPUTS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_input_float(
                    default_value=3.0,
                    tag='clifford_v_e1',
                    label='e1 Vector Component',
                    width=120,
                    callback=lambda: run_clifford_geometric_algebra(),
                )
                dpg.add_input_float(
                    default_value=4.0,
                    tag='clifford_v_e2',
                    label='e2 Vector Component',
                    width=120,
                    callback=lambda: run_clifford_geometric_algebra(),
                )
                dpg.add_spacer(height=10)
                dpg.add_text('BIVECTOR PLANE & ROTATION', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=['e12 Plane (XY)', 'e23 Plane (YZ)', 'e31 Plane (ZX)'],
                    default_value='e12 Plane (XY)',
                    tag='clifford_plane',
                    width=180,
                    callback=lambda: run_clifford_geometric_algebra(),
                )
                dpg.add_slider_float(
                    default_value=90.0,
                    min_value=0.0,
                    max_value=360.0,
                    tag='clifford_angle',
                    label='Angle (Deg)',
                    width=180,
                    callback=lambda: run_clifford_geometric_algebra(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(label='Apply Rotor R v R^dagger', callback=run_clifford_geometric_algebra, width=250)
                dpg.add_spacer(height=10)
                dpg.add_text('Multivector Magnitude Squared:', color=(180, 180, 180))
                dpg.add_text('v^2 = 25.000', tag='clifford_v_sq_text', color=(100, 255, 100))
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='clifford_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('2D Vector & Rotor Rotation Sweep Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=360, tag='clifford_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('3D Rotor Transformation Multivector Breakdown (Selectable cells):')
                with dpg.group(tag='table_clifford_res_container'):
                    pass


def build_view_galois_finite_fields() -> None:
    with dpg.group(tag='view_galois_finite_fields_group', show=False):
        dpg.add_text(
            'Galois Finite Field GF(2^8) & AES Cryptographic MixColumns Matrix Arithmetic',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('GF(2^8) FIELD ELEMENT INPUTS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_input_text(
                    default_value='0x57',
                    tag='galois_byte1',
                    label='Byte A (Hex)',
                    width=120,
                    callback=lambda: run_galois_finite_fields(),
                )
                dpg.add_input_text(
                    default_value='0x83',
                    tag='galois_byte2',
                    label='Byte B (Hex)',
                    width=120,
                    callback=lambda: run_galois_finite_fields(),
                )
                dpg.add_spacer(height=10)
                dpg.add_text('AES IRREDUCIBLE POLYNOMIAL', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_text('P(x) = x^8 + x^4 + x^3 + x + 1 (0x11B)', color=(180, 220, 255))
                dpg.add_spacer(height=10)
                dpg.add_button(
                    label='Multiply Field Elements & MixColumns', callback=run_galois_finite_fields, width=250
                )
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='galois_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('AES 4x4 State Byte Heatmap Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=220, tag='galois_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('GF(2^8) Product Output:', color=(180, 180, 180))
                dpg.add_text('0x57 * 0x83 = 0xC1', tag='galois_poly_res_text', color=(100, 255, 100))
                dpg.add_spacer(height=5)
                dpg.add_text('AES MixColumns Output Matrix State (Selectable cells):')
                with dpg.group(tag='table_galois_res_container'):
                    pass


def build_view_categorical_kleisli() -> None:
    with dpg.group(tag='view_categorical_kleisli_group', show=False):
        dpg.add_text(
            'Categorical Morphisms, Kleisli Monadic Composition (g o_T f) & Kan Extensions',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('CATEGORY TOPOLOGY PRESET', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=['Pipeline (A -> B -> C)', 'Multi-Path Diamond (A -> B,C -> D)'],
                    default_value='Pipeline (A -> B -> C)',
                    tag='kleisli_topology',
                    width=250,
                    callback=lambda: run_categorical_kleisli(),
                )
                dpg.add_spacer(height=10)
                dpg.add_text('MORPHISM WEIGHT INPUTS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_slider_float(
                    default_value=0.8,
                    min_value=0.1,
                    max_value=2.0,
                    tag='kleisli_w_ab',
                    label='f(A->B) Weight',
                    width=180,
                    callback=lambda: run_categorical_kleisli(),
                )
                dpg.add_slider_float(
                    default_value=0.9,
                    min_value=0.1,
                    max_value=2.0,
                    tag='kleisli_w_bc',
                    label='g(B->C) Weight',
                    width=180,
                    callback=lambda: run_categorical_kleisli(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(
                    label='Compose Morphisms Across Monad Semirings', callback=run_categorical_kleisli, width=250
                )
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='kleisli_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('Category Graph Diagram Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=220, tag='kleisli_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('Comparative Kleisli Compositions (g o_T f) Across Monads (Selectable cells):')
                with dpg.group(tag='table_kleisli_res_container'):
                    pass


def build_view_forward_mode_autodiff() -> None:
    with dpg.group(tag='view_forward_mode_autodiff_group', show=False):
        dpg.add_text(
            'Forward-Mode Automatic Differentiation via Dual Numbers (R[ε]/(ε^2)) & Semiring Polymorphism',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('SCALAR AUTODIFF INPUTS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=[
                        'g(x) = ln(x)*sqrt(x) + sin(x)',
                        'sigmoid(x)',
                        'exp(x) / (1 + exp(x))',
                        'x^3 - 4x + cos(x)',
                    ],
                    default_value='g(x) = ln(x)*sqrt(x) + sin(x)',
                    tag='ad_fn_select',
                    width=250,
                    callback=lambda: run_forward_mode_autodiff(),
                )
                dpg.add_input_float(
                    default_value=2.0,
                    tag='ad_input_x',
                    label='Primal Seed x',
                    width=120,
                    callback=lambda: run_forward_mode_autodiff(),
                )
                dpg.add_spacer(height=10)
                dpg.add_text('GRAPH TRANSMISSION PARAMETERS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_input_float(
                    default_value=2.0,
                    tag='ad_edge_x',
                    label='Edge (0->1) x',
                    width=120,
                    callback=lambda: run_forward_mode_autodiff(),
                )
                dpg.add_input_float(
                    default_value=3.0,
                    tag='ad_edge_y',
                    label='Edge (1->2) y',
                    width=120,
                    callback=lambda: run_forward_mode_autodiff(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(label='Evaluate Forward Autodiff', callback=run_forward_mode_autodiff, width=250)
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='ad_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('Network Transmission Sensitivity Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=200, tag='ad_canvas'):
                    pass
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text('Evaluated Primal Value f(x):')
                        dpg.add_input_text(default_value='0.000000', readonly=True, tag='ad_primal_res', width=200)
                    with dpg.group():
                        dpg.add_text('Exact Analytical Derivative df/dx:')
                        dpg.add_input_text(default_value='0.000000', readonly=True, tag='ad_tangent_res', width=200)
                dpg.add_spacer(height=5)
                dpg.add_text('Forward Differentiation Breakdown (Selectable cells):')
                with dpg.group(tag='table_ad_res_container'):
                    pass


def build_view_sparse_neural_backprop() -> None:
    with dpg.group(tag='view_sparse_neural_backprop_group', show=False):
        dpg.add_text(
            'Reverse-Mode Backpropagation via Transposed Matrix Multiplication (W^T * z_bar)',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('TRAINING DATASET & ARCHITECTURE', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=['XOR (Non-Linear)', 'OR Gate', 'AND Gate'],
                    default_value='XOR (Non-Linear)',
                    tag='backprop_dataset',
                    width=250,
                    callback=lambda: run_sparse_neural_backprop(),
                )
                dpg.add_input_int(
                    default_value=4,
                    min_value=2,
                    max_value=16,
                    tag='backprop_hidden',
                    label='Hidden Units',
                    width=120,
                    callback=lambda: run_sparse_neural_backprop(),
                )
                dpg.add_input_float(
                    default_value=2.0,
                    tag='backprop_lr',
                    label='Learning Rate',
                    width=120,
                )
                dpg.add_input_int(
                    default_value=1000,
                    min_value=100,
                    max_value=5000,
                    tag='backprop_epochs',
                    label='Epochs',
                    width=120,
                )
                dpg.add_spacer(height=10)
                dpg.add_button(label='Train Sparse MLP with Backprop', callback=run_sparse_neural_backprop, width=250)
                dpg.add_spacer(height=10)
                dpg.add_input_text(
                    default_value='Final MSE Loss: Not Run', readonly=True, tag='backprop_loss_text', width=280
                )
                dpg.add_spacer(height=5)
                dpg.add_text('', tag='backprop_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('Neural Architecture & Adjoint Pullback Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=220, tag='backprop_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('Model Predictions & Classification Convergence (Selectable cells):')
                with dpg.group(tag='table_backprop_res_container'):
                    pass


def build_view_functional_autograd_engine() -> None:
    with dpg.group(tag='view_functional_autograd_engine_group', show=False):
        dpg.add_text(
            'Functional Reverse-Mode Autograd Engine (Dynamic DAG & Vector-Jacobian Products)',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('COMPUTATION GRAPH EXPRESSION', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=[
                        'f(x,y) = (x^2*y + sin(x)) / (y + exp(x))',
                        'Loss = (w1*x1 + w2*x2)^2 + tanh(y)',
                        'g(x,y,z) = x*y*z + exp(x*z) + ln(y)',
                    ],
                    default_value='f(x,y) = (x^2*y + sin(x)) / (y + exp(x))',
                    tag='autograd_expr',
                    width=250,
                    callback=lambda: run_functional_autograd_engine(),
                )
                dpg.add_spacer(height=5)
                dpg.add_input_float(
                    default_value=1.5,
                    tag='autograd_var_x',
                    label='Variable x',
                    width=120,
                    callback=lambda: run_functional_autograd_engine(),
                )
                dpg.add_input_float(
                    default_value=2.0,
                    tag='autograd_var_y',
                    label='Variable y',
                    width=120,
                    callback=lambda: run_functional_autograd_engine(),
                )
                dpg.add_input_float(
                    default_value=1.0,
                    tag='autograd_var_z',
                    label='Variable z',
                    width=120,
                    callback=lambda: run_functional_autograd_engine(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(
                    label='Execute Reverse Autograd (VJPs)', callback=run_functional_autograd_engine, width=250
                )
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='autograd_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('Computation Graph DAG & Reverse Adjoint Flow Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=220, tag='autograd_canvas'):
                    pass
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text('Output Value:')
                        dpg.add_input_text(default_value='0.000000', readonly=True, tag='autograd_f_val', width=180)
                    with dpg.group():
                        dpg.add_text('Gradient df/dx:')
                        dpg.add_input_text(default_value='0.000000', readonly=True, tag='autograd_grad_x', width=180)
                    with dpg.group():
                        dpg.add_text('Gradient df/dy:')
                        dpg.add_input_text(default_value='0.000000', readonly=True, tag='autograd_grad_y', width=180)
                dpg.add_spacer(height=5)
                dpg.add_text('DAG Nodes Forward Values & Backward Adjoints (Selectable cells):')
                with dpg.group(tag='table_autograd_res_container'):
                    pass


def build_view_quantum_feynman_path_integral() -> None:
    with dpg.group(tag='view_quantum_feynman_path_integral_group', show=False):
        dpg.add_text(
            'Discrete Feynman Path Integrals, Complex Probability Amplitude Semirings & Wave Interference',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('QUANTUM EXPERIMENT SETUP', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=['Double-Slit Diffraction', 'Aharonov-Bohm Gauge Phase Shift'],
                    default_value='Double-Slit Diffraction',
                    tag='quantum_exp_type',
                    width=250,
                    callback=lambda: run_quantum_feynman_path_integral(),
                )
                dpg.add_spacer(height=10)
                dpg.add_text('PATH ACTION & GEOMETRY', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_slider_float(
                    default_value=2.0,
                    min_value=0.5,
                    max_value=6.0,
                    tag='quantum_slit_sep',
                    label='Slit Sep (d)',
                    width=180,
                    callback=lambda: run_quantum_feynman_path_integral(),
                )
                dpg.add_slider_float(
                    default_value=1.0,
                    min_value=0.2,
                    max_value=3.0,
                    tag='quantum_wavelength',
                    label='Wavelength (λ)',
                    width=180,
                    callback=lambda: run_quantum_feynman_path_integral(),
                )
                dpg.add_slider_float(
                    default_value=0.0,
                    min_value=0.0,
                    max_value=3.14159,
                    tag='quantum_flux',
                    label='Magnetic Flux (Φ)',
                    width=180,
                    callback=lambda: run_quantum_feynman_path_integral(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(
                    label='Sum Path Integrals K = Σ exp(iS/ħ)', callback=run_quantum_feynman_path_integral, width=250
                )
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='quantum_path_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('Quantum Superposition Interference & Detector Screen Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=220, tag='quantum_path_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('Feynman Path Summation & Born Rule Probabilities (Selectable cells):')
                with dpg.group(tag='table_quantum_path_res_container'):
                    pass


def build_view_relativistic_dirac_spinor() -> None:
    with dpg.group(tag='view_relativistic_dirac_spinor_group', show=False):
        dpg.add_text(
            'Relativistic Dirac Spinors, Clifford Spacetime Algebra Cl(1,3) & Conserved 4-Currents',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('LORENTZ & ROTOR TRANSFORM', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=['Spatial Rotation (x-y plane)', 'Lorentz Boost (x-axis)'],
                    default_value='Spatial Rotation (x-y plane)',
                    tag='dirac_transform_type',
                    width=250,
                    callback=lambda: run_relativistic_dirac_spinor(),
                )
                dpg.add_spacer(height=10)
                dpg.add_text('TRANSFORMATION PARAMETERS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_slider_float(
                    default_value=180.0,
                    min_value=0.0,
                    max_value=720.0,
                    tag='dirac_angle_deg',
                    label='Angle (Deg, up to 4π)',
                    width=180,
                    callback=lambda: run_relativistic_dirac_spinor(),
                )
                dpg.add_slider_float(
                    default_value=0.8,
                    min_value=0.0,
                    max_value=3.0,
                    tag='dirac_rapidity',
                    label='Boost Rapidity (ξ)',
                    width=180,
                    callback=lambda: run_relativistic_dirac_spinor(),
                )
                dpg.add_spacer(height=10)
                dpg.add_text('SPINOR INITIAL COMPONENTS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_input_float(
                    default_value=1.0,
                    tag='dirac_scalar',
                    label='Scalar α',
                    width=120,
                    callback=lambda: run_relativistic_dirac_spinor(),
                )
                dpg.add_input_float(
                    default_value=0.5,
                    tag='dirac_spin_12',
                    label='Bivector B_12',
                    width=120,
                    callback=lambda: run_relativistic_dirac_spinor(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(label="Apply Rotor ψ' = R ψ R^†", callback=run_relativistic_dirac_spinor, width=250)
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='dirac_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text(
                    'Dirac Spin-1/2 4π Orientation & Conserved Current J^μ Flow Canvas:', color=(180, 180, 180)
                )
                with dpg.drawlist(width=700, height=220, tag='dirac_spinor_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('Multivector Components & Probability Current Density (Selectable cells):')
                with dpg.group(tag='table_dirac_res_container'):
                    pass


def build_view_distributed_vector_clocks() -> None:
    with dpg.group(tag='view_distributed_vector_clocks_group', show=False):
        dpg.add_text(
            'Distributed Causal Ordering, Lamport Clocks & Vector Clock Join-Semilattices',
            color=(150, 180, 255),
        )
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.child_window(width=310, height=520, border=True):
                dpg.add_text('DISTRIBUTED TRACE CONFIG', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_combo(
                    items=['Event Log & Vector Clocks', 'Causality Matrix (Partial Order)', 'CRDT Replica Sync'],
                    default_value='Event Log & Vector Clocks',
                    tag='vclock_view_mode',
                    width=250,
                    callback=lambda: run_distributed_vector_clocks(),
                )
                dpg.add_spacer(height=10)
                dpg.add_button(
                    label='Simulate Cluster & Sync (∨)',
                    callback=run_distributed_vector_clocks,
                    width=250,
                )
                dpg.add_spacer(height=10)
                dpg.add_text('', tag='vclock_status', color=(255, 200, 100), wrap=290)

            with dpg.group():
                dpg.add_text('Distributed Multi-Process Timeline & Causal Message Flow Canvas:', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=220, tag='vclock_canvas'):
                    pass
                dpg.add_spacer(height=5)
                dpg.add_text('Logical Timestamps, Causality Partial Order & Lattice Joins:')
                with dpg.group(tag='table_vclock_res_container'):
                    pass


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
    'extreme_risk_tail_moments',
    'sheaf_cohomology',
    'gaussian_splatting',
    'topological_homology',
    'clifford_geometric_algebra',
    'galois_finite_fields',
    'categorical_kleisli',
    'forward_mode_autodiff',
    'sparse_neural_backprop',
    'functional_autograd_engine',
    'quantum_feynman_path_integral',
    'relativistic_dirac_spinor',
    'distributed_vector_clocks',
]


def change_view(sender: int | str, app_data: Any, user_data: str) -> None:
    selected_view: str = user_data
    for v in VIEWS:
        sel_tag = f'sel_{v}'
        view_tag = f'view_{v}_group'
        if dpg.does_item_exist(sel_tag):
            dpg.set_value(sel_tag, (v == selected_view))
        if dpg.does_item_exist(view_tag):
            if v == selected_view:
                dpg.show_item(view_tag)
            else:
                dpg.hide_item(view_tag)


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
            dpg.add_selectable(
                label='Extreme Tail Risk & Moments',
                tag='sel_extreme_risk_tail_moments',
                callback=change_view,
                user_data='extreme_risk_tail_moments',
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

        with dpg.tree_node(label='Information, Distributed & Crypto', default_open=True):
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
            dpg.add_selectable(
                label='Distributed Vector Clocks',
                tag='sel_distributed_vector_clocks',
                callback=change_view,
                user_data='distributed_vector_clocks',
            )

        with dpg.tree_node(label='Automatic Differentiation & Backprop', default_open=True):
            dpg.add_selectable(
                label='Forward-Mode Autodiff',
                tag='sel_forward_mode_autodiff',
                callback=change_view,
                user_data='forward_mode_autodiff',
            )
            dpg.add_selectable(
                label='Sparse Neural Backprop',
                tag='sel_sparse_neural_backprop',
                callback=change_view,
                user_data='sparse_neural_backprop',
            )
            dpg.add_selectable(
                label='Functional Autograd Engine',
                tag='sel_functional_autograd_engine',
                callback=change_view,
                user_data='functional_autograd_engine',
            )

        with dpg.tree_node(label='Quantum & Spacetime Mechanics', default_open=True):
            dpg.add_selectable(
                label='Quantum Path Integrals',
                tag='sel_quantum_feynman_path_integral',
                callback=change_view,
                user_data='quantum_feynman_path_integral',
            )
            dpg.add_selectable(
                label='Relativistic Dirac Spinors',
                tag='sel_relativistic_dirac_spinor',
                callback=change_view,
                user_data='relativistic_dirac_spinor',
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
                build_view_extreme_risk_tail_moments()
                build_view_sheaf_cohomology()
                build_view_gaussian_splatting()
                build_view_topological_homology()
                build_view_clifford_geometric_algebra()
                build_view_galois_finite_fields()
                build_view_categorical_kleisli()
                build_view_forward_mode_autodiff()
                build_view_sparse_neural_backprop()
                build_view_functional_autograd_engine()
                build_view_quantum_feynman_path_integral()
                build_view_relativistic_dirac_spinor()
                build_view_distributed_vector_clocks()

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
