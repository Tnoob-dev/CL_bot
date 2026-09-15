import os

from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, private
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.db_reqs import get_user
from utils.functions import download_tg_files, get_profile_info


@bot.on_message(command("profile", prefixes=["/"]) & private)
async def profile_panel(client: Client, message: Message):

    profile = await get_profile_info(client, message.from_user.id)
    _, db_info = get_user(message.from_user.id, all_the_users=False)
    pic_path = await download_tg_files(
        client, profile.photo.big_file_id, profile.username
    )
    
    three_mostDl_genres = sorted(db_info.genre_stats.items(), key=lambda item: item[1], reverse=True)
    string = "Sin géneros"
    
    if len(three_mostDl_genres) > 0:
        three_mostDl_genres = three_mostDl_genres[:3]
        
        medals = ['🥇', '🥈', '🥉']
        
        string = ""
        
        for three, med in zip(three_mostDl_genres, medals):
            
            string += f"**{med} {three[0]}: {three[1]}**\n"
            
        
    text = f"""
🆔 {profile.id}
📝 {profile.mention}
#️⃣ Cantidad de descargas: {db_info.int_downloaded}
😎 Géneros favoritos:

{string}
🪪 {"Es admin" if db_info.is_admin else "No es admin"}
{"💎 Es VIP" if db_info.premium_user else "👤 Usuario normal"}
"""

    buttons = [
        [
            InlineKeyboardButton(
                text="🚀🎬Cinema Library", url=f"https://t.me/{os.getenv('CINEMA_ID')}"
            )
        ]
    ]

    if not db_info.premium_user:
        buttons.append(
            [InlineKeyboardButton("💎Vuelvete VIP ahora", callback_data="become_vip")]
        )

        buttons[-1], buttons[0] = buttons[0], buttons[-1]

    await message.reply_photo(
        photo=pic_path, caption=text, reply_markup=InlineKeyboardMarkup(buttons)
    )

    os.remove(pic_path)
