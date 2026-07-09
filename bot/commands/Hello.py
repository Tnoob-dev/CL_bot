from entry.entry import bot
from utils.functions import check_administration, check_user_in_channel, delete_after_delay
from utils.db_reqs import get_game
from utils.db_reqs import insert_user, get_user, update_user_downloads
from db.create_cine_db import Users
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
    if message.command is not None and len(message.command) == 1:
        if check_administration(message):
            await message.reply(f"Hola Administrador: {message.from_user.first_name}")
        else:
            await message.reply_sticker(Path.cwd() / Path("assets") / Path("dancer.tgs"))
            await message.reply(f"Hola {message.from_user.mention}, gracias por usar nuestro bot, nos complace tenerte como usuario, para tener una guia mas detallada de como funciona el bot, utiliza el comando /help.\n\nNos encantaria conocerte, asi que por que no entras a nuestro chat del canal: @chat1080p, donde tambien...shhh...spoiler: ||Podras pedir esa serie o peli que llevas dias buscando|| (Que no se te olvide poner #cine <nombre> y una foto para nosotros saber cual es).")
        return

    if message.from_user is not None:
        user_id = message.from_user.id
        username = message.from_user.username if message.from_user.username is not None else None
        user_founded = get_user(user_id)
        if not user_founded[0]:  # if the user is not in db, add it
            logger.info(f"Insertando usuario {username} ({user_id}) a la db")
            user = Users(id=user_id, username=username, rest_tries=10, is_admin=False, premium_user=False)
            insert_user(user)
            logger.info(f"Usuario {username} añadido a la db")

    if not await check_user_in_channel(client, message):
        return

    if message.command is not None and message.command[0] == "start":
        try:
            if len(message.command) >= 2:
                file_ids: List[int] = get_game(message.command[1])
                for id in file_ids:
                    success = False  # Flag
                    while not success:
                        try:
                            sent_message = await client.copy_message(message.chat.id, int(os.getenv("CHANNEL_ID")), id)  # send files from the backup channel

                            success = True  # success becomes True to reach next file

                            asyncio.create_task(
                                delete_after_delay(client, message.chat.id, sent_message.id, 180)
                            )
                        except FloodWait as f:
                            await asyncio.sleep(f.value)

                await message.reply("Esto tendra una duracion de 3 minutos contados a partir del envio del mensaje.\n\nReenvie a sus mensajes guardados para no perderlo")
                await message.reply_sticker(Path.cwd() / Path("assets") / Path("finished.webp"))
                donation_message = """
💖 ¿Te gusta el contenido del canal?

Si este espacio te aporta valor y quieres apoyar el trabajo del administrador, 
puedes hacer una donación voluntaria. 
Cada aporte ayuda a mantener el canal activo y mejorar la calidad del contenido.

🔗 Usa el comando /donate

¡Gracias por ser parte de esta comunidad! 🙌"""
                await message.reply(donation_message)

                # add 1 more download to user total downloads
                update_user_downloads(user_id)
        except (TypeError, ValueError) as e:
            logger.error(e)