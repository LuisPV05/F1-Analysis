from fastf1.ergast import Ergast

# Jolpica/Ergast no necesita cuenta de F1 ni caché
ergast = Ergast()

# --- Clasificación del GP de Francia 2021 (ronda 7) ---
qualifying = ergast.get_qualifying_results(season=2021, round=7)
df = qualifying.content[0]

print(df.columns.tolist())
print(df.head(10))

# --- Resultado de la carrera ---
race = ergast.get_race_results(season=2021, round=7)
print(race.content[0].head(10))