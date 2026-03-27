"""
__init__.py
===========
Package entry-point for the ComfyUI-AperiodicTiles custom node set.

Imports all node classes from nodes.py and re-exports the two dicts that
ComfyUI requires to register and display the nodes:

    NODE_CLASS_MAPPINGS        — maps node ID strings to their Python classes.
    NODE_DISPLAY_NAME_MAPPINGS — maps node ID strings to human-readable labels
                                 shown in the ComfyUI node browser.
"""

from .nodes import (
    AperiodicHatTiling,
    AperiodicFillCanvas,
    AperiodicAssignHeights,
    AperiodicRenderCanvas,
    AperiodicRenderPanel,
    AperiodicExportSTL
)

NODE_CLASS_MAPPINGS = {
    "AperiodicHatTiling": AperiodicHatTiling,
    "AperiodicFillCanvas": AperiodicFillCanvas,
    "AperiodicAssignHeights": AperiodicAssignHeights,
    "AperiodicRenderCanvas": AperiodicRenderCanvas,
    "AperiodicRenderPanel": AperiodicRenderPanel,
    "AperiodicExportSTL": AperiodicExportSTL
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AperiodicHatTiling": "Hat Tiling Generator",
    "AperiodicFillCanvas": "Fill Canvas (2D Layout)",
    "AperiodicAssignHeights": "Assign Tile Heights & Tilt",
    "AperiodicRenderCanvas": "Render 2D Canvas (HTML)",
    "AperiodicRenderPanel": "Render 3D Panel (HTML)",
    "AperiodicExportSTL": "Export 3D Panel (STL)"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
