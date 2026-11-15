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
    plot_qualifying_delta,
    plot_race_pace,
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
    path = OUTPUT_DIR / f"qualifying_delta_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

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
    path = OUTPUT_DIR / f"race_pace_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    # Dispersión de vueltas de un piloto (por defecto, el ganador)
    driver = args.driver or top[0]
    fig = plot_driver_laptimes(
        laps, driver, f"Tiempos de vuelta de {driver} - {race_name}"
    )
    path = OUTPUT_DIR / f"laptimes_{driver}_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    # Distribución de vueltas de los puntuables
    fig = plot_laptime_distribution(
        laps, race, f"Distribución de tiempos de vuelta - {race_name}"
    )
    path = OUTPUT_DIR / f"laptimes_distribution_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    print()
    for path in saved:
        print(f"Guardado: {path}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()