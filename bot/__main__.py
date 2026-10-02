# BOT CLIENT
# misc
import asyncio

# LOGGING
import logging

# SIGNAL HANDLERS (ver _install_signal_handlers al final del archivo).
# Sin esto, Ctrl-C / `systemctl stop` puede dejar el túnel cloudflared vivo
# como huérfano consumiendo RAM/CPU en el VPS.
import signal

from commands.Collection import collect_messages, end_collection
from commands.Fusion import fusion_posts

# COMMAND FUNCTIONS
from commands.Hello import hello
from commands.InfoPosts import info_posts
from commands.Misc import (
    ascend_to_admin,
    convert_user_premium,
    count_users,
    donations,
    get_top10,
    help_command,
    make_old_posts,
    send_admin_message,
)

from commands.Order import get_orders
from commands.Posts import create_posts, remove_posts
from commands.Profile import profile_panel
from commands.Publicity import publi_command
from commands.Recommendations import recommend
from commands.SearchPosts import search_posts
from commands.Stream import stream_handler
from commands.Subtitles import search_subtitles

# MAIN FUNCTIONS
from db.create_cine_db import create_db
from entry.entry import bot
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.inline_query_handler import InlineQueryHandler

# PYRO
from pyrogram.handlers.message_handler import MessageHandler

# QUERY FUNCTIONS
from queries.cb_queries import query_manager, save_user_photo
from queries.inline_queries import inline_answer
from stream.config import StreamConfig

# STREAM
from stream.server import start_stream_server
from stream.tunnel import start_cloudflare_tunnel

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Create DBs
create_db()

# Commands
bot.add_handler(MessageHandler(hello))
bot.add_handler(MessageHandler(collect_messages))
bot.add_handler(MessageHandler(end_collection))
bot.add_handler(MessageHandler(get_orders))
bot.add_handler(MessageHandler(send_admin_message))
bot.add_handler(MessageHandler(count_users))
bot.add_handler(MessageHandler(ascend_to_admin))
bot.add_handler(MessageHandler(convert_user_premium))
bot.add_handler(MessageHandler(get_top10))
bot.add_handler(MessageHandler(search_subtitles))
bot.add_handler(MessageHandler(help_command))
bot.add_handler(MessageHandler(create_posts))
bot.add_handler(MessageHandler(remove_posts))
bot.add_handler(MessageHandler(info_posts))
bot.add_handler(MessageHandler(search_posts))
bot.add_handler(MessageHandler(donations))
bot.add_handler(MessageHandler(publi_command))
bot.add_handler(MessageHandler(fusion_posts))
bot.add_handler(MessageHandler(stream_handler))
bot.add_handler(MessageHandler(make_old_posts))
bot.add_handler(MessageHandler(profile_panel))
bot.add_handler(MessageHandler(save_user_photo))
bot.add_handler(MessageHandler(recommend))

# Queries
bot.add_handler(CallbackQueryHandler(query_manager))
bot.add_handler(InlineQueryHandler(inline_answer))


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    """Convierte SIGINT/SIGTERM en un apagado limpio.

    Al correr bajo systemd, `systemctl stop` envía SIGTERM. Si el proceso
    muere de golpe, el hijo `cloudflared` puede quedar huérfano (adoptado
    por PID 1) comiéndose la RAM del VPS — una de las causas clásicas de
    que el server "se congele". Con estos handlers podemos detener primero
    el túnel y luego el bot.
    """
    loop = asyncio.get_running_loop()

    def _handler(sig):
        logger.info(f"Señal {signal.Signals(sig).name} recibida, apagando...")
        loop.call_soon_threadsafe(stop_event.set)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handler, sig)
        except NotImplementedError:  # p.ej. Windows
            signal.signal(sig, lambda s, f: loop.call_soon_threadsafe(stop_event.set))


async def main():
    tunnel = None

    # Primero configura el tunnel si es necesario
    if "localhost" in StreamConfig.URL or "127.0.0.1" in StreamConfig.URL:
        logger.info("Starting Cloudflare tunnel...")
        tunnel_url, tunnel = start_cloudflare_tunnel(StreamConfig.PORT)
        if tunnel_url:
            StreamConfig.update_url(tunnel_url)
            logger.info(f"URL updated: {StreamConfig.URL}")
        else:
            logger.info("Could not start tunnel, using local URL")

    # Luego inicia el stream server
    await start_stream_server(bot)
    logger.info(f"Stream server active at: {StreamConfig.URL}")

    # Finalmente inicia el bot
    await bot.start()
    logger.info("Bot started")

    # Esperamos a una señal de apagado (en vez de Event().wait() para siempre)
    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)
    await stop_event.wait()

    # Apagado ordenado: primero el túnel (para no dejar cloudflared huérfano),
    # después el bot.
    if tunnel is not None:
        try:
            tunnel.stop()
        except Exception as e:
            logger.warning(f"Error deteniendo el túnel: {e}")
    try:
        await bot.stop()
    except Exception as e:
        logger.warning(f"Error deteniendo el bot: {e}")
    logger.info("Apagado limpio completado.")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot apagado por el usuario.")
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
