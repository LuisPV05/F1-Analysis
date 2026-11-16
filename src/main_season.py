"""Análisis de una temporada de F1 desde la terminal.

Ejemplo:
    py src/main_season.py --season 2025 --round 12
    py src/main_season.py --season 2025 --round 21 --no-show
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from f1analysis.season import (
    get_driver_standings,
    max_points_remaining,
    who_can_win,
)
from f1analysis.season_plots import plot_title_chances

OUTPUT_DIR = Path("outputs")


def parse_args():
    parser = argparse.ArgumentParser(description="Análisis de una temporada de F1")
    parser.add_argument("--season", type=int, required=True, help="Año, p. ej. 2025")
    parser.add_argument(
        "--round", type=int, required=True, help="Ronda hasta la que se analiza"
    )
    parser.add_argument(
        "--no-show", action="store_true", help="Guardar las gráficas sin abrirlas"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    season, round_ = args.season, args.round
    OUTPUT_DIR.mkdir(exist_ok=True)

    # --- Quién puede ganar aún el campeonato ---
    standings = get_driver_standings(season, round_)
    max_points = max_points_remaining(season, round_)
    table = who_can_win(standings, max_points)

    print(f"Puntos máximos que quedan por disputar: {max_points}\n")
    columns = ["position", "driverCode", "points", "max_points", "can_win"]
    print(table[columns].to_string(index=False))

    fig = plot_title_chances(
        table, f"¿Quién puede ganar el título? Temporada {season}, tras la ronda {round_}"
    )
    path = OUTPUT_DIR / f"title_chances_{season}_r{round_}.png"
    fig.savefig(path, dpi=150)
    print(f"\nGuardado: {path}")

    if args.no_show:
        plt.close("all")
    else:
        plt.show()


if __name__ == "__main__":
    main()