from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private, text, photo
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
from utils.functions import check_administration
from utils.db_reqs import get_user
import asyncio
import logging

# Logger 
logger = logging.getLogger(__name__)

msg_state = {}

@bot.on_message(command("amsg") & private)
async def send_admin_message(client: Client, message: Message):
    
    try:
        # if check_administration(message):
            
        #     user_id = message.from_user.id
            
        #     if not str(user_id) in msg_state:
        #         msg_state[str(user_id)] = {
        #             "admin_mode": True,
        #             "message": None}
                
        #     await message.reply("Envie el mensaje")
        
        if check_administration(message):
            users = get_user(all_the_users=True)
            quantity_users = len(users)
            
            for user in users:
                success = False # Flag
                while not success:
                    try:
                        await client.copy_message(user.id, message.chat.id, message.reply_to_message.id)
                        success = True
                    except FloodWait as f:
                        asyncio.sleep(f.value)
                    except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid) as e:
                        logger.info(f"No se puede enviar a {user.id}: {e}")
                        quantity_users -= 1
                        success = True
                        
            await message.reply(f"Se le envio el mensaje a {quantity_users} usuarios")
    
    except Exception as error:
        logger.error(error)
            
# @bot.on_message(command("send", prefixes=["/"]) & private)
# async def send_message(client: Client, message: Message):
#     try:
        
        
#     except Exception as error:
#         logger.error(error)