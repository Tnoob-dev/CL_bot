from db.create_cine_db import cine_engine, users_engine, Game, User
from sqlmodel import Session, select
from typing import List, Tuple, Dict
import threading
import time
import os
import logging

# Logger 
logger = logging.getLogger(__name__)

# insert movie to db
def insert(query: Game) -> Dict[str, str]:
    try:
        with Session(cine_engine) as session:
            session.add(query)
            session.commit()
        return {"message": "Juego annadido"}
    except Exception as e:
        logger.error(f"Error al annadir a la db -> {e}")

# get movie from db
def get_game(name: str) -> List[int]:
    try:
        with Session(cine_engine) as session:
            statement = select(Game).where(Game.name == name)
            result = session.exec(statement).first()

            return result.file_ids

    except Exception as e:
        logger.error(f"Error al obtener desde la db -> {e}")


#################################################################

# get user from db
def get_user(id: int) -> Tuple[bool, User] | Tuple[bool, None]:
    try:
        with Session(users_engine) as session:
            statement = select(User).where(User.id == id)
            result = session.exec(statement)
            
            user = result.first()   
                     
            if user is not None:
                return (True, user)
            else:
                return (False, None)
    except Exception as e:
        logger.error(f"Error al obtener desde la db -> {e}")
    
# insert user from db
def insert_user(query: User) -> None:
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
    
# update user translations value, from 5, until 0
def update_user_value(id: int):
    try:
        with Session(users_engine) as session:
            statement = select(User).where(User.id == id)
            user = session.exec(statement).one()
            
            user.rest_tries -= 1
            
            session.add(user)
            session.commit()
            session.refresh(user)
        logger.info(f"al usuario {user.username} le quedan {user.rest_tries} intentos")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error al actualizar al usuario {id}, error -> {e}")

# after 24 hours, reset every user translations to 5
def reset_all_users_tries():
    admins: List[str] = os.getenv("ADMINS").split(",")
    try:
        with Session(users_engine) as session:
            statement = select(User)
            users = session.exec(statement).all()
            
            for user in users:
                if str(user.id) in admins:
                    user.rest_tries = 10000
                else:
                    user.rest_tries = 10
                session.add(user)
            
            session.commit()
        logger.info(f"Se han restablecido los intentos de {len(users)} usuarios")
    except Exception as e:
        session.rollback()
        logger.error(f"Error al restablecer intentos de usuarios -> {e}")


def start_daily_reset():
    def reset_loop():
        while True:
            time.sleep(86400)
            reset_all_users_tries()
    
    thread = threading.Thread(target=reset_loop, daemon=True)
    thread.start()
    logger.info("Sistema de reseteo diario iniciado")