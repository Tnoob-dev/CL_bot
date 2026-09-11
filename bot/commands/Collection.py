import logging
from pathlib import Path

from entry.entry import bot
from pyrogram.client import Client
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from pyrogram.filters import command, document, photo, private, video
from pyrogram.types import Message
from utils.functions import check_administration, forward_messages, register_movie

# state for saving messages of files and other data
state = {}


# Logger
logger = logging.getLogger(__name__)


def init_user_state(user_id: int, massive_mode: bool = False) -> None:
    state[str(user_id)] = {
        "collecting": True,
        "massive_mode": massive_mode,
        "messages": [],
        "links": [],
    }


def get_user_state(user_id: int) -> dict | None:
    return state.get(str(user_id))


@bot.on_message(command("massive") & private)
async def massive_collection(client: Client, message: Message):
    if not check_administration(message):
        await message.reply("No tiene permisos para utilizar este comando")
        return

    if message.from_user is not None:
        user_id = message.from_user.id

    if str(user_id) not in state:
        init_user_state(user_id, massive_mode=True)

    await message.reply(
        "Modo masivo activado con las siguientes caracteristicas:\n\n"
        "```OwO\nModo collecion: activado\nSi lees esto eres gay```"
    )


# end_massive command, to end the complete task
@bot.on_message(command("end_massive") & private)
async def end_massive(client: Client, message: Message):
    if not check_administration(message):
        await message.reply("No tiene permisos para utilizar este comando")
        return

    if message.from_user is not None:
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
        document=str(Path.cwd() / Path("bot") / Path("core") / "cine.db")
    )

    del state[str(user_id)]


# end command, forward all the messages to the backup channel
@bot.on_message(command("end") & private)
async def end_collection(client: Client, message: Message):
    try:
        if not check_administration(message):
            await message.reply("No tiene permisos para utilizar este comando")
            return

        if message.from_user is not None:
            user_id = message.from_user.id

        user_state = get_user_state(user_id)

        if not user_state or not user_state.get("collecting"):
            await message.reply("Usted no se encuentra en el modo coleccion")
            return

        messages: list[int] = user_state["messages"]

        if not messages:
            await message.reply("No ha enviado ningun archivo en esta coleccion")
            del state[str(user_id)]
            return

        # forward messages to backup channel
        ids_in_channel = await forward_messages(client, messages)
        messages[:] = ids_in_channel

        if user_state.get("massive_mode"):
            link = register_movie(messages)
            user_state["links"].append(link)
            messages.clear()
            await message.reply(
                "Mensajes reenviados, envie la siguiente temporada, o envie /end_massive"
            )
        else:
            link = register_movie(messages)

            await message.reply("Mensaje(s) enviados al chat de backup")
            await message.reply(
                "Ha salido del modo coleccion, para iniciar una nueva coleccion "
                f"escriba el comando /add\n\nSu enlace es {link}"
            )
            await message.reply_document(
                document=str(Path.cwd() / Path("bot") / Path("core") / "cine.db")
            )

            # delete user from memory
            del state[str(user_id)]

    except PeerIdInvalid:
        await message.reply(
            "❌ Ocurrió un error al reenviar los archivos. "
            "Esto puede deberse a que el canal de backup no está configurado correctamente. "
            "Contacta al administrador si el problema persiste."
        )


# without commands, append messages id to user state message schema
# this will only wait for a document, video or photo
@bot.on_message(private & (document | video | photo), group=1)
async def collect_messages(client: Client, message: Message):
    try:
        if message.from_user and message.from_user.id is not None and check_administration(message):
            user_id = message.from_user.id
            user_state = get_user_state(user_id)
            if user_state and user_state.get("collecting"):
                user_state["messages"].append(message.id)
    except AttributeError as error:
        logger.error(error)
