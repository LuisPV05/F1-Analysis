"""Construye y guarda el conjunto de datos para predecir la posición final.

Ejemplo:
    py src/main_dataset.py
    py src/main_dataset.py --start 2020 --end 2025
"""

import argparse
from pathlib import Path

from f1analysis.dataset import (
    FEATURE_COLUMNS,
    baseline_mae,
    baseline_mae_by_season,
    build_dataset,
)

DATA_DIR = Path("data")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Conjunto de datos para predecir la posición final"
    )
    parser.add_argument("--start", type=int, default=2018, help="Primera temporada")
    parser.add_argument("--end", type=int, default=2025, help="Última temporada")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.start > args.end:
        raise SystemExit("--start no puede ser posterior a --end.")
    DATA_DIR.mkdir(exist_ok=True)

    print("Descargando los resultados de cada carrera (tarda la primera vez)...")
    dataset = build_dataset(args.start, args.end, verbose=True)

    races = dataset.groupby(["season", "round"]).ngroups
    print(
        f"\nFilas: {len(dataset)} ({races} carreras, "
        f"temporadas {args.start}-{args.end})"
    )

    print("\nValores que faltan por variable (los primeros fines de semana no tienen historial):")
    print(dataset[FEATURE_COLUMNS].isna().sum().to_string())

    print(
        f"\nReferencia 'termina donde sale': error medio de "
        f"{baseline_mae(dataset):.3f} posiciones"
    )
    print("\nPor temporada:")
    print(baseline_mae_by_season(dataset).round(3).to_string())

    path = DATA_DIR / f"race_dataset_{args.start}_{args.end}.csv"
    dataset.to_csv(path, index=False)
    print(f"\nGuardado: {path}")


if __name__ == "__main__":
    main()