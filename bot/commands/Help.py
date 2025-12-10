from entry.entry import bot
from pyrogram.client import Client
from pyrogram.types import Message
from pyrogram.filters import command, private
from utils.functions import check_user_in_channel

@bot.on_message(command("help", prefixes=["/"]) & private)
async def help_command(client: Client, message: Message):
    
    if not await check_user_in_channel(client, message):
        return
    
    help_message = """
Claro! ✨

✅Aqui tienes los comandos que puedes utilizar en mi:

#Privado 🤖

/start - Inicia el bot u obtiene los archivos que solicito por el canal
/help - Muestra esta ayuda
/tr - Respondiendo a un subtitulo puede traducirlo a Ingles o Español
/srt <-nombre-> - Obtiene el subtitulo de lo que busco, ejemplo: /srt Breaking Bad

#Grupo 👥

#cine <-nombre-> - Su pedido entrara en la lista de ordenes

PD: Revise siempre el canal antes de hacer un pedido, pues nos toma tiempo cumplir los pedidos de todos, y se nos hace de muy mal gusto subir cosas que ya esten subidas en el canal. 😉

__Gracias por usar nuestro bot, y gracias por ser de la familia Library.__
"""
    
    await message.reply(help_message)