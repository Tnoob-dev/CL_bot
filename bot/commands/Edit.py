from entry.entry import bot
from utils.functions import check_administration
from pyrogram.filters import command, private
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os
import logging


# Logger
logger = logging.getLogger(__name__)

@bot.on_message(command("edit", prefixes=["/"]) & private)
async def edit_posts(client: Client, message: Message):

    if check_administration(message):

        try:
            if len(message.command) == 2:
                
                message_info = await client.get_messages(
                    chat_id=os.getenv("CINEMA_ID"),
                    message_ids=int(message.command[-1])
                )

                await message.reply("Que deseas editar?",
                                    reply_markup=InlineKeyboardMarkup([
                                        [
                                            InlineKeyboardButton("✏️Texto del post", callback_data=f"edit_text_{message_info.id}"),
                                            InlineKeyboardButton("🔄Botones", callback_data=f"edit_btns_{message_info.id}"),
                                        ],
                                        [InlineKeyboardButton("❌Eliminar post", callback_data=f"remove_{message_info.id}")]
                                    ]))
        
        except ValueError:
            await message.reply("El id no es un numero")