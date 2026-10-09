import logging
from datetime import datetime

from db.create_cine_db import Game, Post, Users, cine_engine, posts_engine, users_engine
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import cast, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .cache import ttl_cache

# Logger
logger = logging.getLogger(__name__)


def _session(engine) -> AsyncSession:
    # Without expire_on_commit=False, reading an attribute after commit triggers lazy IO and fails under async
    return AsyncSession(engine, expire_on_commit=False)


# insert movie to db
async def insert(query: Game) -> dict[str, str] | None:
    try:
        async with _session(cine_engine) as session:
            session.add(query)
            await session.commit()
        
    except Exception:
        logger.exception("Error al annadir a la db")
    else:
        return {"message": "Pelicula o Serie annadida"}

# get movie from db
@ttl_cache(maxsize=5_000, ttl=600)
async def get_game(name: str) -> Game:
    try:
        async with _session(cine_engine) as session:
            statement = select(Game).where(Game.name == name)
            result = (await session.exec(statement)).first()

            return result

    except Exception:
        logger.exception("Error al obtener desde la db")

async def update_movie_genres(file_id: str, movie_genres: list[str]):
    
    try:
        async with _session(cine_engine) as session:
            statement = select(Game).where(Game.name == file_id)
            
            result = (await session.exec(statement)).first()
            
            result.movie_genres = movie_genres
            
            session.add(result)
            await session.commit()
            await session.refresh(result)
        get_game.forget(file_id)

    except Exception:
        logger.exception("Ha ocurrido una excepcion")
        return False
    else:
        return True

#################################################################


@ttl_cache(maxsize=20_000, ttl=60)
async def _get_user_by_id(id: int) -> Users | None:
    async with _session(users_engine) as session:
        return (await session.exec(select(Users).where(Users.id == id))).first()


# get user from db
async def get_user(id: int = 0, all_the_users: bool = False) -> tuple[bool, Users | list[Users] | None]:
    try:
        if id != 0 and not all_the_users:
            user = await _get_user_by_id(id)
            return user is not None, user

        async with _session(users_engine) as session:
            return True, list((await session.exec(select(Users))).all())
    except Exception:
        logger.exception("Error al obtener desde la db")
        return False, None


async def get_user_counts() -> tuple[int, int]:
    try:
        async with _session(users_engine) as session:
            statement = select(func.count(), func.count().filter(Users.premium_user))
            return tuple((await session.exec(statement)).one())
    except Exception:
        logger.exception("Error al contar usuarios")
        return 0, 0


async def get_top_users(limit: int = 10) -> list[Users]:
    try:
        async with _session(users_engine) as session:
            statement = select(Users).order_by(Users.int_downloaded.desc()).limit(limit)
            return list((await session.exec(statement)).all())
    except Exception:
        logger.exception("Error al obtener el top de usuarios")
        return []


# insert user to db
async def insert_user(query: Users) -> tuple[bool, str] | None:
    try:
        statement = (
            pg_insert(Users)
            .values(**query.model_dump())
            .on_conflict_do_nothing(index_elements=[Users.id])
        )
        async with _session(users_engine) as session:
            inserted = (await session.exec(statement)).rowcount
            await session.commit()
    except Exception:
        logger.exception("Error al annadir a la db ")
    else:
        if inserted:
            return True, "Usuario añadido a la db"
        return False, "El usuario ya se encuentra en la db"


async def get_or_create_user(user: Users) -> Users | None:
    found, db_user = await get_user(user.id)
    if found:
        return db_user
    await insert_user(user)
    return (await get_user(user.id))[1]


_RECORD_DOWNLOAD = text(f"""
    UPDATE {Users.__tablename__}
    SET int_downloaded = int_downloaded + 1,
        genre_stats = COALESCE(genre_stats, '{{}}'::jsonb) || COALESCE((
            SELECT jsonb_object_agg(g, COALESCE((genre_stats ->> g)::int, 0) + n)
            FROM (SELECT g, count(*) AS n FROM unnest(CAST(:genres AS text[])) AS g GROUP BY g) AS counts
        ), '{{}}'::jsonb)
    WHERE id = :id
""")


async def record_download(id: int, genres: list[str]) -> None:
    genres = [genre.strip() for genre in genres or [] if genre and genre.strip()]
    try:
        async with _session(users_engine) as session:
            await session.exec(_RECORD_DOWNLOAD, params={"id": id, "genres": genres})
            await session.commit()
        _get_user_by_id.forget(id)
    except Exception:
        logger.exception("Error al registrar la descarga del usuario %s", id)

# update user translations value, from 10, until 0
async def update_user_value(id: int) -> None:
    try:
        async with _session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = (await session.exec(statement)).one()

            user.rest_tries -= 1

            session.add(user)
            await session.commit()
            await session.refresh(user)
        _get_user_by_id.forget(id)
        logger.info("Al usuario %s le quedan %s intentos", user.username, user.rest_tries)

    except Exception:
        logger.exception("Error al actualizar al usuario %s", id)



async def update_user_admin(id: int) -> tuple[bool, str]:

    try:
        boolean, _ = await get_user(id, all_the_users=False)

        if not boolean:
            return False, f"Usuario {id} no esta en la db"

        key_word = None

        async with _session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = (await session.exec(statement)).one()

            if not user.is_admin:
                user.is_admin = True
                await session.commit()
                key_word = "**ascendido**"
            else:
                user.is_admin = False
                await session.commit()
                key_word = "**degradado**"
            await session.refresh(user)
        _get_user_by_id.forget(id)

        logger.info("Se han desplegado acciones sobre el usuario %s", id)
        
    except Exception:
        logger.exception("Ocurrio un error al cambiar ajustes de usuario")
        return False, "Ocurrió un error al actualizar los permisos del usuario"
    else:
        return (True, f"Usuario {id} ha sido {key_word}")

async def update_user_premium(id: int, days: int = 30) -> tuple[bool, str]:
    try:
        boolean, _ = await get_user(id, all_the_users=False)
        if not boolean:
            return False, "Usuario no encontrado"

        async with _session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = (await session.exec(statement)).one()

            # Calculamos la fecha base: si ya es premium y no ha expirado, sumamos a su fecha actual.
            # Si no, sumamos a partir de hoy.
            now = int(datetime.now().timestamp())
            base_time = (
                user.premium_expires
                if (user.premium_expires and user.premium_expires > now)
                else now
            )

            # Sumamos los días en segundos
            new_expiration = base_time + (days * 24 * 60 * 60)

            user.premium_user = True
            user.premium_expires = new_expiration

            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Formateamos la fecha para mostrarla al usuario (DD/MM/AAAA)
            expiration_date_str = datetime.fromtimestamp(new_expiration).strftime(
                "%d/%m/%Y"
            )
        _get_user_by_id.forget(id)

        logger.info("Usuario %s actualizado a premium hasta %s", id, expiration_date_str)

    except Exception:
        logger.exception("Error al cambiar ajustes premium del usuario %s", id)
        return False, "Ocurrió un error al actualizar el plan premium del usuario"
    else:
        return True, expiration_date_str

async def is_premium(user: Users) -> bool:
    if not user.premium_user:
        return False

    if user.premium_expires and int(datetime.now().timestamp()) > user.premium_expires:
        await revoke_premium(user.id)
        return False

    return True


async def is_premium_active(id: int) -> bool:
    found, user = await get_user(id, all_the_users=False)
    return found and await is_premium(user)


async def revoke_premium(id: int) -> bool:
    try:
        async with _session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = (await session.exec(statement)).one()

            user.premium_user = False
            user.premium_expires = None

            session.add(user)
            await session.commit()
        _get_user_by_id.forget(id)
        logger.info("Premium revocado para usuario %s", id)
    except Exception:
        logger.exception("Error revocando premium del usuario %s", id)
        return False
    else:
        return True


#################################################################


@ttl_cache(maxsize=2_000, ttl=60)
async def get_post_by_name(name: str) -> list[dict[str, str]] | list:
    try:
        async with _session(posts_engine) as session:
            pattern = f"%{name}%"
            statement = select(Post).where(Post.movie_name.ilike(pattern))
            results = (await session.exec(statement)).all()

    except Exception:
        logger.exception("Error al obtener post por su nombre")
        return []
    else:
        return [{"name": res.movie_name, "link": res.link} for res in results]
        
    
async def get_posts_by_genre(genre: str) -> list[Post | None]:
    try:
        async with _session(posts_engine) as session:
            statement = select(Post).where(
                # search among all the posts and filter by the spcified genre
                cast(Post.movie_genres, JSONB).op('?')(genre)
            )
            
            posts = (await session.exec(statement)).all()
            
    except Exception:
        logger.exception("Error al obtener posts por su genero")
        return []
    else:
        return posts


async def get_post_by_id(id: int) -> Post | None:
    try:
        async with _session(posts_engine) as session:
            statement = select(Post).where(Post.id == id)

            post = (await session.exec(statement)).one()

            if not post:
                return None

            return post
    except Exception:
        logger.exception("Error al obtener post por su ID")


async def insert_post(query: Post) -> dict[str, str]:
    try:
        async with _session(posts_engine) as session:
            session.add(query)
            await session.commit()
        get_post_by_name.clear()
    except Exception:
        logger.exception("Error al insertar post")
    else:
        return {"message": "Post added"}


async def delete_post(id: int) -> tuple[bool, str]:

    try:
        async with _session(posts_engine) as session:
            statement = select(Post).where(Post.id == id)

            founded_post = (await session.exec(statement)).one()

            if founded_post is not None:
                await session.delete(founded_post)
                await session.commit()
                get_post_by_name.clear()

                logger.info("Post %s eliminado correctamente", id)
                return (True, f"Post {id} eliminado correctamente de la db")

    except Exception:
        logger.exception("Ha ocurrido una excepcion en los posts")
        return (False, "Ocurrió un error al eliminar el post de la base de datos")

async def get_genres_from_post_by_file_ids(file_ids: list[int]):
    
    try:
        async with _session(posts_engine) as session:
            statement = select(Post).where(Post.file_ids == file_ids)
            
            result = (await session.exec(statement)).first()
            
            if not result:
                return None
            
            return result
    except Exception:
        logger.exception("Ha ocurrido una excepcion en los posts")