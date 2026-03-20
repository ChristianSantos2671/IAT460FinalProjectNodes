import os

class RenderCanvasNode:
    def __init__(self):
        pass
    
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
        # Setup the output path
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        path = os.path.join(output_dir, filename)
        
        # Extract HTML from the dictionary passed by the previous node
        # We use .get() to avoid crashing if the key is missing
        html_content = height_data.get("html", "<html><body>No Canvas Data Received</body></html>")
        
        # Physically write the file to disk
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"Aperiodic Canvas successfully saved to: {path}")
        return {}

NODE_CLASS_MAPPINGS = {"RenderCanvasNode": RenderCanvasNode}