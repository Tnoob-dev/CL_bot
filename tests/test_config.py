"""Tests for the central configuration module."""

from pathlib import Path

from cinemalibrarybot.config import Settings


def test_settings_load_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NAME", "testbot")
    monkeypatch.setenv("USER_DB", "sqlite:///users.db")

    s = Settings()

    assert s.NAME == "testbot"
    assert s.USER_DB == "sqlite:///users.db"
    assert s.DATA_DIR == tmp_path


def test_derived_paths_resolve_under_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NAME", "mybot")

    s = Settings()

    assert s.session_path == str(tmp_path / "mybot")
    assert s.cine_db_path == tmp_path / "cine.db"
    assert s.cine_db_url == f"sqlite:///{tmp_path / 'cine.db'}"
    assert s.subtitles_dir == tmp_path / "subts"
    assert s.translations_dir == tmp_path / "translations"


def test_cine_db_url_override(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CINE_DB_URL", "sqlite:///custom.db")

    s = Settings()

    assert s.cine_db_url == "sqlite:///custom.db"


def test_assets_dir_is_absolute():
    s = Settings()
    assert isinstance(s.ASSETS_DIR, Path)
    assert s.ASSETS_DIR.is_absolute()


def test_mock_flag_parsing(monkeypatch):
    monkeypatch.setenv("MOCK_MOVIE_DATA", "1")
    assert Settings().MOCK_MOVIE_DATA is True

    monkeypatch.setenv("MOCK_MOVIE_DATA", "0")
    assert Settings().MOCK_MOVIE_DATA is False
