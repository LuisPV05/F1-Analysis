"""Análisis de una carrera de F1 desde la terminal.

Ejemplo:
    py src/main.py --season 2021 --round 7
    py src/main.py --season 2023 --round 1 --top 5 --driver ALO --no-show
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from f1analysis.analysis import (
    best_lap_per_driver,
    fastest_lap,
    qualifying_delta,
)
from f1analysis.data import get_laps, get_qualifying, get_race_results
from f1analysis.plots import (
    plot_driver_laptimes,
    plot_laptime_distribution,
    plot_position_changes,
    plot_qualifying_delta,
    plot_race_pace,
    plot_strategy,
    plot_team_pace,
)

OUTPUT_DIR = Path("outputs")


def parse_args():
    parser = argparse.ArgumentParser(description="Análisis de una carrera de F1")
    parser.add_argument("--season", type=int, required=True, help="Año, p. ej. 2021")
    parser.add_argument("--round", type=int, required=True, help="Número de ronda")
    parser.add_argument(
        "--top", type=int, default=4, help="Pilotos a mostrar en el ritmo (def. 4)"
    )
    parser.add_argument(
        "--driver",
        type=str,
        default=None,
        help="Código del piloto para la dispersión de vueltas (def. ganador)",
    )
    parser.add_argument(
        "--no-show", action="store_true", help="Guardar las gráficas sin abrirlas"
    )
    return parser.parse_args()


def save(fig, filename, saved):
    """Guarda la figura en outputs/ y apunta la ruta."""
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=150)
    saved.append(path)


def main():
    args = parse_args()
    season, round_ = args.season, args.round
    OUTPUT_DIR.mkdir(exist_ok=True)

    race = get_race_results(season, round_)
    race_name = f"{season} ronda {round_}"
    suffix = f"{season}_r{round_}"
    saved = []

    # --- Clasificación ---
    qualifying = qualifying_delta(get_qualifying(season, round_))
    fig = plot_qualifying_delta(
        qualifying, f"Clasificación {race_name}: diferencia con la pole"
    )
    save(fig, f"qualifying_delta_{suffix}.png", saved)

    # --- Vueltas ---
    laps = get_laps(season, round_)
    best = fastest_lap(laps)
    print(
        f"Vuelta rápida: {best['driverCode']} en {best['seconds']:.3f} s "
        f"(vuelta {best['lap']})"
    )
    print("\nMejor vuelta por piloto:")
    print(best_lap_per_driver(laps))

    # Ritmo de los primeros
    top = race.sort_values("position")["driverCode"].head(args.top).tolist()
    fig = plot_race_pace(
        laps, race, top, f"Ritmo de carrera {race_name} (top {args.top})"
    )
    save(fig, f"race_pace_{suffix}.png", saved)

    # Dispersión de vueltas de un piloto (por defecto, el ganador)
    driver = args.driver or top[0]
    fig = plot_driver_laptimes(
        laps, driver, f"Tiempos de vuelta de {driver} - {race_name}"
    )
    save(fig, f"laptimes_{driver}_{suffix}.png", saved)

    # Distribución de vueltas de los puntuables
    fig = plot_laptime_distribution(
        laps, race, f"Distribución de tiempos de vuelta - {race_name}"
    )
    save(fig, f"laptimes_distribution_{suffix}.png", saved)

    # --- Estrategia y resultados ---
    fig = plot_position_changes(laps, race, f"Cambios de posición - {race_name}")
    save(fig, f"position_changes_{suffix}.png", saved)

    fig = plot_team_pace(laps, f"Ritmo por escudería - {race_name}")
    save(fig, f"team_pace_{suffix}.png", saved)

    fig = plot_strategy(laps, race, f"Estrategias por stints - {race_name}")
    save(fig, f"strategy_{suffix}.png", saved)

    print()
    for path in saved:
        print(f"Guardado: {path}")

    if args.no_show:
        plt.close("all")
    else:
        plt.show()


if __name__ == "__main__":
    main()