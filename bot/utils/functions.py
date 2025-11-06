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

async def check_user_in_channel(client: Client, message: Message) -> bool:
    
    if not message.from_user:
        return False
    
    try:
        await client.get_chat_member(chat_id=os.getenv("CINEMA_ID"), user_id=message.from_user.id)
        await client.get_chat_member(chat_id=os.getenv("GAME_LIBRARY_ID"), user_id=message.from_user.id)
        await client.get_chat_member(chat_id=os.getenv("EQUINOX_ID"), user_id=message.from_user.id)
        
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
    except Exception as e:
        print(f"Error inesperado en check_user_in_channel: {e}")
        return False
