"""Datos y cálculos a nivel de temporada: clasificaciones y puntos."""

import fastf1
import pandas as pd
from fastf1.ergast import Ergast

# Sistema de puntos actual: victoria en carrera y victoria en sprint.
RACE_WIN_POINTS = 25
SPRINT_WIN_POINTS = 8

# Nombres que FastF1 ha usado para los fines de semana con sprint.
SPRINT_FORMATS = {"sprint", "sprint_shootout", "sprint_qualifying"}


def get_driver_standings(season, round_):
    """Clasificación de pilotos tras la ronda indicada."""
    response = Ergast().get_driver_standings(season=season, round=round_)
    if not response.content or response.content[0].empty:
        raise ValueError(
            f"No hay clasificación para la temporada {season}, ronda {round_}."
        )
    standings = response.content[0].copy()
    standings["position"] = pd.to_numeric(standings["position"])
    standings["points"] = pd.to_numeric(standings["points"])
    return standings


def max_points_remaining(season, round_):
    """Máximo de puntos que un piloto puede sumar en lo que queda de temporada.

    Supone ganar todas las carreras (25) y todos los sprints (8) restantes.
    Válido para el sistema de puntos actual.
    """
    schedule = fastf1.get_event_schedule(
        season, include_testing=False, backend="ergast"
    )
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