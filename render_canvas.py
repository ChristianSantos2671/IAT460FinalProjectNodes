import os

class RenderCanvasNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "height_data": ("HEIGHT_DATA",),
                "filename": ("STRING", {"default": "aperiodic_canvas.html"}),
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "render"
    CATEGORY = "Aperiodic"

    def render(self, height_data, filename):
        # Use the specific path from your log
        output_dir = r"D:\Users\2003c\Documents\SFU\IAT 460\FinalProject\ComfyUI\output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        path = os.path.join(output_dir, filename)
        
        # --- THE FIX: You must actually write the data here ---
        # Replace 'height_data["html_string"]' with whatever variable 
        # in your project contains the actual HTML code.
        html_content = height_data.get("html", "<html><body>No Data Found</body></html>")
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"SUCCESS: File written to {path}")
        return {}

NODE_CLASS_MAPPINGS = {"RenderCanvasNode": RenderCanvasNode}