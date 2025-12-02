from entry.entry import bot
from utils.functions import check_user_in_channel
from utils.users_translate import Translate
from utils.create_paths import create_user_path, create_output_path
from utils.db_reqs import insert_user, get_user
from db.create_cine_db import User
from pyrogram.filters import command, private
from pyrogram.client import Client
from pyrogram.types import Message
from pathlib import Path

@bot.on_message(command("tr", prefixes=["/"]) & private)
async def translate_srt(client: Client, message: Message):
    
    global file
    
    # path creations
    create_user_path(path=Path.cwd() / Path("bot") / Path("translations") / Path("downloads"), user_id=message.from_user.id)
    create_output_path(user_id=message.from_user.id)
    
    # find the user in db
    user_founded = get_user(message.from_user.id)[0]
    
    # check if the user is in the channel
    if not await check_user_in_channel(client, message):
        return
    else:
        # if user_founded returns None, means user is not in db, so we add it
        if not user_founded:
            await message.reply("Al parecer usted no habia entrado a la DB, ya se encuentra dentro, disfrute")
            
            username = message.from_user.username if message.from_user.username is not None else ""
            
            user = User(id=message.from_user.id, username=username)
            insert_user(user)
        
        # this will return None if the user doesnt reply to a file message
        if message.reply_to_message is not None:
            # after the user replies to a file, we check that the file extension is .srt
            if message.reply_to_message.document.file_name.endswith(".srt"):
                m = await message.reply("Procesando archivo...")
                # download file
                file = await message.reply_to_message.download(file_name=f"./bot/translations/downloads/{message.from_user.id}/")
                # display languages (Spanish and English)
                await m.edit("Archivo descargado, en que idioma lo desea traducir?",
                    reply_markup=Translate.language_keyboard())
            else:
                await message.reply("No ha seleccionado un archivo .srt")

def return_filename() -> str:
    return file.split("/")[-1]