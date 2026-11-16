"""Análisis de una temporada de F1 desde la terminal.

Ejemplo:
    py src/main_season.py --season 2025 --round 12
    py src/main_season.py --season 2022 --round 22 --no-show
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from f1analysis.season import (
    get_driver_standings,
    get_season_data,
    max_points_remaining,
    who_can_win,
)
from f1analysis.season_plots import (
    plot_points_heatmap,
    plot_season_summary,
    plot_title_chances,
)

OUTPUT_DIR = Path("outputs")


def parse_args():
    parser = argparse.ArgumentParser(description="Análisis de una temporada de F1")
    parser.add_argument("--season", type=int, required=True, help="Año, p. ej. 2025")
    parser.add_argument(
        "--round", type=int, required=True, help="Ronda hasta la que se analiza"
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Guardar las gráficas sin abrirlas (ni el HTML en el navegador)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    season, round_ = args.season, args.round
    suffix = f"{season}_r{round_}"
    OUTPUT_DIR.mkdir(exist_ok=True)
    saved = []

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
    path = OUTPUT_DIR / f"title_chances_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    # --- Puntos y posiciones por piloto y carrera ---
    print("\nDescargando los resultados de cada carrera (tarda la primera vez)...")
    points, positions, labels = get_season_data(
        season, up_to_round=round_, verbose=True
    )

    # Comprobación: los totales de la matriz deben coincidir con la clasificación
    standings_points = table.set_index("driverCode")["points"]
    diff = (points.sum(axis=1) - standings_points).dropna()
    mismatches = diff[diff.abs() > 0.01]
    if mismatches.empty:
        print("Comprobación OK: los totales coinciden con la clasificación oficial.")
    else:
        print("Aviso: estos totales no coinciden con la clasificación oficial:")
        print(mismatches)

    # Mapa de calor estático (PNG)
    fig = plot_points_heatmap(
        points, labels, f"Puntos por piloto y carrera - Temporada {season}"
    )
    path = OUTPUT_DIR / f"points_heatmap_{suffix}.png"
    fig.savefig(path, dpi=150)
    saved.append(path)

    # Resumen interactivo (HTML)
    summary = plot_season_summary(
        points, positions, labels, f"Resumen de la temporada {season}"
    )
    path = OUTPUT_DIR / f"season_summary_{suffix}.html"
    summary.write_html(path, include_plotlyjs="cdn")
    saved.append(path)

    print()
    for path in saved:
        print(f"Guardado: {path}")

    if args.no_show:
        plt.close("all")
    else:
        plt.show()
        summary.show()


if __name__ == "__main__":
    main()