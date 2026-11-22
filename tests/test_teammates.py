"""Tests de los duelos entre compañeros de equipo."""

import pandas as pd
import pytest

from f1analysis.teammates import SUMMARY_COLUMNS, teammate_duels

COLUMNS = [
    "round",
    "driverId",
    "driverCode",
    "constructorId",
    "constructorName",
    "quali_pos",
    "race_pos",
    "points",
]
NAN = float("nan")


def make_weekends(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


@pytest.fixture
def weekends():
    return make_weekends(
        [
            # Ronda 1: AAA gana la clasificación y BBB la carrera
            (1, "x_a", "AAA", "x", "Team X", 1, 2, 18),
            (1, "x_b", "BBB", "x", "Team X", 2, 1, 25),
            (1, "y_c", "CCC", "y", "Team Y", 3, 3, 15),
            # Ronda 2: AAA gana las dos
            (2, "x_a", "AAA", "x", "Team X", 3, 1, 25),
            (2, "x_b", "BBB", "x", "Team X", 4, 4, 12),
            (2, "y_c", "CCC", "y", "Team Y", 1, 2, 18),
            # Ronda 3: AAA sin dato de clasificación
            (3, "x_a", "AAA", "x", "Team X", NAN, 5, 10),
            (3, "x_b", "BBB", "x", "Team X", 1, 6, 8),
            (3, "y_c", "CCC", "y", "Team Y", 2, 1, 25),
        ]
    )


def test_only_teams_with_two_drivers_have_duels(weekends):
    result = teammate_duels(weekends)
    assert result["constructorId"].tolist() == ["x"]


def test_counts_wins_in_qualifying_and_race_ignoring_missing_data(weekends):
    row = teammate_duels(weekends).iloc[0]
    assert (row["driver_a"], row["driver_b"]) == ("AAA", "BBB")
    assert row["rounds"] == 3
    assert (row["quali_wins_a"], row["quali_wins_b"]) == (2, 0)
    assert (row["race_wins_a"], row["race_wins_b"]) == (2, 1)
    assert (row["points_a"], row["points_b"]) == (53, 45)


def test_driver_with_more_points_goes_first():
    weekends = make_weekends(
        [
            (1, "x_a", "AAA", "x", "Team X", 1, 2, 18),
            (1, "x_b", "BBB", "x", "Team X", 2, 1, 25),
        ]
    )
    row = teammate_duels(weekends).iloc[0]
    assert (row["driver_a"], row["driver_b"]) == ("BBB", "AAA")
    assert (row["quali_wins_a"], row["quali_wins_b"]) == (0, 1)
    assert (row["race_wins_a"], row["race_wins_b"]) == (1, 0)
    assert (row["points_a"], row["points_b"]) == (25, 18)


def test_three_drivers_in_the_same_team_and_round_make_three_duels():
    weekends = make_weekends(
        [
            (1, "x_a", "AAA", "x", "Team X", 1, 1, 25),
            (1, "x_b", "BBB", "x", "Team X", 2, 2, 18),
            (1, "x_c", "CCC", "x", "Team X", 3, 3, 15),
        ]
    )
    assert len(teammate_duels(weekends)) == 3


def test_teams_are_sorted_by_combined_points():
    weekends = make_weekends(
        [
            (1, "x_a", "AAA", "x", "Team X", 1, 1, 10),
            (1, "x_b", "BBB", "x", "Team X", 2, 2, 5),
            (1, "y_a", "DDD", "y", "Team Y", 3, 3, 25),
            (1, "y_b", "EEE", "y", "Team Y", 4, 4, 18),
        ]
    )
    assert teammate_duels(weekends)["constructorId"].tolist() == ["y", "x"]


def test_no_duels_returns_an_empty_table_with_the_expected_columns():
    weekends = make_weekends([(1, "x_a", "AAA", "x", "Team X", 1, 1, 25)])
    result = teammate_duels(weekends)
    assert result.empty
    assert result.columns.tolist() == SUMMARY_COLUMNS