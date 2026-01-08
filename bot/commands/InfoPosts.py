from entry.entry import bot
from utils.functions import check_administration, download_image, translate_synopsis, translate_title
from utils.movie_search import get_results
from pyrogram.client import Client
from pyrogram.types import Message
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
                    for info in results:
                        kind = "movie" if info["type"].lower() == "movie" or info["type"].lower() == "tvmovie" else "serie"

                        title = info.get("primaryTitle")
                        title_translated = await translate_title(title)
                        year = info.get("startYear")
                        rating = info.get("rating")
                        time_in_seconds = info.get("runtimeSeconds")
                        duration = int(time_in_seconds / 60) if time_in_seconds is not None else "-"
                        genres = ', '.join(info.get("genres"))
                        plot = info.get("plot")
                        synopsis = await translate_synopsis(plot) if plot is not None else ""
                        image = info.get("primaryImage")

                        if kind == "movie":
                            template += f"🎬 {title} | {title_translated if title_translated is not None else title} 🎬\n"
                            template += f"🗓 Año: {year}\n"
                            template += f"⭐️Rating: {rating['aggregateRating'] if rating is not None else '-'}\n"
                            template += f"⏱️ Duración: {duration} minutos\n"
                            template += f"📚 Género: {genres}\n"
                            template += f"📌 Sinopsis: {synopsis if synopsis is not None else plot}\n"
                        else:
                            template += f"🎭 {title} | {title_translated if title_translated is not None else title} 🎭\n"
                            template += f"🗓 Año: {year}\n"
                            template += f"⭐️Rating: {rating["aggregateRating"]}\n"
                            template += f"⏱️ Duración: {duration} minutos por episodio\n"
                            template += f"🎨 Géneros: {genres}\n"
                            template += f"📖 Sinopsis: {synopsis if synopsis is not None else plot}\n"

                        if image:
                            try:
                                await message.reply_photo(image["url"], caption=template)
                            except WebpageMediaEmpty:
                                path = download_image(image["url"])
                                await message.reply_document(path, caption=template)
                                os.remove(path)
                        else:
                            await message.reply(template)

                        template = ""
                    await message.reply("Estos fueron los resultados que encontre☝️")
                else:
                    await message.reply("Nada encontrado")

    except (AttributeError, Exception) as e:
        logger.error(e)
