"""Tests de los cálculos sobre clasificación y vueltas."""

import pandas as pd
import pytest

from f1analysis.analysis import (
    best_lap_per_driver,
    clean_race_laps,
    fastest_lap,
    qualifying_delta,
    quick_laps,
)


def make_laps(rows):
    return pd.DataFrame(rows, columns=["driverCode", "lap", "seconds"])


def test_qualifying_delta_orders_by_best_and_measures_gap_to_pole():
    qualifying = pd.DataFrame(
        {
            "driverCode": ["HAM", "VER", "MAZ"],
            "best": [90.5, 90.0, float("nan")],
        }
    )
    result = qualifying_delta(qualifying)
    assert result["driverCode"].tolist() == ["VER", "HAM"]
    assert result["delta"].tolist() == pytest.approx([0.0, 0.5])


def test_qualifying_delta_does_not_modify_the_input():
    qualifying = pd.DataFrame({"driverCode": ["A", "B"], "best": [91.0, 90.0]})
    qualifying_delta(qualifying)
    assert "delta" not in qualifying.columns


def test_fastest_lap_returns_the_quickest_row():
    laps = make_laps([("HAM", 1, 91.0), ("VER", 1, 90.5), ("VER", 2, 92.0)])
    best = fastest_lap(laps)
    assert best["driverCode"] == "VER"
    assert best["seconds"] == pytest.approx(90.5)
    assert best["lap"] == 1


def test_best_lap_per_driver_is_sorted_and_rounded():
    laps = make_laps(
        [
            ("VER", 1, 90.1234),
            ("VER", 2, 89.9994),
            ("HAM", 1, 90.5),
            ("HAM", 2, 90.2),
        ]
    )
    result = best_lap_per_driver(laps)
    assert result.index.tolist() == ["VER", "HAM"]
    assert result.tolist() == pytest.approx([89.999, 90.2])


def test_clean_race_laps_drops_very_slow_laps():
    laps = make_laps(
        [("VER", 1, 90.0), ("VER", 2, 91.0), ("VER", 3, 92.0), ("VER", 4, 150.0)]
    )
    result = clean_race_laps(laps)
    assert result["seconds"].tolist() == [90.0, 91.0, 92.0]


def test_quick_laps_keeps_laps_within_107_percent_of_the_best():
    laps = make_laps(
        [
            ("VER", 1, 90.0),
            ("VER", 2, 95.0),
            ("VER", 3, 96.2),
            ("VER", 4, 96.4),
            ("VER", 5, 130.0),
        ]
    )
    result = quick_laps(laps)
    assert result["seconds"].tolist() == [90.0, 95.0, 96.2]


def test_quick_laps_accepts_a_custom_threshold():
    laps = make_laps([("VER", 1, 90.0), ("VER", 2, 130.0)])
    assert len(quick_laps(laps, threshold=1.5)) == 2