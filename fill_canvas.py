class FillCanvasNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tiling_data": ("TILING_DATA",),
                "width": ("INT", {"default": 800}),
                "height": ("INT", {"default": 800}),
            },
        }

    RETURN_TYPES = ("CANVAS_DATA",)
    FUNCTION = "fill"
    CATEGORY = "Aperiodic"

    def fill(self, tiling_data, width, height):
        # We ensure the dictionary contains the 'tiles' key
        tiles = tiling_data.get("tiles", [])
        
        # Return the dictionary properly wrapped in a tuple
        return ({"tiles": tiles, "width": width, "height": height},)

NODE_CLASS_MAPPINGS = {"FillCanvasNode": FillCanvasNode}