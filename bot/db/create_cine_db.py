from sqlmodel import SQLModel, Field, create_engine, Column, JSON
from typing import Optional, List
import os
import logging

# Logger 
logger = logging.getLogger(__name__)

# Movies database (the name is game cuz this is the same code used in games library)
class Game(SQLModel, table = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default=None)
    file_ids: List[int] = Field(sa_column=Column(JSON))

# User database for translations
class User(SQLModel, table = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default=None)
    rest_tries: int = Field(default=5)

cine_engine = create_engine("sqlite:///./bot/core/cine.db")
users_engine = create_engine("sqlite:///./bot/core/users.db")

def create_db():
    if not os.path.exists("./bot/core/cine.db"):
        Game.__table__.create(cine_engine)
        
    if not os.path.exists("./bot/core/users.db"):
        User.__table__.create(users_engine)
        
    logger.info("Todas las db han sido creadas")