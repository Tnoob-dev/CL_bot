from entry.entry import bot
from utils.db_reqs import get_post_by_name
from pyrogram.client import Client
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, InlineQuery
from pyrogram.errors import UserNotParticipant, QueryIdInvalid, MessageEmpty
import logging
import os

logger = logging.getLogger(__name__)

async def check(client: Client, query: InlineQuery):
    if not query.from_user:
        return False
    
    try:
        await client.get_chat_member(chat_id=os.getenv("CINEMA_ID"), user_id=query.from_user.id)

        return True
    except UserNotParticipant:
        await query.answer(
            results=[
                InlineQueryResultArticle(
                    title="No perteneces al canal",
                    input_message_content=InputTextMessageContent(
                        message_text=query.query
                    ),
                    url="https://t.me/CL_LibraryBK"
                )
            ], cache_time=1
        )
    except Exception as e:
        logger.error(f"Error inesperado en check_user_in_channel: {e}")
        return False

######## INLINE QUERY

@bot.on_inline_query()
async def inline_answer(client: Client, inline_query: InlineQuery):
    
    if not await check(client, inline_query):
        return
    
    try:
        offset = int(inline_query.offset) if inline_query.offset else 0
        limit = 50

        movies = get_post_by_name(inline_query.query)
        movies_page = movies[offset:offset + limit]

        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title=mov["name"],
                    input_message_content=InputTextMessageContent(
                        message_text=inline_query.query
                    ),
                    url=mov["link"],
                    reply_markup=(
                        InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text=mov["name"],
                                url=mov["link"]
                            )]
                        ])
                    )
                )
                for mov in movies_page
            ], 
            cache_time=60,
            next_offset=str(offset + limit) if len(movies_page) == limit else ""
        )
    
    except QueryIdInvalid as msg:
        logger.error(f"Error buscando, algo paso con el query: {msg}")

    except MessageEmpty:
        pass