# modules/graph_utils.py
# Graph drawing helper for the Algorithm Visualizer.

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from modules.data import GRAPH, NODE_POS

def draw_graph(visited_nodes, final_path, start, goal):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")

    drawn = set()
    for node, neighbors in GRAPH.items():
        for nb, w in neighbors.items():
            edge = tuple(sorted([node, nb]))
            if edge in drawn:
                continue
            drawn.add(edge)
            x1, y1 = NODE_POS[node]
            x2, y2 = NODE_POS[nb]
            ax.plot([x1, x2], [y1, y2], color="#bbb", linewidth=1.8, zorder=1)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(
                mx, my, str(w), fontsize=8, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none"),
                zorder=2,
            )

    # Highlight path edges
    if final_path:
        for i in range(len(final_path) - 1):
            x1, y1 = NODE_POS[final_path[i]]
            x2, y2 = NODE_POS[final_path[i + 1]]
            ax.plot([x1, x2], [y1, y2], color="#E53935", linewidth=3, zorder=3)

    # Draw nodes
    for node, (x, y) in NODE_POS.items():
        if node == start:
            color, ec = "#4CAF50", "#2E7D32"
        elif node == goal:
            color, ec = "#F44336", "#B71C1C"
        elif node in final_path:
            color, ec = "#FF9800", "#E65100"
        elif node in visited_nodes:
            color, ec = "#90CAF9", "#1565C0"
        else:
            color, ec = "#E0E0E0", "#757575"

        circle = plt.Circle((x, y), 0.28, color=color, ec=ec, linewidth=1.5, zorder=4)
        ax.add_patch(circle)
        ax.text(x, y, node, ha="center", va="center", fontsize=12,
                fontweight="bold", color="white" if color != "#E0E0E0" else "#333", zorder=5)

    ax.set_xlim(-0.5, 4.5)
    ax.set_ylim(-0.3, 4.5)
    ax.axis("off")

    legend_patches = [
        mpatches.Patch(color="#4CAF50", label="Start"),
        mpatches.Patch(color="#F44336", label="Goal"),
        mpatches.Patch(color="#FF9800", label="Final Path"),
        mpatches.Patch(color="#90CAF9", label="Visited"),
        mpatches.Patch(color="#E0E0E0", label="Not Visited"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=8, framealpha=0.9)

    return fig
