from entry.entry import bot
from utils.functions import check_administration, check_user_in_channel
from utils.db_reqs import get_game
from utils.db_reqs import insert_user, get_user
from db.create_cine_db import User
from pyrogram.client import Client
from pyrogram.filters import command, private
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from typing import List
from pathlib import Path
import asyncio
import os
import logging

# Logger
logger = logging.getLogger(__name__)

@bot.on_message(command("start", prefixes=["/"]) & private)
async def hello(client: Client, message: Message):

    if not await check_user_in_channel(client, message):
        return

    if message.command is not None and message.command[0] == "start":
        # at this point we will take 3 vars, user_id, username, and user_founded, that will return a Tuple[bool, class] data type if founds the user via user_id,
        # else this will return a Tuple[bool, None]
        user_id = message.from_user.id
        username = message.from_user.username if message.from_user.username is not None else ""
        user_founded = get_user(user_id)
        try:
            if len(message.command) >= 2:

                file_ids: List[int] = get_game(message.command[1])

                for id in file_ids:

                    success = False # Flag
                    while not success:

                        try:
                            # second argument of message.command ("randomIDtoGetThings") starts with new_ (Ex: "new_randomIDtoGetThings")
                            if message.command[1].startswith("new_"):
                                await client.copy_message(message.chat.id, os.getenv("SENDER_BOT"), id) # send files from the private chat of the bot
                            else:
                                await client.copy_message(message.chat.id, int(os.getenv("CHANNEL_ID")), id) # send files from the backup channel

                            success = True # success becomes True to reach next file

                        except FloodWait as f:
                            await asyncio.sleep(f.value)

                await message.reply_sticker(Path.cwd() / Path("assets") / Path("finished.webp"))

            else: # and this else, its in case that we only send /start, without arguments

                if check_administration(message):

                    await message.reply(f"Hola Administrador: {message.from_user.first_name}")

                else:
                    await message.reply_sticker(Path.cwd() / Path("assets") / Path("dancer.tgs"))
                    await message.reply(f"Hola {message.from_user.mention}, gracias por usar nuestro bot, nos complace tenerte como usuario, para tener una guia mas detallada de como funciona el bot, utiliza el comando /help.\n\nNos encantaria conocerte, asi que por que no entras a nuestro chat del canal: @chat1080p, donde tambien...shhh...spoiler: ||Podras pedir esa serie o peli que llevas dias buscando|| (Que no se te olvide poner #cine <nombre> y una foto para nosotros saber cual es).")

            if not user_founded[0]: # if the user is not in db, add it
                logger.info(f"Insertando usuario {username} ({user_id}) a la db")
                user = User(id=user_id, username=username)
                insert_user(user)
                logger.info(f"Usuario {username} añadido a la db")
        except (TypeError, ValueError) as e:
            logger.error(e)
