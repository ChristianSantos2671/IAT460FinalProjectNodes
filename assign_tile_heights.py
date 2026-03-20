import json
import random

class AperiodicAssignHeights:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_data": ("CANVAS_DATA",),
                "seed": ("INT", {"default": 0}),
            },
        }

    RETURN_TYPES = ("HEIGHT_DATA",)
    FUNCTION = "assign"
    CATEGORY = "Aperiodic"

    def assign(self, canvas_data, seed):
        # CRITICAL: Debugging print to see if data is actually arriving
        tiles = canvas_data.get("tiles", [])
        print(f"DEBUG: AssignHeights received {len(tiles)} tiles")

        random.seed(seed)
        heights = [random.randint(1, 5) for _ in range(len(tiles))]
        
        # Convert to JSON for JS injection
        tiles_js = json.dumps(tiles)
        heights_js = json.dumps(heights)

        html_template = f"""
        <html>
        <head><script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script></head>
        <body>
            <div id="plot"></div>
            <script>
                const tileData = {tiles_js};
                const heightData = {heights_js};
                console.log("Tiles received in JS:", tileData);
                
                const traces = tileData.map((tile, i) => ({{
                    x: tile.map(p => p[0]),
                    y: tile.map(p => p[1]),
                    fill: 'toself',
                    type: 'scatter',
                    mode: 'lines',
                    fillcolor: `rgba(100, 150, ${{heightData[i] * 40}}, 0.8)`,
                    line: {{ color: 'black', width: 1 }}
                }}));

                Plotly.newPlot('plot', traces, {{
                    yaxis: {{ scaleanchor: 'x' }},
                    margin: {{ t: 0, b: 0, l: 0, r: 0 }}
                }});
            </script>
        </body>
        </html>
        """
        # Pass everything forward
        return ({"html": html_template, "panel_html": html_template, "tiles": tiles},)

NODE_CLASS_MAPPINGS = { "AperiodicAssignHeights": AperiodicAssignHeights }