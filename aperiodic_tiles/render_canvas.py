"""
render_canvas.py
================
Provides render_canvas() — takes the canvas dict returned by fill_canvas()
and renders the 2-D aperiodic hat-tile tiling as an interactive Plotly figure
(saved to HTML) or a Matplotlib figure (shown on screen / saved to PNG).

Each tile is drawn as a filled polygon using the vertex coordinates stored
directly in the canvas dict.  No SVG file is required.
"""

from __future__ import annotations
import datetime
import os
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import numpy as np


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

_COLOUR_A    = "#5B8DB8"   # muted blue  (every other tile)
_COLOUR_B    = "#E07B54"   # warm orange (alternating tile)
_EDGE_COLOUR = "#1a1a2e"
_EDGE_WIDTH  = 0.6
_ALPHA       = 0.85


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_canvas(
    canvas: dict[str, Any],
    figsize: tuple[float, float] | None = None,
    dpi: int = 100,
    title: str = "Aperiodic Hat Tiling",
    show: bool = True,
    save_path: str | None = None,
) -> matplotlib.figure.Figure:
    """
    Render the 2-D aperiodic hat-tile canvas.

    Parameters
    ----------
    canvas : dict
        The canvas dictionary returned by fill_canvas().
    figsize : (float, float) or None, optional
        Matplotlib figure size in inches.  If None, computed from the canvas
        dimensions.
    dpi : int, optional
        Resolution of the figure.  Default 100.
    title : str, optional
        Figure title.
    show : bool, optional
        If True (default) call plt.show() to display the figure.
    save_path : str or None, optional
        If given, save the figure to this file path.  If the path ends in
        .html or .htm an interactive Plotly figure is saved; otherwise a
        Matplotlib raster/vector image is saved.

    Returns
    -------
    matplotlib.figure.Figure
        The Matplotlib figure object.
    """
    w = canvas["canvas_width"]
    h = canvas["canvas_height"]
    tiles = canvas["tiles"]

    if figsize is None:
        figsize = (
            max(4.0, min(20.0, w / dpi)),
            max(3.0, min(16.0, h / dpi)),
        )

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)   # y-axis flipped: (0,0) at top-left like screen coords
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("#f5f0eb")
    fig.patch.set_facecolor("#f5f0eb")

    patches_a = []
    patches_b = []

    for idx, tile in enumerate(tiles):
        verts = np.array(tile["vertices"])
        patch = MplPolygon(verts, closed=True)
        if idx % 2 == 0:
            patches_a.append(patch)
        else:
            patches_b.append(patch)

    if patches_a:
        ax.add_collection(PatchCollection(
            patches_a,
            facecolor=_COLOUR_A,
            edgecolor=_EDGE_COLOUR,
            linewidth=_EDGE_WIDTH,
            alpha=_ALPHA,
        ))

    if patches_b:
        ax.add_collection(PatchCollection(
            patches_b,
            facecolor=_COLOUR_B,
            edgecolor=_EDGE_COLOUR,
            linewidth=_EDGE_WIDTH,
            alpha=_ALPHA,
        ))

    patch_a = mpatches.Patch(color=_COLOUR_A, label="Hat tile")
    patch_b = mpatches.Patch(color=_COLOUR_B, label="Hat tile (alt.)")
    ax.legend(handles=[patch_a, patch_b], loc="lower right",
              fontsize=8, framealpha=0.7)

    ax.set_title(
        f"{title}  ({len(tiles)} tiles, size={canvas['tile_size']}px)",
        fontsize=10, pad=6,
    )

    plt.tight_layout()

    if save_path:
        ext = os.path.splitext(save_path)[1].lower()
        if ext in (".html", ".htm"):
            _save_canvas_html(canvas, save_path, title)
        else:
            fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
            print(f"[render_canvas] Saved to {save_path}")

    if show:
        plt.show()

    return fig


# ---------------------------------------------------------------------------
# HTML / Plotly 2-D output
# ---------------------------------------------------------------------------

def _save_canvas_html(
    canvas: dict[str, Any],
    path: str,
    title: str = "Aperiodic Hat Tiling",
) -> None:
    """Save an interactive Plotly 2-D figure of the canvas to an HTML file."""
    import plotly.graph_objects as go

    w = canvas["canvas_width"]
    h = canvas["canvas_height"]
    tile_size = canvas["tile_size"]
    tiles = canvas["tiles"]

    xs_a, ys_a = [], []
    xs_b, ys_b = [], []

    for idx, tile in enumerate(tiles):
        verts = np.array(tile["vertices"])
        # Close the polygon with None separator for Plotly
        xs = list(verts[:, 0]) + [verts[0, 0], None]
        ys = list(verts[:, 1]) + [verts[0, 1], None]
        if idx % 2 == 0:
            xs_a.extend(xs)
            ys_a.extend(ys)
        else:
            xs_b.extend(xs)
            ys_b.extend(ys)

    fig = go.Figure()

    if xs_a:
        fig.add_trace(go.Scatter(
            x=xs_a, y=ys_a,
            mode="lines",
            fill="toself",
            fillcolor=_COLOUR_A,
            line=dict(color=_EDGE_COLOUR, width=0.6),
            opacity=_ALPHA,
            name="Hat tile",
        ))

    if xs_b:
        fig.add_trace(go.Scatter(
            x=xs_b, y=ys_b,
            mode="lines",
            fill="toself",
            fillcolor=_COLOUR_B,
            line=dict(color=_EDGE_COLOUR, width=0.6),
            opacity=_ALPHA,
            name="Hat tile (alt.)",
        ))

    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fig.update_layout(
        title=dict(
            text=(
                f"{title}  ({len(tiles)} tiles, size={tile_size}px)"
                f"<br><sup>Created: {created_at}</sup>"
            ),
            font=dict(size=14),
        ),
        xaxis=dict(range=[0, w], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[h, 0], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1),
        plot_bgcolor="#f5f0eb",
        paper_bgcolor="#f5f0eb",
        margin=dict(l=10, r=10, t=65, b=10),
        legend=dict(x=0.8, y=0.02),
    )

    fig.write_html(path, include_plotlyjs=True, full_html=True)
    print(f"[render_canvas] Saved interactive HTML to {path}")
