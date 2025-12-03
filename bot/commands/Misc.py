from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private
import logging

# Logger 
logger = logging.getLogger(__name__)

@bot.on_message(command("h") & private)
async def watch(client: Client, message: Message):
    await message.reply("XD")
    