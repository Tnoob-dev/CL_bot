import logging

from db.create_cine_db import Users
from entry.entry import bot
from opensubtitlescom import OpenSubtitlesException
from pyrogram.client import Client
from pyrogram.filters import command, private
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.db_reqs import get_user, insert_user
from utils.functions import check_user_in_channel
from utils.search_subts import subs

# Logger
logger = logging.getLogger(__name__)

# Mensajes de uso comun (evita duplicar cadenas entre /srt y /bsrt)
NO_RESULTS_TEXT = "No se ha encontrado nada, asegurese de que haya escrito bien el nombre."
USAGE_TEXT = (
    "❌Debe enviar el comando y luego el nombre de la serie/pelicula, junto a la "
    "temporada y/o episodio.❓Ejemplos:\n\n/srt Breaking Bad Season 1\n"
    "/srt Breaking Bad S01E01\n/srt Breaking Bad Temporada 2 Episodio 3"
)
SEARCH_ERROR_TEXT = "❌ Ocurrió un error al buscar subtítulos. Inténtalo de nuevo más tarde."


async def ensure_user_in_db(message: Message):
    """Registra al usuario en la BD si aun no existe."""
    if get_user(message.from_user.id)[0]:
        return

    await message.reply(
        "Al parecer usted no habia entrado a la DB, ya se encuentra dentro, disfrute"
    )
    username = message.from_user.username or ""
    insert_user(Users(id=message.from_user.id, username=username))


def _build_results_markup(result, callback_prefix: str, bulk: bool) -> InlineKeyboardMarkup:
    """Construye el teclado de resultados para modo normal o bulk."""
    rows = [
        [
            InlineKeyboardButton(
                text=f"🔡{sub.file_name}🔡",
                callback_data=f"{callback_prefix}{sub.file_id}",
            )
        ]
        for sub in result
    ]
    if bulk:
        rows.append([InlineKeyboardButton(text="Finalizar❌", callback_data="bulk_end")])
    return InlineKeyboardMarkup(rows)


async def _handle_subtitle_search(client: Client, message: Message, bulk: bool):
    """Flujo compartido de busqueda de subtitulos para /srt y /bsrt."""
    if not await check_user_in_channel(client, message):
        return

    await ensure_user_in_db(message)

    try:
        if len(message.command) < 2:
            await message.reply(USAGE_TEXT)
            return

        query = " ".join(message.command[1:])
        result = subs(query)

        if not result:
            await message.reply(NO_RESULTS_TEXT)
            return

        header = (
            f"🔥Resultados de la busqueda en modo bulk (Para finalizar esta busqueda "
            f"presione el boton de Finalizar❌ en lo ultimo de los botones): ||{query}||🔎:"
            if bulk
            else f"🔥Resultados de la busqueda ||{query}||🔎:"
        )
        await message.reply(
            header,
            reply_markup=_build_results_markup(
                result,
                callback_prefix="bulk_sub_" if bulk else "sub_",
                bulk=bulk,
            ),
        )
    except OpenSubtitlesException as error:
        logger.error(error)
        await message.reply(SEARCH_ERROR_TEXT)


@bot.on_message(command("srt", prefixes=["/"]) & private)
async def search_subtitles(client: Client, message: Message):
    await _handle_subtitle_search(client, message, bulk=False)


@bot.on_message(command("bsrt", prefixes=["/"]) & private)
async def search_subtitles_to_bulk(client: Client, message: Message):
    await _handle_subtitle_search(client, message, bulk=True)
