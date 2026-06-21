# from entry.entry import bot
# from pyrogram.filters import command, private, group
# from pyrogram.types import Message
# from pyrogram.client import Client
# from pyrogram.enums import ParseMode
# import logging
# import os

# # Logger 
# logger = logging.getLogger(__name__)

# @bot.on_message(command("publi", prefixes=["/"]) & (private | group))
# async def publi_command(client: Client, message: Message):
    
#     card_met = os.getenv("CUP_CARD")
#     card_bpa = os.getenv("CUP_CARD2")
#     phone_number = os.getenv("MOBILE")

#     price1, price2, price3 = os.getenv("PRICE1"), os.getenv("PRICE2"), os.getenv("PRICE3")

#     await message.reply(
#     "<b>🚀 PROMOCIONA TU CANAL CON NOSOTROS</b>\n\n"
#     "Ofrecemos diferentes servicios para aumentar tu alcance y conseguir suscriptores reales:\n\n"
    
#     "<b>📢 SERVICIOS DISPONIBLES</b>\n\n"
#     f"<b>1️⃣ Mensaje personalizado en el canal</b>\n"
#     f"   Publicamos tu mensaje directamente en nuestro canal\n"
#     f"   💰 <b>Precio:</b> {price1}\n\n"
    
#     f"<b>2️⃣ Mensaje masivo a todos los usuarios</b>\n"
#     f"   Enviamos tu mensaje por el bot a toda nuestra base de usuarios\n"
#     f"   💰 <b>Precio:</b> {price2}\n\n"
    
#     f"<b>3️⃣ Canal/Grupo obligatorio (1 semana)</b>\n"
#     f"   Los usuarios deben unirse a tu canal/grupo para usar el bot\n"
#     f"   💰 <b>Precio:</b> {price3}\n\n"
    
#     "<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n"
#     "<b>💳 MÉTODOS DE PAGO</b>\n\n"
    
#     "<b>🏦 Transferencias:</b>\n"
#     f"<code>{card_met}</code>\n"
#     f"<code>{card_bpa}</code>\n\n"
    
#     "<b>📱 Saldo Móvil:</b>\n"
#     f"<code>{phone_number}</code>\n\n"
    
#     "<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n"
#     "<b>📩 CONTACTO</b>\n"
#     "Escríbeme al privado para coordinar: @TitiLM10\n\n"
#     "<i>⚡ Respuesta rápida y servicio garantizado</i>",
#     parse_mode=ParseMode.HTML
# )