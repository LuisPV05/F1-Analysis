"""Tests de los cálculos de temporada y de los reintentos."""

import pandas as pd
import pytest
from fastf1.exceptions import ErgastInvalidRequestError

from f1analysis import season
from f1analysis.season import max_points_remaining, who_can_win


def make_standings(with_code=True):
    df = pd.DataFrame(
        {
            "position": [1, 2, 3],
            "points": [100.0, 60.0, 50.0],
            "familyName": ["Piastri", "Norris", "Verstappen"],
        }
    )
    if with_code:
        df["driverCode"] = ["PIA", "NOR", "VER"]
    return df


def test_who_can_win_adds_theoretical_maximum_and_flag():
    result = who_can_win(make_standings(), max_points=40)
    assert result["max_points"].tolist() == [140.0, 100.0, 90.0]
    # El segundo empata con el líder (100) y cuenta como "puede ganar"
    assert result["can_win"].tolist() == [True, True, False]


def test_who_can_win_with_nothing_left_only_leader_and_ties_can_win():
    standings = make_standings()
    standings["points"] = [100.0, 100.0, 50.0]
    result = who_can_win(standings, max_points=0)
    assert result["can_win"].tolist() == [True, True, False]


def test_who_can_win_returns_sorted_by_position_without_touching_the_input():
    standings = make_standings().iloc[[2, 0, 1]]
    result = who_can_win(standings, max_points=40)
    assert result["position"].tolist() == [1, 2, 3]
    assert "max_points" not in standings.columns


def test_who_can_win_builds_driver_code_from_surname_when_missing():
    result = who_can_win(make_standings(with_code=False), max_points=40)
    assert result["driverCode"].tolist() == ["PIA", "NOR", "VER"]


@pytest.fixture
def schedule(monkeypatch):
    """Calendario inventado con los tres nombres que FastF1 usa para sprints."""
    calendar = pd.DataFrame(
        {
            "RoundNumber": [1, 2, 3, 4, 5, 6],
            "EventFormat": [
                "conventional",
                "sprint_qualifying",
                "conventional",
                "sprint_shootout",
                "sprint",
                "conventional",
            ],
        }
    )
    monkeypatch.setattr(season, "_get_schedule", lambda year: calendar)
    return calendar


def test_max_points_remaining_counts_races_and_every_sprint_format(schedule):
    # Quedan las rondas 3 a 6: 4 carreras (100) y 2 sprints (16)
    assert max_points_remaining(2025, 2) == 4 * 25 + 2 * 8


def test_max_points_remaining_is_zero_after_the_last_round(schedule):
    assert max_points_remaining(2025, 6) == 0


def test_with_retry_retries_when_jolpica_says_too_many_requests(monkeypatch):
    waits = []
    monkeypatch.setattr(season.time, "sleep", waits.append)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ErgastInvalidRequestError("Server response: 'Too Many Requests'")
        return "ok"

    assert season._with_retry(flaky) == "ok"
    assert len(calls) == 3
    assert waits == [season.RETRY_WAIT, season.RETRY_WAIT * 2]


def test_with_retry_does_not_retry_other_errors(monkeypatch):
    monkeypatch.setattr(season.time, "sleep", lambda seconds: None)
    calls = []

    def not_found():
        calls.append(1)
        raise ErgastInvalidRequestError("Server response: 'Not Found'")

    with pytest.raises(ErgastInvalidRequestError):
        season._with_retry(not_found)
    assert len(calls) == 1


def test_with_retry_gives_up_after_all_attempts(monkeypatch):
    monkeypatch.setattr(season.time, "sleep", lambda seconds: None)
    calls = []

    def always_busy():
        calls.append(1)
        raise ErgastInvalidRequestError("Too Many Requests")

    with pytest.raises(ErgastInvalidRequestError):
        season._with_retry(always_busy)
    assert len(calls) == season.RETRIES