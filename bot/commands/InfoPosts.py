import logging

from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, group, private, text
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.functions import check_administration
from utils.movie_search import get_results, search_tmdb

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
                                    callback_data=f"info_imdb_{info.get('id')}",
                                )
                            ]
                            for info in results
                        ]
                    ),
                )
            else:
                # try the search in tmdb
                
                results = await search_tmdb(query)
                                            
                if len(results) >= 1:
                    
                    keyboard: list[InlineKeyboardButton] = []
                    
                    for info in results:
                        info: dict
                        if info.get("title") is not None or info.get("name") is not None:
                            
                            mediaId = info.get('id')
                            title = info.get('title') if info.get('title') is not None else info.get('name')
                            date = info.get('release_date').split("-")[0] if info.get('release_date') is not None else info.get('first_air_date').split("-")[0]
                            kind = "movie" if info.get('media_type').lower() == "movie" else "serie"
                            
                            keyboard.append(
                                [InlineKeyboardButton(
                                text=f"{title} - {date}",
                                callback_data=f"info_{kind}_{mediaId}"
                            )]
                                )
                    
                    
                    await m.delete()
                    await message.reply(
                        "IMDB no esta funcionando, asi que busque por TMDB.\n\nSe han encontrado los siguientes resultados⬇️",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    
                else:
                
                    await message.reply("Nada encontrado")

    except (AttributeError, Exception) as e:
        logger.error(e)
