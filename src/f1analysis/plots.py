"""Gráficas con matplotlib y seaborn. Cada función devuelve la figura."""

import matplotlib.pyplot as plt
import seaborn as sns

from .analysis import clean_race_laps, quick_laps
from .styling import add_sorted_driver_legend, get_driver_style, team_color


def _with_stint_labels(laps):
    """Añade la columna 'stint_label' ('Stint 1', 'Stint 2'...)."""
    return laps.assign(stint_label="Stint " + laps["stint"].astype(str))


def _stint_palette(laps):
    """Etiquetas de stint ordenadas y su paleta de colores."""
    stints = sorted(laps["stint"].unique())
    labels = [f"Stint {s}" for s in stints]
    colors = sns.color_palette("Set2", len(stints))
    return labels, dict(zip(labels, colors))


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


def plot_driver_laptimes(laps, driver_code, title):
    """Dispersión de las vueltas de un piloto, coloreadas por stint."""
    driver_laps = laps[laps["driverCode"] == driver_code]
    driver_laps = _with_stint_labels(quick_laps(driver_laps))
    labels, palette = _stint_palette(driver_laps)

    fig, ax = plt.subplots(figsize=(8, 8))
    sns.scatterplot(
        data=driver_laps,
        x="lap",
        y="seconds",
        hue="stint_label",
        hue_order=labels,
        palette=palette,
        s=80,
        linewidth=0,
        ax=ax,
    )

    ax.set_xlabel("Vuelta")
    ax.set_ylabel("Tiempo de vuelta (s)")
    ax.invert_yaxis()  # menos tiempo = más rápido = arriba
    ax.legend(title="Stint")
    ax.grid(alpha=0.3)
    sns.despine(left=True, bottom=True)
    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_laptime_distribution(laps, race, title, top=10):
    """Violín con la distribución de vueltas de los 'top' primeros.

    Encima, cada vuelta como punto coloreado por stint.
    """
    order = race.sort_values("position")["driverCode"].head(top).tolist()
    selected = laps[laps["driverCode"].isin(order)]
    selected = _with_stint_labels(quick_laps(selected))
    labels, stint_palette = _stint_palette(selected)

    driver_palette = {
        code: team_color(team)
        for code, team in zip(race["driverCode"], race["constructorId"])
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.violinplot(
        data=selected,
        x="driverCode",
        y="seconds",
        hue="driverCode",
        order=order,
        inner=None,
        density_norm="area",
        palette=driver_palette,
        legend=False,
        ax=ax,
    )
    sns.swarmplot(
        data=selected,
        x="driverCode",
        y="seconds",
        order=order,
        hue="stint_label",
        hue_order=labels,
        palette=stint_palette,
        linewidth=0,
        size=3,
        ax=ax,
    )

    ax.set_xlabel("Piloto (orden de llegada)")
    ax.set_ylabel("Tiempo de vuelta (s)")
    ax.legend(title="Stint")
    sns.despine(left=True, bottom=True)
    fig.suptitle(title)
    fig.tight_layout()
    return fig