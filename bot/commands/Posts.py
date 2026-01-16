from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.filters import command, private
from utils.functions import check_administration, clean_name
from utils.db_reqs import insert_post, delete_post
from db.create_cine_db import Post
from ast import literal_eval
import os
import logging

# Logger
logger = logging.getLogger(__name__)

@bot.on_message(command("post", prefixes=["/"]) & private)
async def create_posts(client: Client, message: Message):

    try:
        if check_administration(message):

            if not message.reply_to_message or not message.reply_to_message.photo:
                await message.reply("Responde a un mensaje con foto para crear el post.")
                return

            post = message.reply_to_message.photo.file_id

            m = await message.reply("Descargando imagen, creando post y enviando...")
            pic = await client.download_media(post, file_name="./posts/")
            description = message.reply_to_message.caption
            links = literal_eval(message.text[6:])

            sent = await client.send_photo(
                chat_id=os.getenv("CINEMA_ID"),
                photo=pic,
                caption=description,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(text=content[0], url=content[1])] for content in links
                    ]
                )
            )

            await m.edit(f"⏩Post Enviado\n🆔ID: {sent.id}",
                         reply_markup=InlineKeyboardMarkup(
                             [
                                 [InlineKeyboardButton("Eliminar del canal y la BD", callback_data=f"remove_{sent.id}")]
                             ]
                         ))
            os.remove(pic)

            sent_id = sent.id
            name_cleaned = clean_name(sent.caption)

            insert_post(
                Post(
                    id=sent_id,
                    movie_name=name_cleaned,
                    link=f"https://t.me/{os.getenv("CINEMA_ID")}/{sent_id}"
                )
            )

            logger.info("Post enviado y anadido a la db")
    except Exception as e:
        logger.error(e)
        await message.reply(f"Ha ocurrido un error: {e}")


@bot.on_message(command("delpost", prefixes=["/"]) & private)
async def remove_posts(client: Client, message: Message):
    
    user_command = message.command
    clibrary = os.getenv("CINEMA_ID")

    if check_administration(message):
        if len(user_command) >= 2:
            
            boolean, msg = delete_post(int(user_command[-1]))
            
            if not boolean:
                await message.reply(f"❌{msg}❌")
            else:
                await client.delete_messages(chat_id=clibrary, 
                                            message_ids=int(user_command[-1]))
                
                await message.reply("✅Post eliminado de la base de datos y el canal✅")