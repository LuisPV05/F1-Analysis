"""Tests de los estilos por piloto."""

import pandas as pd
import pytest

from f1analysis.styling import (
    DEFAULT_STYLES,
    FALLBACK_COLOR,
    driver_order_in_team,
    get_driver_style,
    team_color,
)


@pytest.fixture
def race():
    """Resultados de carrera con las filas desordenadas a propósito."""
    df = pd.DataFrame(
        {
            "position": [1, 2, 3, 4],
            "driverCode": ["VER", "HAM", "PER", "BOT"],
            "constructorId": ["red_bull", "mercedes", "red_bull", "mercedes"],
        }
    )
    return df.iloc[[2, 0, 3, 1]]


def test_team_color_known_and_unknown_teams():
    assert team_color("red_bull") == "#3671C6"
    assert team_color("equipo_que_no_existe") == FALLBACK_COLOR


def test_driver_order_in_team_follows_finishing_position(race):
    assert driver_order_in_team(race) == {"VER": 0, "HAM": 0, "PER": 1, "BOT": 1}


def test_first_driver_of_a_team_gets_a_solid_line(race):
    style = get_driver_style("VER", race)
    assert style == {"color": "#3671C6", "linestyle": "solid"}


def test_second_driver_of_a_team_gets_a_dashed_line_in_the_team_color(race):
    style = get_driver_style("PER", race)
    assert style == {"color": "#3671C6", "linestyle": "dashed"}


def test_custom_styles_replace_auto_color_and_pick_by_position(race):
    styles = [
        {"color": "auto", "linestyle": "solid", "linewidth": 5},
        {"color": "red", "linestyle": "dotted"},
    ]
    assert get_driver_style("HAM", race, styles) == {
        "color": "#27F4D2",
        "linestyle": "solid",
        "linewidth": 5,
    }
    assert get_driver_style("BOT", race, styles) == {
        "color": "red",
        "linestyle": "dotted",
    }


def test_a_single_custom_style_is_used_for_every_driver(race):
    styles = [{"color": "auto"}]
    assert get_driver_style("PER", race, styles) == {"color": "#3671C6"}


def test_get_driver_style_does_not_modify_the_default_styles(race):
    get_driver_style("VER", race)
    assert DEFAULT_STYLES[0]["color"] == "auto"