"""Datos y cálculos a nivel de temporada: clasificaciones y puntos."""

import time

import fastf1
import pandas as pd
from fastf1.ergast import Ergast
from fastf1.exceptions import ErgastInvalidRequestError

from .cache import cached_dataframe

# Sistema de puntos actual: victoria en carrera y victoria en sprint.
RACE_WIN_POINTS = 25
SPRINT_WIN_POINTS = 8

# Nombres que FastF1 ha usado para los fines de semana con sprint.
SPRINT_FORMATS = {"sprint", "sprint_shootout", "sprint_qualifying"}

RETRIES = 5
RETRY_WAIT = 3.0  # segundos; se multiplica por el número de intento


def _with_retry(call):
    """Ejecuta 'call()' y reintenta si Jolpica responde 'Too Many Requests'."""
    for attempt in range(RETRIES):
        try:
            return call()
        except ErgastInvalidRequestError as error:
            too_many = "Too Many Requests" in str(error)
            if not too_many or attempt == RETRIES - 1:
                raise
            time.sleep(RETRY_WAIT * (attempt + 1))


def _get_schedule(season):
    """Calendario de la temporada (sin test de pretemporada) vía Jolpica."""
    return fastf1.get_event_schedule(
        season, include_testing=False, backend="ergast"
    )


def _download_standings(season, round_):
    response = _with_retry(
        lambda: Ergast().get_driver_standings(season=season, round=round_)
    )
    if not response.content or response.content[0].empty:
        raise ValueError(
            f"No hay clasificación para la temporada {season}, ronda {round_}."
        )
    standings = response.content[0].copy()
    standings["position"] = pd.to_numeric(standings["position"])
    standings["points"] = pd.to_numeric(standings["points"])
    return standings


def get_driver_standings(season, round_):
    """Clasificación de pilotos tras la ronda indicada."""
    return cached_dataframe(
        "driver_standings",
        lambda: _download_standings(season, round_),
        season=season,
        round_=round_,
    )


def max_points_remaining(season, round_):
    """Máximo de puntos que un piloto puede sumar en lo que queda de temporada.

    Supone ganar todas las carreras (25) y todos los sprints (8) restantes.
    Válido para el sistema de puntos actual.
    """
    schedule = _get_schedule(season)
    remaining = schedule[schedule["RoundNumber"] > round_]
    sprints = int(remaining["EventFormat"].isin(SPRINT_FORMATS).sum())
    return len(remaining) * RACE_WIN_POINTS + sprints * SPRINT_WIN_POINTS


def who_can_win(standings, max_points):
    """Añade 'max_points' (máximo teórico) y 'can_win' a la clasificación.

    Simplificación: el líder no suma más puntos y no se tienen en cuenta los
    desempates por posiciones. Un empate a puntos cuenta como "puede ganar".
    """
    table = standings.copy()
    if "driverCode" not in table.columns:
        table["driverCode"] = table["familyName"].str[:3].str.upper()

    leader_points = table["points"].max()
    table["max_points"] = table["points"] + max_points
    table["can_win"] = table["max_points"] >= leader_points
    return table.sort_values("position")


def _download_round_results(ergast, season, round_, has_sprint):
    """Puntos y posición de cada piloto en una ronda, sin pasar por la caché.

    Devuelve un DataFrame indexado por driverCode con las columnas:
      - points: puntos de la carrera más los del sprint, si lo hubo.
      - position: posición de llegada en la carrera.
    Devuelve None si la carrera todavía no tiene resultados.
    """
    race = _with_retry(
        lambda: ergast.get_race_results(season=season, round=round_)
    )
    if not race.content or race.content[0].empty:
        return None

    table = race.content[0].set_index("driverCode")[["points", "position"]].copy()
    table["points"] = table["points"].astype(float)
    table["position"] = pd.to_numeric(table["position"], errors="coerce")

    if has_sprint:
        sprint = _with_retry(
            lambda: ergast.get_sprint_results(season=season, round=round_)
        )
        if sprint.content and not sprint.content[0].empty:
            sprint_points = (
                sprint.content[0].set_index("driverCode")["points"].astype(float)
            )
            total = table["points"].add(sprint_points, fill_value=0)
            table = table.reindex(total.index)
            table["points"] = total
    return table


def _round_results(ergast, season, round_, has_sprint):
    """Igual que _download_round_results, pero usando la caché en disco."""
    return cached_dataframe(
        "round_results",
        lambda: _download_round_results(ergast, season, round_, has_sprint),
        season=season,
        round_=round_,
        sprint=has_sprint,
    )


def get_season_data(season, up_to_round=None, verbose=False):
    """Puntos y posiciones de cada piloto en cada ronda de la temporada.

    Devuelve (points, positions, labels):
      - points: DataFrame con una fila por piloto (driverCode) y una columna
        por ronda (número de ronda). 0 si el piloto no puntuó o no corrió.
      - positions: igual, con la posición de llegada (NaN si no corrió).
      - labels: nombres cortos de las carreras, en el orden de las columnas.
    Se detiene en la primera ronda sin resultados.
    """
    schedule = _get_schedule(season)
    rounds = [int(r) for r in schedule["RoundNumber"]]
    names = {
        int(r): name.removesuffix(" Grand Prix")
        for r, name in zip(schedule["RoundNumber"], schedule["EventName"])
    }
    sprint_rounds = {
        int(r)
        for r in schedule.loc[
            schedule["EventFormat"].isin(SPRINT_FORMATS), "RoundNumber"
        ]
    }

    last_round = max(rounds) if up_to_round is None else min(up_to_round, max(rounds))

    ergast = Ergast()
    points_cols = {}
    position_cols = {}
    labels = []
    for round_ in range(1, last_round + 1):
        if verbose:
            print(f"  Descargando ronda {round_}/{last_round}...")
        results = _round_results(ergast, season, round_, round_ in sprint_rounds)
        if results is None:
            break  # carrera aún no disputada
        points_cols[round_] = results["points"]
        position_cols[round_] = results["position"]
        labels.append(names[round_])

    if not points_cols:
        raise ValueError(f"No hay resultados para la temporada {season}.")

    points = pd.DataFrame(points_cols).fillna(0)
    positions = pd.DataFrame(position_cols).reindex(points.index)
    return points, positions, labels