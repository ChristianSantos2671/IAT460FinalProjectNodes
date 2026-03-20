import subprocess
import sys
import importlib

# List the requirements your AperiodicTiles project needs
REQS = ["z3-solver", "matplotlib"]

def install_reqs():
    for req in REQS:
        try:
            importlib.import_module(req.split('-')[0]) # Simple check for z3 or matplotlib
        except ImportError:
            print(f"[AperiodicTiles] Installing {req}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])

# Execute installation check on startup
install_reqs()

# Now import the node mappings from your separate files
from .hat_tiling import HatTilingNode
from .fill_canvas import FillCanvasNode
from .assign_tile_heights import AssignHeightsNode
from .render_canvas import RenderCanvasNode
from .render_panel import RenderPanelNode

NODE_CLASS_MAPPINGS = {
    "HatTilingNode": HatTilingNode,
    "FillCanvasNode": FillCanvasNode,
    "AssignHeightsNode": AssignHeightsNode,
    "RenderCanvasNode": RenderCanvasNode,
    "RenderPanelNode": RenderPanelNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HatTilingNode": "Aperiodic: Hat Tiling",
    "FillCanvasNode": "Aperiodic: Fill Canvas",
    "AssignHeightsNode": "Aperiodic: Assign Heights",
    "RenderCanvasNode": "Aperiodic: Render HTML Canvas",
    "RenderPanelNode": "Aperiodic: Render HTML Panel",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']