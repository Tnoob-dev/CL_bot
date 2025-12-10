from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, group, photo
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import logging

# Logger 
logger = logging.getLogger(__name__)

# just the order logic for when the user asks for a movie or a tv series
@bot.on_message(command("cine", prefixes=["#"]) & group & photo)
async def get_orders(client: Client, message: Message):
    
    # make mes global to return it
    global mes
    if len(message.command) >= 2:
        # send order to orders channel
        mes = await message.reply("✅Orden Reenviada a los administradores✅",
                            reply_markup=InlineKeyboardMarkup(
                                [
                                    [InlineKeyboardButton("🎬Canal de pedidos🎬", url="https://t.me/CinemaOrders")]
                                ]
                            ))
        
        # create order message
        await client.send_message(chat_id="CinemaOrders",
                                  text=f"🎟Nueva solicitud:\n\n**Pedido**: __{' '.join(message.command[1:])}__\n**Usuario**: {message.from_user.mention} (__{message.from_user.id}__)\n**Link**: {message.link}",
                                  reply_markup=InlineKeyboardMarkup(
                                      [
                                          [
                                              InlineKeyboardButton("🫡Orden Lista🫡", callback_data="order_ready")
                                          ]
                                      ]
                                  ))
    else:
        await message.reply("No voy a reenviar una orden vacia")

def return_mesID():
    return mes.reply_to_message_id