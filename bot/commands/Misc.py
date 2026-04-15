from utils.db_reqs import get_user, update_user_admin
from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private, group
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
            
            # TitiLM10, Nyan, bot, moskitosantana
            not_send = [957370219, 1891819663, 8161420181, 715727671]
            
            for user in users:
                if user.id not in not_send:
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

@bot.on_message(command("admin") & private)
async def ascend_to_admin(client: Client, message: Message):
    
    user_command = message.command
    user_id = message.from_user.id
    owner_id = os.getenv("OWNER_ID")
    
    try:
        if user_id == int(owner_id):
            if len(user_command) >= 2:
                boolean, msg = update_user_admin(user_command[-1])
                
                if boolean:
                    logger.info(msg)
                    await message.reply(f"✅{msg}✅")
                else:
                    logger.error(msg)
                    await message.reply(f"❌{msg}❌")
    except Exception as e:
        logger.error(e)
        await message.reply(f"❌Error de excepcion: {e}❌")
        
@bot.on_message(command("count"))
async def count_users(client: Client, message: Message):

    users = get_user(all_the_users=True)
    await client.send_message(message.chat.id, f"Actualmente tengo registrados a {len(users)} usuarios")

@bot.on_message(command("top10") & (private | group))
async def get_top10(client: Client, message: Message):
    
    bot_username = os.getenv("SENDER_BOT")
    users = get_user(all_the_users=True)
    
    sorted_users = sorted(users, key=lambda u: u.int_downloaded, reverse=True)
    
    emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", 
              "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    top10 = sorted_users[:10]
    
    template = f"🦾TOP 10 Usuarios de @{bot_username}🤖\n"
    
    for i in range(10):
        username = "@" + top10[i].username if top10[i].username is not None else top10[i].id
        emoji = emojis[i]
        downloads = top10[i].int_downloaded
        
        template += f"{emoji}**{username}** - {downloads} Descargas\n"
    
    await message.reply(template)