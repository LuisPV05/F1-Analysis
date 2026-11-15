"""Gráficas con matplotlib. Cada función devuelve la figura."""

import matplotlib.pyplot as plt

from .analysis import clean_race_laps
from .styling import add_sorted_driver_legend, get_driver_style, team_color


def plot_qualifying_delta(qualifying, title):
    """Barras con la diferencia de cada piloto respecto a la pole.

    'qualifying' debe venir de analysis.qualifying_delta().
    """
    colors = [team_color(team) for team in qualifying["constructorId"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(qualifying["driverCode"], qualifying["delta"], color=colors)
    ax.invert_yaxis()  # la pole arriba
    ax.set_xlabel("Diferencia con la pole (s)")
    ax.set_title(title)

    for y, delta in enumerate(qualifying["delta"]):
        ax.text(delta + 0.005, y, f"+{delta:.3f}", va="center", fontsize=8)

    fig.tight_layout()
    return fig


def plot_race_pace(laps, race, driver_codes, title, styles=None):
    """Líneas con el tiempo de vuelta de los pilotos indicados.

    'race' son los resultados de carrera (para colores y orden de leyenda).
    'styles' permite estilos personalizados (ver styling.DEFAULT_STYLES).
    """
    fig, ax = plt.subplots(figsize=(11, 6))

    for code in driver_codes:
        driver_laps = laps[laps["driverCode"] == code].sort_values("lap")
        driver_laps = clean_race_laps(driver_laps)
        style = get_driver_style(code, race, styles)
        ax.plot(driver_laps["lap"], driver_laps["seconds"], label=code, **style)

    ax.set_xlabel("Vuelta")
    ax.set_ylabel("Tiempo de vuelta (s)")
    ax.set_title(title)
    add_sorted_driver_legend(ax, race)
    fig.tight_layout()
    return fig