import logging
import math
import asyncio
from collections import OrderedDict
from typing import AsyncGenerator, Optional
import time
from pyrogram import Client, raw
from pyrogram.file_id import FileId, PHOTO_TYPES

from .config import StreamConfig
from .file_properties import FileInfo, get_file_info_by_id
from .cache import global_chunk_cache, global_coordinator, global_download_semaphore
from .prefetch import global_prefetch_manager
from .tg_download import fetch_chunk, FileReferenceExpiredError

logger = logging.getLogger(__name__)


def _build_location(file_id: FileId):
    """Construye el InputFileLocation adecuado (foto o documento) a partir de un FileId decodificado."""
    if file_id.file_type in PHOTO_TYPES:
        return raw.types.InputPhotoFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size or "y",
        )
    return raw.types.InputDocumentFileLocation(
        id=file_id.media_id,
        access_hash=file_id.access_hash,
        file_reference=file_id.file_reference,
        thumb_size=file_id.thumbnail_size or "",
    )


class PyrogramStreamer:
    """Descarga chunks de archivos de Telegram para streaming HTTP, usando cache y preloading."""

    def __init__(self, client: Client):
        self.client = client
        self.cached_files: OrderedDict[int, FileInfo] = OrderedDict()

    async def get_file_properties(self, message_id: int) -> Optional[FileInfo]:
        """Obtiene las propiedades de un archivo, con caché."""
        if message_id in self.cached_files:
            return self.cached_files[message_id]

        file_info = await get_file_info_by_id(
            self.client, StreamConfig.BIN_CHANNEL, message_id
        )
        if not file_info:
            logger.debug(f"Archivo no encontrado para message_id {message_id}")
            return None

        if len(self.cached_files) >= StreamConfig.CACHE_SIZE:
            self.cached_files.popitem(last=False)

        self.cached_files[message_id] = file_info
        logger.debug(f"FileInfo cacheado para message_id {message_id}")
        return file_info

    async def _refresh_file_reference(self, message_id: int) -> Optional[FileInfo]:
        """Vuelve a pedir el mensaje a Telegram para obtener un file_reference fresco."""
        self.cached_files.pop(message_id, None)
        fresh_info = await get_file_info_by_id(self.client, StreamConfig.BIN_CHANNEL, message_id)
        if fresh_info:
            self.cached_files[message_id] = fresh_info
            logger.info(f"file_reference refrescado para message_id {message_id}")
        return fresh_info

    async def download(
        self,
        file_info: FileInfo,
        file_size: int,
        from_bytes: int,
        until_bytes: int,
        quality: str = "auto",
    ) -> AsyncGenerator[bytes, None]:
        chunk_size = StreamConfig.CHUNK_SIZE

        file_id = FileId.decode(file_info.file_id)
        dc_id = file_id.dc_id
        location = _build_location(file_id)

        offset = from_bytes - (from_bytes % chunk_size)
        first_part_cut = from_bytes - offset
        first_part = math.floor(offset / chunk_size)
        last_part_cut = until_bytes % chunk_size + 1
        last_part = math.ceil(until_bytes / chunk_size)
        part_count = last_part - first_part
        total_parts = math.ceil(file_size / chunk_size)

        prefetch_count = StreamConfig.PREFETCH_COUNT

        logger.debug(
            f"Streaming: chunks {first_part}-{last_part} de {part_count} (total {total_parts}) "
            f"quality={quality}"
        )

        try:
            session = None
            current_part = 1
            current_offset = offset

            # Rate limiting logic
            window_start_time = time.time()
            bytes_sent_in_window = 0

            duration = getattr(file_info, "duration", 0)
            if duration and duration > 0:
                real_avg_bytes_per_sec = file_info.file_size / duration
            else:
                real_avg_bytes_per_sec = 1.5 * 1024 * 1024  # 1.5 MB/s por defecto

            # La "calidad" no transcodifica el video: solo limita la velocidad de
            # envío para simular menor calidad / ahorrar datos en conexiones malas.
            quality_cap = StreamConfig.QUALITY_CAPS_BYTES_PER_SEC.get(quality)
            if quality_cap:
                avg_bytes_per_sec = min(real_avg_bytes_per_sec, quality_cap)
            else:
                avg_bytes_per_sec = real_avg_bytes_per_sec

            initial_burst_seconds = 15  # Primeros 15s de video sin limitar
            window_send_seconds = 60    # Enviar durante 60s
            window_pause_seconds = 50   # Pausar 50s
            initial_burst_bytes = avg_bytes_per_sec * initial_burst_seconds
            window_send_bytes_limit = avg_bytes_per_sec * window_send_seconds

            consecutive_failures = 0
            max_consecutive_failures = 3

            while current_part <= part_count:
                chunk = await global_chunk_cache.get(file_info.file_id, current_offset)

                if not chunk:
                    should_download = await global_coordinator.wait_or_start(file_info.file_id, current_offset)
                    if should_download:
                        try:
                            if not session:
                                session = await self.client.get_session(dc_id, is_media=True)

                            try:
                                chunk = await fetch_chunk(
                                    session, location, current_offset, chunk_size,
                                    StreamConfig.SLEEP_THRESHOLD, global_download_semaphore,
                                    StreamConfig.MAX_TELEGRAM_RETRIES, StreamConfig.RETRY_BASE_DELAY,
                                )
                            except FileReferenceExpiredError:
                                fresh_info = await self._refresh_file_reference(file_info.message_id)
                                if fresh_info:
                                    file_info.file_id = fresh_info.file_id
                                    file_id = FileId.decode(file_info.file_id)
                                    location = _build_location(file_id)
                                    session = await self.client.get_session(dc_id, is_media=True)
                                    chunk = await fetch_chunk(
                                        session, location, current_offset, chunk_size,
                                        StreamConfig.SLEEP_THRESHOLD, global_download_semaphore,
                                        StreamConfig.MAX_TELEGRAM_RETRIES, StreamConfig.RETRY_BASE_DELAY,
                                    )
                                else:
                                    chunk = None

                            if chunk:
                                await global_chunk_cache.put(file_info.file_id, current_offset, chunk)
                        finally:
                            await global_coordinator.finish(file_info.file_id, current_offset)
                    else:
                        chunk = await global_chunk_cache.get(file_info.file_id, current_offset)

                if not chunk:
                    consecutive_failures += 1
                    logger.error(
                        f"No se pudo obtener el chunk en offset {current_offset} "
                        f"(fallo consecutivo {consecutive_failures}/{max_consecutive_failures})"
                    )
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("Demasiados fallos consecutivos, abortando el stream.")
                        break
                    # pequeña espera antes de reintentar el mismo offset una vez más
                    await asyncio.sleep(1.0)
                    continue

                consecutive_failures = 0

                # Iniciar prefetch de los siguientes bloques (1 minuto aprox)
                if current_part == 1 or current_part % 5 == 0:
                    prefetch_start_offset = current_offset + chunk_size
                    prefetch_start_part = first_part + current_part
                    if prefetch_start_offset < file_size:
                        global_prefetch_manager.start_prefetch(
                            self.client, dc_id, file_info.file_id, location,
                            prefetch_start_offset, prefetch_start_part, prefetch_count,
                            chunk_size, file_size, message_id=file_info.message_id,
                            refresh_callback=self._refresh_file_reference,
                        )

                current_offset += chunk_size

                chunk_to_yield = chunk
                if part_count == 1:
                    chunk_to_yield = chunk[first_part_cut:last_part_cut]
                elif current_part == 1:
                    chunk_to_yield = chunk[first_part_cut:]
                elif current_part == part_count:
                    chunk_to_yield = chunk[:last_part_cut]

                # Rate limiting (también usado para simular "calidad" más baja)
                if avg_bytes_per_sec > 0:
                    chunk_size_sent = len(chunk_to_yield)
                    bytes_sent_in_window += chunk_size_sent

                    if bytes_sent_in_window > initial_burst_bytes:
                        expected_time = (bytes_sent_in_window - initial_burst_bytes) / avg_bytes_per_sec
                        actual_time = time.time() - window_start_time

                        if actual_time < expected_time:
                            sleep_time = expected_time - actual_time
                            await asyncio.sleep(sleep_time)

                    if bytes_sent_in_window >= window_send_bytes_limit + initial_burst_bytes:
                        logger.debug(
                            f"Ventana completada: {(bytes_sent_in_window - initial_burst_bytes) / 1024 / 1024:.1f}MB "
                            f"en {window_send_seconds}s. Pausando {window_pause_seconds}s..."
                        )
                        await asyncio.sleep(window_pause_seconds)

                        window_start_time = time.time()
                        bytes_sent_in_window = 0

                yield chunk_to_yield

                current_part += 1

        except (GeneratorExit, StopAsyncIteration):
            logger.debug("Streaming interrumpido por el cliente")
            raise
        except Exception:
            logger.error("Error durante el streaming", exc_info=True)