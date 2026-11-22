"""Duelos entre compañeros de equipo de una temporada desde la terminal.

Ejemplo:
    py src/main_teammates.py --season 2023
    py src/main_teammates.py --season 2025 --round 12 --no-show
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from f1analysis.teammates import get_weekend_results, teammate_duels
from f1analysis.teammates_plots import plot_teammate_duels

OUTPUT_DIR = Path("outputs")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Duelos entre compañeros de equipo de una temporada"
    )
    parser.add_argument("--season", type=int, required=True, help="Año, p. ej. 2023")
    parser.add_argument(
        "--round",
        type=int,
        default=None,
        help="Ronda hasta la que se analiza (por defecto, toda la temporada)",
    )
    parser.add_argument(
        "--no-show", action="store_true", help="Guardar la gráfica sin abrirla"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Descargando los resultados de cada fin de semana (tarda la primera vez)...")
    weekends = get_weekend_results(args.season, up_to_round=args.round, verbose=True)
    last_round = int(weekends["round"].max())

    summary = teammate_duels(weekends)
    if summary.empty:
        raise SystemExit("No hay duelos entre compañeros en esa temporada.")

    print()
    print(summary.drop(columns=["constructorId"]).to_string(index=False))

    fig = plot_teammate_duels(
        summary,
        f"Duelos entre compañeros - Temporada {args.season} (hasta la ronda {last_round})",
    )
    path = OUTPUT_DIR / f"teammates_{args.season}_r{last_round}.png"
    fig.savefig(path, dpi=150)
    print(f"\nGuardado: {path}")

    if args.no_show:
        plt.close("all")
    else:
        plt.show()


if __name__ == "__main__":
    main()