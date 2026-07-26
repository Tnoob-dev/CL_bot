"""Seed the databases with sample data for local development.

Inserts a handful of posts (so /search, the inline query and #cine requests
return results), a catalog entry, and a sample user. Safe to run repeatedly.

Usage:
    uv run python scripts/seed_dev_data.py
    # or, inside the dev stack:
    make seed
"""

from __future__ import annotations

import logging

from cinemalibrarybot.repositories.create_cine_db import (
    Game,
    Post,
    Users,
    create_db,
)
from cinemalibrarybot.repositories.db_reqs import insert, insert_post, insert_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

SAMPLE_POSTS = [
    ("The Shawshank Redemption", "https://t.me/example/1"),
    ("Breaking Bad", "https://t.me/example/2"),
    ("Leon: The Professional", "https://t.me/example/3"),
    ("The Matrix", "https://t.me/example/4"),
    ("Interstellar", "https://t.me/example/5"),
]

SAMPLE_CATALOG = [
    ("The Matrix", [101, 102]),
    ("Interstellar", [201]),
]

SAMPLE_USERNAME = "dev_user"


def main() -> None:
    create_db()

    for name, link in SAMPLE_POSTS:
        insert_post(Post(movie_name=name, link=link))
        logger.info("post seeded: %s", name)

    for name, file_ids in SAMPLE_CATALOG:
        insert(Game(name=name, file_ids=file_ids))
        logger.info("catalog seeded: %s", name)

    insert_user(Users(id=1, username=SAMPLE_USERNAME, is_admin=True, premium_user=True))
    logger.info("user seeded: %s", SAMPLE_USERNAME)

    logger.info("Done. Try /search matrix in your dev bot.")


if __name__ == "__main__":
    main()
