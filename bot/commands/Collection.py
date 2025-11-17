from entry.entry import bot
from utils.functions import check_administration
from utils.db_reqs import insert
from db.create_cine_db import Game
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private, document, video, photo, user
from pyrogram.errors import FloodWait
from pathlib import Path
import asyncio
import os

# state for saving messages of files
state = {}

# add command, for start adding messages id to state var
@bot.on_message(command("add") & private)
async def start_collection(client: Client, message: Message):
    
    user_id = message.from_user.id

    # check if user is admin
    if check_administration(message):
        if not str(user_id) in state: # if the user is not in state, add it with all the followings schemas
            state[str(user_id)] = {
                "collecting": True,
                "messages": []
            }
            
            await message.reply("Esperando mensajes...\n Al terminar envie /end para crear el post")
        else:
            await message.reply("Usted ya se encuentra actualmente coleccionando archivos")
            

# end command, finish command add, and forward all the messages to the backup channel
@bot.on_message(command("end") & private)
async def end_collection(client: Client, message: Message):
    
    try:
        if check_administration(message): # check if user is admin
             
            if not str(message.from_user.id) in state: # if the user id is not in state, means that the user never used the command add
                await message.reply("Usted no se encuentra en el modo coleccion")
            else:
                messages = state[str(message.from_user.id)]["messages"] # get all the messages that the user collected
                
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
                            
                if len(state[str(message.from_user.id)]["messages"]) > 0:
                    await message.reply("Mensaje(s) enviados al chat de backup")
                
                # Once all the files has been forwarded, insert code to DB
                insert(Game(name="new_" + str(messages[-1]), file_ids=messages))
                
                
                await message.reply(f"Ha salido del modo coleccion, para iniciar una nueva coleccion escriba el comando /add\n\nSu enlace es https://t.me/{os.getenv("SENDER_BOT")}?start=new_{messages[-1]}")
                await message.reply_document(document=Path.cwd() / Path("bot") / Path("core") / "cine.db")
                
                # delete user from memory
                del state[str(message.from_user.id)]
    except IndexError:
        # if is not a document, video or photo, isn't a valid file
        await message.reply("Ha enviado un tipo de archivo no valido, intentelo de nuevo")
        return

# without commands, append messages id to user state message schema
# this will only wait for a document, video or photo
@bot.on_message(private & document | video | photo)
async def collect_messages(client: Client, message: Message):
    
    # check user is admin
    if check_administration(message):
        if str(message.from_user.id) in state: # if user id is in state, means its in collection mode
            state[str(message.from_user.id)]["messages"].append(message.id) # just append to that schema