"""Tests del calendario: reintentos y caché en disco."""

from datetime import date

import pandas as pd
import pytest

from f1analysis import cache, season

PAST_SEASON = date.today().year - 3


def make_schedule():
    return pd.DataFrame(
        {
            "RoundNumber": [1, 2],
            "EventName": ["Bahrain Grand Prix", "Saudi Arabian Grand Prix"],
            "EventFormat": ["conventional", "sprint_qualifying"],
            "Country": ["Bahrain", "Saudi Arabia"],  # columna que no se usa
        }
    )


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.delenv(cache.DISABLE_VARIABLE, raising=False)
    monkeypatch.setattr(season.time, "sleep", lambda seconds: None)


def test_schedule_is_retried_when_fastf1_cannot_load_it(monkeypatch):
    calls = []

    def flaky(year, **kwargs):
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("Failed to load any schedule data.")
        return make_schedule()

    monkeypatch.setattr(season.fastf1, "get_event_schedule", flaky)

    result = season._get_schedule(PAST_SEASON)

    assert len(calls) == 3
    assert result["RoundNumber"].tolist() == [1, 2]


def test_schedule_gives_up_after_all_attempts(monkeypatch):
    calls = []

    def always_fails(year, **kwargs):
        calls.append(1)
        raise ValueError("Failed to load any schedule data.")

    monkeypatch.setattr(season.fastf1, "get_event_schedule", always_fails)

    with pytest.raises(ValueError):
        season._get_schedule(PAST_SEASON)
    assert len(calls) == season.RETRIES


def test_schedule_keeps_only_the_columns_the_project_uses(monkeypatch):
    monkeypatch.setattr(
        season.fastf1, "get_event_schedule", lambda year, **kwargs: make_schedule()
    )
    result = season._get_schedule(PAST_SEASON)
    assert result.columns.tolist() == season.SCHEDULE_COLUMNS


def test_schedule_is_served_from_disk_the_second_time(monkeypatch):
    calls = []

    def count_calls(year, **kwargs):
        calls.append(1)
        return make_schedule()

    monkeypatch.setattr(season.fastf1, "get_event_schedule", count_calls)

    first = season._get_schedule(PAST_SEASON)
    second = season._get_schedule(PAST_SEASON)

    assert len(calls) == 1
    pd.testing.assert_frame_equal(first, second)