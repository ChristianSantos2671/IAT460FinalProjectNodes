"""
assign_tile_heights.py
======================
Provides assign_tile_heights() — takes the 2-D canvas description produced by
fill_canvas() and extends each tile into the third dimension by assigning it:
    • a random height  (extruded in the +z direction)
    • a slant vector  (the surface normal of the top face, giving it a tilt)

Output structure (a "panel dict")
----------------------------------
The returned dict is a copy of the input canvas dict with each tile entry
augmented:
{
    "tile_size":  float,
    "canvas_width":  float,
    "canvas_height": float,
    "tiles": [
        {
            "vertices": [[x0,y0], ..., [xN,yN]],  # polygon vertices (unchanged)
            # --- new 3-D fields ---
            "height":  float,           # extrusion height in the +z direction
            "slant":   [float, float, float],  # unit normal of the top face
                                                # (points roughly upward in +z)
        },
        ...
    ]
}

The slant vector is chosen as follows:
    1. A random tilt magnitude θ ∈ [0°, max_tilt_deg] is drawn.
    2. A random azimuth φ ∈ [0°, 360°) is drawn.
    3. The unit normal is  n = (sin θ cos φ,  sin θ sin φ,  cos θ).
   This means the top surface tilts by at most max_tilt_deg away from
   horizontal.  When θ = 0 the top face is perfectly flat (normal = (0, 0, 1)).
"""

from __future__ import annotations
import copy
import math
import random
from typing import Any


def assign_tile_heights(
    canvas: dict[str, Any],
    min_height: float,
    max_height: float,
    max_tilt_deg: float = 30.0,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Assign random heights and slant vectors to each tile in a canvas layout.

    Parameters
    ----------
    canvas : dict
        The canvas dictionary returned by fill_canvas().
    min_height : float
        Minimum extrusion height for a tile (same units as pixel coordinates).
    max_height : float
        Maximum extrusion height.
    max_tilt_deg : float, optional
        Maximum tilt of the top surface away from horizontal (degrees).
        0 → all tops are perfectly flat.  Default is 30°.
    seed : int or None, optional
        Random seed for reproducibility.  If None the result is non-
        deterministic.

    Returns
    -------
    dict
        A "panel" dictionary: a deep copy of *canvas* with ``height`` and
        ``slant`` added to each tile entry.

    Raises
    ------
    ValueError
        If min_height > max_height or either is negative.
    """
    if min_height < 0 or max_height < 0:
        raise ValueError("Heights must be non-negative.")
    if min_height > max_height:
        raise ValueError(
            f"min_height ({min_height}) must be <= max_height ({max_height})."
        )
    if max_tilt_deg < 0 or max_tilt_deg > 90:
        raise ValueError("max_tilt_deg must be in [0, 90].")

    rng = random.Random(seed)
    panel = copy.deepcopy(canvas)

    for tile in panel["tiles"]:
        # height
        tile["height"] = rng.uniform(min_height, max_height)

        # slant (top-face unit normal)
        theta = math.radians(rng.uniform(0.0, max_tilt_deg))
        phi   = math.radians(rng.uniform(0.0, 360.0))
        tile["slant"] = [
            math.sin(theta) * math.cos(phi),
            math.sin(theta) * math.sin(phi),
            math.cos(theta),
        ]

    panel["type"]        = "panel"
    panel["min_height"]  = min_height
    panel["max_height"]  = max_height
    panel["max_tilt_deg"] = max_tilt_deg

    return panel
