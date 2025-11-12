from entry.entry import bot
from utils.functions import check_administration, check_user_in_channel
from utils.db_reqs import get_game
from pyrogram.client import Client
from pyrogram.filters import command, private, text
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from typing import List
from pathlib import Path
import asyncio
import os

@bot.on_message(command("start", prefixes=["/"]) & private & text)
async def hello(client: Client, message: Message):
    
    if message.command is not None:
        try:
            if len(message.command) >= 2:
                if not await check_user_in_channel(client, message):
                    return
                else:
                    file_ids: List[int] = get_game(message.command[1])

                    for id in file_ids:
                        
                        success = False
                        while not success:
                            
                            try:
                            
                                if message.command[1].startswith("new_"):
                                    await client.copy_message(message.chat.id, os.getenv("SENDER_BOT"), id)
                                else:
                                    await client.copy_message(message.chat.id, os.getenv("CHANNEL_ID"), id)
                                success = True
                            
                            except FloodWait as f:
                                await asyncio.sleep(f.value)
                                
                    await message.reply_sticker(Path.cwd() / Path("assets") / Path("finished.webp"))
            else:
                
                if check_administration(message):
                    await message.reply(f"Hola Administrador: {message.from_user.first_name}")
                else:
                    await message.reply_sticker(Path.cwd() / Path("assets") / Path("dancer.tgs"))
                    await message.reply(f"Hola {message.from_user.mention}, Busca la pelicula en el canal o grupo y toca el enlace para obtenerlo aqui")
        
        except (TypeError, ValueError) as e:
            print(e)