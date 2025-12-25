from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, private, group, photo, text
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from utils.functions import check_user_in_channel
from utils.db_reqs import get_post_by_name
import logging

# Logger 
logger = logging.getLogger(__name__)

# just the order logic for when the user asks for a movie or a tv series
@bot.on_message(command("cine", prefixes=["#"]) & group & photo)
async def get_orders(client: Client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) >= 2:
        user_message = ' '.join(message.command[1:])
        
        results = get_post_by_name(user_message)
        
        if len(results) > 0:
            
            keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=res.get("name"),
                        url=res.get("link")
                    )
                ]
                for res in results
            ] + [
                [
                    InlineKeyboardButton(
                        text="❌Mi orden no esta❌",
                        callback_data=f"order_not_found_{user_id}_{user_message}"
                    )
                ]
            ]
        )
            
            await message.reply("Segun tu peticion encontre esto", 
                                reply_markup=keyboard)
        else:
            mes = await message.reply("✅Orden Reenviada a los administradores✅",
                                reply_markup=InlineKeyboardMarkup(
                                    [
                                        [InlineKeyboardButton("🎬Canal de pedidos🎬", url="https://t.me/CinemaOrders")]
                                    ]
                                ))
            
            await client.send_message(chat_id="CinemaOrders",
                                      text=f"🎟Nueva solicitud:\n\n**Pedido**: __{user_message}__\n**Usuario**: {message.from_user.mention} (__{user_id}__)\n**Link**: {message.link}",
                                      reply_markup=InlineKeyboardMarkup(
                                          [
                                              [
                                                  InlineKeyboardButton("🫡Orden Lista🫡", callback_data=f"order_ready_{mes.reply_to_message_id}") # reply_to_message_id is deprecated, investigate about reply_parameters
                                              ]
                                          ]
                                      ))
    else:
        await message.reply("No voy a reenviar una orden vacia")

@bot.on_message(command("pedido", prefixes=["/"]) & private & text)
async def order_in_private(client: Client, message: Message):
    
    user_id = message.from_user.id
    
    if not await check_user_in_channel(client, message):
        return
    
    if message.command is not None and len(message.command) >= 2:
        user_message = ' '.join(message.command[1:])
        
        results = get_post_by_name(user_message)
        
        if len(results) > 0:
            keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=res.get("name"),
                        url=res.get("link")
                    )
                ]
                for res in results
            ] + [
                [
                    InlineKeyboardButton(
                        text="❌Mi orden no esta❌",
                        callback_data=f"pm_order_not_found_{user_id}_{user_message}"
                    )
                ]
            ]
        )
            await message.reply("Segun tu peticion encontre esto", 
                                reply_markup=keyboard)
        else:
            await message.reply("✅Orden Reenviada a los administradores✅",
                                reply_markup=InlineKeyboardMarkup(
                                    [
                                        [InlineKeyboardButton("🎬Canal de pedidos🎬", url="https://t.me/CinemaOrders")]
                                    ]
                                ))
            
            await client.send_message(chat_id="CinemaOrders",
                                    text=f"🎟Nueva solicitud:\n\n**Pedido**: __{user_message}__\n**Usuario**: {message.from_user.mention} (__{user_id}__)",
                                    reply_markup=InlineKeyboardMarkup(
                                        [
                                            [
                                                InlineKeyboardButton("🫡Orden Lista🫡", callback_data=f"order_ready_pm_{user_id}")
                                            ]
                                        ]
                                    ))
    else:
        await message.reply("No voy a reenviar una orden vacia")
    
    