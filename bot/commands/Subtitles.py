import logging

from db.create_cine_db import Users
from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, private
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.db_reqs import get_user, insert_user
from utils.functions import check_user_in_channel

# Logger
logger = logging.getLogger(__name__)

class SrtUser:
    def __init__(self):
        self.user_srt = {}

srt_state = SrtUser()

@bot.on_message(command(["srt", "bsrt"], prefixes=["/"]) & private)
async def search_subtitles(client: Client, message: Message):

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
        
    if not await check_user_in_channel(client, message):
        return


    if len(message.command) > 2:
        movie = message.command
        movie.pop(0)

        query = " ".join(movie)
        
        srt_state.user_srt[str(message.from_user.id)] = query
        
        spanish_cbdata = "srt_es" if message.command[0] == "srt" else "bsrt_es"
        english_cbdata = "srt_en" if message.command[0] == "srt" else "bsrt_en"
        arabic_cbdata = "srt_ar" if message.command[0] == "srt" else "bsrt_ar"
        
        await message.reply(
            text="Seleccione un idioma para continuar:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text="🇪🇸Español", callback_data=spanish_cbdata), InlineKeyboardButton(text="🇺🇸English", callback_data=english_cbdata)],
                    [InlineKeyboardButton(text="عربي🇸🇦", callback_data=arabic_cbdata)]
                ]
            ))