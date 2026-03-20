class AssignHeightsNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_data": ("CANVAS_DATA",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
        }

    RETURN_TYPES = ("HEIGHT_DATA",)
    FUNCTION = "assign"
    CATEGORY = "Aperiodic/Processing"

    def assign(self, canvas_data, seed):
        # Implementation from assign_tile_heights.py
        height_data = {"canvas": canvas_data, "seed": seed}
        return (height_data,)

NODE_CLASS_MAPPINGS = {"AssignHeightsNode": AssignHeightsNode}