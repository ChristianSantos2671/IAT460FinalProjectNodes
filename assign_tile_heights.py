import json
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
        # Fix: Look for 'tiles' inside canvas_data
        tiles = canvas_data.get("tiles", [])
        random.seed(seed)
        
        # Logic from your original project: 1 height per tile
        heights = [random.randint(1, 5) for _ in range(len(tiles))]
        
        # Convert Python lists to JSON strings for the HTML template
        tiles_js = json.dumps(tiles)
        heights_js = json.dumps(heights)

        # Plotly Template (mimics your original project)
        plotly_html = f"""
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>
        </head>
        <body>
            <div id="plot" style="width:100%;height:100vh;"></div>
            <script>
                const tileData = {tiles_js};
                const heightData = {heights_js};
                
                const traces = tileData.map((tile, i) => ({{
                    x: tile.map(p => p[0]),
                    y: tile.map(p => p[1]),
                    fill: 'toself',
                    type: 'scatter',
                    mode: 'lines',
                    fillcolor: `rgba(40, 120, ${{heightData[i] * 45}}, 0.7)`,
                    line: {{ color: 'black', width: 1 }}
                }}));

                Plotly.newPlot('plot', traces, {{
                    showlegend: false,
                    xaxis: {{ visible: false }},
                    yaxis: {{ visible: false, scaleanchor: 'x' }},
                    margin: {{ t: 0, b: 0, l: 0, r: 0 }}
                }});
            </script>
        </body>
        </html>
        """

        return ({"html": plotly_html, "panel_html": plotly_html, "tiles": tiles},)

NODE_CLASS_MAPPINGS = {"AperiodicAssignHeights": AperiodicAssignHeights}