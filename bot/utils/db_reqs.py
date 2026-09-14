import logging
from datetime import datetime

from db.create_cine_db import Game, Post, Users, cine_engine, posts_engine, users_engine
from sqlmodel import Session, select

# Logger
logger = logging.getLogger(__name__)


# insert movie to db
def insert(query: Game) -> dict[str, str] | None:
    try:
        with Session(cine_engine) as session:
            session.add(query)
            session.commit()
        return {"message": "Pelicula o Serie annadida"}
    except Exception as e:
        session.rollback()
        logger.error(f"Error al annadir a la db -> {e}")


# get movie from db
def get_game(name: str) -> list[int]:
    try:
        with Session(cine_engine) as session:
            statement = select(Game).where(Game.name == name)
            result = session.exec(statement).first()

            return result.file_ids

    except Exception as e:
        logger.error(f"Error al obtener desde la db -> {e}")

def update_movie_genres(file_id: str, movie_genres: list[str]):
    
    try:
        with Session(cine_engine) as session:
            statement = select(Game).where(Game.name == file_id)
            
            result = session.exec(statement).first()
            
            result.movie_genres = movie_genres
            
            session.add(result)
            session.commit()
            session.refresh(result)
            
            return True

    except Exception as e:
        logger.error(f"Ha ocurrido una excepcion -> {e}")
        return False

#################################################################


# get user from db
def get_user(id: int = 0, all_the_users: bool = False) -> tuple[bool, Users | list[Users] | None]:
    try:
        with Session(users_engine) as session:
            if id != 0 and not all_the_users:
                statement = select(Users).where(Users.id == id)
                result = session.exec(statement)
                user = result.first()
                if user is not None:
                    return True, user
                else:
                    return False, None
            else:
                statement = select(Users)
                users = session.exec(statement).all()
                return True, list(users)
    except Exception as e:
        logger.error(f"Error al obtener desde la db -> {e}")
        return False, None


# insert user to db
def insert_user(query: Users) -> tuple[bool, str] | None:
    try:
        r = get_user(query.id)

        # logger.info(r)

        if not r[0]:
            with Session(users_engine) as session:
                session.add(query)
                session.commit()
            return True, "Usuario añadido a la db"
        else:
            return False, "El usuario ya se encuentra en la db"
    except Exception as e:
        logger.error(f"Error al annadir a la db -> {e}")

########### apply this function tomorrow
def update_user_genres(id: int, genres: list[str]):
    
    try:
        with Session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = session.exec(statement).one()
            
            if user.genre_stats is None:
                user.genre_stats = {}
                
            for genre in genres:
                genre_clean = genre.strip()
                if genre_clean:
                    user.genre_stats[genre_clean] =  user.genre_stats.get(genre_clean, 0) + 1
                    
            session.add(user)
            session.commit()
            session.refresh(user)
    except Exception as e:
        logger.error(f"Error al actualizar contador de generos: USER_ID: {user.id}\n\nError:{e}")    

# update user translations value, from 10, until 0
def update_user_value(id: int) -> None:
    try:
        with Session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = session.exec(statement).one()

            user.rest_tries -= 1

            session.add(user)
            session.commit()
            session.refresh(user)
        logger.info(f"al usuario {user.username} le quedan {user.rest_tries} intentos")

    except Exception as e:
        session.rollback()
        logger.error(f"Error al actualizar al usuario {id}, error -> {e}")


def update_user_downloads(id: int) -> None:
    try:
        with Session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = session.exec(statement).one()

            user.int_downloaded += 1

            session.add(user)
            session.commit()
            session.refresh(user)
        logger.info(f"al usuario {user.username} se le ha sumado una descarga")

    except Exception as e:
        session.rollback()
        logger.error(f"Error al actualizar al usuario {id}, error -> {e}")


def update_user_admin(id: int) -> tuple[bool, str]:

    try:
        boolean, _ = get_user(id, all_the_users=False)

        if not boolean:
            return False, f"Usuario {id} no esta en la db"

        key_word = None

        with Session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = session.exec(statement).one()

            if not user.is_admin:
                user.is_admin = True
                session.commit()
                key_word = "**ascendido**"
            else:
                user.is_admin = False
                session.commit()
                key_word = "**degradado**"
            session.refresh(user)

        logger.info(f"Se han desplegado acciones sobre el usuario {id}")
        return (True, f"Usuario {id} ha sido {key_word}")

    except Exception as e:
        session.rollback()
        logger.error(f"Ocurrio un error al cambiar ajustes de usuario -> {e}")
        return False, "Ocurrió un error al actualizar los permisos del usuario"


def update_user_premium(id: int, days: int = 30) -> tuple[bool, str]:
    try:
        boolean, _ = get_user(id, all_the_users=False)
        if not boolean:
            return False, "Usuario no encontrado"

        with Session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = session.exec(statement).one()

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
            session.commit()
            session.refresh(user)

            # Formateamos la fecha para mostrarla al usuario (DD/MM/AAAA)
            expiration_date_str = datetime.fromtimestamp(new_expiration).strftime(
                "%d/%m/%Y"
            )

        logger.info(f"Usuario {id} actualizado a premium hasta {expiration_date_str}")
        return True, expiration_date_str

    except Exception as e:
        logger.error(f"Error al cambiar ajustes premium del usuario {id} -> {e}")
        return False, "Ocurrió un error al actualizar el plan premium del usuario"


def is_premium_active(id: int) -> bool:
    try:
        boolean, user = get_user(id, all_the_users=False)
        if not boolean or not user or not user.premium_user:
            return False

        now = int(datetime.now().timestamp())
        # Si tiene fecha de expiración y la fecha actual es mayor, expiró
        if user.premium_expires and now > user.premium_expires:
            revoke_premium(id)  # Lo desactivamos automáticamente
            return False

        return True
    except Exception as e:
        logger.error(f"Error verificando premium del usuario {id} -> {e}")
        return False


def revoke_premium(id: int) -> bool:
    try:
        with Session(users_engine) as session:
            statement = select(Users).where(Users.id == id)
            user = session.exec(statement).one()

            user.premium_user = False
            user.premium_expires = None

            session.add(user)
            session.commit()
        logger.info(f"Premium revocado para usuario {id}")
        return True
    except Exception as e:
        logger.error(f"Error revocando premium del usuario {id} -> {e}")
        return False


#################################################################


def get_post_by_name(name: str) -> list[dict[str, str]] | list:
    try:
        with Session(posts_engine) as session:
            pattern = f"%{name}%"
            statement = select(Post).where(Post.movie_name.ilike(pattern))
            results = session.exec(statement).all()

            return [{"name": res.movie_name, "link": res.link} for res in results]
    except Exception as e:
        logger.error(e)
        return []


def get_post_by_id(id: int) -> Post | None:
    try:
        with Session(posts_engine) as session:
            statement = select(Post).where(Post.id == id)

            post = session.exec(statement).one()

            if not post:
                return None

            return post
    except Exception as e:
        logger.error(e)
        raise


def insert_post(query: Post) -> dict[str, str]:
    try:
        with Session(posts_engine) as session:
            session.add(query)
            session.commit()
        return {"message": "Post added"}
    except Exception as e:
        session.rollback()
        logger.error(e)


def delete_post(id: int) -> tuple[bool, str]:

    try:
        with Session(posts_engine) as session:
            statement = select(Post).where(Post.id == id)

            founded_post = session.exec(statement).one()

            if founded_post is not None:
                session.delete(founded_post)
                session.commit()

                logger.info(f"Post {id} eliminado correctamente")
                return (True, f"Post {id} eliminado correctamente de la db")

    except Exception as e:
        logger.error(f"Ha ocurrido una excepcion en los posts -> {e}")
        return (False, "Ocurrió un error al eliminar el post de la base de datos")

def get_genres_from_post_by_file_ids(file_ids: list[int]):
    
    try:
        with Session(posts_engine) as session:
            statement = select(Post).where(Post.file_ids == file_ids)
            
            result = session.exec(statement).first()
            
            if not result:
                return None
            
            return result
    except Exception as e:
        logger.error(f"Ha ocurrido una excepcion en los posts -> {e}")