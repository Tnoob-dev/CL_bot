from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private
import os


@bot.on_message(command("donate", prefixes=["/"]) & private)
async def donations(client: Client, message: Message):

    my_msg = f"""
Hola {message.from_user.mention}

✨ Este canal es posible gracias a ti ✨

Si el contenido te ha sido útil y quieres retribuir de alguna forma, 
aceptamos donaciones voluntarias.

No es obligatorio, pero cada pequeño gesto ayuda a seguir creciendo.

Para cubanos en la isla 🇨🇺:
🎁 Tarjeta CUP: {os.getenv("CUP_CARD")}
🎁 Saldo Movil: {os.getenv("MOBILE")}

Para Residentes de otros Países 🌎:
🎁 Wallet BNB (BEP20): {os.getenv("Wallet_BEP")}

En caso de ser otro tipo de moneda u otro tipo de incentivo,
puede escribir directamente al DM: @TitiLM10

¡Gracias de corazón por estar aquí! ❤️
"""

    await message.reply(my_msg)