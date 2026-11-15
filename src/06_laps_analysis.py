from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from fastf1.ergast import Ergast

SEASON = 2021
ROUND = 7
PAGE = 100  # filas por petición


def to_seconds(value):
    if pd.isna(value):
        return float("nan")
    if isinstance(value, pd.Timedelta):
        return value.total_seconds()
    return float(value)


def fetch_all_laps(ergast, season, round_):
    """Descarga todas las vueltas de una carrera pidiendo páginas de PAGE filas."""
    frames = []
    offset = 0
    while True:
        resp = ergast.get_lap_times(
            season=season, round=round_, limit=PAGE, offset=offset
        )
        if not resp.content:
            break
        page = resp.content[0]
        if page.empty:
            break
        frames.append(page)
        if len(page) < PAGE:
            break
        offset += PAGE
    return pd.concat(frames, ignore_index=True)


ergast = Ergast()

# --- Vueltas de la carrera ---
laps = fetch_all_laps(ergast, SEASON, ROUND)
laps = laps.rename(columns={"number": "lap"})
laps["seconds"] = laps["time"].apply(to_seconds)
print(f"Vueltas descargadas: {len(laps)}")
print(f"Última vuelta: {laps['lap'].max()}")

# --- Añadir código de piloto y escudería desde los resultados de carrera ---
race = ergast.get_race_results(season=SEASON, round=ROUND).content[0]
drivers = race[["driverId", "driverCode", "constructorName"]]
laps = laps.merge(drivers, on="driverId", how="left")

# --- Equivalente a pick_fastest(): vuelta rápida de la carrera ---
fastest = laps.loc[laps["seconds"].idxmin()]
print(
    f"\nVuelta rápida: {fastest['driverCode']} "
    f"en {fastest['seconds']:.3f} s (vuelta {fastest['lap']})"
)

# --- Mejor vuelta de cada piloto ---
best_per_driver = (
    laps.groupby("driverCode")["seconds"].min().sort_values().round(3)
)
print("\nMejor vuelta por piloto:")
print(best_per_driver)

# --- Gráfica: ritmo de los 4 primeros ---
top4 = race.sort_values("position")["driverCode"].head(4).tolist()
fig, ax = plt.subplots(figsize=(11, 6))

for code in top4:
    d = laps[laps["driverCode"] == code].sort_values("lap")
    # Quitamos vueltas muy lentas (salida, boxes, coche de seguridad)
    d = d[d["seconds"] < d["seconds"].median() * 1.07]
    ax.plot(d["lap"], d["seconds"], marker="o", markersize=3, label=code)

ax.set_xlabel("Vuelta")
ax.set_ylabel("Tiempo de vuelta (s)")
ax.set_title(f"Ritmo de carrera GP de Francia {SEASON} (top 4)")
ax.legend()
plt.tight_layout()

output = Path("outputs")
output.mkdir(exist_ok=True)
fig.savefig(output / "race_pace.png", dpi=150)
print("\nGuardado en outputs/race_pace.png")
plt.show()