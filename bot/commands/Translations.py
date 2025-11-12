from entry.entry import bot
from utils.functions import check_user_in_channel
from utils.translate import Translate
from utils.create_paths import create_user_path, create_output_path
from pyrogram.filters import command, private
from pyrogram.client import Client
from pyrogram.types import Message
from pathlib import Path

@bot.on_message(command("tr", prefixes=["/"]) & private)
async def translate_srt(client: Client, message: Message):
    
    global m, file
    
    create_user_path(path=Path.cwd() / Path("bot") / Path("translations") / Path("downloads"), user_id=message.from_user.id)
    create_output_path(user_id=message.from_user.id)
    
    if not await check_user_in_channel(client, message):
        return
    else:
        if message.reply_to_message.document.file_name.endswith(".srt"):
            m = await message.reply("Procesando archivo...")
            file = await message.reply_to_message.download(file_name=f"./bot/translations/downloads/{message.from_user.id}/")
            await m.edit("Archivo descargado, en que idioma lo desea traducir?",
                   reply_markup=Translate.language_keyboard())
        else:
            await message.reply("No ha seleccionado un archivo .srt")

def return_filename():
    return file