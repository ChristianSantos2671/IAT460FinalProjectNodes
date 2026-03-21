import os
import numpy as np
import folder_paths
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
                "gap": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 20.0}),
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
                "min_height": ("FLOAT", {"default": 2.0, "min": 0.0}),
                "max_height": ("FLOAT", {"default": 10.0, "min": 0.0}),
                "max_tilt_deg": ("FLOAT", {"default": 30.0, "min": 0.0, "max": 90.0}),
                "seed": ("INT", {"default": 0, "min": 0}),
            }
        }
    RETURN_TYPES = ("TILE_HEIGHT_DATA",)
    FUNCTION = "execute"
    CATEGORY = CAT

    def execute(self, tile_polygons, min_height, max_height, max_tilt_deg, seed):
        # Calls the function from assign_tile_heights.py
        panel_dict = assign_tile_heights.assign_tile_heights(
            canvas=tile_polygons,
            min_height=min_height,
            max_height=max_height,
            max_tilt_deg=max_tilt_deg,
            seed=seed
        )
        return (panel_dict,)

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
            }
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "execute"
    CATEGORY = CAT
    OUTPUT_NODE = True

    def execute(self, tile_height_data, filename):
        from stl import mesh
        tiles = tile_height_data["tiles"]
        all_facets = []

        for tile in tiles:
            # Using the function we just updated above
            xs, ys, zs, i_f, j_f, k_f = render_panel._build_tile_mesh(tile)
            
            # Prepare vertices for numpy-stl
            vertices = np.column_stack([xs, ys, zs])
            for i, j, k in zip(i_f, j_f, k_f):
                all_facets.append([vertices[i], vertices[j], vertices[k]])

        # Create the mesh and save
        stl_mesh = mesh.Mesh(np.zeros(len(all_facets), dtype=mesh.Mesh.dtype))
        for i, facet in enumerate(all_facets):
            stl_mesh.vectors[i] = facet

        out_path = os.path.join(folder_paths.get_output_directory(), filename)
        stl_mesh.save(out_path)
        
        return {"ui": {"text": [out_path]}, "result": (out_path,)}

# Mapping for ComfyUI to recognize the nodes
NODE_CLASS_MAPPINGS = {
    "AperiodicHatTiling": AperiodicHatTiling,
    "AperiodicFillCanvas": AperiodicFillCanvas,
    "AperiodicAssignHeights": AperiodicAssignHeights,
    "AperiodicRenderCanvas": AperiodicRenderCanvas,
    "AperiodicRenderPanel": AperiodicRenderPanel,
    "AperiodicExportSTL": AperiodicExportSTL
}