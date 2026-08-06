import logging
import os
import re
from ast import literal_eval

from db.create_cine_db import Post
from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, private
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.db_reqs import delete_post, get_post_by_id, insert_post
from utils.functions import check_administration, clean_name
from utils.rt_client import info

# Logger
logger = logging.getLogger(__name__)


@bot.on_message(command("post", prefixes=["/"]) & private)
async def create_posts(client: Client, message: Message):

    try:
        if check_administration(message):
            if not message.reply_to_message or not message.reply_to_message.photo:
                await message.reply(
                    "Responde a un mensaje con foto para crear el post."
                )
                return

            post = message.reply_to_message.photo.file_id

            m = await message.reply("Descargando imagen, creando post y enviando...")
            pic = await client.download_media(post, file_name="./posts/")
            description = message.reply_to_message.caption
            
            if description.startswith("🎬"):
                title = re.search(r"^🎬\s*(.*?)\s*🎬$", description, re.MULTILINE).group(1).split("|")
            else:
                title = re.search(r"^🎭\s*(.*?)\s*🎭$$", description, re.MULTILINE).group(1).split("|")
            
            rt_info = await info(title[0])
            
            rt_url = rt_info.get("tomatoes").get("reviews_links")
            audience_url = rt_info.get("audience").get("reviews_links")
            
            links = literal_eval(message.text[6:])

            sent = await client.send_photo(
                chat_id=os.getenv("CINEMA_ID"),
                photo=pic,
                caption=description.markdown,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="Rotten Tomatoes 🍅 Reviews", url=rt_url),
                            InlineKeyboardButton(text="Review de la Audiencia🙋", url=audience_url)
                        ],
                        *[
                            [InlineKeyboardButton(text=content[0], url=content[1])]
                            for content in links
                    ]]
                ),
            )

            await m.edit(
                f"⏩Post Enviado\n🆔ID: {sent.id}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Eliminar del canal y la BD",
                                callback_data=f"remove_{sent.id}",
                            )
                        ]
                    ]
                ),
            )
            os.remove(pic)

            sent_id = sent.id
            name_cleaned = clean_name(sent.caption)

            insert_post(
                Post(
                    id=sent_id,
                    movie_name=name_cleaned,
                    link=f"https://t.me/{os.getenv('CINEMA_ID')}/{sent_id}",
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

    if check_administration(message) and len(user_command) >= 2:
        post_id = int(user_command[-1])
        post = get_post_by_id(post_id)

        boolean, msg = delete_post(post_id)

        if not boolean:
            await message.reply(f"❌{msg}❌")
        else:
            await client.delete_messages(chat_id=clibrary, message_ids=post_id)

            await message.reply("✅Post eliminado de la base de datos y el canal✅")

            await client.send_message(
                chat_id=int(os.getenv("OWNER_ID")),
                text=f"El administrador {message.from_user.mention} ha eliminado __{post.movie_name}__ de la db",
            )
