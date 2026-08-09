import asyncio
import logging
import os

from entry.entry import bot
from pyrogram.client import Client
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    PeerIdInvalid,
    UserIsBlocked,
    UserIsBot,
)
from pyrogram.filters import command, group, private
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils.db_reqs import get_user, update_user_admin, update_user_premium
from utils.functions import (
    check_administration,
    check_user_in_channel,
    gen_ids,
    register_movie,
)

# Logger
logger = logging.getLogger(__name__)


@bot.on_message(command("help", prefixes=["/"]) & private)
async def help_command(client: Client, message: Message):

    if not await check_user_in_channel(client, message):
        return

    help_message = f"""
📖 **Menú de Ayuda**

Estos son los comandos disponibles:

🔹 /start - Inicia el bot u obtiene el archivo solicitado
🔹 /help - Obtiene la ayuda del bot
🔹 /count - Ver cuántos usuarios hay registrados en el bot
🔹 /srt - Búsqueda online de subtítulos
🔹 /search - Buscar posts del canal
🔹 /top10 - Obtener el top 10 de usuarios que más descargan del canal
🔹 /profile - Ver tu perfil de usuario
🔹 /vip - Adquirir plan VIP
🔹 /stream - Hacer stream a archivos y videos
🔹 /donate - Ver métodos de donación para el canal
🔹 /publi - Ver ofertas de publicidad

❓ Si tienes dudas o problemas, contacta a un administrador. En el chat del canal @{os.getenv("GROUP_ID")}.
"""

    await message.reply(help_message)


@bot.on_message(command("donate", prefixes=["/"]) & private)
async def donations(client: Client, message: Message):

    my_msg = f"""
Hola {message.from_user.mention}

✨ Este canal es posible gracias a ti ✨

Si el contenido te ha sido útil y quieres retribuir de alguna forma,
aceptamos donaciones voluntarias.

No es obligatorio, pero cada pequeño gesto ayuda a seguir creciendo.

Para cubanos en la isla 🇨🇺:
🎁 Tarjeta CUP METROPOLITANO: {os.getenv("CUP_CARD")}
🎁 Tarjeta CUP BPA: {os.getenv("CUP_CARD2")}
🎁 Saldo Movil: {os.getenv("MOBILE")}

Para Residentes de otros Países 🌎:
🎁 Wallet BNB (BEP20): {os.getenv("Wallet_BEP")}

En caso de ser otro tipo de moneda u otro tipo de incentivo,
puede escribir directamente al DM: @TitiLM10

¡Gracias de corazón por estar aquí! ❤️
"""

    await message.reply(my_msg)


@bot.on_message(command("advise") & private)
async def send_admin_message(client: Client, message: Message):

    try:
        owner_id = os.getenv("OWNER_ID")
        if message.from_user.id == int(owner_id):
            _, users = get_user(all_the_users=True)
            quantity_users = len(users)
            await message.reply(f"Enviando mensaje {quantity_users} a usuarios")

            blocked_users = 0
            bots = 0

            # TitiLM10, Nyan, bot, moskitosantana
            not_send = [957370219, 1891819663, 8161420181, 715727671]

            for user in users:
                if user.id not in not_send:
                    success = False  # Flag
                    while not success:
                        try:
                            await client.copy_message(
                                user.id, message.chat.id, message.reply_to_message.id
                            )
                            success = True
                        except FloodWait as f:
                            await asyncio.sleep(f.value)
                        except (
                            UserIsBlocked,
                            InputUserDeactivated,
                            PeerIdInvalid,
                        ) as e:
                            logger.warning(f"No se puede enviar a {user.id}: {e}")
                            blocked_users += 1
                            success = True
                        except UserIsBot:
                            logger.warning(
                                f"No se puede enviar a {user.id} porque es un bot"
                            )
                            bots += 1
                            success = True

            await message.reply(
                f"--Summary--:\n\n👥Total de usuarios registrados: {quantity_users}\n✅Cantidad de usuarios a los que se le envio el mensaje: {quantity_users - blocked_users}\n🚫Cantidad de usuarios que tienen bloqueado al bot: {blocked_users}\n🤖Cantidad de Bots: {bots}"
            )
        else:
            await message.reply("❌No tiene permisos para usar este comando❌")

    except Exception as error:
        logger.error(error)


@bot.on_message(command("admin") & private)
async def ascend_to_admin(client: Client, message: Message):

    user_command = message.command
    user_id = message.from_user.id
    owner_id = os.getenv("OWNER_ID")

    try:
        if user_id == int(owner_id) and len(user_command) == 2:
            boolean, msg = update_user_admin(user_command[-1])

            if boolean:
                logger.info(msg)
                await message.reply(f"✅{msg}✅")
            else:
                logger.error(msg)
                await message.reply(f"❌{msg}❌")
    except Exception as e:
        logger.error(e)
        await message.reply(f"❌Error de excepcion: {e}❌")


@bot.on_message(command("premium", prefixes=["/"]) & private)
async def convert_user_premium(client: Client, message: Message):

    if not check_administration(message):
        return

    user_command = message.command

    try:
        if len(user_command) == 2:
            boolean, dead_date = update_user_premium(user_command[-1], 32)

            if boolean:
                logger.info(
                    f"Se le ha otorgado premium al usuario {user_command[-1]} hasta "
                    + dead_date
                )
                await message.reply(
                    f"Se le ha otorgado premium al usuario {user_command[-1]} hasta "
                    + dead_date
                )
                await client.send_message(
                    chat_id=int(message.command[-1]),
                    text="Se le ha otorgado premium hasta " + dead_date,
                )
            else:
                logger.error(f"Error al otorgar premium al usuario {user_command[-1]}")
                await message.reply(
                    f"Error al otorgar premium al usuario {user_command[-1]}"
                )

    except Exception as e:
        logger.error(e)
        await message.reply(f"❌Error de excepcion: {e}❌")


@bot.on_message(command("vip", prefixes=["/"]) & private)
async def vip_command(client: Client, message: Message):

    await message.reply(
        text=(
            "✨ *¡Lleva tu experiencia al siguiente nivel!* ✨\n\n"
            "Descubre todos los beneficios exclusivos de nuestro **Plan VIP** 💎 y los sencillos pasos para activarlo.\n\n"
            "Presiona el botón de abajo para más información ⬇️"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💎 Ver Beneficios y Precios", callback_data="become_vip"
                    )
                ]
            ]
        ),
    )


@bot.on_message(command("count"))
async def count_users(client: Client, message: Message):

    _, users = get_user(all_the_users=True)

    premium_users = [user for user in users if user.premium_user]

    await client.send_message(
        chat_id=message.chat.id,
        text=f"Actualmente tengo registrados a {len(users)} usuarios 👤\n\n{len(premium_users)} son premium 💎",
    )


@bot.on_message(command("top10") & (private | group))
async def get_top10(client: Client, message: Message):

    bot_username = os.getenv("SENDER_BOT")
    _, users = get_user(all_the_users=True)

    sorted_users = sorted(users, key=lambda u: u.int_downloaded, reverse=True)

    emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    top10 = sorted_users[:10]

    template = f"🦾TOP 10 Usuarios de @{bot_username}🤖\n"

    for i in range(10):
        username = (
            "@" + top10[i].username if top10[i].username is not None else top10[i].id
        )
        emoji = emojis[i]
        downloads = top10[i].int_downloaded

        template += f"{emoji}**{username}** - {downloads} Descargas\n"

    await message.reply(template)


@bot.on_message(command("old", prefixes=["/"]) & private)
async def make_old_posts(client: Client, message: Message):

    if not check_administration(message):
        return

    if message.reply_to_message and message.reply_to_message.text:
        # massive mode
        lines = message.reply_to_message.text.strip().split("\n")
        resultados = []
        errores = []

        for i, line in enumerate(lines, start=1):
            parts = line.strip().split()

            if len(parts) not in (1, 2):
                errores.append(f"Línea {i}: formato inválido ➜ '{line}'")
                continue

            try:
                if len(parts) == 1:
                    generated_id = await gen_ids(int(parts[0]))
                else:
                    inicio, final = int(parts[0]), int(parts[1])
                    generated_id = await gen_ids(inicio, final)
            except ValueError:
                errores.append(f"Línea {i}: IDs no numéricos ➜ '{line}'")
                continue

            link = register_movie(generated_id)
            resultados.append((f"Temporada {i}", link))

        await message.reply(f"```python\n\n{resultados!s}```")

    elif message.command is not None and len(message.command) >= 2:
        # normal mode
        if len(message.command) > 3:
            await message.reply("Error, solo deben ser 2 ids, un inicio y un final")
            return

        match len(message.command):
            case 2:
                generated_id = await gen_ids(int(message.command[-1]))
            case 3:
                generated_id = await gen_ids(
                    int(message.command[1]), int(message.command[-1])
                )

        link = register_movie(generated_id)
        await message.reply(f"[('Temporada 1', '{link}')]")
