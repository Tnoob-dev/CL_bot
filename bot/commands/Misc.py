from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private, text, photo
from utils.functions import check_administration
from utils.db_reqs import get_user
import logging

# Logger 
logger = logging.getLogger(__name__)

msg_state = {}

@bot.on_message(command("amsg") & private)
async def send_admin_message(client: Client, message: Message):
    
    if check_administration(message):
        
        user_id = message.from_user.id
        
        if not str(user_id) in msg_state:
            msg_state[str(user_id)] = {
                "admin_mode": True,
                "message": None}
            
        await message.reply("Envie el mensaje")
        
@bot.on_message(command("send", prefixes=["/"]) & private)
async def send_message(client: Client, message: Message):
    try:
        
        if check_administration(message):
            user_id = message.from_user.id
            if str(user_id) in msg_state:
                users = get_user(all_the_users=True)
                
                for user in users:
                    await client.copy_message(user.id, message.chat.id, msg_state[str(user_id)]["message"])
            
                del msg_state[str(user_id)]
            else:
                await message.reply("No has entrado en modo administrador para enviar mensajes")
    except Exception as error:
        logger.error(error)

@bot.on_message(command("cancel", prefixes=["/"]) & private)
async def cancel_action(client: Client, message: Message):
    try:
        if check_administration(message):
            user_id = message.from_user.id
            if str(user_id) in msg_state:
                del msg_state[str(user_id)]
                await message.reply("Accion cancelada")
            else:
                await message.reply("No se encuentra actualmente en modo administrador")
    except Exception as error:
        logger.error(error)
        
@bot.on_message(private & text | photo)
async def message_to_users(client: Client, message: Message):
    try:
        if message.from_user.id is not None:
            if check_administration(message):
                user_id = message.from_user.id
                if str(user_id) in msg_state:
                    msg_state[str(user_id)]["message"] = message.id
    except AttributeError as error:
        logger.error(error)