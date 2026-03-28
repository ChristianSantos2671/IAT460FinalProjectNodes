"""
export_mould_stl.py
===================
Provides export_mould_stl() -- converts a panel dict (returned by
assign_tile_heights()) into a binary STL file describing a casting mould
for the aperiodic-tile panel produced by export_stl.py.

Mould geometry
--------------
The mould is a rectangular shell (closed box with an open top) that wraps
a skin of uniform thickness around the aperiodic-tile 3-D shape.

Coordinate system (mould as printed, open face up for pouring):

    z = 0                   -- solid bottom of the mould (the buffer layer
                               below the deepest column-tip cavity).
    z = wall_thickness      -- floor of the deepest cavity (tip of the tallest
                               column when the mould is flipped right-side-up).
    z = mould_height        -- the open top face from which liquid is poured.
    mould_height            = global_max_col_top_z + wall_thickness

Outer XY footprint of the mould:
    [tile_bx_min - wall_thickness, tile_bx_max + wall_thickness]
    [tile_by_min - wall_thickness, tile_by_max + wall_thickness]
where tile_bx/by_min/max are computed from the tile vertex bounding box
expanded by base_margin (same margin used in export_stl.py).

Each tile cavity:
    - Opens at z = mould_height (the pour face).
    - Its floor at vertex (bx, by) is at:
          z = wall_thickness + (global_max_col_top_z - col_top_z_at(bx,by))
      The tallest column vertex produces the deepest cavity (floor at z = wall_thickness).
      Flatter/shorter columns have shallower cavities (floor higher up).
    - Side walls are vertical, connecting the open top to the tilted floor.

When flipped upside-down and filled with liquid:
    - The cavities form the columns of the finished panel.
    - Extra liquid above the column tips forms the connecting base plate.
    - After hardening and demoulding the result is the export_stl.py shape.

Dependencies
------------
numpy-stl  (pip install numpy-stl)
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import numpy as np


# ---------------------------------------------------------------------------
# Geometry helpers (2-D)
# ---------------------------------------------------------------------------

def _signed_area_2d(poly):
    """Shoelace signed area. Positive = CW on screen (Y-down) = CCW from +Z."""
    n = len(poly)
    area = 0.0
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area * 0.5


def _ear_clip(poly, ccw_from_above=True):
    """
    Ear-clip triangulation for a simple polygon in screen-space (Y-down).
    Returns list of (i, j, k) index triples into poly.
    ccw_from_above=True  => face normals point upward (+Z).
    ccw_from_above=False => face normals point downward (-Z).
    """
    n = len(poly)
    if n < 3:
        return []
    area = _signed_area_2d(poly)
    if area < 0:
        work = poly[::-1]
        orig_idx = list(range(n - 1, -1, -1))
    else:
        work = list(poly)
        orig_idx = list(range(n))

    def cross2d(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def point_in_tri(p, a, b, c):
        d1 = cross2d(p, a, b)
        d2 = cross2d(p, b, c)
        d3 = cross2d(p, c, a)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def is_ear(idx, ring):
        pi = ring[(idx - 1) % len(ring)]
        ci = ring[idx]
        ni = ring[(idx + 1) % len(ring)]
        a, b, c = work[pi], work[ci], work[ni]
        if cross2d(a, b, c) <= 0:
            return False
        for vi in ring:
            if vi in (pi, ci, ni):
                continue
            if point_in_tri(work[vi], a, b, c):
                return False
        return True

    ring = list(range(n))
    tris = []
    attempts = 0
    while len(ring) > 3:
        if attempts > len(ring) ** 2:
            tris += [(ring[0], ring[i], ring[i + 1]) for i in range(1, len(ring) - 1)]
            ring = []
            break
        found = False
        for i in range(len(ring)):
            if is_ear(i, ring):
                pi = ring[(i - 1) % len(ring)]
                ci = ring[i]
                ni = ring[(i + 1) % len(ring)]
                tris.append((pi, ci, ni))
                ring.pop(i)
                found = True
                break
        if not found:
            tris += [(ring[0], ring[i], ring[i + 1]) for i in range(1, len(ring) - 1)]
            break
        attempts += 1
    if len(ring) == 3:
        tris.append((ring[0], ring[1], ring[2]))

    result = [(orig_idx[a], orig_idx[b], orig_idx[c]) for a, b, c in tris]
    if not ccw_from_above:
        result = [(a, c, b) for a, b, c in result]
    return result


# ---------------------------------------------------------------------------
# Column-top z helper
# ---------------------------------------------------------------------------

def _col_top_z(bx, by, height, slant, cx, cy):
    """
    Return the z-coordinate of the column top surface at position (bx, by).
    The top face is a tilted plane through (cx, cy, height) with normal slant.
    """
    nx, ny, nz = slant
    if abs(nz) < 1e-9:
        return float(height)
    return float(height) - (nx * (bx - cx) + ny * (by - cy)) / nz


# ---------------------------------------------------------------------------
# Mould surface builders
# ---------------------------------------------------------------------------

def _box_bottom(x0, x1, y0, y1):
    """
    Solid bottom face of the mould box at z = 0. Normal points downward (-Z).
    """
    corners = [
        [x0, y0, 0.0], [x1, y0, 0.0],
        [x1, y1, 0.0], [x0, y1, 0.0],
    ]
    # CW from above = normal -Z
    return [
        [corners[0], corners[2], corners[1]],
        [corners[0], corners[3], corners[2]],
    ]


def _box_sides(x0, x1, y0, y1, mould_height):
    """
    Four vertical outer side walls of the mould box. Normals point outward.
    The walls run from z=0 to z=mould_height.
    """
    D = mould_height
    b = [[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0]]
    t = [[x0, y0, D], [x1, y0, D], [x1, y1, D], [x0, y1, D]]
    facets = []
    # Front  (-Y)
    facets += [[b[0], b[1], t[1]], [b[0], t[1], t[0]]]
    # Right  (+X)
    facets += [[b[1], b[2], t[2]], [b[1], t[2], t[1]]]
    # Back   (+Y)
    facets += [[b[2], b[3], t[3]], [b[2], t[3], t[2]]]
    # Left   (-X)
    facets += [[b[3], b[0], t[0]], [b[3], t[0], t[3]]]
    return facets


def _top_face_with_holes(x0, x1, y0, y1, mould_height, tiles):
    """
    Triangulate the top face of the mould (z = mould_height) as a flat
    rectangle with one tile-shaped hole per tile, so the cavities are visible
    from above.  Normal of the face points upward (+Z).

    Implementation
    --------------
    Uses Shapely (if available) for robust polygon-with-holes triangulation,
    falling back to a pure-Python bridge-cut ear-clip approach.

    With Shapely: the rectangle with holes is computed exactly, then
    triangulated via its ``triangulate`` method.

    Without Shapely: tiles are processed in left-to-right order of their
    rightmost vertex so that each bridge seam is as short as possible and
    does not cross previously inserted seams.
    """
    D = mould_height

    # ── Try Shapely first (most robust) ──────────────────────────────────
    try:
        from shapely.geometry import Polygon, MultiPolygon
        from shapely.ops import triangulate as sh_triangulate, unary_union

        outer_poly = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        holes = [Polygon([(v[0], v[1]) for v in tile["vertices"]]) for tile in tiles]
        hole_union = unary_union(holes)
        # face = the mould top surface: rectangle minus all tile footprints
        face = outer_poly.difference(hole_union)

        def _emit_triangle(coords, facets_list):
            """Append one triangle (3 coords) with normal +Z to facets_list."""
            v0 = [coords[0][0], coords[0][1], D]
            v1 = [coords[1][0], coords[1][1], D]
            v2 = [coords[2][0], coords[2][1], D]
            ax, ay = coords[1][0]-coords[0][0], coords[1][1]-coords[0][1]
            bx2, by2 = coords[2][0]-coords[0][0], coords[2][1]-coords[0][1]
            cross_z = ax * by2 - ay * bx2
            if cross_z > 0:
                facets_list.append([v0, v1, v2])
            else:
                facets_list.append([v0, v2, v1])

        facets = []
        # sh_triangulate returns Delaunay triangles covering the convex hull of
        # all vertices.  We intersect each triangle with `face` to clip it
        # exactly to the mould-top surface (rectangle minus tile holes).
        for tri in sh_triangulate(face, tolerance=0.0):
            clipped = face.intersection(tri)
            if clipped.is_empty:
                continue
            geoms = (
                list(clipped.geoms)
                if hasattr(clipped, "geoms")
                else [clipped]
            )
            for g in geoms:
                g_type = g.geom_type
                if g_type == "Polygon":
                    coords = list(g.exterior.coords)[:-1]
                    if len(coords) == 3:
                        _emit_triangle(coords, facets)
                    elif len(coords) > 3:
                        # Sub-triangulate via fan
                        for i in range(1, len(coords) - 1):
                            _emit_triangle(
                                [coords[0], coords[i], coords[i + 1]], facets
                            )
        return facets

    except ImportError:
        pass  # fall through to pure-Python bridge-cut below

    # ── Pure-Python bridge-cut fallback ───────────────────────────────────
    # Outer ring wound CW on screen (shoelace area > 0) => normal +Z.
    outer = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    current_poly = list(outer)

    # Process tiles sorted by the x-coordinate of their rightmost vertex,
    # left-to-right, so each bridge is short and does not cross prior seams.
    sorted_tiles = sorted(
        tiles,
        key=lambda t: max(v[0] for v in t["vertices"]),
    )

    for tile in sorted_tiles:
        verts2d = [(v[0], v[1]) for v in tile["vertices"]]
        n_hole = len(verts2d)
        hole_area = _signed_area_2d(verts2d)
        # Hole must wind CCW on screen (area < 0) — opposite to the outer ring.
        if hole_area >= 0:
            hole = verts2d[::-1]
        else:
            hole = list(verts2d)

        # Bridge anchor = rightmost hole vertex (best visibility to outer ring).
        hb = max(range(n_hole), key=lambda i: hole[i][0])
        hole = hole[hb:] + hole[:hb]   # rotate so anchor is index 0
        hx, hy = hole[0]

        # Outer-ring vertex to connect to: rightmost outer vertex with x >= hx,
        # or if none exists, the closest outer vertex.
        candidates = [i for i, p in enumerate(current_poly) if p[0] >= hx]
        if candidates:
            ob = min(candidates, key=lambda i: abs(current_poly[i][1] - hy))
        else:
            ob = min(
                range(len(current_poly)),
                key=lambda i: (current_poly[i][0] - hx) ** 2 + (current_poly[i][1] - hy) ** 2,
            )

        bridge_outer = current_poly[ob]
        bridge_hole  = hole[0]
        current_poly = (
            current_poly[: ob + 1]
            + list(hole)
            + [bridge_hole]
            + [bridge_outer]
            + current_poly[ob + 1 :]
        )

    facets = []
    for a, b, c in _ear_clip(current_poly, ccw_from_above=True):
        v0 = [current_poly[a][0], current_poly[a][1], D]
        v1 = [current_poly[b][0], current_poly[b][1], D]
        v2 = [current_poly[c][0], current_poly[c][1], D]
        facets.append([v0, v1, v2])
    return facets


def _cavity_facets(tile, mould_height, wall_thickness, global_max_col_top_z):
    """
    Build the interior surface of one tile cavity.

    Cavity geometry (mould upright, open top for pouring):
        - Opens at z = mould_height.
        - Floor at each vertex: z = wall_thickness + (global_max_col_top_z - col_top_z)
          so the globally tallest column tip maps to the deepest cavity floor
          (z = wall_thickness) and shorter columns map to shallower floors.
        - Side walls are vertical between mould_height and floor_z per edge.

    Side-wall normals point inward (toward the cavity interior).
    Floor normals point upward (+Z), i.e. toward the open pour face.
    """
    verts2d = [(v[0], v[1]) for v in tile["vertices"]]
    n = len(verts2d)
    height = tile["height"]
    slant  = tile["slant"]
    cx = sum(v[0] for v in verts2d) / n
    cy = sum(v[1] for v in verts2d) / n

    # z of the column top at each bottom-ring vertex (from export_stl.py geometry)
    col_top_zs = [_col_top_z(bx, by, height, slant, cx, cy) for bx, by in verts2d]

    # Cavity floor z: deepest point = wall_thickness (tallest col tip),
    # shallower columns yield higher floor (closer to mould_height).
    floor_zs = [wall_thickness + (global_max_col_top_z - ctz) for ctz in col_top_zs]
    # Clamp just in case of floating-point overshoot
    floor_zs = [max(wall_thickness, min(mould_height, fz)) for fz in floor_zs]

    facets = []
    area = _signed_area_2d(verts2d)
    ccw = (area > 0)  # CCW from +Z in 3-D (screen-space Y-down: area>0 = CCW from +Z)

    # ── Side walls ────────────────────────────────────────────────────────
    for idx in range(n):
        nxt = (idx + 1) % n
        bx0, by0 = verts2d[idx]
        bx1, by1 = verts2d[nxt]
        top0 = [bx0, by0, mould_height]
        top1 = [bx1, by1, mould_height]
        bot0 = [bx0, by0, floor_zs[idx]]
        bot1 = [bx1, by1, floor_zs[nxt]]
        # Inward-facing normals for cavity walls (opposite to export_stl side walls)
        if ccw:
            facets.append([top0, top1, bot0])
            facets.append([top1, bot1, bot0])
        else:
            facets.append([top0, bot0, top1])
            facets.append([top1, bot0, bot1])

    # ── Cavity floor (tilted, normal pointing toward pour opening = +Z) ──
    for a, b, c in _ear_clip(verts2d, ccw_from_above=True):
        v0 = [verts2d[a][0], verts2d[a][1], floor_zs[a]]
        v1 = [verts2d[b][0], verts2d[b][1], floor_zs[b]]
        v2 = [verts2d[c][0], verts2d[c][1], floor_zs[c]]
        facets.append([v0, v1, v2])

    return facets


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_mould_stl(
    panel: dict,
    out_path: str,
    wall_thickness: float = 10.0,
    base_margin: float = 5.0,
    scale: float = 1.0,
) -> str:
    """
    Build the casting-mould STL from a panel dict and save it to out_path.

    Parameters
    ----------
    panel : dict
        The panel dictionary returned by assign_tile_heights().
    out_path : str
        Destination file path (will be created/overwritten).
    wall_thickness : float
        Uniform skin thickness (mm) of the mould walls:
          - Added to all four sides of the tile bounding box.
          - Forms the solid buffer below the deepest column-tip cavity.
        Increase for higher-temperature materials (e.g. molten metal).
    base_margin : float
        Extra margin (mm, pre-scale) added around the tile bounding box
        before the wall_thickness is applied.  Matches the base_margin
        used in export_stl.py.
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
            "numpy-stl is required for STL export. "
            "Install it with:  pip install numpy-stl"
        ) from exc

    tiles = panel["tiles"]

    # ── Step 1: compute tile vertex bounding box (pre-scale) ─────────────
    all_xs = [v[0] for tile in tiles for v in tile["vertices"]]
    all_ys = [v[1] for tile in tiles for v in tile["vertices"]]
    tile_xmin, tile_xmax = min(all_xs), max(all_xs)
    tile_ymin, tile_ymax = min(all_ys), max(all_ys)

    # Apply base_margin then wall_thickness for outer footprint
    margin = base_margin + wall_thickness
    x0 = tile_xmin - margin
    x1 = tile_xmax + margin
    y0 = tile_ymin - margin
    y1 = tile_ymax + margin

    # ── Step 2: compute global max column-top z across all tile vertices ──
    global_max_col_top_z = 0.0
    for tile in tiles:
        verts2d = [(v[0], v[1]) for v in tile["vertices"]]
        n = len(verts2d)
        cx = sum(v[0] for v in verts2d) / n
        cy = sum(v[1] for v in verts2d) / n
        for bx, by in verts2d:
            ctz = _col_top_z(bx, by, tile["height"], tile["slant"], cx, cy)
            if ctz > global_max_col_top_z:
                global_max_col_top_z = ctz

    mould_height = global_max_col_top_z + wall_thickness

    # ── Step 3: assemble all surface facets ───────────────────────────────
    all_facets: list = []

    # Solid bottom face (z = 0, normal -Z)
    all_facets.extend(_box_bottom(x0, x1, y0, y1))

    # Four outer side walls (z = 0 .. mould_height)
    all_facets.extend(_box_sides(x0, x1, y0, y1, mould_height))

    # Top face of the mould (z = mould_height): solid rectangular rim with one
    # hole per tile footprint so the cavities are visible from above.
    all_facets.extend(_top_face_with_holes(x0, x1, y0, y1, mould_height, tiles))

    # Per-tile cavity interiors (side walls + tilted floor)
    for tile in tiles:
        all_facets.extend(_cavity_facets(tile, mould_height, wall_thickness, global_max_col_top_z))

    # ── Step 4: scale and save ────────────────────────────────────────────
    n = len(all_facets)
    stl_data    = np.zeros(n, dtype=stl_mesh.Mesh.dtype)
    export_mesh = stl_mesh.Mesh(stl_data)
    for idx, (v0, v1, v2) in enumerate(all_facets):
        export_mesh.vectors[idx] = [
            [c * scale for c in v0],
            [c * scale for c in v1],
            [c * scale for c in v2],
        ]

    out_path = str(Path(out_path).with_suffix(".stl"))
    export_mesh.save(out_path)
    return out_path
