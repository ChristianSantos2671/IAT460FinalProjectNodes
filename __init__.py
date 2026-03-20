# __init__.py
import subprocess
import sys
import importlib

# Dependency check
REQS = ["z3-solver", "matplotlib", "numpy"]

def install_reqs():
    for req in REQS:
        try:
            importlib.import_module(req.replace('-', '_'))
        except ImportError:
            print(f"[AperiodicTiles] Installing {req}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])

install_reqs()

# Match these names to the classes inside your .py files
from .hat_tiling import HatTilingNode
from .fill_canvas import FillCanvasNode
from .assign_tile_heights import AperiodicAssignHeights
from .render_canvas import RenderCanvasNode
from .render_panel import RenderPanelNode

NODE_CLASS_MAPPINGS = {
    "HatTilingNode": HatTilingNode,
    "FillCanvasNode": FillCanvasNode,
    "AperiodicAssignHeights": AperiodicAssignHeights,
    "RenderCanvasNode": RenderCanvasNode,
    "RenderPanelNode": RenderPanelNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HatTilingNode": "Aperiodic: Hat Tiling",
    "FillCanvasNode": "Aperiodic: Fill Canvas",
    "AperiodicAssignHeights": "Aperiodic: Assign Heights",
    "RenderCanvasNode": "Aperiodic: Render HTML Canvas",
    "RenderPanelNode": "Aperiodic: Render HTML Panel",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']