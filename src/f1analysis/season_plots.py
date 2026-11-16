"""Gráficas a nivel de temporada."""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

YES_COLOR = "#2ca02c"
NO_COLOR = "#999999"


def plot_title_chances(table, title):
    """Barras con los puntos actuales y el máximo teórico de cada piloto.

    'table' debe venir de season.who_can_win(). Barra oscura: puntos
    actuales. Barra clara: máximo teórico. La línea marca los puntos del líder.
    """
    table = table.sort_values("position")
    colors = [YES_COLOR if win else NO_COLOR for win in table["can_win"]]
    leader_points = table["points"].max()

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(table["driverCode"], table["max_points"], color=colors, alpha=0.3)
    ax.barh(table["driverCode"], table["points"], color=colors)
    ax.axvline(leader_points, color="black", linestyle="--", linewidth=1)

    ax.invert_yaxis()  # el líder arriba
    ax.set_xlabel("Puntos")
    ax.set_title(
        f"{title}\nBarra oscura: puntos actuales · barra clara: máximo teórico"
    )
    ax.grid(axis="x", alpha=0.3)

    handles = [
        Patch(facecolor=YES_COLOR, label="Puede ganar"),
        Patch(facecolor=NO_COLOR, label="Sin opciones"),
        Line2D([0], [0], color="black", linestyle="--", label="Puntos del líder"),
    ]
    ax.legend(handles=handles, loc="lower right")
    fig.tight_layout()
    return fig