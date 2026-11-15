import pandas as pd
from fastf1.ergast import Ergast

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

ergast = Ergast()

# --- Clasificación: columnas útiles con los tiempos de Q3 ---
qualifying = ergast.get_qualifying_results(season=2021, round=7)
df_q = qualifying.content[0]
print("Top 10 y tiempos de Q3:")
print(df_q[["position", "driverCode", "constructorName", "Q3"]].head(10))

# --- Tiempos por vuelta de la carrera (GP de Francia 2021) ---
laps = ergast.get_lap_times(season=2021, round=7, limit=2000)
print("\nTipo de respuesta:", type(laps))
print("Número de DataFrames:", len(laps.content))
print("Descripción:\n", laps.description)

df_laps = laps.content[0]
print("\nColumnas:", df_laps.columns.tolist())
print(df_laps.head())