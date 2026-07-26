"""Central application configuration.

Two responsibilities:

1. Load the runtime ``.env`` (from ``DATA_DIR``) into ``os.environ`` so that all
   code — including modules that still read ``os.getenv`` directly — sees the
   configured values regardless of the process working directory.
2. Expose a typed :data:`settings` object for the concerns that benefit most
   from being centralized and path-safe: filesystem locations, database URLs,
   the Telegram client credentials, and the offline-mock flags.

New code should read configuration from :data:`settings` rather than calling
``os.getenv`` directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The runtime data directory holds the .env file, the Pyrogram session, the
# SQLite catalog (cine.db), and any working dirs (subtitles, translations).
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
_ENV_FILE = DATA_DIR / ".env"

# Populate os.environ early so legacy os.getenv call sites keep working no
# matter where the process was started from.
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    """Typed view over the environment.

    All fields are optional with safe defaults so importing the package never
    fails on a partially-filled ``.env`` (useful for tests and minimal dev
    runs). Values are read from ``os.environ`` first, then the ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Filesystem ---------------------------------------------------------
    DATA_DIR: Path = DATA_DIR
    ASSETS_DIR: Path = Path(os.getenv("ASSETS_DIR", "./assets")).resolve()

    # --- Telegram client ----------------------------------------------------
    # Kept as strings (the Pyrogram Client accepts them) so an empty template
    # value never raises a validation error at import time.
    NAME: str = "cinemalibrarybot"
    TELEGRAM_API_ID: str = ""
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_BOT_TOKEN: str = ""

    # --- Databases ----------------------------------------------------------
    USER_DB: str = ""
    POSTGRE_DB_URL: str = ""
    # Optional override for the SQLite movie catalog; defaults under DATA_DIR.
    CINE_DB_URL: str = ""

    # --- Movie info (with offline mock) ------------------------------------
    IMDB_API_URL: str = ""
    MOCK_MOVIE_DATA: bool = False
    FIXTURES_DIR: Path = Path("./tests/fixtures/movie_search")

    # --- Derived paths ------------------------------------------------------
    @computed_field  # type: ignore[prop-decorator]
    @property
    def session_path(self) -> str:
        """Pyrogram session base path (``<DATA_DIR>/<NAME>``)."""
        return str(self.DATA_DIR / self.NAME)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cine_db_url(self) -> str:
        """SQLAlchemy URL for the SQLite catalog."""
        return self.CINE_DB_URL or f"sqlite:///{self.DATA_DIR / 'cine.db'}"

    @property
    def cine_db_path(self) -> Path:
        return self.DATA_DIR / "cine.db"

    @property
    def subtitles_dir(self) -> Path:
        return self.DATA_DIR / "subts"

    @property
    def translations_dir(self) -> Path:
        return self.DATA_DIR / "translations"

    def ensure_runtime_dirs(self) -> None:
        """Create the writable runtime directories if they don't exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_runtime_dirs()
