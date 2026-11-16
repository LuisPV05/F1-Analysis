"""Gráficas a nivel de temporada."""

import matplotlib.pyplot as plt
import seaborn as sns
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


def plot_points_heatmap(matrix, labels, title):
    """Mapa de calor de puntos por piloto y carrera, con el total a la derecha.

    'matrix' y 'labels' vienen de season.get_points_matrix(). Los pilotos se
    ordenan por puntos totales, de más a menos.
    """
    totals = matrix.sum(axis=1).sort_values(ascending=False)
    matrix = matrix.loc[totals.index]

    fig, (ax_main, ax_total) = plt.subplots(
        1,
        2,
        figsize=(14, 9),
        gridspec_kw={"width_ratios": [len(matrix.columns), 2]},
    )

    sns.heatmap(
        matrix,
        ax=ax_main,
        cmap="Blues",
        vmin=0,
        annot=True,
        fmt="g",
        annot_kws={"size": 8},
        cbar=False,
        linewidths=0.5,
        linecolor="white",
        xticklabels=labels,
        yticklabels=matrix.index,
    )
    ax_main.xaxis.tick_top()
    ax_main.tick_params(axis="x", labelrotation=90)
    ax_main.set_xlabel("")
    ax_main.set_ylabel("")

    sns.heatmap(
        totals.to_frame("Total"),
        ax=ax_total,
        cmap="Blues",
        vmin=0,
        annot=True,
        fmt="g",
        annot_kws={"size": 8},
        cbar=False,
        linewidths=0.5,
        linecolor="white",
        xticklabels=["Total"],
        yticklabels=False,
    )
    ax_total.xaxis.tick_top()
    ax_total.set_xlabel("")
    ax_total.set_ylabel("")

    fig.suptitle(title)
    fig.tight_layout()
    return fig