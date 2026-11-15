import fastf1

fastf1.Cache.enable_cache("cache")

# --- Calendario completo de una temporada ---
schedule = fastf1.get_event_schedule(2021)
print(schedule[["RoundNumber", "Country", "EventName", "EventDate"]])

# --- Columnas disponibles ---
print("\nColumnas:")
print(list(schedule.columns))

# --- Seleccionar eventos concretos ---
gp_12 = schedule.get_event_by_round(12)
print("\nRonda 12:", gp_12["EventName"], "-", gp_12["Country"])

gp_austin = schedule.get_event_by_name("Austin")
print("Austin:", gp_austin["EventName"], "-", gp_austin["Country"])