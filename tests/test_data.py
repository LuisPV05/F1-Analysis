"""Tests de las funciones de datos que no necesitan red."""

import math

import pandas as pd
import pytest
import requests

from f1analysis import cache, data, season
from f1analysis.data import add_stints, to_seconds


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    """Sin pausa entre peticiones: los tests no deben esperar."""
    monkeypatch.setattr(season, "MIN_INTERVAL", 0.0)


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


class FakeSeasonResponse:
    """Respuesta con varias carreras: una tabla por carrera y su descripción."""

    def __init__(self, tables, rounds):
        self.content = tables
        self.description = pd.DataFrame({"round": rounds})


class FakeErgast:
    def __init__(self, pages):
        self.pages = pages
        self.offsets = []

    def get_race_results(self, season, limit, offset):
        self.offsets.append(offset)
        return self.pages[offset // limit]


def test_download_season_race_results_joins_pages_and_labels_each_round(monkeypatch):
    monkeypatch.setattr(data, "PAGE_SIZE", 3)
    pages = [
        # La ronda 2 queda partida entre las dos páginas
        FakeSeasonResponse(
            [pd.DataFrame({"driverId": ["a", "b"]}), pd.DataFrame({"driverId": ["a"]})],
            ["1", "2"],
        ),
        FakeSeasonResponse([pd.DataFrame({"driverId": ["b"]})], ["2"]),
    ]
    fake = FakeErgast(pages)
    monkeypatch.setattr(data, "Ergast", lambda: fake)

    result = data._download_season_race_results(2024)

    assert result["round"].tolist() == [1, 1, 2, 2]
    assert result["driverId"].tolist() == ["a", "b", "a", "b"]
    assert fake.offsets == [0, 3]


def test_download_season_race_results_without_data_returns_none(monkeypatch):
    fake = FakeErgast([FakeSeasonResponse([], [])])
    monkeypatch.setattr(data, "Ergast", lambda: fake)
    assert data._download_season_race_results(2024) is None


def test_get_season_race_results_without_data_fails(monkeypatch):
    monkeypatch.setenv(cache.DISABLE_VARIABLE, "1")
    monkeypatch.setattr(data, "_download_season_race_results", lambda season: None)
    with pytest.raises(ValueError):
        data.get_season_race_results(2024)