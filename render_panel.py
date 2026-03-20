import os

class RenderPanelNode:
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
        output_dir = r"D:\Users\2003c\Documents\SFU\IAT 460\FinalProject\ComfyUI\output"
        path = os.path.join(output_dir, filename)
        
        # --- THE FIX: Ensure this node pulls the Panel HTML ---
        html_content = height_data.get("panel_html", "<html><body>No Panel Data</body></html>")
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"SUCCESS: File written to {path}")
        return {}

NODE_CLASS_MAPPINGS = {"RenderPanelNode": RenderPanelNode}