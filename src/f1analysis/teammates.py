"""Duelos entre compañeros de equipo: clasificación, carrera y puntos."""

from itertools import combinations

import pandas as pd

from .data import get_qualifying, get_race_results

# Tope de rondas que se intentan: el calendario más largo ha tenido 24.
MAX_ROUNDS = 30

SUMMARY_COLUMNS = [
    "constructorId",
    "constructorName",
    "driver_a",
    "driver_b",
    "rounds",
    "quali_wins_a",
    "quali_wins_b",
    "race_wins_a",
    "race_wins_b",
    "points_a",
    "points_b",
]


def _weekend(season, round_):
    """Resultados de un fin de semana: una fila por piloto.

    Columnas: driverId, driverCode, constructorId, constructorName,
    race_pos, points y quali_pos (NaN si no hay datos de clasificación).
    Devuelve None si la carrera todavía no se ha disputado. Los reintentos
    ante fallos de red los hace la capa de datos.
    """
    try:
        race = get_race_results(season, round_)
    except ValueError:
        return None

    try:
        qualifying = get_qualifying(season, round_)
    except ValueError:
        qualifying = None

    codes = (
        race["driverCode"]
        if "driverCode" in race.columns
        else pd.Series(pd.NA, index=race.index)
    )
    table = pd.DataFrame(
        {
            "driverId": race["driverId"],
            "driverCode": codes.fillna(race["familyName"].str[:3].str.upper()),
            "constructorId": race["constructorId"],
            "constructorName": race["constructorName"],
            "race_pos": pd.to_numeric(race["position"], errors="coerce"),
            "points": pd.to_numeric(race["points"], errors="coerce").fillna(0),
        }
    )

    table["quali_pos"] = float("nan")
    if qualifying is not None:
        positions = pd.to_numeric(
            qualifying.set_index("driverId")["position"], errors="coerce"
        )
        table["quali_pos"] = table["driverId"].map(positions)
    return table


def get_weekend_results(season, up_to_round=None, verbose=False):
    """Resultados de todos los fines de semana de una temporada.

    Devuelve un DataFrame con una fila por piloto y ronda (columna 'round').
    Recorre las rondas en orden y se detiene en la primera sin resultados,
    así que no necesita el calendario.
    """
    last_round = MAX_ROUNDS if up_to_round is None else up_to_round

    frames = []
    for round_ in range(1, last_round + 1):
        if verbose:
            print(f"  Descargando ronda {round_}...")
        weekend = _weekend(season, round_)
        if weekend is None:
            break  # carrera aún no disputada
        weekend.insert(0, "round", round_)
        frames.append(weekend)

    if not frames:
        raise ValueError(f"No hay resultados para la temporada {season}.")
    return pd.concat(frames, ignore_index=True)


def _ahead(first, second):
    """1.0 si 'first' acaba por delante de 'second' (posición menor).

    0.0 si no, y NaN si falta alguno de los dos datos.
    """
    if pd.isna(first) or pd.isna(second):
        return float("nan")
    return 1.0 if first < second else 0.0


def _put_leader_first(summary):
    """Intercambia a y b en las parejas donde b suma más puntos que a."""
    swap = summary["points_a"] < summary["points_b"]
    result = summary.copy()
    for field in ["driver", "quali_wins", "race_wins", "points"]:
        result.loc[swap, f"{field}_a"] = summary.loc[swap, f"{field}_b"]
        result.loc[swap, f"{field}_b"] = summary.loc[swap, f"{field}_a"]
    return result


def teammate_duels(weekends):
    """Resumen de los duelos entre compañeros de equipo.

    'weekends' viene de get_weekend_results(). Una fila por pareja de pilotos
    de una misma escudería, con las columnas de SUMMARY_COLUMNS:
      - rounds: carreras en las que fueron compañeros.
      - quali_wins_a/b y race_wins_a/b: veces que cada uno acabó por delante
        (se ignoran las rondas sin dato de alguno de los dos).
      - points_a/b: puntos de carrera en esas rondas, sin contar sprints.
    El piloto 'a' es el que más puntos suma en los duelos. Las escuderías van
    ordenadas por los puntos de sus dos pilotos, de más a menos.

    Una posición menor es mejor. En carrera, los abandonos quedan por detrás
    de los que terminan, según la clasificación oficial.
    """
    rows = []
    for (round_, constructor_id), group in weekends.groupby(
        ["round", "constructorId"]
    ):
        drivers = group.sort_values("driverId").to_dict("records")
        for first, second in combinations(drivers, 2):
            rows.append(
                {
                    "constructorId": constructor_id,
                    "constructorName": first["constructorName"],
                    "round": round_,
                    "driver_a": first["driverCode"],
                    "driver_b": second["driverCode"],
                    "quali_a_ahead": _ahead(first["quali_pos"], second["quali_pos"]),
                    "race_a_ahead": _ahead(first["race_pos"], second["race_pos"]),
                    "points_a": first["points"],
                    "points_b": second["points"],
                }
            )

    if not rows:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    summary = (
        pd.DataFrame(rows)
        .groupby(
            ["constructorId", "constructorName", "driver_a", "driver_b"],
            as_index=False,
        )
        .agg(
            rounds=("round", "count"),
            quali_wins_a=("quali_a_ahead", lambda s: int((s == 1).sum())),
            quali_wins_b=("quali_a_ahead", lambda s: int((s == 0).sum())),
            race_wins_a=("race_a_ahead", lambda s: int((s == 1).sum())),
            race_wins_b=("race_a_ahead", lambda s: int((s == 0).sum())),
            points_a=("points_a", "sum"),
            points_b=("points_b", "sum"),
        )
    )
    summary = _put_leader_first(summary)

    order = (summary["points_a"] + summary["points_b"]).sort_values(ascending=False)
    return summary.loc[order.index, SUMMARY_COLUMNS].reset_index(drop=True)