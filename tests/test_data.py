"""Tests de las funciones de datos que no necesitan red."""

import math

import pandas as pd
import pytest
import requests

from f1analysis import data, season
from f1analysis.data import add_stints, to_seconds


@pytest.mark.parametrize(
    "value, expected",
    [
        (pd.Timedelta("0 days 00:01:29.990000"), 89.99),
        ("1:29.990", 89.99),
        ("0:59.500", 59.5),
        ("29.5", 29.5),
        (12.25, 12.25),
    ],
)
def test_to_seconds_valid_values(value, expected):
    assert to_seconds(value) == pytest.approx(expected)


@pytest.mark.parametrize("value", [None, float("nan"), pd.NaT, "", "   "])
def test_to_seconds_empty_values_are_nan(value):
    assert math.isnan(to_seconds(value))


def make_laps():
    rows = [("a", lap) for lap in range(1, 6)] + [("b", lap) for lap in range(1, 4)]
    return pd.DataFrame(rows, columns=["driverId", "lap"])


def make_pit_stops(rows):
    return pd.DataFrame(rows, columns=["driverId", "stop", "lap"])


def test_add_stints_increments_after_each_pit_stop():
    pit_stops = make_pit_stops([("a", 1, 2), ("a", 2, 4)])
    result = add_stints(make_laps(), pit_stops)

    stints_a = result.loc[result["driverId"] == "a", "stint"].tolist()
    stints_b = result.loc[result["driverId"] == "b", "stint"].tolist()
    # La vuelta de entrada a boxes (2 y 4) cuenta para el stint que termina
    assert stints_a == [1, 1, 2, 2, 3]
    assert stints_b == [1, 1, 1]


def test_add_stints_without_pit_stops_is_a_single_stint():
    pit_stops = make_pit_stops([])
    result = add_stints(make_laps(), pit_stops)
    assert set(result["stint"]) == {1}


def test_add_stints_ignores_pit_stops_of_other_drivers():
    pit_stops = make_pit_stops([("zzz", 1, 2)])
    result = add_stints(make_laps(), pit_stops)
    assert set(result["stint"]) == {1}


def test_add_stints_does_not_modify_the_input():
    laps = make_laps()
    add_stints(laps, make_pit_stops([("a", 1, 2)]))
    assert "stint" not in laps.columns


class FakeResponse:
    def __init__(self, content):
        self.content = content


def test_fetch_all_retries_a_slow_page_and_joins_all_pages(monkeypatch):
    monkeypatch.setattr(season.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(data, "PAGE_SIZE", 2)
    pages = [pd.DataFrame({"x": [1, 2]}), pd.DataFrame({"x": [3]})]
    offsets = []

    def method(season, round, limit, offset):
        offsets.append(offset)
        if len(offsets) == 1:
            raise requests.exceptions.ReadTimeout("respuesta lenta")
        return FakeResponse([pages[offset // 2]])

    result = data._fetch_all(method, 2023, 1)

    assert result["x"].tolist() == [1, 2, 3]
    # El primer intento falla y se repite la misma página antes de pasar a la siguiente
    assert offsets == [0, 0, 2]