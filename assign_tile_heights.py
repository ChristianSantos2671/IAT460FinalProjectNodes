import random

class AperiodicAssignHeights:
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
    CATEGORY = "Aperiodic"

    def assign(self, canvas_data, seed):
        tiles = canvas_data.get("tiles", [])
        random.seed(seed)
        
        # Assign heights (logic from your original project)
        heights = [random.randint(1, 5) for _ in range(len(tiles))]
        
        # Generate the HTML for the Main Canvas
        canvas_html = self.generate_html(tiles, heights, is_panel=False)
        
        # Generate the HTML for the Panel
        panel_html = self.generate_html(tiles, heights, is_panel=True)

        return ({"html": canvas_html, "panel_html": panel_html, "tiles": tiles, "heights": heights},)

    def generate_html(self, tiles, heights, is_panel=False):
        # This string mimics the logic in your original ChristianSantos2671/AperiodicTiles repo
        title = "Aperiodic Panel" if is_panel else "Aperiodic Canvas"
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.0/p5.js"></script>
    <style>body {{ margin: 0; display: flex; justify-content: center; background: #222; }}</style>
</head>
<body>
    <script>
        const tiles = {tiles};
        const heights = {heights};

        function setup() {{
            createCanvas(windowWidth, windowHeight);
            noLoop();
        }}

        function draw() {{
            background(240);
            stroke(0);
            for (let i = 0; i < tiles.length; i++) {{
                let t = tiles[i];
                let h = heights[i];
                fill(h * 50, 100, 200); // Color based on assigned height
                beginShape();
                for (let p of t) {{
                    vertex(p[0], p[1]);
                }}
                endShape(CLOSE);
            }}
        }}
    </script>
</body>
</html>
"""

NODE_CLASS_MAPPINGS = {"AperiodicAssignHeights": AperiodicAssignHeights}