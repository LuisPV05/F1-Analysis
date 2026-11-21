"""Datos a lo largo de varias temporadas."""

import pandas as pd
from fastf1.ergast import Ergast

from .cache import cached_dataframe
from .season import _with_retry


def _first_item(value):
    """Primer elemento si 'value' es una lista; si no, el propio valor."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _download_season_standings(ergast, season):
    response = _with_retry(
        lambda: ergast.get_driver_standings(season=season)
    )
    if not response.content or response.content[0].empty:
        return None

    standings = response.content[0].copy()
    for col in ["position", "points", "wins"]:
        standings[col] = pd.to_numeric(standings[col], errors="coerce")
    return standings.sort_values("position")


def _season_standings(ergast, season):
    """Clasificación final de pilotos de una temporada, ordenada por posición.

    Devuelve None si la temporada no tiene datos.
    """
    return cached_dataframe(
        "final_standings",
        lambda: _download_season_standings(ergast, season),
        season=season,
    )


def _find_driver(standings, query):
    """Fila del piloto que coincide con 'query' (o None si no corrió).

    Busca sin distinguir mayúsculas en driverId ('max_verstappen'),
    driverCode ('VER') y apellido ('Verstappen'). Si el apellido coincide
    con varios pilotos, devuelve el mejor clasificado.
    """
    query = query.lower()
    mask = pd.Series(False, index=standings.index)
    for column in ("driverId", "driverCode", "familyName"):
        if column in standings.columns:
            mask |= standings[column].astype(str).str.lower() == query
    found = standings[mask]
    return None if found.empty else found.iloc[0]


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
        standings = _season_standings(ergast, season)
        if standings is None:
            continue

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


def get_driver_comparison(start, end, drivers, verbose=False):
    """Puntos, victorias y posición final de varios pilotos por temporada.

    'drivers' es una lista de identificadores (driverId, código o apellido;
    mejor el driverId para evitar ambigüedades, p. ej. 'max_verstappen').

    Devuelve (comparison, order):
      - comparison: DataFrame con una fila por piloto y temporada en la que
        corrió: season, driver, points, wins, position y team_id.
      - order: nombres de los pilotos en el orden en que se pidieron.
    """
    ergast = Ergast()
    rows = []
    names = {}

    for season in range(start, end + 1):
        if verbose:
            print(f"  Descargando temporada {season}...")
        standings = _season_standings(ergast, season)
        if standings is None:
            continue

        for query in drivers:
            row = _find_driver(standings, query)
            if row is None:
                continue  # no corrió esa temporada
            names.setdefault(query, f"{row['givenName']} {row['familyName']}")
            rows.append(
                {
                    "season": season,
                    "driver": names[query],
                    "points": row["points"],
                    "wins": row["wins"],
                    "position": row["position"],
                    "team_id": _first_item(row["constructorIds"]),
                }
            )

    missing = [query for query in drivers if query not in names]
    if missing:
        raise ValueError(
            f"No se encontró a {', '.join(missing)} entre {start} y {end}. "
            "Prueba con el identificador de Jolpica, p. ej. 'max_verstappen'."
        )

    order = [names[query] for query in drivers]
    return pd.DataFrame(rows), order