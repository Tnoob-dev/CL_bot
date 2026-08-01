import logging

from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, group, private, text
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.functions import check_administration
from utils.movie_search import get_results

logger = logging.getLogger(__name__)


@bot.on_message(command("info") & (private | group) & text)
async def info_posts(client: Client, message: Message):

    try:
        if check_administration(message) and message.command is not None and len(message.command) >= 2:
            m = await message.reply("Buscando contenido audiovisual🔎🎬")
            movie = message.command
            movie.pop(0)

            query = " ".join(movie)

            results = await get_results(query)

            if len(results) >= 1:
                await m.delete()

                await message.reply(
                    "Se han encontrado los siguientes 5 resultados⬇️",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text=f"{info.get('primaryTitle')} - {info.get('startYear')}",
                                    callback_data=f"info_{info.get('id')}",
                                )
                            ]
                            for info in results
                        ]
                    ),
                )
            else:
                await message.reply("Nada encontrado")

    except (AttributeError, Exception) as e:
        logger.error(e)
