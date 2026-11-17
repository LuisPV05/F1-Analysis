"""Comparativa de campeones entre temporadas desde la terminal.

Ejemplo:
    py src/main_history.py --start 2010 --end 2025
    py src/main_history.py --start 2000 --end 2025 --no-show
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from f1analysis.history import get_champions
from f1analysis.history_plots import plot_champions

OUTPUT_DIR = Path("outputs")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Comparativa de campeones entre temporadas"
    )
    parser.add_argument("--start", type=int, required=True, help="Primera temporada")
    parser.add_argument("--end", type=int, required=True, help="Última temporada")
    parser.add_argument(
        "--no-show", action="store_true", help="Guardar la gráfica sin abrirla"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.start > args.end:
        raise SystemExit("--start no puede ser posterior a --end.")
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Descargando las clasificaciones finales...")
    champions = get_champions(args.start, args.end, verbose=True)

    columns = [
        "season",
        "champion",
        "champion_team",
        "champion_points",
        "champion_wins",
        "runner_up",
        "margin",
    ]
    print()
    print(champions[columns].to_string(index=False))

    fig = plot_champions(
        champions, f"Campeones del mundo de pilotos {args.start}-{args.end}"
    )
    path = OUTPUT_DIR / f"champions_{args.start}_{args.end}.png"
    fig.savefig(path, dpi=150)
    print(f"\nGuardado: {path}")

    if args.no_show:
        plt.close("all")
    else:
        plt.show()


if __name__ == "__main__":
    main()