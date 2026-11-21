"""Caché en disco de los datos de Jolpica ya procesados.

Las temporadas terminadas no cambian, así que se guardan para siempre. Los
datos del año en curso caducan a las 12 horas, porque pueden aparecer
carreras nuevas.

Para desactivarla, define la variable de entorno F1ANALYSIS_NO_CACHE=1.
Para vaciarla, borra la carpeta .cache/.

Los archivos se guardan con pickle: es una caché local, nunca cargues una
procedente de una fuente en la que no confíes.
"""

import os
import time
from datetime import date
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(".cache") / "f1analysis"
CURRENT_YEAR_TTL = 12 * 3600  # segundos
DISABLE_VARIABLE = "F1ANALYSIS_NO_CACHE"


def _cache_path(name, season, params):
    """Ruta del archivo de caché, p. ej. race_results_2021_round_7.pkl."""
    parts = [name, str(season)]
    parts += [f"{key}_{value}" for key, value in sorted(params.items())]
    return CACHE_DIR / ("_".join(parts) + ".pkl")


def _is_fresh(path, season):
    """True si el archivo sigue siendo válido."""
    if season < date.today().year:
        return True  # temporada terminada: no cambia
    age = time.time() - path.stat().st_mtime
    return age < CURRENT_YEAR_TTL


def _disabled():
    return os.environ.get(DISABLE_VARIABLE, "") not in ("", "0")


def cached_dataframe(name, loader, season, **params):
    """Devuelve el DataFrame de loader(), usando la caché en disco.

    'name' y 'params' identifican el dato (p. ej. "race_results" con
    round_=7). 'season' decide la caducidad. Si loader() devuelve None, no
    se guarda nada.
    """
    if _disabled():
        return loader()

    path = _cache_path(name, season, params)
    if path.exists() and _is_fresh(path, season):
        try:
            return pd.read_pickle(path)
        except Exception:
            pass  # archivo corrupto o de otra versión: se descarga de nuevo

    result = loader()
    if result is not None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        result.to_pickle(path)
    return result