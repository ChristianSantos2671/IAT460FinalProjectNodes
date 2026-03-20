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
    CATEGORY = "Aperiodic"

    def generate(self, iterations):
        # IMPORTANT: Replace this with your actual generation logic
        # For testing, we'll create one dummy 'Hat' tile (a quadrilateral)
        sample_tile = [[0, 0], [100, 0], [100, 100], [0, 100]]
        tiles = [sample_tile for _ in range(5)] # Create 5 tiles
        
        # This dictionary is what 'TILING_DATA' actually is
        return ({"tiles": tiles, "iterations": iterations},)

NODE_CLASS_MAPPINGS = {"HatTilingNode": HatTilingNode}