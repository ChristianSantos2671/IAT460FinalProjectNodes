"""
nodes.py
========
Defines all ComfyUI custom nodes for the Aperiodic Tiles package.

Node pipeline (left to right):

    AperiodicHatTiling      -- generates raw hat-tile geometry on a hex lattice.
    AperiodicFillCanvas     -- filters and scales tiles to fill a pixel canvas,
                              returning a canvas dict.
    AperiodicAssignHeights  -- adds height and surface-tilt data to every tile,
                              producing a panel dict ready for 3-D output.
    AperiodicRenderCanvas   -- renders the 2-D tile layout as an interactive
                              Plotly HTML file (via render_canvas.py).
    AperiodicRenderPanel    -- renders the 3-D extruded panel as an interactive
                              Plotly HTML file (via render_panel.py).
    AperiodicExportSTL      -- exports the 3-D panel as a binary STL file for
                              manufacturing / 3-D printing (via export_stl.py).
    AperiodicExportMouldSTL -- exports a casting mould as a binary STL file:
                              the geometric negative of the columns, forming a
                              block with cavities into which liquid material can
                              be poured to produce the finished panel cast
                              (via export_mould_stl.py).

All nodes are registered in NODE_CLASS_MAPPINGS at the bottom of this file and
re-exported through __init__.py so ComfyUI discovers them automatically.
"""

import os
import numpy as np
import folder_paths
from .aperiodic_tiles import (
    hat_tiling,
    fill_canvas,
    assign_tile_heights,
    render_canvas,
    render_panel,
    export_stl,
    export_mould_stl as export_mould_stl_mod,
)

CAT = "Aperiodic Tiles"


class AperiodicHatTiling:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "width": ("FLOAT", {"default": 1000.0}),
                "height": ("FLOAT", {"default": 1000.0}),
                "tile_size": ("FLOAT", {"default": 50.0}),
            }
        }
    RETURN_TYPES = ("HAT_DATA",)
    FUNCTION = "execute"
    CATEGORY = CAT

    def execute(self, width, height, tile_size):
        tiles = hat_tiling.generate_hat_tiling(
            canvas_w=width,
            canvas_h=height,
            tile_size=tile_size
        )
        return ({"tiles": tiles, "w": width, "h": height, "s": tile_size},)


class AperiodicFillCanvas:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "hat_data": ("HAT_DATA",),
                "gap": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 20.0}),
            }
        }
    RETURN_TYPES = ("TILE_POLYGONS",)
    FUNCTION = "execute"
    CATEGORY = CAT

    def execute(self, hat_data, gap):
        canvas_dict = fill_canvas.fill_canvas(
            width=hat_data["w"],
            height=hat_data["h"],
            tile_size=hat_data["s"],
            gap=gap
        )
        return (canvas_dict,)


class AperiodicAssignHeights:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_polygons": ("TILE_POLYGONS",),
                "min_height": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "max_height": ("FLOAT", {"default": 50.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "mode": (["radial_ripple", "linear_ripple", "noise"], {"default": "radial_ripple"}),
                "frequency": ("FLOAT", {"default": 0.05, "min": 0.001, "max": 0.5, "step": 0.001}),
                "tilt_strength": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 5.0, "step": 0.01}),
                "angle": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 360.0, "step": 1.0}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("TILE_HEIGHT_DATA",)
    FUNCTION = "execute"
    CATEGORY = CAT

    def execute(self, tile_polygons, min_height, max_height, mode, frequency, tilt_strength, angle, seed):
        tile_height_data = assign_tile_heights.assign_tile_heights(
            canvas=tile_polygons,
            min_height=min_height,
            max_height=max_height,
            mode=mode,
            frequency=frequency,
            tilt_strength=tilt_strength,
            angle=angle,
            seed=seed
        )
        return (tile_height_data,)


class AperiodicRenderCanvas:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_polygons": ("TILE_POLYGONS",),
            }
        }
    RETURN_TYPES = ()
    FUNCTION = "execute"
    CATEGORY = CAT
    OUTPUT_NODE = True

    def execute(self, tile_polygons):
        out_path = os.path.join(folder_paths.get_output_directory(), "aperiodic_canvas.html")
        render_canvas.render_canvas(canvas=tile_polygons, show=False, save_path=out_path)
        return {"ui": {"text": [out_path]}}


class AperiodicRenderPanel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_height_data": ("TILE_HEIGHT_DATA",),
                "colour_a":    ("STRING", {"default": "#0d47a1",
                                           "tooltip": "Hex colour for even-indexed tile columns (e.g. #0d47a1). Tall tiles are this colour; short tiles get a light tint."}),
                "colour_b":    ("STRING", {"default": "#bf360c",
                                           "tooltip": "Hex colour for odd-indexed tile columns (e.g. #bf360c)."}),
                "bg_colour":   ("STRING", {"default": "#1a1a2e",
                                           "tooltip": "Hex colour for the page / environment background surrounding the 3-D scene."}),
                "grid_colour": ("STRING", {"default": "#e8e8f0",
                                           "tooltip": "Hex colour applied to all three axis grid planes (X, Y and Z backgrounds)."}),
            }
        }
    RETURN_TYPES = ()
    FUNCTION = "execute"
    CATEGORY = CAT
    OUTPUT_NODE = True

    def execute(self, tile_height_data, colour_a, colour_b, bg_colour, grid_colour):
        out_path = os.path.join(folder_paths.get_output_directory(), "aperiodic_panel_3d.html")
        render_panel.render_panel(
            panel=tile_height_data,
            show=False,
            save_html=out_path,
            colour_a=colour_a,
            colour_b=colour_b,
            bg_colour=bg_colour,
            grid_colour=grid_colour,
        )
        return {"ui": {"text": [out_path]}}


class AperiodicExportSTL:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_height_data": ("TILE_HEIGHT_DATA",),
                "filename": ("STRING", {"default": "aperiodic_tiling.stl"}),
                "base_thickness": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 50.0, "step": 0.1}),
                "base_margin": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 100.0, "step": 0.5}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.001, "max": 100.0, "step": 0.001}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "execute"
    CATEGORY = CAT
    OUTPUT_NODE = True

    def execute(self, tile_height_data, filename, base_thickness, base_margin, scale):
        if not filename.lower().endswith(".stl"):
            filename += ".stl"
        out_path = os.path.join(folder_paths.get_output_directory(), filename)
        try:
            saved = export_stl.export_panel_stl(
                panel=tile_height_data,
                out_path=out_path,
                base_thickness=base_thickness,
                base_margin=base_margin,
                scale=scale,
            )
            return {"ui": {"text": [f"Saved to: {saved} (scale={scale})"]}}
        except Exception as exc:
            return {"ui": {"text": [f"Error: {exc}"]}}


class AperiodicExportMouldSTL:
    """
    Exports a casting mould STL -- a rectangular shell with one cavity per
    tile column, shaped as the geometric negative of the aperiodic panel.

    The mould is printed open-face-up.  Liquid is poured in, fills the
    cavities (forming the columns) plus a connecting base layer.  After
    hardening and demoulding the result is the export_stl.py shape.

    Parameters
    ----------
    wall_thickness : float
        Uniform skin thickness (mm) of the mould:
          - Outer side walls extend the tile bounding box by this amount.
          - Bottom buffer sits below the deepest column-tip cavity by this amount.
        Use larger values for high-temperature materials such as molten metal.
    base_margin : float
        Extra gap (mm) between the tile footprint and the inner face of the
        mould walls (matches the base_margin used in the panel STL export).
    base_thickness : float
        Height (mm) of the short raised "dam collar" walls that extend above
        the mould top face.  Pour extra liquid to this depth above the tile
        holes to form the connecting base plate of the finished cast.  When
        flipped right-side-up, this layer becomes the flat base joining all
        columns together.  Set to 0 to omit the collar.
    scale : float
        Uniform scale applied to every coordinate before export.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_height_data": ("TILE_HEIGHT_DATA",),
                "filename": ("STRING", {"default": "aperiodic_mould.stl"}),
                "wall_thickness": ("FLOAT", {"default": 10.0, "min": 1.0, "max": 100.0, "step": 0.1}),
                "base_margin": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 100.0, "step": 0.5}),
                "base_thickness": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.001, "max": 100.0, "step": 0.001}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "execute"
    CATEGORY = CAT
    OUTPUT_NODE = True

    def execute(self, tile_height_data, filename, wall_thickness, base_margin, base_thickness, scale):
        if not filename.lower().endswith(".stl"):
            filename += ".stl"
        out_path = os.path.join(folder_paths.get_output_directory(), filename)
        try:
            saved = export_mould_stl_mod.export_mould_stl(
                panel=tile_height_data,
                out_path=out_path,
                wall_thickness=wall_thickness,
                base_margin=base_margin,
                base_thickness=base_thickness,
                scale=scale,
            )
            return {"ui": {"text": [f"Mould saved to: {saved} (scale={scale})"]}}
        except Exception as exc:
            return {"ui": {"text": [f"Error: {exc}"]}}


# Mapping for ComfyUI to recognise the nodes
NODE_CLASS_MAPPINGS = {
    "AperiodicHatTiling": AperiodicHatTiling,
    "AperiodicFillCanvas": AperiodicFillCanvas,
    "AperiodicAssignHeights": AperiodicAssignHeights,
    "AperiodicRenderCanvas": AperiodicRenderCanvas,
    "AperiodicRenderPanel": AperiodicRenderPanel,
    "AperiodicExportSTL": AperiodicExportSTL,
    "AperiodicExportMouldSTL": AperiodicExportMouldSTL,
}
