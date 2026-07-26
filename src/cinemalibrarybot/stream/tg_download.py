import asyncio
import logging
from typing import Optional

from pyrogram import raw
from pyrogram.errors import FloodWait, RPCError

logger = logging.getLogger(__name__)


class FileReferenceExpiredError(Exception):
    """El file_reference del media ya no es válido.

    Quien llame debe refrescarlo (re-obteniendo el mensaje original desde
    Telegram) y reconstruir el location antes de reintentar.
    """
    pass


async def fetch_chunk(
    session,
    location,
    offset: int,
    chunk_size: int,
    sleep_threshold: int,
    semaphore: asyncio.Semaphore,
    max_retries: int = 4,
    base_delay: float = 1.0,
) -> Optional[bytes]:
    """Descarga un chunk de Telegram con reintentos y backoff exponencial.

    - Ante FLOOD_WAIT espera lo que Telegram pide y reintenta.
    - Ante errores de file_reference caducado, lanza FileReferenceExpiredError
      para que el caller refresque el location y reintente desde fuera.
    - Ante otros errores transitorios (timeouts, desconexiones, etc.) reintenta
      con backoff exponencial hasta max_retries antes de rendirse.
    - Retorna None si se agotan los reintentos por causas no recuperables.
    """
    attempt = 0
    while attempt <= max_retries:
        try:
            async with semaphore:
                result = await session.invoke(
                    raw.functions.upload.GetFile(
                        location=location,
                        offset=offset,
                        limit=chunk_size,
                    ),
                    sleep_threshold=sleep_threshold,
                )
            if isinstance(result, raw.types.upload.File) and result.bytes:
                return result.bytes
            return None

        except FloodWait as e:
            wait_time = e.value + 1
            logger.warning(f"FloodWait de Telegram: esperando {wait_time}s (offset={offset})")
            await asyncio.sleep(wait_time)
            attempt += 1

        except RPCError as e:
            error_text = f"{e.__class__.__name__} {e}".upper()
            if "FILE_REFERENCE" in error_text:
                raise FileReferenceExpiredError(str(e))

            attempt += 1
            if attempt > max_retries:
                logger.error(f"Se agotaron los reintentos en offset {offset}: {e}")
                return None
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                f"Error de Telegram ({e.__class__.__name__}) en offset {offset}, "
                f"intento {attempt}/{max_retries}: {e}"
            )
            await asyncio.sleep(delay)

        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Se agotaron los reintentos en offset {offset}: {e}")
                return None
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                f"Error inesperado descargando offset {offset}, "
                f"intento {attempt}/{max_retries}: {e}"
            )
            await asyncio.sleep(delay)

    return None