import numpy as np
import z3
from collections import defaultdict

def generate_hat_tiling(canvas_w: float, canvas_h: float, tile_size: float) -> list[np.ndarray]:
    grid_size = int(max(canvas_w, canvas_h) / (tile_size * 1.5)) + 4
    six_rotations = np.exp(1j * (np.pi / 3 * np.arange(6)))
    kite = np.array([0, 0.5, 1 / np.sqrt(3) * np.exp(1j * np.pi / 6), 0.5 * np.exp(1j * np.pi / 3), 0])
    x, y = np.mgrid[-2:grid_size, -2:grid_size]
    hexagon_centers = x + 0.5 * y + 1j * np.sqrt(3) / 2 * y
    indices = [[2, 2, 2, 2, 2, 2, 1, 1], [2, 2, 2, 2, 1, 1, 2, 2], [1, 2, 3, 4, 0, 1, 5, 4]]
    kites_local = (kite[None, None, None, :] * six_rotations[None, None, :, None] + hexagon_centers[:, :, None, None])
    hat_kites_local = kites_local[indices[0], indices[1], indices[2], :]
    hats = hat_kites_local[None, :, :] * six_rotations[:, None, None]
    reflected = np.real(hats) - 1j * np.imag(hats)
    hats_variants = np.concatenate([hats, reflected], axis=0) 
    hats_placed = (hats_variants[None, None, :, :, :] + hexagon_centers[:, :, None, None, None]).reshape(-1, 8, 5)

    hat_centers = np.round(np.mean(hats_placed, axis=-1), 2)
    hat_map = defaultdict(list)
    for idx, centers in enumerate(hat_centers):
        for c in centers: hat_map[c].append(idx)

    hat_present = [z3.Bool(f"h{i}") for i in range(len(hats_placed))]
    solver = z3.Solver()
    for p in hat_map.keys():
        group = [hat_present[i] for i in hat_map[p]]
        for a in range(len(group)):
            for b in range(a + 1, len(group)):
                solver.add(z3.Not(z3.And(group[a], group[b])))
        if len(group) == max(len(v) for v in hat_map.values()):
            solver.add(z3.Or(group))

    if solver.check() != z3.sat: return []
    model = solver.model()
    chosen_indices = [i for i, h in enumerate(hat_present) if z3.is_true(model[h])]
    
    final_tiles = []
    for idx in chosen_indices:
        tile_complex = hats_placed[idx].flatten()
        points = []
        for p in tile_complex:
            if not any(np.isclose(p, existing) for existing in points): points.append(p)
        verts = np.array([[p.real * tile_size, p.imag * tile_size] for p in points])
        final_tiles.append(verts)
    return final_tiles

class HatTilingNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"canvas_w": ("FLOAT", {"default": 1920.0}), "canvas_h": ("FLOAT", {"default": 1080.0}), "tile_size": ("FLOAT", {"default": 40.0})}}
    RETURN_TYPES = ("RAW_TILES",)
    FUNCTION = "execute"
    CATEGORY = "Aperiodic Tiles"
    def execute(self, canvas_w, canvas_h, tile_size):
        return (generate_hat_tiling(canvas_w, canvas_h, tile_size),)