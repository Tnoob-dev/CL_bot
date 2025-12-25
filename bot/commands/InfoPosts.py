from entry.entry import bot
from utils.functions import check_user_in_channel, download_image, translate_synopsis, translate_title
from utils.db_reqs import get_user, insert_user
from utils.movie_search import get_results
from db.create_cine_db import User
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.errors.exceptions import WebpageMediaEmpty
from pyrogram.filters import command, private, group, text
import logging
import os

logger = logging.getLogger(__name__)

@bot.on_message(command("info") & private | group & text)
async def info_posts(client: Client, message: Message):
    
    if message.from_user is not None:
        user_founded = get_user(message.from_user.id)[0]
    
    try:
        if not await check_user_in_channel(client, message):
            return
        
        if not user_founded:
            await message.reply("Al parecer usted no habia entrado a la DB, ya se encuentra dentro, disfrute")
            username = message.from_user.username if message.from_user.username is not None else ""
            user = User(id=message.from_user.id, username=username)
            insert_user(user)
        
        if message.command is not None:
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
                            template += f"🎬 {title} | {title_translated} 🎬\n"
                            template += f"🗓 Año: {year}\n"
                            template += f"⭐️Rating: {rating['aggregateRating'] if rating is not None else '-'}\n"
                            template += f"⏱️ Duración: {duration} minutos\n"
                            template += f"📚 Género: {genres}\n"
                            template += f"📌 Sinopsis: {synopsis}\n"
                        else:
                            template += f"🎭 {title} | {title_translated} 🎭\n"
                            template += f"🗓 Año: {year}\n"
                            template += f"⭐️Rating: {rating["aggregateRating"]}\n"
                            template += f"⏱️ Duración: {duration} minutos por episodio\n"
                            template += f"🎨 Géneros: {genres}\n"
                            template += f"📖 Sinopsis: {synopsis}\n"
                            
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