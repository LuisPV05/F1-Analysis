"""Gráficas del campeonato de constructores."""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .season_plots import NO_COLOR, YES_COLOR
from .styling import team_color


def plot_constructor_chances(table, title):
    """Barras con los puntos actuales y el máximo teórico de cada equipo.

    'table' viene de constructors.who_can_win_constructors(). Barra oscura:
    puntos actuales. Barra clara: máximo teórico. La línea marca los puntos
    del líder.
    """
    table = table.sort_values("position")
    colors = [YES_COLOR if win else NO_COLOR for win in table["can_win"]]
    leader_points = table["points"].max()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(table["constructorName"], table["max_points"], color=colors, alpha=0.3)
    ax.barh(table["constructorName"], table["points"], color=colors)
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


def plot_constructor_progress(cumulative, names, title):
    """Líneas con los puntos acumulados de cada equipo, ronda a ronda.

    'cumulative' y 'names' vienen de constructors.get_constructor_progress().
    La leyenda va ordenada por puntos finales, de más a menos.
    """
    rounds = list(cumulative.columns)
    order = cumulative.iloc[:, -1].sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(11, 7))
    for constructor_id in order:
        ax.plot(
            rounds,
            cumulative.loc[constructor_id],
            color=team_color(constructor_id),
            marker="o",
            markersize=3,
            label=names[constructor_id],
        )

    ax.set_xticks(rounds)
    ax.set_xlabel("Ronda")
    ax.set_ylabel("Puntos acumulados")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig