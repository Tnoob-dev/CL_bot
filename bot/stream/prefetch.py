import asyncio
import logging

from pyrogram import Client, raw

from .cache import global_chunk_cache, global_coordinator, global_download_semaphore
from .config import StreamConfig

logger = logging.getLogger(__name__)


class PrefetchManager:
    def __init__(self):
        self.active_tasks: set[asyncio.Task] = set()

    def start_prefetch(
        self,
        client: Client,
        dc_id: int,
        file_id_str: str,
        location,
        offset: int,
        start_part: int,
        part_count: int,
        chunk_size: int,
        file_size: int,
        **_ignored,
    ):
        # **_ignored absorbe message_id/refresh_callback si algún caller viejo
        # todavía los pasa; el prefetch ya no los necesita (ver más abajo).
        task = asyncio.create_task(
            self._prefetch_worker(
                client,
                dc_id,
                file_id_str,
                location,
                offset,
                start_part,
                part_count,
                chunk_size,
                file_size,
            )
        )
        self.active_tasks.add(task)
        task.add_done_callback(self.active_tasks.discard)

    async def _prefetch_worker(
        self,
        client: Client,
        dc_id: int,
        file_id_str: str,
        location,
        start_offset: int,
        start_part: int,
        part_count: int,
        chunk_size: int,
        file_size: int,
    ):
        """
        El prefetch es trabajo descartable en segundo plano: si un chunk falla,
        simplemente se salta y sigue con el siguiente (igual que el diseño
        original). A propósito NO reintenta ni refresca file_reference aquí:
        si lo hiciera, un chunk problemático haría que el prefetch se pusiera
        a reintentar agresivamente compitiendo por el mismo cupo de
        concurrencia (global_download_semaphore) que necesita el stream
        principal para seguir sirviendo al usuario en vivo.
        """
        try:
            session = await client.get_session(dc_id, is_media=True)
            current_offset = start_offset

            for _ in range(start_part, start_part + part_count):
                if current_offset >= file_size:
                    break

                cached_chunk = await global_chunk_cache.get(file_id_str, current_offset)
                if not cached_chunk:
                    should_download = await global_coordinator.wait_or_start(
                        file_id_str, current_offset
                    )
                    if should_download:
                        try:
                            async with global_download_semaphore:
                                result = await session.invoke(
                                    raw.functions.upload.GetFile(
                                        location=location,
                                        offset=current_offset,
                                        limit=chunk_size,
                                    ),
                                    sleep_threshold=StreamConfig.SLEEP_THRESHOLD,
                                )
                            if (
                                isinstance(result, raw.types.upload.File)
                                and result.bytes
                            ):
                                await global_chunk_cache.put(
                                    file_id_str, current_offset, result.bytes
                                )
                        except Exception as e:
                            logger.debug(
                                f"Prefetch: chunk descartado en offset {current_offset}: {e}"
                            )
                        finally:
                            await global_coordinator.finish(file_id_str, current_offset)
                current_offset += chunk_size
        except Exception as e:
            logger.debug(f"Prefetch abortado/fallo: {e}")


global_prefetch_manager = PrefetchManager()
