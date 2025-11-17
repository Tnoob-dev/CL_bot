from entry.entry import bot
from utils.functions import check_administration, check_user_in_channel
from utils.db_reqs import get_game
from utils.db_reqs import insert_user, get_user
from db.create_cine_db import User
from pyrogram.client import Client
from pyrogram.filters import command, private, text
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from typing import List
from pathlib import Path
import asyncio
import os

# command start, maybe can we think that is something trivial, but is not
@bot.on_message(command("start", prefixes=["/"]) & private & text)
async def hello(client: Client, message: Message):
    
    # at this point we will take 3 vars, user_id, username, and user_founded, that will return a Tuple[bool, class] data type if founds the user via user_id,
    # else this will return a Tuple[bool, None]
    user_id = message.from_user.id
    username = message.from_user.username
    user_founded = get_user(user_id)
    
    # this was to evade troubles, if message.command is None, we will do nothing
    if message.command is not None:
        
        try:
            # see if the command is higher than 2, Ex: /start=randomIDtoGetThings, message.command returns in that case ["start", "randomIDtoGetThings"]
            if len(message.command) >= 2:
                # check if user is not in all required channels, in case he doesn't, return and do nothing, else, keep with the 
                if not await check_user_in_channel(client, message):
                    return
                else:
                    # get file_ids of the files, based on the function get_game
                    file_ids: List[int] = get_game(message.command[1])
                    
                    # iterate through file ids list
                    for id in file_ids:
                        
                        success = False # Flag
                        while not success:
                            
                            try:
                                # if the second argument of message.command ("randomIDtoGetThings") starts with new_ (Ex: "new_randomIDtoGetThings")
                                if message.command[1].startswith("new_"):
                                    await client.copy_message(message.chat.id, os.getenv("SENDER_BOT"), id) # send files from the private chat of the bot
                                else:
                                    await client.copy_message(message.chat.id, os.getenv("CHANNEL_ID"), id) # send files from the backup channel
                                
                                success = True # success becomes True to pass next file
                            
                            except FloodWait as f:
                                await asyncio.sleep(f.value)
                    
                    # send finished sticker
                    await message.reply_sticker(Path.cwd() / Path("assets") / Path("finished.webp"))
            
            else: # and this else, its in case that we only send /start, without arguments
                
                # check if user is admin
                if check_administration(message):

                    await message.reply(f"Hola Administrador: {message.from_user.first_name}")

                else: # in case isn't admin, reply with funny sticker and hello message

                    await message.reply_sticker(Path.cwd() / Path("assets") / Path("dancer.tgs"))
                    await message.reply(f"Hola {message.from_user.mention}, Busca la pelicula en el canal o grupo y toca el enlace para obtenerlo aqui")
            
            if not user_founded[0]: # if the user is not in db, add it
                print(f"Insertando usuario {username} ({user_id}) a la db")
                user = User(id=user_id, username=username)
                insert_user(user)
                print(f"Usuario {username} añadido a la db")
        except (TypeError, ValueError) as e:
            print(e)