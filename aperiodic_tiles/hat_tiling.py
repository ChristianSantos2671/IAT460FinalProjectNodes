"""
hat_tiling.py
=============
Generates an aperiodic hat-tile (Einstein tile) tiling using the approach
from the reference Colab notebook:
  https://colab.research.google.com/drive/1cBs3HGFQ6cz8z9o5HIr2OqhpD5A3LcqO

Algorithm
---------
1.  Build a hex grid of hexagon centres.
2.  Form kite shapes from the hex grid (each hexagon is divided into 6 kites).
3.  Assemble hat tiles from 8 kites each, in 12 orientations (6 rotations ×
    2 chiralities = 12 variants per grid cell).
4.  Use the Z3 SAT solver to choose a non-overlapping, gap-free subset of hat
    tiles — "at most one per shared point" and "at least one per fully-shared
    point".
5.  Compute the outline segments for each chosen tile.
6.  Convert complex-number coordinates to pixel (x, y) coordinates, scaled
    and centred on the requested canvas size.

The public API returns a list of hat tiles, each described by its polygon
vertices in pixel space.
"""

from __future__ import annotations
import math
from collections import defaultdict
from typing import NamedTuple

import numpy as np
import z3


# ---------------------------------------------------------------------------
# Hat-tile geometry (in hex-lattice complex coordinates)
# ---------------------------------------------------------------------------

def _build_hat_outline(scale: float) -> np.ndarray:
    """
    Return the outline segments of the canonical hat tile at unit scale.

    The hat is assembled from 8 kite shapes on the hex grid.  The outline is
    the set of kite edges that are NOT shared with another kite inside the hat
    (i.e. the exterior boundary edges only).

    Returns
    -------
    np.ndarray, shape (14, 2), dtype complex128
        14 boundary edge segments, each as a pair of complex endpoints.
        Coordinates use the hex-lattice complex convention:
            real axis = x direction (pointing right)
            imag axis = y direction (pointing up)
    """
    six_rotations = np.exp(1j * (np.pi / 3 * np.arange(6)))

    # A single kite: 5 complex vertices (closed polygon, first == last)
    kite = np.array([
        0,
        0.5,
        1 / np.sqrt(3) * np.exp(1j * np.pi / 6),
        0.5 * np.exp(1j * np.pi / 3),
        0,
    ])

    # Build a small hex grid just large enough to assemble the canonical hat
    x, y = np.mgrid[-2:5, -2:5]
    hex_centers = x + 0.5 * y + 1j * np.sqrt(3) / 2 * y
    kites = (kite[None, None, None, :]
             * six_rotations[None, None, :, None]
             + hex_centers[:, :, None, None])

    # 8 kites that make one hat tile (row, col, rotation indices into hex_centers)
    indices = [
        [2, 2, 2, 2, 2, 2, 1, 1],  # row
        [2, 2, 2, 2, 1, 1, 2, 2],  # col
        [1, 2, 3, 4, 0, 1, 5, 4],  # rotation
    ]
    hat_kites = kites[indices[0], indices[1], indices[2], :]  # (8, 5)

    hat_kites = np.round(hat_kites, 8)

    # All directed edges of all kites
    segments = np.concatenate(
        [hat_kites[:, 1:, None], hat_kites[:, :-1, None]], axis=2
    ).reshape(-1, 2)

    # Outline = edges that do NOT appear reversed (i.e. not interior shared edges)
    reversed_segs = set((seg[1], seg[0]) for seg in segments)
    outline = np.array([s for s in segments if tuple(s) not in reversed_segs])
    # outline shape: (14, 2)
    return outline * scale


def generate_hat_tiling(
    canvas_w: float,
    canvas_h: float,
    tile_size: float,
) -> list[np.ndarray]:
    """
    Generate hat tile placements that cover a canvas of canvas_w × canvas_h px.

    Parameters
    ----------
    canvas_w, canvas_h : float
        Canvas dimensions in pixels.
    tile_size : float
        Approximate pixel size for one hex-lattice unit.  Larger values produce
        bigger (and fewer) tiles; smaller values produce smaller (and more) tiles.

    Returns
    -------
    list of np.ndarray, each shape (N_vertices, 2), dtype float64
        Polygon vertices for each hat tile in pixel space (x right, y down),
        centred on the canvas.  Vertices are ordered and closed
        (first vertex == last vertex is NOT repeated; use as open polygon).
    """
    # The Colab reference uses grid_size=12 which yields ~98 tiles on a hex
    # patch roughly 10 units across.  We scale those tiles to fill the canvas.
    # Cap grid_size to keep Z3 tractable (≤16 → ≤16*16*12 ≈ 3072 candidates).
    hex_unit = tile_size  # pixels per hex lattice unit (after scaling)
    grid_size = 12        # fixed: matches the Colab reference

    six_rotations = np.exp(1j * (np.pi / 3 * np.arange(6)))

    # ── Build hex grid ───────────────────────────────────────────────────────
    x, y = np.mgrid[-2:grid_size - 2, -2:grid_size - 2]
    hexagon_centers = x + 0.5 * y + 1j * np.sqrt(3) / 2 * y  # (G, G)

    # ── Kites ────────────────────────────────────────────────────────────────
    kite = np.array([
        0,
        0.5,
        1 / np.sqrt(3) * np.exp(1j * np.pi / 6),
        0.5 * np.exp(1j * np.pi / 3),
        0,
    ])
    kites = (kite[None, None, None, :]
             * six_rotations[None, None, :, None]
             + hexagon_centers[:, :, None, None])  # (G, G, 6, 5)

    # ── Hat tiles (8 kites each, 12 orientations per cell) ──────────────────
    indices = [
        [2, 2, 2, 2, 2, 2, 1, 1],
        [2, 2, 2, 2, 1, 1, 2, 2],
        [1, 2, 3, 4, 0, 1, 5, 4],
    ]
    # Canonical hat kites (in local frame, before rotation/reflection)
    hat_kites_local = kites[indices[0], indices[1], indices[2], :]  # (8, 5)

    # Apply 6 rotations + 6 reflections → 12 orientations
    hats = hat_kites_local[None, :, :] * six_rotations[:, None, None]  # (6, 8, 5)
    reflected = np.real(hats) - 1j * np.imag(hats)                     # (6, 8, 5)
    hats = np.concatenate([hats, reflected], axis=0)                    # (12, 8, 5)

    # Place all 12 orientations at every hex centre
    hats = (hats[None, None, :, :, :]
            + hexagon_centers[:, :, None, None, None])  # (G, G, 12, 8, 5)
    hats = np.reshape(hats, (-1, 8, 5))  # (G*G*12, 8, 5)

    # ── Z3 SAT: choose non-overlapping tiles ─────────────────────────────────
    hat_centers = np.round(np.mean(hats, axis=-1), 2)  # (N, 8) kite centres

    hats_with_point: dict = defaultdict(list)
    for hat_idx, centers in enumerate(hat_centers):
        for loc in centers:
            hats_with_point[loc].append(hat_idx)

    max_pop = max(len(v) for v in hats_with_point.values())
    full_points = [p for p, v in hats_with_point.items() if len(v) == max_pop]
    all_points  = list(hats_with_point.keys())

    hat_present = [z3.Bool(f"hat{i}") for i in range(len(hats))]
    solver = z3.Solver()

    # At most one hat per shared kite centre
    for p in all_points:
        group = [hat_present[i] for i in hats_with_point[p]]
        for a in range(len(group)):
            for b in range(a + 1, len(group)):
                solver.add(z3.Not(z3.And(group[a], group[b])))

    # At least one hat at fully-contested points
    for p in full_points:
        solver.add(z3.Or([hat_present[i] for i in hats_with_point[p]]))

    solver.check()
    model = solver.model()
    chosen = np.array([z3.is_true(model[h]) for h in hat_present])

    # ── Compute outline polygons for chosen tiles ────────────────────────────
    # Use the canonical (un-rounded) hat_kites for the outline computation
    hat_kites_r = np.round(hat_kites_local, 8)
    segs = np.concatenate(
        [hat_kites_r[:, 1:, None], hat_kites_r[:, :-1, None]], axis=2
    ).reshape(-1, 2)
    rev = set((s[1], s[0]) for s in segs)
    outline_local = np.array([s for s in segs if tuple(s) not in rev])  # (14, 2)

    # Apply 12 orientations + translate to hex centres
    outlines = outline_local[None, :, :] * six_rotations[:, None, None]
    outlines_r = np.real(outlines) - 1j * np.imag(outlines)
    outlines = np.concatenate([outlines, outlines_r], axis=0)  # (12, 14, 2)
    outlines = (outlines[None, None, :, :, :]
                + hexagon_centers[:, :, None, None, None])  # (G, G, 12, 14, 2)
    outlines = np.reshape(outlines, (-1, outline_local.shape[0], 2))  # (N, 14, 2)

    chosen_outlines = outlines[chosen]  # (K, 14, 2) complex

    # ── Convert complex → pixel (x, y) arrays, scale and centre ─────────────
    # Convention: real → x (right), imag → y (down in screen coords)
    # The Colab plots with imag as x and real as y; we follow that convention
    # so x = imag part, y = real part (matches screen coords with y pointing down)

    # Collect all vertices to find bounding box
    all_verts = chosen_outlines.reshape(-1)
    raw_xs = all_verts.imag  # screen x
    raw_ys = all_verts.real  # screen y

    raw_cx = (raw_xs.min() + raw_xs.max()) / 2.0
    raw_cy = (raw_ys.min() + raw_ys.max()) / 2.0

    # Scale: fit the tiling to cover the canvas.
    # The tiling natural span in each direction:
    span_x = (raw_xs.max() - raw_xs.min())
    span_y = (raw_ys.max() - raw_ys.min())

    # Use tile_size directly as the hex unit scale factor.
    # (tile_size pixels per hex-lattice unit)
    scale = hex_unit  # pixels per unit

    cx_target = canvas_w / 2.0
    cy_target = canvas_h / 2.0

    # Build list of polygon vertex arrays in pixel space
    tiles: list[np.ndarray] = []
    for outline_segs in chosen_outlines:
        # Extract ordered polygon vertices from the 14 unordered segments
        # Each segment: [pt_a, pt_b] as complex
        # Build a dict of adjacency to walk the polygon
        seg_list = [(s[0], s[1]) for s in outline_segs]
        adj: dict = defaultdict(list)
        for a, b in seg_list:
            adj[a].append(b)

        # Walk from the first vertex
        start = seg_list[0][0]
        poly_c = [start]
        current = start
        for _ in range(len(seg_list)):
            nexts = adj[current]
            if not nexts:
                break
            nxt = nexts[0]
            if nxt == start:
                break
            poly_c.append(nxt)
            current = nxt

        poly = np.array(poly_c)
        # Apply: x = imag, y = real, scale, centre
        px = poly.imag * scale + (cx_target - raw_cx * scale)
        py = poly.real * scale + (cy_target - raw_cy * scale)
        tiles.append(np.stack([px, py], axis=1))

    return tiles
