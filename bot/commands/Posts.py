from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.filters import command, private
from utils.functions import check_administration, check_existence
from pathlib import Path
from ast import literal_eval
import os
import logging

# Logger 
logger = logging.getLogger(__name__)


@bot.on_message(command("post", prefixes=["/"]) & private)
async def create_posts(client: Client, message: Message):
    
    
    if check_administration(message):
        
        post = message.reply_to_message.photo.file_id
        if post is not None:
            m = await message.reply("Descargando imagen, creando post y enviando...")
            pic = await client.download_media(post, file_name="./posts/")
            description = message.reply_to_message.caption
            links = literal_eval(message.text[6:])
            
            await m.edit("Post Enviado")
            
            await client.send_photo(
                chat_id=os.getenv("CINEMA_ID"),
                photo=pic,
                caption=description,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(text=content[0], url=content[1])] for content in links
                    ]
                )
            )
            
    