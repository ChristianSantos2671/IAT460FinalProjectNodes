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
    """
    Signed area via the shoelace formula.

    In standard math coordinates (Y-up):
        Positive → CCW winding,  Negative → CW winding.

    In screen/canvas coordinates (Y-down, as used here):
        The Y axis is flipped, so the sign is reversed:
        Positive → CW  winding (as seen from above in 3-D, i.e. +Z looking down),
        Negative → CCW winding (as seen from above in 3-D).
    """
    n = len(poly)
    area = 0.0
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area * 0.5


def _ear_clip_triangulate(
    poly: list[tuple[float, float]],
    ccw_from_above: bool = True,
) -> list[tuple[int, int, int]]:
    """
    Ear-clipping triangulation for a simple (non-self-intersecting) polygon.

    Parameters
    ----------
    poly : list of (x, y)
        Polygon vertices in screen-space (Y-down) coordinates.
    ccw_from_above : bool
        If True  (default), returned triangle windings are CCW as seen from
        above (+Z), so their face normals point upward (+Z).
        If False, windings are CW from above (normals point downward, −Z).

    Returns
    -------
    list of (i, j, k) index triples into the original `poly` list.

    Implementation notes
    --------------------
    In screen-space Y-down, the shoelace formula gives *positive* area for
    polygons wound CW on screen, which equals CCW from +Z in 3-D.
    The ear-clip cross-product (cross2d) is also sign-flipped relative to
    math-space: a positive cross2d means the turn is CW on screen = CCW
    from +Z, which is the "convex" direction for a CW-on-screen polygon.

    The algorithm therefore works in screen-space directly:
      • It expects the input ring to be CW on screen (= CCW from +Z, area > 0).
      • If the polygon is CCW on screen (area < 0), we reverse it, run the
        algorithm, and un-reverse the output indices.
      • All returned triangles are wound CW on screen = CCW from +Z (upward
        normal).  Pass ccw_from_above=False to flip them.
    """
    n = len(poly)
    if n < 3:
        return []

    area = _signed_area(poly)

    # Work on a copy that is guaranteed to be CW-on-screen (area > 0 = CCW-from-above).
    # If already CW-on-screen keep as is; if CCW-on-screen reverse so the
    # ear-clip convexity test (positive cross2d) works correctly.
    if area < 0:
        # CCW on screen → reverse to make CW on screen
        work = poly[::-1]
        # orig_idx[new_index] = original index
        orig_idx = list(range(n - 1, -1, -1))
    else:
        work = list(poly)
        orig_idx = list(range(n))

    def cross2d(o, a, b):
        """2-D cross product; positive = CW turn on screen = convex for a CW-on-screen poly."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

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
        a, b, c = work[prev_i], work[curr_i], work[next_i]
        # Must be a convex (positive cross2d) vertex for a CW-on-screen poly
        if cross2d(a, b, c) <= 0:
            return False
        for vi in ring:
            if vi in (prev_i, curr_i, next_i):
                continue
            if point_in_triangle(work[vi], a, b, c):
                return False
        return True

    ring = list(range(n))
    triangles_work = []   # indices into `work`

    attempts = 0
    while len(ring) > 3:
        if attempts > len(ring) ** 2:
            # Fallback: fan from ring[0]
            triangles_work += [(ring[0], ring[i], ring[i + 1])
                               for i in range(1, len(ring) - 1)]
            ring = []
            break
        found = False
        for i in range(len(ring)):
            if is_ear(i, ring):
                prev_i = ring[(i - 1) % len(ring)]
                curr_i = ring[i]
                next_i = ring[(i + 1) % len(ring)]
                triangles_work.append((prev_i, curr_i, next_i))
                ring.pop(i)
                found = True
                break
        if not found:
            # Fallback: fan from ring[0]
            triangles_work += [(ring[0], ring[i], ring[i + 1])
                               for i in range(1, len(ring) - 1)]
            break
        attempts += 1

    if len(ring) == 3:
        triangles_work.append((ring[0], ring[1], ring[2]))

    # Map indices from the working (possibly reversed) polygon back to the
    # original vertex ordering.  The working triangles are CW-on-screen
    # (= CCW-from-above, outward normal +Z).
    result = [(orig_idx[a], orig_idx[b], orig_idx[c])
              for a, b, c in triangles_work]

    # If caller needs CW-from-above (outward normal −Z), flip each triangle.
    if not ccw_from_above:
        result = [(a, c, b) for a, b, c in result]

    return result


def _build_tile_mesh(tile: dict[str, Any], z_floor: float = 0.0) -> tuple[
    list[float], list[float], list[float],
    list[int], list[int], list[int],
    list[int], list[int], list[int],
    int,
]:
    """
    Build the 3-D mesh (vertices + triangle faces) for one extruded hat tile.
    Ensures the tile sits at or above z=z_floor regardless of tilt.

    Returns
    -------
    xs, ys, zs : vertex coordinate lists
    top_i, top_j, top_k : face index lists for the top face only
    side_i, side_j, side_k : face index lists for the side walls only
    n_top_tris : number of triangles in the top face
    """
    verts2d = [(v[0], v[1]) for v in tile["vertices"]]
    n = len(verts2d)
    height = tile["height"]
    slant = tile["slant"]

    # Centroid for the tilt plane equation
    cx = sum(v[0] for v in verts2d) / n
    cy = sum(v[1] for v in verts2d) / n

    # Pre-calculate tilt to prevent any top vertex falling below z_floor
    raw_top_zs = [_top_vertex(bx, by, height, slant, cx, cy)[2]
                  for bx, by in verts2d]
    min_tz = min(raw_top_zs)
    z_offset = (z_floor - min_tz) if min_tz < z_floor else 0.0

    xs, ys, zs = [], [], []

    # Bottom ring: indices 0..n-1
    for bx, by in verts2d:
        xs.append(bx); ys.append(by); zs.append(z_floor)

    # Top ring: indices n..2n-1
    for bx, by in verts2d:
        tx, ty, tz = _top_vertex(bx, by, height, slant, cx, cy)
        xs.append(tx); ys.append(ty); zs.append(tz + z_offset)

    # Winding sense as seen from +Z (needed for correct side-wall outward normals)
    poly_area = _signed_area(verts2d)
    ccw_from_above = (poly_area > 0)   # positive shoelace area = CCW from +Z

    # ── Top face ──────────────────────────────────────────────────────────
    top_2d = [(xs[n + i], ys[n + i]) for i in range(n)]
    top_i, top_j, top_k = [], [], []
    for a, b, c in _ear_clip_triangulate(top_2d, ccw_from_above=True):
        top_i.append(n + a); top_j.append(n + b); top_k.append(n + c)

    # ── Side walls ────────────────────────────────────────────────────────
    side_i, side_j, side_k = [], [], []
    for idx in range(n):
        nxt = (idx + 1) % n
        bl, br = idx, nxt
        tl, tr = n + idx, n + nxt
        if ccw_from_above:
            side_i.append(bl); side_j.append(br); side_k.append(tr)
            side_i.append(bl); side_j.append(tr); side_k.append(tl)
        else:
            side_i.append(bl); side_j.append(tl); side_k.append(tr)
            side_i.append(bl); side_j.append(tr); side_k.append(br)

    return xs, ys, zs, top_i, top_j, top_k, side_i, side_j, side_k, len(top_i)


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# Default tile colours (dark end of the gradient)
_DEFAULT_COLOUR_A = "#0d47a1"   # deep blue   (even tiles)
_DEFAULT_COLOUR_B = "#bf360c"   # deep orange (odd tiles)
_DEFAULT_BG_COLOUR   = "#1a1a2e"  # dark-navy page background
_DEFAULT_GRID_COLOUR = "#e8e8f0"  # light blue-grey grid planes


def _height_colour(
    height: float,
    min_h: float,
    max_h: float,
    idx: int,
    colour_a: str = _DEFAULT_COLOUR_A,
    colour_b: str = _DEFAULT_COLOUR_B,
) -> str:
    """
    Return a hex colour string for the given tile height.

    Tiles with even *idx* interpolate from a light tint of *colour_a* (short)
    to *colour_a* itself (tall).  Odd tiles do the same with *colour_b*.
    The light tint is produced by blending the chosen colour 30 % toward white.
    """
    t = max(0.0, min(1.0, (height - min_h) / max(max_h - min_h, 1e-9)))
    base = colour_a if idx % 2 == 0 else colour_b
    br, bg, bb = _hex_to_rgb(base)
    # Light end: blend 70 % white + 30 % base colour
    lr = int(br * 0.30 + 255 * 0.70)
    lg = int(bg * 0.30 + 255 * 0.70)
    lb = int(bb * 0.30 + 255 * 0.70)
    # Interpolate: t=0 → light end, t=1 → dark (base) colour
    r = int(lr + (br - lr) * t)
    g = int(lg + (bg - lg) * t)
    b = int(lb + (bb - lb) * t)
    r, g, b = [max(0, min(255, v)) for v in (r, g, b)]
    return f"#{r:02x}{g:02x}{b:02x}"


def _shade_colour(hex_colour: str, brightness: float) -> str:
    """
    Scale an RGB hex colour by a brightness factor (0–1) and return hex.
    Used to pre-compute the lit colour of the top face so every triangle
    on that face gets the identical colour value regardless of Plotly's
    per-triangle normal recomputation.
    """
    r, g, b = _hex_to_rgb(hex_colour)
    r = max(0, min(255, int(r * brightness)))
    g = max(0, min(255, int(g * brightness)))
    b = max(0, min(255, int(b * brightness)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _top_face_brightness(slant: list[float]) -> float:
    """
    Compute the diffuse-lighting brightness of the top face given its slant
    (surface normal) and the global light direction.

    The light direction matches lightposition=dict(x=1e5, y=-1e5, z=1e5),
    i.e. L = normalise([1, -1, 1]).

    Returns a brightness in [ambient, ambient + diffuse] to match the
    lighting parameters used for the side-wall traces.
    """
    # Normalise the surface normal (slant may be un-normalised)
    nx, ny, nz = slant
    mag = math.sqrt(nx * nx + ny * ny + nz * nz)
    if mag < 1e-9:
        nx, ny, nz = 0.0, 0.0, 1.0
    else:
        nx, ny, nz = nx / mag, ny / mag, nz / mag

    # Light direction (unit vector toward the light source)
    lx, ly, lz = 1.0, -1.0, 1.0
    lmag = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / lmag, ly / lmag, lz / lmag

    # Lambertian diffuse: N · L, clamped to [0, 1]
    n_dot_l = max(0.0, nx * lx + ny * ly + nz * lz)

    ambient = 0.55
    diffuse = 0.7
    return ambient + diffuse * n_dot_l


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_panel(
    panel: dict[str, Any],
    title: str = "Aperiodic Hat Tiling — 3-D Panel",
    show: bool = True,
    save_html: str | None = None,
    colour_a: str = _DEFAULT_COLOUR_A,
    colour_b: str = _DEFAULT_COLOUR_B,
    bg_colour: str = _DEFAULT_BG_COLOUR,
    grid_colour: str = _DEFAULT_GRID_COLOUR,
) -> go.Figure:
    """
    Render the 3-D extruded hat-tile panel using Plotly.

    Each tile is split into two go.Mesh3d traces:

    1. Top face — uses ``facecolor`` (one explicit hex colour per triangle).
       Every triangle on the top face receives the *same* pre-computed colour,
       derived from the tile's true surface normal and the scene light direction.
       This guarantees a uniformly shaded top surface regardless of how Plotly's
       WebGL engine computes per-triangle normals internally.

    2. Side walls — uses ``flatshading=True`` with Plotly's lighting engine.
       Each wall quad is two triangles whose normals differ, so they correctly
       shade as a single angled surface.

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
    colour_a : str, optional
        Hex colour (e.g. ``"#0d47a1"``) used for even-indexed tile columns.
        Short tiles receive a light tint; tall tiles receive the full colour.
    colour_b : str, optional
        Hex colour used for odd-indexed tile columns.
    bg_colour : str, optional
        Hex colour for the page/environment background (outside the 3-D scene).
    grid_colour : str, optional
        Hex colour applied to all three axis grid planes (X, Y, Z backgrounds).

    Returns
    -------
    plotly.graph_objects.Figure
    """
    tiles    = panel["tiles"]
    min_h    = panel.get("min_height", 0.0)
    max_h    = panel.get("max_height", 1.0)

    # Shared lighting / light-position kwargs for the side-wall traces
    _lighting     = dict(ambient=0.55, diffuse=0.7, specular=0.15,
                         roughness=0.8, fresnel=0.05)
    _lightpos     = dict(x=1e5, y=-1e5, z=1e5)

    meshes = []
    for idx, tile in enumerate(tiles):
        xs, ys, zs, top_i, top_j, top_k, side_i, side_j, side_k, n_top = \
            _build_tile_mesh(tile)

        base_colour = _height_colour(tile["height"], min_h, max_h, idx,
                                     colour_a=colour_a, colour_b=colour_b)

        # ── 1. Top face: facecolor — one identical colour per triangle ────
        # Pre-compute the lit colour from the true surface normal so all
        # triangles on this (planar) face are rendered at the same brightness.
        brightness   = _top_face_brightness(tile["slant"])
        top_colour   = _shade_colour(base_colour, brightness)
        top_facecolors = [top_colour] * n_top   # same colour for every tri

        top_mesh = go.Mesh3d(
            x=xs, y=ys, z=zs,
            i=top_i, j=top_j, k=top_k,
            facecolor=top_facecolors,
            opacity=1.0,
            flatshading=True,       # required when facecolor is set
            showscale=False,
            hovertemplate=(
                f"Height: {tile['height']:.1f}<br>"
                f"Tile index: {idx} (top)<extra></extra>"
            ),
        )
        meshes.append(top_mesh)

        # ── 2. Side walls: standard flat-shaded lighting ──────────────────
        if side_i:
            side_mesh = go.Mesh3d(
                x=xs, y=ys, z=zs,
                i=side_i, j=side_j, k=side_k,
                color=base_colour,
                opacity=1.0,
                flatshading=True,
                lighting=_lighting,
                lightposition=_lightpos,
                showscale=False,
                hovertemplate=(
                    f"Height: {tile['height']:.1f}<br>"
                    f"Tile index: {idx} (side)<extra></extra>"
                ),
            )
            meshes.append(side_mesh)

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
                       backgroundcolor=grid_colour),
            yaxis=dict(title="Y (px)", showbackground=True,
                       backgroundcolor=grid_colour),
            zaxis=dict(title="Height", showbackground=True,
                       backgroundcolor=grid_colour),
            camera=camera,
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor=bg_colour,
        font=dict(color="#e8e8e8"),
    )

    if save_html:
        fig.write_html(save_html)
        print(f"[render_panel] Saved interactive HTML to {save_html}")

    if show:
        fig.show()

    return fig
