"""Campeonato de constructores: clasificación, opciones al título y evolución."""

import pandas as pd
from fastf1.ergast import Ergast

from .cache import cached_dataframe
from .season import SPRINT_FORMATS, _get_schedule, _with_retry

# Máximo que un equipo puede sumar en un fin de semana: primero y segundo.
RACE_MAX_POINTS = 25 + 18
SPRINT_MAX_POINTS = 8 + 7


def _download_standings(season, round_):
    response = _with_retry(
        lambda: Ergast().get_constructor_standings(season=season, round=round_)
    )
    if not response.content or response.content[0].empty:
        raise ValueError(
            f"No hay clasificación de constructores para la temporada {season}, "
            f"ronda {round_}."
        )
    standings = response.content[0].copy()
    standings["position"] = pd.to_numeric(standings["position"])
    standings["points"] = pd.to_numeric(standings["points"])
    return standings


def get_constructor_standings(season, round_):
    """Clasificación de constructores tras la ronda indicada."""
    return cached_dataframe(
        "constructor_standings",
        lambda: _download_standings(season, round_),
        season=season,
        round_=round_,
    )


def max_points_remaining_constructors(season, round_):
    """Máximo de puntos que un equipo puede sumar en lo que queda de temporada.

    Supone que sus dos pilotos terminan primero y segundo en todas las
    carreras (43) y en todos los sprints (15) restantes. Válido para el
    sistema de puntos actual.
    """
    schedule = _get_schedule(season)
    remaining = schedule[schedule["RoundNumber"] > round_]
    sprints = int(remaining["EventFormat"].isin(SPRINT_FORMATS).sum())
    return len(remaining) * RACE_MAX_POINTS + sprints * SPRINT_MAX_POINTS


def who_can_win_constructors(standings, max_points):
    """Añade 'max_points' (máximo teórico) y 'can_win' a la clasificación.

    Simplificación: el líder no suma más puntos y no se tienen en cuenta los
    desempates. Un empate a puntos cuenta como "puede ganar".
    """
    table = standings.copy()
    leader_points = table["points"].max()
    table["max_points"] = table["points"] + max_points
    table["can_win"] = table["max_points"] >= leader_points
    return table.sort_values("position")


def _cumulative_matrix(standings_by_round):
    """Puntos acumulados de cada equipo tras cada ronda.

    'standings_by_round' es un diccionario {ronda: clasificación}, con las
    columnas constructorId, constructorName y points. Devuelve
    (cumulative, names):
      - cumulative: DataFrame con una fila por equipo (constructorId) y una
        columna por ronda. Un equipo que aún no aparece tiene 0 puntos, y si
        deja de aparecer conserva los que tenía.
      - names: Series con el nombre de cada equipo, indexada por constructorId.
    """
    columns = {}
    names = {}
    for round_, standings in standings_by_round.items():
        indexed = standings.set_index("constructorId")
        columns[round_] = indexed["points"]
        names.update(indexed["constructorName"].to_dict())

    cumulative = pd.DataFrame(columns).ffill(axis=1).fillna(0)
    return cumulative, pd.Series(names)


def round_points(cumulative):
    """Puntos que suma cada equipo en cada ronda (diferencia entre rondas).

    Una sanción que reste puntos puede dar un valor negativo.
    """
    per_round = cumulative.diff(axis=1)
    per_round.iloc[:, 0] = cumulative.iloc[:, 0]
    return per_round


def get_constructor_progress(season, up_to_round=None, verbose=False):
    """Puntos acumulados de cada constructor tras cada ronda de la temporada.

    Devuelve (cumulative, names, labels):
      - cumulative y names, como en _cumulative_matrix.
      - labels: nombres cortos de las carreras, en el orden de las columnas.
    Se detiene en la primera ronda sin clasificación.
    """
    schedule = _get_schedule(season)
    last_round = max(int(r) for r in schedule["RoundNumber"])
    if up_to_round is not None:
        last_round = min(up_to_round, last_round)
    race_names = {
        int(r): name.removesuffix(" Grand Prix")
        for r, name in zip(schedule["RoundNumber"], schedule["EventName"])
    }

    frames = {}
    for round_ in range(1, last_round + 1):
        if verbose:
            print(f"  Descargando ronda {round_}/{last_round}...")
        try:
            frames[round_] = get_constructor_standings(season, round_)
        except ValueError:
            break  # carrera aún no disputada

    if not frames:
        raise ValueError(f"No hay clasificación de constructores en {season}.")

    cumulative, names = _cumulative_matrix(frames)
    labels = [race_names[int(r)] for r in cumulative.columns]
    return cumulative, names, labels