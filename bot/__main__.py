# BOT CLIENT
from entry.entry import bot
# LOGGING
import logging

# COMMAND FUNCTIONS
from commands.Hello import hello
from commands.Help import help_command
from commands.Collection import collect_messages, end_collection
from commands.InfoPosts import info_posts
from commands.Misc import count_users, send_admin_message, ascend_to_admin, get_top10
from commands.Order import get_orders
# from commands.Translations import translate_srt
from commands.Posts import create_posts, remove_posts
from commands.SearchPosts import search_posts
from commands.Subtitles import search_subtitles

# MAIN FUNCTIONS
from db.create_cine_db import create_db
from utils.create_paths import create_download_path, create_translations_path
from utils.db_reqs import start_daily_reset

# PYRO
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler

# QUERY FUNCTIONS
from queries.cb_queries import query_manager

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

# Commands
bot.add_handler(MessageHandler(hello))
bot.add_handler(MessageHandler(collect_messages))
bot.add_handler(MessageHandler(end_collection))
bot.add_handler(MessageHandler(get_orders))
# bot.add_handler(MessageHandler(translate_srt))
bot.add_handler(MessageHandler(send_admin_message))
bot.add_handler(MessageHandler(count_users))
bot.add_handler(MessageHandler(ascend_to_admin))
bot.add_handler(MessageHandler(get_top10))
bot.add_handler(MessageHandler(search_subtitles))
bot.add_handler(MessageHandler(help_command))
bot.add_handler(MessageHandler(create_posts))
bot.add_handler(MessageHandler(remove_posts))
bot.add_handler(MessageHandler(info_posts))
bot.add_handler(MessageHandler(search_posts))

# Queries
bot.add_handler(CallbackQueryHandler(query_manager))

if __name__ == "__main__":
    logger.info("Bot started")
    bot.run()
