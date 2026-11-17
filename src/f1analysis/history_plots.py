"""Gráficas que comparan varias temporadas."""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from .styling import team_color

RUNNER_UP_COLOR = "#d0d0d0"
ERA_NOTE = (
    "Los sistemas de puntos cambian entre épocas: "
    "compara con cuidado puntos de años distintos"
)


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

    fig.suptitle(f"{title}\n{ERA_NOTE}")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return fig


def plot_driver_comparison(comparison, order, title):
    """Puntos, victorias y posición final de varios pilotos por temporada.

    'comparison' y 'order' vienen de history.get_driver_comparison(). Las
    temporadas en que un piloto no corrió quedan como hueco, y una estrella
    marca los años en que ganó el título. Cada piloto tiene un color propio
    (no el de su escudería, porque puede cambiar de equipo).
    """
    seasons = list(
        range(int(comparison["season"].min()), int(comparison["season"].max()) + 1)
    )
    palette = plt.get_cmap("tab10")
    n_drivers = len(order)
    width = 0.8 / n_drivers

    fig, (ax_points, ax_wins, ax_position) = plt.subplots(
        3, 1, figsize=(11, 11), sharex=True
    )

    for i, name in enumerate(order):
        data = (
            comparison[comparison["driver"] == name]
            .set_index("season")
            .reindex(seasons)
        )
        color = palette(i)

        # Puntos, con estrella en los títulos
        ax_points.plot(
            seasons, data["points"], marker="o", color=color, label=name
        )
        champion = data[data["position"] == 1]
        ax_points.scatter(
            champion.index,
            champion["points"],
            marker="*",
            s=300,
            color=color,
            edgecolor="black",
            zorder=3,
        )

        # Victorias, en barras agrupadas
        offset = (i - (n_drivers - 1) / 2) * width
        ax_wins.bar(
            [s + offset for s in seasons],
            data["wins"].fillna(0),
            width,
            color=color,
        )

        # Posición final del campeonato
        ax_position.plot(seasons, data["position"], marker="o", color=color)

    handles, labels = ax_points.get_legend_handles_labels()
    handles.append(
        Line2D(
            [0],
            [0],
            marker="*",
            color="white",
            markerfacecolor="grey",
            markeredgecolor="black",
            markersize=15,
            label="Título",
        )
    )
    ax_points.legend(handles=handles, loc="upper left")
    ax_points.set_ylabel("Puntos")
    ax_points.grid(alpha=0.3)

    ax_wins.set_ylabel("Victorias")
    ax_wins.grid(axis="y", alpha=0.3)
    ax_wins.set_axisbelow(True)

    max_position = int(comparison["position"].max())
    ax_position.set_ylim(max_position + 0.5, 0.5)  # la posición 1 arriba
    ax_position.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax_position.set_ylabel("Posición final")
    ax_position.grid(alpha=0.3)
    ax_position.set_xticks(seasons)
    ax_position.set_xticklabels([str(s) for s in seasons], rotation=45)

    fig.suptitle(f"{title}\n{ERA_NOTE}")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig