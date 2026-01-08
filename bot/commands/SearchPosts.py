from entry.entry import bot
from utils.functions import check_user_in_channel
from utils.db_reqs import get_post_by_name
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.filters import command, private, group
import logging

# Logger
logger = logging.getLogger(__name__)

@bot.on_message(command("search", prefixes=["/"]) & (private | group))
async def search_posts(client: Client, message: Message):
    
    if not await check_user_in_channel(client, message):
        return
    
    if message.command is not None:
        
        m = await message.reply("__🔎Buscando...🔎__")
        
        if len(message.command) >= 2:
            await m.delete()
            user_message = ' '.join(message.command[1:])
            
            results = get_post_by_name(user_message)
            
            if len(results) > 0:
                keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=res.get("name"),
                            url=res.get("link")
                        )
                    ]
                    for res in results
                ] + [
                    [
                        InlineKeyboardButton(
                            text="❌Cerrar❌",
                            callback_data="close"
                        )
                    ]
                ]
            )
                await message.reply("🏆🔥Estos fueron los resultados que encontre para su busqueda🔎👀:", reply_markup=keyboard)
            
            else:
                await m.delete()
                await message.reply("No he encontrado nada con ese nombre")