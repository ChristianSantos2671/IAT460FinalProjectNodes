"""
export_stl.py
=============
Provides export_panel_stl() — converts a panel dict (returned by
assign_tile_heights()) into a binary STL file describing the extruded
aperiodic-tile columns.

Geometry
--------
The exported solid consists of:
    • One fully-closed prismatic column per tile.  Each column's bottom
      face sits at z = 0 and its top face is tilted according to
      tile["slant"].
    • A flat rectangular base-plate whose top face is at z = 0
      (touching the bottoms of every column) and whose bottom face is at
      z = -base_thickness.  The base plate is sized to the tight bounding
      box of the tile columns plus a small margin, so it never intersects
      any column volume.

All coordinates are optionally scaled by `scale` before export.

Dependencies
------------
numpy-stl  (pip install numpy-stl)
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Internal geometry helpers
# ---------------------------------------------------------------------------

def _baseplate_facets(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    base_thickness: float,
) -> list[list]:
    """
    Return triangle facets for a solid rectangular box whose *top* face is
    at z = 0 and whose *bottom* face is at z = -base_thickness.

    The box spans x in [x_min, x_max], y in [y_min, y_max].
    """
    z0 = -base_thickness   # bottom of base
    z1 = 0.0               # top of base  (= bottom of columns)

    corners = [
        [x_min, y_min, z0],  # 0 bottom-front-left
        [x_max, y_min, z0],  # 1 bottom-front-right
        [x_max, y_max, z0],  # 2 bottom-back-right
        [x_min, y_max, z0],  # 3 bottom-back-left
        [x_min, y_min, z1],  # 4 top-front-left
        [x_max, y_min, z1],  # 5 top-front-right
        [x_max, y_max, z1],  # 6 top-back-right
        [x_min, y_max, z1],  # 7 top-back-left
    ]

    # 6 faces × 2 triangles each (outward-facing normals)
    face_indices = [
        # bottom face (normal -Z)
        (0, 2, 1), (0, 3, 2),
        # top face (normal +Z)
        (4, 5, 6), (4, 6, 7),
        # front face (normal -Y)
        (0, 1, 5), (0, 5, 4),
        # right face (normal +X)
        (1, 2, 6), (1, 6, 5),
        # back face (normal +Y)
        (2, 3, 7), (2, 7, 6),
        # left face (normal -X)
        (3, 0, 4), (3, 4, 7),
    ]

    facets = []
    for i, j, k in face_indices:
        facets.append([corners[i], corners[j], corners[k]])
    return facets


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_panel_stl(
    panel: dict[str, Any],
    out_path: str,
    base_thickness: float = 10.0,
    base_margin: float = 5.0,
    scale: float = 1.0,
) -> str:
    """
    Build the column STL from a panel dict and save it to *out_path*.

    Parameters
    ----------
    panel : dict
        The panel dictionary returned by assign_tile_heights().
    out_path : str
        Destination file path (will be created/overwritten).
    base_thickness : float
        Thickness of the rectangular base-plate (mm).  The plate occupies
        z = -base_thickness .. 0, sitting completely below the columns.
    base_margin : float
        Extra margin (mm, pre-scale) added around the tile bounding box
        when sizing the base-plate.
    scale : float
        Uniform scale factor applied to every coordinate before export.

    Returns
    -------
    str
        The resolved output path.
    """
    try:
        from stl import mesh as stl_mesh
    except ImportError as exc:
        raise ImportError(
            "numpy-stl is required for STL export.  "
            "Install it with:  pip install numpy-stl"
        ) from exc

    # Lazy import so this module doesn't force render_panel to load at startup
    from . import render_panel as rp

    tiles = panel["tiles"]

    all_facets: list[list] = []

    # ── 1. Tile columns (z_floor = 0; columns sit at z = 0 and above) ────
    all_xs: list[float] = []
    all_ys: list[float] = []

    for tile in tiles:
        xs, ys, zs, top_i, top_j, top_k, side_i, side_j, side_k, _ = \
            rp._build_tile_mesh(tile, z_floor=0.0)

        verts = np.column_stack([xs, ys, zs]) * scale

        # Top face and side walls
        for i, j, k in zip(top_i + side_i, top_j + side_j, top_k + side_k):
            all_facets.append([verts[i].tolist(), verts[j].tolist(), verts[k].tolist()])

        # Bottom face — closes the prism so each column is a proper solid.
        # Bottom ring = indices 0..n-1, all at z = 0.
        # Downward-facing normal → CW winding from above (ccw_from_above=False).
        verts2d = [(v[0], v[1]) for v in tile["vertices"]]
        bot_tris = rp._ear_clip_triangulate(verts2d, ccw_from_above=False)
        for a, b, c in bot_tris:
            all_facets.append([verts[a].tolist(), verts[b].tolist(), verts[c].tolist()])

        # Accumulate XY extents of the bottom ring (already scaled)
        n_verts = len(verts2d)
        all_xs.extend(verts[:n_verts, 0].tolist())
        all_ys.extend(verts[:n_verts, 1].tolist())

    # ── 2. Base-plate (z = -base_thickness .. 0) ─────────────────────────
    # Sized to the tight bounding box of the tiles + margin, so it sits
    # completely outside the column volume while touching their bottoms.
    margin = base_margin * scale
    bx_min = min(all_xs) - margin
    bx_max = max(all_xs) + margin
    by_min = min(all_ys) - margin
    by_max = max(all_ys) + margin
    bt     = base_thickness * scale

    for facet in _baseplate_facets(bx_min, bx_max, by_min, by_max, bt):
        all_facets.append(facet)

    # ── 3. Assemble and save ──────────────────────────────────────────────
    n = len(all_facets)
    stl_data    = np.zeros(n, dtype=stl_mesh.Mesh.dtype)
    export_mesh = stl_mesh.Mesh(stl_data)
    for idx, (v0, v1, v2) in enumerate(all_facets):
        export_mesh.vectors[idx] = [v0, v1, v2]

    out_path = str(Path(out_path).with_suffix(".stl"))
    export_mesh.save(out_path)
    return out_path
