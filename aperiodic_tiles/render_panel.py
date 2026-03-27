"""
render_panel.py
===============
Provides render_panel() — takes the panel dict returned by assign_tile_heights()
and renders a fully interactive 3-D model of the extruded aperiodic tiling.

Each hat tile is a prism:
    • bottom face  — the hat polygon at z = 0
    • top face     — the same polygon shifted up by tile["height"] and
                     tilted according to tile["slant"] (unit normal of the top)
    • side walls   — connecting the bottom and top edges

Rendered with Plotly (go.Mesh3d) which opens in a browser window and lets the
user rotate, zoom and pan the model freely.

Colours
-------
Tiles cycle through a blue → orange colour palette whose shade is proportional
to height.  Taller tiles get a darker shade.
"""

from __future__ import annotations
import datetime
import math
from typing import Any

import numpy as np
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _top_vertex(
    bx: float, by: float,
    height: float,
    slant: list[float],
    cx: float, cy: float,
) -> tuple[float, float, float]:
    """
    Compute the z-coordinate of a top-face vertex.

    The plane of the top face passes through the centroid (cx, cy, height)
    with unit normal n = (nx, ny, nz).  Solving the plane equation for z:
        Z = height - (nx*(X-cx) + ny*(Y-cy)) / nz
    Falls back to flat top if nz ≈ 0.
    """
    nx, ny, nz = slant
    if abs(nz) < 1e-9:
        return (bx, by, height)
    dz = -(nx * (bx - cx) + ny * (by - cy)) / nz
    return (bx, by, height + dz)


def _signed_area(poly: list[tuple[float, float]]) -> float:
    """Signed area via the shoelace formula. Positive = CCW, negative = CW."""
    n = len(poly)
    area = 0.0
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area * 0.5


def _ear_clip_triangulate(poly: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
    """
    Ear-clipping triangulation for a simple (non-self-intersecting) polygon.
    Returns a list of (i, j, k) index triples.

    The algorithm assumes CCW winding (positive signed area).  If the input
    polygon is CW (negative signed area, common in screen-space coords where
    Y increases downward), the vertex order is reversed internally so that
    reflex-vertex detection works correctly on concave hat tiles.
    """
    n = len(poly)
    if n < 3:
        return []

    # Ensure CCW winding so the ear-clip cross-product test is correct.
    # A CW polygon (negative signed area, common in screen-space where Y is
    # downward) has its reflex vertices misidentified if we don't flip first.
    # We reverse the vertex list, triangulate, then map indices back to the
    # original ordering so callers always get indices into their own list.
    if _signed_area(poly) < 0:
        poly = poly[::-1]
        # fwd[new_index] = original_index
        fwd = [n - 1 - k for k in range(n)]
    else:
        fwd = list(range(n))

    def cross2d(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    def point_in_triangle(p, a, b, c):
        d1 = cross2d(p, a, b)
        d2 = cross2d(p, b, c)
        d3 = cross2d(p, c, a)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def is_ear(idx, ring):
        prev_i = ring[(idx - 1) % len(ring)]
        curr_i = ring[idx]
        next_i = ring[(idx + 1) % len(ring)]
        a, b, c = poly[prev_i], poly[curr_i], poly[next_i]
        if cross2d(a, b, c) <= 0:
            return False
        for k, vi in enumerate(ring):
            if vi in (prev_i, curr_i, next_i):
                continue
            if point_in_triangle(poly[vi], a, b, c):
                return False
        return True

    ring = list(range(n))
    triangles = []
    attempts = 0
    while len(ring) > 3:
        if attempts > len(ring) ** 2:
            # fallback: fan triangulation
            raw = [(ring[0], ring[i], ring[i+1]) for i in range(1, len(ring)-1)]
            return [(fwd[a], fwd[b], fwd[c]) for a, b, c in raw]
        found = False
        for i in range(len(ring)):
            if is_ear(i, ring):
                prev_i = ring[(i-1) % len(ring)]
                curr_i = ring[i]
                next_i = ring[(i+1) % len(ring)]
                triangles.append((prev_i, curr_i, next_i))
                ring.pop(i)
                found = True
                break
        if not found:
            raw = [(ring[0], ring[i], ring[i+1]) for i in range(1, len(ring)-1)]
            return [(fwd[a], fwd[b], fwd[c]) for a, b, c in raw]
        attempts += 1
    if len(ring) == 3:
        triangles.append((ring[0], ring[1], ring[2]))

    # Map reversed indices back to original vertex ordering
    return [(fwd[a], fwd[b], fwd[c]) for a, b, c in triangles]


def _build_tile_mesh(tile: dict[str, Any]) -> tuple[
    list[float], list[float], list[float],
    list[int], list[int], list[int],
]:
    """
    Build the 3-D mesh (vertices + triangle faces) for one extruded hat tile.
    Ensures the tile sits at or above z=0 regardless of tilt.
    Returns (xs, ys, zs, i_f, j_f, k_f) for go.Mesh3d or STL export.
    """
    verts2d = [(v[0], v[1]) for v in tile["vertices"]]
    n = len(verts2d)
    height = tile["height"]
    slant = tile["slant"]

    # Calculate centroid for the tilt plane equation
    cx = sum(v[0] for v in verts2d) / n
    cy = sum(v[1] for v in verts2d) / n

    # --- STEP 1: PRE-CALCULATE TILT TO PREVENT DOWNWARD EXTRUSION ---
    # We find the 'lowest' point of the tilted top face
    raw_top_zs = []
    for bx, by in verts2d:
        _, _, tz = _top_vertex(bx, by, height, slant, cx, cy)
        raw_top_zs.append(tz)
    
    # If the lowest point of the top is below 0, we shift the whole tile up
    min_tz = min(raw_top_zs)
    z_offset = abs(min_tz) if min_tz < 0 else 0 

    xs, ys, zs = [], [], []

    # --- STEP 2: GENERATE VERTICES ---
    # Bottom ring (z=0): indices 0..n-1
    for bx, by in verts2d:
        xs.append(bx); ys.append(by); zs.append(0.0)

    # Top ring (z varies + offset): indices n..2n-1
    for i, (bx, by) in enumerate(verts2d):
        tx, ty, tz = _top_vertex(bx, by, height, slant, cx, cy)
        xs.append(tx); ys.append(ty); zs.append(tz + z_offset)

    # --- STEP 3: GENERATE FACES (TRIANGULATION) ---
    i_f, j_f, k_f = [], [], []

    # Bottom face (Looking 'up' from below, so we reverse winding)
    for a, b, c in _ear_clip_triangulate(verts2d):
        i_f.append(a); j_f.append(c); k_f.append(b)

    # Top face
    top_2d = [(xs[n+i], ys[n+i]) for i in range(n)]
    for a, b, c in _ear_clip_triangulate(top_2d):
        i_f.append(n+a); j_f.append(n+b); k_f.append(n+c)

    # Side walls (Quads split into two triangles)
    for idx in range(n):
        nxt = (idx + 1) % n
        bl, br, tl, tr = idx, nxt, n+idx, n+nxt
        # Triangle 1
        i_f.append(bl); j_f.append(br); k_f.append(tl)
        # Triangle 2
        i_f.append(br); j_f.append(tr); k_f.append(tl)

    return xs, ys, zs, i_f, j_f, k_f


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _height_colour(height: float, min_h: float, max_h: float, idx: int) -> str:
    # 1. Clamp t between 0 and 1 to prevent negative colors
    t = max(0.0, min(1.0, (height - min_h) / max(max_h - min_h, 1e-9)))
    
    if idx % 2 == 0:
        # Blue palette
        r = int(13  + (227 - 13)  * (1 - t))
        g = int(71  + (242 - 71)  * (1 - t))
        b = int(161 + (253 - 161) * (1 - t))
    else:
        # Orange palette
        r = int(191 + (255 - 191) * (1 - t))
        g = int(54  + (243 - 54)  * (1 - t))
        b = int(12  + (224 - 12)  * (1 - t))
    
    # 2. Final safety clamp before hex conversion
    r, g, b = [max(0, min(255, val)) for val in (r, g, b)]
    
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_panel(
    panel: dict[str, Any],
    title: str = "Aperiodic Hat Tiling — 3-D Panel",
    show: bool = True,
    save_html: str | None = None,
) -> go.Figure:
    """
    Render the 3-D extruded hat-tile panel using Plotly.

    Parameters
    ----------
    panel : dict
        The panel dictionary returned by assign_tile_heights().
    title : str, optional
        Title shown in the Plotly figure.
    show : bool, optional
        If True (default), open the figure in a browser window.
    save_html : str or None, optional
        If given, save the interactive HTML to this file path.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    tiles     = panel["tiles"]
    min_h     = panel.get("min_height", 0.0)
    max_h     = panel.get("max_height", 1.0)
    canvas_w  = panel["canvas_width"]
    canvas_h  = panel["canvas_height"]

    meshes = []
    for idx, tile in enumerate(tiles):
        xs, ys, zs, i_f, j_f, k_f = _build_tile_mesh(tile)

        # A single uniform colour per tile avoids the per-triangle shading
        # artefact that appears when vertexcolor + flatshading are combined.
        # flatshading=True shades each triangle by its own face normal; with
        # vertexcolor Plotly can produce visibly different shades for each
        # triangle of the (mathematically flat) top face, making it look as
        # though the top has multiple different slants.  Using a single color
        # string lets Plotly shade the mesh with smooth lighting instead,
        # so the flat top reads as one continuous surface.
        main_colour = _height_colour(tile["height"], min_h, max_h, idx)

        mesh = go.Mesh3d(
            x=xs, y=ys, z=zs,
            i=i_f, j=j_f, k=k_f,
            color=main_colour,
            opacity=1.0,
            flatshading=False,   # smooth lighting keeps the flat top looking flat
            lighting=dict(
                ambient=0.4,
                diffuse=0.9,
                specular=0.3,
                roughness=0.5,
                fresnel=0.1,
            ),
            lightposition=dict(x=canvas_w * 0.5, y=-canvas_h, z=max_h * 10),
            showscale=False,
            hovertemplate=(
                f"Height: {tile['height']:.1f}<br>"
                f"Tile index: {idx}<extra></extra>"
            ),
        )
        meshes.append(mesh)

    fig = go.Figure(data=meshes)

    camera = dict(eye=dict(x=1.5, y=-1.5, z=1.2), up=dict(x=0, y=0, z=1))
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fig.update_layout(
        title=dict(
            text=f"{title}<br><sup>Created: {created_at}</sup>",
            font=dict(size=16),
        ),
        scene=dict(
            xaxis=dict(title="X (px)", showbackground=True,
                       backgroundcolor="#e8e8f0"),
            yaxis=dict(title="Y (px)", showbackground=True,
                       backgroundcolor="#e8e8f0"),
            zaxis=dict(title="Height", showbackground=True,
                       backgroundcolor="#d8d8e8"),
            camera=camera,
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e8e8e8"),
    )

    if save_html:
        fig.write_html(save_html)
        print(f"[render_panel] Saved interactive HTML to {save_html}")

    if show:
        fig.show()

    return fig
