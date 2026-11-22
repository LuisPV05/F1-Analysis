"""Gráficas de duelos entre compañeros de equipo."""

import matplotlib.pyplot as plt

from .styling import team_color


def plot_teammate_duels(summary, title):
    """Reparto de victorias de cada pareja, en clasificación y en carrera.

    'summary' viene de teammates.teammate_duels(). Cada barra se divide entre
    los dos pilotos: el piloto con más puntos (a) va a la izquierda, en el
    color de su escudería, y su compañero (b) a la derecha, en tono claro.
    """
    summary = summary.reset_index(drop=True)
    labels = [
        f"{name}\n{rounds} carreras"
        for name, rounds in zip(summary["constructorName"], summary["rounds"])
    ]

    fig, axes = plt.subplots(
        1, 2, figsize=(13, 0.9 * len(summary) + 2.5), sharey=True
    )

    for ax, metric, panel_title in zip(
        axes, ["quali", "race"], ["Clasificación", "Carrera"]
    ):
        for i, row in summary.iterrows():
            wins_a = row[f"{metric}_wins_a"]
            wins_b = row[f"{metric}_wins_b"]
            total = wins_a + wins_b
            if total == 0:
                continue  # sin datos para este duelo

            share = wins_a / total
            color = team_color(row["constructorId"])
            ax.barh(i, share, color=color, edgecolor="black")
            ax.barh(
                i, 1 - share, left=share, color=color, alpha=0.3, edgecolor="black"
            )
            ax.text(
                0.01,
                i,
                f"{row['driver_a']} {int(wins_a)}",
                va="center",
                ha="left",
                fontsize=9,
                fontweight="bold",
            )
            ax.text(
                0.99,
                i,
                f"{int(wins_b)} {row['driver_b']}",
                va="center",
                ha="right",
                fontsize=9,
            )

        ax.axvline(0.5, color="black", linestyle="--", linewidth=1)
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.set_title(panel_title)

    axes[0].set_yticks(range(len(summary)))
    axes[0].set_yticklabels(labels)
    axes[0].invert_yaxis()  # la escudería con más puntos arriba

    fig.suptitle(
        f"{title}\n"
        "Izquierda: piloto con más puntos · derecha (tono claro): su compañero"
    )
    fig.tight_layout()
    return fig