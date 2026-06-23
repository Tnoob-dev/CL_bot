from entry.entry import bot
from utils.functions import check_administration, clean_name
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup
from pyrogram.filters import command, private
import os
import logging


# Logger
logger = logging.getLogger(__name__)

@bot.on_message(command("fusion", prefixes=["/"]) & private)
async def fusion_posts(client: Client, message: Message):

    if check_administration(message) and message.command is not None:

        if len(message.command) == 3:
            
            command = message.command

            try:
                post1_id = int(command[-2])
                post2_id = int(command[-1])
            except ValueError:
                await message.reply("Los IDs deben ser numeros validos")
                return
            
            chat_id = os.getenv("CINEMA_ID")

            message_info = await client.get_messages(
                chat_id=chat_id,
                message_ids=[post1_id, post2_id]
            )

            post1_info = message_info[0]
            post2_info = message_info[1]

            combined_keyboard = []
            combined_keyboard.extend(post1_info.reply_markup.inline_keyboard)
            combined_keyboard.extend(post2_info.reply_markup.inline_keyboard)

            try:
                await client.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=post1_id,
                    reply_markup=InlineKeyboardMarkup(combined_keyboard)
                )

                await client.delete_messages(
                    chat_id=chat_id,
                    message_ids=post2_id
                )

                await message.reply(f"Post #1 ||{post1_id}|| editado con el nuevo inline markup✅📝\n\nPost #2 ha sido eliminado🗑")
                
                logger.info(f"Se ha editado el post de {post1_id}")
            
            except Exception as e:
                await message.reply(f"Error - {e}")