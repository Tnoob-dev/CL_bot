from entry.entry import bot
from commands.Hello import hello
from commands.Collection import start_collection, end_collection, collect_messages
from commands.Order import get_orders, order_query
from pyrogram.handlers.message_handler import MessageHandler


# Commands
bot.add_handler(MessageHandler(hello))
bot.add_handler(MessageHandler(start_collection))
bot.add_handler(MessageHandler(end_collection))
bot.add_handler(MessageHandler(collect_messages))
bot.add_handler(MessageHandler(get_orders))

if __name__ == "__main__":
    print("starting bot")
    bot.start()
    print("bot started")
    bot.loop.run_forever()
