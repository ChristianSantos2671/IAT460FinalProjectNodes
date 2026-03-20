import sys
import os

# Adjust path to import your original logic if needed
sys.path.append(os.path.dirname(__file__))

class HatTilingNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "iterations": ("INT", {"default": 3, "min": 1, "max": 10}),
                "scale": ("FLOAT", {"default": 1.0, "step": 0.1}),
            },
        }

    RETURN_TYPES = ("TILING_DATA",)
    FUNCTION = "generate"
    CATEGORY = "Aperiodic/Generation"

    def generate(self, iterations, scale):
        # Logic from your original hat_tiling.py
        # Result should be the object/list passed to fill_canvas
        tiling_data = {"iterations": iterations, "scale": scale} 
        return (tiling_data,)

NODE_CLASS_MAPPINGS = {"HatTilingNode": HatTilingNode}