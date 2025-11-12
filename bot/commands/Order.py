from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, group
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


@bot.on_message(command("cine", prefixes=["#"]) & group)
async def get_orders(client: Client, message: Message):
    
    global mes
    if len(message.command) >= 2:
        mes = await message.reply("✅Orden Reenviada a los administradores✅",
                            reply_markup=InlineKeyboardMarkup(
                                [
                                    [InlineKeyboardButton("🎬Canal de pedidos🎬", url="https://t.me/CinemaOrders")]
                                ]
                            ))
        
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