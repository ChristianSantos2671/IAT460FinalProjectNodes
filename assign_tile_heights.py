import random
import json

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
        
        # 1. Assign random heights 1-5
        heights = [random.randint(1, 5) for _ in range(len(tiles))]
        
        # 2. Convert tiles to a JSON-safe format for JavaScript
        # This ensures the browser doesn't see "[]" empty arrays
        tiles_json = json.dumps(tiles)
        heights_json = json.dumps(heights)

        # 3. Build the Plotly HTML Template
        html_template = f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>
        </head>
        <body>
            <div id="plot" style="width:100%;height:100vh;"></div>
            <script>
                const tileData = {tiles_json};
                const heightData = {heights_json};
                
                const traces = tileData.map((tile, i) => {{
                    return {{
                        x: tile.map(p => p[0]),
                        y: tile.map(p => p[1]),
                        fill: 'toself',
                        type: 'scatter',
                        mode: 'lines',
                        fillcolor: `rgba(100, 150, ${{heightData[i] * 40}}, 0.8)`,
                        line: {{ color: 'black', width: 1 }}
                    }};
                }});

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

        return ({"html": html_template, "panel_html": html_template, "tiles": tiles, "heights": heights},)

NODE_CLASS_MAPPINGS = { "AperiodicAssignHeights": AperiodicAssignHeights }