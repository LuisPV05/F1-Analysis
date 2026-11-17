"""Gráficas que comparan varias temporadas."""

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from .styling import team_color

RUNNER_UP_COLOR = "#d0d0d0"


def plot_champions(champions, title):
    """Puntos de campeón y subcampeón, y victorias del campeón, por temporada.

    'champions' viene de history.get_champions(). Las barras del campeón
    llevan el color de su escudería y su apellido encima.
    """
    seasons = champions["season"].astype(str).tolist()
    x = list(range(len(champions)))
    width = 0.4
    colors = [team_color(team) for team in champions["champion_team_id"]]

    fig, (ax_points, ax_wins) = plt.subplots(
        2, 1, figsize=(11, 9), sharex=True
    )

    # --- Puntos ---
    champion_points = champions["champion_points"]
    ax_points.bar(
        [i - width / 2 for i in x],
        champion_points,
        width,
        color=colors,
        edgecolor="black",
    )
    ax_points.bar(
        [i + width / 2 for i in x],
        champions["runner_up_points"],
        width,
        color=RUNNER_UP_COLOR,
        edgecolor="grey",
    )
    for i, points, name in zip(x, champion_points, champions["champion"]):
        ax_points.text(
            i - width / 2,
            points + 2,
            name,
            rotation=90,
            ha="center",
            va="bottom",
            fontsize=8,
        )
    top = champions[["champion_points", "runner_up_points"]].max().max()
    ax_points.set_ylim(0, top * 1.3)
    ax_points.set_ylabel("Puntos")
    ax_points.grid(axis="y", alpha=0.3)
    ax_points.set_axisbelow(True)
    ax_points.legend(
        handles=[
            Patch(facecolor="white", edgecolor="black", label="Campeón (color de su escudería)"),
            Patch(facecolor=RUNNER_UP_COLOR, edgecolor="grey", label="Subcampeón"),
        ],
        loc="upper left",
    )

    # --- Victorias del campeón ---
    ax_wins.bar(x, champions["champion_wins"], color=colors, edgecolor="black")
    ax_wins.set_ylabel("Victorias del campeón")
    ax_wins.grid(axis="y", alpha=0.3)
    ax_wins.set_axisbelow(True)
    ax_wins.set_xticks(x)
    ax_wins.set_xticklabels(seasons, rotation=45)

    fig.suptitle(
        f"{title}\nLos sistemas de puntos cambian entre épocas: "
        "compara con cuidado puntos de años distintos"
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return fig