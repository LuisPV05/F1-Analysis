# F1-Analysis

Análisis de datos de Fórmula 1 con Python: resultados de carrera, clasificación, tiempos por vuelta y ritmo de carrera, usando [FastF1](https://docs.fastf1.dev/) y la API [Jolpica](https://github.com/jolpica/jolpica-f1) (compatible con Ergast).

Proyecto personal de aprendizaje en análisis de datos. Se construyó paso a paso a partir de la sección *Getting Started* de la documentación de FastF1 y después se reorganizó en un paquete reutilizable con una herramienta de línea de comandos.

## Gráficas

Ejemplo con el GP de Francia 2021 (`--season 2021 --round 7`).

**Diferencia con la pole en clasificación**

![Diferencia con la pole](outputs/qualifying_delta_2021_r7.png)

**Ritmo de carrera de los 4 primeros**

![Ritmo de carrera](outputs/race_pace_2021_r7.png)

## Qué hace

- Descarga resultados de clasificación y de carrera de cualquier temporada y ronda.
- Obtiene los tiempos de todas las vueltas de una carrera (con paginación de la API).
- Calcula la vuelta rápida y la mejor vuelta de cada piloto.
- Genera gráficas con matplotlib y las guarda en `outputs/`, con la temporada y la ronda en el nombre del archivo.

## Datos y limitaciones

Los datos se obtienen de Jolpica a través de `fastf1.ergast`, por lo que **no hace falta ninguna cuenta**.

Desde octubre de 2026, Formula 1 exige autenticación (suscripción F1TV Access o superior) en sus APIs de datos, y FastF1 v3.9.0 lo refleja al cargar sesiones con `session.load()`. Este proyecto evita esa vía a propósito.

La contrapartida es que **no hay telemetría** (velocidad, freno, acelerador), solo resultados y tiempos por vuelta.

## Instalación

Requiere Python 3.10 o superior.

```powershell
git clone https://github.com/LuisPV05/F1-Analysis.git
cd F1-Analysis
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## Uso

Desde la raíz del repo:

```powershell
py src/main.py --season 2021 --round 7
```

Opciones:

| Opción | Descripción |
|---|---|
| `--season` | Año de la temporada (obligatorio) |
| `--round` | Número de ronda (obligatorio) |
| `--top` | Número de pilotos en la gráfica de ritmo (por defecto 4) |
| `--no-show` | Guarda las gráficas sin abrirlas en pantalla |

Ejemplo sin abrir ventanas:

```powershell
py src/main.py --season 2023 --round 1 --top 5 --no-show
```

El programa muestra por consola la vuelta rápida y la mejor vuelta de cada piloto, y guarda dos gráficas en `outputs/`.

## Estructura

```
F1-Analysis/
├── README.md
├── requirements.txt
├── .gitignore
├── outputs/                      # gráficas generadas
└── src/
    ├── main.py                   # herramienta de línea de comandos
    ├── f1analysis/               # paquete con la lógica
    │   ├── data.py               # descarga y limpieza de datos (Jolpica)
    │   ├── analysis.py           # cálculos: delta con la pole, vuelta rápida...
    │   └── plots.py              # gráficas con matplotlib
    ├── 01_basics.py              # ejemplo: sesiones y eventos
    ├── 02_schedule.py            # ejemplo: calendario de temporada
    ├── 03_results_ergast.py      # ejemplo: resultados con Jolpica
    └── 04_laps_ergast.py         # ejemplo: exploración de tiempos por vuelta
```

Los scripts numerados son los primeros pasos de aprendizaje y se conservan como ejemplos. La funcionalidad actual está en `src/main.py` y en el paquete `src/f1analysis/`.

## Tecnologías

- Python
- FastF1 (módulo `fastf1.ergast`)
- pandas
- matplotlib

## Próximos pasos

- [x] Reorganizar el código en módulos reutilizables (datos, análisis, gráficas).
- [x] Elegir temporada y ronda desde la línea de comandos.
- [ ] Mover los scripts de ejemplo a una carpeta `examples/`.
- [ ] Análisis de estrategia: paradas en boxes por piloto.
- [ ] Comparativas entre temporadas.
- [ ] Telemetría, si se dispone de acceso a los datos.

## Autor

Luis Pérez Velasco · [@LuisPV05](https://github.com/LuisPV05)