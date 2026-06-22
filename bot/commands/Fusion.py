from entry.entry import bot
from utils.functions import check_administration
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup
from pyrogram.filters import command, private
import os
import logging


@bot.on_message(command("fusion", prefixes=["/"]) & private)
async def fusion_posts(client: Client, message: Message):

    if check_administration(message) and message.command is not None:

        if message.command is not None and len(message.command) == 3:
            
            command = message.command

            post1_id = int(command[-2])
            post2_id = int(command[-1])

            if post1_id == None or post2_id == None:
                await message.reply("Uno o ambos ids no son validos")
                return
            
            message_info = await client.get_messages(
                chat_id=os.getenv("CINEMA_ID"),
                message_ids=[post1_id, post2_id]
            )

            post1_info = message_info[0]
            post2_info = message_info[1]


            post1_info.reply_markup.inline_keyboard.extend(post2_info.reply_markup.inline_keyboard)

            await client.edit_message_reply_markup(
                chat_id=os.getenv("CINEMA_ID"),
                message_id=post1_id,
                reply_markup=InlineKeyboardMarkup(post1_info.reply_markup.inline_keyboard)
            )

            await message.reply("Post editado con el nuevo inline markup")