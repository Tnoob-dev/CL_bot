# BOT CLIENT
from entry.entry import bot
# LOGGING
import logging

# misc
import asyncio

# COMMAND FUNCTIONS
from commands.Hello import hello
from commands.Help import help_command
from commands.Collection import collect_messages, end_collection
from commands.InfoPosts import info_posts
from commands.Misc import count_users, send_admin_message, ascend_to_admin, get_top10, make_old_posts, convert_user_premium
from commands.Order import get_orders
from commands.Posts import create_posts, remove_posts
from commands.SearchPosts import search_posts
from commands.Subtitles import search_subtitles
from commands.Donations import donations
from commands.Publicity import publi_command
from commands.Fusion import fusion_posts
from commands.Edit import edit_posts
from commands.Stream import stream_handler
from commands.Profile import profile_panel

# MAIN FUNCTIONS
from db.create_cine_db import create_db

# PYRO
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.inline_query_handler import InlineQueryHandler

# QUERY FUNCTIONS
from queries.cb_queries import query_manager, save_user_photo
from queries.inline_queries import inline_answer

# STREAM
from stream.server import start_stream_server
from stream.tunnel import start_cloudflare_tunnel
from stream.config import StreamConfig

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Create DBs
create_db()

# Commands
bot.add_handler(MessageHandler(hello))
bot.add_handler(MessageHandler(collect_messages))
bot.add_handler(MessageHandler(end_collection))
bot.add_handler(MessageHandler(get_orders))
bot.add_handler(MessageHandler(send_admin_message))
bot.add_handler(MessageHandler(count_users))
bot.add_handler(MessageHandler(ascend_to_admin))
bot.add_handler(MessageHandler(convert_user_premium))
bot.add_handler(MessageHandler(get_top10))
bot.add_handler(MessageHandler(search_subtitles))
bot.add_handler(MessageHandler(help_command))
bot.add_handler(MessageHandler(create_posts))
bot.add_handler(MessageHandler(remove_posts))
bot.add_handler(MessageHandler(info_posts))
bot.add_handler(MessageHandler(search_posts))
bot.add_handler(MessageHandler(donations))
bot.add_handler(MessageHandler(publi_command))
bot.add_handler(MessageHandler(fusion_posts))
bot.add_handler(MessageHandler(edit_posts))
bot.add_handler(MessageHandler(stream_handler))
bot.add_handler(MessageHandler(make_old_posts))
bot.add_handler(MessageHandler(profile_panel))
bot.add_handler(MessageHandler(save_user_photo))

# Queries
bot.add_handler(CallbackQueryHandler(query_manager))
bot.add_handler(InlineQueryHandler(inline_answer))

async def main():
    # Primero configura el tunnel si es necesario
    if "localhost" in StreamConfig.URL or "127.0.0.1" in StreamConfig.URL:
        logger.info("Starting Cloudflare tunnel...")
        tunnel_url, _ = start_cloudflare_tunnel(StreamConfig.PORT)
        if tunnel_url:
            StreamConfig.update_url(tunnel_url)
            logger.info(f"URL updated: {StreamConfig.URL}")
        else:
            logger.info("Could not start tunnel, using local URL")

    # Luego inicia el stream server
    await start_stream_server(bot)
    logger.info(f"Stream server active at: {StreamConfig.URL}")

    # Finalmente inicia el bot
    await bot.start()
    logger.info("Bot started")

    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot apagado por el usuario.")
    finally:
        loop.close()
