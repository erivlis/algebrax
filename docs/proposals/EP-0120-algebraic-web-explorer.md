---
title: "EP-0120: The Algebraic Web Explorer & Interactive Visual Studio"
description: "A zero-dependency web-based interactive visual laboratory for semiring matrix powers, simplicial homology, Clifford GA rotors, and Kleisli monads."
icon: lucide/compass
status: draft
---

# EP-0120: The Algebraic Web Explorer & Interactive Visual Studio

| Field       | Value                                                  |
|:------------|:-------------------------------------------------------|
| **EP**      | 0120                                                   |
| **Title**   | The Algebraic Web Explorer & Interactive Visual Studio |
| **Author**  | Eran Rivlis & Antigravity                              |
| **Status**  | Draft                                                  |
| **Type**    | Feature / Visual Track                                 |
| **Created** | 2026-08-02                                             |
| **Updated** | 2026-08-02                                             |

---

## Abstract

This proposal specifies **The Algebraic Web Explorer** (`site/explorer/index.html`), a zero-dependency, browser-native
visual studio for `algebrax`. It complements the DearPyGui desktop lab (`recipes/lab.py`) with a lightweight web
interface for interactively inspecting:

1. **Semiring Matrix Operations**: Live matrix power propagation across Standard, Tropical, Boolean, Viterbi, and
   Provenance semirings.
2. **Simplicial Homology & Betti Barcodes**: Interactive 2D/3D mesh rendering, boundary
   nilpotency $D_{k-1} \circ D_k = \mathbf{0}$, and Betti number invariants $\beta_k$.
3. **Clifford Geometric Algebra**: Interactive 3D vector rotor rotations $v' = R v R^\dagger$ over $Cl (3,0)$
   multivectors.
4. **Galois Finite Fields**: AES $\text{GF} (2^8)$ polynomial modulo reductions and MixColumns matrix state heatmaps.
5. **Categorical Kleisli String Diagrams**: Monadic morphism compositions $g \circ_T f$ over category graphs.

---

## Architecture & Design

### Technology Stack

- **Structure**: Semantic HTML5 with dark-mode glassmorphism styling.
- **Logic**: Modern vanilla JavaScript (ES2024), modular, zero external framework overhead.
- **Graphics**: HTML5 Canvas 2D/3D rendering engines for real-time vector, graph, and mesh visualizations.

### Web Sitemap

```text
site/explorer/
├── index.html               (Main Web Explorer Layout & Tab Controller)
├── css/
│   └── explorer.css         (Theme Tokens, Dark Mode & Glassmorphism Utilities)
└── js/
    ├── core.js              (Pure JS Sparse Matrix & Semiring Arithmetic Engine)
    ├── homology.js          (Simplicial Mesh & Betti Barcode Renderer)
    ├── clifford.js          (Clifford Multivector & 3D Rotor Visualizer)
    ├── galois.js            (GF(2^8) Polynomial & AES MixColumns Heatmap)
    └── kleisli.js           (Category Graph & Monad Composition Diagrammer)
```

---

## The Council Heuristic & Falsifiable Invariants

1. **Aesthetic Excellence (The Physicist)**: Modern typography, vibrant dark-mode color palettes (HSL tailored), smooth
   micro-animations, and interactive hover tooltips.
2. **Mathematical Accuracy (The Council)**: Identical numerical results to `algebrax` Python core, verified via
   automated browser tests.
3. **Zero Magic / No Bloat (Dennis)**: Pure Vanilla JS and CSS without heavy framework dependencies (React, Vue, or
   Tailwind build steps).

---

## Implementation Roadmap

- [ ] **Phase 1**: Core HTML5/CSS Glassmorphism Shell (`site/explorer/index.html` & `explorer.css`).
- [ ] **Phase 2**: Pure JS Semiring Matrix Engine (`js/core.js`).
- [ ] **Phase 3**: Simplicial Homology & Betti Barcode Renderer (`js/homology.js`).
- [ ] **Phase 4**: Clifford Rotor Visualizer & Galois MixColumns Heatmap (`js/clifford.js` & `js/galois.js`).
- [ ] **Phase 5**: Categorical Kleisli Monad Diagrammer (`js/kleisli.js`).
