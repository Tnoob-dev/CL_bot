from utils.functions import check_administration
from utils.db_reqs import get_user
from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
import asyncio
import logging
import os

# Logger
logger = logging.getLogger(__name__)

@bot.on_message(command("advise") & private)
async def send_admin_message(client: Client, message: Message):

    try:
        owner_id = os.getenv("OWNER_ID")
        if message.from_user.id == int(owner_id):
            users = get_user(all_the_users=True)
            quantity_users = len(users)
            await message.reply("Enviando mensaje a usuarios")
            blocked_users = 0
            for user in users: # bot id
                if user.id != 8161420181 or user.id != 715727671:
                    success = False # Flag
                    while not success:
                        try:
                            await client.copy_message(user.id, message.chat.id, message.reply_to_message.id)
                            success = True
                        except FloodWait as f:
                            asyncio.sleep(f.value)
                        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid) as e:
                            logger.info(f"No se puede enviar a {user.id}: {e}")
                            blocked_users += 1
                            success = True

            await message.reply(f"--Summary--:\n\n👥Total de usuarios registrados: {quantity_users}\n✅Cantidad de usuarios a los que se le envio el mensaje: {quantity_users - blocked_users}\n🚫Cantidad de usuarios que tienen bloqueado al bot: {blocked_users}")
        else:
            await message.reply("❌No tiene permisos para usar este comando❌")

    except Exception as error:
        logger.error(error)

@bot.on_message(command("count"))
async def count_users(client: Client, message: Message):

    users = get_user(all_the_users=True)
    await client.send_message(message.chat.id, f"Actualmente tengo registrados a {len(users)} usuarios")

@bot.on_message(command("send_db", prefixes=["/"]) & (private))
async def send_db(client: Client, message: Message):

    if check_administration(message):

        db_path = "./bot/core/users.db"

        await message.reply_document(db_path)
