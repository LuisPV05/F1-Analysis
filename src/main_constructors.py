"""Campeonato de constructores de una temporada desde la terminal.

Ejemplo:
    py src/main_constructors.py --season 2023 --round 22
    py src/main_constructors.py --season 2025 --round 12 --no-show
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from f1analysis.constructors import (
    get_constructor_progress,
    get_constructor_standings,
    max_points_remaining_constructors,
    round_points,
    who_can_win_constructors,
)
from f1analysis.constructors_plots import (
    plot_constructor_chances,
    plot_constructor_progress,
)
from f1analysis.season_plots import plot_points_heatmap

OUTPUT_DIR = Path("outputs")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Campeonato de constructores de una temporada"
    )
    parser.add_argument("--season", type=int, required=True, help="Año, p. ej. 2023")
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
    suffix = f"{season}_r{round_}"
    OUTPUT_DIR.mkdir(exist_ok=True)
    saved = []

    # --- Quién puede ganar aún el campeonato ---
    standings = get_constructor_standings(season, round_)
    max_points = max_points_remaining_constructors(season, round_)
    table = who_can_win_constructors(standings, max_points)

    print(f"Puntos máximos que quedan por disputar por equipo: {max_points}\n")
    columns = ["position", "constructorName", "points", "max_points", "can_win"]
    print(table[columns].to_string(index=False))

    fig = plot_constructor_chances(
        table,
        f"¿Quién puede ganar el campeonato de constructores? "
        f"Temporada {season}, tras la ronda {round_}",
    )
    path = OUTPUT_DIR / f"constructor_chances_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    # --- Evolución de los puntos ---
    print("\nDescargando la clasificación de cada ronda (tarda la primera vez)...")
    cumulative, names, labels = get_constructor_progress(
        season, up_to_round=round_, verbose=True
    )

    fig = plot_constructor_progress(
        cumulative,
        names,
        f"Puntos acumulados de los constructores - Temporada {season}",
    )
    path = OUTPUT_DIR / f"constructor_progress_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    # --- Mapa de calor de puntos por carrera ---
    per_round = round_points(cumulative)
    per_round.index = [names[constructor_id] for constructor_id in per_round.index]
    fig = plot_points_heatmap(
        per_round,
        labels,
        f"Puntos por constructor y carrera - Temporada {season}",
    )
    path = OUTPUT_DIR / f"constructor_heatmap_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    print()
    for path in saved:
        print(f"Guardado: {path}")

    if args.no_show:
        plt.close("all")
    else:
        plt.show()


if __name__ == "__main__":
    main()