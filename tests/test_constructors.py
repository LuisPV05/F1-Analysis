"""Tests del campeonato de constructores."""

import pandas as pd
import pytest

from f1analysis import constructors
from f1analysis.constructors import (
    _cumulative_matrix,
    max_points_remaining_constructors,
    round_points,
    who_can_win_constructors,
)


def make_standings(rows):
    return pd.DataFrame(rows, columns=["constructorId", "constructorName", "points"])


def test_who_can_win_adds_theoretical_maximum_and_flag():
    standings = pd.DataFrame(
        {
            "position": [1, 2, 3],
            "constructorName": ["A", "B", "C"],
            "points": [100.0, 70.0, 50.0],
        }
    )
    result = who_can_win_constructors(standings, max_points=30)
    assert result["max_points"].tolist() == [130.0, 100.0, 80.0]
    # B empata con el líder (100) y cuenta como "puede ganar"
    assert result["can_win"].tolist() == [True, True, False]


def test_who_can_win_returns_sorted_by_position_without_touching_the_input():
    standings = pd.DataFrame(
        {"position": [2, 1], "constructorName": ["B", "A"], "points": [50.0, 80.0]}
    )
    result = who_can_win_constructors(standings, max_points=10)
    assert result["position"].tolist() == [1, 2]
    assert "max_points" not in standings.columns


def test_max_points_remaining_counts_43_per_race_and_15_per_sprint(monkeypatch):
    calendar = pd.DataFrame(
        {
            "RoundNumber": [1, 2, 3, 4],
            "EventFormat": [
                "conventional",
                "sprint_qualifying",
                "conventional",
                "sprint",
            ],
        }
    )
    monkeypatch.setattr(constructors, "_get_schedule", lambda season: calendar)

    # Quedan las rondas 2 a 4: 3 carreras (129) y 2 sprints (30)
    assert max_points_remaining_constructors(2025, 1) == 3 * 43 + 2 * 15
    assert max_points_remaining_constructors(2025, 4) == 0


@pytest.fixture
def progress():
    frames = {
        1: make_standings([("a", "Team A", 25), ("b", "Team B", 18)]),
        2: make_standings(
            [("a", "Team A", 50), ("b", "Team B", 30), ("c", "Team C", 4)]
        ),
        # Team B no aparece en la ronda 3: conserva sus puntos
        3: make_standings([("a", "Team A", 60), ("c", "Team C", 10)]),
    }
    return _cumulative_matrix(frames)


def test_cumulative_matrix_has_one_column_per_round(progress):
    cumulative, _ = progress
    assert cumulative.columns.tolist() == [1, 2, 3]


def test_cumulative_matrix_fills_late_teams_with_zero_and_keeps_missing_ones(progress):
    cumulative, _ = progress
    assert cumulative.loc["a"].tolist() == [25, 50, 60]
    assert cumulative.loc["b"].tolist() == [18, 30, 30]
    assert cumulative.loc["c"].tolist() == [0, 4, 10]


def test_cumulative_matrix_keeps_team_names(progress):
    _, names = progress
    assert names["a"] == "Team A"
    assert names["c"] == "Team C"


def test_round_points_is_the_difference_between_rounds(progress):
    cumulative, _ = progress
    per_round = round_points(cumulative)
    assert per_round.loc["a"].tolist() == [25, 25, 10]
    assert per_round.loc["b"].tolist() == [18, 12, 0]
    assert per_round.loc["c"].tolist() == [0, 4, 6]


def test_round_points_does_not_modify_the_input(progress):
    cumulative, _ = progress
    round_points(cumulative)
    assert cumulative.loc["a"].tolist() == [25, 50, 60]


def test_round_points_can_be_negative_after_a_points_deduction():
    cumulative = pd.DataFrame({1: [25.0], 2: [10.0]}, index=["a"])
    assert round_points(cumulative).loc["a"].tolist() == [25, -15]