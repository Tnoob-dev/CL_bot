from db.create_cine_db import cine_engine, users_engine, Game, User
from sqlmodel import Session, select
from typing import List, Tuple
import threading
import time

def insert(query: Game) -> None: # No estoy pa retornar el str del print xd
    try:
        with Session(cine_engine) as session:
            session.add(query)
            session.commit()
        print("Juego annadido")
    except Exception as e:
        raise Exception(f"Error al annadir a la db -> {e}")

def get_game(name: str) -> List[int]:
    try:
        with Session(cine_engine) as session:
            statement = select(Game).where(Game.name == name)
            result = session.exec(statement).first()

            return result.file_ids

    except Exception as e:
        raise Exception(f"Error al obtener desde la db -> {e}")


#################################################################

def get_user(id: int) -> Tuple[bool, User] | Tuple[bool, None]:
    try:
        with Session(users_engine) as session:
            statement = select(User).where(User.id == id)
            result = session.exec(statement)
            
            if result:
                return (True, result.first())
            else:
                return (False, None)
    except Exception as e:
        raise Exception(f"Error al obtener desde la db -> {e}")
    

def insert_user(query: User) -> None:
    try:
        r = get_user(query.id)
        
        if not r[0]:
            with Session(users_engine) as session:
                session.add(query)
                session.commit()
            print("Usuario annadido")
        else:
            print("El usuario ya esta en la db")
    except Exception as e:
        raise Exception(f"Error al annadir a la db -> {e}")
    
def update_user_value(id: int):
    try:
        with Session(users_engine) as session:
            statement = select(User).where(User.id == id)
            user = session.exec(statement).one()
            
            user.rest_tries -= 1
            
            session.add(user)
            session.commit()
            session.refresh(user)
        print(f"al usuario {user.username} le quedan {user.rest_tries} intentos")
            
    except Exception as e:
        session.rollback()
        raise Exception(f"Error al actualizar al usuario {id}, error -> {e}")


def reset_all_users_tries():
    try:
        with Session(users_engine) as session:
            statement = select(User)
            users = session.exec(statement).all()
            
            for user in users:
                user.rest_tries = 5
                session.add(user)
            
            session.commit()
        print(f"Se han restablecido los intentos de {len(users)} usuarios")
    except Exception as e:
        session.rollback()
        raise Exception(f"Error al restablecer intentos de usuarios -> {e}")


def start_daily_reset():
    def reset_loop():
        while True:
            time.sleep(86400)  # 24 horas en segundos
            reset_all_users_tries()
    
    thread = threading.Thread(target=reset_loop, daemon=True)
    thread.start()
    print("Sistema de reseteo diario iniciado")
