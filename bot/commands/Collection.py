from entry.entry import bot
from utils.functions import check_administration, forward_messages
from utils.db_reqs import insert
from db.create_cine_db import Game
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private, document, video, photo
from pathlib import Path
from typing import List
import os

# state for saving messages of files and other data
state = {}

# massive command, to add a lot of files, in only one command, instead of multiple /add commands
@bot.on_message(command("massive") & private)
async def massive_collection(client: Client, message: Message):
    user_id = message.from_user.id
    
    if check_administration(message):
        if not str(user_id) in state:
            state[str(user_id)] = {
                "collecting": True,
                "massive_mode": True,
                "messages": [],
                "links": []
            }
            
            await message.reply("Modo masivo activado, envie /end para determinar por temporadas, y envie /end_massive para terminar el modo masivo")


# end_massive command, to end the complete task
@bot.on_message(command("end_massive") & private)
async def end_massive(client: Client, message: Message):
    if check_administration(message):
        user_id = message.from_user.id
        links = state[str(user_id)]["links"] # get links from the user state dict
        unlinked_urls = '\n'.join(links) # put one down another
        
        await message.reply(f"Aqui tiene todos los enlaces:\n{unlinked_urls}")
        await message.reply_document(document=Path.cwd() / Path("bot") / Path("core") / "cine.db")
        
        # delete user from memory
        del state[str(user_id)] 
    else:
        await message.reply("No tiene permisos para utilizar este comando")
        

# add command, for start adding messages id to state var
@bot.on_message(command("add") & private)
async def start_collection(client: Client, message: Message):
    
    user_id = message.from_user.id

    # check if user is admin
    if check_administration(message):
        if not str(user_id) in state: # if the user is not in state, add it with all the followings schemas
            state[str(user_id)] = {
                "collecting": True,
                "massive_mode": False,
                "messages": []
            }
            
            await message.reply("Esperando mensajes...\n Al terminar envie /end para crear el post")
        else:
            await message.reply("Usted ya se encuentra actualmente coleccionando archivos")
            

# end command, finish command add, and forward all the messages to the backup channel
@bot.on_message(command("end") & private)
async def end_collection(client: Client, message: Message):
    user_id = message.from_user.id
    try:
        if check_administration(message): # check if user is admin
             
            if not str(user_id) in state: # if the user id is not in state, means that the user never used the command add
                await message.reply("Usted no se encuentra en el modo coleccion")
            else:
                if state[str(user_id)]["massive_mode"]:
                    messages: List[int] = state[str(user_id)]["messages"]
                    
                    await forward_messages(client, messages) # forward messages to backup channel
                    
                    # Once all the files has been forwarded, insert code to DB
                    insert(Game(name="new_" + str(messages[-1]), file_ids=messages))
                    
                    # append links of files, to the "links" schema in the user dict
                    state[str(user_id)]["links"].append(f"https://t.me/{os.getenv("SENDER_BOT")}?start=new_{messages[-1]}")
                    
                    # clear list for receive new messages
                    messages.clear()
                    
                    await message.reply("Mensajes reenviados, envie la siguiente temporada, o envie /end_massive")
                else:
                    messages = state[str(user_id)]["messages"] # get all the messages that the user collected
                    
                    await forward_messages(client, messages) # forward messages to backup channel
                                
                    if len(state[str(user_id)]["messages"]) > 0:
                        await message.reply("Mensaje(s) enviados al chat de backup")
                    
                    # Once all the files has been forwarded, insert code to DB
                    insert(Game(name="new_" + str(messages[-1]), file_ids=messages))
                    
                    
                    await message.reply(f"Ha salido del modo coleccion, para iniciar una nueva coleccion escriba el comando /add\n\nSu enlace es https://t.me/{os.getenv("SENDER_BOT")}?start=new_{messages[-1]}")
                    await message.reply_document(document=Path.cwd() / Path("bot") / Path("core") / "cine.db")
                    
                    # delete user from memory
                    del state[str(user_id)]
    except IndexError:
        # if is not a document, video or photo, isn't a valid file
        await message.reply("Ha enviado un tipo de archivo no valido, intentelo de nuevo")
        return

# without commands, append messages id to user state message schema
# this will only wait for a document, video or photo
@bot.on_message(private & document | video | photo)
async def collect_messages(client: Client, message: Message):
    user_id = message.from_user.id
    # check user is admin
    if check_administration(message):
        if str(user_id) in state: # if user id is in state, means its in collection mode
            state[str(user_id)]["messages"].append(message.id) # just append to that schema