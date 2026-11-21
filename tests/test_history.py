"""Tests de la búsqueda de pilotos en una clasificación."""

import pandas as pd
import pytest

from f1analysis.history import _find_driver, _first_item


@pytest.fixture
def standings():
    return pd.DataFrame(
        {
            "position": [1, 2, 20],
            "driverId": ["max_verstappen", "hamilton", "jos_verstappen"],
            "driverCode": ["VER", "HAM", "JOS"],
            "familyName": ["Verstappen", "Hamilton", "Verstappen"],
        }
    )


def test_first_item_of_list_tuple_and_plain_value():
    assert _first_item(["red_bull", "alpha_tauri"]) == "red_bull"
    assert _first_item(("a", "b")) == "a"
    assert _first_item([]) is None
    assert _first_item("mercedes") == "mercedes"


def test_find_driver_by_id(standings):
    assert _find_driver(standings, "hamilton")["driverCode"] == "HAM"


def test_find_driver_by_code_ignoring_case(standings):
    assert _find_driver(standings, "ham")["driverId"] == "hamilton"


def test_find_driver_by_surname_returns_the_best_classified(standings):
    assert _find_driver(standings, "verstappen")["driverId"] == "max_verstappen"


def test_find_driver_by_id_disambiguates_same_surname(standings):
    assert _find_driver(standings, "jos_verstappen")["driverCode"] == "JOS"


def test_find_driver_not_found_returns_none(standings):
    assert _find_driver(standings, "alonso") is None


def test_find_driver_works_without_driver_code_column(standings):
    without_code = standings.drop(columns=["driverCode"])
    assert _find_driver(without_code, "hamilton")["position"] == 2
    assert _find_driver(without_code, "ham") is None