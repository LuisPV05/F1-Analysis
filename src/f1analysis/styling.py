"""Estilos de gráfica por piloto: color de escudería y tipo de trazo.

Equivalente sin cuenta F1TV de fastf1.plotting.get_driver_style y
fastf1.plotting.add_sorted_driver_legend.
"""

# Colores por constructorId (identificadores de Jolpica/Ergast).
TEAM_COLORS = {
    "red_bull": "#3671C6",
    "mercedes": "#27F4D2",
    "ferrari": "#E8002D",
    "mclaren": "#FF8000",
    "alpine": "#FF87BC",
    "renault": "#FFF500",
    "aston_martin": "#229971",
    "racing_point": "#F596C8",
    "alphatauri": "#5E8FAA",
    "toro_rosso": "#469BFF",
    "rb": "#6692FF",
    "alfa": "#C92D4B",
    "sauber": "#52E252",
    "haas": "#B6BABD",
    "williams": "#64C4FF",
    "force_india": "#F596C8",
}
FALLBACK_COLOR = "#999999"

# Un estilo por posición dentro del equipo: primer piloto, segundo piloto.
# "auto" en el color se sustituye por el color de la escudería.
DEFAULT_STYLES = [
    {"color": "auto", "linestyle": "solid"},
    {"color": "auto", "linestyle": "dashed"},
]


def team_color(constructor_id):
    """Color de una escudería (gris si no está en la tabla)."""
    return TEAM_COLORS.get(constructor_id, FALLBACK_COLOR)


def driver_order_in_team(race):
    """Índice de cada piloto dentro de su equipo (0 = primero en meta).

    'race' son los resultados de carrera (data.get_race_results).
    """
    order = {}
    seen = {}
    for _, row in race.sort_values("position").iterrows():
        team = row["constructorId"]
        order[row["driverCode"]] = seen.get(team, 0)
        seen[team] = seen.get(team, 0) + 1
    return order


def get_driver_style(driver_code, race, styles=None):
    """Diccionario de estilo (color, linestyle...) listo para ax.plot(**style).

    'styles' es una lista de diccionarios, uno por posición en el equipo.
    Con "color": "auto" se usa el color de la escudería.
    """
    styles = styles or DEFAULT_STYLES
    row = race.loc[race["driverCode"] == driver_code].iloc[0]
    index = driver_order_in_team(race)[driver_code]

    style = dict(styles[min(index, len(styles) - 1)])
    if style.get("color") == "auto":
        style["color"] = team_color(row["constructorId"])
    return style


def add_sorted_driver_legend(ax, race):
    """Leyenda con los pilotos ordenados por posición final en la carrera."""
    finishing = {
        code: i
        for i, code in enumerate(race.sort_values("position")["driverCode"])
    }
    handles, labels = ax.get_legend_handles_labels()
    pairs = sorted(zip(handles, labels), key=lambda p: finishing.get(p[1], 99))
    if pairs:
        sorted_handles, sorted_labels = zip(*pairs)
        return ax.legend(sorted_handles, sorted_labels)
    return None