class FillCanvasNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tiling_data": ("TILING_DATA",),
                "width": ("INT", {"default": 800}),
                "height": ("INT", {"default": 600}),
            },
        }

    RETURN_TYPES = ("CANVAS_DATA",)
    FUNCTION = "fill"
    CATEGORY = "Aperiodic/Processing"

    def fill(self, tiling_data, width, height):
        # Implementation from your fill_canvas.py
        canvas_data = {"data": tiling_data, "w": width, "h": height}
        return (canvas_data,)

NODE_CLASS_MAPPINGS = {"FillCanvasNode": FillCanvasNode}