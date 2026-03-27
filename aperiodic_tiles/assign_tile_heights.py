"""
assign_tile_heights.py
======================
Provides assign_tile_heights() — takes a canvas dict returned by fill_canvas()
and augments each tile with a scalar height and a surface-normal slant vector,
producing a "panel" dict that can be passed to render_panel().

Height and tilt are driven by one of three procedural modes:

    radial_ripple  — concentric sine-wave rings expanding from the canvas
                     centre; the slope of the wave determines the tilt.
    linear_ripple  — parallel sine-wave bands travelling in a user-specified
                     direction (angle); useful for wave-like surface profiles.
    noise          — a deterministic sin/cos pattern sampled at each tile's
                     centroid; produces a grid-aligned undulation with no tilt.

Output structure (a "panel" dict)
----------------------------------
Extends the canvas dict with:
    • tile["height"]  float  — extrusion height at the tile's centroid (px).
    • tile["slant"]   [nx, ny, nz]  — unnormalised surface normal of the top
                                      face; passed to render_panel._top_vertex().
    • panel["type"]   "panel"  — marker used by downstream nodes.
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
    mode: str = "radial_ripple",
    frequency: float = 0.05,
    tilt_strength: float = 0.2,
    angle: float = 0.0,
    seed: int | None = None,
) -> dict[str, Any]:
    
    panel = copy.deepcopy(canvas)
    
    width = canvas.get("canvas_width", 1000.0)
    height_canv = canvas.get("canvas_height", 1000.0)
    center_x, center_y = width / 2, height_canv / 2
    
    rad_a = math.radians(angle)
    cos_a, sin_a = math.cos(rad_a), math.sin(rad_a)
    h_range = max_height - min_height

    for tile in panel["tiles"]:
        verts = tile["vertices"]
        avg_x = sum(v[0] for v in verts) / len(verts)
        avg_y = sum(v[1] for v in verts) / len(verts)
        
        # Default state (Flat)
        slant = [0.0, 0.0, 1.0]
        h_val = min_height

        if mode == "radial_ripple":
            dx, dy = avg_x - center_x, avg_y - center_y
            d = math.sqrt(dx**2 + dy**2)
            val = (math.sin(d * frequency) + 1) / 2
            h_val = min_height + (val * h_range)
            
            slope = math.cos(d * frequency) * tilt_strength
            nx = (dx / d * slope) if d > 0 else 0
            ny = (dy / d * slope) if d > 0 else 0
            slant = [nx, ny, 1.0]

        elif mode == "linear_ripple":
            projected = avg_x * cos_a + avg_y * sin_a
            val = (math.sin(projected * frequency) + 1) / 2
            h_val = min_height + (val * h_range)
            
            slope = math.cos(projected * frequency) * tilt_strength
            slant = [cos_a * slope, sin_a * slope, 1.0]

        elif mode == "noise":
            # Coherent height variation
            val = (math.sin(avg_x * frequency) + math.cos(avg_y * frequency)) / 2
            val = (val + 1) / 2
            h_val = min_height + (val * h_range)
            slant = [0.0, 0.0, 1.0]

        tile["height"] = float(h_val)
        tile["slant"] = slant

    panel["type"] = "panel"
    return panel
