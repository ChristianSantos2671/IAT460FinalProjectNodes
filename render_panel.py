import os

class RenderPanelNode:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "height_data": ("HEIGHT_DATA",),
                "filename": ("STRING", {"default": "aperiodic_panel.html"}),
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "render"
    CATEGORY = "Aperiodic"

    def render(self, height_data, filename):
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        path = os.path.join(output_dir, filename)
        
        # Extract Panel HTML (Assuming your logic stores it in 'panel_html')
        html_content = height_data.get("panel_html", "<html><body>No Panel Data Received</body></html>")
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"Aperiodic Panel successfully saved to: {path}")
        return {}

NODE_CLASS_MAPPINGS = {"RenderPanelNode": RenderPanelNode}