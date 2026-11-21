"""Tests de la caché en disco. Usan una carpeta temporal, nunca .cache/."""

import os
import time
from datetime import date

import pandas as pd
import pytest

from f1analysis import cache

CURRENT_YEAR = date.today().year
PAST_SEASON = CURRENT_YEAR - 3
FRAME = pd.DataFrame({"value": [1, 2, 3]})


class CountingLoader:
    """Loader que cuenta cuántas veces se le llama."""

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.result


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.delenv(cache.DISABLE_VARIABLE, raising=False)


def test_second_call_is_served_from_disk():
    loader = CountingLoader(FRAME)
    first = cache.cached_dataframe("data", loader, PAST_SEASON)
    second = cache.cached_dataframe("data", loader, PAST_SEASON)

    assert loader.calls == 1
    pd.testing.assert_frame_equal(first, second)


def test_different_parameters_are_cached_separately():
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("data", loader, PAST_SEASON, round_=1)
    cache.cached_dataframe("data", loader, PAST_SEASON, round_=2)
    cache.cached_dataframe("data", loader, PAST_SEASON, round_=1)
    assert loader.calls == 2


def test_different_names_are_cached_separately():
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("one", loader, PAST_SEASON)
    cache.cached_dataframe("two", loader, PAST_SEASON)
    assert loader.calls == 2


def test_none_results_are_not_cached():
    loader = CountingLoader(None)
    assert cache.cached_dataframe("data", loader, PAST_SEASON) is None
    assert cache.cached_dataframe("data", loader, PAST_SEASON) is None

    assert loader.calls == 2
    assert not cache.CACHE_DIR.exists()


def test_cache_can_be_disabled_with_an_environment_variable(monkeypatch):
    monkeypatch.setenv(cache.DISABLE_VARIABLE, "1")
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("data", loader, PAST_SEASON)
    cache.cached_dataframe("data", loader, PAST_SEASON)

    assert loader.calls == 2
    assert not cache.CACHE_DIR.exists()


def test_environment_variable_set_to_zero_does_not_disable_the_cache(monkeypatch):
    monkeypatch.setenv(cache.DISABLE_VARIABLE, "0")
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("data", loader, PAST_SEASON)
    cache.cached_dataframe("data", loader, PAST_SEASON)
    assert loader.calls == 1


def test_corrupt_cache_file_is_downloaded_again():
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("data", loader, PAST_SEASON)
    path = cache._cache_path("data", PAST_SEASON, {})
    path.write_bytes(b"esto no es un pickle")

    result = cache.cached_dataframe("data", loader, PAST_SEASON)

    assert loader.calls == 2
    pd.testing.assert_frame_equal(result, FRAME)


def _make_old(path, extra_seconds):
    old = time.time() - cache.CURRENT_YEAR_TTL - extra_seconds
    os.utime(path, (old, old))


def test_current_year_data_expires_after_the_ttl():
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("data", loader, CURRENT_YEAR)
    _make_old(cache._cache_path("data", CURRENT_YEAR, {}), 60)

    cache.cached_dataframe("data", loader, CURRENT_YEAR)
    assert loader.calls == 2


def test_current_year_data_is_reused_while_fresh():
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("data", loader, CURRENT_YEAR)
    cache.cached_dataframe("data", loader, CURRENT_YEAR)
    assert loader.calls == 1


def test_past_seasons_never_expire():
    loader = CountingLoader(FRAME)
    cache.cached_dataframe("data", loader, PAST_SEASON)
    _make_old(cache._cache_path("data", PAST_SEASON, {}), 10 * 365 * 24 * 3600)

    cache.cached_dataframe("data", loader, PAST_SEASON)
    assert loader.calls == 1