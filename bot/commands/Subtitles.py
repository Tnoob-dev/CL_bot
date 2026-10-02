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

async def check_user_in_db(message: Message):
    user_founded = get_user(message.from_user.id)[0]
    
    if not user_founded:
        await message.reply(
            "Al parecer usted no habia entrado a la DB, ya se encuentra dentro, disfrute"
        )
        username = (
            message.from_user.username
            if message.from_user.username is not None
            else ""
        )
        user = Users(id=message.from_user.id, username=username)
        insert_user(user)

@bot.on_message(command("srt", prefixes=["/"]) & private)
async def search_subtitles(client: Client, message: Message):
    
    if not await check_user_in_channel(client, message):
            return
        
    await check_user_in_db(message)
    
    try:
        if len(message.command) >= 2:
            movie = message.command
            movie.pop(0)

            query = " ".join(movie)

            result = subs(query)

            if result is not None and len(result) > 0:
                await message.reply(
                    f"🔥Resultados de la busqueda ||{query}||🔎:",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text=f"🔡{sub.file_name}🔡",
                                    callback_data=f"sub_{sub.file_id}",
                                )
                            ]
                            for sub in result
                        ]
                    ),
                )
            else:
                await message.reply(
                    "No se ha encontrado nada, asegurese de que haya escrito bien el nombre."
                )
        else:
            await message.reply(
                "❌Debe enviar el comando y luego el nombre de la serie/pelicula, junto a la temporada y/o episodio.❓Ejemplos:\n\n/srt Breaking Bad Season 1\n/srt Breaking Bad S01E01\n/srt Breaking Bad Temporada 2 Episodio 3"
            )
    except OpenSubtitlesException as error:
        logger.error(error)
        await message.reply("❌ Ocurrió un error al buscar subtítulos. Inténtalo de nuevo más tarde.")


@bot.on_message(command("bsrt", prefixes=["/"]) & private)
async def search_subtitles_to_bulk(client: Client, message: Message):
    
    if not await check_user_in_channel(client, message):
                return
            
    await check_user_in_db(message)
    
    try:
        if len(message.command) >= 2:
            
            movie = message.command
            movie.pop(0)

            query = " ".join(movie)

            result = subs(query)
            keyboard = [[InlineKeyboardButton(text=f"🔡{sub.file_name}🔡", callback_data=f"bulk_sub_{sub.file_id}")] for sub in result]
            keyboard.extend([[InlineKeyboardButton(text="Finalizar❌", callback_data="bulk_end")]])
            
            if result is not None and len(result) > 0:
                await message.reply(
                    f"🔥Resultados de la busqueda en modo bulk (Para finalizar esta busqueda presione el boton de Finalizar❌ en lo ultimo de los botones): ||{query}||🔎:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await message.reply(
                    "No se ha encontrado nada, asegurese de que haya escrito bien el nombre."
                )
        else:
            await message.reply(
                "❌Debe enviar el comando y luego el nombre de la serie/pelicula, junto a la temporada y/o episodio.❓Ejemplos:\n\n/srt Breaking Bad Season 1\n/srt Breaking Bad S01E01\n/srt Breaking Bad Temporada 2 Episodio 3"
            )

    except OpenSubtitlesException as error:
        logger.error(error)
        await message.reply("❌ Ocurrió un error al buscar subtítulos. Inténtalo de nuevo más tarde.")