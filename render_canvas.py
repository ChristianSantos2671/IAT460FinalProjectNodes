import os, folder_paths, matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection

class RenderCanvasNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"height_data": ("HEIGHT_DATA",), "filename": ("STRING", {"default": "tiling_2d.png"})}}
    OUTPUT_NODE = True
    RETURN_TYPES = ()
    FUNCTION = "render"
    CATEGORY = "Aperiodic Tiles"

    def render(self, height_data, filename):
        tiles, w, h = height_data["tiles"], height_data["canvas_width"], height_data["canvas_height"]
        fig, ax = plt.subplots(figsize=(w/100, h/100))
        ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.axis("off")
        patches = [MplPolygon(tile["vertices"], closed=True) for tile in tiles]
        ax.add_collection(PatchCollection(patches, facecolor="#5B8DB8", edgecolor="#1a1a2e", linewidth=0.6))
        path = os.path.join(folder_paths.get_output_directory(), filename)
        fig.savefig(path, bbox_inches="tight", pad_inches=0); plt.close(fig)
        return {"ui": {"text": [f"Saved to {path}"]}}