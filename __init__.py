from .hat_tiling import HatTilingNode
from .fill_canvas import FillCanvasNode
from .assign_tile_heights import AssignTileHeightsNode
from .render_canvas import RenderCanvasNode
from .render_panel import RenderPanel3DNode

NODE_CLASS_MAPPINGS = {
    "HatTilingNode": HatTilingNode,
    "FillCanvasNode": FillCanvasNode,
    "AssignTileHeightsNode": AssignTileHeightsNode,
    "RenderCanvasNode": RenderCanvasNode,
    "RenderPanel3DNode": RenderPanel3DNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HatTilingNode": "1. Hat Tiling Generator",
    "FillCanvasNode": "2. Aperiodic Fill Canvas",
    "AssignTileHeightsNode": "3. Assign Tile Heights & Slant",
    "RenderCanvasNode": "4. Render 2D Layout",
    "RenderPanel3DNode": "5. Render 3D Panel",
}