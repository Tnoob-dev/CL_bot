import logging
import os

from sqlmodel import JSON, BigInteger, Column, Field, SQLModel, create_engine

# Logger
logger = logging.getLogger(__name__)


# Movies database (the name is game cuz this is the same code used in games library first version bot)
class Game(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default=None)
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
    genre_stats: dict = Field(default_factory=dict, sa_column=Column(JSON))

# Posts database to save and show posts when user or admin needs it
class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movie_name: str = Field(default=None)
    movie_genres: list[str] = Field(sa_column=Column(JSON))
    link: str = Field(default=None)
    file_ids: list[str] = Field(sa_column=Column(JSON))


# cine_engine = create_engine("sqlite:///./bot/core/cine.db")
cine_engine = create_engine(os.getenv("POSTGRE_CINE_DB"))
# users_engine = create_engine("sqlite:///./bot/core/users.db")
users_engine = create_engine(os.getenv("USER_DB"))
posts_engine = create_engine(os.getenv("POSTGRE_DB_URL"))


def create_db():
    if not os.path.exists("./bot/core/cine.db"):
        Game.__table__.create(cine_engine)

    Users.__table__.create(users_engine, checkfirst=True)

    Post.__table__.create(posts_engine, checkfirst=True)
    logger.info("Todas las db han sido creadas")
