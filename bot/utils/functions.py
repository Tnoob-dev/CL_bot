from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant, FloodWait
from typing import List, Dict
from pathlib import Path
import os
import asyncio
import json
import logging

# Logger 
logger = logging.getLogger(__name__)

# check if a path or file exists
def check_existence(path: Path):
    return False if not path.exists() else True

# check if a user is admin
def check_administration(message: Message) -> bool:
    admins: List[str] = os.getenv("ADMINS").split(",")
    
    if str(message.from_user.id) not in admins:
        return False
    
    return True

# check if a user is in the channel
async def check_user_in_channel(client: Client, message: Message) -> bool:
    
    if not message.from_user:
        return False
    
    try:
        await client.get_chat_member(chat_id=os.getenv("CINEMA_ID"), user_id=message.from_user.id)
        await client.get_chat_member(chat_id=os.getenv("ANIME_ID"), user_id=message.from_user.id)
        # await client.get_chat_member(chat_id=os.getenv("GAME_LIBRARY_ID"), user_id=message.from_user.id)
        # await client.get_chat_member(chat_id=os.getenv("EQUINOX_ID"), user_id=message.from_user.id)
        
        return True
    except UserNotParticipant:
        await message.reply_sticker(Path.cwd() / Path("assets") / Path("tongue_out.tgs"))
        await message.reply("Para usar este bot, primero debes unirte a nuestros canales.", 
                            reply_markup=InlineKeyboardMarkup(
                                [
                                    [InlineKeyboardButton("🎬Cinema Library🎬", url=f"https://t.me/{os.getenv("CINEMA_ID")}")],
                                    [InlineKeyboardButton("🇯🇵Anime Library🇯🇵", url=f"https://t.me/{os.getenv("ANIME_ID")}")],
                                    [InlineKeyboardButton("♻️Intentar de nuevo", url=f"https://t.me/{os.getenv("SENDER_BOT")}?{'='.join(message.command) if len(message.command) == 2 else "start"}")]
                                ]
                            ))
        return False
    except Exception as e:
        logger.error(f"Error inesperado en check_user_in_channel: {e}")
        return False

async def forward_messages(client: Client, messages: List[int]):
    # for loop into messaages to send all the file to backup channel
    for message_id in messages:
        success = False # Flag: if True, means file sent to backup channel succesfully
        
        # while loop...
        while not success:
            try:
                
                # forwarding
                await client.copy_message(chat_id=os.getenv("CHANNEL_ID"), from_chat_id=os.getenv("SENDER_BOT"), message_id=message_id)
                success = True # change flag to True and go for the next file
                
            except FloodWait as f: # if exists flood sleep bot the time estimated
                
                await asyncio.sleep(f.value)
                
def save_to_json(subtitles: List[Dict[str, int | str]], user_id: int, output_file: str):
    try:
        
        with open(f"./bot/translations/downloads/{user_id}/{output_file}", 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=2)
            
    except Exception as error:
        logger.error(f"Error guardando el json -> {error}")
        
def clear_path(path: str) -> None:
    
    if os.path.exists(path):
        files = os.listdir(path)
        
        if len(files) > 0:
            for file in files:
                os.remove(path + file)

def get_clicked_button_text(query: CallbackQuery):
    key = query.data
    
    for markup in query.message.reply_markup.inline_keyboard:
        if markup[0].callback_data == key:
            return markup[0].text