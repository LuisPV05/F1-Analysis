"""Datos a lo largo de varias temporadas."""

import pandas as pd
from fastf1.ergast import Ergast

from .season import _with_retry


def _first_item(value):
    """Primer elemento si 'value' es una lista; si no, el propio valor."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def get_champions(start, end, verbose=False):
    """Campeón y subcampeón de cada temporada entre 'start' y 'end' (incluidas).

    Devuelve un DataFrame con una fila por temporada y las columnas:
    season, champion, champion_points, champion_wins, champion_team,
    champion_team_id, runner_up, runner_up_points y margin (diferencia de
    puntos entre ambos).

    En una temporada sin terminar, el "campeón" es el líder actual.
    """
    ergast = Ergast()
    rows = []

    for season in range(start, end + 1):
        if verbose:
            print(f"  Descargando temporada {season}...")
        response = _with_retry(
            lambda: ergast.get_driver_standings(season=season)
        )
        if not response.content or response.content[0].empty:
            continue

        standings = response.content[0].copy()
        for col in ["position", "points", "wins"]:
            standings[col] = pd.to_numeric(standings[col], errors="coerce")
        standings = standings.sort_values("position")

        first = standings.iloc[0]
        second = standings.iloc[1] if len(standings) > 1 else None

        rows.append(
            {
                "season": season,
                "champion": first["familyName"],
                "champion_points": first["points"],
                "champion_wins": first["wins"],
                "champion_team": _first_item(first["constructorNames"]),
                "champion_team_id": _first_item(first["constructorIds"]),
                "runner_up": None if second is None else second["familyName"],
                "runner_up_points": float("nan") if second is None else second["points"],
                "margin": (
                    float("nan") if second is None else first["points"] - second["points"]
                ),
            }
        )

    if not rows:
        raise ValueError(f"No hay clasificaciones entre {start} y {end}.")
    return pd.DataFrame(rows)