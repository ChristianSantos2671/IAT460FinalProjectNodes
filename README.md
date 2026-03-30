# ComfyUI Aperiodic Soundproofing Panel Generator Nodes

## Overview

ComfyUI-AperiodicTiles is a custom node pack for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that generates **aperiodic hat-tile (Einstein tile) patterns** and turns them into production-ready 3-D assets.

Starting from a single set of parameters, the pipeline:

1. Generates a mathematically aperiodic tiling using the "hat" monotile (Smith et al., 2023).
2. Renders the 2-D layout as an interactive HTML viewer.
3. Extrudes each tile into a 3-D column whose height and surface tilt follow a procedural wave or noise pattern.
4. Renders the 3-D panel as a fully interactive HTML viewer.
5. Exports the columns as a binary **STL file** ready for 3-D printing or CNC machining.
6. Exports a **casting mould STL** — the geometric negative of the columns — into which liquid material (resin, silicone, concrete, plaster, …) can be poured to reproduce the panel as a cast.

## Features

- **Aperiodic hat-tile geometry** — uses a Z3 SAT solver to select a valid, gap-free non-repeating tiling on a hex lattice.
- **Procedural height mapping** — three modes (`radial_ripple`, `linear_ripple`, `noise`) drive column height and surface tilt.
- **Interactive 3-D preview** — Plotly-based HTML viewers open in any browser; fully rotatable, zoomable, and pannable.
- **Column STL export** — watertight solid with a flat base-plate and one tilted prism per tile.
- **Mould STL export** — solid rectangular block with per-tile cavities exactly matching the column geometry; flip upside down, pour, demould.
- **Uniform scale control** — all STL exporters accept a `scale` multiplier to convert canvas units to physical millimetres.

## Dependencies

| Package | Purpose |
|---|---|
| `numpy` | Array maths throughout |
| `z3-solver` | SAT solver for valid hat-tile selection |
| `plotly` | Interactive HTML 3-D/2-D viewers |
| `numpy-stl` | Binary STL file writing |

Install with:

```bash
pip install numpy z3-solver plotly numpy-stl
```

## Installation

1. Clone or copy this folder into your ComfyUI `custom_nodes/` directory:

   ```
   ComfyUI/
   └── custom_nodes/
       └── ComfyUI-AperiodicTiles/   ← this folder
           ├── __init__.py
           ├── nodes.py
           └── aperiodic_tiles/
   ```

2. Install dependencies (see above).

3. Start (or restart) ComfyUI. The seven nodes appear under the **Aperiodic Tiles** category in the node browser.

## Node Reference

### 1. Hat Tiling Generator

**Category:** Aperiodic Tiles  
**Output:** `HAT_DATA`

Generates the raw hat-tile geometry on a hex lattice using a Z3 SAT solver.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `width` | FLOAT | 1000 | Canvas width in pixels |
| `height` | FLOAT | 1000 | Canvas height in pixels |
| `tile_size` | FLOAT | 50 | Hex-lattice unit size in pixels. Larger = bigger, fewer tiles |

### 2. Fill Canvas (2D Layout)

**Category:** Aperiodic Tiles  
**Input:** `HAT_DATA`  
**Outputs:** `TILE_POLYGONS`, `RECT_BOUNDS`

Filters and scales the raw tiles to fill the canvas, applying an optional gap between tiles.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hat_data` | HAT_DATA | — | Output of Hat Tiling Generator |
| `gap` | FLOAT | 5.0 | Gap between adjacent tiles in pixels (0 = shared edges) |

### 3. Assign Tile Heights & Tilt

**Category:** Aperiodic Tiles  
**Input:** `TILE_POLYGONS`  
**Output:** `TILE_HEIGHT_DATA`

Adds a scalar extrusion height and a surface-tilt normal to every tile, driven by a procedural pattern.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tile_polygons` | TILE_POLYGONS | — | Output of Fill Canvas |
| `min_height` | FLOAT | 10.0 | Minimum column height (px / mm after scaling) |
| `max_height` | FLOAT | 50.0 | Maximum column height |
| `mode` | ENUM | `radial_ripple` | Height pattern: `radial_ripple`, `linear_ripple`, or `noise` |
| `frequency` | FLOAT | 0.05 | Spatial frequency of the wave/noise pattern |
| `tilt_strength` | FLOAT | 0.2 | How steeply the top face tilts (0 = flat top) |
| `angle` | FLOAT | 0.0 | Direction of travel for `linear_ripple` mode (degrees) |
| `seed` | INT | 0 | Random seed (reserved for future stochastic modes) |

### 4. Render 2D Canvas (HTML)

**Category:** Aperiodic Tiles  
**Input:** `TILE_POLYGONS`  
**Output:** `HTML_PATH` (also an output node — saves file)

Renders the flat 2-D tile layout as an interactive Plotly HTML file saved to the ComfyUI output directory (`aperiodic_canvas.html`).

### 5. Render 3D Panel (HTML)

**Category:** Aperiodic Tiles  
**Input:** `TILE_HEIGHT_DATA`  
**Output:** `HTML_PATH` (also an output node — saves file)

Renders the extruded 3-D panel as an interactive Plotly HTML file (`aperiodic_panel_3d.html`). The viewer is fully rotatable, zoomable, and pannable in any browser.

### 6. Export 3D Panel (STL)

**Category:** Aperiodic Tiles  
**Input:** `TILE_HEIGHT_DATA`  
**Output:** `STRING` (file path; also an output node — saves file)

Exports the column panel as a binary STL file. The solid consists of a flat rectangular base-plate plus one tilted prism per tile.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tile_height_data` | TILE_HEIGHT_DATA | — | Output of Assign Tile Heights & Tilt |
| `filename` | STRING | `aperiodic_tiling.stl` | Output filename (saved to ComfyUI output directory) |
| `base_thickness` | FLOAT | 10.0 | Thickness of the solid base-plate beneath all columns |
| `scale` | FLOAT | 1.0 | Uniform scale factor (e.g. 0.1 to convert 1 px → 0.1 mm) |

### 7. Export Casting Mould (STL)

**Category:** Aperiodic Tiles  
**Input:** `TILE_HEIGHT_DATA`  
**Output:** `STRING` (file path; also an output node — saves file)

Exports a casting mould as a binary STL file. The mould is a solid rectangular block with one cavity per tile column. Each cavity exactly replicates the shape of the corresponding column (including the tilted top surface).

When the mould is **flipped upside down** and filled with liquid material, the liquid fills the cavities (forming the columns) and covers the `base_thickness` layer (forming the solid connecting floor). After curing/hardening and demoulding, the result is a faithful cast of the original panel.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tile_height_data` | TILE_HEIGHT_DATA | — | Output of Assign Tile Heights & Tilt |
| `filename` | STRING | `aperiodic_mould.stl` | Output filename (saved to ComfyUI output directory) |
| `base_thickness` | FLOAT | 10.0 | Extra solid depth above the tallest column. Becomes the cast panel's floor when the mould is flipped and filled |
| `scale` | FLOAT | 1.0 | Uniform scale factor |

## Connecting the Nodes — Step-by-Step

Follow these steps in the ComfyUI graph editor to build the full pipeline.

### Step 1 — Add a Hat Tiling Generator node
Right-click the canvas → **Add Node → Aperiodic Tiles → Hat Tiling Generator**.  
Set `width`, `height`, and `tile_size` to your desired canvas size and tile resolution.

### Step 2 — Add a Fill Canvas node and connect it
Right-click → **Add Node → Aperiodic Tiles → Fill Canvas (2D Layout)**.  
Connect:
- `Hat Tiling Generator` → **`HAT_DATA` output** → `Fill Canvas` **`hat_data` input**

Adjust `gap` to control the visual spacing between tiles.

### Step 3 — (Optional) Preview the 2-D layout
Right-click → **Add Node → Aperiodic Tiles → Render 2D Canvas (HTML)**.  
Connect:
- `Fill Canvas` → **`TILE_POLYGONS` output** → `Render 2D Canvas` **`tile_polygons` input**

Queue the prompt. Open the saved `aperiodic_canvas.html` from the ComfyUI output folder in your browser.

### Step 4 — Add an Assign Tile Heights & Tilt node
Right-click → **Add Node → Aperiodic Tiles → Assign Tile Heights & Tilt**.  
Connect:
- `Fill Canvas` → **`TILE_POLYGONS` output** → `Assign Tile Heights & Tilt` **`tile_polygons` input**

Tune `min_height`, `max_height`, `mode`, `frequency`, and `tilt_strength` to shape the relief.

### Step 5 — (Optional) Preview the 3-D panel
Right-click → **Add Node → Aperiodic Tiles → Render 3D Panel (HTML)**.  
Connect:
- `Assign Tile Heights & Tilt` → **`TILE_HEIGHT_DATA` output** → `Render 3D Panel` **`tile_height_data` input**

Queue the prompt and open `aperiodic_panel_3d.html` in your browser to inspect the extruded geometry interactively.

### Step 6 — Export the column panel STL
Right-click → **Add Node → Aperiodic Tiles → Export 3D Panel (STL)**.  
Connect:
- `Assign Tile Heights & Tilt` → **`TILE_HEIGHT_DATA` output** → `Export 3D Panel` **`tile_height_data` input**

Set `filename`, `base_thickness` (floor thickness), and `scale` (unit → mm conversion).  
Queue the prompt. The STL is saved to the ComfyUI output directory.

### Step 7 — Export the casting mould STL
Right-click → **Add Node → Aperiodic Tiles → Export Casting Mould (STL)**.  
Connect:
- `Assign Tile Heights & Tilt` → **`TILE_HEIGHT_DATA` output** → `Export Casting Mould` **`tile_height_data` input**

> **Both STL export nodes share the same `TILE_HEIGHT_DATA` source.**  
> Wire the single output of `Assign Tile Heights & Tilt` to *both* `Export 3D Panel` and `Export Casting Mould` simultaneously — ComfyUI allows one output to fan out to multiple inputs.

Set `filename` (e.g. `aperiodic_mould.stl`), `base_thickness`, and `scale`.  
Queue the prompt. The mould STL is saved to the ComfyUI output directory.

## Pipeline Diagram

```
┌─────────────────────────┐
│  Hat Tiling Generator   │
│  width, height,         │
│  tile_size              │
└──────────┬──────────────┘
           │ HAT_DATA
           ▼
┌─────────────────────────┐
│  Fill Canvas (2D Layout)│
│  gap                    │
└──────┬──────────────────┘
       │ TILE_POLYGONS          ┌─────────────────────────┐
       ├────────────────────────► Render 2D Canvas (HTML)  │
       │                        │  → aperiodic_canvas.html │
       │                        └─────────────────────────┘
       ▼
┌─────────────────────────┐
│ Assign Tile Heights &   │
│ Tilt                    │
│ min/max_height, mode,   │
│ frequency, tilt_strength│
└──────┬──────────────────┘
       │ TILE_HEIGHT_DATA
       ├──────────────────────────────────────────────────────┐
       │                                                      │
       ▼                                                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌─────────────────────────┐
│ Render 3D Panel  │   │ Export 3D Panel  │   │ Export Casting Mould    │
│ (HTML)           │   │ (STL)            │   │ (STL)                   │
│ → panel_3d.html  │   │ → columns.stl    │   │ → mould.stl             │
└──────────────────┘   └──────────────────┘   └─────────────────────────┘
```

## File Structure

```
ComfyUI-AperiodicTiles/
├── __init__.py                      # Node registration for ComfyUI
├── nodes.py                         # All ComfyUI node class definitions
├── README.md                        # This file
└── aperiodic_tiles/                 # Core library modules
    ├── hat_tiling.py                # Hat-tile geometry + Z3 SAT solver
    ├── fill_canvas.py               # Canvas filtering and gap shrinkage
    ├── assign_tile_heights.py       # Procedural height & tilt assignment
    ├── render_canvas.py             # 2-D Plotly HTML renderer
    ├── render_panel.py              # 3-D Plotly HTML renderer
    ├── export_stl.py                # Column panel STL exporter
    └── export_mould_stl.py          # Casting mould STL exporter
```

## Mould Geometry Explained

The casting mould is a solid rectangular block whose dimensions match the full canvas:

```
X ∈ [0, canvas_width]
Y ∈ [0, canvas_height]
Z ∈ [0, mould_depth]   where mould_depth = base_thickness + max_column_height
```

The block is divided into two structurally distinct zones:

```
z ∈ [0,              base_thickness]  ← solid base slab — no cavities, completely solid
z ∈ [base_thickness, mould_depth   ]  ← cavity zone — one open cavity per tile column
```

The top face (z = mould_depth) is open above each tile footprint — those are the mouths of the cavities. The bottom face (z = 0) and all four side walls are solid and unbroken.

**Cavity geometry per tile:**
- **Side walls** — vertical prism walls that descend from the top face (z = mould_depth) down to the cavity floor.
- **Cavity floor** — a tilted planar surface at `z = base_thickness + column_height_at_vertex`. This exactly mirrors the tilted top face of the corresponding column so the cavity reproduces the column faithfully. Crucially, the floor never descends below `z = base_thickness`, so the solid base slab beneath it is always intact.

**How to use the mould:**
1. 3-D print or CNC-mill the mould STL.
2. Apply a release agent to the cavity surfaces.
3. Place the mould **upside down** (cavity openings facing up).
4. Pour your liquid material (resin, silicone, concrete, plaster, etc.) until the level reaches the top rim of the upside-down mould. The liquid fills all the column cavities and covers the `base_thickness` layer, which becomes the solid connecting floor of the finished panel.
5. Allow the material to cure / harden.
6. Demould (remove the mould block). The cast panel is a faithful reproduction of the original aperiodic column layout.

**Matching the two STL files:**  
Both `Export 3D Panel (STL)` and `Export Casting Mould (STL)` must receive data from the **same** `Assign Tile Heights & Tilt` node and use the **same `scale` value** so that the physical dimensions of the column panel and its mould are identical.
