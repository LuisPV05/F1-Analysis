from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from fastf1.ergast import Ergast

SEASON = 2021
ROUND = 7


def to_seconds(value):
    """Convierte Timedelta o texto 'm:ss.mmm' a segundos. NaT/None -> NaN."""
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


ergast = Ergast()
df = ergast.get_qualifying_results(season=SEASON, round=ROUND).content[0].copy()

# Mejor tiempo de cada piloto entre Q1, Q2 y Q3
for col in ["Q1", "Q2", "Q3"]:
    df[col] = df[col].apply(to_seconds)
df["best"] = df[["Q1", "Q2", "Q3"]].min(axis=1)
df = df.dropna(subset=["best"]).sort_values("best")

# Diferencia respecto a la pole
df["delta"] = df["best"] - df["best"].iloc[0]

# Un color por escudería
teams = df["constructorName"].unique()
palette = plt.get_cmap("tab10")
team_color = {team: palette(i % 10) for i, team in enumerate(teams)}
colors = [team_color[t] for t in df["constructorName"]]

# Gráfica
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(df["driverCode"], df["delta"], color=colors)
ax.invert_yaxis()  # el poleman arriba
ax.set_xlabel("Diferencia con la pole (s)")
ax.set_title(f"Clasificación GP de Francia {SEASON}: diferencia con la pole")

# Etiqueta con la diferencia al final de cada barra
for y, delta in enumerate(df["delta"]):
    ax.text(delta + 0.005, y, f"+{delta:.3f}", va="center", fontsize=8)

plt.tight_layout()

# Guardar en outputs/ y mostrar
output = Path("outputs")
output.mkdir(exist_ok=True)
fig.savefig(output / "qualifying_delta.png", dpi=150)
print("Guardado en outputs/qualifying_delta.png")
plt.show()