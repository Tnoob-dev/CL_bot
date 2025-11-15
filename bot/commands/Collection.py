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

state = {}

@bot.on_message(command("add") & private)
async def start_collection(client: Client, message: Message):
    
    user_id = message.from_user.id

    if check_administration(message):
        if not str(user_id) in state:
            state[str(user_id)] = {
                "collecting": True,
                "messages": []
            }
            
            await message.reply("Esperando mensajes...\n Al terminar envie /end para crear el post")
        else:
            await message.reply("Usted ya se encuentra actualmente coleccionando archivos")
            
                
@bot.on_message(command("end") & private)
async def end_collection(client: Client, message: Message):
    
    try:
        if check_administration(message):
            if not str(message.from_user.id) in state:
                await message.reply("Usted no se encuentra en el modo coleccion")
            
            else:
                messages = state[str(message.from_user.id)]["messages"]    
                
                for message_id in messages:
                    success = False
                    
                    while not success:
                        try:
                            await client.copy_message(chat_id=os.getenv("CHANNEL_ID"), from_chat_id=os.getenv("SENDER_BOT"), message_id=message_id)
                            success = True
                        except FloodWait as f:
                            await asyncio.sleep(f.value)
                            
                if len(state[str(message.from_user.id)]["messages"]) > 0:
                    await message.reply("Mensaje(s) enviados al chat de backup")
                
                insert(
                    Game(name="new_" + str(messages[-1]), file_ids=messages)
                )
                
                await message.reply(f"Ha salido del modo coleccion, para iniciar una nueva coleccion escriba el comando /add\n\nSu enlace es https://t.me/{os.getenv("SENDER_BOT")}?start=new_{messages[-1]}")
                await message.reply_document(document=Path.cwd() / Path("bot") / Path("core") / "cine.db")
                
                del state[str(message.from_user.id)]
    except IndexError:
        await message.reply("Ha enviado un tipo de archivo no valido, intentelo de nuevo")
        return
                
@bot.on_message(private & document | video | photo & user)
async def collect_messages(client: Client, message: Message):
    
    if check_administration(message):
        if str(message.from_user.id) in state:
            state[str(message.from_user.id)]["messages"].append(message.id)
