from entry.entry import bot
from utils.search_subts import subs
from utils.db_reqs import get_user, insert_user
from utils.functions import check_user_in_channel
from db.create_cine_db import User
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.filters import command, private
import logging

# Logger 
logger = logging.getLogger(__name__)


@bot.on_message(command("srt", prefixes=["/"]) & private)
async def search_subtitles(client: Client, message: Message):
    
    user_founded = get_user(message.from_user.id)[0]
    
    try:
        if not await check_user_in_channel(client, message):
            return
        else:
            if not user_founded:
                await message.reply("Al parecer usted no habia entrado a la DB, ya se encuentra dentro, disfrute")
                username = message.from_user.username if message.from_user.username is not None else ""
                user = User(id=message.from_user.id, username=username)
                insert_user(user)
                
            if len(message.command) >= 2:
                movie = message.command
                movie.pop(0)
                
                query = ' '.join(movie)
                
                result = subs(query)
                
                if result is not None and len(result) > 0:
                    await message.reply(f"🔥Resultados de la busqueda ||{query}||🔎:",
                                        reply_markup=InlineKeyboardMarkup(
                                            [
                                                [InlineKeyboardButton(text=f"🔡{sub.file_name}🔡", callback_data=f"sub_{sub.file_id}")] for sub in result
                                            ]
                                        ))
                else:
                    await message.reply("No se ha encontrado nada, asegurese de que haya escrito bien el nombre.")
            else:
                await message.reply("❌Debe enviar el comando y luego el nombre de la serie/pelicula, junto a la temporada y/o episodio.❓Ejemplos:\n\n/srt Breaking Bad Season 1\n/srt Breaking Bad S01E01\n/srt Breaking Bad Temporada 2 Episodio 3")
    except Exception as error:
        await message.reply(error)