from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, group
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from utils.functions import check_administration

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
        

        

@bot.on_callback_query()
async def order_query(client: Client, query: CallbackQuery):

    if query.data == 'order_ready':
        if check_administration(query):
                await client.send_message(chat_id="chat1080p", 
                                        text="Su pedido ha sido completado",
                                        reply_to_message_id=mes.reply_to_message_id)
                await query.message.delete()
        else:
            await query.answer(text="🤨", show_alert=True)