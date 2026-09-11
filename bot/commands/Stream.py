import logging

from entry.entry import bot
from pyrogram.client import Client
from pyrogram.filters import command, private
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from stream.config import StreamConfig
from stream.file_properties import get_file_info_by_id, get_short_hash, pack_file
from utils.db_reqs import is_premium_active
from utils.functions import check_administration

logger = logging.getLogger(__name__)


@bot.on_message(command("stream", prefixes=["/"]) & private)
async def stream_handler(client: Client, message: Message):

    if is_premium_active(message.from_user.id) or check_administration(message):
        if not message.reply_to_message and not _has_media(message):
            await message.reply(
                "<blockquote><b>Uso:</b> Envía un archivo y responde con "
                "<code>/stream</code>.</blockquote>",
            )
            return

        target = message.reply_to_message if message.reply_to_message else message

        if not _has_media(target):
            await message.reply(
                "<blockquote><b>Error:</b> El mensaje no contiene un archivo.</blockquote>"
            )
            return

        try:
            status_msg = await message.reply(
                "<blockquote><i>Generando enlace de stream...</i></blockquote>"
            )

            forwarded = await target.copy(
                chat_id=StreamConfig.BIN_CHANNEL,
                caption=f"{target.caption if target.caption else ''}\n\n👤 Archivo o video siendo stremeado por {message.from_user.mention}\n\n🆔 ID <code>{message.from_user.id}</code>",
            )

            file_info = await get_file_info_by_id(
                client, StreamConfig.BIN_CHANNEL, forwarded.id
            )
            if not file_info:
                await status_msg.edit_text(
                    "<blockquote><b>Error:</b> No se pudo obtener info del archivo.</blockquote>"
                )
                return

            logger.info(
                "Nombre del archivo a stremear despues de crear hash: "
                + str(file_info.file_name)
            )
            logger.info(
                "Tamanho del archivo a stremear despues de crear hash: "
                + str(file_info.file_size)
            )
            logger.info(
                "MimeType del archivo a stremear despues de crear hash: "
                + str(file_info.mime_type)
            )
            logger.info(
                "MessageID del archivo a stremear despues de crear hash: "
                + str(file_info.message_id)
            )

            # hash y link
            full_hash = pack_file(
                file_info.file_name,
                file_info.file_size,
                file_info.mime_type,
                file_info.message_id,
            )

            logger.info("Full hash: " + full_hash)
            logger.info("Short Hash: " + get_short_hash(full_hash))

            file_hash = get_short_hash(full_hash)
            stream_link = f"{StreamConfig.URL}stream/{forwarded.id}?hash={file_hash}"

            # enlace
            watch_link = f"{StreamConfig.URL}watch/{forwarded.id}?hash={file_hash}"

            text = f"🎬 <b>{file_info.file_name}</b>\n"
            text += f"<code>{file_info.file_size / 1024 / 1024:.1f} MB</code>"

            buttons = [
                [InlineKeyboardButton("Ver en navegador", url=watch_link)],
                [InlineKeyboardButton("Ver en Reproductor", url=stream_link)],
            ]

            await status_msg.delete()
            await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))

            print(f"Stream link generado: {stream_link} (msg_id={forwarded.id})")

        except Exception as e:
            logger.error(f"Error generando stream link: {e}")
            await message.reply(
                "<blockquote><b>Error:</b> No se pudo generar el enlace de stream. Inténtalo de nuevo más tarde.</blockquote>"
            )

    else:
        await message.reply(
            "Usted no ha adquirido un plan VIP aun, para hacerlo use el comando /vip"
        )


async def stream_media_handler(client: Client, message: Message):
    """Handler para archivos enviados directamente al bot (sin /stream)."""
    await stream_handler(client, message)


def _has_media(message: Message) -> bool:
    """Verifica si un mensaje tiene media que se pueda streamear."""
    return bool(
        message.document
        or message.video
        or message.audio
        or message.photo
        or message.voice
        or message.video_note
    )
