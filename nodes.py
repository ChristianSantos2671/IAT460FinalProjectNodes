"""
nodes.py
========
Defines all ComfyUI custom nodes for the Aperiodic Tiles package.

Node pipeline (left to right):

    AperiodicHatTiling      — generates raw hat-tile geometry on a hex lattice.
    AperiodicFillCanvas     — filters and scales tiles to fill a pixel canvas,
                              returning a canvas dict and bounding-box bounds.
    AperiodicAssignHeights  — adds height and surface-tilt data to every tile,
                              producing a panel dict ready for 3-D output.
    AperiodicRenderCanvas   — renders the 2-D tile layout as an interactive
                              Plotly HTML file (via render_canvas.py).
    AperiodicRenderPanel    — renders the 3-D extruded panel as an interactive
                              Plotly HTML file (via render_panel.py).
    AperiodicExportSTL      — exports the 3-D panel as a binary STL file for
                              manufacturing / 3-D printing.

All nodes are registered in NODE_CLASS_MAPPINGS at the bottom of this file and
re-exported through __init__.py so ComfyUI discovers them automatically.
"""

import os
import sys
import numpy as np
import folder_paths
from pathlib import Path
from .aperiodic_tiles import hat_tiling, fill_canvas, assign_tile_heights, render_canvas, render_panel

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
        # Calls the function from hat_tiling.py
        tiles = hat_tiling.generate_hat_tiling(
            canvas_w=width, 
            canvas_h=height, 
            tile_size=tile_size
        )
        # Wrap data for the next node
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
    RETURN_TYPES = ("TILE_POLYGONS", "RECT_BOUNDS")
    FUNCTION = "execute"
    CATEGORY = CAT

    def execute(self, hat_data, gap):
        # Calls the function from fill_canvas.py
        canvas_dict = fill_canvas.fill_canvas(
            width=hat_data["w"],
            height=hat_data["h"],
            tile_size=hat_data["s"],
            gap=gap
        )
        bounds = [hat_data["w"], hat_data["h"]]
        return (canvas_dict, bounds)

class AperiodicAssignHeights:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_polygons": ("TILE_POLYGONS",),
                "min_height": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "max_height": ("FLOAT", {"default": 50.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                # Removed "random" from the list below
                "mode": (["radial_ripple", "linear_ripple", "noise"], {"default": "radial_ripple"}),
                "frequency": ("FLOAT", {"default": 0.05, "min": 0.001, "max": 0.5, "step": 0.001}),
                "tilt_strength": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 5.0, "step": 0.01}),
                "angle": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 360.0, "step": 1.0}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("TILE_HEIGHT_DATA",)
    FUNCTION = "execute"
    CATEGORY = "Aperiodic Tiles"

    def execute(self, tile_polygons, min_height, max_height, mode, frequency, tilt_strength, angle, seed):
        from .aperiodic_tiles import assign_tile_heights
        
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
    RETURN_TYPES = ("HTML_PATH",)
    FUNCTION = "execute"
    CATEGORY = CAT
    OUTPUT_NODE = True

    def execute(self, tile_polygons):
        out_path = os.path.join(folder_paths.get_output_directory(), "aperiodic_canvas.html")
        # Calls render_canvas with the full dict and save_path
        render_canvas.render_canvas(
            canvas=tile_polygons,
            show=False,
            save_path=out_path
        )
        return {"ui": {"text": [out_path]}, "result": (out_path,)}

class AperiodicRenderPanel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_height_data": ("TILE_HEIGHT_DATA",),
            }
        }
    RETURN_TYPES = ("HTML_PATH",)
    FUNCTION = "execute"
    CATEGORY = CAT
    OUTPUT_NODE = True

    def execute(self, tile_height_data):
        out_path = os.path.join(folder_paths.get_output_directory(), "aperiodic_panel_3d.html")
        render_panel.render_panel(
            panel=tile_height_data,
            show=False,
            save_html=out_path
        )
        return {"ui": {"text": [out_path]}, "result": (out_path,)}

class AperiodicExportSTL:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tile_height_data": ("TILE_HEIGHT_DATA",),
                "filename": ("STRING", {"default": "aperiodic_tiling.stl"}),
                "base_thickness": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 20.0, "step": 0.1}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.001, "max": 100.0, "step": 0.001}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "execute"
    CATEGORY = "Aperiodic Tiles"
    OUTPUT_NODE = True

    def execute(self, tile_height_data, filename, base_thickness, scale):
        # --- ROBUST IMPORT FIX ---
        # Manually add the current directory to sys.path to bypass the hyphen-path error
        current_dir = str(Path(__file__).parent.resolve())
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        
        try:
            # Import from the injected path
            import render_panel
            from stl import mesh
        except ImportError as e:
            return {"ui": {"text": [f"Error importing render_panel: {str(e)}"]}, "result": ("",)}

        tiles = tile_height_data["tiles"]
        canvas_w = tile_height_data["canvas_width"]
        canvas_h = tile_height_data["canvas_height"]
        
        all_facets = []

        # 1. Generate the Floor Baseplate
        fx, fy, fz, fi, fj, fk = render_panel._get_baseplate_mesh(
            canvas_w, 
            canvas_h, 
            base_thickness, 
            0.0 
        )
        
        # Apply scaling to the floor vertices
        f_verts = np.column_stack([fx, fy, fz]) * scale
        
        floor_indices = [
            (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
            (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)
        ]
        
        for i, j, k in floor_indices:
            all_facets.append([f_verts[i], f_verts[j], f_verts[k]])

        # 2. Generate each Tile Prism
        for tile in tiles:
            xs, ys, zs, i_f, j_f, k_f = render_panel._build_tile_mesh(tile, 0.0)
            
            # Apply scaling to the tile vertices
            vertices = np.column_stack([xs, ys, zs]) * scale
            
            for i, j, k in zip(i_f, j_f, k_f):
                all_facets.append([vertices[i], vertices[j], vertices[k]])

        # 3. Create the STL Mesh
        num_facets = len(all_facets)
        stl_data = np.zeros(num_facets, dtype=mesh.Mesh.dtype)
        export_mesh = mesh.Mesh(stl_data)

        for i, facet in enumerate(all_facets):
            export_mesh.vectors[i] = facet

        # 4. Save to ComfyUI Output Directory
        if not filename.lower().endswith(".stl"):
            filename += ".stl"
            
        out_path = os.path.join(folder_paths.get_output_directory(), filename)
        export_mesh.save(out_path)

        return {"ui": {"text": [f"Saved to: {out_path} (Scale: {scale})"]}, "result": (out_path,)}

# Mapping for ComfyUI to recognize the nodes
NODE_CLASS_MAPPINGS = {
    "AperiodicHatTiling": AperiodicHatTiling,
    "AperiodicFillCanvas": AperiodicFillCanvas,
    "AperiodicAssignHeights": AperiodicAssignHeights,
    "AperiodicRenderCanvas": AperiodicRenderCanvas,
    "AperiodicRenderPanel": AperiodicRenderPanel,
    "AperiodicExportSTL": AperiodicExportSTL
}
