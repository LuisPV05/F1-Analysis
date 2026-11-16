"""Gráficas a nivel de temporada."""

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from plotly.subplots import make_subplots

YES_COLOR = "#2ca02c"
NO_COLOR = "#999999"


def plot_title_chances(table, title):
    """Barras con los puntos actuales y el máximo teórico de cada piloto.

    'table' debe venir de season.who_can_win(). Barra oscura: puntos
    actuales. Barra clara: máximo teórico. La línea marca los puntos del líder.
    """
    table = table.sort_values("position")
    colors = [YES_COLOR if win else NO_COLOR for win in table["can_win"]]
    leader_points = table["points"].max()

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(table["driverCode"], table["max_points"], color=colors, alpha=0.3)
    ax.barh(table["driverCode"], table["points"], color=colors)
    ax.axvline(leader_points, color="black", linestyle="--", linewidth=1)

    ax.invert_yaxis()  # el líder arriba
    ax.set_xlabel("Puntos")
    ax.set_title(
        f"{title}\nBarra oscura: puntos actuales · barra clara: máximo teórico"
    )
    ax.grid(axis="x", alpha=0.3)

    handles = [
        Patch(facecolor=YES_COLOR, label="Puede ganar"),
        Patch(facecolor=NO_COLOR, label="Sin opciones"),
        Line2D([0], [0], color="black", linestyle="--", label="Puntos del líder"),
    ]
    ax.legend(handles=handles, loc="lower right")
    fig.tight_layout()
    return fig


def plot_points_heatmap(matrix, labels, title):
    """Mapa de calor de puntos por piloto y carrera, con el total a la derecha.

    'matrix' y 'labels' vienen de season.get_season_data(). Los pilotos se
    ordenan por puntos totales, de más a menos.
    """
    totals = matrix.sum(axis=1).sort_values(ascending=False)
    matrix = matrix.loc[totals.index]

    fig, (ax_main, ax_total) = plt.subplots(
        1,
        2,
        figsize=(14, 9),
        gridspec_kw={"width_ratios": [len(matrix.columns), 2]},
    )

    sns.heatmap(
        matrix,
        ax=ax_main,
        cmap="Blues",
        vmin=0,
        annot=True,
        fmt="g",
        annot_kws={"size": 8},
        cbar=False,
        linewidths=0.5,
        linecolor="white",
        xticklabels=labels,
        yticklabels=matrix.index,
    )
    ax_main.xaxis.tick_top()
    ax_main.tick_params(axis="x", labelrotation=90)
    ax_main.set_xlabel("")
    ax_main.set_ylabel("")

    sns.heatmap(
        totals.to_frame("Total"),
        ax=ax_total,
        cmap="Blues",
        vmin=0,
        annot=True,
        fmt="g",
        annot_kws={"size": 8},
        cbar=False,
        linewidths=0.5,
        linecolor="white",
        xticklabels=["Total"],
        yticklabels=False,
    )
    ax_total.xaxis.tick_top()
    ax_total.set_xlabel("")
    ax_total.set_ylabel("")

    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_season_summary(points, positions, labels, title):
    """Resumen interactivo de la temporada (figura de plotly).

    Mapa de calor de puntos por piloto y carrera, más una columna con el
    total. Al pasar el ratón por una celda se ve también la posición de
    llegada. 'points', 'positions' y 'labels' vienen de
    season.get_season_data().
    """
    # El de menos puntos primero: plotly dibuja el primer elemento abajo
    totals = points.sum(axis=1).sort_values(ascending=True)
    points = points.loc[totals.index]
    positions = positions.reindex(index=points.index, columns=points.columns)

    hover_positions = positions.map(
        lambda value: "N/A" if pd.isna(value) else str(int(value))
    )
    # Con el número de ronda delante, para que no se mezclen carreras con
    # el mismo nombre en una temporada
    race_labels = [f"{rnd}. {label}" for rnd, label in zip(points.columns, labels)]
    total_values = totals.to_numpy()

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.85, 0.15],
        subplot_titles=(title, "Puntos totales"),
    )
    fig.update_layout(width=1000, height=800)

    fig.add_trace(
        go.Heatmap(
            x=race_labels,
            y=points.index,
            z=points.values,
            text=points.values,
            texttemplate="%{text}",
            textfont={"size": 12},
            customdata=hover_positions.values,
            hovertemplate=(
                "Piloto: %{y}<br>"
                "Carrera: %{x}<br>"
                "Puntos: %{z}<br>"
                "Posición: %{customdata}<extra></extra>"
            ),
            colorscale="YlGnBu",
            showscale=False,
            zmin=0,
            zmax=points.to_numpy().max(),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Heatmap(
            x=["Total"] * len(total_values),
            y=points.index,
            z=total_values,
            text=total_values,
            texttemplate="%{text}",
            textfont={"size": 12},
            hovertemplate="Piloto: %{y}<br>Puntos: %{z}<extra></extra>",
            colorscale="YlGnBu",
            showscale=False,
            zmin=0,
            zmax=total_values.max(),
        ),
        row=1,
        col=2,
    )
    fig.update_xaxes(tickangle=-60, row=1, col=1)
    return fig