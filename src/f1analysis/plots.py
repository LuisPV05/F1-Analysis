"""Gráficas con matplotlib. Cada función devuelve la figura."""

import matplotlib.pyplot as plt

from .analysis import clean_race_laps


def plot_qualifying_delta(qualifying, title):
    """Barras con la diferencia de cada piloto respecto a la pole.

    'qualifying' debe venir de analysis.qualifying_delta().
    """
    teams = qualifying["constructorName"].unique()
    palette = plt.get_cmap("tab10")
    team_color = {team: palette(i % 10) for i, team in enumerate(teams)}
    colors = [team_color[t] for t in qualifying["constructorName"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(qualifying["driverCode"], qualifying["delta"], color=colors)
    ax.invert_yaxis()  # la pole arriba
    ax.set_xlabel("Diferencia con la pole (s)")
    ax.set_title(title)

    for y, delta in enumerate(qualifying["delta"]):
        ax.text(delta + 0.005, y, f"+{delta:.3f}", va="center", fontsize=8)

    fig.tight_layout()
    return fig


def plot_race_pace(laps, driver_codes, title):
    """Líneas con el tiempo de vuelta de los pilotos indicados."""
    fig, ax = plt.subplots(figsize=(11, 6))

    for code in driver_codes:
        driver_laps = laps[laps["driverCode"] == code].sort_values("lap")
        driver_laps = clean_race_laps(driver_laps)
        ax.plot(
            driver_laps["lap"],
            driver_laps["seconds"],
            marker="o",
            markersize=3,
            label=code,
        )

    ax.set_xlabel("Vuelta")
    ax.set_ylabel("Tiempo de vuelta (s)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig