import asyncio
import logging
import os
from pathlib import Path

from db.create_cine_db import Users
from entry.entry import bot
from pyrogram.client import Client
from pyrogram.errors import FloodWait
from pyrogram.filters import command, private
from pyrogram.types import Message
from utils.db_reqs import (
    get_game,
    get_or_create_user,
    is_premium,
    record_download,
)
from utils.functions import check_user_in_channel

# Logger
logger = logging.getLogger(__name__)

# --- Global concurrency control -------------------------------------------
# Shared semaphore so many simultaneous downloads cannot trigger massive
# FloodWaits on the Telegram API (each client call slot is rate limited).
_COPY_SEMAPHORE = asyncio.Semaphore(10)

# Keep strong references to fire-and-forget tasks; without this, Python's
# garbage collector may destroy pending tasks (deletes never executed) and
# unretrieved exceptions can destabilize the Pyrogram updater.
_BACKGROUND_TASKS: set[asyncio.Task] = set()


def _spawn_background_task(coro) -> None:
    """Create a task keeping a reference until it finishes."""
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


async def _safe_delete_after_delay(
    client: Client, chat_id: int, message_ids: list[int], delay: int
) -> None:
    """Delete all parts of one download in a single API call after delay."""
    try:
        await asyncio.sleep(delay)
        await client.delete_messages(chat_id, message_ids)
        logger.info("Mensajes %s eliminados del chat %s", message_ids, chat_id)
    except Exception:
        logger.exception("No se pudieron eliminar mensajes en chat %s", chat_id)


@bot.on_message(
    command("start", prefixes=["/"]) & private, group=1  # off the main handler
                                                  # group: concurrent chats
                                                  # never block each other
)
async def hello(client: Client, message: Message):

    if message.from_user is None:
        return

    user_id = message.from_user.id
    user = await asyncio.to_thread(
        get_or_create_user,
        Users(
            id=user_id,
            username=message.from_user.username,
            rest_tries=10,
            is_admin=False,
            premium_user=False,
        ),
    )
    if user is None:
        return

    if message.command is not None and len(message.command) == 1:
        if user.is_admin:
            await message.reply(f"Hola Administrador: {message.from_user.first_name}")
        else:
            await message.reply_sticker(
                Path.cwd() / Path("assets") / Path("dancer.tgs")
            )
            await message.reply(
                f"Hola {message.from_user.mention}, gracias por usar nuestro bot, nos complace tenerte como usuario, para tener una guia mas detallada de como funciona el bot, utiliza el comando /help.\n\nNos encantaria conocerte, asi que por que no entras a nuestro chat del canal: @chat1080p, donde tambien...shhh...spoiler: ||Podras pedir esa serie o peli que llevas dias buscando|| (Que no se te olvide poner #cine <nombre> y una foto para nosotros saber cual es)."
            )
        return

    if not await check_user_in_channel(client, message):
        return

    if message.command is not None and message.command[0] == "start":
        try:
            if len(message.command) >= 2:
                # Blocking DB access (sync SQLAlchemy/psycopg2) moved off the
                # event loop so other users' requests keep being served while
                # this query runs.
                result = await asyncio.to_thread(get_game, message.command[1])

                is_restricted = not user.is_admin and not await asyncio.to_thread(
                    is_premium, user
                )
                delete_delay = int(os.getenv("DELETE_MESSAGE_DELAY", "180"))
                channel_id = int(os.getenv("CHANNEL_ID"))
                sent_ids: list[int] = []

                async def copy_one(file_id: str) -> int | None:
                    """Copy a single file with bounded concurrency and
                    limited FloodWait retries so one bad file cannot block
                    the whole bot."""
                    async with _COPY_SEMAPHORE:
                        for attempt in range(3):
                            try:
                                sent = await client.copy_message(
                                    message.chat.id, channel_id, file_id
                                )
                            except FloodWait as f:
                                # Respect Telegram's wait, but cap it; very
                                # long waits are retried later, not blocked on.
                                wait = min(f.value, 60)
                                logger.warning(
                                    "FloodWait %ss (esperando %ss), "
                                    "intento %s/3 para %s", 
                                    f.value, 
                                    wait, 
                                    attempt + 1, 
                                    file_id
                                )
                                await asyncio.sleep(wait)
                            except Exception:
                                logger.exception("Error copiando %s", file_id)
                                break
                            else:
                                return sent.id
                        return None

                # All parts of this download are copied concurrently (limited
                # by the semaphore) instead of strictly one after another.
                results = await asyncio.gather(
                    *(copy_one(fid) for fid in result.file_ids)
                )
                sent_ids = [mid for mid in results if mid is not None]

                if is_restricted:
                    # ONE background task deletes ALL the parts in a single
                    # API call instead of spawning a task (and a delete call)
                    # per file. Fewer tasks + fewer delete requests => the
                    # mass-deleting scenario no longer saturates the API.
                    if sent_ids:
                        _spawn_background_task(
                            _safe_delete_after_delay(
                                client, message.chat.id, sent_ids, delete_delay
                            )
                        )
                    await message.reply(
                        "Esto tendrá una duración de 3 minutos ⏳ contados a partir del envío del mensaje. 📨\n\n¡Reenvíalo a tus mensajes guardados para no perderlo! 📂✅"
                    )
                    await message.reply(
                        "Si deseas eliminar esta restricción, usa el comando /vip o /profile para acceder a nuestro plan premium, el más barato de todo Telegram🚀"
                    )

                await message.reply_sticker(
                    Path.cwd() / Path("assets") / Path("finished.webp")
                )


                donation_message = """
💖 ¿Te gusta el contenido del canal?

Si este espacio te aporta valor y quieres apoyar el trabajo del administrador,
puedes hacer una donación voluntaria.
Cada aporte ayuda a mantener el canal activo y mejorar la calidad del contenido.

🔗 Usa el comando /donate

¡Gracias por ser parte de esta comunidad! 🙌"""
                await message.reply(donation_message)

                await asyncio.to_thread(
                    record_download, user_id, result.movie_genres
                )
        except (TypeError, ValueError):
            logger.exception("Error al obtener los archivos que pide el usuario")
