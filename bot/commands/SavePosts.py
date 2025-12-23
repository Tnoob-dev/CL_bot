from entry.entry import bot
from utils.functions import check_administration
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private, group, text


@bot.on_message(command("xd", prefixes=["/"]) & group)
async def save_post(client: Client, message: Message):
    
    if check_administration(message):
        msg = message.reply_to_message
        
        if not msg:
            await message.reply("Responde a un mensaje con /save")
            return
        
        if msg.forward_from_chat and msg.forward_from_chat.type == "channel":
            original_chat = msg.forward_from_chat
            message_id = msg.forward_from_message_id
            caption = message.caption
            channel_username = original_chat.username
            
            if channel_username:
                message_link = f"https://t.me/{channel_username}/{message_id}"
                
            print(f"ID: {message_id}")
            print(f"Link: {message_link}")
            print(f"Caption: {caption}")