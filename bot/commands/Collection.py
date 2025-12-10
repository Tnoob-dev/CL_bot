from entry.entry import bot
from utils.functions import check_administration, forward_messages
from utils.db_reqs import insert
from db.create_cine_db import Game
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private, document, video, photo
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from pathlib import Path
from typing import List
import os
import logging


# state for saving messages of files and other data
state = {}


# Logger
logger = logging.getLogger(__name__)


def init_user_state(user_id: int, massive_mode: bool = False) -> None:
    state[str(user_id)] = {
        "collecting": True,
        "massive_mode": massive_mode,
        "messages": [],
        "links": [],  # siempre presente, aunque no se use en modo normal
    }


def get_user_state(user_id: int) -> dict | None:
    return state.get(str(user_id))


def build_season_link(last_message_id: int) -> str:
    name = f"new_{last_message_id}"
    return f"https://t.me/{os.getenv('SENDER_BOT')}?start={name}"


def register_movie(messages: List[int]) -> str:
    
    last_id = messages[-1]
    name = f"new_{last_id}"
    insert(Game(name=name, file_ids=messages))
    return build_season_link(last_id)


# massive command, to add a lot of files, in only one command, instead of multiple /add commands
@bot.on_message(command("massive") & private)
async def massive_collection(client: Client, message: Message):
    if not check_administration(message):
        await message.reply("No tiene permisos para utilizar este comando")
        return

    user_id = message.from_user.id
    if str(user_id) not in state:
        init_user_state(user_id, massive_mode=True)

    await message.reply(
        "Modo masivo activado con las siguientes caracteristicas:\n\n"
        "``````"
    )


# end_massive command, to end the complete task
@bot.on_message(command("end_massive") & private)
async def end_massive(client: Client, message: Message):
    if not check_administration(message):
        await message.reply("No tiene permisos para utilizar este comando")
        return

    user_id = message.from_user.id
    user_state = get_user_state(user_id)

    if not user_state or not user_state.get("massive_mode"):
        await message.reply("No se encuentra en modo masivo")
        return

    links = user_state.get("links", [])
    formed_seasons = []

    season_counter = 1
    for link in links:
        formed_seasons.append((f"Temporada {season_counter}", link))
        season_counter += 1

    await message.reply(f"```python\n{formed_seasons}```")
    await message.reply_document(
        document=Path.cwd() / Path("bot") / Path("core") / "cine.db"
    )

    # delete user from memory
    del state[str(user_id)]


# add command, for start adding messages id to state var
@bot.on_message(command("add") & private)
async def start_collection(client: Client, message: Message):
    # check if user is admin
    if not check_administration(message):
        await message.reply("No tiene permisos para utilizar este comando")
        return

    user_id = message.from_user.id
    if str(user_id) not in state:
        init_user_state(user_id, massive_mode=False)
        await message.reply("Esperando mensajes...\nAl terminar envie /end para crear el post")
    else:
        await message.reply("Usted ya se encuentra actualmente coleccionando archivos")


# end command, finish command add, and forward all the messages to the backup channel
@bot.on_message(command("end") & private)
async def end_collection(client: Client, message: Message):
    try:
        if not check_administration(message):
            await message.reply("No tiene permisos para utilizar este comando")
            return

        user_id = message.from_user.id
        user_state = get_user_state(user_id)

        if not user_state or not user_state.get("collecting"):
            await message.reply("Usted no se encuentra en el modo coleccion")
            return

        messages: List[int] = user_state["messages"]

        if not messages:
            await message.reply("No ha enviado ningun archivo en esta coleccion")
            # si quieres, puedes limpiar el estado aquí
            del state[str(user_id)]
            return

        # forward messages to backup channel
        await forward_messages(client, messages)

        if user_state.get("massive_mode"):
            link = register_movie(messages)
            user_state["links"].append(link)
            messages.clear()
            await message.reply("Mensajes reenviados, envie la siguiente temporada, o envie /end_massive")
        else:
            link = register_movie(messages)

            await message.reply("Mensaje(s) enviados al chat de backup")
            await message.reply(
                "Ha salido del modo coleccion, para iniciar una nueva coleccion "
                f"escriba el comando /add\n\nSu enlace es {link}"
            )
            await message.reply_document(
                document=Path.cwd() / Path("bot") / Path("core") / "cine.db"
            )

            # delete user from memory
            del state[str(user_id)]

    except PeerIdInvalid as e:
        await message.reply(
            f"Error -> **{e}**\n\nEste error tal vez es porque despues de inicializar el bot "
            "no puso algun mensaje random en el canal de backup"
        )
    except Exception as error:
        logger.error(error)
        await message.reply("Ha ocurrido un error inesperado, revise los logs del bot")


# without commands, append messages id to user state message schema
# this will only wait for a document, video or photo
@bot.on_message(private & (document | video | photo))
async def collect_messages(client: Client, message: Message):
    # check user is admin
    try:
        if message.from_user and message.from_user.id is not None:
            if check_administration(message):
                user_id = message.from_user.id
                user_state = get_user_state(user_id)
                if user_state and user_state.get("collecting"):
                    user_state["messages"].append(message.id)
    except AttributeError as error:
        logger.error(error)
