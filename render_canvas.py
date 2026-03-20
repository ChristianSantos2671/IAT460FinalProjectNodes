import os

class RenderCanvasNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "height_data": ("HEIGHT_DATA",),
                "filename": ("STRING", {"default": "canvas.html"}),
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "render"
    CATEGORY = "Aperiodic"

    def render(self, height_data, filename):
        # Navigate to the ComfyUI/output folder
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        output_path = os.path.join(base_path, "output")
        os.makedirs(output_path, exist_ok=True)
        
        full_path = os.path.join(output_path, filename)
        html_content = height_data.get("html", "<h1>No Data</h1>")

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"File successfully saved: {full_path}")
        return {}

NODE_CLASS_MAPPINGS = {"RenderCanvasNode": RenderCanvasNode}