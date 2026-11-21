"""Descarga y limpieza de datos de F1 desde Jolpica (vía fastf1.ergast)."""

import pandas as pd
from fastf1.ergast import Ergast

from .cache import cached_dataframe

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


def _fetch_all(method, season, round_):
    """Descarga todas las páginas de una consulta paginada.

    Devuelve un DataFrame (vacío si no hay datos).
    """
    frames = []
    offset = 0
    while True:
        response = method(
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
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _download_race_results(season, round_):
    response = Ergast().get_race_results(season=season, round=round_)
    return _first_table(response, season, round_)


def get_race_results(season, round_):
    """Resultado de la carrera."""
    return cached_dataframe(
        "race_results",
        lambda: _download_race_results(season, round_),
        season=season,
        round_=round_,
    )


def _download_qualifying(season, round_):
    response = Ergast().get_qualifying_results(season=season, round=round_)
    df = _first_table(response, season, round_)
    for col in ["Q1", "Q2", "Q3"]:
        df[col] = df[col].apply(to_seconds)
    df["best"] = df[["Q1", "Q2", "Q3"]].min(axis=1)
    return df


def get_qualifying(season, round_):
    """Clasificación con Q1, Q2, Q3 y mejor tiempo ('best') en segundos."""
    return cached_dataframe(
        "qualifying",
        lambda: _download_qualifying(season, round_),
        season=season,
        round_=round_,
    )


def _download_pit_stops(season, round_):
    pit = _fetch_all(Ergast().get_pit_stops, season, round_)
    if pit.empty:
        return pd.DataFrame(columns=["driverId", "stop", "lap"])
    pit["lap"] = pd.to_numeric(pit["lap"])
    return pit


def get_pit_stops(season, round_):
    """Paradas en boxes. Columnas útiles: driverId, stop, lap.

    Si la API no tiene paradas para esa carrera, devuelve un DataFrame vacío.
    """
    return cached_dataframe(
        "pit_stops",
        lambda: _download_pit_stops(season, round_),
        season=season,
        round_=round_,
    )


def _get_lap_times(season, round_):
    """Tiempos por vuelta tal como los devuelve la API (todas las páginas)."""
    return cached_dataframe(
        "lap_times",
        lambda: _fetch_all(Ergast().get_lap_times, season, round_),
        season=season,
        round_=round_,
    )


def add_stints(laps, pit_stops):
    """Añade la columna 'stint' (1, 2, 3...) a cada vuelta.

    Una vuelta pertenece al stint siguiente si el piloto ya había parado
    en una vuelta anterior. La vuelta de entrada a boxes cuenta aún para el
    stint que termina.
    """
    pit_laps = pit_stops.groupby("driverId")["lap"].apply(list).to_dict()
    laps = laps.copy()
    laps["stint"] = [
        1 + sum(pit_lap < lap for pit_lap in pit_laps.get(driver, []))
        for driver, lap in zip(laps["driverId"], laps["lap"])
    ]
    return laps


def get_laps(season, round_):
    """Todas las vueltas de la carrera, con piloto, escudería y stint.

    Columnas: lap, driverId, position, time, seconds, driverCode,
    constructorId, constructorName, stint.
    """
    laps = _get_lap_times(season, round_)
    if laps.empty:
        raise ValueError(
            f"No hay vueltas para la temporada {season}, ronda {round_}."
        )

    laps = laps.rename(columns={"number": "lap"})
    laps["lap"] = pd.to_numeric(laps["lap"])
    laps["position"] = pd.to_numeric(laps["position"], errors="coerce")
    laps["seconds"] = laps["time"].apply(to_seconds)

    race = get_race_results(season, round_)
    drivers = race[["driverId", "driverCode", "constructorId", "constructorName"]]
    laps = laps.merge(drivers, on="driverId", how="left")

    return add_stints(laps, get_pit_stops(season, round_))