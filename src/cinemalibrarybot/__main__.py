# BOT CLIENT
from cinemalibrarybot.client import bot
# LOGGING
import logging

# misc
import asyncio

# COMMAND FUNCTIONS
from cinemalibrarybot.handlers.Hello import hello
from cinemalibrarybot.handlers.Collection import collect_messages, end_collection
from cinemalibrarybot.handlers.InfoPosts import info_posts
from cinemalibrarybot.handlers.Misc import (help_command,
                           count_users,
                           send_admin_message,
                           ascend_to_admin,
                           get_top10,
                           make_old_posts,
                           donations,
                           convert_user_premium)
from cinemalibrarybot.handlers.Order import get_orders
from cinemalibrarybot.handlers.Posts import create_posts, remove_posts
from cinemalibrarybot.handlers.SearchPosts import search_posts
from cinemalibrarybot.handlers.Subtitles import search_subtitles
from cinemalibrarybot.handlers.Publicity import publi_command
from cinemalibrarybot.handlers.Fusion import fusion_posts
from cinemalibrarybot.handlers.Stream import stream_handler
from cinemalibrarybot.handlers.Profile import profile_panel

# MAIN FUNCTIONS
from cinemalibrarybot.repositories.create_cine_db import create_db

# PYRO
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.inline_query_handler import InlineQueryHandler

# QUERY FUNCTIONS
from cinemalibrarybot.handlers.cb_queries import query_manager, save_user_photo
from cinemalibrarybot.handlers.inline_queries import inline_answer

# STREAM
from cinemalibrarybot.stream.server import start_stream_server
from cinemalibrarybot.stream.tunnel import start_cloudflare_tunnel
from cinemalibrarybot.stream.config import StreamConfig

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def register_handlers() -> None:
    """Register every message/callback/inline handler on the bot.

    The command modules also self-register via ``@bot.on_message`` decorators at
    import time; these explicit registrations are kept to preserve the exact
    dispatch behavior of the original bot.
    """
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


def run() -> None:
    """Console-script entry point (``cl-bot`` / ``python -m cinemalibrarybot``)."""
    create_db()
    register_handlers()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot apagado por el usuario.")
    finally:
        loop.close()


if __name__ == "__main__":
    run()
