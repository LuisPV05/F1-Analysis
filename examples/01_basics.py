import fastf1

# Activa la caché para no descargar los datos cada vez
fastf1.Cache.enable_cache("cache")

# --- Cargar una sesión: Qualifying de la carrera 7 de 2021 ---
session = fastf1.get_session(2021, 7, "Q")
print("Sesión:", session.name)
print("Fecha:", session.date)

# --- El evento al que pertenece la sesión ---
event = session.event
print("\nEvento:", event["EventName"])
print("País:", event["Country"])
print("Fecha de la carrera:", event["EventDate"])

# --- Cargar un evento directamente y sacar la carrera ---
event = fastf1.get_event(2021, 7)
race = event.get_race()
print("\nSesión obtenida desde el evento:", race.name)

# --- Cargar por nombre (no hace falta el nombre exacto) ---
event = fastf1.get_event(2021, "Emilia Romagna")
print("\nPor nombre:", event["EventName"])

# --- Cargar por localización ---
session = fastf1.get_session(2021, "Silverstone", "Q")
print("Por localización:", session.event["EventName"])