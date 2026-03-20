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
        # Force the path to your SFU project output
        output_path = r"D:\Users\2003c\Documents\SFU\IAT 460\FinalProject\ComfyUI\output"
        os.makedirs(output_path, exist_ok=True)
        full_path = os.path.join(output_path, filename)

        html_content = height_data.get("html", "")
        
        if not html_content or "const tileData = [];" in html_content:
            print("WARNING: Render node received empty tile data!")

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return {}

NODE_CLASS_MAPPINGS = {"RenderCanvasNode": RenderCanvasNode}