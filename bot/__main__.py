# BOT CLIENT
from entry.entry import bot

# LOGGING
import logging

# COMMAND FUNCTIONS
from commands.Hello import hello
from commands.Help import help_command
from commands.Collection import start_collection, end_collection, collect_messages
from commands.Order import get_orders
from commands.Translations import translate_srt
from commands.Misc import send_admin_message
from commands.Posts import create_posts
from commands.Subtitles import search_subtitles

# QUERY FUNCTIONS
from queries.queries import query_manager

# MAIN FUNCTIONS
from utils.create_paths import create_translations_path, create_download_path
from utils.db_reqs import start_daily_reset
from db.create_cine_db import create_db
from utils.functions import clear_path

# PYRO
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Daily reset for 5 tries of srt translation quota
start_daily_reset()

# Create DBs
create_db()

# Paths
create_translations_path()
create_download_path()

# Clear folder
clear_path("./posts/")

# Commands
bot.add_handler(MessageHandler(hello))
bot.add_handler(MessageHandler(start_collection))
bot.add_handler(MessageHandler(collect_messages))
bot.add_handler(MessageHandler(end_collection))
bot.add_handler(MessageHandler(get_orders))
bot.add_handler(MessageHandler(translate_srt))
bot.add_handler(MessageHandler(send_admin_message))
bot.add_handler(MessageHandler(create_posts))
bot.add_handler(MessageHandler(search_subtitles))
bot.add_handler(MessageHandler(help_command))

# Queries
bot.add_handler(CallbackQueryHandler(query_manager))


if __name__ == "__main__":
    logger.info("Starting Bot")
    bot.start()
    logger.info("Bot Started")
    bot.loop.run_forever()
