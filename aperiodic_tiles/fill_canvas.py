"""
fill_canvas.py
==============
Provides fill_canvas() — generates an aperiodic hat-tile layout that covers a
rectangular canvas and returns a data structure that can be passed directly to
render_canvas() and assign_tile_heights().

Output structure (a "canvas dict")
-----------------------------------
{
    "tile_size":    float,  # hex-lattice unit length in pixels
    "canvas_width": float,
    "canvas_height": float,
    "tiles": [
        {
            "vertices": [[x0,y0], [x1,y1], ..., [xN,yN]],
                        # ordered polygon vertices in canvas pixel coords
                        # (x right, y down); NOT closed (last != first)
        },
        ...
    ]
}
"""

from __future__ import annotations
from typing import Any

import numpy as np

from .hat_tiling import generate_hat_tiling


def fill_canvas(
    width: float,
    height: float,
    tile_size: float,
    gap: float = 0.0,
) -> dict[str, Any]:
    """
    Generate an aperiodic hat-tile layout that covers a rectangular canvas.

    Uses the same kite-assembly + Z3 SAT approach as the reference Colab
    notebook (https://colab.research.google.com/drive/1cBs3HGFQ6cz8z9o5HIr2OqhpD5A3LcqO):
    build candidate hat tiles on a hex grid, use the SAT solver to select a
    non-overlapping, gap-free subset, then scale and centre them on the canvas.

    Parameters
    ----------
    width : float
        Width of the canvas in pixels.
    height : float
        Height of the canvas in pixels.
    tile_size : float
        Pixel length of one hex-lattice unit edge.  Larger values produce
        bigger (and fewer) tiles; smaller values produce smaller (and more).
    gap : float, optional
        Gap between adjacent tiles in pixels.  Each tile polygon is shrunk
        toward its centroid by this many pixels.  0 (default) means tiles
        share edges exactly (no gap).  Typical values: 1–4 px.

    Returns
    -------
    dict
        A "canvas" dictionary with keys ``tile_size``, ``canvas_width``,
        ``canvas_height``, ``gap``, and ``tiles``.  Each entry in ``tiles``
        has a ``vertices`` key containing a list of [x, y] pixel coordinates
        forming the ordered polygon of that tile.
        This dict is the expected input to render_canvas() and
        assign_tile_heights().
    """
    raw_tiles: list[np.ndarray] = generate_hat_tiling(
        canvas_w=width,
        canvas_h=height,
        tile_size=tile_size,
    )

    # Filter: keep only tiles whose centroid is within a generous margin of
    # the canvas so the full canvas is covered but we don't carry excessive
    # off-screen tiles.
    margin = tile_size * 6
    tiles_out: list[dict[str, Any]] = []
    for verts in raw_tiles:
        cx = verts[:, 0].mean()
        cy = verts[:, 1].mean()
        if (
            -margin <= cx <= width + margin
            and -margin <= cy <= height + margin
        ):
            if gap > 0:
                # Shrink each vertex toward the centroid by `gap` pixels.
                # The inset factor scales the distance from centroid.
                # We compute the mean edge length to get a proportional inset.
                edge_lengths = np.linalg.norm(
                    np.diff(verts, axis=0, append=verts[:1]), axis=1
                )
                mean_edge = edge_lengths.mean()
                # inset_fraction shrinks by `gap` px relative to centroid dist
                centroid = np.array([cx, cy])
                # direction from centroid to each vertex
                dirs = verts - centroid
                dists = np.linalg.norm(dirs, axis=1, keepdims=True)
                dists = np.where(dists < 1e-9, 1.0, dists)
                unit_dirs = dirs / dists
                shrunk = verts - unit_dirs * gap
                tiles_out.append({"vertices": shrunk.tolist()})
            else:
                tiles_out.append({"vertices": verts.tolist()})

    return {
        "tile_size":    tile_size,
        "canvas_width": width,
        "canvas_height": height,
        "gap":          gap,
        "tiles":        tiles_out,
    }
