"""Cálculos sobre los datos de clasificación y vueltas."""


def qualifying_delta(qualifying):
    """Ordena por mejor tiempo y añade 'delta' (segundos respecto a la pole)."""
    df = qualifying.dropna(subset=["best"]).sort_values("best").copy()
    df["delta"] = df["best"] - df["best"].iloc[0]
    return df


def fastest_lap(laps):
    """Fila de la vuelta más rápida de la carrera."""
    return laps.loc[laps["seconds"].idxmin()]


def best_lap_per_driver(laps):
    """Mejor vuelta (s) de cada piloto, de menor a mayor."""
    return laps.groupby("driverCode")["seconds"].min().sort_values().round(3)


def clean_race_laps(driver_laps, factor=1.07):
    """Quita vueltas muy lentas (salida, boxes, coche de seguridad).

    Descarta las vueltas por encima de factor * la mediana del piloto.
    """
    limit = driver_laps["seconds"].median() * factor
    return driver_laps[driver_laps["seconds"] < limit]