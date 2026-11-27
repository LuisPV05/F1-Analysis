"""Conjunto de datos para predecir la posición final de un piloto en carrera.

Cada fila es un piloto en una carrera. Las variables usan solo información
disponible *antes* de esa carrera: la posición de salida y el historial de
las carreras anteriores. Así el conjunto de datos no "ve el futuro".
"""

import pandas as pd

from .data import get_season_race_results

FORM_WINDOW = 5  # carreras anteriores para la forma del piloto y del equipo
DNF_WINDOW = 10  # carreras anteriores para la tasa de abandonos

TARGET = "position"
FEATURE_COLUMNS = [
    "grid",
    "field_size",
    "driver_form",
    "team_form",
    "driver_dnf_rate",
]
KEY_COLUMNS = ["season", "round", "driverId", "constructorId"]
RESULT_COLUMNS = ["driverId", "constructorId", "grid", "position", "status"]


def is_finish(status):
    """True si el piloto vio la bandera (acabó o terminó doblado).

    Jolpica usa 'Finished' y '+1 Lap', '+2 Laps'... para los que terminan, y
    el motivo (Engine, Collision...) para los que abandonan.
    """
    text = str(status)
    return text == "Finished" or text == "Lapped" or text.startswith("+")


def get_race_table(season, verbose=False):
    """Resultados de todas las carreras de una temporada, una fila por piloto.

    Columnas: season, round, driverId, constructorId, grid, position, status.
    Los resultados se descargan por temporada, en pocas peticiones.
    """
    if verbose:
        print(f"  Descargando temporada {season}...")

    race = get_season_race_results(season)
    table = race[["round"] + RESULT_COLUMNS].copy()
    table.insert(0, "season", season)
    for column in ["grid", "position"]:
        table[column] = pd.to_numeric(table[column], errors="coerce")
    table = table.sort_values("round", kind="stable")
    return table.dropna(subset=["position"])


def add_features(results):
    """Añade las variables de predicción a una tabla de resultados.

    'results' necesita las columnas season, round, driverId, constructorId,
    grid, position y status. Las variables de forma de cada carrera se
    calculan solo con las carreras anteriores (cronológicamente), de modo que
    la primera carrera de un piloto o de un equipo queda sin valor (NaN).

    Devuelve KEY_COLUMNS, status, FEATURE_COLUMNS y TARGET, sin modificar la
    tabla original.
    """
    df = results.sort_values(["season", "round"], kind="stable").reset_index(drop=True)

    df["field_size"] = df.groupby(["season", "round"])["driverId"].transform("count")
    # grid == 0 es salir desde el pit lane: cuenta como salir el último
    df["grid"] = df["grid"].where(df["grid"] > 0, df["field_size"])
    df["dnf"] = (~df["status"].apply(is_finish)).astype(float)

    # Forma del piloto: solo carreras anteriores (shift(1) deja fuera la actual)
    by_driver = df.groupby("driverId")
    df["driver_form"] = by_driver["position"].transform(
        lambda s: s.shift(1).rolling(FORM_WINDOW, min_periods=1).mean()
    )
    df["driver_dnf_rate"] = by_driver["dnf"].transform(
        lambda s: s.shift(1).rolling(DNF_WINDOW, min_periods=1).mean()
    )

    # Forma del equipo: posición media de sus coches en cada carrera, y de ahí
    # la media de las carreras anteriores
    team_races = (
        df.groupby(["constructorId", "season", "round"], as_index=False)["position"]
        .mean()
        .rename(columns={"position": "team_position"})
        .sort_values(["season", "round"], kind="stable")
    )
    team_races["team_form"] = team_races.groupby("constructorId")[
        "team_position"
    ].transform(lambda s: s.shift(1).rolling(FORM_WINDOW, min_periods=1).mean())
    df = df.merge(
        team_races[["constructorId", "season", "round", "team_form"]],
        on=["constructorId", "season", "round"],
        how="left",
    )

    return df[KEY_COLUMNS + ["status"] + FEATURE_COLUMNS + [TARGET]]


def build_dataset(start, end, verbose=False):
    """Conjunto de datos de las temporadas entre 'start' y 'end' (incluidas)."""
    if start > end:
        raise ValueError("La primera temporada no puede ser posterior a la última.")
    tables = [get_race_table(season, verbose=verbose) for season in range(start, end + 1)]
    return add_features(pd.concat(tables, ignore_index=True))


def split_by_season(dataset, test_season):
    """Separa los datos en entrenamiento (temporadas anteriores) y prueba.

    Se entrena con el pasado y se prueba con una temporada posterior, como
    ocurriría de verdad: nunca se mezclan carreras al azar.
    """
    train = dataset[dataset["season"] < test_season]
    test = dataset[dataset["season"] == test_season]
    if test.empty:
        raise ValueError(f"La temporada {test_season} no está en el conjunto de datos.")
    if train.empty:
        raise ValueError(f"No hay temporadas anteriores a {test_season} para entrenar.")
    return train.copy(), test.copy()


def baseline_mae(dataset):
    """Error medio, en posiciones, de la referencia "termina donde sale"."""
    return float((dataset[TARGET] - dataset["grid"]).abs().mean())


def baseline_mae_by_season(dataset):
    """Igual que baseline_mae, desglosado por temporada."""
    errors = (dataset[TARGET] - dataset["grid"]).abs()
    return errors.groupby(dataset["season"]).mean()