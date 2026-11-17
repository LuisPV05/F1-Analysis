"""Comparativa de pilotos entre temporadas desde la terminal.

Ejemplo:
    py src/main_drivers.py --start 2010 --end 2025
    py src/main_drivers.py --start 2005 --end 2018 --drivers alonso vettel
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from f1analysis.history import get_driver_comparison
from f1analysis.history_plots import plot_driver_comparison

OUTPUT_DIR = Path("outputs")
DEFAULT_DRIVERS = ["hamilton", "max_verstappen"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Comparativa de pilotos entre temporadas"
    )
    parser.add_argument("--start", type=int, required=True, help="Primera temporada")
    parser.add_argument("--end", type=int, required=True, help="Última temporada")
    parser.add_argument(
        "--drivers",
        nargs="+",
        default=DEFAULT_DRIVERS,
        help="Pilotos a comparar (driverId, código o apellido), mínimo 2. "
        "Por defecto: hamilton max_verstappen",
    )
    parser.add_argument(
        "--no-show", action="store_true", help="Guardar la gráfica sin abrirla"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.start > args.end:
        raise SystemExit("--start no puede ser posterior a --end.")
    if len(args.drivers) < 2:
        raise SystemExit("Indica al menos dos pilotos en --drivers.")
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Descargando las clasificaciones finales...")
    comparison, order = get_driver_comparison(
        args.start, args.end, args.drivers, verbose=True
    )

    summary = (
        comparison.groupby("driver")
        .agg(
            temporadas=("season", "count"),
            titulos=("position", lambda s: int((s == 1).sum())),
            victorias=("wins", "sum"),
            puntos=("points", "sum"),
        )
        .reindex(order)
    )
    print("\nResumen:")
    print(summary.to_string())

    points = comparison.pivot(index="season", columns="driver", values="points")
    print("\nPuntos por temporada:")
    print(points[order].to_string())

    fig = plot_driver_comparison(
        comparison,
        order,
        f"{' vs '.join(order)}, temporadas {args.start}-{args.end}",
    )
    names = "_vs_".join(args.drivers).lower().replace(" ", "")
    path = OUTPUT_DIR / f"drivers_{names}_{args.start}_{args.end}.png"
    fig.savefig(path, dpi=150)
    print(f"\nGuardado: {path}")

    if args.no_show:
        plt.close("all")
    else:
        plt.show()


if __name__ == "__main__":
    main()