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
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, filename)

        # Pull the Panel HTML string specifically
        html_content = height_data.get("panel_html", "<html><body>No Panel Data Found</body></html>")

        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"SUCCESS: Aperiodic Panel saved to {path}")
        return {}

NODE_CLASS_MAPPINGS = {"RenderPanelNode": RenderPanelNode}