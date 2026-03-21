import numpy as np

class FillCanvasNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"raw_tiles": ("RAW_TILES",), "width": ("FLOAT", {"default": 1920.0}), "height": ("FLOAT", {"default": 1080.0}), "tile_size": ("FLOAT", {"default": 40.0}), "gap": ("FLOAT", {"default": 0.0})}}
    RETURN_TYPES = ("TILING_DATA",)
    FUNCTION = "execute"
    CATEGORY = "Aperiodic Tiles"

    def execute(self, raw_tiles, width, height, tile_size, gap):
        all_verts = np.concatenate(raw_tiles)
        offset_x = (width / 2.0) - ((all_verts[:, 0].min() + all_verts[:, 0].max()) / 2.0)
        offset_y = (height / 2.0) - ((all_verts[:, 1].min() + all_verts[:, 1].max()) / 2.0)
        tiles_out = []
        for verts in raw_tiles:
            v = verts.copy()
            v[:, 0] += offset_x; v[:, 1] += offset_y
            cx, cy = v[:, 0].mean(), v[:, 1].mean()
            if gap > 0:
                dirs = v - [cx, cy]
                dists = np.linalg.norm(dirs, axis=1, keepdims=True)
                v = v - (dirs / np.where(dists < 1e-9, 1.0, dists)) * gap
            tiles_out.append({"vertices": v.tolist()})
        return ({"tile_size": tile_size, "canvas_width": width, "canvas_height": height, "tiles": tiles_out},)