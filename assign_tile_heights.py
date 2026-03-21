import random

class AssignTileHeightsNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"tiling_data": ("TILING_DATA",), "min_height": ("FLOAT", {"default": 5.0}), "max_height": ("FLOAT", {"default": 50.0})}}
    RETURN_TYPES = ("HEIGHT_DATA",)
    FUNCTION = "execute"
    CATEGORY = "Aperiodic Tiles"

    def execute(self, tiling_data, min_height, max_height):
        tiles = tiling_data["tiles"]
        for tile in tiles:
            tile["height"] = random.uniform(min_height, max_height)
            tile["slant"] = [random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 1.0]
        tiling_data["min_height"] = min_height
        tiling_data["max_height"] = max_height
        return (tiling_data,)