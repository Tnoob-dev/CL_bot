from entry.entry import bot
from utils.functions import check_administration
from utils.movie_search import get_results
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions import WebpageMediaEmpty
from pyrogram.filters import command, private, group, text
import logging
import os

logger = logging.getLogger(__name__)

@bot.on_message(command("info") & (private | group) & text)
async def info_posts(client: Client, message: Message):

    try:
        if check_administration(message) and message.command is not None:
            if len(message.command) >= 2:
                m = await message.reply("Buscando contenido audiovisual🔎🎬")
                movie = message.command
                movie.pop(0)

                query = ' '.join(movie)

                template = ""

                results = await get_results(query)

                if len(results) >= 1:
                    await m.delete()

                    await message.reply("Se han encontrado los siguientes 5 resultados⬇️",
                                        reply_markup=InlineKeyboardMarkup(
                                            [
                                                [InlineKeyboardButton(
                                                    text=f"{info.get("primaryTitle")} - {info.get("startYear")}", 
                                                    callback_data=f"info_{info.get("id")}")]

                                                for info in results
                                            ]
                                        ))
                else:
                    await message.reply("Nada encontrado")

    except (AttributeError, Exception) as e:
        logger.error(e)
