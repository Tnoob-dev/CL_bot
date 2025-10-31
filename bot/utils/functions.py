from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant
from typing import List
from pathlib import Path
import os

def check_administration(message: Message) -> bool:
    admins: List[str] = os.getenv("ADMINS").split(",")
    
    if str(message.from_user.id) not in admins:
        return False
    
    return True

async def check_user_in_channel(client: Client, message: Message):
    try:
        await client.get_chat_member(os.getenv("CINEMA_ID"), message.from_user.id)
        await client.get_chat_member(os.getenv("GAME_LIBRARY_ID"), message.from_user.id)
        await client.get_chat_member(os.getenv("EQUINOX_ID"), message.from_user.id)
        return True
    except UserNotParticipant:
        await message.reply_sticker(Path.cwd() / Path("assets") / Path("tongue_out.tgs"))
        await message.reply("Para usar este bot, primero debes unirte a nuestros canales.", 
                            reply_markup=InlineKeyboardMarkup(
                                [
                                    [InlineKeyboardButton("🎬Cinema Library🎬", url="https://t.me/CL_LibraryBK")],
                                    [InlineKeyboardButton("🎮Games Library🎮", url="https://t.me/Game_Library_Pro")],
                                    [InlineKeyboardButton("🌐Equinox🌐", url="https://t.me/TechConnectivityC")]
                                ]
                            ))
        return False
