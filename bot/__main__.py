from entry.entry import bot
from commands.Hello import hello
from commands.Collection import start_collection, end_collection, collect_messages
from commands.Order import get_orders
from commands.Translations import translate_srt
from queries.queries import query_manager
from utils.create_paths import create_translations_path, create_download_path
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler


# Paths
create_translations_path()
create_download_path()

# Commands
bot.add_handler(MessageHandler(hello))
bot.add_handler(MessageHandler(start_collection))
bot.add_handler(MessageHandler(collect_messages))
bot.add_handler(MessageHandler(end_collection))
bot.add_handler(MessageHandler(get_orders))
bot.add_handler(MessageHandler(translate_srt))

# Queries
bot.add_handler(CallbackQueryHandler(query_manager))

if __name__ == "__main__":
    print("starting bot")
    bot.start()
    print("bot started")
    bot.loop.run_forever()
