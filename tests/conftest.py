"""Shared test configuration.

Sets a safe, offline environment *before* the application package is imported,
so importing it never touches a real Telegram/Postgres/API endpoint and writes
only to a throwaway data directory.
"""

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_TEST_DATA = _ROOT / ".pytest-data"

os.environ.setdefault("DATA_DIR", str(_TEST_DATA))
os.environ.setdefault("MOCK_MOVIE_DATA", "1")
os.environ.setdefault("IMDB_API_URL", "")
os.environ.setdefault("FIXTURES_DIR", str(_ROOT / "tests" / "fixtures" / "movie_search"))

# Dummy Telegram credentials so the Pyrogram Client can be constructed offline.
os.environ.setdefault("TELEGRAM_API_ID", "12345")
os.environ.setdefault("TELEGRAM_API_HASH", "0123456789abcdef0123456789abcdef")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "12345:TEST-TOKEN")

# Point the databases at throwaway SQLite files (only used if create_db runs).
os.environ.setdefault("USER_DB", f"sqlite:///{_TEST_DATA / 'users.db'}")
os.environ.setdefault("POSTGRE_DB_URL", f"sqlite:///{_TEST_DATA / 'posts.db'}")
