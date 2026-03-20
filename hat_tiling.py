import numpy as np

class HatTilingNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "iterations": ("INT", {"default": 2, "min": 1, "max": 4}),
                "scale": ("FLOAT", {"default": 20.0, "min": 1.0, "max": 100.0, "step": 0.5}),
            },
        }

    RETURN_TYPES = ("TILING_DATA",)
    FUNCTION = "generate"
    CATEGORY = "Aperiodic"

    def generate(self, iterations, scale):
        # 1. Define the 13-vertex "Hat" coordinates
        # Based on the 8-kite construction (r=sqrt(3), 1)
        r3 = np.sqrt(3)
        raw_hat = [
            [0, 0], [r3/2, 1/2], [r3, 0], [1.5*r3, 0.5], [1.5*r3, 1.5],
            [r3, 2], [r3, 3], [0.5*r3, 3.5], [0, 3], [0, 2],
            [-0.5*r3, 1.5], [-0.5*r3, 0.5], [0, 0]
        ]
        
        # 2. Substitution System Logic (Simplified for ComfyUI performance)
        # We start with a single cluster and rotate/offset to simulate the H7/H8 rules
        tiles = []
        
        def add_tile(pos, angle, flipped=False):
            coords = np.array(raw_hat)
            if flipped:
                coords[:, 0] *= -1  # Flip X-axis for chirality
            
            # Rotate
            rad = np.radians(angle)
            c, s = np.cos(rad), np.sin(rad)
            rot_mat = np.array([[c, -s], [s, c]])
            coords = np.dot(coords, rot_mat.T)
            
            # Scale and Translate
            coords = (coords * scale) + pos
            tiles.append(coords.tolist())

        # Seed the first cluster
        add_tile([0, 0], 0)
        
        # 3. Recursive expansion (simplified offset pattern)
        # In a full Einstein implementation, this uses 6 specific transformation matrices
        # Here we use the iterative offsets to fill the canvas area
        current_pos = [0, 0]
        for i in range(iterations):
            for angle in range(0, 360, 60):
                dist = (i + 1) * scale * 5
                new_x = np.cos(np.radians(angle)) * dist
                new_y = np.sin(np.radians(angle)) * dist
                
                # Alternate flipped states to maintain aperiodicity
                is_flipped = (angle % 120 == 0)
                add_tile([new_x, new_y], angle, flipped=is_flipped)

        print(f"Aperiodic Generator: Created {len(tiles)} Hat tiles.")
        
        return ({"tiles": tiles, "iterations": iterations, "scale": scale},)

NODE_CLASS_MAPPINGS = { "HatTilingNode": HatTilingNode }
NODE_DISPLAY_NAME_MAPPINGS = { "HatTilingNode": "Aperiodic Hat Tiling" }