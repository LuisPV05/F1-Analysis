"""Descarga y limpieza de datos de F1 desde Jolpica (vía fastf1.ergast)."""

import pandas as pd
from fastf1.ergast import Ergast

PAGE_SIZE = 100  # filas por petición a la API


def to_seconds(value):
    """Convierte Timedelta o texto 'm:ss.mmm' a segundos. Vacío -> NaN."""
    if pd.isna(value):
        return float("nan")
    if isinstance(value, pd.Timedelta):
        return value.total_seconds()
    text = str(value).strip()
    if not text:
        return float("nan")
    if ":" in text:
        minutes, seconds = text.split(":")
        return int(minutes) * 60 + float(seconds)
    return float(text)


def _first_table(response, season, round_):
    """Devuelve el primer DataFrame de una respuesta o un error claro."""
    if not response.content or response.content[0].empty:
        raise ValueError(
            f"No hay datos para la temporada {season}, ronda {round_}."
        )
    return response.content[0].copy()


def get_race_results(season, round_):
    """Resultado de la carrera."""
    response = Ergast().get_race_results(season=season, round=round_)
    return _first_table(response, season, round_)


def get_qualifying(season, round_):
    """Clasificación con Q1, Q2, Q3 y mejor tiempo ('best') en segundos."""
    response = Ergast().get_qualifying_results(season=season, round=round_)
    df = _first_table(response, season, round_)
    for col in ["Q1", "Q2", "Q3"]:
        df[col] = df[col].apply(to_seconds)
    df["best"] = df[["Q1", "Q2", "Q3"]].min(axis=1)
    return df


def get_laps(season, round_):
    """Todas las vueltas de la carrera, con piloto y escudería.

    Columnas: lap, driverId, position, time, seconds, driverCode,
    constructorName.
    """
    ergast = Ergast()
    frames = []
    offset = 0
    while True:
        response = ergast.get_lap_times(
            season=season, round=round_, limit=PAGE_SIZE, offset=offset
        )
        if not response.content or response.content[0].empty:
            break
        page = response.content[0]
        frames.append(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    if not frames:
        raise ValueError(
            f"No hay vueltas para la temporada {season}, ronda {round_}."
        )

    laps = pd.concat(frames, ignore_index=True)
    laps = laps.rename(columns={"number": "lap"})
    laps["seconds"] = laps["time"].apply(to_seconds)

    race = get_race_results(season, round_)
    drivers = race[["driverId", "driverCode", "constructorName"]]
    return laps.merge(drivers, on="driverId", how="left")