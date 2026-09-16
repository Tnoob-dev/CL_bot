import os
import random

from entry.entry import bot
from utils.db_reqs import get_user, get_posts_by_genre
from utils.functions import create_telegraph_page
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.filters import command, private


@bot.on_message(command("recommend", prefixes=["/"]) & private)
async def recommend(client: Client, message: Message):
    
    user = get_user(
        id=message.from_user.id,
        all_the_users=False
    )
    
    user_genres = user[1].genre_stats
    sorted_genres = sorted(user_genres.items(), key=lambda item: item[1], reverse=True)
    
    if len(sorted_genres) > 0:
        fav_genre = sorted_genres[0][0]
        
        posts = get_posts_by_genre(fav_genre)
        random.shuffle(posts)
        
        html = f"<h3>✨100 Posts sugeridos para ti segun tu género favorito ({fav_genre})🤟</h3><br><br>"
        
        for post in posts[:100]:
            html += f"<a href='{post.link}'>🇺🇸{post.movie_name}🇲🇽</a><br>"
        
        html += f"<br><h3>🦾Gracias por ser parte de <a href='https://t.me/{os.getenv('CINEMA_ID')}'>Cinema Library</a>🍿</h3>"
        
        post4user = [[InlineKeyboardButton(text=f"🇺🇸{post.movie_name}🇲🇽", url=post.link)] for post in posts[:10]]
        
        tgp_page = await create_telegraph_page(
            short_name=message.from_user.id,
            content=html
        )
        
        post4user.extend([
            [
                InlineKeyboardButton(text="❤️", callback_data="nothing"),
                InlineKeyboardButton(text="🍿", callback_data="nothing"),
                InlineKeyboardButton(text="🥱", callback_data="nothing")
            ],
            [
                InlineKeyboardButton(text="Mira mas resultados aqui✨", url=str(tgp_page))
            ]
        ])
        
        await message.reply(
            f"__🎬 ¡Es hora de maratón! 🍿\nDado que te encanta el género **{fav_genre}**, he seleccionado estas 10 joyas audiovisuales que encajan perfecto con tus gustos. ✨\n¡A disfrutar! 🎥__",
            reply_markup=InlineKeyboardMarkup(post4user)
        )
        
    else:
        await message.reply("Aun no ha descargado nada, asi que no se que recomendarle🙈")