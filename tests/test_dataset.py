"""Tests del conjunto de datos de predicción. No usan la red."""

import pandas as pd
import pytest

from f1analysis import dataset
from f1analysis.dataset import (
    FEATURE_COLUMNS,
    TARGET,
    add_features,
    baseline_mae,
    baseline_mae_by_season,
    build_dataset,
    get_race_table,
    is_finish,
    split_by_season,
)

COLUMNS = ["season", "round", "driverId", "constructorId", "grid", "position", "status"]


def make_results():
    """Tres carreras con dos equipos de dos pilotos. El piloto d sale del pit lane."""
    rows = [
        (2024, 1, "a", "x", 1, 1, "Finished"),
        (2024, 1, "b", "x", 2, 3, "Finished"),
        (2024, 1, "c", "y", 3, 2, "Finished"),
        (2024, 1, "d", "y", 0, 4, "Engine"),
        (2024, 2, "a", "x", 2, 3, "+1 Lap"),
        (2024, 2, "b", "x", 1, 5, "Collision"),
        (2024, 2, "c", "y", 3, 1, "Finished"),
        (2024, 2, "d", "y", 4, 2, "Finished"),
        (2024, 3, "a", "x", 1, 5, "Accident"),
        (2024, 3, "b", "x", 2, 2, "Finished"),
        (2024, 3, "c", "y", 3, 1, "Finished"),
        (2024, 3, "d", "y", 4, 4, "Finished"),
    ]
    return pd.DataFrame(rows, columns=COLUMNS)


def feature(result, round_, driver, column):
    return result.set_index(["round", "driverId"]).loc[(round_, driver), column]


@pytest.mark.parametrize(
    "status, expected",
    [
        ("Finished", True),
        ("+1 Lap", True),
        ("+2 Laps", True),
        ("Lapped", True),
        ("Engine", False),
        ("Collision", False),
        ("Accident", False),
        (None, False),
    ],
)
def test_is_finish(status, expected):
    assert is_finish(status) is expected


def test_add_features_returns_the_expected_columns():
    result = add_features(make_results())
    assert result.columns.tolist() == (
        ["season", "round", "driverId", "constructorId", "status"]
        + FEATURE_COLUMNS
        + [TARGET]
    )
    assert len(result) == 12


def test_add_features_does_not_modify_the_input():
    results = make_results()
    add_features(results)
    assert results.columns.tolist() == COLUMNS
    assert results.loc[3, "grid"] == 0


def test_field_size_counts_the_drivers_in_each_race():
    result = add_features(make_results())
    assert set(result["field_size"]) == {4}


def test_pit_lane_start_counts_as_starting_last():
    result = add_features(make_results())
    assert feature(result, 1, "d", "grid") == 4


def test_driver_form_averages_only_previous_races():
    result = add_features(make_results())
    assert pd.isna(feature(result, 1, "a", "driver_form"))
    assert feature(result, 2, "a", "driver_form") == 1.0
    assert feature(result, 3, "a", "driver_form") == 2.0  # media de 1 y 3


def test_driver_dnf_rate_counts_retirements_but_not_lapped_finishers():
    result = add_features(make_results())
    # a: acabó y terminó doblado, sin abandonos
    assert feature(result, 3, "a", "driver_dnf_rate") == 0.0
    # b: abandonó en la ronda 2 -> media de (acabó, abandonó)
    assert feature(result, 3, "b", "driver_dnf_rate") == 0.5
    # d: abandonó en la ronda 1
    assert feature(result, 2, "d", "driver_dnf_rate") == 1.0
    assert feature(result, 3, "d", "driver_dnf_rate") == 0.5


def test_team_form_averages_both_cars_over_previous_races():
    result = add_features(make_results())
    assert pd.isna(feature(result, 1, "a", "team_form"))
    # Equipo x: ronda 1 -> (1 + 3) / 2 = 2; ronda 2 -> (3 + 5) / 2 = 4
    assert feature(result, 2, "a", "team_form") == 2.0
    assert feature(result, 2, "b", "team_form") == 2.0
    assert feature(result, 3, "a", "team_form") == 3.0


def test_features_of_a_race_never_depend_on_later_races():
    original = add_features(make_results())

    changed = make_results()
    last_round = changed["round"] == 3
    changed.loc[last_round, "position"] = [4, 3, 2, 1]
    changed.loc[last_round, "status"] = "Engine"
    modified = add_features(changed)

    earlier = original["round"] < 3
    pd.testing.assert_frame_equal(
        original.loc[earlier, FEATURE_COLUMNS].reset_index(drop=True),
        modified.loc[modified["round"] < 3, FEATURE_COLUMNS].reset_index(drop=True),
    )


def test_form_carries_over_between_seasons():
    previous = make_results()
    previous["season"] = 2023
    both = pd.concat([previous, make_results()], ignore_index=True)

    result = add_features(both)
    first_of_2024 = result[(result["season"] == 2024) & (result["round"] == 1)]
    form_a = first_of_2024.set_index("driverId").loc["a", "driver_form"]
    assert form_a == pytest.approx((1 + 3 + 5) / 3)  # sus tres carreras de 2023


def fake_season_results(rounds_available):
    """Sustituye a get_season_race_results con las rondas indicadas (0 = sin datos)."""

    def get_season_race_results(season):
        if rounds_available == 0:
            raise ValueError("No hay datos")
        frames = [
            pd.DataFrame(
                {
                    "round": [round_, round_],
                    "driverId": ["a", "b"],
                    "constructorId": ["x", "x"],
                    "grid": ["1", "0"],
                    "position": ["2", "1"],
                    "status": ["Finished", "Engine"],
                    "extra_column": [0, 0],
                }
            )
            for round_ in range(1, rounds_available + 1)
        ]
        return pd.concat(frames, ignore_index=True)

    return get_season_race_results


def test_get_race_table_reads_every_round_of_the_season(monkeypatch):
    monkeypatch.setattr(dataset, "get_season_race_results", fake_season_results(2))

    table = get_race_table(2024)

    assert table["round"].tolist() == [1, 1, 2, 2]
    assert set(table["season"]) == {2024}
    assert table["grid"].tolist() == [1, 0, 1, 0]  # convertido a número
    assert "extra_column" not in table.columns


def test_get_race_table_without_results_fails(monkeypatch):
    monkeypatch.setattr(dataset, "get_season_race_results", fake_season_results(0))
    with pytest.raises(ValueError):
        get_race_table(2024)


def test_build_dataset_joins_seasons_and_adds_features(monkeypatch):
    monkeypatch.setattr(dataset, "get_season_race_results", fake_season_results(2))

    result = build_dataset(2023, 2024)

    assert sorted(set(result["season"])) == [2023, 2024]
    assert set(FEATURE_COLUMNS) <= set(result.columns)
    assert len(result) == 8


def test_build_dataset_rejects_an_inverted_range():
    with pytest.raises(ValueError):
        build_dataset(2025, 2020)


@pytest.fixture
def three_seasons():
    frames = []
    for season in (2022, 2023, 2024):
        frame = make_results()
        frame["season"] = season
        frames.append(frame)
    return add_features(pd.concat(frames, ignore_index=True))


def test_split_by_season_trains_on_the_past_and_tests_on_one_season(three_seasons):
    train, test = split_by_season(three_seasons, 2024)
    assert sorted(set(train["season"])) == [2022, 2023]
    assert set(test["season"]) == {2024}


def test_split_by_season_fails_when_the_test_season_is_missing(three_seasons):
    with pytest.raises(ValueError):
        split_by_season(three_seasons, 2030)


def test_split_by_season_fails_without_earlier_seasons(three_seasons):
    with pytest.raises(ValueError):
        split_by_season(three_seasons, 2022)


def test_baseline_mae_is_the_mean_gap_between_grid_and_finish():
    data = pd.DataFrame(
        {
            "season": [2023, 2023, 2024],
            "grid": [1, 5, 3],
            "position": [1, 3, 4],
        }
    )
    assert baseline_mae(data) == pytest.approx(1.0)  # errores 0, 2 y 1
    by_season = baseline_mae_by_season(data)
    assert by_season.loc[2023] == pytest.approx(1.0)
    assert by_season.loc[2024] == pytest.approx(1.0)