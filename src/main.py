"""Análisis de una carrera de F1 desde la terminal.

Ejemplo:
    py src/main.py --season 2021 --round 7
    py src/main.py --season 2023 --round 1 --top 5 --no-show
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
from f1analysis.plots import plot_qualifying_delta, plot_race_pace

OUTPUT_DIR = Path("outputs")


def parse_args():
    parser = argparse.ArgumentParser(description="Análisis de una carrera de F1")
    parser.add_argument("--season", type=int, required=True, help="Año, p. ej. 2021")
    parser.add_argument("--round", type=int, required=True, help="Número de ronda")
    parser.add_argument(
        "--top", type=int, default=4, help="Pilotos a mostrar en el ritmo (def. 4)"
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

    # --- Clasificación ---
    qualifying = qualifying_delta(get_qualifying(season, round_))
    fig_q = plot_qualifying_delta(
        qualifying, f"Clasificación {race_name}: diferencia con la pole"
    )
    path_q = OUTPUT_DIR / f"qualifying_delta_{season}_r{round_}.png"
    fig_q.savefig(path_q, dpi=150)

    # --- Vueltas y ritmo ---
    laps = get_laps(season, round_)
    best = fastest_lap(laps)
    print(
        f"Vuelta rápida: {best['driverCode']} en {best['seconds']:.3f} s "
        f"(vuelta {best['lap']})"
    )
    print("\nMejor vuelta por piloto:")
    print(best_lap_per_driver(laps))

    top = race.sort_values("position")["driverCode"].head(args.top).tolist()
    fig_p = plot_race_pace(
        laps, race, top, f"Ritmo de carrera {race_name} (top {args.top})"
    )
    path_p = OUTPUT_DIR / f"race_pace_{season}_r{round_}.png"
    fig_p.savefig(path_p, dpi=150)

    print(f"\nGuardado: {path_q}")
    print(f"Guardado: {path_p}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()