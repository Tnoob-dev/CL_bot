import logging
import os
from functools import cache

from sqlalchemy import Engine, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.ext.mutable import MutableDict
from sqlmodel import JSON, BigInteger, Column, Field, SQLModel, create_engine

# Logger
logger = logging.getLogger(__name__)


# Movies database (the name is game cuz this is the same code used in games library first version bot)
class Game(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default=None, index=True)
    file_ids: list[int] = Field(sa_column=Column(JSON))
    movie_genres: list[str] = Field(sa_column=Column(JSON))

# Users database
class Users(SQLModel, table=True):
    id: int | None = Field(sa_type=BigInteger, default=None, primary_key=True)
    username: str | None = Field(default=None)
    rest_tries: int = Field(default=5)
    is_admin: bool = Field(default=False)
    premium_user: bool = Field(default=False)
    premium_expires: int | None = Field(default=None)
    int_downloaded: int = Field(default=0)
    genre_stats: dict = Field(default_factory=dict, sa_column=Column(MutableDict.as_mutable(JSONB)))

# Posts database to save and show posts when user or admin needs it
class Post(SQLModel, table=True):
    __table_args__ = (
        Index("ix_post_movie_name_trgm", "movie_name", postgresql_using="gin", postgresql_ops={"movie_name": "gin_trgm_ops"}),
        Index("ix_post_movie_genres", "movie_genres", postgresql_using="gin"),
    )

    id: int | None = Field(default=None, primary_key=True)
    movie_name: str = Field(default=None)
    movie_genres: list[str] = Field(sa_column=Column(JSONB))
    link: str = Field(default=None)
    file_ids: list[str] = Field(sa_column=Column(JSON))

# use sqlite or postgres, idk just specify it in your environment

# The DB host caps each database at 5 connections
_POOL = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "4")),
    "max_overflow": 0,
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_pre_ping": True,
    "pool_recycle": 300,
}


@cache
def _engine(url: str) -> Engine:
    return create_engine(url, **_POOL)


cine_engine = _engine(os.getenv("POSTGRE_CINE_DB"))
users_engine = _engine(os.getenv("USER_DB"))
posts_engine = _engine(os.getenv("POSTGRE_DB_URL"))


_MIGRATIONS = {
    "pg_trgm": "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "post.movie_genres a jsonb": """
        DO $$ BEGIN
            IF (SELECT data_type FROM information_schema.columns
                WHERE table_name = 'post' AND column_name = 'movie_genres') = 'json' THEN
                ALTER TABLE post ALTER COLUMN movie_genres TYPE jsonb USING movie_genres::jsonb;
            END IF;
        END $$
    """,
}


def _run(engine: Engine, description: str, statement) -> None:
    # A failed migration must not stop the bot: queries work without it, only slower
    try:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL lock_timeout = '10s'"))
            conn.execute(statement)
    except Exception:
        logger.exception("No se pudo aplicar la migracion: %s", description)


def _create(engine: Engine, model: type[SQLModel], migrations: dict[str, str] | None = None) -> None:
    table = model.__table__
    with engine.begin() as conn:
        conn.execute(CreateTable(table, if_not_exists=True))

    for description, sql in (migrations or {}).items():
        _run(engine, description, text(sql))

    for index in table.indexes:
        _run(engine, f"indice {index.name}", CreateIndex(index, if_not_exists=True))


def create_db():
    _create(cine_engine, Game)
    _create(users_engine, Users)
    _create(posts_engine, Post, _MIGRATIONS)
    logger.info("Todas las db han sido creadas")
